"""Unit tests for the field normalizers."""

from pipeline.normalizers import (
    NormalizationOptions,
    load_normalization_options,
    normalize_email,
    normalize_name,
    normalize_phone,
    normalize_postal,
    normalize_row,
)

OPTS = NormalizationOptions()


def test_load_real_options(project_root):
    options = load_normalization_options(project_root / "config" / "pipeline.yaml")
    assert options.phone_default_country_code == "1"
    assert options.name_title_case is True


def test_normalize_name_collapses_and_titles():
    assert normalize_name("  john   smith  ", OPTS) == "John Smith"
    assert normalize_name("MARY  JONES", OPTS) == "Mary Jones"


def test_normalize_phone_with_and_without_plus():
    assert normalize_phone("+1 (555) 123-4567", OPTS) == "+15551234567"
    assert normalize_phone("555.987.6543", OPTS) == "+15559876543"
    assert normalize_phone("", OPTS) == ""
    assert normalize_phone(None, OPTS) == ""


def test_normalize_postal_uppercases():
    assert normalize_postal("m5h 2n2", OPTS) == "M5H 2N2"


def test_normalize_email_lowercases():
    assert normalize_email("  JANE.DOE@EXAMPLE.COM ") == "jane.doe@example.com"


def test_normalizers_are_idempotent():
    row = {
        "full_name": "  john   smith ",
        "email": "JOHN.SMITH@EXAMPLE.COM",
        "phone": "555.987.6543",
        "postal_code": "m5h 2n2",
    }
    once = normalize_row(row, OPTS)
    twice = normalize_row(once, OPTS)
    assert once == twice


def test_normalize_row_only_touches_known_fields():
    row = {"customer_id": "1", "full_name": "jane doe", "unknown": "  keep me  "}
    result = normalize_row(row, OPTS)
    assert result["full_name"] == "Jane Doe"
    assert result["customer_id"] == "1"
    assert result["unknown"] == "  keep me  "
