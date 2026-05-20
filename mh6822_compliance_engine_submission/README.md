# MH6822 Homework 2: OTC Derivatives Compliance Engine

A multi-jurisdictional reportability checker for OTC derivatives,
covering the Dodd-Frank Title VII (CFTC), EMIR Refit (ESMA), ASIC DTR
and MAS SF(RDC)R reporting regimes, with first-class handling of the
prediction-market / event-contract classification frontier.

The full project report is in [`docs/report.md`](docs/report.md);
the Module 4 written analysis on prediction-market classification is
in [`docs/module4_classification_analysis.md`](docs/module4_classification_analysis.md).

---

## Quick start

```bash
# 1. Install the only third-party dependency (Plotly).
pip install -r requirements.txt

# 2. Run the engine on the instructor portfolio under CFTC + EMIR.
python run_compliance_check.py --input trades.json --regimes CFTC,EMIR

# 3. Generate the visual dashboard from the JSON report.
python dashboard.py

# 4. Open the dashboard.
open reports/dashboard.html       # macOS
xdg-open reports/dashboard.html   # Linux

# 5. Run the test suite.
python -m unittest discover -s tests -v
```

Outputs land in `reports/`:

* `compliance_report.json`, full structured record per trade
* `compliance_report.csv`, flat one-row-per-trade summary
* `compliance_report.md`, human-readable summary
* `dashboard.html`, Plotly dashboard (4 panels + interpretation)

---

## Running the full 34-trade portfolio

The six team-designed trades in `additional_trades.json` are described
in [`docs/report.md`](docs/report.md). The combined 34-trade portfolio
is provided as `portfolio_full.json`. To run the engine on it under
three regimes:

```bash
python run_compliance_check.py \
    --input portfolio_full.json \
    --regimes CFTC,EMIR,MAS

python dashboard.py
```

---

## Architecture

```
src/compliance_engine/
  models.py                # ParsedTrade, UpiLookupResult, ComplianceResult
  utils.py                 # LEI / UTI / ISO 8601 / ISO 4217 validators
  module1_parser.py        # parser + classifier
  module2_upi_lookup.py    # template library + attribute validation
  module3_compliance.py    # 4-regime compliance checker

data/product_definitions/PROD/OTC-Products/
  UPI/<AssetClass>/*.UPI.V1.json     # 25 deterministic ANNA-DSB-style product templates
  codesets/                          # 5 controlled vocabularies
    ISOCurrencyCode.json             #   180 ISO 4217 codes + precious metals
    FpmlRatesReferenceRate.json      #   32 codes; LIBOR retained as warning
    DebtSeniority.json
    CreditIndex.json
    CommodityCode.json

run_compliance_check.py    # CLI runner
dashboard.py               # Plotly dashboard generator
tests/test_engine.py       # 62 tests; regression-guards official data, taxonomy gap, and verdict tallies

trades.json                # instructor portfolio (28 trades)
additional_trades.json     # team-designed (6 trades)
portfolio_full.json        # combined (34)

docs/
  report.md                          # main project report
  module4_classification_analysis.md # event contracts written analysis
  event_contract_upi_template.json   # proposed schema extension (machine-readable)
  regulatory_sources.md              # citation/source-hygiene checklist
  marker_guide.md                    # fast verification guide
  presentation_script.md             # 5-minute video script
```

The pipeline is three stateless functions over three immutable
dataclasses, see `docs/report.md` Section 1. Each report also includes a
`finding_type` field so ordinary identifier failures are separated from
taxonomy and jurisdictional-scope gaps.

---

## Swapping in the production ANNA-DSB library

The `data/product_definitions/PROD/OTC-Products/` tree mirrors the
public ANNA-DSB Product-Definitions repository so that swapping in the
production library is a single git clone:

```bash
bash scripts/update_anna_dsb_product_definitions.sh
```

The script clones https://github.com/ANNA-DSB/Product-Definitions into
`data/product_definitions/` and the engine picks up the new templates
automatically, no code changes required. (A backup of the local
templates is created first.)

---

## Sample output

```
$ python run_compliance_check.py --input trades.json --regimes CFTC,EMIR
Processed 28 trades across regimes CFTC,EMIR
  JSON: reports/compliance_report.json
  CSV:  reports/compliance_report.csv
  MD:   reports/compliance_report.md
  CFTC: COMPLIANT=1, CONDITIONAL=2, NONCOMPLIANT=24, NOT_APPLICABLE=1
  EMIR: NONCOMPLIANT=25, NOT_APPLICABLE=3
```

The single CFTC-COMPLIANT trade is T017, a sovereign CDS whose null
collateral fields are acceptable under CFTC's firm-level reporting but
fail EMIR's per-trade requirement. The 2 CONDITIONAL trades are T026
and T028, Kalshi-listed event contracts on a CFTC-regulated DCM,
routed to CONDITIONAL with a citation to CFTC ANPR 91 FR 12516, RIN
3038-AF65 (March 2026).

---

## Testing

62 tests across 14 test classes:

```
$ python -m unittest discover -s tests -v
...
Ran 62 tests in <1s
OK
```

The headline test is `TestExpectedVerdictCounts`, which freezes the
engine's verdict tally on the 28-trade instructor portfolio (CFTC:
COMPLIANT=1, CONDITIONAL=2, NONCOMPLIANT=24, NOT_APPLICABLE=1; EMIR:
NONCOMPLIANT=25, NOT_APPLICABLE=3). If a later change shifts any
verdict, the test fails and the diff identifies which module's logic
moved.

---

## Limitations

See `docs/report.md` Section 6. Three areas are explicitly out of
scope: the production ANNA-DSB template distribution, GLEIF / SDR
queries for issuance status and duplicate detection, and natural-
language semantic analysis of event descriptions.

---

## Team

| Member | Matriculation number | Primary | Secondary |
|---|---|---|---|
| NGUYEN NGOC TIEN | G2506667B | Module 1 parser/classifier; Module 2 UPI lookup; official-trade regression tests | CLI integration and output verification |
| KOK WEN SHIN | G2506930B | Module 3 compliance checker; Module 4 classification-frontier analysis; dashboard interpretation | Regulatory-source hygiene and presentation script |

Team contact details are recorded in `team.csv`.

---

## Recording

Presentation recording: 
