"""Field normalizers driven by config/pipeline.yaml.

Each normalizer is idempotent: applying it twice yields the same result as applying it
once. Options (phone country code, name casing, postal casing) come from the
``normalization`` section of pipeline.yaml.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.config import load_yaml


@dataclass(frozen=True)
class NormalizationOptions:
    """Normalization behavior, loaded from pipeline.yaml."""

    phone_default_country_code: str = "1"
    name_title_case: bool = True
    name_collapse_whitespace: bool = True
    postal_uppercase: bool = True

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> NormalizationOptions:
        phone = data.get("phone", {}) or {}
        name = data.get("name", {}) or {}
        postal = data.get("postal_code", {}) or {}
        return cls(
            phone_default_country_code=str(phone.get("default_country_code", "1")),
            name_title_case=bool(name.get("title_case", True)),
            name_collapse_whitespace=bool(name.get("collapse_whitespace", True)),
            postal_uppercase=bool(postal.get("uppercase", True)),
        )


def load_normalization_options(path: str | Path) -> NormalizationOptions:
    """Load the normalization options from pipeline.yaml."""
    data = load_yaml(path)
    return NormalizationOptions.from_config(data.get("normalization", {}) or {})


def normalize_whitespace(value: str) -> str:
    """Collapse runs of whitespace into single spaces and strip the ends."""
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str | None, options: NormalizationOptions) -> str:
    if value is None:
        return ""
    text = normalize_whitespace(value) if options.name_collapse_whitespace else value.strip()
    if options.name_title_case:
        text = text.title()
    return text


def normalize_phone(value: str | None, options: NormalizationOptions) -> str:
    """Normalize a phone number to a ``+<digits>`` form.

    If the value already starts with ``+`` the digits are kept as-is; otherwise the
    default country code is prepended.
    """
    if value is None:
        return ""
    stripped = value.strip()
    if stripped == "":
        return ""
    digits = re.sub(r"\D", "", stripped)
    if digits == "":
        return ""
    if stripped.startswith("+"):
        return "+" + digits
    return "+" + options.phone_default_country_code + digits


def normalize_postal(value: str | None, options: NormalizationOptions) -> str:
    if value is None:
        return ""
    text = normalize_whitespace(value)
    return text.upper() if options.postal_uppercase else text


def normalize_email(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def normalize_row(row: dict[str, str], options: NormalizationOptions) -> dict[str, str]:
    """Return a new row with known fields normalized."""
    result = dict(row)
    if "full_name" in result:
        result["full_name"] = normalize_name(result["full_name"], options)
    if "phone" in result:
        result["phone"] = normalize_phone(result["phone"], options)
    if "postal_code" in result:
        result["postal_code"] = normalize_postal(result["postal_code"], options)
    if "email" in result:
        result["email"] = normalize_email(result["email"])
    return result
