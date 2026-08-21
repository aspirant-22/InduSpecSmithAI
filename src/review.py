"""Row-level confidence scoring and duplicate analysis (report-only).

Phase 8 (R1 + R2). Nothing here writes or alters the delivery CSV: the
252-column schema is fixed and pipeline output is never modified. The
confidence score is an evidence-completeness proxy computed ONLY from
signals present in the input row and the generated output row. It is NOT
a prediction-accuracy estimate - no row-level ground truth exists for
the 1,000-row dataset, so none is assumed.

Every rule mirrors a signal already used by tools/evaluate.py section J
(placeholders, duplicate MPNs, duplicate descriptions, leading-token
mismatch, typo dictionary, sparse descriptions) or section G (mobile
description length). All functions are pure and deterministic; callers
sort before rendering so repeated runs are byte-identical.
"""
import re
from collections import Counter

MOBILE_MIN, MOBILE_MAX = 60, 80
SPARSE_DESC_MIN = 20
NEAR_MISS_SIMILARITY = 0.8

# Score bands. LOW is exactly the needs-human-review set.
BAND_HIGH_MIN = 80
BAND_MEDIUM_MIN = 60

# Documented penalties. Order matters: it is also the reason-code order
# emitted for every row, which keeps reports stable.
PENALTIES = (
    # (reason code, weight, description)
    ("no_attributes", 25,
     "no attribute slots populated"),
    ("mobile_desc_short", 15,
     "MOBILE_DESC below the strict %d-char floor" % MOBILE_MIN),
    ("duplicate_mpn_group", 15,
     "Mfg_Part_Num appears on more than one row"),
    ("manufacturer_unresolved", 10,
     "MANUFACTURER_NAME blank in output"),
    ("sparse_input_desc", 10,
     "Part_Desc shorter than %d characters" % SPARSE_DESC_MIN),
    ("suspected_typo", 10,
     "known typo pattern in Part_Desc"),
    ("brand_unresolved", 5,
     "BRAND_NAME blank in output"),
    ("mpn_desc_mismatch", 5,
     "leading desc token does not match Mfg_Part_Num"),
)
WEIGHTS = {code: w for code, w, _ in PENALTIES}
REASON_HELP = {code: help_ for code, _, help_ in PENALTIES}

# Same dictionary as tools/evaluate.py section J.
TYPO_DICT = {
    "mocrowave": "microwave", "outet": "outlet", "brakcet": "bracket",
    "indudtrial": "industrial", "trox": "trex", "rachet": "ratchet",
    "frming": "framing",
}


def attr_slot_count(out_row):
    """Populated ATTRIBUTE_LABEL slots (the established coverage metric)."""
    return sum(1 for i in range(1, 51)
               if out_row.get("ATTRIBUTE_LABEL %d" % i, "").strip())


def leading_token_mismatch(in_row):
    """True when a qualified leading desc token differs from the MPN.

    A token qualifies only when it looks like a part number (>=5 chars,
    contains a digit, restricted charset) - identical rule to the
    evaluation harness, so ordinary first words never trigger it. Both
    hard mismatches and near-misses count; the score does not pretend to
    tell them apart.
    """
    mpn = (in_row.get("Mfg_Part_Num", "") or "").strip()
    toks = (in_row.get("Part_Desc", "") or "").strip().split()
    if not toks:
        return False
    tok = toks[0]
    if not (re.search(r"\d", tok) and len(tok) >= 5
            and re.fullmatch(r"[A-Za-z0-9\-/.]+", tok)):
        return False
    return tok.upper() != mpn.upper()


def suspected_typo(in_row):
    """First known typo found in the description, else None."""
    low = (in_row.get("Part_Desc", "") or "").lower()
    for t in sorted(TYPO_DICT):
        if re.search(r"\b" + re.escape(t) + r"\b", low):
            return t
    return None


def duplicate_mpn_groups(in_rows):
    """{mpn: [1-based row numbers]} for every MPN appearing more than once."""
    counts = Counter((r.get("Mfg_Part_Num", "") or "").strip()
                     for r in in_rows)
    groups = {}
    for pos, r in enumerate(in_rows, start=1):
        mpn = (r.get("Mfg_Part_Num", "") or "").strip()
        if mpn and counts[mpn] > 1:
            groups.setdefault(mpn, []).append(pos)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def duplicate_desc_groups(in_rows):
    """{normalized_desc: [1-based row numbers]} for shared descriptions."""
    key = lambda r: (r.get("Part_Desc", "") or "").strip().lower()
    counts = Counter(key(r) for r in in_rows)
    groups = {}
    for pos, r in enumerate(in_rows, start=1):
        k = key(r)
        if k and counts[k] > 1:
            groups.setdefault(k, []).append(pos)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def score_row(in_row, out_row, dup_sizes=None):
    """Deterministic evidence-completeness score for one row.

    Starts at 100 and applies each documented penalty once. Returns the
    score, band, needs-human-review flag and the ordered reason list.
    """
    reasons = []
    if attr_slot_count(out_row) == 0:
        reasons.append("no_attributes")
    mobile_len = len(out_row.get("MOBILE_DESC", ""))
    if mobile_len < MOBILE_MIN:
        reasons.append("mobile_desc_short")
    if dup_sizes and (dup_sizes.get((in_row.get("Mfg_Part_Num", "") or "")
                                    .strip(), 0) > 1):
        reasons.append("duplicate_mpn_group")
    if not out_row.get("MANUFACTURER_NAME", "").strip():
        reasons.append("manufacturer_unresolved")
    if len((in_row.get("Part_Desc", "") or "").strip()) < SPARSE_DESC_MIN:
        reasons.append("sparse_input_desc")
    if suspected_typo(in_row):
        reasons.append("suspected_typo")
    if not out_row.get("BRAND_NAME", "").strip():
        reasons.append("brand_unresolved")
    if leading_token_mismatch(in_row):
        reasons.append("mpn_desc_mismatch")

    confidence = max(0, 100 - sum(WEIGHTS[r] for r in reasons))
    if confidence >= BAND_HIGH_MIN:
        band = "HIGH"
    elif confidence >= BAND_MEDIUM_MIN:
        band = "MEDIUM"
    else:
        band = "LOW"
    return {"confidence": confidence, "band": band,
            "needs_human_review": confidence < BAND_MEDIUM_MIN,
            "reasons": reasons, "mobile_desc_len": mobile_len}


def build_review_rows(in_rows, out_rows):
    """Per-row review records aligned positionally with the input."""
    if len(in_rows) != len(out_rows):
        raise ValueError("input/output row count mismatch: %d vs %d"
                         % (len(in_rows), len(out_rows)))
    counts = Counter((r.get("Mfg_Part_Num", "") or "").strip()
                     for r in in_rows)
    records = []
    for pos, (in_row, out_row) in enumerate(zip(in_rows, out_rows), start=1):
        s = score_row(in_row, out_row, dup_sizes=counts)
        records.append({
            "row": pos,
            "mfg_part_num": (in_row.get("Mfg_Part_Num", "") or "").strip(),
            "confidence": s["confidence"],
            "band": s["band"],
            "needs_human_review": s["needs_human_review"],
            "reasons": "|".join(s["reasons"]),
            "attribute_slots": attr_slot_count(out_row),
            "mobile_desc_len": s["mobile_desc_len"],
            "duplicate_group_size": counts[(in_row.get("Mfg_Part_Num", "")
                                            or "").strip()],
        })
    return records


def summarize(records, mpn_groups, desc_groups):
    """Aggregate stats for the report header (all sorted/deterministic)."""
    bands = Counter(r["band"] for r in records)
    reason_counts = Counter(rc for r in records
                            for rc in r["reasons"].split("|") if rc)
    return {
        "rows": len(records),
        "needs_human_review": sum(1 for r in records
                                  if r["needs_human_review"]),
        "bands": {b: bands.get(b, 0) for b in ("HIGH", "MEDIUM", "LOW")},
        "reason_frequency": sorted(reason_counts.items(),
                                   key=lambda kv: (-kv[1], kv[0])),
        "duplicate_mpn_groups": mpn_groups,
        "duplicate_desc_groups": desc_groups,
    }
