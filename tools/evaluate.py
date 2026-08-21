"""Validation & evaluation report for the pipeline output.

Checks:
  - header parity with the expected-output template
  - required field presence
  - spec length limits (INVOICE_DESC <= 40, MOBILE_DESC <= 85)
  - placeholder leakage in generated fields
  - attribute triples integrity (label/value pairing)
  - optional ground-truth field-by-field scoring when the reference file exists

Writes output/evaluation_report.md
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import references

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED = os.path.join(ROOT, "data", "input",
                        "Unihack_ Expected Output - Delivery Format.csv")
OUTPUT = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")
REPORT = os.path.join(ROOT, "output", "evaluation_report.md")

PLACEHOLDER = re.compile(r"^--.*--$|^[-x]{1,3}$", re.I)

REQUIRED = ["Mfg_Part_Num", "Part_Desc", "Dept", "Class", "Fine", "Classpath",
            "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC", "LONG_DESC1",
            "Product Name", "MANUFACTURER_NAME", "BRAND_NAME"]


def main():
    if not os.path.exists(OUTPUT):
        raise SystemExit("run the pipeline first: python -m src.pipeline")

    with open(EXPECTED, encoding="utf-8-sig") as f:
        exp_headers = next(csv.reader(f))
    with open(OUTPUT, encoding="utf-8") as f:
        out_headers = next(csv.reader(f))
        rows = list(csv.DictReader(f, fieldnames=out_headers))

    report = []
    add = report.append
    add("# Evaluation report")
    add("")
    add("Rows: %d" % len(rows))
    add("Header parity: %s (%d cols vs expected %d)" %
        (exp_headers == out_headers, len(out_headers), len(exp_headers)))
    add("")

    # 1. required field presence
    missing = {k: 0 for k in REQUIRED}
    for r in rows:
        for k in REQUIRED:
            if not r.get(k):
                missing[k] += 1
    add("## Required-field emptiness")
    for k, n in missing.items():
        add("- %-22s %d" % (k, n))
    add("")

    # 2. length limits
    inv_over = [r for r in rows if len(r.get("INVOICE_DESC", "")) > 40]
    mob_over = [r for r in rows if len(r.get("MOBILE_DESC", "")) > 85]
    add("## Length limits")
    add("- INVOICE_DESC > 40 chars: %d" % len(inv_over))
    add("- MOBILE_DESC   > 85 chars: %d" % len(mob_over))
    add("")

    # 3. placeholder leakage in generated fields
    leak = [k for k in REQUIRED
            if any(PLACEHOLDER.search(r.get(k, "")) for r in rows)]
    add("## Placeholder leakage in generated fields")
    add(", ".join(leak) if leak else "none")
    add("")

    # 4. attribute triple integrity
    bad_triples = 0
    attr_count = set()
    for r in rows:
        for i in range(1, 51):
            lab = r.get("ATTRIBUTE_LABEL %d" % i, "")
            val = r.get("ATTRIBUTE_VALUE %d" % i, "")
            if lab and not val:
                bad_triples += 1
            if lab:
                attr_count.add(lab)
    add("## Attribute triples")
    add("- distinct labels used: %d" % len(attr_count))
    add("- labels without values: %d" % bad_triples)
    add("")

    # 5. ground truth scoring (optional)
    gt = references.load_ground_truth()
    if gt:
        add("## Ground-truth scoring (%d expected rows)" % len(gt))
        hits = 0
        tot = 0
        for g in gt:
            mpn = g.get("Mfg_Part_Num", "")
            comp = next((r for r in rows if r["Mfg_Part_Num"] == mpn), None)
            if not comp:
                continue
            for col in ["Class", "Fine", "BRAND_NAME", "MANUFACTURER_NAME",
                        "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC"]:
                if g.get(col) and g[col] != "-":
                    tot += 1
                    if comp.get(col) == g[col]:
                        hits += 1
        add("- field-level accuracy: %d/%d (%.1f%%)" %
            (hits, tot, 100.0 * hits / max(tot, 1)))
    else:
        add("## Ground-truth scoring")
        add("reference ground-truth file not present in data/reference - skipped")
    add("")

    # 6. taxonomy distribution
    from collections import Counter
    dept = Counter(r["Dept"] for r in rows)
    fine = Counter(r["Fine"] for r in rows)
    add("## Taxonomy distribution")
    add("- depts: %s" % dict(dept))
    add("- top fines: %s" % dict(fine.most_common(12)))
    add("")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("wrote %s" % REPORT)


if __name__ == "__main__":
    main()