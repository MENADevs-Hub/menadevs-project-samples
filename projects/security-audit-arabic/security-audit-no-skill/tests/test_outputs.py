"""
Harbor verifier for security-audit task.

Validates:
- Reflected XSS in search is neutralized
- Stored XSS in dashboard is neutralized
- CSP is restrictive (no wildcards, no unsafe directives)
- Open redirects are rejected; safe redirects work
- Session cookies use secure flags
- HTTP security headers are present
- SECURITY_REPORT.md documents findings
- Application unit tests under /app/tests pass
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

from app import app  # noqa: E402

REPORT_PATH = Path("/app/SECURITY_REPORT.md")
APP_TESTS_DIR = Path("/app/tests")

XSS_PAYLOAD = '<img src=x onerror=alert(1)>'
PROTOCOL_RELATIVE = "//evil.example/phish"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_security_report_exists_and_covers_findings():
    assert REPORT_PATH.is_file(), "Missing /app/SECURITY_REPORT.md"
    text = REPORT_PATH.read_text(encoding="utf-8").lower()
    for topic in (
        "xss",
        "open redirect",
        "session cookie",
        "security header",
    ):
        assert topic in text, f"SECURITY_REPORT.md should discuss: {topic}"
    assert (
        "csp" in text
        or "content security policy" in text
        or "content-security-policy" in text
    ), "SECURITY_REPORT.md should discuss CSP"
    for label in ("severity", "root cause", "remediation"):
        assert label in text, f"SECURITY_REPORT.md should include '{label}' sections"


def test_reflected_xss_neutralized(client):
    response = client.get("/search", query_string={"q": XSS_PAYLOAD})
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # User input must not be injected as raw HTML (angle brackets escaped).
    assert "<img" not in body
    assert "&lt;img" in body
    assert "<script" not in body.lower()


def test_csp_is_restrictive(client):
    response = client.get("/")
    csp = response.headers.get("Content-Security-Policy", "")
    assert csp, "Content-Security-Policy header is required"
    assert "*" not in csp, "CSP must not use wildcard sources"
    assert "'unsafe-eval'" not in csp, "CSP must not use unsafe-eval"
    directives = [d.strip() for d in csp.split(";")]
    script_dir = next((d for d in directives if d.startswith("script-src")), "")
    assert "'unsafe-inline'" not in script_dir, (
        "script-src must not allow unsafe-inline"
    )


def test_open_redirect_rejected(client):
    for target in (
        "https://evil.example/phish",
        "http://attacker.test/",
        PROTOCOL_RELATIVE,
        "javascript:alert(1)",
    ):
        response = client.get("/redirect", query_string={"next": target})
        assert response.status_code == 400, f"Should reject redirect to {target!r}"


@pytest.mark.parametrize(
    "target,expected_location",
    [
        ("/dashboard", "/dashboard"),
        ("https://example.com/welcome", "https://example.com/welcome"),
    ],
)
def test_safe_redirects_allowed(client, target, expected_location):
    response = client.get("/redirect", query_string={"next": target}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == expected_location


def test_session_cookie_hardened(client):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] in ("Lax", "Strict", "lax", "strict")

    response = client.post("/login", data={"username": "auditor"}, follow_redirects=False)
    set_cookie = response.headers.get("Set-Cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite" in set_cookie


def test_stored_xss_in_dashboard_neutralized(client):
    client.post("/login", data={"username": XSS_PAYLOAD}, follow_redirects=True)
    response = client.get("/dashboard")
    body = response.get_data(as_text=True)
    assert "<img" not in body, "Session username must be escaped in dashboard"
    assert "&lt;img" in body


def test_security_headers_present(client):
    response = client.get("/")
    for header in (
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
    ):
        assert response.headers.get(header), f"Missing {header}"


def test_legitimate_app_flow(client):
    assert client.get("/").status_code == 200
    search = client.get("/search", query_string={"q": "quarterly"})
    assert search.status_code == 200
    assert "quarterly" in search.get_data(as_text=True)
    client.post("/login", data={"username": "pat"}, follow_redirects=True)
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    assert "pat" in dash.get_data(as_text=True)


def test_app_unit_tests_written():
    """Check the agent extended the test suite (not just the original smoke test)."""
    assert APP_TESTS_DIR.is_dir(), "/app/tests directory is required"
    test_files = list(APP_TESTS_DIR.glob("test_*.py"))
    assert test_files, "/app/tests must contain at least one test_*.py file"
    combined = ""
    for tf in test_files:
        combined += tf.read_text(encoding="utf-8")
    test_count = combined.count("\ndef test_")
    assert test_count >= 4, (
        f"/app/tests has only {test_count} test function(s); write at least 4 "
        "security regression tests"
    )
