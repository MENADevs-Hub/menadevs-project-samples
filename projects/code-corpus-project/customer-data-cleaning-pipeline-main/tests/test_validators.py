"""Unit tests for the validation rule engine."""

import pytest

from pipeline.config import load_schema
from pipeline.loader import load_csv
from pipeline.validators import (
    Rule,
    ValidationConfigError,
    load_rules,
    validate_row,
    validate_rows,
)


def test_load_real_rules(project_root):
    rules = load_rules(project_root / "config" / "validation_rules.yaml")
    types_by_field = {(r.field, r.type) for r in rules}
    assert ("email", "required") in types_by_field
    assert ("email", "email") in types_by_field
    assert ("country", "enum") in types_by_field


def test_load_rules_rejects_unknown_type(tmp_path):
    path = tmp_path / "rules.yaml"
    path.write_text("rules:\n  email:\n    - type: bogus\n", encoding="utf-8")
    with pytest.raises(ValidationConfigError):
        load_rules(path)


def test_required_rule():
    rule = Rule(field="full_name", type="required", params={})
    assert validate_row({"full_name": "John"}, [rule]) == []
    assert validate_row({"full_name": "   "}, [rule])[0].code == "required"
    assert validate_row({}, [rule])[0].code == "required"


def test_email_rule():
    rule = Rule(field="email", type="email", params={})
    assert validate_row({"email": "a@b.com"}, [rule]) == []
    assert validate_row({"email": "not-an-email"}, [rule])[0].code == "invalid_email"
    # empty passes the format rule (required handles emptiness)
    assert validate_row({"email": ""}, [rule]) == []


def test_phone_rule():
    rule = Rule(field="phone", type="phone", params={})
    assert validate_row({"phone": "+1 (555) 123-4567"}, [rule]) == []
    assert validate_row({"phone": "12"}, [rule])[0].code == "invalid_phone"


def test_enum_rule():
    rule = Rule(field="country", type="enum", params={"values": ["US", "CA"]})
    assert validate_row({"country": "US"}, [rule]) == []
    assert validate_row({"country": "XX"}, [rule])[0].code == "not_in_enum"


def test_regex_rule():
    rule = Rule(field="signup_date", type="regex", params={"pattern": r"^\d{4}-\d{2}-\d{2}$"})
    assert validate_row({"signup_date": "2023-01-15"}, [rule]) == []
    assert validate_row({"signup_date": "bad-date"}, [rule])[0].code == "regex_mismatch"


def test_range_rule():
    rule = Rule(field="age", type="range", params={"min": 0, "max": 120})
    assert validate_row({"age": "30"}, [rule]) == []
    assert validate_row({"age": "200"}, [rule])[0].code == "out_of_range"
    assert validate_row({"age": "abc"}, [rule])[0].code == "out_of_range"


def test_multiple_violations_on_one_row():
    rules = [
        Rule(field="full_name", type="required", params={}),
        Rule(field="email", type="email", params={}),
    ]
    violations = validate_row({"full_name": "", "email": "bad"}, rules)
    assert {v.code for v in violations} == {"required", "invalid_email"}


def test_validate_rows_splits_real_sample(project_root, sample_raw_csv):
    schema = load_schema(project_root / "config" / "schema.yaml")
    rules = load_rules(project_root / "config" / "validation_rules.yaml")
    rows = load_csv(sample_raw_csv, schema).rows
    result = validate_rows(rows, rules)
    assert len(result.valid_rows) + len(result.rejected) == len(rows)
    assert len(result.rejected) > 0
