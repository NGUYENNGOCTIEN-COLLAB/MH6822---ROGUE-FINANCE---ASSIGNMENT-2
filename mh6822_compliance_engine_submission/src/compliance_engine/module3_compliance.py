"""Module 3: multi-jurisdictional compliance checker.

For each (trade, regime) pair returns a ``ComplianceResult`` with:

* ``status``: COMPLIANT | NONCOMPLIANT | CONDITIONAL | NOT_APPLICABLE
* ``reporting_obligation``: YES | NO | CONDITIONAL | UNKNOWN
* ``mandatory_fields_checked``: explicit audit trail
* ``errors``: per-field problems found
* ``warnings``: deprecated-but-acceptable signals (e.g. LIBOR)
* ``notes``: regulatory citations and context

Regimes: CFTC (Dodd-Frank Title VII), EMIR Refit (April 2024 ITS), ASIC DTR
(October 2024) and MAS SF(RDC)R (October 2024).

The CFTC ``CONDITIONAL`` flag is reserved for trades whose reportability is
the subject of an active rulemaking. The canonical case is a Kalshi-listed
event contract, where CFTC ANPR 91 FR 12516 (RIN 3038-AF65, March 2026) is
considering whether political-outcome contracts fall under §40.11. The flag
is triggered by the structured ``platform_type == "CFTC_REGULATED_DCM"``
field rather than substring search, so it works on any DCM not just Kalshi.
"""

from __future__ import annotations

from typing import Any

from .models import ComplianceResult, ParsedTrade, UpiLookupResult
from .module1_parser import (
    CLASSIFICATION_CONVENTIONAL,
    CLASSIFICATION_NOVEL,
)
from .utils import (
    first_present,
    is_present,
    validate_action_type,
    validate_currency,
    validate_date,
    validate_iso8601_utc,
    validate_lei,
    validate_uti,
)


# Common Data Element fields the regimes share.
CDE_REQUIRED_FIELDS = [
    "uti",
    "reporting_counterparty_lei",
    "other_counterparty_lei",
    "execution_timestamp",
    "effective_date",
    "maturity_or_expiry_date",
    "notional_currency",
    "notional_amount",
    "action_type",
    "cleared",
]

# EMIR / ASIC / MAS additionally require collateral-level fields per trade.
COLLATERAL_FIELDS = [
    "collateral_portfolio_code",
    "initial_margin_posted",
    "variation_margin_posted",
]

# CFTC-regulated DCM trigger for event contracts. Reads the structured
# platform_type enum, falling back to legacy venue/platform fields if absent.
CFTC_DCM_PLATFORM_TYPES = {"CFTC_REGULATED_DCM", "DCM"}

# CFTC ANPR citation for event contracts on a DCM.
# Verified against the Federal Register: Document No. 2026-05105.
CFTC_EVENT_NOTE = (
    "Event contract executed on a CFTC-regulated DCM. Reporting treatment is "
    "CONDITIONAL pending the CFTC Advance Notice of Proposed Rulemaking on "
    "Prediction Markets (RIN 3038-AF65, 91 FR 12516, Federal Register "
    "Document No. 2026-05105, March 16 2026; comment period closed April 30 "
    "2026). The rulemaking package is cross-referenced with CFTC Press "
    "Release 9194-26, CFTC Press Release 9193-26, and CFTC Staff Letter No. "
    "26-08 (Prediction Markets Advisory). Manual review required."
)

# Notes for non-CFTC regimes when the trade is a novel event contract.
EMIR_EVENT_NOTE = (
    "Event contract not currently classified as an OTC derivative under EMIR "
    "Refit (April 2024 ITS). Where the venue is unauthorised in the EU, the "
    "contract typically falls under national gambling regulation (e.g. § 4(1) "
    "GlüStV 2021 in Germany, ANJ enforcement in France) rather than financial "
    "reporting. Polymarket has been blocked by ANJ (France) since November "
    "2024."
)

ASIC_EVENT_NOTE = (
    "Event contract not within the scope of the ASIC Derivative Transaction "
    "Rules. ASIC has not made a determination that prediction-market event "
    "contracts are reportable derivatives under the Corporations Act 2001."
)

MAS_EVENT_NOTE = (
    "Event contract not within the scope of the MAS SF(RDC)R 2013 reporting "
    "model used here. The correct Singapore OTC derivatives reporting source "
    "is MAS Guidelines SFA 06A-G01 to the SF(RDC)R 2013 (May 2024); MAS "
    "Notice SFA 04-N18 is not the OTC derivatives reporting source because it "
    "concerns cross-border arrangements with foreign offices. Public materials "
    "frame Polymarket-style activity in Singapore through the Gambling "
    "Regulatory Authority and the Gambling Control Act 2022: section 20(3) "
    "addresses gambling with unlawful or unlicensed gambling service providers. "
    "Manual legal classification is required before treating such activity as "
    "MAS-reportable derivatives data."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _explain(status: str, regime: str, errors: list[str], notes: list[str]) -> str:
    """Build a one-sentence plain-English audit summary."""
    if status == "COMPLIANT":
        return (
            f"All mandatory {regime} reporting fields validated; trade is "
            "ready for SDR submission."
        )
    if status == "CONDITIONAL":
        return (
            f"Trade is in scope of {regime} but reporting treatment is "
            "subject to active rulemaking; manual review required before "
            "SDR submission."
        )
    if status == "NOT_APPLICABLE":
        return (
            f"Trade falls outside the {regime} reporting perimeter; no "
            "submission required under the cited rules."
        )
    if status == "NONCOMPLIANT":
        n = len(errors)
        if n == 0:
            return f"Trade fails {regime} compliance check; review the audit trail."
        primary_field = errors[0].split(":", 1)[0].strip() if ":" in errors[0] else "primary check"
        if n == 1:
            return f"Trade fails {regime} on {primary_field}; remediate before resubmission."
        return (
            f"Trade fails {regime} on {n} fields (first: {primary_field}); "
            "remediate all flagged fields before resubmission."
        )
    return f"{regime} returned status {status}."


def _field_error(field: str, message: str) -> str:
    return f"{field}: {message}"


def _is_cftc_dcm(raw_trade: dict[str, Any]) -> bool:
    """Detect a CFTC-regulated DCM via structured field, with venue fallback."""
    if raw_trade.get("platform_type") in CFTC_DCM_PLATFORM_TYPES:
        return True
    # Fall back to legacy venue / platform_classification substring (covers
    # portfolios that don't use the structured enum).
    venue = (raw_trade.get("venue") or "").upper()
    classification = (raw_trade.get("platform_classification") or "").upper()
    if "DCM" in venue or "DCM" in classification:
        return True
    return False


def _validate_common_fields(
    raw_trade: dict[str, Any],
    upi_result: UpiLookupResult,
    require_collateral: bool,
) -> tuple[list[str], list[str], list[str]]:
    """Run the CDE field checks. Returns (errors, warnings, fields_checked)."""
    errors: list[str] = []
    warnings: list[str] = list(upi_result.warnings)
    checked = list(CDE_REQUIRED_FIELDS) + (
        list(COLLATERAL_FIELDS) if require_collateral else []
    )

    # UPI: present in raw or produced by lookup.
    raw_upi = raw_trade.get("upi")
    if not is_present(raw_upi) and not is_present(upi_result.upi_code):
        errors.append(_field_error(
            "upi", f"mandatory UPI unavailable; lookup status={upi_result.status}",
        ))
    if upi_result.status in {"INVALID_ATTRIBUTES", "NOT_FOUND"}:
        errors.append(_field_error(
            "upi", f"UPI lookup failed with status {upi_result.status}",
        ))
        for vmsg in upi_result.validation_errors:
            errors.append(_field_error("upi_attribute", vmsg))

    # LEI on both sides.
    ok, msg = validate_lei(raw_trade.get("reporting_counterparty_lei"))
    if not ok:
        errors.append(_field_error("reporting_counterparty_lei", msg))
    ok, msg = validate_lei(raw_trade.get("other_counterparty_lei"))
    if not ok:
        errors.append(_field_error("other_counterparty_lei", msg))

    # UTI.
    ok, msg = validate_uti(
        raw_trade.get("uti"),
        raw_trade.get("reporting_counterparty_lei"),
    )
    if not ok:
        errors.append(_field_error("uti", msg))

    # Execution timestamp.
    ok, msg = validate_iso8601_utc(raw_trade.get("execution_timestamp"))
    if not ok:
        errors.append(_field_error("execution_timestamp", msg))

    # Effective date.
    ok, msg = validate_date(raw_trade.get("effective_date"), "effective_date")
    if not ok:
        errors.append(_field_error("effective_date", msg))

    # Maturity / expiry / settlement date - try several field names.
    expiry = first_present(
        raw_trade,
        ["maturity_date", "expiry_date", "expiration_date", "settlement_date"],
    )
    ok, msg = validate_date(expiry, "maturity_or_expiry_date")
    if not ok:
        errors.append(_field_error("maturity_or_expiry_date", msg))

    # Notional currency: single field or per-leg pair (cross-currency swap).
    nc = raw_trade.get("notional_currency")
    leg_ccys = [raw_trade.get("notional_currency_leg1"), raw_trade.get("notional_currency_leg2")]
    if is_present(nc):
        ok, msg = validate_currency(nc)
        if not ok:
            errors.append(_field_error("notional_currency", msg))
    elif all(is_present(c) for c in leg_ccys):
        for idx, val in enumerate(leg_ccys, 1):
            ok, msg = validate_currency(val)
            if not ok:
                errors.append(_field_error(f"notional_currency_leg{idx}", msg))
    else:
        errors.append(_field_error(
            "notional_currency", "mandatory notional currency is missing "
            "(neither single field nor leg1/leg2 pair present)",
        ))

    # Notional amount: same single-or-pair pattern.
    na = raw_trade.get("notional_amount")
    leg_amts = [raw_trade.get("notional_amount_leg1"), raw_trade.get("notional_amount_leg2")]
    if is_present(na):
        if isinstance(na, bool) or not isinstance(na, (int, float)) or na <= 0:
            errors.append(_field_error("notional_amount", f"must be a positive number, got {na!r}"))
    elif all(is_present(a) for a in leg_amts):
        for idx, val in enumerate(leg_amts, 1):
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
                errors.append(_field_error(
                    f"notional_amount_leg{idx}", f"must be a positive number, got {val!r}",
                ))
    else:
        errors.append(_field_error(
            "notional_amount", "mandatory notional amount is missing",
        ))

    # Action type.
    ok, msg = validate_action_type(raw_trade.get("action_type"))
    if not ok:
        errors.append(_field_error("action_type", msg))

    # Cleared flag must be a real boolean, not a string "yes"/"no".
    cleared = raw_trade.get("cleared")
    if cleared is None or "cleared" not in raw_trade:
        errors.append(_field_error("cleared", "mandatory cleared indicator is missing"))
    elif not isinstance(cleared, bool):
        errors.append(_field_error(
            "cleared", f"must be boolean (got {type(cleared).__name__}: {cleared!r})",
        ))

    if require_collateral:
        for f in COLLATERAL_FIELDS:
            v = raw_trade.get(f)
            if v is None:
                errors.append(_field_error(f, "mandatory collateral field is missing or null"))
            elif f != "collateral_portfolio_code":
                # Margin numbers must be numeric. Zero is allowed; negative is not.
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    errors.append(_field_error(f, f"must be numeric (got {type(v).__name__}: {v!r})"))
                elif v < 0:
                    errors.append(_field_error(f, f"must not be negative (got {v})"))

    return sorted(set(errors)), sorted(set(warnings)), checked


# ---------------------------------------------------------------------------
# Per-regime checkers
# ---------------------------------------------------------------------------

def check_cftc_compliance(
    parsed: ParsedTrade,
    upi: UpiLookupResult,
    raw: dict[str, Any],
) -> ComplianceResult:
    if parsed.classification_flag == CLASSIFICATION_NOVEL:
        if _is_cftc_dcm(raw):
            errs: list[str] = []
            notes = [CFTC_EVENT_NOTE, upi.classification_note or ""]
            return ComplianceResult(
                trade_id=parsed.trade_id,
                regime="CFTC",
                status="CONDITIONAL",
                reporting_obligation="CONDITIONAL",
                notes=notes,
                mandatory_fields_checked=["platform_type", "asset_class", "classification_flag"],
                explanation=_explain("CONDITIONAL", "CFTC", errs, notes),
            )
        notes = [
            "Event contract not executed on a CFTC-regulated DCM; "
            "outside the CFTC reporting perimeter.",
            upi.classification_note or "",
        ]
        return ComplianceResult(
            trade_id=parsed.trade_id,
            regime="CFTC",
            status="NOT_APPLICABLE",
            reporting_obligation="NO",
            notes=notes,
            mandatory_fields_checked=["platform_type", "venue", "platform_classification"],
            explanation=_explain("NOT_APPLICABLE", "CFTC", [], notes),
        )

    if parsed.classification_flag != CLASSIFICATION_CONVENTIONAL:
        errs = ["classification: cannot determine CFTC obligation for ambiguous instrument"]
        return ComplianceResult(
            trade_id=parsed.trade_id,
            regime="CFTC",
            status="NONCOMPLIANT",
            reporting_obligation="UNKNOWN",
            errors=errs,
            explanation=_explain("NONCOMPLIANT", "CFTC", errs, []),
        )

    errors, warnings, checked = _validate_common_fields(raw, upi, require_collateral=False)
    if parsed.parse_errors:
        errors.extend(_field_error("parse", e) for e in parsed.parse_errors)
    status = "COMPLIANT" if not errors else "NONCOMPLIANT"
    final_errors = sorted(set(errors))
    return ComplianceResult(
        trade_id=parsed.trade_id,
        regime="CFTC",
        status=status,
        reporting_obligation="YES",
        errors=final_errors,
        warnings=warnings,
        mandatory_fields_checked=checked,
        explanation=_explain(status, "CFTC", final_errors, []),
    )


def _check_collateral_regime(
    parsed: ParsedTrade,
    upi: UpiLookupResult,
    raw: dict[str, Any],
    regime: str,
    event_note: str,
) -> ComplianceResult:
    """Shared body for EMIR / ASIC / MAS checks."""
    if parsed.classification_flag == CLASSIFICATION_NOVEL:
        notes = [event_note, upi.classification_note or ""]
        return ComplianceResult(
            trade_id=parsed.trade_id,
            regime=regime,
            status="NOT_APPLICABLE",
            reporting_obligation="NO",
            notes=notes,
            mandatory_fields_checked=["asset_class", "classification_flag"],
            explanation=_explain("NOT_APPLICABLE", regime, [], notes),
        )

    if parsed.classification_flag != CLASSIFICATION_CONVENTIONAL:
        errs = [f"classification: cannot determine {regime} obligation for ambiguous instrument"]
        return ComplianceResult(
            trade_id=parsed.trade_id,
            regime=regime,
            status="NONCOMPLIANT",
            reporting_obligation="UNKNOWN",
            errors=errs,
            explanation=_explain("NONCOMPLIANT", regime, errs, []),
        )

    errors, warnings, checked = _validate_common_fields(raw, upi, require_collateral=True)
    if parsed.parse_errors:
        errors.extend(_field_error("parse", e) for e in parsed.parse_errors)
    status = "COMPLIANT" if not errors else "NONCOMPLIANT"
    final_errors = sorted(set(errors))
    return ComplianceResult(
        trade_id=parsed.trade_id,
        regime=regime,
        status=status,
        reporting_obligation="YES",
        errors=final_errors,
        warnings=warnings,
        mandatory_fields_checked=checked,
        explanation=_explain(status, regime, final_errors, []),
    )


def check_emir_compliance(parsed, upi, raw):
    return _check_collateral_regime(parsed, upi, raw, "EMIR", EMIR_EVENT_NOTE)


def check_asic_compliance(parsed, upi, raw):
    return _check_collateral_regime(parsed, upi, raw, "ASIC", ASIC_EVENT_NOTE)


def check_mas_compliance(parsed, upi, raw):
    return _check_collateral_regime(parsed, upi, raw, "MAS", MAS_EVENT_NOTE)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

REGIME_CHECKERS = {
    "CFTC": check_cftc_compliance,
    "EMIR": check_emir_compliance,
    "ASIC": check_asic_compliance,
    "MAS": check_mas_compliance,
}


def check_compliance(
    parsed: ParsedTrade,
    upi: UpiLookupResult,
    raw_trade: dict[str, Any],
    regimes: list[str],
) -> dict[str, ComplianceResult]:
    out: dict[str, ComplianceResult] = {}
    for r in regimes:
        norm = r.strip().upper()
        if norm in REGIME_CHECKERS:
            out[norm] = REGIME_CHECKERS[norm](parsed, upi, raw_trade)
        else:
            errs = [f"regime {r!r} not implemented"]
            out[norm] = ComplianceResult(
                trade_id=parsed.trade_id,
                regime=norm,
                status="NOT_IMPLEMENTED",
                reporting_obligation="UNKNOWN",
                errors=errs,
                explanation=f"Regime {norm} is not yet implemented in this engine; no verdict produced.",
            )
    return out
