"""Description generators (MOBILE/INVOICE/SHORT/LONG/RETAIL/MARKETING/FEATURES).

Evidence rules (Category-A alignment):
  - Every value in every description comes from the input row itself:
    Part_Desc tokens, resolved brand/manufacturer, or attributes extracted
    from Part_Desc. Nothing is padded, invented or "rounded out".
  - MOBILE_DESC targets the observed ground-truth range of 60-80 chars by
    choosing the most complete supported variant that fits; if the evidence
    cannot reach 60 chars the shorter evidence-based text wins over filler.
  - INVOICE_DESC is uppercase and <= 40 chars.
  - MARKETING_DESCRIPTION stays blank: no manufacturer marketing copy can be
    derived deterministically from the provided data.
  - ITEM_FEATURES lists only extracted attributes; generic filler bullets
    are never added.
"""
import re

from .knowledge import INV_ABBR
from .common import normalize_ws

MOBILE_MIN = 60
MOBILE_MAX = 80
INVOICE_MAX = 40
SHORT_MAX = 200
LONG_MAX = 500

# phrases that must never appear (generic fabricated filler)
FORBIDDEN_FILLER = (
    "professional-grade build",
    "engineered for reliable",
    "manufacturer warranty applies",
    "compatible with standard mounting",
    "built for the worksite",
)


def _truncate_words(s, limit):
    """Hard limit at a word boundary; returns s unchanged if short enough."""
    if len(s) <= limit:
        return s
    cut = s[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,")


def mobile_in_range(s):
    """Explicit validator: MOBILE_DESC must be 60-80 characters."""
    return MOBILE_MIN <= len(s) <= MOBILE_MAX


def _abbrev(text):
    """Apply the invoice abbreviation dictionary to free text."""
    low = " " + text.lower().strip() + " "
    for word, code in INV_ABBR.items():
        low = re.sub(r"\b" + re.escape(word) + r"\b", " " + code + " ", low)
    return normalize_ws(low.replace(" - ", " ")).strip()


def _attr_map(attrs):
    return {lab: (val, uom) for lab, val, uom in attrs}


MOUNT_CODES = {"Leg": "LEG", "Built-in": "BLTIN", "Wall": "WALL",
               "Ceiling": "CEIL"}
MATERIAL_CODES = {"Stainless Steel": "SST", "Steel": "STL", "Aluminum": "ALUM",
                  "PVC": "PVC", "Composite": "COMP", "Vinyl": "VNL",
                  "Brass": "BRS", "Copper": "CPR", "Wood": "WD"}


def mobile_desc(manufacturer, brand, product, series, mpn, mounting, desc):
    """60-80 char headline built from the most complete supported variant.

    Candidate pieces, ground-truth order: [manufacturer], brand, product,
    series, mpn, [mounting]. The fullest variant that fits <=80 chars wins;
    shorter evidence-based output is preferred over any padding.
    """
    variants = []
    for use_mfr in (True, False):
        for use_mount in (True, False):
            for use_series in (True, False):
                parts = []
                if use_mfr and manufacturer:
                    parts.append(manufacturer)
                if brand:
                    parts.append(brand)
                if product:
                    parts.append(product)
                if use_series and series:
                    parts.append(series)
                if mpn:
                    parts.append(mpn)
                if use_mount and mounting:
                    parts.append(mounting)
                if parts:
                    variants.append(", ".join(parts))
    fit = [v for v in variants if len(v) <= MOBILE_MAX]
    if fit:
        return max(fit, key=len)
    # even the barest variant exceeds 80: truncate the shortest one
    return _truncate_words(min(variants, key=len), MOBILE_MAX)


def invoice_desc(desc, attrs, product, mpn):
    """<=40 char uppercase invoice line from supported attributes only."""
    av = _attr_map(attrs)
    toks = []
    p = _abbrev(product or "")
    if p:
        toks.append(p.upper())
    mount = av.get("Mounting Type", ("", ""))[0]
    if mount:
        toks.append(MOUNT_CODES.get(mount, _abbrev(mount).upper()))
    cycles = av.get("Number of Wash Cycles", ("", ""))[0]
    if cycles:
        toks.append(str(cycles))
    mat = av.get("Material", ("", ""))[0]
    code = MATERIAL_CODES.get(mat)
    if code:
        toks.append(code)
    v = av.get("Voltage Rating", ("", ""))[0]
    a = av.get("Amperage Rating", ("", ""))[0]
    if v:
        toks.append("%sV" % v)
    if a:
        toks.append("%sA" % a)
    snd = av.get("Sound Level", ("", ""))[0]
    if snd:
        toks.append("%sDBA" % snd)
    grit = av.get("Abrasive Grit", ("", ""))[0]
    if grit:
        toks.append(str(grit).upper())
    hp = av.get("Horsepower", ("", ""))[0]
    if hp:
        toks.append("%sHP" % hp)
    ga = av.get("Gauge", ("", ""))[0]
    if ga:
        toks.append("%sGA" % ga)
    s = " ".join(toks).upper()
    return _truncate_words(s, INVOICE_MAX)


def _short_phrase(lab, val, uom):
    """Attribute phrase in the observed SHORT_DESC style."""
    if lab == "Mounting Type":
        return "%s Mounting" % val
    if lab == "Number of Wash Cycles":
        return "%s-Wash Cycle" % val
    if lab == "Speed":
        return "%s-Speed" % val
    if uom:
        return "%s %s" % (val, uom)
    return str(val)


def _long_phrase(lab, val, uom):
    """Attribute phrase in the observed LONG_DESC1 style."""
    if lab == "Number of Wash Cycles":
        return "%s Wash Cycles" % val
    if lab == "Sound Level":
        return "%s dBA Sound Level" % val
    if lab == "Mounting Type":
        return "%s Mounting" % val
    if lab == "Speed":
        return "%s-Speed" % val
    if uom:
        return "%s %s" % (val, uom)
    return str(val)


def _detail_phrases(attrs, formatter):
    """Ordered attribute phrases; Material/Color/Finish deduped by value."""
    details = []
    seen_values = set()
    for lab, val, uom in attrs:
        if not val or lab in ("Series", "Model", "Additional Information"):
            continue
        if lab in ("Material", "Color", "Finish"):
            if str(val) in seen_values:
                continue
            seen_values.add(str(val))
            details.append(str(val))
        else:
            details.append(formatter(lab, val, uom))
    return details


def short_desc(desc, attrs, brand, series, mpn, product, mounting):
    """Brand + Series + MPN + Product + 'With' + supported attribute phrases."""
    parts = [p for p in (brand, series, mpn, product) if p]
    details = _detail_phrases(attrs, _short_phrase)
    s = " ".join(parts)
    if details:
        s += " With " + ", ".join(details)
    return _truncate_words(s, SHORT_MAX)


def long_desc1(desc, attrs, brand, product, series, mpn, addl_text=""):
    """Brand + Product + Series + supported specs + Additional Information."""
    head = " ".join(p for p in (brand, product) if p)
    spec = []
    if series:
        spec.append(series)
    spec += _detail_phrases(attrs, _long_phrase)
    s = head
    if spec:
        s += ", " + ", ".join(spec)
    if addl_text:
        s += ", Additional Information: " + addl_text
    return _truncate_words(s, LONG_MAX)


def retail_desc(desc, attrs, product, series):
    """Ground-truth structure: '[Series] Product, attr phrases' - no brand/MPN."""
    lead = " ".join(p for p in (series, product) if p) or "Product"
    details = _detail_phrases(attrs, _short_phrase)
    s = lead
    if details:
        s += ", " + ", ".join(details)
    return _truncate_words(s, SHORT_MAX)


def marketing_description(desc, attrs, brand, product):
    """Intentionally blank.

    The expected-output sample shows manufacturer marketing copy that cannot
    be derived deterministically from the provided input columns. Per the
    no-hallucination rule this field stays empty rather than being filled
    with generated claims.
    """
    return ""


def item_features(attrs, maxn=10):
    """Evidence-backed attribute bullets only - never generic filler."""
    feats = []
    for lab, val, uom in attrs:
        if not val:
            continue
        feats.append("%s: %s%s" % (lab, val, (" " + uom) if uom else ""))
    return feats[:maxn]


INFO_TOKENS = [
    "delay start", "fold tine", "leak detection", "sani rinse",
    "sensor cycle", "triple wash", "normal cycle", "quick wash",
    "moisture repellent", "heating element", "third rack", "3rd rack",
]


def additional_information(desc, attrs):
    """'Additional Information:' tail from feature tokens found in Part_Desc."""
    extra = []
    low = desc.lower()
    for token in INFO_TOKENS:
        if re.search(r"\b" + re.escape(token) + r"\b", low):
            extra.append(token.title())
    return extra
