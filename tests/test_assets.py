"""Phase 3 tests: deterministic asset naming (no existence claims).

Run:  python -m unittest tests.test_assets -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import process_row, _asset_base, _asset_fields


class AssetBaseTests(unittest.TestCase):
    def test_display_form_case_preserved(self):
        self.assertEqual(_asset_base("Whirlpool®", "WDTS7024RZ"),
                         "Whirlpool_WDTS7024RZ")
        self.assertEqual(_asset_base("FRIGIDAIRE®", "PDSH4816AF"),
                         "FRIGIDAIRE_PDSH4816AF")

    def test_spaces_and_symbols_removed(self):
        self.assertEqual(_asset_base("Feit Electric", "BP40"),
                         "FeitElectric_BP40")
        self.assertEqual(_asset_base("Black & Decker", "BD123"),
                         "BlackDecker_BD123")

    def test_mpn_punctuation_handling(self):
        self.assertEqual(_asset_base("Satco", "10-4 SO"), "Satco_10-4SO")
        self.assertEqual(_asset_base("Southwire", "5B-332-080"),
                         "Southwire_5B-332-080")
        self.assertEqual(_asset_base("Milwaukee", '14"x1/8"'), "Milwaukee_14x18")

    def test_no_brand_no_filename(self):
        self.assertEqual(_asset_base("", "XYZ123"), "")
        self.assertEqual(_asset_fields("", "XYZ123"), {})

    def test_no_mpn_no_filename(self):
        self.assertEqual(_asset_base("Whirlpool®", ""), "")
        self.assertEqual(_asset_fields("Whirlpool®", ""), {})

    def test_deterministic(self):
        a = _asset_fields("Whirlpool®", "WDTS7024RZ")
        b = _asset_fields("Whirlpool®", "WDTS7024RZ")
        self.assertEqual(a, b)


class AssetFieldTests(unittest.TestCase):
    FIELDS = _asset_fields("Whirlpool®", "WDTS7024RZ")

    def test_all_five_image_variants(self):
        self.assertEqual(self.FIELDS["Product Image"],
                         "Whirlpool_WDTS7024RZ.jpg")
        for i in range(1, 5):
            self.assertEqual(self.FIELDS["Alternate Image %d" % i],
                             "Whirlpool_WDTS7024RZ_%d.jpg" % i)

    def test_specification_sheet(self):
        self.assertEqual(self.FIELDS["Specification Sheet"],
                         "Whirlpool_WDTS7024RZ_Specification_Sheet.pdf")


class NoExistenceClaimTests(unittest.TestCase):
    ROWS = [
        {"Mfg_Part_Num": "WDTS7024RZ",
         "Part_Desc": "WDTS7024RZ Dishwasher SS",
         "E1_Brand": "-- Unbranded --",
         "Unilog_Brand": "-- No Unilog Brand --",
         "DIB_Brand": "-- No DIB Brand --",
         "Part_Manuf": "Appliance Dealers Cooperative (APPDE)"},
        {"Mfg_Part_Num": "49-94-1940",
         "Part_Desc": "49-94-1940 Milw 14\"x1/8\"x1\" Masonry Cut Off Disc"},
        {"Mfg_Part_Num": "AGB15512BS",
         "Part_Desc": "AGB15512BS 1x6-12' Brownstone Grooved - Harvest Azek PVC Decking"},
    ]
    EXISTENCE_COLS = ["Actual Image (Yes/No)", "MFR URL", "Ref URL 1",
                      "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5",
                      "SDS", "SDS_1", "Catalog",
                      "Instruction/Installation Manual", "Service Manual",
                      "Owners/User Manual", "Line Drawing", "MTR", "RoHS",
                      "Full Engineering Drawing", "Product Label/Insert",
                      "Video Link", "Video Link 1"]

    def test_actual_image_flag_never_claimed(self):
        for row in self.ROWS:
            out = process_row(row)
            for col in self.EXISTENCE_COLS:
                self.assertEqual(out.get(col, ""),
                                 "", "%s claimed in %r" %
                                 (col, row["Mfg_Part_Num"]))

    def test_placeholder_brands_do_not_invent_asset_names(self):
        row = {"Mfg_Part_Num": "XYZ123", "Part_Desc": "Widget Steel 4 in",
               "E1_Brand": "-- Unbranded --",
               "Unilog_Brand": "-- No Unilog Brand --",
               "DIB_Brand": "-- No DIB Brand --",
               "Part_Manuf": "-"}
        out = process_row(row)
        self.assertEqual(out.get("Product Image", ""), "")
        self.assertEqual(out.get("Specification Sheet", ""), "")
        for i in range(1, 5):
            self.assertEqual(out.get("Alternate Image %d" % i, ""), "")

    def test_branded_rows_get_expected_names_only(self):
        out = process_row(self.ROWS[0])
        self.assertEqual(out["Product Image"], "Whirlpool_WDTS7024RZ.jpg")
        self.assertEqual(out["Specification Sheet"],
                         "Whirlpool_WDTS7024RZ_Specification_Sheet.pdf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
