"""Comprehensive Phase-5 evaluation for the UniHack delivery output.

Sections (report order):
  A. Header parity            B. Row counts
  C. Input field preservation (positional, placeholder-aware)
  D/E. Ground-truth exact-match & populated-field accuracy (2 GT rows)
  F. Output coverage by category
  G. Character-limit compliance (MOBILE 60-80 strict, INVOICE <=40 CAPS)
  H. Unsupported / inferred value detection (INFERRED > 0 => FAIL)
  I. Blank-field analysis     J. Data-quality flags (flags only)
  K. Ground-truth sample-size disclaimer

Every function returns a plain dict so tests can call them directly.
"""
import csv
import json
import os
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.descriptions import FORBIDDEN_FILLER

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED = os.path.join(ROOT, "data", "input",
                        "Unihack_ Expected Output - Delivery Format.csv")
INPUT = os.path.join(ROOT, "data", "input", "Unihack_ Sample Dataset - Input.csv")
OUTPUT = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")
REPORT = os.path.join(ROOT, "output", "evaluation_report.md")
RUN_REPORT = os.path.join(ROOT, "output", "run_report.json")

SIX_COLUMNS = ["Mfg_Part_Num", "Part_Desc", "E1_Brand", "Unilog_Brand",
               "DIB_Brand", "Part_Manuf"]

DISCLAIMER = ("Only 2 rows are available for direct output-level "
              "ground-truth evaluation. This is NOT statistically "
              "representative of the 1,000-row evaluation dataset.")

MOBILE_MIN, MOBILE_MAX, INVOICE_MAX = 60, 80, 40

URL_COLUMNS = {"MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4",
               "Ref URL 5", "Video Link", "Video Link 1"}

CATEGORY_BUCKETS = [
    ("identifiers/input", ["PART_NUMBER", "SKU - MY_PART_NUMBER",
                           "Mfg_Part_Num", "Part_Desc", "E1_Brand",
                           "Unilog_Brand", "DIB_Brand", "Part_Manuf"]),
    ("manufacturer/brand", ["MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME",
                            "MANUFACTURER_PART_NUMBER",
                            "ALTERNATE_PART_NUMBER"]),
    ("taxonomy", ["Dept", "Class", "Fine", "Classpath", "Product Name"]),
    ("descriptions", ["MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC",
                      "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION"]),
    ("attributes", ["ATTRIBUTE_%s %d" % (k, i) for i in range(1, 51)
                    for k in ("LABEL", "VALUE", "UOM")]),
    ("features/marketing", ["ITEM_FEATURES_%d" % i for i in range(1, 21)] +
     ["With", "Standard/Approvals", "Application", "Includes", "Prop 65"]),
    ("assets", ["Product Image", "Alternate Image 1", "Alternate Image 2",
                "Alternate Image 3", "Alternate Image 4",
                "Specification Sheet", "Actual Image (Yes/No)"]),
    ("urls/documents", sorted(URL_COLUMNS) +
     ["SDS", "SDS_1", "Catalog", "Warranty Information",
      "Instruction/Installation Manual", "Service Manual",
      "Owners/User Manual", "Line Drawing", "MTR", "RoHS",
      "Full Engineering Drawing", "Product Label/Insert"]),
    ("commercial/logistics", ["Warranty", "List Price", "Selling Qty",
                              "Selling UOM", "Standard Packaging Information",
                              "LENGTH", "LENGTH_UOM", "WIDTH", "WIDTH_UOM",
                              "HEIGHT", "HEIGHT_UOM", "WEIGHT", "WEIGHT_UOM",
                              "VOLUME", "VOLUME_UOM", "UPC", "EAN", "GTIN",
                              "UNSPSC", "Country Of Origin", "Discontinued"]),
]

# Fields whose blankness is intentional under the no-hallucination rule
# (no source data exists for them in the provided dataset).
INTENTIONAL_BLANK = set(
    ["PART_NUMBER", "SKU - MY_PART_NUMBER", "TRADE_NAME",
     "ALTERNATE_PART_NUMBER", "Warranty", "Warranty Information",
     "Standard Packaging Information", "Selling Qty", "Selling UOM",
     "List Price", "UPC", "EAN", "GTIN", "UNSPSC", "Country Of Origin",
     "Discontinued", "LENGTH", "LENGTH_UOM", "WIDTH", "WIDTH_UOM",
     "HEIGHT", "HEIGHT_UOM", "WEIGHT", "WEIGHT_UOM", "VOLUME", "VOLUME_UOM"]
    + sorted(URL_COLUMNS))

TYPO_DICT = {
    "mocrowave": "microwave", "outet": "outlet", "brakcet": "bracket",
    "indudtrial": "industrial", "trox": "trex", "rachet": "ratchet",
    "frming": "framing",
}


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        headers = next(rdr)
        return headers, [dict(zip(headers, r)) for r in rdr]


# ---------------------------------------------------------------- A
def check_header_parity(exp_hdr, out_hdr):
    missing = [h for h in exp_hdr if h not in out_hdr]
    extra = [h for h in out_hdr if h not in exp_hdr]
    order_mismatch = not missing and not extra and exp_hdr != out_hdr
    return {"expected_count": len(exp_hdr), "actual_count": len(out_hdr),
            "missing": missing, "extra": extra,
            "order_mismatch": order_mismatch,
            "pass": exp_hdr == out_hdr}


# ---------------------------------------------------------------- B
def check_row_counts(n_in, n_out):
    return {"input_rows": n_in, "output_rows": n_out,
            "missing_rows": max(0, n_in - n_out),
            "extra_rows": max(0, n_out - n_in),
            "pass": n_in == n_out}


# ---------------------------------------------------------------- C
def _is_placeholder(v):
    s = (v or "").strip()
    return s.startswith("--") or s == "-"


def check_input_preservation(in_rows, out_rows):
    n = min(len(in_rows), len(out_rows))
    cells = mismatches = 0
    mismatch_examples = []
    placeholder_totals = {}
    for c in SIX_COLUMNS:
        ph_in = ph_kept = 0
        for i in range(n):
            a, b = in_rows[i].get(c, ""), out_rows[i].get(c, "")
            cells += 1
            if a.strip() == b.strip():
                if _is_placeholder(a):
                    ph_in += 1
                    if a.strip() == b.strip():
                        ph_kept += 1
            else:
                mismatches += 1
                if len(mismatch_examples) < 5:
                    mismatch_examples.append({"row": i, "column": c,
                                              "input": a, "output": b})
        placeholder_totals[c] = {"placeholders_in_input": ph_in,
                                 "preserved_verbatim": ph_kept}
    return {"compared_cells": cells, "exact_matches": cells - mismatches,
            "mismatches": mismatches, "mismatch_examples": mismatch_examples,
            "placeholder_preservation": placeholder_totals,
            "positional": True, "pass": mismatches == 0}


# ---------------------------------------------------------------- D/E
def _match_gt_row(gt_row, out_rows):
    """Unique match on (Mfg_Part_Num, Part_Desc); never guess among dups."""
    by_mpn = [r for r in out_rows
              if r.get("Mfg_Part_Num") == gt_row.get("Mfg_Part_Num")]
    if not by_mpn:
        return None, "UNMATCHED"
    cands = [r for r in by_mpn
             if r.get("Part_Desc") == gt_row.get("Part_Desc")]
    if len(cands) == 1:
        return cands[0], "MATCHED"
    # MPN exists but desc cannot disambiguate (0 or >1 candidates)
    return None, "AMBIGUOUS"


def ground_truth_scores(gt_hdr, gt_rows, out_rows):
    per_field = {}
    totals = {"expected_populated": 0, "predicted_populated": 0,
              "exact_matches": 0, "incorrect_values": 0,
              "missing_predictions": 0}
    row_results = []
    for g in gt_rows:
        comp, status = _match_gt_row(g, out_rows)
        row_results.append({"mpn": g.get("Mfg_Part_Num"), "status": status})
        if status != "MATCHED":
            continue
        for col in gt_hdr:
            gv, ov = g.get(col, ""), comp.get(col, "")
            if gv == "":
                continue
            f = per_field.setdefault(col, {"expected_populated": 0,
                                           "exact_matches": 0,
                                           "mismatches": 0,
                                           "missing_predictions": 0,
                                           "examples": []})
            f["expected_populated"] += 1
            totals["expected_populated"] += 1
            if ov != "":
                totals["predicted_populated"] += 1
            if gv == ov:
                f["exact_matches"] += 1
                totals["exact_matches"] += 1
            elif ov == "":
                f["missing_predictions"] += 1
                totals["missing_predictions"] += 1
            else:
                f["mismatches"] += 1
                totals["incorrect_values"] += 1
                if len(f["examples"]) < 3:
                    f["examples"].append({"expected": gv, "got": ov})
    evaluated_fields = len(per_field)
    unevaluable_fields = [c for c in gt_hdr
                          if c not in per_field
                          and all(r.get(c, "") == "" for r in gt_rows)]
    acc = 100.0 * totals["exact_matches"] / max(1, totals["expected_populated"])
    pop_acc = 100.0 * totals["exact_matches"] / max(1, totals["predicted_populated"])
    return {"row_matches": row_results,
            "fields_with_ground_truth": evaluated_fields,
            "fields_without_ground_truth": len(unevaluable_fields),
            "unevaluable_field_names": unevaluable_fields,
            "per_field": per_field, "totals": totals,
            "field_accuracy_pct": round(acc, 1),
            "populated_accuracy_pct": round(pop_acc, 1),
            "sample_size": len(gt_rows)}


# ---------------------------------------------------------------- F
def coverage_by_category(out_rows, out_hdr):
    bucketed = {name: cols for name, cols in CATEGORY_BUCKETS}
    bucketed_cols = {c for _, cols in CATEGORY_BUCKETS for c in cols}
    other = [h for h in out_hdr if h not in bucketed_cols]
    results = {}
    for name, cols in CATEGORY_BUCKETS + [("other", other)]:
        cols = [c for c in cols if c in out_hdr]
        pop = sum(1 for r in out_rows for c in cols if r.get(c, "") != "")
        total = len(cols) * len(out_rows)
        results[name] = {"populated": pop, "blank": total - pop,
                         "total": total,
                         "pct_populated": round(100.0 * pop / max(1, total), 1)}
    return results


# ---------------------------------------------------------------- G
def char_limit_compliance(out_rows):
    mob_ok = mob_short = mob_over = 0
    mob_examples = []
    inv_over = inv_lower = 0
    inv_examples = []
    for r in out_rows:
        m = r.get("MOBILE_DESC", "")
        if MOBILE_MIN <= len(m) <= MOBILE_MAX:
            mob_ok += 1
        elif len(m) > MOBILE_MAX:
            mob_over += 1
            if len(mob_examples) < 5:
                mob_examples.append({"mpn": r.get("Mfg_Part_Num"),
                                     "len": len(m), "value": m})
        else:
            mob_short += 1  # NON-COMPLIANT: below strict 60-char floor
        v = r.get("INVOICE_DESC", "")
        if len(v) > INVOICE_MAX:
            inv_over += 1
            if len(inv_examples) < 5:
                inv_examples.append({"mpn": r.get("Mfg_Part_Num"),
                                     "len": len(v), "value": v})
        elif v and v != v.upper():
            inv_lower += 1
    return {"mobile": {"compliant_60_80": mob_ok,
                       "non_compliant_below_60_evidence_short": mob_short,
                       "violations_above_80": mob_over,
                       "violation_examples": mob_examples},
            "invoice": {"over_40": inv_over, "not_uppercase": inv_lower,
                        "violation_examples": inv_examples},
            "hard_violations": mob_over + inv_over + inv_lower,
            "pass": (mob_over + inv_over + inv_lower) == 0}


# ---------------------------------------------------------------- H
GENERATED_TEXT_COLS = ["MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC",
                       "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION"]


def unsupported_value_scan(out_rows, prov_by_status):
    inferred = prov_by_status.get("INFERRED", 0)
    filler_hits = []
    url_hits = []
    existence_hits = []
    warranty_hits = []
    banned = tuple(f.lower() for f in FORBIDDEN_FILLER)
    for r in out_rows:
        for c in GENERATED_TEXT_COLS:
            low = (r.get(c, "") or "").lower()
            if any(p in low for p in banned):
                filler_hits.append({"mpn": r.get("Mfg_Part_Num"), "col": c})
        for c in URL_COLUMNS:
            if r.get(c, ""):
                url_hits.append({"mpn": r.get("Mfg_Part_Num"), "col": c,
                                 "value": r[c]})
        if r.get("Actual Image (Yes/No)", ""):
            existence_hits.append({"mpn": r.get("Mfg_Part_Num"),
                                   "value": r["Actual Image (Yes/No)"]})
        w = r.get("Warranty", "")
        if w:
            warranty_hits.append({"mpn": r.get("Mfg_Part_Num"), "value": w})
    return {"inferred_emitted": inferred,
            "filler_phrases": filler_hits[:10],
            "fabricated_urls": url_hits[:10],
            "asset_existence_claims": existence_hits[:10],
            "blanket_warranty_claims": warranty_hits[:10],
            "pass": inferred == 0 and not (filler_hits or url_hits
                                           or existence_hits
                                           or warranty_hits)}


# ---------------------------------------------------------------- I
def blank_field_analysis(out_rows, out_hdr):
    total_cells = len(out_rows) * len(out_hdr)
    blank_cells = sum(1 for r in out_rows for h in out_hdr if r.get(h, "") == "")
    fully_blank = [h for h in out_hdr
                   if all(r.get(h, "") == "" for r in out_rows)]
    intentional_blanks = sum(1 for r in out_rows for h in INTENTIONAL_BLANK
                             if h in out_hdr and r.get(h, "") == "")
    cov = coverage_by_category(out_rows, out_hdr)
    return {"total_cells": total_cells, "blank_cells": blank_cells,
            "pct_blank": round(100.0 * blank_cells / max(1, total_cells), 1),
            "fully_blank_columns": len(fully_blank),
            "intentional_no_source_blanks": intentional_blanks,
            "by_category": {k: v["blank"] for k, v in cov.items()}}


# ---------------------------------------------------------------- J
def data_quality_flags(in_rows, out_rows):
    flags = {}
    mpn_counts = Counter(r.get("Mfg_Part_Num", "") for r in in_rows)
    dups = {k: v for k, v in mpn_counts.items() if v > 1}
    flags["duplicate_mpns"] = {"count": len(dups), "items": dups}

    mismatch = near = 0
    examples = []
    for r in in_rows:
        desc = (r.get("Part_Desc", "") or "").strip()
        mpn = (r.get("Mfg_Part_Num", "") or "").strip()
        toks = desc.split()
        if not toks:
            continue
        tok = toks[0]
        if not (re.search(r"\d", tok) and len(tok) >= 5
                and re.fullmatch(r"[A-Za-z0-9\-/.]+", tok)):
            continue
        if tok.upper() != mpn.upper():
            ratio = SequenceMatcher(None, tok.upper(), mpn.upper()).ratio()
            if ratio >= 0.8:
                near += 1
                if len(examples) < 5:
                    examples.append({"mpn": mpn, "desc_token": tok,
                                     "similarity": round(ratio, 2)})
            else:
                mismatch += 1
    flags["mpn_desc_mismatch"] = {"exact_leading_token_mismatch": mismatch,
                                  "near_miss_similarity": near,
                                  "near_miss_examples": examples}

    typo_hits = Counter()
    for r in in_rows:
        low = (r.get("Part_Desc", "") or "").lower()
        for t in TYPO_DICT:
            if re.search(r"\b" + re.escape(t) + r"\b", low):
                typo_hits[t] += 1
    flags["suspected_typos"] = {"distinct": len(typo_hits),
                                "rows_affected": sum(typo_hits.values()),
                                "detail": dict(typo_hits)}

    flags["placeholder_brands"] = {
        "E1_Brand": sum(1 for r in in_rows if _is_placeholder(r.get("E1_Brand", ""))),
        "Unilog_Brand": sum(1 for r in in_rows if _is_placeholder(r.get("Unilog_Brand", ""))),
        "DIB_Brand": sum(1 for r in in_rows if _is_placeholder(r.get("DIB_Brand", ""))),
    }
    flags["missing_manufacturer"] = sum(
        1 for r in in_rows if r.get("Part_Manuf", "").strip() in ("-", ""))
    flags["missing_resolved_brand"] = sum(
        1 for r in out_rows if r.get("BRAND_NAME", "") == "")
    flags["sparse_descriptions_lt20"] = sum(
        1 for r in in_rows if len((r.get("Part_Desc", "") or "").strip()) < 20)
    desc_counts = Counter(
        (r.get("Part_Desc", "") or "").strip().lower() for r in in_rows)
    dup_desc = {k: v for k, v in desc_counts.items() if k and v > 1}
    flags["duplicate_descriptions"] = {"groups": len(dup_desc),
                                       "extra_copies": sum(v - 1 for v in dup_desc.values())}
    return flags


# ---------------------------------------------------------------- render
def render_report(res):
    add = lambda lines, s="": lines.append(s)
    L = []
    add(L, "# Evaluation report (Phase 5)")
    add(L)
    add(L, DISCLAIMER)
    add(L)
    a = res["header"]
    add(L, "## A. Header parity - %s" % ("PASS" if a["pass"] else "FAIL"))
    add(L, "- expected %d / actual %d / missing %d / extra %d / order mismatch %s"
        % (a["expected_count"], a["actual_count"], len(a["missing"]),
           len(a["extra"]), a["order_mismatch"]))
    if a["missing"] or a["extra"]:
        add(L, "- missing: %s extra: %s" % (a["missing"], a["extra"]))
    add(L)
    b = res["rows"]
    add(L, "## B. Row count - %s" % ("PASS" if b["pass"] else "FAIL"))
    add(L, "- input %(input_rows)d / output %(output_rows)d / "
           "missing %(missing_rows)d / extra %(extra_rows)d" % b)
    add(L)
    c = res["preservation"]
    add(L, "## C. Input field preservation (positional) - %s"
        % ("PASS" if c["pass"] else "FAIL"))
    add(L, "- %d/%d cells preserved verbatim (%d mismatches)"
        % (c["exact_matches"], c["compared_cells"], c["mismatches"]))
    for col, d in c["placeholder_preservation"].items():
        add(L, "- %-14s placeholders %5d -> preserved %5d"
            % (col, d["placeholders_in_input"], d["preserved_verbatim"]))
    for ex in c["mismatch_examples"]:
        add(L, "- MISMATCH row %(row)s %(column)s: %(input)r -> %(output)r" % ex)
    add(L)
    d = res["gt"]
    add(L, "## D/E. Ground-truth accuracy (%d GT rows)" % d["sample_size"])
    add(L, "- row matching: %s"
        % ", ".join("%(mpn)s=%(status)s" % r for r in d["row_matches"]))
    add(L, "- fields with ground truth: %d / without: %d (unevaluable)"
        % (d["fields_with_ground_truth"], d["fields_without_ground_truth"]))
    t = d["totals"]
    add(L, "- expected populated cells: %(expected_populated)d | "
           "predicted populated: %(predicted_populated)d | exact: "
           "%(exact_matches)d | incorrect: %(incorrect_values)d | "
           "missing predictions: %(missing_predictions)d" % t)
    add(L, "- field-level exact-match accuracy: %.1f%% | populated-field "
           "accuracy: %.1f%%" % (d["field_accuracy_pct"],
                                 d["populated_accuracy_pct"]))
    add(L)
    add(L, "### Per-field detail (GT-populated fields)")
    for col in sorted(d["per_field"],
                      key=lambda k: -d["per_field"][k]["expected_populated"]):
        f = d["per_field"][col]
        pct = 100.0 * f["exact_matches"] / max(1, f["expected_populated"])
        add(L, "- %-28s %2d/%2d exact (%5.1f%%) missing:%d%s"
            % (col, f["exact_matches"], f["expected_populated"], pct,
               f["missing_predictions"],
               "" if not f["examples"] else " e.g. %s" % f["examples"][:1]))
    add(L)
    add(L, "## F. Output coverage by category")
    for name, v in res["coverage"].items():
        add(L, "- %-22s populated %7d / blank %7d (%5.1f%%)"
            % (name, v["populated"], v["blank"], v["pct_populated"]))
    add(L)
    g = res["limits"]
    add(L, "## G. Character-limit compliance - %s"
        % ("PASS" if g["pass"] else "FAIL"))
    add(L, "- MOBILE_DESC 60-80: %d compliant | %d NON-COMPLIANT (<60, "
           "evidence-short, left honest) | %d violations (>80)"
        % (g["mobile"]["compliant_60_80"],
           g["mobile"]["non_compliant_below_60_evidence_short"],
           g["mobile"]["violations_above_80"]))
    for ex in g["mobile"]["violation_examples"]:
        add(L, "  - OVER-80 %(mpn)s len=%(len)d %(value)r" % ex)
    add(L, "- INVOICE_DESC <=40 CAPS: %d over-length | %d not-uppercase"
        % (g["invoice"]["over_40"], g["invoice"]["not_uppercase"]))
    for ex in g["invoice"]["violation_examples"]:
        add(L, "  - OVER-40 %(mpn)s len=%(len)d %(value)r" % ex)
    add(L)
    h = res["unsupported"]
    add(L, "## H. Unsupported / inferred value detection - %s"
        % ("PASS" if h["pass"] else "FAIL"))
    add(L, "- INFERRED emitted: %d (must be 0)" % h["inferred_emitted"])
    add(L, "- filler phrases: %d | fabricated URLs: %d | asset-existence "
           "claims: %d | blanket warranty claims: %d"
        % (len(h["filler_phrases"]), len(h["fabricated_urls"]),
           len(h["asset_existence_claims"]), len(h["blanket_warranty_claims"])))
    add(L)
    i_ = res["blanks"]
    add(L, "## I. Blank-field analysis")
    add(L, "- %(blank_cells)d/%(total_cells)d cells blank (%(pct_blank)s%%); "
           "%(fully_blank_columns)d columns always blank; "
           "%(intentional_no_source_blanks)d blanks are intentional "
           "(no source data)" % i_)
    for k, v in i_["by_category"].items():
        add(L, "- blank in %-22s %7d" % (k, v))
    add(L)
    j = res["quality"]
    add(L, "## J. Data-quality flags (flags only - no auto-correction)")
    add(L, "- duplicate MPNs: %(count)d %(items)s" % j["duplicate_mpns"])
    add(L, "- MPN/desc leading-token mismatches: %(exact_leading_token_mismatch)d"
           " | near-misses: %(near_miss_similarity)d %(near_miss_examples)s"
        % j["mpn_desc_mismatch"])
    add(L, "- suspected typos: %(rows_affected)d rows, %(distinct)s kinds "
           "%(detail)s" % j["suspected_typos"])
    add(L, "- placeholder brands: %(placeholder_brands)s" % j)
    add(L, "- missing manufacturer: %(missing_manufacturer)d | "
           "missing resolved brand: %(missing_resolved_brand)d" % j)
    add(L, "- sparse descriptions (<20 ch): %(sparse_descriptions_lt20)d | "
           "duplicate description groups: %(groups)d (+%(extra_copies)d copies)"
        % {**j, **j["duplicate_descriptions"]})
    add(L)
    add(L, "## K. Ground-truth sample size")
    add(L, DISCLAIMER)
    add(L)
    add(L, "## Provenance summary")
    add(L, "- " + ", ".join("%s=%d" % (s, n) for s, n in
                            res["provenance"].items()))
    add(L)
    add(L, "## Overall verdict: %s" % res["verdict"])
    return L


def main():
    exp_hdr, gt_rows = load_csv(EXPECTED)
    in_hdr, in_rows = load_csv(INPUT)
    out_hdr, out_rows = load_csv(OUTPUT)

    prov = {}
    if os.path.exists(RUN_REPORT):
        with open(RUN_REPORT, encoding="utf-8") as f:
            prov = json.load(f).get("attribute_provenance", {}).get("by_status", {})

    res = {
        "header": check_header_parity(exp_hdr, out_hdr),
        "rows": check_row_counts(len(in_rows), len(out_rows)),
        "preservation": check_input_preservation(in_rows, out_rows),
        "gt": ground_truth_scores(exp_hdr, gt_rows, out_rows),
        "coverage": coverage_by_category(out_rows, out_hdr),
        "limits": char_limit_compliance(out_rows),
        "unsupported": unsupported_value_scan(out_rows, prov),
        "blanks": blank_field_analysis(out_rows, out_hdr),
        "quality": data_quality_flags(in_rows, out_rows),
        "provenance": prov,
    }
    gates = [res["header"]["pass"], res["rows"]["pass"],
             res["preservation"]["pass"], res["limits"]["pass"],
             res["unsupported"]["pass"]]
    res["verdict"] = "PASS" if all(gates) else "FAIL"

    lines = render_report(res)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote %s" % REPORT)
    print("verdict:", res["verdict"])
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
