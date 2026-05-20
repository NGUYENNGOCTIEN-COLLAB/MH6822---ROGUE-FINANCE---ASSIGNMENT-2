"""Dataclass models for the three pipeline stages.

Each stage produces an immutable record consumed by the next. The shapes are
deliberately small and JSON-serialisable so the runner can stream them straight
into the report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class ParsedTrade:
    """Module 1 output: one record per raw trade.

    parse_status: SUCCESS | PARTIAL | FAILED
    classification_flag: CONVENTIONAL_DERIVATIVE | NOVEL_INSTRUMENT_NO_TAXONOMY
                       | CLASSIFICATION_AMBIGUOUS
    """

    trade_id: str
    parse_status: str
    asset_class: Optional[str]
    instrument_type: Optional[str]
    use_case: Optional[str]
    classification_flag: str
    parse_errors: list[str] = field(default_factory=list)
    classified_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class UpiLookupResult:
    """Module 2 output.

    status: FOUND | INVALID_ATTRIBUTES | NOT_FOUND | NO_PRODUCT_DEFINITION
    """

    trade_id: str
    status: str
    matched_template: Optional[str]
    upi_code: Optional[str]
    classification_note: Optional[str]
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ComplianceResult:
    """Module 3 output: one record per (trade, regime) pair.

    status: COMPLIANT | NONCOMPLIANT | CONDITIONAL | NOT_APPLICABLE
    reporting_obligation: YES | NO | CONDITIONAL | UNKNOWN
        Separated from status so the audit trail can answer the two
        independent questions "is this trade in scope?" and "does it pass?"
    mandatory_fields_checked: explicit list of which fields were evaluated;
        becomes part of the audit record.
    explanation: plain-English summary of the verdict suitable for a non-
        technical audit consumer (compliance officer, examiner, auditor).
        One sentence, derived from status, error count, and notes.
    """

    trade_id: str
    regime: str
    status: str
    reporting_obligation: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    mandatory_fields_checked: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
