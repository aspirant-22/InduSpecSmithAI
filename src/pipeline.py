"""Full enrichment pipeline: raw rows -> 252-column Delivery Format.

Usage:
    python -m src.pipeline [--input path] [--output out.csv]

Reads the exact expected-output header order from the expected file in
data/input so the emitted CSV is column-for-column compatible.
"""
import csv
import os
import re
import sys

from .common import clean
from .classify import classify
from .branding import resolve_brand, resolve_manufacturer
from .extract import extract_all
from .descriptions import (
    mobile_desc, invoice_desc, short_desc, long_desc1, retail_desc,
    marketing_description, item_features, additional_information,
)
from . import references

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "input")
OUT_DIR = os.path.join(ROOT, "output")
EXPECTED_FILE = os.path.join(DATA_DIR,
                             "Unihack_ Expected Output - Delivery Format.csv")


def _asset_name(brand, mpn):
    b = re.sub(r"[^A-Za-z0-9]", "", brand or "").upper()
    m = re.sub(r"[^A-Za-z0-9_-]", "", clean(mpn))
    return "%s_%s.jpg" % (b, m) if b else "%s.jpg" % m


def process_row(row):
    """Enrich a single input row -> dict keyed by output column name."""
    desc = clean(row.get("Part_Desc", ""))
    mpn = clean(row.get("Mfg_Part_Num", ""))
    brand = resolve_brand(row)
    manufacturer = resolve_manufacturer(row, brand)
    tax = classify(desc)
    attrs = extract_all(desc, mpn, brand)

    product = tax["product"]
    series = next((v for l, v, _ in attrs if l == "Series"), "")
    mounting = next((v for l, v, _ in attrs if l == "Mounting Type"), "")

    # attribute triple columns
    attr_cols = {}
    for i, (lab, val, uom) in enumerate(attrs[:50], start=1):
        attr_cols["ATTRIBUTE_LABEL %d" % i] = lab
        attr_cols["ATTRIBUTE_VALUE %d" % i] = val
        attr_cols["ATTRIBUTE_UOM %d" % i] = uom

    feats = item_features(attrs)
    feat_cols = {"ITEM_FEATURES_%d" % (i + 1): f for i, f in enumerate(feats)}

    addl = additional_information(desc, attrs)
    addl_text = ", ".join(addl) if addl else ""

    # input columns are passed through verbatim - placeholders included
    out = {
        "PART_NUMBER": "",
        "Mfg_Part_Num": mpn,
        "Part_Desc": desc,
        "E1_Brand": clean(row.get("E1_Brand", "")),
        "Unilog_Brand": clean(row.get("Unilog_Brand", "")),
        "DIB_Brand": clean(row.get("DIB_Brand", "")),
        "Part_Manuf": clean(row.get("Part_Manuf", "")),
        "MANUFACTURER_NAME": manufacturer,
        "BRAND_NAME": brand,
        "TRADE_NAME": "",
        "MANUFACTURER_PART_NUMBER": mpn,
        "ALTERNATE_PART_NUMBER": "",
        "Dept": tax["dept"],
        "Class": tax["class"],
        "Fine": tax["fine"],
        "Classpath": tax["classpath"],
        "MOBILE_DESC": mobile_desc(manufacturer, brand, product, series, mpn,
                                   mounting, desc),
        "INVOICE_DESC": invoice_desc(desc, attrs, product, mpn),
        "SHORT_DESC": short_desc(desc, attrs, brand, series, mpn, product,
                                 mounting),
        "LONG_DESC1": long_desc1(desc, attrs, brand, product, series, mpn),
        "RETAIL_DESC": retail_desc(desc, attrs, brand, product, mpn),
        "MARKETING_DESCRIPTION": marketing_description(desc, attrs, brand,
                                                       product),
        "Product Name": product,
        "Standard/Approvals": "",
        "Warranty": "",
        "Warranty Information": "",
        "Standard Packaging Information": "",
        "Selling Qty": "",
        "Selling UOM": "",
        "Product Image": _asset_name(brand, mpn),
        "Actual Image (Yes/No)": "",
        "Country Of Origin": "",
        "Discontinued": "",
        "UNSPSC": "",
        "UPC": "",
        "List Price": "",
    }
    out.update(attr_cols)
    out.update(feat_cols)
    return out


def load_input(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    return rows


def main():
    input_path = os.path.join(DATA_DIR, "Unihack_ Sample Dataset - Input.csv")
    if "--input" in sys.argv:
        input_path = sys.argv[sys.argv.index("--input") + 1]

    # exact header order from the expected-output template
    with open(EXPECTED_FILE, encoding="utf-8-sig", errors="replace") as f:
        headers = next(csv.reader(f))
    if len(headers) != 252:
        raise SystemExit("expected 252 columns, got %d" % len(headers))

    rows = load_input(input_path)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "Unihack_Delivery_Output.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(process_row(row))

    report = {
        "input_file": input_path,
        "rows": len(rows),
        "columns_out": len(headers),
        "output_file": out_path,
        "reference": references.apply(),
    }
    with open(os.path.join(OUT_DIR, "run_report.json"), "w") as f:
        import json
        json.dump(report, f, indent=2)
    print("wrote %d rows -> %s" % (len(rows), out_path))
    print("reference status:", report["reference"])


if __name__ == "__main__":
    main()