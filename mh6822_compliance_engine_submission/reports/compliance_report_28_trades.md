# Compliance Report

**Generated:** 2026-05-17T14:27:39.226367+00:00  
**Trades:** 28  
**Regimes:** CFTC, EMIR

## Portfolio summary

**By classification:**
- CONVENTIONAL_DERIVATIVE: 25
- NOVEL_INSTRUMENT_NO_TAXONOMY: 3

**By UPI status:**
- FOUND: 23
- INVALID_ATTRIBUTES: 2
- NO_PRODUCT_DEFINITION: 3

**By finding type:**
- IDENTIFIER_ERROR: 24
- FIELD_VALIDATION_ERROR: 1
- TAXONOMY_GAP_WITH_REGULATORY_NEXUS: 2
- JURISDICTIONAL_SCOPE_GAP: 1

**By regime:**
- **CFTC**: COMPLIANT=1, CONDITIONAL=2, NONCOMPLIANT=24, NOT_APPLICABLE=1
- **EMIR**: NONCOMPLIANT=25, NOT_APPLICABLE=3

## Top error fields

| Field | Count |
|---|---:|
| `EMIR.variation_margin_posted` | 14 |
| `CFTC.other_counterparty_lei` | 13 |
| `EMIR.other_counterparty_lei` | 13 |
| `EMIR.collateral_portfolio_code` | 13 |
| `EMIR.initial_margin_posted` | 13 |
| `CFTC.reporting_counterparty_lei` | 11 |
| `EMIR.reporting_counterparty_lei` | 11 |
| `CFTC.upi` | 4 |
| `EMIR.upi` | 4 |
| `CFTC.upi_attribute` | 3 |
| `EMIR.upi_attribute` | 3 |
| `CFTC.parse` | 2 |
| `EMIR.parse` | 2 |
| `UPI.missing` | 2 |
| `CFTC.uti` | 1 |
| `EMIR.uti` | 1 |
| `UPI.notional_currency` | 1 |
| `CFTC.notional_currency` | 1 |
| `EMIR.notional_currency` | 1 |
| `PARSER.execution_timestamp` | 1 |

## Top warning fields

| Field | Count |
|---|---:|
| `UPI.reference_rate` | 1 |
| `CFTC.reference_rate` | 1 |
| `EMIR.reference_rate` | 1 |

## Per-trade results

| Trade | Class | Use case | Finding type | Class. flag | UPI | CFTC | EMIR |
|---|---|---|---|---|---|---|---|
| T001 | Rates | Fixed_Float | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T002 | Credit | Corporate | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T003 | FX | NDF | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T004 | Equity | SingleName_Put | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T005 | Rates | Fixed_Float | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T006 | Rates | Basis | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T007 | Commodities | SingleName | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T008 | Rates | Swaption | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T009 | FX | Vanilla | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | INVALID_ATTRIBUTES | ✗ | ✗ |
| T010 | Credit | Index | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T011 | Rates | CrossCurrency | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T012 | Equity | TotalReturn_SingleIndex | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T013 | Rates | Inflation | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T014 | FX | Standard | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T015 | Rates | Cap | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T016 | Equity | Variance | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T017 | Credit | Sovereign | FIELD_VALIDATION_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✓ | ✗ |
| T018 | Rates | OIS | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T019 | Commodities | SingleName | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T020 | FX | Barrier | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T021 | Rates | Fixed_Float | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | INVALID_ATTRIBUTES | ✗ | ✗ |
| T022 | Credit | ABS | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T023 | Equity | SingleName | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T024 | Rates | Fixed_Float | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T025 | FX | Deliverable | IDENTIFIER_ERROR | CONVENTIONAL_DERIVATIVE | FOUND | ✗ | ✗ |
| T026 | EventContract | PoliticalOutcome | TAXONOMY_GAP_WITH_REGULATORY_NEXUS | NOVEL_INSTRUMENT_NO_TAXONOMY | NO_PRODUCT_DEFINITION | ? | n/a |
| T027 | EventContract | MacroeconomicOutcome | JURISDICTIONAL_SCOPE_GAP | NOVEL_INSTRUMENT_NO_TAXONOMY | NO_PRODUCT_DEFINITION | n/a | n/a |
| T028 | EventContract | RegulatoryDecisionOutcome | TAXONOMY_GAP_WITH_REGULATORY_NEXUS | NOVEL_INSTRUMENT_NO_TAXONOMY | NO_PRODUCT_DEFINITION | ? | n/a |

*Legend:* ✓ COMPLIANT, ✗ NONCOMPLIANT, ? CONDITIONAL, n/a NOT_APPLICABLE, ∅ NOT_IMPLEMENTED.


## Detailed findings (non-compliant and conditional trades)

### T001: Rates/Swap/Fixed_Float
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26

### T002: Credit/Swap/Corporate
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 2 fields (first: other_counterparty_lei); remediate all flagged fields before resubmission.
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - variation_margin_posted: must not be negative (got -15000)

### T003: FX/Forward/NDF
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - variation_margin_posted: mandatory collateral field is missing or null

### T004: Equity/Option/SingleName_Put
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI 'MISSING_LEI' must be 20 characters: 18 uppercase alphanumeric plus 2 numeric check digits
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI 'MISSING_LEI' must be 20 characters: 18 uppercase alphanumeric plus 2 numeric check digits
  - variation_margin_posted: mandatory collateral field is missing or null

### T005: Rates/Swap/Fixed_Float
**UPI warnings:**
  - reference_rate='GBP-LIBOR-BBA' references LIBOR; deprecated benchmark (retained as warning for legacy trade handling per FCA / Federal Reserve cessation guidance, 30 June 2023)
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26

### T006: Rates/Swap/Basis
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 2 fields (first: reporting_counterparty_lei); remediate all flagged fields before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - uti: UTI is missing
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 5 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - uti: UTI is missing
  - variation_margin_posted: mandatory collateral field is missing or null

### T007: Commodities/Swap/SingleName
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - variation_margin_posted: mandatory collateral field is missing or null

### T008: Rates/Option/Swaption
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26

### T009: FX/Option/Vanilla
**UPI validation errors:**
  - notional_currency: currency code 'INVALID_CCY' must be a three-letter uppercase ISO 4217 code
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 5 fields (first: notional_currency); remediate all flagged fields before resubmission.
  - notional_currency: currency code 'INVALID_CCY' must be a three-letter uppercase ISO 4217 code
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - upi: UPI lookup failed with status INVALID_ATTRIBUTES
  - upi: mandatory UPI unavailable; lookup status=INVALID_ATTRIBUTES
  - upi_attribute: notional_currency: currency code 'INVALID_CCY' must be a three-letter uppercase ISO 4217 code
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 8 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - notional_currency: currency code 'INVALID_CCY' must be a three-letter uppercase ISO 4217 code
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - upi: UPI lookup failed with status INVALID_ATTRIBUTES
  - upi: mandatory UPI unavailable; lookup status=INVALID_ATTRIBUTES
  - upi_attribute: notional_currency: currency code 'INVALID_CCY' must be a three-letter uppercase ISO 4217 code
  - variation_margin_posted: mandatory collateral field is missing or null

### T010: Credit/Swap/Index
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26

### T011: Rates/Swap/CrossCurrency
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62

### T012: Equity/Swap/TotalReturn_SingleIndex
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38

### T013: Rates/Swap/Inflation
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 2 fields (first: execution_timestamp); remediate all flagged fields before resubmission.
  - execution_timestamp: execution_timestamp must use ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ
  - parse: execution_timestamp must use ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 2 fields (first: execution_timestamp); remediate all flagged fields before resubmission.
  - execution_timestamp: execution_timestamp must use ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ
  - parse: execution_timestamp must use ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ

### T014: FX/Swap/Standard
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 2 fields (first: other_counterparty_lei); remediate all flagged fields before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 5 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - variation_margin_posted: mandatory collateral field is missing or null

### T015: Rates/Cap_Floor/Cap
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26

### T016: Equity/Swap/Variance
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - variation_margin_posted: mandatory collateral field is missing or null

### T017: Credit/Swap/Sovereign
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 3 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - variation_margin_posted: mandatory collateral field is missing or null

### T018: Rates/Swap/OIS
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38

### T019: Commodities/Option/SingleName
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - reporting_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - variation_margin_posted: mandatory collateral field is missing or null

### T020: FX/Option/Barrier
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 2 fields (first: other_counterparty_lei); remediate all flagged fields before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 5 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
  - reporting_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
  - variation_margin_posted: mandatory collateral field is missing or null

### T021: Rates/Swap/Fixed_Float
**UPI validation errors:**
  - missing required attribute ReferenceRateTermUnit (looked in ['reference_rate_term_unit'])
  - missing required attribute ReferenceRateTermValue (looked in ['reference_rate_term_value'])
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on 6 fields (first: maturity_or_expiry_date); remediate all flagged fields before resubmission.
  - maturity_or_expiry_date: maturity_or_expiry_date is not a valid calendar date: time data '9999-99-99' does not match format '%Y-%m-%d'
  - parse: maturity_date is not a valid calendar date: time data '9999-99-99' does not match format '%Y-%m-%d'
  - upi: UPI lookup failed with status INVALID_ATTRIBUTES
  - upi: mandatory UPI unavailable; lookup status=INVALID_ATTRIBUTES
  - upi_attribute: missing required attribute ReferenceRateTermUnit (looked in ['reference_rate_term_unit'])
  - upi_attribute: missing required attribute ReferenceRateTermValue (looked in ['reference_rate_term_value'])
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 9 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - maturity_or_expiry_date: maturity_or_expiry_date is not a valid calendar date: time data '9999-99-99' does not match format '%Y-%m-%d'
  - parse: maturity_date is not a valid calendar date: time data '9999-99-99' does not match format '%Y-%m-%d'
  - upi: UPI lookup failed with status INVALID_ATTRIBUTES
  - upi: mandatory UPI unavailable; lookup status=INVALID_ATTRIBUTES
  - upi_attribute: missing required attribute ReferenceRateTermUnit (looked in ['reference_rate_term_unit'])
  - upi_attribute: missing required attribute ReferenceRateTermValue (looked in ['reference_rate_term_value'])
  - variation_margin_posted: mandatory collateral field is missing or null

### T022: Credit/Swap/ABS
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on reporting_counterparty_lei; remediate before resubmission.
  - reporting_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38

### T023: Equity/Forward/SingleName
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI '2138002TXD6KSZ3V5X27' has invalid MOD 97-10 check digits; expected 26
  - variation_margin_posted: mandatory collateral field is missing or null

### T024: Rates/Swap/Fixed_Float
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '4R3ZURLYISNNNMHMK608' has invalid MOD 97-10 check digits; expected 62

### T025: FX/Forward/Deliverable
**CFTC: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails CFTC on other_counterparty_lei; remediate before resubmission.
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
**EMIR: NONCOMPLIANT** (reporting_obligation=YES)
  - *Explanation:* Trade fails EMIR on 4 fields (first: collateral_portfolio_code); remediate all flagged fields before resubmission.
  - collateral_portfolio_code: mandatory collateral field is missing or null
  - initial_margin_posted: mandatory collateral field is missing or null
  - other_counterparty_lei: LEI '9695009AXSRNHZE85Y20' has invalid MOD 97-10 check digits; expected 38
  - variation_margin_posted: mandatory collateral field is missing or null

### T026: EventContract/BinaryEventContract/PoliticalOutcome
**CFTC: CONDITIONAL** (reporting_obligation=CONDITIONAL)
  - *Explanation:* Trade is in scope of CFTC but reporting treatment is subject to active rulemaking; manual review required before SDR submission.
  - *Note:* Event contract executed on a CFTC-regulated DCM. Reporting treatment is CONDITIONAL pending the CFTC Advance Notice of Proposed Rulemaking on Prediction Markets (RIN 3038-AF65, 91 FR 12516, Federal Register Document No. 2026-05105, March 16 2026; comment period closed April 30 2026). The rulemaking package is cross-referenced with CFTC Press Release 9194-26, CFTC Press Release 9193-26, and CFTC Staff Letter No. 26-08 (Prediction Markets Advisory). Manual review required.
  - *Note:* Asset class 'EventContract' (instrument 'BinaryEventContract') has no product definition in the ANNA-DSB UPI library. This is the regulatory classification frontier the assignment is testing for. See Module 4 for the proposed schema extension.

### T028: EventContract/BinaryEventContract/RegulatoryDecisionOutcome
**CFTC: CONDITIONAL** (reporting_obligation=CONDITIONAL)
  - *Explanation:* Trade is in scope of CFTC but reporting treatment is subject to active rulemaking; manual review required before SDR submission.
  - *Note:* Event contract executed on a CFTC-regulated DCM. Reporting treatment is CONDITIONAL pending the CFTC Advance Notice of Proposed Rulemaking on Prediction Markets (RIN 3038-AF65, 91 FR 12516, Federal Register Document No. 2026-05105, March 16 2026; comment period closed April 30 2026). The rulemaking package is cross-referenced with CFTC Press Release 9194-26, CFTC Press Release 9193-26, and CFTC Staff Letter No. 26-08 (Prediction Markets Advisory). Manual review required.
  - *Note:* Asset class 'EventContract' (instrument 'BinaryEventContract') has no product definition in the ANNA-DSB UPI library. This is the regulatory classification frontier the assignment is testing for. See Module 4 for the proposed schema extension.
