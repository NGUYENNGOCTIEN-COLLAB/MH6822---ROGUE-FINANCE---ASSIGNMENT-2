"""Module 1: trade parser and instrument classifier.

The parser ingests one raw trade dictionary and emits a ``ParsedTrade`` record.
It is deliberately permissive: every input returns a record. Data-quality
problems are accumulated in ``parse_errors`` and surface via ``parse_status``.

The classifier emits a flag that drives downstream behaviour:

* ``CONVENTIONAL_DERIVATIVE`` - one of the five established asset classes;
  proceed to UPI lookup against the ANNA-DSB Product Definition library.
* ``NOVEL_INSTRUMENT_NO_TAXONOMY`` - a prediction-market or event contract;
  short-circuit Module 2 with ``NO_PRODUCT_DEFINITION`` and route to a
  jurisdictional decision in Module 3 (CONDITIONAL or NOT_APPLICABLE).
* ``CLASSIFICATION_AMBIGUOUS`` - missing / unrecognised metadata; both
  downstream modules treat this as a data-quality failure rather than a
  taxonomy frontier.
"""

from __future__ import annotations

from typing import Any

from .models import ParsedTrade
from .utils import (
    first_present,
    is_present,
    validate_date,
    validate_iso8601_utc,
)


CONVENTIONAL_ASSET_CLASSES = {"Rates", "Credit", "FX", "Equity", "Commodities"}
NOVEL_ASSET_CLASSES = {
    "EventContract",
    "PredictionContract",
    "PredictionMarket",
    "PoliticalRisk",
}

CLASSIFICATION_CONVENTIONAL = "CONVENTIONAL_DERIVATIVE"
CLASSIFICATION_NOVEL = "NOVEL_INSTRUMENT_NO_TAXONOMY"
CLASSIFICATION_AMBIGUOUS = "CLASSIFICATION_AMBIGUOUS"

# Heuristic substrings that route an unknown asset class to NOVEL rather than
# AMBIGUOUS. Picks up "BinaryEvent", "PredictionContract2", etc.
NOVEL_HEURISTIC_TOKENS = ("event", "predict", "binary")


def classify_instrument(trade: dict[str, Any]) -> str:
    """Return the regulatory taxonomy flag for a trade."""
    asset_class = trade.get("asset_class")
    instrument_type = trade.get("instrument_type")

    if not is_present(asset_class) or not is_present(instrument_type):
        return CLASSIFICATION_AMBIGUOUS
    if asset_class in CONVENTIONAL_ASSET_CLASSES:
        return CLASSIFICATION_CONVENTIONAL
    if asset_class in NOVEL_ASSET_CLASSES:
        return CLASSIFICATION_NOVEL

    # Heuristic catch for unknown asset classes that smell novel.
    haystack = f"{asset_class} {instrument_type}".lower()
    if any(token in haystack for token in NOVEL_HEURISTIC_TOKENS):
        return CLASSIFICATION_NOVEL

    return CLASSIFICATION_AMBIGUOUS


# Fields that the runner displays in summaries and the dashboard. Promoted
# eagerly to ``classified_fields`` so downstream code does not have to keep
# the raw dict around in memory if it doesn't need to.
_CLASSIFIED_FIELDS = (
    "notional_currency", "notional_amount",
    "notional_currency_leg1", "notional_amount_leg1",
    "notional_currency_leg2", "notional_amount_leg2",
    "cleared", "uti", "upi", "execution_timestamp",
    "effective_date", "maturity_date", "settlement_date",
    "expiry_date", "expiration_date",
    "action_type", "platform", "platform_type",
    "venue", "platform_classification",
    "reporting_counterparty_lei", "other_counterparty_lei",
)


def _extract_classified_fields(trade: dict[str, Any]) -> dict[str, Any]:
    return {k: trade.get(k) for k in _CLASSIFIED_FIELDS if is_present(trade.get(k))}


def parse_trade(trade: Any) -> ParsedTrade:
    """Parse a single raw trade. Never raises."""
    # Defensive: handle non-dict inputs (None, lists, scalars) without crashing.
    if not isinstance(trade, dict):
        return ParsedTrade(
            trade_id="UNKNOWN_TRADE_ID",
            parse_status="FAILED",
            asset_class=None,
            instrument_type=None,
            use_case=None,
            classification_flag=CLASSIFICATION_AMBIGUOUS,
            parse_errors=[f"trade record is not a JSON object (got {type(trade).__name__})"],
        )

    errors: list[str] = []
    trade_id = trade.get("trade_id")
    if not is_present(trade_id):
        trade_id = "UNKNOWN_TRADE_ID"
        errors.append("trade_id is missing")

    asset_class = trade.get("asset_class")
    instrument_type = trade.get("instrument_type")
    use_case = trade.get("use_case")

    if not is_present(asset_class):
        errors.append("asset_class is missing")
    if not is_present(instrument_type):
        errors.append("instrument_type is missing")
    if not is_present(use_case):
        errors.append("use_case is missing")

    flag = classify_instrument(trade)
    if flag == CLASSIFICATION_AMBIGUOUS and is_present(asset_class):
        errors.append(
            f"classification ambiguous: asset_class {asset_class!r} not on the "
            "conventional or novel whitelist"
        )

    # Timestamp must always be ISO 8601 UTC for both conventional and novel.
    ok, msg = validate_iso8601_utc(trade.get("execution_timestamp"))
    if not ok:
        errors.append(msg)

    # Conventional derivatives must have effective_date and maturity_date.
    # Novel event contracts use settlement_date (event resolution date) instead;
    # absence of maturity_date is therefore not a parse error in the novel case.
    if flag == CLASSIFICATION_CONVENTIONAL:
        for fname in ("effective_date", "maturity_date"):
            ok, msg = validate_date(trade.get(fname), fname)
            if not ok:
                errors.append(msg)
    else:
        # Validate any date-shaped field that *is* present, but don't require it.
        for fname in ("effective_date", "maturity_date", "settlement_date"):
            if is_present(trade.get(fname)):
                ok, msg = validate_date(trade.get(fname), fname)
                if not ok:
                    errors.append(msg)

    if flag == CLASSIFICATION_AMBIGUOUS or trade_id == "UNKNOWN_TRADE_ID":
        parse_status = "FAILED" if errors else "PARTIAL"
    else:
        parse_status = "SUCCESS" if not errors else "PARTIAL"

    return ParsedTrade(
        trade_id=str(trade_id),
        parse_status=parse_status,
        asset_class=asset_class if is_present(asset_class) else None,
        instrument_type=instrument_type if is_present(instrument_type) else None,
        use_case=use_case if is_present(use_case) else None,
        classification_flag=flag,
        parse_errors=errors,
        classified_fields=_extract_classified_fields(trade),
    )


def parse_portfolio(trades: list[Any]) -> list[ParsedTrade]:
    """Parse every record defensively. One bad trade does not poison the batch."""
    return [parse_trade(t) for t in trades]
