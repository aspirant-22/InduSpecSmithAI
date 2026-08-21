"""Phase 8 tests: confidence scoring + report-only duplicate analysis.

Run:  python -m unittest tests.test_review -v
"""
import csv
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.review import (
    BAND_HIGH_MIN, BAND_MEDIUM_MIN, WEIGHTS,
    attr_slot_count, build_review_rows, duplicate_desc_groups,
    duplicate_mpn_groups, leading_token_mismatch, score_row, suspected_typo,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(ROOT, "data", "input",
                     "Unihack_ Sample Dataset - Input.csv")
OUTPUT = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        headers = next(rdr)
        return [dict(zip(headers, r)) for r in rdr]


def out_row(overrides=None):
    """Minimal generated-output row for scoring tests."""
    r = {"MOBILE_DESC": "x" * 70, "MANUFACTURER_NAME": "Acme",
         "BRAND_NAME": "Acme"}
    for i in range(1, 51):
        r["ATTRIBUTE_LABEL %d" % i] = ""
    r.update(overrides or {})
    return r


def in_row(mpn="ABC123", desc="ABC123 Widget Steel 4 in"):
    return {"Mfg_Part_Num": mpn, "Part_Desc": desc}


class ScoreTests(unittest.TestCase):
    def test_perfect_row_scores_100_high(self):
        s = score_row(in_row(), out_row({"ATTRIBUTE_LABEL 1": "Material"}))
        self.assertEqual(s["confidence"], 100)
        self.assertEqual(s["band"], "HIGH")
        self.assertFalse(s["needs_human_review"])
        self.assertEqual(s["reasons"], [])

    def test_each_penalty_weight_is_documented_and_applied_once(self):
        base_in = in_row()
        base_out = out_row({"ATTRIBUTE_LABEL 1": "Material"})
        cases = [
            ("no_attributes", out_row(), 25),
            ("mobile_desc_short",
             out_row({"ATTRIBUTE_LABEL 1": "Material",
                      "MOBILE_DESC": "x" * 59}), 15),
            ("manufacturer_unresolved",
             out_row({"ATTRIBUTE_LABEL 1": "Material",
                      "MANUFACTURER_NAME": ""}), 10),
            ("brand_unresolved",
             out_row({"ATTRIBUTE_LABEL 1": "Material",
                      "BRAND_NAME": ""}), 5),
            ("sparse_input_desc", None, 10),
            ("mpn_desc_mismatch", None, 5),
        ]
        for reason, o, weight in cases:
            self.assertEqual(WEIGHTS[reason], weight)
            if reason == "sparse_input_desc":
                s = score_row(in_row(desc="short"), base_out)
            elif reason == "mpn_desc_mismatch":
                s = score_row(in_row(desc="XYZ98765 Widget Steel 4 in"),
                              base_out)
            else:
                s = score_row(base_in, o)
            self.assertIn(reason, s["reasons"], reason)
            self.assertEqual(s["confidence"], 100 - weight, reason)

    def test_duplicate_mpn_penalty_applied_via_dup_sizes(self):
        s = score_row(in_row("AVM6EV", "AVM6 EV Mini Snip Red"),
                      out_row({"ATTRIBUTE_LABEL 1": "Material"}),
                      dup_sizes={"AVM6EV": 2})
        self.assertIn("duplicate_mpn_group", s["reasons"])
        self.assertEqual(s["confidence"], 85)

    def test_typo_flagged(self):
        self.assertEqual(suspected_typo(in_row(desc="rachet Wrench 3/8 in")),
                         "rachet")
        s = score_row(in_row(desc="rachet Wrench 3/8 in drive"),
                      out_row({"ATTRIBUTE_LABEL 1": "Size"}))
        self.assertIn("suspected_typo", s["reasons"])

    def test_ordinary_first_word_never_counts_as_mismatch(self):
        self.assertFalse(leading_token_mismatch(
            in_row(desc="Widget Steel 4 in")))
        self.assertTrue(leading_token_mismatch(
            in_row(desc="ABC-123X Widget")))

    def test_band_boundaries(self):
        # exactly one penalty -> 90, HIGH, not flagged
        s = score_row(in_row(), out_row({"ATTRIBUTE_LABEL 1": "Material",
                                         "MANUFACTURER_NAME": ""}))
        self.assertEqual(s["confidence"], 90)
        self.assertEqual(s["band"], "HIGH")
        # drop to exactly 60 -> still MEDIUM
        s = score_row(in_row(),
                      out_row({"ATTRIBUTE_LABEL 1": "Material",
                               "MANUFACTURER_NAME": "",
                               "BRAND_NAME": "",
                               "MOBILE_DESC": "x" * 55}))
        self.assertEqual(s["confidence"], 100 - 10 - 5 - 15)
        self.assertEqual(s["band"], "MEDIUM")
        self.assertFalse(s["needs_human_review"])
        # one more small penalty crosses into LOW
        s = score_row(in_row(desc="ABC123 a"),
                      out_row({"MANUFACTURER_NAME": "",
                               "BRAND_NAME": "",
                               "MOBILE_DESC": "x" * 55}))
        self.assertLess(s["confidence"], BAND_MEDIUM_MIN)
        self.assertEqual(s["band"], "LOW")
        self.assertTrue(s["needs_human_review"])
        self.assertGreaterEqual(BAND_HIGH_MIN, BAND_MEDIUM_MIN)

    def test_score_floors_at_zero_and_is_deterministic(self):
        worst_in = in_row("AVM6EV", "rachet")
        worst_out = out_row({"MOBILE_DESC": "", "MANUFACTURER_NAME": "",
                             "BRAND_NAME": ""})
        a = score_row(worst_in, worst_out, dup_sizes={"AVM6EV": 2})
        b = score_row(worst_in, worst_out, dup_sizes={"AVM6EV": 2})
        self.assertEqual(a, b)
        self.assertGreaterEqual(a["confidence"], 0)


class DuplicateGroupTests(unittest.TestCase):
    def test_avm6ev_group_found_with_both_positions(self):
        rows = load_csv(INPUT)
        groups = duplicate_mpn_groups(rows)
        self.assertEqual(groups.get("AVM6EV"), [783, 784])

    def test_avm6ev_rows_both_present_and_unmerged_in_output(self):
        inp, out = load_csv(INPUT), load_csv(OUTPUT)
        self.assertEqual(len(inp), len(out))
        for pos in (783, 784):  # 1-based data-row numbers
            self.assertEqual(inp[pos - 1]["Mfg_Part_Num"], "AVM6EV")
            self.assertEqual(out[pos - 1]["Mfg_Part_Num"], "AVM6EV")
        descs = {inp[p - 1]["Part_Desc"] for p in (783, 784)}
        self.assertEqual(len(descs), 2)

    def test_duplicate_description_groups(self):
        rows = [{"Part_Desc": "Same Thing"},
                {"Part_Desc": "same thing"},
                {"Part_Desc": "Different Item"},
                {"Part_Desc": ""}]
        groups = duplicate_desc_groups(rows)
        self.assertEqual(groups, {"same thing": [1, 2]})

    def test_unique_mpns_produce_no_groups(self):
        rows = [{"Mfg_Part_Num": "A"}, {"Mfg_Part_Num": "B"}]
        self.assertEqual(duplicate_mpn_groups(rows), {})


class BuildReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp = load_csv(INPUT)
        cls.out = load_csv(OUTPUT)
        cls.records = build_review_rows(cls.inp, cls.out)

    def test_positional_alignment_full_dataset(self):
        self.assertEqual(len(self.records), 1000)
        for pos, rec in enumerate(self.records):
            self.assertEqual(rec["row"], pos + 1)
            self.assertEqual(rec["mfg_part_num"],
                             self.inp[pos]["Mfg_Part_Num"].strip())

    def test_scores_within_range_and_bands_valid(self):
        for rec in self.records:
            self.assertTrue(0 <= rec["confidence"] <= 100)
            self.assertIn(rec["band"], ("HIGH", "MEDIUM", "LOW"))
            self.assertEqual(rec["needs_human_review"],
                             rec["band"] == "LOW")

    def test_gt_dishwashers_score_high_with_honest_reasons(self):
        by_mpn = {r["mfg_part_num"]: r for r in self.records}
        pd = by_mpn["PDSH4816AF"]
        self.assertEqual((pd["band"], pd["confidence"]), ("HIGH", 100))
        wd = by_mpn["WDTS7024RZ"]
        self.assertEqual(wd["band"], "HIGH")
        self.assertIn("mobile_desc_short", wd["reasons"])
        self.assertFalse(wd["needs_human_review"])

    def test_duplicate_size_recorded_on_avm6ev_rows(self):
        avm = [r for r in self.records
               if r["mfg_part_num"] == "AVM6EV"]
        self.assertEqual(len(avm), 2)
        for rec in avm:
            self.assertEqual(rec["duplicate_group_size"], 2)
            self.assertIn("duplicate_mpn_group", rec["reasons"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
