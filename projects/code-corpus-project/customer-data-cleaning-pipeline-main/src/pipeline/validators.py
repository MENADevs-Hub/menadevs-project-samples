"""Validation rule engine driven by config/validation_rules.yaml.

Each field can have a list of rules. Supported rule types: required, email, phone,
regex, range, enum. Format rules (everything except ``required``) pass on empty values
so emptiness is reported once by ``required`` rather than by every rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.config import load_yaml

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_CODES = {
    "required": "required",
    "email": "invalid_email",
    "phone": "invalid_phone",
    "regex": "regex_mismatch",
    "enum": "not_in_enum",
    "range": "out_of_range",
}


class ValidationConfigError(ValueError):
    """Raised when the validation rules config is invalid."""


@dataclass(frozen=True)
class Rule:
    """A single rule bound to a field."""

    field: str
    type: str
    params: dict[str, Any]


@dataclass(frozen=True)
class RuleViolation:
    """A failed rule for a given field."""

    field: str
    rule: str
    code: str


@dataclass
class RejectedRow:
    """A row that failed one or more rules."""

    row: dict[str, str]
    violations: list[RuleViolation]


@dataclass
class ValidationResult:
    """Split of rows into those that passed and those that were rejected."""

    valid_rows: list[dict[str, str]] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _check_required(value: Any, params: dict[str, Any]) -> bool:
    return not _is_empty(value)


def _check_email(value: Any, params: dict[str, Any]) -> bool:
    if _is_empty(value):
        return True
    return bool(EMAIL_RE.match(value.strip()))


def _check_phone(value: Any, params: dict[str, Any]) -> bool:
    if _is_empty(value):
        return True
    digits = re.sub(r"\D", "", value)
    min_digits = params.get("min_digits", 7)
    max_digits = params.get("max_digits", 15)
    return min_digits <= len(digits) <= max_digits


def _check_regex(value: Any, params: dict[str, Any]) -> bool:
    if _is_empty(value):
        return True
    pattern = params.get("pattern", "")
    return bool(re.match(pattern, value.strip()))


def _check_enum(value: Any, params: dict[str, Any]) -> bool:
    if _is_empty(value):
        return True
    return value.strip() in params.get("values", [])


def _check_range(value: Any, params: dict[str, Any]) -> bool:
    if _is_empty(value):
        return True
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    low = params.get("min")
    high = params.get("max")
    if low is not None and number < low:
        return False
    if high is not None and number > high:
        return False
    return True


_CHECKERS = {
    "required": _check_required,
    "email": _check_email,
    "phone": _check_phone,
    "regex": _check_regex,
    "enum": _check_enum,
    "range": _check_range,
}


def load_rules(path: str | Path) -> list[Rule]:
    """Load and validate the field rules from a YAML file."""
    data = load_yaml(path)
    if "rules" not in data:
        raise ValidationConfigError("validation config must contain a 'rules' key")

    rules: list[Rule] = []
    for field_name, field_rules in data["rules"].items():
        for raw in field_rules:
            rule_type = raw.get("type")
            if rule_type not in _CHECKERS:
                raise ValidationConfigError(
                    f"unknown rule type '{rule_type}' for field '{field_name}'"
                )
            params = {key: value for key, value in raw.items() if key != "type"}
            rules.append(Rule(field=field_name, type=rule_type, params=params))
    return rules


def validate_row(row: dict[str, str], rules: list[Rule]) -> list[RuleViolation]:
    """Return all rule violations for a single row."""
    violations: list[RuleViolation] = []
    for rule in rules:
        checker = _CHECKERS[rule.type]
        if not checker(row.get(rule.field), rule.params):
            violations.append(
                RuleViolation(field=rule.field, rule=rule.type, code=_CODES[rule.type])
            )
    return violations


def validate_rows(rows: list[dict[str, str]], rules: list[Rule]) -> ValidationResult:
    """Split rows into valid and rejected based on the rules."""
    result = ValidationResult()
    for row in rows:
        violations = validate_row(row, rules)
        if violations:
            result.rejected.append(RejectedRow(row=row, violations=violations))
        else:
            result.valid_rows.append(row)
    return result
