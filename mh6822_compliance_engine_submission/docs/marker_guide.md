# Marker Guide

This file highlights the fastest way to verify the submission.

## 1. Install and test

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 62 tests
OK
```

## 2. Official 28-trade run

```bash
python run_compliance_check.py \
  --input trades.json \
  --regimes CFTC,EMIR \
  --output-json reports/compliance_report_28_trades.json \
  --output-csv reports/compliance_report_28_trades.csv \
  --output-md reports/compliance_report_28_trades.md
```

Expected summary:

```text
CFTC: COMPLIANT=1, CONDITIONAL=2, NONCOMPLIANT=24, NOT_APPLICABLE=1
EMIR: NONCOMPLIANT=25, NOT_APPLICABLE=3
```

## 3. Required event-contract asymmetry

| Trade | CFTC | EMIR | UPI |
|---|---:|---:|---:|
| T026 | CONDITIONAL | NOT_APPLICABLE | NO_PRODUCT_DEFINITION |
| T027 | NOT_APPLICABLE | NOT_APPLICABLE | NO_PRODUCT_DEFINITION |
| T028 | CONDITIONAL | NOT_APPLICABLE | NO_PRODUCT_DEFINITION |

Tests covering this:

```text
TestCompliance.test_t026_kalshi_dcm_conditional_under_cftc
TestCompliance.test_t027_polymarket_not_applicable_everywhere
TestCompliance.test_t028_kalshi_dcm_conditional_under_cftc
```

## 4. Full 34-trade run

```bash
python run_compliance_check.py \
  --input portfolio_full.json \
  --regimes CFTC,EMIR,MAS \
  --output-json reports/compliance_report_34_trades.json \
  --output-csv reports/compliance_report_34_trades.csv \
  --output-md reports/compliance_report_34_trades.md
```

Expected summary:

```text
CFTC: COMPLIANT=3, CONDITIONAL=3, NONCOMPLIANT=27, NOT_APPLICABLE=1
EMIR: COMPLIANT=2, NONCOMPLIANT=28, NOT_APPLICABLE=4
MAS:  COMPLIANT=2, NONCOMPLIANT=28, NOT_APPLICABLE=4
```

## 5. Additional trades

| Trade | Asset class | Expected point |
|---|---|---|
| T029 | Rates | Clean OIS; CFTC/EMIR compliant. |
| T030 | FX | Negative notional error. |
| T031 | Equity | Invalid ISIN-shaped underlier. |
| T032 | Commodities | Off-codeset commodity. |
| T033 | EventContract | Additional event-contract taxonomy gap. |
| T034 | Credit | Clean Credit trade; completes conventional coverage. |

## 6. Core policy insight and finding_type

The engine deliberately distinguishes four situations, readable from the
`finding_type` field plus the combination of `classification_flag`, the UPI
`status` and the per-regime compliance `status` in the JSON report:

- identifier error, such as a bad LEI / UTI / UPI (conventional trade,
  `INVALID_ATTRIBUTES` or NONCOMPLIANT on an identifier field);
- field validation error, such as negative notional or invalid
  collateral (conventional trade, `INVALID_ATTRIBUTES` / NONCOMPLIANT);
- taxonomy gap with a regulatory nexus, such as T026 / T028 / T033
  (novel trade, `NO_PRODUCT_DEFINITION`, CFTC CONDITIONAL);
- jurisdictional scope gap, such as T027 (novel trade,
  `NO_PRODUCT_DEFINITION`, NOT_APPLICABLE under every regime).

That distinction is the core policy insight of Module 4.

## 7. Dashboard

```bash
python dashboard.py --report reports/compliance_report_34_trades.json --out reports/dashboard.html
```

Open:

```text
reports/dashboard.html
```

The dashboard has the four requested visuals: heatmap, error frequency, asset-class breakdown and classification-frontier panel.
