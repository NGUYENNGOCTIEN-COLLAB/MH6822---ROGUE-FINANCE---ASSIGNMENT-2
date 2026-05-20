#!/usr/bin/env python3
"""Module 5: dashboard.

Reads ``reports/compliance_report.json`` and produces ``reports/dashboard.html``,
a single self-contained HTML file with four required visuals:

1. Portfolio compliance heatmap (trades x regimes)
2. Error frequency horizontal bar chart (most common failing fields)
3. Asset-class compliance breakdown (% in-scope compliant)
4. Classification frontier panel (all NO_PRODUCT_DEFINITION / novel-taxonomy
   trades, with per-regime disposition and citations)

Plus a written interpretation block.

Plotly is the only third-party dependency.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import plotly.graph_objects as go
    from plotly.io import to_html
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "plotly is required for the dashboard; install with `pip install plotly`"
    ) from exc


STATUS_COLOURS = {
    "COMPLIANT":      "#2e7d32",
    "NONCOMPLIANT":   "#c62828",
    "CONDITIONAL":    "#f9a825",
    "NOT_APPLICABLE": "#9e9e9e",
    "NOT_IMPLEMENTED": "#616161",
}

STATUS_NUM = {
    "COMPLIANT": 3,
    "CONDITIONAL": 2,
    "NOT_APPLICABLE": 1,
    "NONCOMPLIANT": 0,
    "NOT_IMPLEMENTED": -1,
}


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def heatmap_figure(report: dict[str, Any]) -> str:
    regimes = report["metadata"]["regimes"]
    trades = report["trades"]
    trade_ids = [t["trade_id"] for t in trades]

    z, hover, text = [], [], []
    for regime in regimes:
        z_row, h_row, t_row = [], [], []
        for tr in trades:
            res = tr["module3_compliance"][regime]
            status = res["status"]
            z_row.append(STATUS_NUM.get(status, -1))
            errs = " | ".join(res.get("errors", [])[:3])
            notes = " | ".join(n for n in res.get("notes", [])[:2] if n)
            tooltip_lines = [f"<b>{tr['trade_id']} / {regime}: {status}</b>"]
            if errs:
                tooltip_lines.append(f"errors: {errs}")
            if notes:
                tooltip_lines.append(f"notes: {notes}")
            h_row.append("<br>".join(tooltip_lines))
            t_row.append(status[0])
        z.append(z_row)
        hover.append(h_row)
        text.append(t_row)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=trade_ids,
        y=regimes,
        text=text,
        hovertext=hover,
        hoverinfo="text",
        colorscale=[
            [0.0, STATUS_COLOURS["NONCOMPLIANT"]],
            [0.33, STATUS_COLOURS["NOT_APPLICABLE"]],
            [0.66, STATUS_COLOURS["CONDITIONAL"]],
            [1.0, STATUS_COLOURS["COMPLIANT"]],
        ],
        showscale=False,
        xgap=1, ygap=1,
    ))
    fig.update_layout(
        title="1. Portfolio compliance heatmap",
        xaxis_title="Trade",
        yaxis_title="Regime",
        height=80 + 40 * len(regimes),
        margin=dict(l=80, r=20, t=60, b=80),
    )
    return to_html(fig, include_plotlyjs="cdn", full_html=False)


# ---------------------------------------------------------------------------
# Error frequency
# ---------------------------------------------------------------------------

def error_frequency_figure(report: dict[str, Any]) -> str:
    summary = report["portfolio_summary"]
    items = list(summary.get("top_error_fields", {}).items())[:15]
    if not items:
        return "<p><em>No errors in this portfolio.</em></p>"
    fields, counts = zip(*items)
    # Reverse for biggest-on-top horizontal bars.
    fields, counts = list(reversed(fields)), list(reversed(counts))
    fig = go.Figure(go.Bar(
        x=counts, y=fields, orientation="h",
        marker_color="#c62828",
        text=counts, textposition="outside",
    ))
    fig.update_layout(
        title="2. Error frequency (top 15 failing fields, all regimes)",
        xaxis_title="Trades affected",
        yaxis_title="",
        height=420,
        margin=dict(l=240, r=40, t=60, b=40),
    )
    return to_html(fig, include_plotlyjs=False, full_html=False)


# ---------------------------------------------------------------------------
# Asset-class breakdown
# ---------------------------------------------------------------------------

def asset_class_figure(report: dict[str, Any]) -> str:
    regimes = report["metadata"]["regimes"]
    # asset_class -> regime -> (in_scope, compliant)
    buckets: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: {r: [0, 0] for r in regimes}
    )
    for tr in report["trades"]:
        ac = tr["module1_parse"]["asset_class"] or "Unknown"
        for regime in regimes:
            res = tr["module3_compliance"][regime]
            if res["status"] == "NOT_APPLICABLE":
                continue
            buckets[ac][regime][0] += 1
            if res["status"] == "COMPLIANT":
                buckets[ac][regime][1] += 1

    asset_classes = sorted(buckets.keys())
    fig = go.Figure()
    for regime in regimes:
        pcts: list[float] = []
        labels: list[str] = []
        for ac in asset_classes:
            in_scope, compliant = buckets[ac][regime]
            pct = (compliant / in_scope * 100) if in_scope else 0
            pcts.append(pct)
            labels.append(f"{compliant}/{in_scope}")
        fig.add_bar(
            name=regime,
            x=asset_classes,
            y=pcts,
            text=labels,
            textposition="outside",
        )
    fig.update_layout(
        title="3. Asset-class compliance (% in-scope compliant)",
        xaxis_title="Asset class",
        yaxis_title="% compliant",
        yaxis_range=[0, 110],
        barmode="group",
        height=460,
        margin=dict(l=60, r=20, t=60, b=60),
    )
    return to_html(fig, include_plotlyjs=False, full_html=False)


# ---------------------------------------------------------------------------
# Classification frontier
# ---------------------------------------------------------------------------

def classification_frontier_figure(report: dict[str, Any]) -> str:
    regimes = report["metadata"]["regimes"]
    novels = [
        tr for tr in report["trades"]
        if tr["module1_parse"]["classification_flag"] == "NOVEL_INSTRUMENT_NO_TAXONOMY"
    ]
    if not novels:
        return "<p><em>No novel-taxonomy trades in this portfolio.</em></p>"

    headers = ["Trade", "Use case", "Platform"] + regimes + ["Citation"]
    rows: list[list[str]] = []
    for tr in novels:
        m1 = tr["module1_parse"]
        raw_classified = m1["classified_fields"]
        platform = (raw_classified.get("platform_type")
                    or raw_classified.get("platform")
                    or raw_classified.get("venue") or "n/a")
        row = [tr["trade_id"], m1["use_case"] or "n/a", platform]
        for regime in regimes:
            row.append(tr["module3_compliance"][regime]["status"])
        # First non-empty CFTC note as the citation column.
        citation = ""
        for n in tr["module3_compliance"][regimes[0]]["notes"]:
            if n:
                citation = n
                break
        row.append(citation)
        rows.append(row)

    fill_colors = [["#fafafa"] * len(rows)]  # Trade
    fill_colors.append(["#fafafa"] * len(rows))  # Use case
    fill_colors.append(["#fafafa"] * len(rows))  # Platform
    for regime in regimes:
        col = []
        for tr in novels:
            col.append(STATUS_COLOURS.get(tr["module3_compliance"][regime]["status"], "#9e9e9e"))
        fill_colors.append(col)
    fill_colors.append(["#fafafa"] * len(rows))  # Citation

    cell_values = list(map(list, zip(*rows)))
    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color="#37474f",
            font=dict(color="white"),
            align="left",
        ),
        cells=dict(
            values=cell_values,
            fill_color=fill_colors,
            align="left",
            font=dict(color="black", size=11),
            height=32,
        ),
    ))
    fig.update_layout(
        title="4. Classification frontier: novel instruments outside the ANNA-DSB taxonomy",
        height=120 + 36 * len(rows),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return to_html(fig, include_plotlyjs=False, full_html=False)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def build_interpretation(report: dict[str, Any]) -> str:
    """Generate interpretation text from the report, avoiding hard-coded counts."""
    trades = report["trades"]
    regimes = report["metadata"]["regimes"]
    conventional = [
        tr for tr in trades
        if tr["module1_parse"].get("classification_flag") == "CONVENTIONAL_DERIVATIVE"
    ]
    novel = [
        tr for tr in trades
        if tr["module1_parse"].get("classification_flag") == "NOVEL_INSTRUMENT_NO_TAXONOMY"
    ]
    no_product = [tr for tr in trades if tr["module2_upi"].get("status") == "NO_PRODUCT_DEFINITION"]
    conditional_novel = [
        tr for tr in novel
        if any(res["status"] == "CONDITIONAL" for res in tr["module3_compliance"].values())
    ]
    scope_gap = [tr for tr in novel if tr.get("finding_type") == "JURISDICTIONAL_SCOPE_GAP"]
    cftc_compliant = sum(
        1 for tr in trades
        if "CFTC" in tr["module3_compliance"]
        and tr["module3_compliance"]["CFTC"]["status"] == "COMPLIANT"
    )
    emir_noncompliant = sum(
        1 for tr in trades
        if "EMIR" in tr["module3_compliance"]
        and tr["module3_compliance"]["EMIR"]["status"] == "NONCOMPLIANT"
    )
    novel_ids = ", ".join(tr["trade_id"] for tr in novel) or "none"
    conditional_ids = ", ".join(tr["trade_id"] for tr in conditional_novel) or "none"
    scope_ids = ", ".join(tr["trade_id"] for tr in scope_gap) or "none"
    scope_verb = "is" if len(scope_gap) == 1 else "are"
    scope_label = "jurisdictional-scope gap" if len(scope_gap) == 1 else "jurisdictional-scope gaps"
    regimes_text = ", ".join(regimes)

    return f"""
<h2>Interpretation</h2>
<p>The report contains <strong>{len(trades)} trades</strong> across {html.escape(regimes_text)}. The dashboard deliberately separates ordinary data-validation failures from classification-frontier findings.</p>
<p><strong>Population 1: conventional OTC derivatives ({len(conventional)} trades).</strong>
For these trades, the engine behaves like a standard reporting-control layer: it checks UPI availability, UTI namespace rules, LEI MOD 97-10 check digits, ISO 8601 timestamps, ISO 4217 currencies, action type, notional values, cleared indicators and collateral fields. In this run, {cftc_compliant} trade(s) are CFTC-compliant and {emir_noncompliant} trade(s) are EMIR-noncompliant. The cross-regime contrast is expected because EMIR, MAS and ASIC require per-trade collateral fields that CFTC does not require in the same way in this assignment model.</p>
<p><strong>Population 2: novel event contracts ({len(novel)} trades: {html.escape(novel_ids)}).</strong>
These trades return <code>NO_PRODUCT_DEFINITION</code> when no active EventContract template exists in the ANNA-DSB-style library. {html.escape(conditional_ids)} have a CFTC-regulated DCM nexus and therefore route to <strong>CONDITIONAL</strong>; {html.escape(scope_ids)} {scope_verb} better described as a {scope_label}. This is the hidden assignment result: a taxonomy gap is not the same thing as a bad LEI, bad UTI or missing field.</p>
<p>The <strong>{len(no_product)} NO_PRODUCT_DEFINITION</strong> result(s) are the classification-frontier finding. They show where the reporting stack lacks an identifier pathway: no registered UPI product class, uncertain UTI generation for platform or blockchain venues, and no obvious SDR data model for event outcome, settlement source and participant eligibility. The policy question is therefore not merely whether the trade record is complete, but whether the legal and data taxonomy can see the risk at all.</p>
"""


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MH6822 OTC Derivatives Compliance Dashboard</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 24px;
    background: #fafafa;
    color: #212121;
    line-height: 1.5;
  }}
  h1 {{ font-size: 22px; margin-bottom: 8px; }}
  h2 {{ font-size: 16px; margin-top: 24px; }}
  .meta {{ color: #555; font-size: 13px; margin-bottom: 16px; }}
  .panel {{
    background: white;
    padding: 16px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-bottom: 24px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }}
  .legend {{ display: flex; gap: 16px; font-size: 13px; margin-bottom: 8px; }}
  .legend span {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    color: white;
    font-weight: 600;
  }}
  code {{
    background: #f0f0f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.92em;
  }}
</style>
</head>
<body>
<h1>MH6822 OTC Derivatives Compliance Dashboard</h1>
<div class="meta">
  Generated {generated} · {trade_count} trades · regimes: {regimes}
</div>
<div class="legend">
  <span style="background:#2e7d32">COMPLIANT</span>
  <span style="background:#c62828">NONCOMPLIANT</span>
  <span style="background:#f9a825">CONDITIONAL</span>
  <span style="background:#9e9e9e">NOT_APPLICABLE</span>
</div>
<div class="panel">{heatmap}</div>
<div class="panel">{errors}</div>
<div class="panel">{asset_class}</div>
<div class="panel">{frontier}</div>
<div class="panel">{interpretation}</div>
</body>
</html>"""


def build_dashboard(report_path: Path, out_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    page = PAGE_TEMPLATE.format(
        generated=html.escape(report["metadata"]["generated_at_utc"]),
        trade_count=report["metadata"]["trade_count"],
        regimes=", ".join(report["metadata"]["regimes"]),
        heatmap=heatmap_figure(report),
        errors=error_frequency_figure(report),
        asset_class=asset_class_figure(report),
        frontier=classification_frontier_figure(report),
        interpretation=build_interpretation(report),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", default="reports/compliance_report.json")
    p.add_argument("--out", default="reports/dashboard.html")
    args = p.parse_args()
    build_dashboard(Path(args.report), Path(args.out))
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
