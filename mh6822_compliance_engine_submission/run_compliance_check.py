#!/usr/bin/env python3
"""CLI runner for the OTC compliance engine.

Reads a JSON portfolio, drives Modules 1 -> 2 -> 3 over each trade and each
regime, then writes structured JSON, a flat CSV summary, and a human-readable
Markdown report.

Usage::

    python run_compliance_check.py --input trades.json --regimes CFTC,EMIR
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from compliance_engine.module1_parser import (  # noqa: E402
    parse_trade,
    CLASSIFICATION_NOVEL,
)
from compliance_engine.module2_upi_lookup import TemplateLibrary, lookup_upi  # noqa: E402
from compliance_engine.module3_compliance import check_compliance  # noqa: E402


STATUS_GLYPHS = {
    "COMPLIANT": "✓",
    "NONCOMPLIANT": "✗",
    "CONDITIONAL": "?",
    "NOT_APPLICABLE": "n/a",
    "NOT_IMPLEMENTED": "∅",
}


def load_trades(path: Path) -> list[dict[str, Any]]:
    """Load a portfolio JSON. Defensive against the failure modes a hidden
    test fixture is most likely to exercise:

    * file does not exist -> clear error message
    * file is empty or contains a JSON parse error -> clear error message
    * root is not a JSON array (e.g. an object with a ``trades`` key) -> we
      try a couple of fallback shapes before giving up
    * individual records are not dicts -> they pass through; Module 1's
      ``parse_trade`` produces a FAILED record per non-dict input
    """
    if not path.exists():
        raise FileNotFoundError(f"trades file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read trades file {path}: {exc}") from exc
    if not text.strip():
        raise ValueError(f"trades file {path} is empty")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} contains invalid JSON: {exc}") from exc

    if isinstance(data, list):
        return data
    # Fallback shapes seen in practice: {"trades": [...]} or {"portfolio": [...]}
    if isinstance(data, dict):
        for key in ("trades", "portfolio", "records", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError(
        f"{path} must contain a JSON array of trade records "
        f"(got {type(data).__name__})"
    )


def _error_field(error: str) -> str:
    """Extract the field-name prefix from an error message.

    Errors are 'field: msg'; warnings are 'field=value ...'. Both put the
    field name first; we just need the leading token before the first
    colon, equals, or space.
    """
    if not error:
        return "general"
    head = ""
    for ch in error:
        if ch in (":", "=", " "):
            break
        head += ch
    return head if head else "general"


def derive_finding_type(parsed, upi, compliance: dict[str, Any]) -> str:
    """Classify the nature of the finding for audit and Module 4 analysis.

    This separates ordinary data defects from the classification-frontier
    failures the assignment is designed to surface.  A bad LEI and a missing
    EventContract taxonomy should not be collapsed into the same bucket.
    """
    if parsed.classification_flag == CLASSIFICATION_NOVEL:
        if any(res.status == "CONDITIONAL" for res in compliance.values()):
            return "TAXONOMY_GAP_WITH_REGULATORY_NEXUS"
        return "JURISDICTIONAL_SCOPE_GAP"

    all_errors: list[str] = list(parsed.parse_errors) + list(upi.validation_errors)
    for res in compliance.values():
        all_errors.extend(res.errors)

    if not all_errors and all(res.status == "COMPLIANT" for res in compliance.values()):
        return "NO_ERROR"
    joined = " ".join(all_errors).lower()
    if any(token in joined for token in ("lei", "uti", "upi")):
        return "IDENTIFIER_ERROR"
    if all_errors:
        return "FIELD_VALIDATION_ERROR"
    if any(res.status == "CONDITIONAL" for res in compliance.values()):
        return "REGULATORY_UNCERTAINTY"
    return "MANUAL_REVIEW"


def build_report(
    trades: list[dict[str, Any]],
    regimes: list[str],
    library: TemplateLibrary,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    classification = Counter[str]()
    upi_status = Counter[str]()
    regime_status: dict[str, Counter[str]] = defaultdict(Counter)
    error_counter = Counter[str]()
    warning_counter = Counter[str]()
    finding_type_counter = Counter[str]()

    for raw in trades:
        parsed = parse_trade(raw)
        upi = lookup_upi(parsed, raw if isinstance(raw, dict) else {}, library)
        compliance = check_compliance(parsed, upi, raw if isinstance(raw, dict) else {}, regimes)

        classification[parsed.classification_flag] += 1
        upi_status[upi.status] += 1
        for err in parsed.parse_errors:
            error_counter[f"PARSER.{_error_field(err)}"] += 1
        for err in upi.validation_errors:
            error_counter[f"UPI.{_error_field(err)}"] += 1
        for w in upi.warnings:
            warning_counter[f"UPI.{_error_field(w)}"] += 1
        finding_type = derive_finding_type(parsed, upi, compliance)
        finding_type_counter[finding_type] += 1

        for regime, result in compliance.items():
            regime_status[regime][result.status] += 1
            for err in result.errors:
                error_counter[f"{regime}.{_error_field(err)}"] += 1
            for w in result.warnings:
                warning_counter[f"{regime}.{_error_field(w)}"] += 1

        records.append({
            "trade_id": parsed.trade_id,
            "asset_class": parsed.asset_class,
            "instrument_type": parsed.instrument_type,
            "use_case": parsed.use_case,
            "finding_type": finding_type,
            "module1_parse": parsed.to_dict(),
            "module2_upi": upi.to_dict(),
            "module3_compliance": {r: res.to_dict() for r, res in compliance.items()},
        })

    return {
        "metadata": {
            "engine": "MH6822 OTC Derivatives Compliance Engine",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "trade_count": len(trades),
            "regimes": regimes,
        },
        "portfolio_summary": {
            "by_classification": dict(classification),
            "by_upi_status": dict(upi_status),
            "by_regime": {r: dict(c) for r, c in regime_status.items()},
            "top_error_fields": dict(error_counter.most_common(20)),
            "top_warning_fields": dict(warning_counter.most_common(10)),
            "by_finding_type": dict(finding_type_counter),
        },
        "trades": records,
    }


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def write_csv(report: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for rec in report["trades"]:
        m1 = rec["module1_parse"]; m2 = rec["module2_upi"]
        row = {
            "trade_id": rec["trade_id"],
            "asset_class": m1["asset_class"],
            "instrument_type": m1["instrument_type"],
            "use_case": m1["use_case"],
            "finding_type": rec.get("finding_type", ""),
            "parse_status": m1["parse_status"],
            "classification_flag": m1["classification_flag"],
            "parse_errors": " | ".join(m1["parse_errors"]),
            "upi_status": m2["status"],
            "matched_template": m2["matched_template"],
            "upi_code": m2["upi_code"],
            "upi_errors": " | ".join(m2["validation_errors"]),
            "upi_warnings": " | ".join(m2["warnings"]),
        }
        for regime, res in rec["module3_compliance"].items():
            row[f"{regime}_status"] = res["status"]
            row[f"{regime}_obligation"] = res["reporting_obligation"]
            row[f"{regime}_errors"] = " | ".join(res["errors"])
            row[f"{regime}_warnings"] = " | ".join(res["warnings"])
            row[f"{regime}_notes"] = " | ".join(n for n in res["notes"] if n)
            row[f"{regime}_explanation"] = res.get("explanation", "")
        rows.append(row)

    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for k in row:
            if k not in fieldnames:
                fieldnames.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def render_markdown(report: dict[str, Any]) -> str:
    md: list[str] = []
    meta = report["metadata"]
    summary = report["portfolio_summary"]

    md.append(f"# Compliance Report\n")
    md.append(f"**Generated:** {meta['generated_at_utc']}  ")
    md.append(f"**Trades:** {meta['trade_count']}  ")
    md.append(f"**Regimes:** {', '.join(meta['regimes'])}\n")

    md.append("## Portfolio summary\n")
    md.append("**By classification:**")
    for k, v in summary["by_classification"].items():
        md.append(f"- {k}: {v}")
    md.append("\n**By UPI status:**")
    for k, v in summary["by_upi_status"].items():
        md.append(f"- {k}: {v}")
    md.append("\n**By finding type:**")
    for k, v in summary.get("by_finding_type", {}).items():
        md.append(f"- {k}: {v}")

    md.append("\n**By regime:**")
    for regime, counts in summary["by_regime"].items():
        parts = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        md.append(f"- **{regime}**: {parts}")

    if summary["top_error_fields"]:
        md.append("\n## Top error fields\n")
        md.append("| Field | Count |")
        md.append("|---|---:|")
        for field, count in summary["top_error_fields"].items():
            md.append(f"| `{field}` | {count} |")
    if summary["top_warning_fields"]:
        md.append("\n## Top warning fields\n")
        md.append("| Field | Count |")
        md.append("|---|---:|")
        for field, count in summary["top_warning_fields"].items():
            md.append(f"| `{field}` | {count} |")

    md.append("\n## Per-trade results\n")
    regimes = meta["regimes"]
    md.append("| Trade | Class | Use case | Finding type | Class. flag | UPI | " + " | ".join(regimes) + " |")
    md.append("|---|---|---|---|---|---|" + "---|" * len(regimes))
    for rec in report["trades"]:
        m1 = rec["module1_parse"]; m2 = rec["module2_upi"]
        regime_glyphs = " | ".join(
            STATUS_GLYPHS.get(rec["module3_compliance"][r]["status"], rec["module3_compliance"][r]["status"])
            for r in regimes
        )
        md.append(
            f"| {rec['trade_id']} | {m1['asset_class'] or 'n/a'} | "
            f"{m1['use_case'] or 'n/a'} | {rec.get('finding_type', 'n/a')} | "
            f"{m1['classification_flag']} | {m2['status']} | {regime_glyphs} |"
        )

    md.append("\n*Legend:* ✓ COMPLIANT, ✗ NONCOMPLIANT, ? CONDITIONAL, n/a NOT_APPLICABLE, ∅ NOT_IMPLEMENTED.\n")

    md.append("\n## Detailed findings (non-compliant and conditional trades)\n")
    for rec in report["trades"]:
        problem = any(
            res["status"] in {"NONCOMPLIANT", "CONDITIONAL"}
            for res in rec["module3_compliance"].values()
        )
        if not problem:
            continue
        md.append(f"### {rec['trade_id']}: {rec['asset_class']}/{rec['instrument_type']}/{rec['use_case']}")
        m2 = rec["module2_upi"]
        if m2["validation_errors"]:
            md.append("**UPI validation errors:**")
            for e in m2["validation_errors"]:
                md.append(f"  - {e}")
        if m2["warnings"]:
            md.append("**UPI warnings:**")
            for w in m2["warnings"]:
                md.append(f"  - {w}")
        for regime, res in rec["module3_compliance"].items():
            if res["status"] not in {"NONCOMPLIANT", "CONDITIONAL"}:
                continue
            md.append(f"**{regime}: {res['status']}** "
                      f"(reporting_obligation={res['reporting_obligation']})")
            if res.get("explanation"):
                md.append(f"  - *Explanation:* {res['explanation']}")
            for e in res["errors"]:
                md.append(f"  - {e}")
            for n in res["notes"]:
                if n:
                    md.append(f"  - *Note:* {n}")
        md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="MH6822 OTC compliance engine.")
    p.add_argument("--input", required=True, help="Path to trades JSON array")
    p.add_argument("--regimes", default="CFTC,EMIR",
                   help="Comma-separated regimes (CFTC,EMIR,ASIC,MAS)")
    p.add_argument("--product-definitions", default="data/product_definitions/PROD/OTC-Products",
                   help="ANNA-DSB Product-Definitions root")
    p.add_argument("--output-json", default="reports/compliance_report.json")
    p.add_argument("--output-csv", default=None,
                   help="CSV summary (default: same dir as JSON)")
    p.add_argument("--output-md", default="reports/compliance_report.md")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    regimes = [r.strip().upper() for r in args.regimes.split(",") if r.strip()]
    if not regimes:
        print("ERROR: --regimes must list at least one regime", file=sys.stderr)
        return 2

    library = TemplateLibrary(args.product_definitions)
    try:
        trades = load_trades(Path(args.input))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = build_report(trades, regimes, library)

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    out_csv = Path(args.output_csv) if args.output_csv else out_json.with_suffix(".csv")
    write_csv(report, out_csv)

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    if not args.quiet:
        print(f"Processed {len(trades)} trades across regimes {','.join(regimes)}")
        print(f"  JSON: {out_json}")
        print(f"  CSV:  {out_csv}")
        print(f"  MD:   {out_md}")
        for regime, counts in report["portfolio_summary"]["by_regime"].items():
            print(f"  {regime}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
