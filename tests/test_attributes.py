"""Phase 4 tests: evidence-based attribute extraction & provenance.

Run:  python -m unittest tests.test_attributes -v
"""
import csv
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extract import extract_all
from src.facts import (Fact, COPIED, NORMALIZED, DERIVED, INFERRED, UNKNOWN,
                       provenance_totals)
from src.pipeline import process_row, DISHWASHER_SCHEMA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BULB_DESC = "564922 60W Led BA11 50k 3pk"
DISHWASHER_DESC = "KDFM404KPS Dishwasher SS"
SPARSE_DESC = "Widget Steel 4 in"


def _labels(attrs):
    return [f.label for f in attrs]


class ExtractionTests(unittest.TestCase):
    def test_direct_extraction_bulb(self):
        attrs = extract_all(BULB_DESC, "564922", "Philips")
        by = {f.label: f for f in attrs}
        self.assertEqual(by["Wattage"].value, "60")
        self.assertEqual(by["Wattage"].uom, "W")
        self.assertEqual(by["Package Quantity"].value, "3")
        self.assertIn(by["Package Quantity"].uom.lower(), ("pk", "pc"))

    def test_deterministic_normalization_color_temperature(self):
        attrs = extract_all(BULB_DESC, "564922", "Philips")
        ct = {f.label: f for f in attrs}["Color Temperature"]
        self.assertEqual(ct.value, "5000")
        self.assertEqual(ct.uom, "K")

    def test_voltage_normalization(self):
        attrs = extract_all("Motor 120V 15 Amp", "X1", "")
        by = {f.label: f for f in attrs}
        self.assertEqual(by["Voltage Rating"].triple, ("Voltage Rating", "120", "V"))
        self.assertEqual(by["Amperage Rating"].value, "15")

    def test_every_fact_carries_evidence_and_status(self):
        for f in extract_all(BULB_DESC, "564922", "Philips"):
            self.assertTrue(f.evidence, f.label)
            self.assertEqual(f.status, NORMALIZED)

    def test_no_match_returns_no_fact(self):
        labels = _labels(extract_all("Plain Widget", "X1", ""))
        self.assertNotIn("Voltage Rating", labels)
        self.assertNotIn("Sound Level", labels)
        self.assertNotIn("Color Temperature", labels)


class MappingTests(unittest.TestCase):
    def test_dishwasher_schema_labels_exact_order(self):
        out = process_row({"Mfg_Part_Num": "KDFM404KPS",
                           "Part_Desc": DISHWASHER_DESC})
        got = [out["ATTRIBUTE_LABEL %d" % i] for i in range(1, 16)]
        self.assertEqual(got, DISHWASHER_SCHEMA)

    def test_schema_blank_values_stay_labeled(self):
        out = process_row({"Mfg_Part_Num": "KDFM404KPS",
                           "Part_Desc": DISHWASHER_DESC})
        model_i = DISHWASHER_SCHEMA.index("Model") + 1
        plug_i = DISHWASHER_SCHEMA.index("Plug Type") + 1
        self.assertEqual(out["ATTRIBUTE_LABEL %d" % model_i], "Model")
        self.assertEqual(out["ATTRIBUTE_VALUE %d" % model_i], "")
        self.assertEqual(out["ATTRIBUTE_LABEL %d" % plug_i], "Plug Type")
        self.assertEqual(out["ATTRIBUTE_VALUE %d" % plug_i], "")

    def test_supported_value_fills_schema_slot(self):
        out = process_row({"Mfg_Part_Num": "KDFM404KPS",
                           "Part_Desc": DISHWASHER_DESC})
        mat_i = DISHWASHER_SCHEMA.index("Material") + 1
        self.assertEqual(out["ATTRIBUTE_LABEL %d" % mat_i], "Material")
        self.assertEqual(out["ATTRIBUTE_VALUE %d" % mat_i], "Stainless Steel")

    def test_non_dishwasher_keeps_extraction_order(self):
        out = process_row({"Mfg_Part_Num": "564922", "Part_Desc": BULB_DESC})
        expected = _labels(extract_all(BULB_DESC, "", ""))
        got = [out["ATTRIBUTE_LABEL %d" % i] for i in range(1, len(expected) + 1)]
        self.assertEqual(got, expected)
        # deterministic: rerun gives identical columns
        out2 = process_row({"Mfg_Part_Num": "564922", "Part_Desc": BULB_DESC})
        for i in range(1, 51):
            for k in ("LABEL", "VALUE", "UOM"):
                col = "ATTRIBUTE_%s %d" % (k, i)
                self.assertEqual(out[col], out2[col])

    def test_unused_slots_blank(self):
        out = process_row({"Mfg_Part_Num": "564922", "Part_Desc": BULB_DESC})
        n_labels = len(_labels(extract_all(BULB_DESC, "", "")))
        for i in range(n_labels + 1, 51):
            self.assertEqual(out["ATTRIBUTE_LABEL %d" % i], "")


class NoHallucinationTests(unittest.TestCase):
    FORBIDDEN_LABELS = {"Warranty", "Certification", "Country Of Origin",
                        "Capacity", "Lumens"}

    def test_sparse_desc_leaves_unsupported_blank(self):
        out = process_row({"Mfg_Part_Num": "X1", "Part_Desc": SPARSE_DESC})
        emitted = {}
        for i in range(1, 51):
            lab = out["ATTRIBUTE_LABEL %d" % i]
            if lab:
                emitted[lab] = out["ATTRIBUTE_VALUE %d" % i]
        self.assertEqual(emitted, {"Material": "Steel"})

    def test_no_forbidden_labels_anywhere(self):
        for desc in (BULB_DESC, DISHWASHER_DESC, SPARSE_DESC,
                     '49-94-1940 Milw 14"x1/8"x1" Masonry Cut Off Disc'):
            out = process_row({"Mfg_Part_Num": "T", "Part_Desc": desc})
            for i in range(1, 51):
                lab = out["ATTRIBUTE_LABEL %d" % i]
                if lab:
                    self.assertNotIn(lab, self.FORBIDDEN_LABELS - {"Lumens"}
                                     | ({"Lumens"} if "lm" not in desc.lower()
                                        else set()))

    def test_placeholder_brands_create_no_attributes(self):
        row = {"Mfg_Part_Num": "XYZ123", "Part_Desc": SPARSE_DESC,
               "E1_Brand": "-- Unbranded --",
               "Unilog_Brand": "-- No Unilog Brand --",
               "DIB_Brand": "-- No DIB Brand --", "Part_Manuf": "-"}
        out = process_row(row)
        brands = [out["E1_Brand"], out["Unilog_Brand"],
                  out["DIB_Brand"], out["Part_Manuf"]]
        joined = " ".join(out["ATTRIBUTE_LABEL %d" % i] + " " +
                          out["ATTRIBUTE_VALUE %d" % i]
                          for i in range(1, 51)).lower()
        self.assertEqual(brands[0], "-- Unbranded --")
        for bad in ("unbranded", "no unilog", "no dib"):
            self.assertNotIn(bad, joined)


class ProvenanceTests(unittest.TestCase):
    def test_status_classification(self):
        facts = extract_all(BULB_DESC, "564922", "Philips")
        self.assertTrue(all(f.status == NORMALIZED for f in facts))

    def test_derived_and_unknown_in_schema(self):
        from src.pipeline import _attribute_slots
        slots = _attribute_slots("Dishwasher", extract_all(DISHWASHER_DESC,
                                                           "K", ""), "")
        addl = [f for f in slots if f.label == "Additional Information"][0]
        self.assertEqual(addl.status, UNKNOWN)
        slots2 = _attribute_slots("Dishwasher", [], "Sensor Cycle")
        addl2 = [f for f in slots2 if f.label == "Additional Information"][0]
        self.assertEqual(addl2.status, DERIVED)
        self.assertEqual(addl2.value, "Sensor Cycle")

    def test_provenance_totals_counts(self):
        rows = [extract_all(BULB_DESC, "", ""),
                extract_all(SPARSE_DESC, "", "")]
        totals = provenance_totals(rows)
        self.assertGreater(totals["emitted_populated"], 0)
        self.assertEqual(totals["by_status"]["INFERRED"], 0)


class RegressionTests(unittest.TestCase):
    """Phase 1-3 protection inside the Phase-4 suite."""

    def test_six_input_columns_verbatim(self):
        with open(ROOT + r"\data\input\Unihack_ Sample Dataset - Input.csv",
                  encoding="utf-8-sig") as f:
            inp = list(csv.DictReader(f))
        sample = inp[0]
        out = process_row(sample)
        for c in ["Mfg_Part_Num", "Part_Desc", "E1_Brand", "Unilog_Brand",
                  "DIB_Brand", "Part_Manuf"]:
            self.assertEqual(out[c], sample[c].strip())

    def test_header_parity_unchanged(self):
        with open(ROOT + r"\data\input\Unihack_ Expected Output - Delivery Format.csv",
                  encoding="utf-8-sig") as f:
            hdr = next(csv.reader(f))
        self.assertEqual(len(hdr), 252)

    def test_asset_fields_still_generated(self):
        out = process_row({"Mfg_Part_Num": "WDTS7024RZ",
                           "Part_Desc": "WDTS7024RZ Dishwasher SS"})
        self.assertEqual(out["Product Image"], "Whirlpool_WDTS7024RZ.jpg")
        self.assertEqual(out["Actual Image (Yes/No)"], "")

    def test_descriptions_unchanged_contract(self):
        out = process_row({"Mfg_Part_Num": "PDSH4816AF",
                           "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only"})
        self.assertLessEqual(len(out["INVOICE_DESC"]), 40)
        self.assertEqual(out["MARKETING_DESCRIPTION"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
