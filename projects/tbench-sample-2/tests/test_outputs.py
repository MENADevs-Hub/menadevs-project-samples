"""Behavioral tests for the email suppression window repair task."""

import json
import os
import subprocess
from pathlib import Path

APP_DIR = Path(os.environ.get("APP_DIR", "/app"))
CLI = APP_DIR / "bin" / "suppression-cli.js"


def run_plan(tmp_path: Path, rows: list[object] | list[str], as_of: str = "2026-06-01T00:00:00Z") -> dict:
    """Run the suppression CLI against JSONL rows and return the parsed report."""
    events_path = tmp_path / "events.jsonl"
    out_path = tmp_path / "report.json"
    lines = []
    for row in rows:
        if isinstance(row, str):
            lines.append(row)
        else:
            lines.append(json.dumps(row, separators=(",", ":")))
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = subprocess.run(
        ["node", str(CLI), "--events", str(events_path), "--as-of", as_of, "--out", str(out_path)],
        cwd=APP_DIR,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert out_path.exists(), "CLI did not create the requested report file"
    return json.loads(out_path.read_text(encoding="utf-8"))


def recipient(report: dict, email: str) -> dict:
    """Find one recipient object by canonical email."""
    matches = [item for item in report["recipients"] if item["email"] == email]
    assert len(matches) == 1, f"expected exactly one recipient for {email}, got {matches}"
    return matches[0]


def reason_codes(report: dict, email: str) -> list[str]:
    """Return the active reason codes for one recipient."""
    return [reason["code"] for reason in recipient(report, email)["reasons"]]


def test_bounce_expiration_half_open_boundary_and_zero_day_override(tmp_path: Path) -> None:
    """Bounce windows must expire at the exact boundary and honor explicit zero-day overrides."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "hard-edge",
                "email": "Edge@example.com",
                "type": "bounce",
                "subtype": "hard",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            {
                "event_id": "zero-soft",
                "email": "Zero@example.com",
                "type": "bounce",
                "subtype": "soft",
                "expiry_days": 0,
                "timestamp": "2026-06-01T00:00:00Z",
            },
            {
                "event_id": "active-soft",
                "email": "Active@example.com",
                "type": "bounce",
                "subtype": "soft",
                "timestamp": "2026-05-25T00:00:00Z",
            },
        ],
        as_of="2026-06-30T00:00:00Z",
    )

    assert recipient(report, "edge@example.com")["suppressed"] is False
    assert recipient(report, "zero@example.com")["suppressed"] is False
    assert reason_codes(report, "active@example.com") == []

    report_active = run_plan(
        tmp_path,
        [
            {
                "event_id": "active-soft",
                "email": "Active@example.com",
                "type": "bounce",
                "subtype": "soft",
                "timestamp": "2026-05-25T00:00:00Z",
            }
        ],
        as_of="2026-06-01T00:00:00Z",
    )
    assert reason_codes(report_active, "active@example.com") == ["soft_bounce"]
    assert recipient(report_active, "active@example.com")["reasons"][0]["expires_at"] == "2026-06-08T00:00:00.000Z"


def test_complaint_and_hard_bounce_survive_later_global_resubscribe(tmp_path: Path) -> None:
    """Resubscribe clears soft bounces and unsubscribes but not complaints or hard bounces."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "soft-1",
                "email": "Mixed@example.com",
                "type": "bounce",
                "subtype": "soft",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "hard-1",
                "email": "Mixed@example.com",
                "type": "bounce",
                "subtype": "hard",
                "timestamp": "2026-05-02T00:00:00Z",
            },
            {
                "event_id": "complaint-1",
                "email": "Mixed@example.com",
                "type": "complaint",
                "timestamp": "2026-05-03T00:00:00Z",
            },
            {
                "event_id": "unsub-1",
                "email": "Mixed@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-04T00:00:00Z",
            },
            {
                "event_id": "resub-global",
                "email": "Mixed@example.com",
                "type": "resubscribe",
                "timestamp": "2026-05-05T00:00:00Z",
            },
        ],
    )

    item = recipient(report, "mixed@example.com")
    assert item["suppressed"] is True
    assert [reason["code"] for reason in item["reasons"]] == ["complaint", "hard_bounce"]
    assert all(reason["event_id"] in {"complaint-1", "hard-1"} for reason in item["reasons"])


def test_unsubscribe_scope_and_list_resubscribe_are_not_global(tmp_path: Path) -> None:
    """A list-scoped resubscribe clears only that list while a global resubscribe clears all list unsubscribes."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "unsub-news",
                "email": "Scope@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "unsub-promos",
                "email": "Scope@example.com",
                "type": "unsubscribe",
                "list_id": "promos",
                "timestamp": "2026-05-02T00:00:00Z",
            },
            {
                "event_id": "resub-news",
                "email": "Scope@example.com",
                "type": "resubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-03T00:00:00Z",
            },
        ],
    )
    assert recipient(report, "scope@example.com")["reasons"] == [
        {
            "code": "unsubscribe",
            "scope": "list:promos",
            "event_id": "unsub-promos",
            "since": "2026-05-02T00:00:00.000Z",
            "expires_at": None,
        }
    ]

    cleared = run_plan(
        tmp_path,
        [
            {
                "event_id": "unsub-news",
                "email": "Scope@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "unsub-promos",
                "email": "Scope@example.com",
                "type": "unsubscribe",
                "list_id": "promos",
                "timestamp": "2026-05-02T00:00:00Z",
            },
            {
                "event_id": "resub-all",
                "email": "Scope@example.com",
                "type": "resubscribe",
                "timestamp": "2026-05-03T00:00:00Z",
            },
        ],
    )
    assert recipient(cleared, "scope@example.com")["suppressed"] is False


def test_out_of_order_events_are_applied_by_timestamp_then_line(tmp_path: Path) -> None:
    """Out-of-order JSONL rows must be applied chronologically, with line order only breaking timestamp ties."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "late-resub",
                "email": "Order@example.com",
                "type": "resubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-10T00:00:00Z",
            },
            {
                "event_id": "early-unsub",
                "email": "Order@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "tie-unsub",
                "email": "Tie@example.com",
                "type": "unsubscribe",
                "list_id": "product",
                "timestamp": "2026-05-11T00:00:00Z",
            },
            {
                "event_id": "tie-resub",
                "email": "Tie@example.com",
                "type": "resubscribe",
                "list_id": "product",
                "timestamp": "2026-05-11T00:00:00Z",
            },
        ],
    )
    assert recipient(report, "order@example.com")["suppressed"] is False
    assert recipient(report, "tie@example.com")["suppressed"] is False


def test_duplicate_event_ids_warn_and_keep_first_valid_line(tmp_path: Path) -> None:
    """Duplicate event ids must leave the first valid row in force and ignore later duplicates."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "dup-1",
                "email": "Dup@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "dup-1",
                "email": "Dup@example.com",
                "type": "complaint",
                "timestamp": "2026-05-02T00:00:00Z",
            },
        ],
    )

    assert reason_codes(report, "dup@example.com") == ["unsubscribe"]
    assert report["warnings"] == [
        {"code": "duplicate_event", "line": 2, "event_id": "dup-1", "detail": "dup-1"}
    ]


def test_invalid_and_future_rows_have_documented_warning_shape_without_creating_recipients(tmp_path: Path) -> None:
    """Invalid JSON, invalid timestamps, unknown types, missing lists, and future rows must produce sorted warnings only."""
    report = run_plan(
        tmp_path,
        [
            "{not-json",
            {
                "event_id": "bad-time",
                "email": "badtime@example.com",
                "type": "complaint",
                "timestamp": "not-a-date",
            },
            {
                "event_id": "unknown",
                "email": "unknown@example.com",
                "type": "paused",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "missing-list",
                "email": "list@example.com",
                "type": "unsubscribe",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "future",
                "email": "future@example.com",
                "type": "complaint",
                "timestamp": "2026-07-01T00:00:00Z",
            },
        ],
    )

    assert report["recipients"] == []
    assert [list(warning.keys()) for warning in report["warnings"]] == [
        ["code", "line", "event_id", "detail"],
        ["code", "line", "event_id", "detail"],
        ["code", "line", "event_id", "detail"],
        ["code", "line", "event_id", "detail"],
        ["code", "line", "event_id", "detail"],
    ]
    assert report["warnings"] == [
        {"code": "invalid_json", "line": 1, "event_id": None, "detail": "{not-json"},
        {"code": "invalid_timestamp", "line": 2, "event_id": "bad-time", "detail": "not-a-date"},
        {"code": "unknown_type", "line": 3, "event_id": "unknown", "detail": "paused"},
        {"code": "missing_list", "line": 4, "event_id": "missing-list", "detail": "list_id"},
        {"code": "future_event", "line": 5, "event_id": "future", "detail": "2026-07-01T00:00:00.000Z"},
    ]
    assert report["summary"]["warning_count"] == 5


def test_email_normalization_preserves_plus_tags_but_trims_and_lowercases(tmp_path: Path) -> None:
    """Canonical email identity must trim and lowercase without dropping plus tags."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "spaced",
                "email": "  User+Promo@Example.COM  ",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "plain",
                "email": "user@example.com",
                "type": "complaint",
                "timestamp": "2026-05-01T00:00:00Z",
            },
        ],
    )
    assert {item["email"] for item in report["recipients"]} == {"user@example.com", "user+promo@example.com"}
    assert reason_codes(report, "user+promo@example.com") == ["unsubscribe"]
    assert reason_codes(report, "user@example.com") == ["complaint"]


def test_report_schema_sorting_and_summary_counts_are_deterministic(tmp_path: Path) -> None:
    """The report must use the documented key order, recipient sorting, reason sorting, and active reason counts."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "z-unsub",
                "email": "z@example.com",
                "type": "unsubscribe",
                "list_id": "promos",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "a-hard",
                "email": "a@example.com",
                "type": "bounce",
                "subtype": "hard",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "a-complaint",
                "email": "a@example.com",
                "type": "complaint",
                "timestamp": "2026-05-02T00:00:00Z",
            },
            {
                "event_id": "m-soft",
                "email": "m@example.com",
                "type": "bounce",
                "subtype": "soft",
                "timestamp": "2026-05-30T00:00:00Z",
            },
        ],
    )

    assert list(report.keys()) == ["as_of", "summary", "recipients", "warnings"]
    assert list(report["summary"].keys()) == [
        "total_recipients",
        "suppressed_recipients",
        "warning_count",
        "active_reason_counts",
    ]
    assert [item["email"] for item in report["recipients"]] == ["a@example.com", "m@example.com", "z@example.com"]
    assert reason_codes(report, "a@example.com") == ["complaint", "hard_bounce"]
    assert report["summary"] == {
        "total_recipients": 3,
        "suppressed_recipients": 3,
        "warning_count": 0,
        "active_reason_counts": {
            "complaint": 1,
            "hard_bounce": 1,
            "soft_bounce": 1,
            "unsubscribe": 1,
        },
    }


def test_validation_warning_codes_cover_missing_identity_email_subtype_and_expiry(tmp_path: Path) -> None:
    """Missing identity/email, invalid email, bad bounce subtype, and bad expiry values must use documented warnings."""
    report = run_plan(
        tmp_path,
        [
            {
                "email": "missingid@example.com",
                "type": "complaint",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "missing-email",
                "type": "complaint",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "invalid-email",
                "email": "not-an-email",
                "type": "complaint",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "bad-subtype",
                "email": "badsub@example.com",
                "type": "bounce",
                "subtype": "mailbox-full",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "bad-expiry",
                "email": "badexp@example.com",
                "type": "bounce",
                "subtype": "hard",
                "expiry_days": -1,
                "timestamp": "2026-05-01T00:00:00Z",
            },
        ],
        as_of="2026-06-01T00:00:00Z",
    )

    assert report["warnings"] == [
        {"code": "missing_event_id", "line": 1, "event_id": None, "detail": "event_id"},
        {"code": "missing_email", "line": 2, "event_id": "missing-email", "detail": ""},
        {"code": "invalid_email", "line": 3, "event_id": "invalid-email", "detail": "not-an-email"},
        {"code": "unknown_bounce_subtype", "line": 4, "event_id": "bad-subtype", "detail": "mailbox-full"},
        {"code": "invalid_expiry_days", "line": 5, "event_id": "bad-expiry", "detail": "-1"},
    ]
    assert [item["email"] for item in report["recipients"]] == ["badexp@example.com"]
    assert recipient(report, "badexp@example.com")["reasons"] == [
        {
            "code": "hard_bounce",
            "scope": "global",
            "event_id": "bad-expiry",
            "since": "2026-05-01T00:00:00.000Z",
            "expires_at": "2026-10-28T00:00:00.000Z",
        }
    ]


def test_later_same_scope_reason_replaces_previous_reason_after_chronological_sort(tmp_path: Path) -> None:
    """A later active reason with the same email, code, and scope must replace the earlier one even from out-of-order rows."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "new-newsletter-unsub",
                "email": "Replace@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-20T00:00:00Z",
            },
            {
                "event_id": "old-newsletter-unsub",
                "email": "Replace@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
        ],
        as_of="2026-06-01T00:00:00Z",
    )

    assert recipient(report, "replace@example.com")["reasons"] == [
        {
            "code": "unsubscribe",
            "scope": "list:newsletter",
            "event_id": "new-newsletter-unsub",
            "since": "2026-05-20T00:00:00.000Z",
            "expires_at": None,
        }
    ]


def test_unsubscribe_expiry_days_uses_half_open_expiration_window(tmp_path: Path) -> None:
    """List unsubscribe expiry_days must create expiring reasons that are inactive at the exact boundary."""
    at_boundary = run_plan(
        tmp_path,
        [
            {
                "event_id": "short-unsub",
                "email": "Expire@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "expiry_days": 2,
                "timestamp": "2026-05-01T00:00:00Z",
            }
        ],
        as_of="2026-05-03T00:00:00Z",
    )
    assert recipient(at_boundary, "expire@example.com")["suppressed"] is False
    assert recipient(at_boundary, "expire@example.com")["reasons"] == []

    still_active = run_plan(
        tmp_path,
        [
            {
                "event_id": "long-unsub",
                "email": "Expire@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "expiry_days": 7,
                "timestamp": "2026-05-28T00:00:00Z",
            }
        ],
        as_of="2026-06-01T00:00:00Z",
    )
    assert recipient(still_active, "expire@example.com")["reasons"] == [
        {
            "code": "unsubscribe",
            "scope": "list:newsletter",
            "event_id": "long-unsub",
            "since": "2026-05-28T00:00:00.000Z",
            "expires_at": "2026-06-04T00:00:00.000Z",
        }
    ]


def test_future_duplicate_event_reserves_event_id_before_older_past_duplicate(tmp_path: Path) -> None:
    """Duplicate filtering happens before the future-event filter, so a future winner can reserve an event id."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "move-1",
                "email": "FutureDup@example.com",
                "type": "complaint",
                "timestamp": "2026-07-01T00:00:00Z",
            },
            {
                "event_id": "move-1",
                "email": "FutureDup@example.com",
                "type": "unsubscribe",
                "list_id": "newsletter",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "reused-after-invalid",
                "type": "complaint",
                "timestamp": "2026-05-01T00:00:00Z",
            },
            {
                "event_id": "reused-after-invalid",
                "email": "Reuse@example.com",
                "type": "complaint",
                "timestamp": "2026-05-02T00:00:00Z",
            },
        ],
    )

    assert [item["email"] for item in report["recipients"]] == ["reuse@example.com"]
    assert reason_codes(report, "reuse@example.com") == ["complaint"]
    assert report["warnings"] == [
        {"code": "future_event", "line": 1, "event_id": "move-1", "detail": "2026-07-01T00:00:00.000Z"},
        {"code": "duplicate_event", "line": 2, "event_id": "move-1", "detail": "move-1"},
        {"code": "missing_email", "line": 3, "event_id": "reused-after-invalid", "detail": ""},
    ]


def test_invalid_json_warning_detail_preserves_raw_line_text(tmp_path: Path) -> None:
    """Invalid JSON warning details must preserve the full raw input line, including spaces and long text."""
    long_bad_line = "  {not-json:" + ("x" * 150) + "  "
    report = run_plan(
        tmp_path,
        [
            long_bad_line,
            {
                "event_id": "valid-after-bad",
                "email": "AfterBad@example.com",
                "type": "unsubscribe",
                "list_id": "alerts",
                "timestamp": "2026-05-01T00:00:00Z",
            },
        ],
    )

    assert report["warnings"] == [
        {"code": "invalid_json", "line": 1, "event_id": None, "detail": long_bad_line}
    ]
    assert reason_codes(report, "afterbad@example.com") == ["unsubscribe"]


def test_invalid_expiry_on_future_row_emits_both_warnings_without_creating_recipient(tmp_path: Path) -> None:
    """A future row with invalid expiry_days remains valid enough to emit both expiry and future warnings."""
    report = run_plan(
        tmp_path,
        [
            {
                "event_id": "future-bad-expiry",
                "email": "FutureBadExpiry@example.com",
                "type": "bounce",
                "subtype": "hard",
                "expiry_days": "30",
                "timestamp": "2026-06-02T00:00:00Z",
            }
        ],
        as_of="2026-06-01T00:00:00Z",
    )

    assert report["recipients"] == []
    assert report["warnings"] == [
        {"code": "future_event", "line": 1, "event_id": "future-bad-expiry", "detail": "2026-06-02T00:00:00.000Z"},
        {"code": "invalid_expiry_days", "line": 1, "event_id": "future-bad-expiry", "detail": "30"},
    ]
