"""Phase 5 tests: evaluation engine (A-K sections).

Run:  python -m unittest tests.test_evaluation -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.evaluate import (
    check_header_parity, check_row_counts, check_input_preservation,
    ground_truth_scores, _match_gt_row, char_limit_compliance,
    unsupported_value_scan, data_quality_flags, coverage_by_category,
    blank_field_analysis, render_report, main as eval_main,
    DISCLAIMER, SIX_COLUMNS, ROOT,
)

H3 = ["Mfg_Part_Num", "Part_Desc", "MOBILE_DESC"]


def row(mpn, desc, **kw):
    r = {"Mfg_Part_Num": mpn, "Part_Desc": desc}
    r.update(kw)
    return r


class HeaderParityTests(unittest.TestCase):
    def test_identical_pass(self):
        r = check_header_parity(H3, ["Mfg_Part_Num", "Part_Desc", "MOBILE_DESC"])
        self.assertTrue(r["pass"])
        self.assertEqual(r["expected_count"], 3)

    def test_missing_and_extra_detected(self):
        r = check_header_parity(["A", "B"], ["B", "C"])
        self.assertFalse(r["pass"])
        self.assertEqual(r["missing"], ["A"])
        self.assertEqual(r["extra"], ["C"])

    def test_order_mismatch_detected(self):
        r = check_header_parity(["A", "B"], ["B", "A"])
        self.assertFalse(r["pass"])
        self.assertTrue(r["order_mismatch"])


class RowCountTests(unittest.TestCase):
    def test_equal_pass(self):
        self.assertTrue(check_row_counts(1000, 1000)["pass"])

    def test_missing_and_extra(self):
        r = check_row_counts(1000, 998)
        self.assertFalse(r["pass"])
        self.assertEqual(r["missing_rows"], 2)
        r2 = check_row_counts(10, 12)
        self.assertEqual(r2["extra_rows"], 2)


class PreservationTests(unittest.TestCase):
    def test_positional_match(self):
        ins = [row("M1", "D1", E1_Brand="-- Unbranded --"),
               row("M1", "D-different")]  # duplicate MPN, different desc
        outs = [row("M1", "D1", E1_Brand="-- Unbranded --"), row("M1", "D-different")]
        r = check_input_preservation(ins, outs)
        self.assertTrue(r["pass"])
        self.assertEqual(r["compared_cells"], 12)  # 6 cols x 2 rows, positional

    def test_mismatch_caught_despite_duplicate_mpn(self):
        ins = [row("M1", "D1"), row("M1", "D2")]
        outs = [row("M1", "WRONG"), row("M1", "D2")]
        r = check_input_preservation(ins, outs)
        self.assertFalse(r["pass"])  # MPN-keyed matching would have missed this
        self.assertEqual(r["mismatches"], 1)
        self.assertEqual(r["mismatch_examples"][0]["row"], 0)

    def test_placeholder_preservation_counted(self):
        ins = [row("M1", "x", Unilog_Brand="-- No Unilog Brand --")]
        outs = [row("M1", "x", Unilog_Brand="-- No Unilog Brand --")]
        r = check_input_preservation(ins, outs)
        d = r["placeholder_preservation"]["Unilog_Brand"]
        self.assertEqual(d["placeholders_in_input"], 1)
        self.assertEqual(d["preserved_verbatim"], 1)


class GroundTruthTests(unittest.TestCase):
    OUT = [row("PDSH4816AF", "PDSH Dishwasher SS", MOBILE_DESC="x" * 65),
           row("AVM6EV", "Snip Red"),
           row("AVM6EV", "Snip Green")]

    def test_unique_match(self):
        got, status = _match_gt_row(row("PDSH4816AF", "PDSH Dishwasher SS"), self.OUT)
        self.assertEqual(status, "MATCHED")

    def test_ambiguous_never_guessed(self):
        got, status = _match_gt_row(row("AVM6EV", "Snip ???"), self.OUT)
        self.assertIsNone(got)
        self.assertEqual(status, "AMBIGUOUS")

    def test_unmatched(self):
        _, status = _match_gt_row(row("NOPE", "Nothing"), self.OUT)
        self.assertEqual(status, "UNMATCHED")

    def test_scores_and_populated_accuracy(self):
        gt_hdr = ["Mfg_Part_Num", "Part_Desc", "MOBILE_DESC", "Warranty"]
        gt_rows = [
            row("PDSH4816AF", "PDSH Dishwasher SS",
                MOBILE_DESC="x" * 65, Warranty="1 Year Manufacturer"),
            row("GHOST-1", "No such row", MOBILE_DESC="y" * 70),
        ]
        res = ground_truth_scores(gt_hdr, gt_rows, self.OUT)
        statuses = {r["mpn"]: r["status"] for r in res["row_matches"]}
        self.assertEqual(statuses["PDSH4816AF"], "MATCHED")
        self.assertEqual(statuses["GHOST-1"], "UNMATCHED")
        t = res["totals"]
        # matched row: Mfg_Part_Num, Part_Desc, MOBILE_DESC exact by
        # construction; Warranty populated in GT, blank in ours
        self.assertEqual(t["exact_matches"], 3)
        self.assertEqual(t["missing_predictions"], 1)
        self.assertEqual(t["incorrect_values"], 0)
        self.assertEqual(res["field_accuracy_pct"], 75.0)
        self.assertIn("Warranty", res["per_field"])

    def test_both_blank_is_not_a_miss(self):
        gt_hdr = ["Mfg_Part_Num", "Part_Desc", "MARKETING_DESCRIPTION"]
        gt_rows = [row("PDSH4816AF", "PDSH Dishwasher SS")]
        res = ground_truth_scores(gt_hdr, gt_rows, self.OUT)
        self.assertNotIn("MARKETING_DESCRIPTION", res["per_field"])
        self.assertIn("MARKETING_DESCRIPTION", res["unevaluable_field_names"])


class CharLimitTests(unittest.TestCase):
    ROWS = [row("A", "d", MOBILE_DESC="x" * 70, INVOICE_DESC="DISHWASHER SST"),
            row("B", "d", MOBILE_DESC="x" * 50, INVOICE_DESC="dishwasher"),
            row("C", "d", MOBILE_DESC="x" * 90, INVOICE_DESC="Y" * 41)]

    def test_strict_mobile_buckets(self):
        r = char_limit_compliance(self.ROWS)
        self.assertEqual(r["mobile"]["compliant_60_80"], 1)
        self.assertEqual(r["mobile"]["non_compliant_below_60_evidence_short"], 1)
        self.assertEqual(r["mobile"]["violations_above_80"], 1)
        self.assertFalse(r["pass"])  # >80 is a hard violation

    def test_invoice_limits(self):
        r = char_limit_compliance(self.ROWS)
        self.assertEqual(r["invoice"]["over_40"], 1)
        self.assertEqual(r["invoice"]["not_uppercase"], 1)

    def test_all_good_passes(self):
        rows = [row("A", "d", MOBILE_DESC="x" * 65, INVOICE_DESC="OK TOOL")]
        self.assertTrue(char_limit_compliance(rows)["pass"])


class UnsupportedValueTests(unittest.TestCase):
    BASE = dict(MOBILE_DESC="", INVOICE_DESC="", SHORT_DESC="", LONG_DESC1="",
                RETAIL_DESC="", MARKETING_DESCRIPTION="")

    def test_inferred_nonzero_fails(self):
        rows = [row("A", "d", **self.BASE)]
        r = unsupported_value_scan(rows, {"INFERRED": 2})
        self.assertFalse(r["pass"])
        self.assertEqual(r["inferred_emitted"], 2)

    def test_zero_inferred_passes_clean_rows(self):
        rows = [row("A", "d", **self.BASE)]
        self.assertTrue(unsupported_value_scan(rows, {"INFERRED": 0})["pass"])

    def test_filler_url_existence_warranty_flagged(self):
        bad = row("A", "d", **self.BASE)
        bad["SHORT_DESC"] = "Engineered for reliable performance"
        bad["MFR URL"] = "https://example.com/fake"
        bad["Actual Image (Yes/No)"] = "Yes"
        bad["Warranty"] = "1 Year Manufacturer"
        r = unsupported_value_scan([bad], {"INFERRED": 0})
        self.assertTrue(r["filler_phrases"])
        self.assertTrue(r["fabricated_urls"])
        self.assertTrue(r["asset_existence_claims"])
        self.assertTrue(r["blanket_warranty_claims"])
        self.assertFalse(r["pass"])


class DataQualityTests(unittest.TestCase):
    def test_duplicate_mpn_flagged(self):
        ins = [row("AVM6EV", "Snip Red"), row("AVM6EV", "Snip Green")]
        flags = data_quality_flags(ins, [])
        self.assertEqual(flags["duplicate_mpns"]["items"]["AVM6EV"], 2)

    def test_typo_and_sparse_flags(self):
        ins = [row("X1", "X1 Mocrowave OTR"), row("X2", "ok"),
               row("X3", "ab")]
        flags = data_quality_flags(ins, [])
        self.assertEqual(flags["suspected_typos"]["detail"].get("mocrowave"), 1)
        self.assertGreaterEqual(flags["sparse_descriptions_lt20"], 1)

    def test_mpn_desc_near_miss(self):
        ins = [row("55226BKLFU", "55226BKFLU Bracket")]
        flags = data_quality_flags(ins, [])
        self.assertEqual(flags["mpn_desc_mismatch"]["near_miss_similarity"], 1)

    def test_placeholder_and_missing_counts(self):
        ins = [row("X9", "Widget Steel", E1_Brand="-- Unbranded --",
                   Unilog_Brand="-- No Unilog Brand --",
                   DIB_Brand="-- No DIB Brand --", Part_Manuf="-")]
        outs = [row("X9", "Widget Steel", BRAND_NAME="")]
        flags = data_quality_flags(ins, outs)
        self.assertEqual(flags["placeholder_brands"]["E1_Brand"], 1)
        self.assertEqual(flags["missing_manufacturer"], 1)
        self.assertEqual(flags["missing_resolved_brand"], 1)


class CoverageBlankTests(unittest.TestCase):
    HDR = ["Mfg_Part_Num", "Part_Desc", "MOBILE_DESC"]

    def test_coverage_percent(self):
        rows = [row("A", "d", MOBILE_DESC="abc"),
                row("B", "e")]  # MOBILE_DESC blank on row 2
        cov = coverage_by_category(rows, self.HDR)
        self.assertEqual(cov["identifiers/input"]["populated"], 4)
        self.assertEqual(cov["descriptions"]["populated"], 1)
        self.assertEqual(cov["descriptions"]["blank"], 1)

    def test_blank_analysis(self):
        rows = [row("A", "d", MOBILE_DESC="")]
        b = blank_field_analysis(rows, self.HDR)
        self.assertEqual(b["total_cells"], 3)
        self.assertEqual(b["blank_cells"], 1)
        self.assertEqual(b["fully_blank_columns"], 1)


class ReportIntegrationTests(unittest.TestCase):
    def test_disclaimer_in_rendered_report(self):
        lines = render_report({
            "header": check_header_parity(H3, H3),
            "rows": check_row_counts(1, 1),
            "preservation": check_input_preservation(
                [row("M", "D")], [row("M", "D")]),
            "gt": ground_truth_scores(H3, [], []),
            "coverage": {}, "limits": char_limit_compliance([]),
            "unsupported": unsupported_value_scan([], {"INFERRED": 0}),
            "blanks": blank_field_analysis([], H3),
            "quality": data_quality_flags([], []),
            "provenance": {"NORMALIZED": 1262, "UNKNOWN": 137},
            "verdict": "PASS"})
        text = "\n".join(lines)
        self.assertIn(DISCLAIMER, text)
        self.assertIn("Overall verdict: PASS", text)

    def test_main_runs_on_real_outputs(self):
        out_csv = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")
        if not os.path.exists(out_csv):
            self.skipTest("pipeline output not present")
        self.assertEqual(eval_main(), 0)  # INFERRED=0 gate + all gates


if __name__ == "__main__":
    unittest.main(verbosity=2)
