"""Validation primitives shared by Modules 1, 2 and 3.

All validators return ``(ok: bool, message: str)``. ``message`` is empty on
success and human-readable on failure. None of them ever raise on input.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Optional


# ISO 4217 alpha-3 currency codes plus precious metals (XAU/XAG/XPT/XPD) and
# selected fund codes that appear in OTC reporting (XBA-XBD test ranges).
ISO_CURRENCY_CODES = {
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BOV",
    "BRL", "BSD", "BTN", "BWP", "BYN", "BZD", "CAD", "CDF", "CHE", "CHF",
    "CHW", "CLF", "CLP", "CNY", "COP", "COU", "CRC", "CUC", "CUP", "CVE",
    "CZK", "DJF", "DKK", "DOP", "DZD", "EGP", "ERN", "ETB", "EUR", "FJD",
    "FKP", "GBP", "GEL", "GHS", "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD",
    "HNL", "HRK", "HTG", "HUF", "IDR", "ILS", "INR", "IQD", "IRR", "ISK",
    "JMD", "JOD", "JPY", "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD",
    "KYD", "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "LYD", "MAD", "MDL",
    "MGA", "MKD", "MMK", "MNT", "MOP", "MRU", "MUR", "MVR", "MWK", "MXN",
    "MXV", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "OMR",
    "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR", "RON", "RSD",
    "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SLE",
    "SOS", "SRD", "SSP", "STN", "SVC", "SYP", "SZL", "THB", "TJS", "TMT",
    "TND", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD", "USN",
    "UYI", "UYU", "UYW", "UZS", "VED", "VES", "VND", "VUV", "WST", "XAF",
    "XAG", "XAU", "XBA", "XBB", "XBC", "XBD", "XCD", "XDR", "XOF", "XPD",
    "XPF", "XPT", "XSU", "XTS", "XUA", "XXX", "YER", "ZAR", "ZMW", "ZWL",
}

# CDE Action Type codes: CFTC Part 43/45, EMIR Refit ITS Annex.
ACTION_TYPES = {
    "NEW", "MODIFY", "CORRECT", "TERMINATE", "ERROR", "REVIVE",
    "POSITION", "VALUATION", "MARGIN_UPDATE",
}

TIMESTAMP_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEI_RE = re.compile(r"^[A-Z0-9]{18}\d{2}$")
UTI_SUFFIX_RE = re.compile(r"^[A-Z0-9-]{1,32}$")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def is_present(value: Any) -> bool:
    """A field is "present" iff it is not None and not the empty string."""
    return value is not None and value != ""


def first_present(mapping: dict[str, Any], names: list[str]) -> Any:
    """Return the value of the first key in *names* that's present."""
    for name in names:
        if is_present(mapping.get(name)):
            return mapping.get(name)
    return None


# ---------------------------------------------------------------------------
# Date / time / currency
# ---------------------------------------------------------------------------

def validate_iso8601_utc(value: Optional[str]) -> tuple[bool, str]:
    if not is_present(value):
        return False, "execution_timestamp is missing"
    if not isinstance(value, str) or not TIMESTAMP_UTC_RE.match(value):
        return False, "execution_timestamp must use ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ"
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        return False, f"execution_timestamp is not a valid calendar timestamp: {exc}"
    return True, ""


def validate_date(value: Optional[str], field_name: str) -> tuple[bool, str]:
    if not is_present(value):
        return False, f"{field_name} is missing"
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False, f"{field_name} must use YYYY-MM-DD format (got {value!r})"
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        return False, f"{field_name} is not a valid calendar date: {exc}"
    return True, ""


def validate_currency(code: Optional[str]) -> tuple[bool, str]:
    if not is_present(code):
        return False, "currency code is missing"
    if not isinstance(code, str) or len(code) != 3 or code != code.upper():
        return False, f"currency code {code!r} must be a three-letter uppercase ISO 4217 code"
    if code not in ISO_CURRENCY_CODES:
        return False, f"currency code {code!r} is not in the ISO 4217 validation set"
    return True, ""


def validate_currency_pair(pair: Optional[str]) -> tuple[bool, str]:
    if not is_present(pair):
        return False, "currency pair is missing"
    if not isinstance(pair, str) or "/" not in pair:
        return False, f"currency pair {pair!r} must use BASE/QUOTE format"
    base, quote = pair.split("/", 1)
    ok_b, msg_b = validate_currency(base)
    if not ok_b:
        return False, f"currency pair {pair!r} base leg invalid: {msg_b}"
    ok_q, msg_q = validate_currency(quote)
    if not ok_q:
        return False, f"currency pair {pair!r} quote leg invalid: {msg_q}"
    return True, ""


# ---------------------------------------------------------------------------
# LEI (ISO 17442) - MOD 97-10 check digits per ISO 7064
# ---------------------------------------------------------------------------

def _char_to_num(ch: str) -> str:
    if ch.isdigit():
        return ch
    return str(ord(ch) - ord("A") + 10)


def compute_lei_check_digits(body18: str) -> str:
    """Compute ISO 7064 MOD 97-10 check digits for an 18-character LEI body."""
    if len(body18) != 18 or not re.fullmatch(r"[A-Z0-9]{18}", body18):
        raise ValueError("LEI body must be exactly 18 uppercase alphanumeric characters")
    numeric = "".join(_char_to_num(ch) for ch in body18) + "00"
    return f"{98 - (int(numeric) % 97):02d}"


def validate_lei(lei: Optional[str]) -> tuple[bool, str]:
    if not is_present(lei):
        return False, "LEI is missing"
    if not isinstance(lei, str):
        return False, "LEI must be a string"
    if not LEI_RE.fullmatch(lei):
        return False, (
            f"LEI {lei!r} must be 20 characters: 18 uppercase alphanumeric "
            "plus 2 numeric check digits"
        )
    expected = compute_lei_check_digits(lei[:18])
    if expected != lei[18:]:
        return False, f"LEI {lei!r} has invalid MOD 97-10 check digits; expected {expected}"
    return True, ""


# ---------------------------------------------------------------------------
# UTI (ISO 23897)
# ---------------------------------------------------------------------------

def validate_uti(uti: Optional[str], reporting_lei: Optional[str]) -> tuple[bool, str]:
    """Validate a UTI per ISO 23897.

    Rules:
      - Total length <= 52 characters
      - First 20 characters form a syntactically valid LEI namespace
      - Namespace must equal the reporting counterparty's LEI (when supplied)
      - Suffix is uppercase letters, digits, or hyphens, length 1-32
    """
    if not is_present(uti):
        return False, "UTI is missing"
    if not isinstance(uti, str):
        return False, "UTI must be a string"
    if len(uti) > 52:
        return False, f"UTI exceeds 52-character maximum length (got {len(uti)})"
    if len(uti) <= 20:
        return False, "UTI must contain a 20-character namespace LEI followed by a suffix"

    namespace, suffix = uti[:20], uti[20:]
    if not LEI_RE.fullmatch(namespace):
        return False, (
            "UTI namespace must be 20 characters: 18 uppercase alphanumeric "
            "plus 2 numeric check digits"
        )
    if reporting_lei is not None and namespace != reporting_lei:
        return False, "UTI namespace LEI does not match reporting_counterparty_lei"
    if not UTI_SUFFIX_RE.fullmatch(suffix):
        return False, (
            "UTI suffix must contain only uppercase letters, digits, and hyphens "
            "and be 1-32 characters long"
        )
    return True, ""


# ---------------------------------------------------------------------------
# Action type
# ---------------------------------------------------------------------------

def validate_action_type(value: Optional[str]) -> tuple[bool, str]:
    if not is_present(value):
        return False, "action_type is missing"
    if value not in ACTION_TYPES:
        return False, f"action_type {value!r} is not a recognised CDE action code"
    return True, ""
