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


class Phase6GaugeTests(unittest.TestCase):
    def _gauge(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Gauge")

    def test_nail_gauge_15ga(self):
        g = self._gauge('603150 2-1/2" Finish Nail 15GA - 4M')
        self.assertEqual(g.triple, ("Gauge", "15", "ga"))
        self.assertEqual(g.evidence, "15GA")

    def test_mixed_case_ga(self):
        g = self._gauge("Paslode CT200S24 18Ga ST Brad Nailer")
        self.assertEqual(g.value, "18")
        self.assertEqual(g.uom, "ga")

    def test_gauge_after_voltage_token(self):
        g = self._gauge('XNB04Z Makita 18V 2" Brad Nailer 18GA (Bare)')
        self.assertEqual(g.value, "18")

    def test_unrelated_numbers_not_gauge(self):
        for desc in ("Widget Steel 4 in", "Motor 120V 15 Amp",
                     "Plain Bolt 18V", "Disc 4-1/2\" x 1/8\""):
            self.assertIsNone(self._gauge(desc), desc)


class Phase6HorsepowerTests(unittest.TestCase):
    def _hp(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Horsepower")

    def test_decimal_hp(self):
        h = self._hp('JT1-549 JWBS18SFX 18" Bandsaw - 1.75HP 1PH 115V')
        self.assertEqual(h.triple, ("Horsepower", "1.75", "hp"))

    def test_integer_hp_with_voltage(self):
        by = {f.label: f for f in
              extract_all("10047VS Oliver 3HP 230V 1PH Shaper 1-1/4 Spindle",
                          "", "")}
        self.assertEqual(by["Horsepower"].triple, ("Horsepower", "3", "hp"))
        self.assertEqual(by["Voltage Rating"].value, "230")

    def test_fraction_hp(self):
        h = self._hp("Pump 1/2 HP Cast Iron")
        self.assertEqual(h.triple, ("Horsepower", "1/2", "hp"))

    def test_no_phase_attribute_invented(self):
        labels = _labels(extract_all(
            'JT1-549 JWBS18SFX 18" Bandsaw - 1.75HP 1PH 115V', "", ""))
        for bad in ("Phase", "PH", "Power Phase"):
            self.assertNotIn(bad, labels)

    def test_hp_does_not_interfere_with_voltage(self):
        by = {f.label: f for f in extract_all("2HP,115V 1Ph Motor", "", "")}
        self.assertEqual(by["Horsepower"].value, "2")
        self.assertEqual(by["Voltage Rating"].value, "115")


class Phase6SpeedTests(unittest.TestCase):
    def _speed(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Speed")

    def test_two_speed(self):
        s = self._speed("DCGG581B Dewalt 20V Grease Gun 2-Speed")
        self.assertEqual(s.triple, ("Speed", "2", ""))

    def test_space_form(self):
        s = self._speed("Drill 3 speed Reversible")
        self.assertEqual(s.value, "3")

    def test_no_speed_from_arbitrary_number(self):
        self.assertIsNone(self._speed("Grease Gun 20V"))
        self.assertIsNone(self._speed("Variable speed motor"))
        self.assertIsNone(self._speed("Widget 2"))


class Phase6RangeTests(unittest.TestCase):
    def _range(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Range")

    def test_laser_range(self):
        r = self._range("DW089CG Dewalt Laser Level - 3 Line 30ft Range")
        self.assertEqual(r.triple, ("Range", "30", "ft"))

    def test_range_prefix_form(self):
        r = self._range("Detector Range of 50 ft")
        self.assertEqual(r.triple, ("Range", "50", "ft"))

    def test_bare_feet_refused(self):
        # chalk reel line length is NOT deterministically a range
        self.assertIsNone(self._range("IWHT48441RC Irwin 100ft - Red Chalk & Reel Set"))

    def test_range_not_size(self):
        attrs = extract_all("Dewalt Laser Level - 3 Line 30ft Range", "", "")
        self.assertEqual(_labels(attrs).count("Size"), 0)


class Phase6WeightTests(unittest.TestCase):
    def _weight(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Weight")

    def test_bottle_oz(self):
        w = self._weight("48-22-8396R Milw 24oz Bottle - Insulated")
        self.assertEqual(w.triple, ("Weight", "24", "oz"))

    def test_second_bottle(self):
        w = self._weight("48-22-8397R Milw 36oz Bottle - Insulated")
        self.assertEqual(w.value, "36")

    def test_oz_without_container_refused(self):
        self.assertIsNone(self._weight("Framing Hammer 16oz"))
        self.assertIsNone(self._weight("LED Bulb 9W"))


class Phase6DimensionTests(unittest.TestCase):
    def _size(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Size")

    def test_bare_in_double(self):
        s = self._size("DCM200B Dewalt 1/2in x 18in - Band File")
        self.assertEqual(s.value, "1/2 in x 18 in")

    def test_single_blade_diameter(self):
        s = self._size("48-40-0740 Milw 7-1/4in. 24T - Framing Circ Saw Blade")
        self.assertEqual(s.value, "7-1/4 in")  # never '24 in'

    def test_dual_imperial_metric(self):
        s = self._size("BC-12300 BigCal 12\"/300mm")
        self.assertEqual(s.value, "12 in")

    def test_metric_square(self):
        s = self._size("MLSQ1120 Milw 300mm Rafter - Square (Metric)")
        self.assertEqual(s.value, "300 mm")

    def test_quoted_dims_unchanged(self):
        # existing canon: disc rows emit the diameter as Size
        s = self._size('49-94-1940 Milw 14"x1/8"x1" Masonry Cut Off Disc')
        self.assertEqual(s.value, "14 in")

    def test_spaced_single_inch_stays_refused(self):
        # project canon: 'Widget Steel 4 in' emits Material only
        self.assertIsNone(self._size("Widget Steel 4 in"))

    def test_n_in_1_trap_rejected(self):
        self.assertIsNone(self._size("3 in 1 Oil Multi Tool"))

    def test_mpn_numbers_not_dimensions(self):
        self.assertIsNone(self._size("48-40-0740 circular saw"))
        self.assertIsNone(self._size("Item 12345 in stock"))


class Phase6PackageWordTests(unittest.TestCase):
    def _pack(self, desc):
        by = {f.label: f for f in extract_all(desc, "", "")}
        return by.get("Package Quantity")

    def test_word_pack(self):
        p = self._pack("48-11-2422 Milw M12 CP2.0 Battery Two Pack")
        self.assertEqual(p.triple, ("Package Quantity", "2", "pk"))
        self.assertEqual(p.evidence, "Two Pack")

    def test_digit_pack_unchanged(self):
        p = self._pack("564922 60W Led BA11 50k 3pk")
        self.assertEqual(p.triple, ("Package Quantity", "3", "pk"))

    def test_bare_count_word_refused(self):
        self.assertIsNone(self._pack("Two way radio"))
        self.assertIsNone(self._pack("Three legged stool"))


class Phase6FalsePositiveTests(unittest.TestCase):
    """Product-number traps and contextual ambiguity locks."""

    def test_18v_never_gauge(self):
        by = {f.label: f for f in
              extract_all("Makita 18V 2\" Brad Nailer", "", "")}
        self.assertNotIn("Gauge", by)

    def test_18ga_never_voltage_or_amperage(self):
        by = {f.label: f for f in
              extract_all("Paslode CT200S24 18Ga ST Brad Nailer", "", "")}
        self.assertIn("Gauge", by)
        self.assertNotIn("Voltage Rating", by)
        self.assertNotIn("Amperage Rating", by)

    def test_2speed_not_size(self):
        by = {f.label: f for f in
              extract_all("DCGG581B Dewalt 20V Grease Gun 2-Speed", "", "")}
        self.assertIn("Speed", by)
        self.assertNotIn("Size", by)

    def test_30ft_range_not_size(self):
        by = {f.label: f for f in
              extract_all("Dewalt Laser Level - 3 Line 30ft Range", "", "")}
        self.assertIn("Range", by)
        self.assertNotIn("Size", by)

    def test_24oz_bottle_not_dimension(self):
        by = {f.label: f for f in
              extract_all("Milw 24oz Bottle - Insulated", "", "")}
        self.assertIn("Weight", by)
        self.assertNotIn("Size", by)

    def test_50k_is_cct_not_wattage(self):
        by = {f.label: f for f in
              extract_all('801274 10w LED 6" Retro 50k', "", "")}
        self.assertEqual(by["Wattage"].value, "10")
        self.assertEqual(by["Color Temperature"].value, "5000")

    def test_120v_15a_pair_preserved(self):
        by = {f.label: f for f in extract_all("Motor 120V 15A", "", "")}
        self.assertEqual(by["Voltage Rating"].triple,
                         ("Voltage Rating", "120", "V"))
        self.assertEqual(by["Amperage Rating"].triple,
                         ("Amperage Rating", "15", "A"))

    def test_single_wattage_fact_only(self):
        facts = [f for f in extract_all("Lamp 60W bulb 60W equivalent", "", "")
                 if f.label == "Wattage"]
        self.assertEqual(len(facts), 1)

    def test_mpn_style_tokens_stay_inert(self):
        labels = _labels(extract_all("48-22-8396R Milw insulated", "", ""))
        self.assertEqual(labels, [])


class Phase6ProvenanceTests(unittest.TestCase):
    REAL_DESCS = [
        '603150 2-1/2" Finish Nail 15GA - 4M',
        "JT1-549 JWBS18SFX 18\" Bandsaw - 1.75HP 1PH 115V",
        "DCGG581B Dewalt 20V Grease Gun 2-Speed",
        "DW089CG Dewalt Laser Level - 3 Line 30ft Range",
        "48-22-8396R Milw 24oz Bottle - Insulated",
        "DCM200B Dewalt 1/2in x 18in - Band File",
        "BC-12300 BigCal 12\"/300mm",
        "48-11-2422 Milw M12 CP2.0 Battery Two Pack",
    ]

    def test_new_facts_carry_full_provenance(self):
        for desc in self.REAL_DESCS:
            for f in extract_all(desc, "", ""):
                self.assertEqual(f.source, "Part_Desc", desc)
                self.assertTrue(f.evidence, "%s / %s" % (desc, f.label))
                self.assertEqual(f.status, NORMALIZED)

    def test_inferred_never_emitted_phase6(self):
        for desc in self.REAL_DESCS:
            for f in extract_all(desc, "", ""):
                self.assertNotEqual(f.status, INFERRED)

    def test_uom_values_are_canonical(self):
        checks = {"Gauge": "ga", "Horsepower": "hp", "Range": "ft",
                  "Weight": "oz"}
        for desc in self.REAL_DESCS:
            for f in extract_all(desc, "", ""):
                if f.label in checks:
                    self.assertEqual(f.uom, checks[f.label])

    def test_dataset_wide_no_inferred_and_known_labels(self):
        import csv as _csv
        allowed = {"Series", "Voltage Rating", "Amperage Rating", "Wattage",
                   "Sound Level", "Color Temperature", "Lumens",
                   "Number of Wash Cycles", "Mounting Type", "Size",
                   "Material", "Color", "Finish", "Abrasive Grit",
                   "Package Quantity", "Gauge", "Horsepower", "Speed",
                   "Range", "Weight"}
        with open(ROOT + r"\data\input\Unihack_ Sample Dataset - Input.csv",
                  encoding="utf-8-sig") as fh:
            rows = list(_csv.DictReader(fh))
        for r in rows:
            for f in extract_all(r["Part_Desc"], r["Mfg_Part_Num"], ""):
                self.assertIn(f.label, allowed, r["Mfg_Part_Num"])
                self.assertEqual(f.status, NORMALIZED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
