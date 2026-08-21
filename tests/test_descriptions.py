"""Phase 2 tests: evidence-based description generation.

Run:  python -m unittest tests.test_descriptions -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.descriptions import (
    mobile_desc, invoice_desc, short_desc, long_desc1, retail_desc,
    marketing_description, item_features, additional_information,
    mobile_in_range, FORBIDDEN_FILLER, MOBILE_MIN, MOBILE_MAX, INVOICE_MAX,
)
from src.extract import extract_all
from src.pipeline import process_row


class MobileDescTests(unittest.TestCase):
    def test_rich_evidence_lands_in_60_80(self):
        s = mobile_desc("Whirlpool Corporation", "Whirlpool®", "Dishwasher",
                        "Eco Series", "WDTS7024RZ", "Built-in", "")
        self.assertTrue(mobile_in_range(s),
                        "expected 60-80 chars, got %d: %r" % (len(s), s))
        for piece in ("Whirlpool", "Dishwasher", "Eco Series", "WDTS7024RZ"):
            self.assertIn(piece, s)

    def test_sparse_evidence_prefers_short_over_filler(self):
        s = mobile_desc("", "Satco", "LED Light Bulb", "", "564922", "", "")
        self.assertLessEqual(len(s), MOBILE_MAX)
        self.assertLess(len(s), MOBILE_MIN)  # shorter, not padded
        for piece in ("Satco", "LED Light Bulb", "564922"):
            self.assertIn(piece, s)

    def test_never_exceeds_80(self):
        s = mobile_desc("Some Very Long Manufacturer Name Inc",
                        "Brandname", "Extra Long Product Type Name",
                        "Deluxe Ultra Premium Series", "ABCDEF1234567890",
                        "Built-in", "")
        self.assertLessEqual(len(s), MOBILE_MAX)

    def test_validator_bounds(self):
        self.assertFalse(mobile_in_range("x" * 59))
        self.assertTrue(mobile_in_range("x" * 60))
        self.assertTrue(mobile_in_range("x" * 80))
        self.assertFalse(mobile_in_range("x" * 81))


class InvoiceDescTests(unittest.TestCase):
    ATTRS = [
        ("Series", "Eco Series", ""),
        ("Number of Wash Cycles", "5", ""),
        ("Voltage Rating", "120", "V"),
        ("Amperage Rating", "15", "A"),
        ("Sound Level", "47", "dBA"),
        ("Material", "Stainless Steel", ""),
        ("Mounting Type", "Leg", ""),
    ]

    def test_length_and_uppercase(self):
        s = invoice_desc("x", self.ATTRS, "Dishwasher", "PDSH4816AF")
        self.assertLessEqual(len(s), INVOICE_MAX)
        self.assertEqual(s, s.upper())

    def test_supported_tokens_present(self):
        s = invoice_desc("x", self.ATTRS, "Dishwasher", "PDSH4816AF")
        for tok in ("DISHWASHER", "LEG", "5", "SST", "120V", "15A"):
            self.assertIn(tok, s)

    def test_empty_attrs_gives_product_only(self):
        s = invoice_desc("x", [], "Cut-Off Disc", "49-94-1940")
        self.assertLessEqual(len(s), INVOICE_MAX)
        self.assertEqual(s, s.upper())


class FillerTests(unittest.TestCase):
    ROWS = [  # real rows from different categories
        {"Mfg_Part_Num": "PDSH4816AF",
         "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only"},
        {"Mfg_Part_Num": "DC5004WE", "Part_Desc": "DC5004WE SQ Elect Dryer Wh"},
        {"Mfg_Part_Num": "49-94-1940",
         "Part_Desc": "49-94-1940 Milw 14\"x1/8\"x1\" Masonry Cut Off Disc"},
        {"Mfg_Part_Num": "AGB15512BS",
         "Part_Desc": "AGB15512BS 1x6-12' Brownstone Grooved - Harvest Azek PVC Decking"},
        {"Mfg_Part_Num": "564922", "Part_Desc": "564922 60W Led BA11 50k 3pk"},
        {"Mfg_Part_Num": "10-4 SO", "Part_Desc": "10-4 SO Cord (Linear Foot)"},
    ]
    GENERATED = ["MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC", "LONG_DESC1",
                 "RETAIL_DESC", "MARKETING_DESCRIPTION"] + \
                ["ITEM_FEATURES_%d" % i for i in range(1, 11)]

    def test_marketing_always_blank(self):
        self.assertEqual(marketing_description("x", [], "BRAND", "Widget"), "")
        self.assertEqual(
            marketing_description("x", [("Material", "Steel", "")], "B", "W"), "")

    def test_item_features_no_padding(self):
        self.assertEqual(item_features([]), [])
        feats = item_features([("Voltage Rating", "120", "V")])
        self.assertEqual(feats, ["Voltage Rating: 120 V"])

    def test_no_forbidden_phrases_in_any_generated_field(self):
        banned = tuple(f.lower() for f in FORBIDDEN_FILLER)
        for row in self.ROWS:
            out = process_row(row)
            for k in self.GENERATED:
                low = (out.get(k) or "").lower()
                for phrase in banned:
                    self.assertNotIn(phrase, low,
                                     "%s leaked into %s of %r" %
                                     (phrase, k, row["Mfg_Part_Num"]))


class UnsupportedValueTests(unittest.TestCase):
    def test_no_voltage_or_sound_when_absent_from_desc(self):
        desc = "AGB15512BS 1x6-12' Brownstone Grooved - Harvest Azek PVC Decking"
        attrs = extract_all(desc, "AGB15512BS", "Trex")
        short = short_desc(desc, attrs, "Trex", "", "AGB15512BS",
                           "Decking Board", "")
        long1 = long_desc1(desc, attrs, "Trex", "Decking Board", "", "")
        inv = invoice_desc(desc, attrs, "Decking Board", "AGB15512BS")
        for text in (short, long1, inv):
            self.assertNotIn(" V", text)
            self.assertNotIn("DBA", text.upper().replace("DBA", "DBA"))
            self.assertNotIn("120", text)

    def test_supported_wattage_does_appear(self):
        desc = "564922 60W Led BA11 50k 3pk"
        attrs = extract_all(desc, "564922", "Satco")
        labels = [lab for lab, _, _ in attrs]
        self.assertIn("Wattage", labels)
        long1 = long_desc1(desc, attrs, "Satco", "LED Light Bulb", "", "")
        self.assertIn("60 W", long1)

    def test_retail_has_no_brand_or_mpn(self):
        attrs = [("Mounting Type", "Leg", ""), ("Material", "Stainless Steel", "")]
        s = retail_desc("x", attrs, "Dishwasher", "Professional Series")
        self.assertEqual(s, "Professional Series Dishwasher, Leg Mounting, "
                            "Stainless Steel")
        self.assertNotIn("FRIGIDAIRE", s.upper())
        self.assertNotIn("PDSH4816AF", s)

    def test_additional_information_word_boundary(self):
        # 'eco' must not match inside unrelated words
        self.assertEqual(additional_information("Economy Grade Widget", []), [])


class IntegrationTests(unittest.TestCase):
    """Category-aware checks across real rows from different families."""

    CASES = [
        ("PDSH4816AF", "PDSH4816AF Dishwasher SS - Display Only"),
        ("DC5004WE", "DC5004WE SQ Elect Dryer Wh"),
        ("49-94-1940", "49-94-1940 Milw 14\"x1/8\"x1\" Masonry Cut Off Disc"),
        ("AGB15512BS",
         "AGB15512BS 1x6-12' Brownstone Grooved - Harvest Azek PVC Decking"),
        ("564922", "564922 60W Led BA11 50k 3pk"),
        ("10-4 SO", "10-4 SO Cord (Linear Foot)"),
    ]

    def test_all_categories_respect_limits(self):
        for mpn, desc in self.CASES:
            out = process_row({"Mfg_Part_Num": mpn, "Part_Desc": desc})
            mob = out["MOBILE_DESC"]
            self.assertLessEqual(len(mob), MOBILE_MAX, "%r -> %r" % (mpn, mob))
            inv = out["INVOICE_DESC"]
            self.assertLessEqual(len(inv), INVOICE_MAX, "%r -> %r" % (mpn, inv))
            self.assertEqual(inv, inv.upper(), "%r -> %r" % (mpn, inv))
            if mob:
                self.assertTrue(mobile_in_range(mob) or len(mob) < MOBILE_MIN,
                                "%r mobile=%d not in range and not short"
                                % (mpn, len(mob)))

    def test_placeholders_still_preserved(self):
        row = {"Mfg_Part_Num": "X1",
               "Part_Desc": "X1 Widget Steel",
               "E1_Brand": "-- Unbranded --",
               "Unilog_Brand": "-- No Unilog Brand --",
               "DIB_Brand": "-- No DIB Brand --",
               "Part_Manuf": "-"}
        out = process_row(row)
        self.assertEqual(out["E1_Brand"], "-- Unbranded --")
        self.assertEqual(out["Unilog_Brand"], "-- No Unilog Brand --")
        self.assertEqual(out["DIB_Brand"], "-- No DIB Brand --")
        self.assertEqual(out["Part_Manuf"], "-")
        self.assertEqual(out["PART_NUMBER"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
