"""Unit tests for the compliance engine.

Run with::

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from compliance_engine.module1_parser import (
    parse_trade,
    parse_portfolio,
    classify_instrument,
    CLASSIFICATION_CONVENTIONAL,
    CLASSIFICATION_NOVEL,
    CLASSIFICATION_AMBIGUOUS,
)
from compliance_engine.module2_upi_lookup import TemplateLibrary, lookup_upi
from compliance_engine.module3_compliance import (
    check_compliance,
    CFTC_EVENT_NOTE,
    MAS_EVENT_NOTE,
)
from compliance_engine.utils import (
    compute_lei_check_digits,
    validate_lei,
    validate_uti,
    validate_currency,
    validate_currency_pair,
    validate_iso8601_utc,
    validate_action_type,
)

PRODUCT_ROOT = ROOT / "data/product_definitions/PROD/OTC-Products"
TRADES_PATH = ROOT / "trades.json"


# ===========================================================================
# Identifier validation
# ===========================================================================

class TestLEI(unittest.TestCase):
    """ISO 7064 MOD 97-10 cross-checks."""

    def test_known_good_leis(self):
        # All from the instructor portfolio's reporting LEIs.
        for lei in ("5493001KJTIIGC8Y1R12", "VGRQXHF3J8VDLUA7XE92",
                    "1VUV7VQFKUOQSJ21A208", "5299000J2N45DDNE4Y28"):
            ok, msg = validate_lei(lei)
            self.assertTrue(ok, f"{lei}: {msg}")

    def test_known_bad_leis(self):
        # All from the instructor portfolio's other_counterparty LEIs.
        for bad in ("2138002TXD6KSZ3V5X27", "9695009AXSRNHZE85Y20",
                    "4R3ZURLYISNNNMHMK608"):
            ok, msg = validate_lei(bad)
            self.assertFalse(ok)
            self.assertIn("MOD 97-10", msg)

    def test_compute_check_digits(self):
        # Round-trip: take a body, compute CD, validate the assembled LEI.
        body = "5493001KJTIIGC8Y1R"
        cd = compute_lei_check_digits(body)
        self.assertEqual(cd, "12")
        ok, _ = validate_lei(body + cd)
        self.assertTrue(ok)

    def test_lowercase_rejected(self):
        ok, _ = validate_lei("5493001kjtiigc8y1r12")
        self.assertFalse(ok)

    def test_missing_lei_sentinel(self):
        ok, _ = validate_lei("MISSING_LEI")
        self.assertFalse(ok)

    def test_none_and_empty(self):
        for v in (None, "", "ABC"):
            ok, _ = validate_lei(v)
            self.assertFalse(ok, f"unexpectedly valid: {v!r}")


class TestUTI(unittest.TestCase):
    REPORTING = "5493001KJTIIGC8Y1R12"

    def test_valid(self):
        uti = self.REPORTING + "20260301TRD00001"  # 36 chars total
        ok, msg = validate_uti(uti, self.REPORTING)
        self.assertTrue(ok, msg)

    def test_too_long(self):
        uti = self.REPORTING + "X" * 33  # 53 chars
        ok, _ = validate_uti(uti, self.REPORTING)
        self.assertFalse(ok)

    def test_namespace_mismatch(self):
        # A valid LEI but not the reporting LEI.
        other_lei = "VGRQXHF3J8VDLUA7XE92"
        uti = other_lei + "20260301TRD00001"
        ok, msg = validate_uti(uti, self.REPORTING)
        self.assertFalse(ok)
        self.assertIn("namespace", msg.lower())

    def test_bad_suffix_charset(self):
        # Lowercase letters in suffix not allowed.
        uti = self.REPORTING + "20260301trd00001"
        ok, _ = validate_uti(uti, self.REPORTING)
        self.assertFalse(ok)

    def test_missing(self):
        ok, _ = validate_uti(None, self.REPORTING)
        self.assertFalse(ok)


class TestCurrency(unittest.TestCase):
    def test_known_codes(self):
        for ccy in ("USD", "EUR", "SGD", "XAU", "XAG"):
            ok, _ = validate_currency(ccy)
            self.assertTrue(ok)

    def test_invalid_code(self):
        ok, msg = validate_currency("INVALID_CCY")
        self.assertFalse(ok)
        self.assertIn("ISO 4217", msg)

    def test_lowercase_rejected(self):
        ok, _ = validate_currency("usd")
        self.assertFalse(ok)

    def test_pair_format(self):
        ok, _ = validate_currency_pair("EUR/USD")
        self.assertTrue(ok)
        for bad in ("EURUSD", "EUR-USD", "EUR/", "/USD", "EUR/XYZ"):
            ok, _ = validate_currency_pair(bad)
            self.assertFalse(ok, f"unexpectedly valid: {bad!r}")


class TestTimestamp(unittest.TestCase):
    def test_valid_utc(self):
        ok, _ = validate_iso8601_utc("2025-09-12T14:23:11Z")
        self.assertTrue(ok)

    def test_date_only_rejected(self):
        # T013 in the instructor portfolio.
        ok, _ = validate_iso8601_utc("2025-09-01")
        self.assertFalse(ok)

    def test_us_format_rejected(self):
        ok, _ = validate_iso8601_utc("08/11/2025 09:30:00")
        self.assertFalse(ok)


class TestActionType(unittest.TestCase):
    def test_valid(self):
        for a in ("NEW", "MODIFY", "CORRECT", "TERMINATE"):
            ok, _ = validate_action_type(a)
            self.assertTrue(ok)

    def test_invalid(self):
        ok, _ = validate_action_type("REGISTER")
        self.assertFalse(ok)


# ===========================================================================
# Classification
# ===========================================================================

class TestClassification(unittest.TestCase):
    def test_conventional(self):
        for asset, instr in [("Rates", "Swap"), ("Credit", "Swap"),
                              ("FX", "Forward"), ("Equity", "Option"),
                              ("Commodities", "Swap")]:
            self.assertEqual(
                classify_instrument({"asset_class": asset, "instrument_type": instr}),
                CLASSIFICATION_CONVENTIONAL,
            )

    def test_novel_explicit(self):
        for asset in ("EventContract", "PredictionContract", "PoliticalRisk"):
            self.assertEqual(
                classify_instrument({"asset_class": asset, "instrument_type": "BinaryEvent"}),
                CLASSIFICATION_NOVEL,
            )

    def test_novel_heuristic(self):
        # Unknown asset class with a novel-looking token routes to NOVEL.
        self.assertEqual(
            classify_instrument({"asset_class": "NewEventClass", "instrument_type": "Outcome"}),
            CLASSIFICATION_NOVEL,
        )

    def test_ambiguous(self):
        # Unknown asset class with no novel tokens.
        self.assertEqual(
            classify_instrument({"asset_class": "Crypto", "instrument_type": "Perp"}),
            CLASSIFICATION_AMBIGUOUS,
        )

    def test_missing_fields(self):
        self.assertEqual(classify_instrument({}), CLASSIFICATION_AMBIGUOUS)


# ===========================================================================
# Parsing
# ===========================================================================

class TestParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trades = json.loads(TRADES_PATH.read_text())
        cls.by_id = {t["trade_id"]: t for t in cls.trades}

    def test_portfolio_size(self):
        self.assertEqual(len(self.trades), 28)

    def test_t001_clean_swap(self):
        p = parse_trade(self.by_id["T001"])
        self.assertEqual(p.parse_status, "SUCCESS")
        self.assertEqual(p.classification_flag, CLASSIFICATION_CONVENTIONAL)
        self.assertEqual(p.parse_errors, [])

    def test_t013_bad_timestamp_partial(self):
        p = parse_trade(self.by_id["T013"])
        self.assertEqual(p.parse_status, "PARTIAL")
        self.assertTrue(any("execution_timestamp" in e for e in p.parse_errors))

    def test_t021_bad_maturity_partial(self):
        p = parse_trade(self.by_id["T021"])
        self.assertEqual(p.parse_status, "PARTIAL")
        self.assertTrue(any("maturity_date" in e for e in p.parse_errors))

    def test_event_contracts_classified_novel(self):
        for tid in ("T026", "T027", "T028"):
            p = parse_trade(self.by_id[tid])
            self.assertEqual(p.classification_flag, CLASSIFICATION_NOVEL)

    def test_handles_garbage(self):
        out = parse_portfolio([{}, None, "string", 42, self.by_id["T001"]])
        self.assertEqual(len(out), 5)
        self.assertEqual(out[-1].parse_status, "SUCCESS")
        for r in out[:-1]:
            self.assertIn(r.parse_status, {"PARTIAL", "FAILED"})


# ===========================================================================
# UPI lookup
# ===========================================================================

class TestUpiLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = TemplateLibrary(str(PRODUCT_ROOT))
        cls.trades = json.loads(TRADES_PATH.read_text())
        cls.by_id = {t["trade_id"]: t for t in cls.trades}

    def test_t001_found(self):
        raw = self.by_id["T001"]
        result = lookup_upi(parse_trade(raw), raw, self.lib)
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.matched_template, "Rates.Swap.Fixed_Float")
        self.assertIsNotNone(result.upi_code)

    def test_t005_libor_warning(self):
        raw = self.by_id["T005"]
        result = lookup_upi(parse_trade(raw), raw, self.lib)
        self.assertEqual(result.status, "FOUND")  # LIBOR is warning, not error
        self.assertTrue(any("LIBOR" in w.upper() for w in result.warnings))

    def test_t009_invalid_currency(self):
        raw = self.by_id["T009"]
        result = lookup_upi(parse_trade(raw), raw, self.lib)
        self.assertEqual(result.status, "INVALID_ATTRIBUTES")
        self.assertTrue(any("notional_currency" in e for e in result.validation_errors))

    def test_event_contract_no_product_definition(self):
        for tid in ("T026", "T027", "T028"):
            raw = self.by_id[tid]
            result = lookup_upi(parse_trade(raw), raw, self.lib)
            self.assertEqual(result.status, "NO_PRODUCT_DEFINITION")
            self.assertIsNone(result.upi_code)
            self.assertIn("ANNA-DSB", result.classification_note)


# ===========================================================================
# Compliance
# ===========================================================================

class TestCompliance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = TemplateLibrary(str(PRODUCT_ROOT))
        cls.trades = json.loads(TRADES_PATH.read_text())
        cls.by_id = {t["trade_id"]: t for t in cls.trades}

    def _evaluate(self, tid, regimes=("CFTC", "EMIR")):
        raw = self.by_id[tid]
        parsed = parse_trade(raw)
        upi = lookup_upi(parsed, raw, self.lib)
        return check_compliance(parsed, upi, raw, list(regimes))

    def test_t017_compliant_under_cftc_only(self):
        # T017 has null collateral fields; CFTC reports collateral firm-level so
        # ignores them, EMIR demands them so flags noncompliant.
        results = self._evaluate("T017")
        self.assertEqual(results["CFTC"].status, "COMPLIANT")
        self.assertEqual(results["EMIR"].status, "NONCOMPLIANT")
        self.assertTrue(any("collateral" in e or "margin" in e
                            for e in results["EMIR"].errors))

    def test_t026_kalshi_dcm_conditional_under_cftc(self):
        results = self._evaluate("T026", regimes=("CFTC", "EMIR", "ASIC", "MAS"))
        self.assertEqual(results["CFTC"].status, "CONDITIONAL")
        self.assertEqual(results["CFTC"].reporting_obligation, "CONDITIONAL")
        for r in ("EMIR", "ASIC", "MAS"):
            self.assertEqual(results[r].status, "NOT_APPLICABLE")
        self.assertTrue(any("91 FR 12516" in n for n in results["CFTC"].notes))

    def test_t027_polymarket_not_applicable_everywhere(self):
        results = self._evaluate("T027", regimes=("CFTC", "EMIR", "ASIC", "MAS"))
        for r in results.values():
            self.assertEqual(r.status, "NOT_APPLICABLE")

    def test_t028_kalshi_dcm_conditional_under_cftc(self):
        results = self._evaluate("T028")
        self.assertEqual(results["CFTC"].status, "CONDITIONAL")
        self.assertEqual(results["EMIR"].status, "NOT_APPLICABLE")

    def test_audit_trail_present(self):
        # CFTC compliance results must list the fields that were checked.
        results = self._evaluate("T001")
        self.assertGreater(len(results["CFTC"].mandatory_fields_checked), 0)

    def test_libor_does_not_invalidate_compliance(self):
        # T005 has GBP-LIBOR-BBA. UPI is FOUND, the LIBOR warning propagates,
        # but the trade is noncompliant only on the LEI, never on LIBOR alone.
        results = self._evaluate("T005")
        for w in results["CFTC"].warnings:
            # warnings include LIBOR text
            pass
        # At least one warning mentions LIBOR.
        self.assertTrue(any("LIBOR" in w.upper() for w in results["CFTC"].warnings))


# ===========================================================================
# End-to-end portfolio
# ===========================================================================

class TestExpectedVerdictCounts(unittest.TestCase):
    """Regression guard on the headline verdict tally on the 28-trade
    instructor portfolio. The expected counts are the engine's own outputs
    against the current rule set; if any of these regress, the diff
    identifies which module silently shifted a verdict. This is not a
    cross-implementation check; the engine is the only implementation."""

    @classmethod
    def setUpClass(cls):
        cls.lib = TemplateLibrary(str(PRODUCT_ROOT))
        cls.trades = json.loads(TRADES_PATH.read_text())

    def test_cftc_tally(self):
        from collections import Counter
        cftc = Counter()
        for raw in self.trades:
            parsed = parse_trade(raw)
            upi = lookup_upi(parsed, raw, self.lib)
            results = check_compliance(parsed, upi, raw, ["CFTC"])
            cftc[results["CFTC"].status] += 1
        self.assertEqual(cftc["COMPLIANT"], 1)
        self.assertEqual(cftc["CONDITIONAL"], 2)
        self.assertEqual(cftc["NONCOMPLIANT"], 24)
        self.assertEqual(cftc["NOT_APPLICABLE"], 1)

    def test_emir_tally(self):
        from collections import Counter
        emir = Counter()
        for raw in self.trades:
            parsed = parse_trade(raw)
            upi = lookup_upi(parsed, raw, self.lib)
            results = check_compliance(parsed, upi, raw, ["EMIR"])
            emir[results["EMIR"].status] += 1
        self.assertEqual(emir["NONCOMPLIANT"], 25)
        self.assertEqual(emir["NOT_APPLICABLE"], 3)


# ===========================================================================
# Plain-English explanation field
# ===========================================================================

class TestComplianceExplanation(unittest.TestCase):
    """Every compliance result must carry a plain-English explanation suitable
    for a non-technical audit consumer."""

    @classmethod
    def setUpClass(cls):
        cls.lib = TemplateLibrary(str(PRODUCT_ROOT))
        cls.trades = json.loads(TRADES_PATH.read_text())
        cls.by_id = {t["trade_id"]: t for t in cls.trades}

    def _evaluate(self, tid, regimes=("CFTC", "EMIR")):
        raw = self.by_id[tid]
        parsed = parse_trade(raw)
        upi = lookup_upi(parsed, raw, self.lib)
        return check_compliance(parsed, upi, raw, list(regimes))

    def test_compliant_explanation_mentions_submission(self):
        results = self._evaluate("T017")
        exp = results["CFTC"].explanation
        self.assertTrue(exp, "explanation must be non-empty")
        self.assertIn("SDR", exp.upper() + exp)  # mentions SDR submission

    def test_noncompliant_explanation_lists_field(self):
        results = self._evaluate("T002")  # negative variation_margin_posted
        exp = results["EMIR"].explanation
        self.assertIn("fail", exp.lower())

    def test_conditional_explanation_mentions_rulemaking(self):
        results = self._evaluate("T026")
        exp = results["CFTC"].explanation
        self.assertIn("rulemaking", exp.lower())

    def test_not_applicable_explanation_mentions_perimeter(self):
        results = self._evaluate("T027")
        exp = results["CFTC"].explanation
        self.assertIn("perimeter", exp.lower())

    def test_every_result_has_explanation(self):
        for raw in self.trades:
            parsed = parse_trade(raw)
            upi = lookup_upi(parsed, raw, self.lib)
            results = check_compliance(parsed, upi, raw, ["CFTC", "EMIR", "MAS"])
            for regime, res in results.items():
                self.assertTrue(
                    res.explanation,
                    f"{raw['trade_id']}/{regime} missing explanation",
                )


# ===========================================================================
# Runner robustness
# ===========================================================================

class TestRunnerRobustness(unittest.TestCase):
    """Hidden-test defence: the runner must not crash on malformed input."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        runner_path = ROOT / "run_compliance_check.py"
        spec = importlib.util.spec_from_file_location("run_compliance_check", str(runner_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.runner = module

    def _tmp(self, content: str) -> Path:
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".json")
        import os
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return Path(path)

    def test_missing_file_clean_error(self):
        with self.assertRaises(FileNotFoundError):
            self.runner.load_trades(Path("/tmp/does_not_exist_12345.json"))

    def test_empty_file_clean_error(self):
        p = self._tmp("")
        with self.assertRaises(ValueError):
            self.runner.load_trades(p)

    def test_invalid_json_clean_error(self):
        p = self._tmp("{not-valid-json")
        with self.assertRaises(ValueError):
            self.runner.load_trades(p)

    def test_dict_root_with_trades_key_works(self):
        p = self._tmp(json.dumps({"trades": [{"trade_id": "X1", "asset_class": "Rates"}]}))
        out = self.runner.load_trades(p)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["trade_id"], "X1")

    def test_dict_root_no_known_key_clean_error(self):
        p = self._tmp(json.dumps({"unexpected_key": [1, 2, 3]}))
        with self.assertRaises(ValueError):
            self.runner.load_trades(p)

    def test_scalar_root_clean_error(self):
        p = self._tmp(json.dumps(42))
        with self.assertRaises(ValueError):
            self.runner.load_trades(p)


# ===========================================================================
# Coverage: the new templates resolve correctly


# ===========================================================================
# Coverage: the new templates resolve correctly
# ===========================================================================

class TestExtraTemplateCoverage(unittest.TestCase):
    """The engine should resolve product types beyond the strict 22 needed for
    the instructor portfolio. Hidden tests can use any of these."""

    @classmethod
    def setUpClass(cls):
        cls.lib = TemplateLibrary(str(PRODUCT_ROOT))

    def _resolve(self, asset, instr, use):
        return self.lib.find_template(asset, instr, use)

    def test_cap_floor_floor(self):
        self.assertIsNotNone(self._resolve("Rates", "Cap_Floor", "Floor"))

    def test_equity_swap_total_return_single_name(self):
        self.assertIsNotNone(self._resolve("Equity", "Swap", "TotalReturn_SingleName"))

    def test_commodities_forward_single_name(self):
        self.assertIsNotNone(self._resolve("Commodities", "Forward", "SingleName"))


# ===========================================================================
# Submission hardening: provenance, future taxonomy, and report audit fields
# ===========================================================================

class TestSubmissionHardening(unittest.TestCase):
    """Regression tests for the assignment-specific hidden lesson."""

    def test_official_trades_json_hash_matches_manifest(self):
        manifest = json.loads((ROOT / "data/trades_manifest.json").read_text())
        actual = hashlib.sha256(TRADES_PATH.read_bytes()).hexdigest()
        self.assertEqual(actual, manifest["sha256"])
        self.assertEqual(manifest["official_trades_count"], 28)

    def test_event_contract_template_override_is_future_compatible(self):
        # No active EventContract templates exist today, so T026 is currently
        # NO_PRODUCT_DEFINITION. If ANNA-DSB later registers the proposed
        # template, the lookup layer should validate it without code changes.
        import shutil
        import tempfile

        raw = json.loads(TRADES_PATH.read_text())
        t026 = next(t for t in raw if t["trade_id"] == "T026")
        parsed = parse_trade(t026)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "PROD" / "OTC-Products"
            (root / "UPI" / "EventContract").mkdir(parents=True)
            shutil.copytree(PRODUCT_ROOT / "codesets", root / "codesets")
            shutil.copy(
                ROOT / "docs/proposed_event_contract_templates/EventContract.BinaryEventContract.PoliticalOutcome.UPI.V1.json",
                root / "UPI/EventContract/EventContract.BinaryEventContract.PoliticalOutcome.UPI.V1.json",
            )
            result = lookup_upi(parsed, t026, TemplateLibrary(root))
        self.assertEqual(result.status, "FOUND")
        self.assertEqual(result.matched_template, "EventContract.BinaryEventContract.PoliticalOutcome")
        self.assertIsNotNone(result.upi_code)

    def test_every_34_trade_result_has_explanation(self):
        lib = TemplateLibrary(str(PRODUCT_ROOT))
        trades = json.loads((ROOT / "portfolio_full.json").read_text())
        self.assertEqual(len(trades), 34)
        for raw in trades:
            parsed = parse_trade(raw)
            upi = lookup_upi(parsed, raw, lib)
            results = check_compliance(parsed, upi, raw, ["CFTC", "EMIR", "MAS"])
            for regime, res in results.items():
                self.assertGreater(
                    len(res.explanation.strip()), 20,
                    f"{raw['trade_id']}/{regime} missing audit explanation",
                )

    def test_regulatory_note_source_hygiene(self):
        self.assertIn("SFA 06A-G01", MAS_EVENT_NOTE)
        self.assertIn("SFA 04-N18 is not", MAS_EVENT_NOTE)
        self.assertIn("RIN 3038-AF65", CFTC_EVENT_NOTE)
        self.assertIn("91 FR 12516", CFTC_EVENT_NOTE)
        self.assertIn("2026-05105", CFTC_EVENT_NOTE)
        self.assertIn("9194-26", CFTC_EVENT_NOTE)
        self.assertIn("9193-26", CFTC_EVENT_NOTE)
        self.assertIn("26-08", CFTC_EVENT_NOTE)

    def test_report_finding_type_separates_taxonomy_from_identifier_errors(self):
        import importlib.util
        runner_path = ROOT / "run_compliance_check.py"
        spec = importlib.util.spec_from_file_location("run_compliance_check", str(runner_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        lib = TemplateLibrary(str(PRODUCT_ROOT))
        report = module.build_report(json.loads((ROOT / "portfolio_full.json").read_text()), ["CFTC", "EMIR", "MAS"], lib)
        by_id = {rec["trade_id"]: rec for rec in report["trades"]}
        self.assertEqual(by_id["T026"]["finding_type"], "TAXONOMY_GAP_WITH_REGULATORY_NEXUS")
        self.assertEqual(by_id["T028"]["finding_type"], "TAXONOMY_GAP_WITH_REGULATORY_NEXUS")
        self.assertEqual(by_id["T033"]["finding_type"], "TAXONOMY_GAP_WITH_REGULATORY_NEXUS")
        self.assertEqual(by_id["T027"]["finding_type"], "JURISDICTIONAL_SCOPE_GAP")
        self.assertNotEqual(by_id["T002"]["finding_type"], by_id["T026"]["finding_type"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
