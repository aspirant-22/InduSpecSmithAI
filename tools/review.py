"""Phase 8 review CLI: confidence scoring + duplicate analysis sidecar.

Reads the input dataset and the generated delivery CSV, writes:
  output/review_report.csv   one row per input row, positional order
  output/review_report.md    methodology, thresholds, summary, dup groups

Report-only: never modifies the delivery CSV, never merges or reorders
rows. Deterministic - repeated runs produce byte-identical files.

Usage: python tools/review.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.review import (
    BAND_HIGH_MIN, BAND_MEDIUM_MIN, PENALTIES, REASON_HELP,
    build_review_rows, duplicate_desc_groups, duplicate_mpn_groups,
    summarize,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(ROOT, "data", "input",
                     "Unihack_ Sample Dataset - Input.csv")
OUTPUT = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")
CSV_OUT = os.path.join(ROOT, "output", "review_report.csv")
MD_OUT = os.path.join(ROOT, "output", "review_report.md")


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        headers = next(rdr)
        return headers, [dict(zip(headers, r)) for r in rdr]


def write_csv(records):
    cols = ["row", "mfg_part_num", "confidence", "band",
            "needs_human_review", "reasons", "attribute_slots",
            "mobile_desc_len", "duplicate_group_size"]
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow([r[c] for c in cols])


def render_md(summary):
    L = []
    L.append("# Review report (Phase 8)")
    L.append("")
    L.append("Sidecar reporting only. The 252-column delivery CSV is not "
             "modified; no rows are merged, removed, reordered or altered.")
    L.append("")
    L.append("## What the confidence score is (and is not)")
    L.append("- Evidence-completeness proxy per row, computed from signals "
             "already used by the evaluation harness (sections G and J).")
    L.append("- It is NOT a prediction-accuracy estimate: no row-level "
             "ground truth exists for the 1,000-row dataset, so none is "
             "assumed.")
    L.append("- All emitted attribute values remain NORMALIZED or blank; "
             "INFERRED stays 0. The score never invents content.")
    L.append("")
    L.append("## Scoring rules")
    L.append("- Every row starts at 100; each fired rule subtracts its "
             "weight once; the score floors at 0.")
    L.append("- Rules and weights (fixed evaluation order = reason order):")
    for code, weight, help_ in PENALTIES:
        L.append("  - %-24s -%d  %s" % (code, weight, help_))
    L.append("- Bands: HIGH >= %d, MEDIUM %d-%d, LOW < %d."
             % (BAND_HIGH_MIN, BAND_MEDIUM_MIN, BAND_HIGH_MIN - 1,
                BAND_MEDIUM_MIN))
    L.append("- needs_human_review = score < %d (the LOW band)."
             % BAND_MEDIUM_MIN)
    L.append("- Threshold rationale: a LOW row fails at least the "
             "attribute-evidence and description-length checks together "
             "or carries a hard data-quality flag (duplicate MPN, typo, "
             "sparse description), i.e. a human should confirm the record "
             "before commerce use.")
    L.append("")
    L.append("## Summary")
    s = summary
    L.append("- rows scored: %(rows)d" % s)
    L.append("- bands: HIGH %(HIGH)d | MEDIUM %(MEDIUM)d | LOW %(LOW)d"
             % s["bands"])
    L.append("- needs human review: %d of %d (%.1f%%)"
             % (s["needs_human_review"], s["rows"],
                100.0 * s["needs_human_review"] / max(1, s["rows"])))
    L.append("- reason frequency (rule fires across rows):")
    for code, n in s["reason_frequency"]:
        L.append("  - %-22s %4d  (%s)" % (code, n, REASON_HELP[code]))
    L.append("")
    L.append("## Duplicate MPN groups (report-only)")
    if not s["duplicate_mpn_groups"]:
        L.append("- none")
    for mpn, rows in s["duplicate_mpn_groups"].items():
        L.append("- `%s` -> data rows %s (%d copies); both/all rows remain "
                 "in place in input and output" % (mpn, rows, len(rows)))
    L.append("")
    L.append("## Duplicate description groups (report-only)")
    if not s["duplicate_desc_groups"]:
        L.append("- none")
    for desc, rows in s["duplicate_desc_groups"].items():
        L.append("- rows %s share description: %r" % (rows, desc[:80]))
    L.append("")
    L.append("## Positional integrity")
    L.append("- review rows are aligned 1:1 with input data-row order "
             "(row column = 1-based data row number); verified against "
             "Mfg_Part_Num per position.")
    return [x + "\n" for x in L]


def main():
    _, in_rows = load_csv(INPUT)
    _, out_rows = load_csv(OUTPUT)
    if len(in_rows) != len(out_rows):
        print("ABORT: row count mismatch %d vs %d"
              % (len(in_rows), len(out_rows)))
        return 1
    for pos, (i, o) in enumerate(zip(in_rows, out_rows), start=1):
        if i.get("Mfg_Part_Num") != o.get("Mfg_Part_Num"):
            print("ABORT: positional MPN mismatch at data row %d" % pos)
            return 1

    records = build_review_rows(in_rows, out_rows)
    mpn_groups = duplicate_mpn_groups(in_rows)
    desc_groups = duplicate_desc_groups(in_rows)
    summary = summarize(records, mpn_groups, desc_groups)

    write_csv(records)
    with open(MD_OUT, "w", encoding="utf-8", newline="") as f:
        f.writelines(render_md(summary))

    print("wrote %s (%d rows)" % (CSV_OUT, len(records)))
    print("wrote %s" % MD_OUT)
    print("needs human review: %d / %d" % (summary["needs_human_review"],
                                           summary["rows"]))
    print("duplicate MPN groups: %d %s"
          % (len(mpn_groups),
             {k: v for k, v in sorted(mpn_groups.items())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
