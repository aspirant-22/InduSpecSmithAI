"""Attribute extraction from descriptions.

Every extractor performs a deterministic normalization of a token found in
Part_Desc and returns a Fact carrying its own provenance (see src/facts.py).
No extractor may invent values: if the pattern is not present, it returns
None and the attribute stays blank.
"""
import re

from .knowledge import (
    COLOR_CODES, COLOR_WORDS, FINISH_TOKENS, MATERIAL_WORDS, PACK_PATTERNS,
    UNIT_STANDARD, SERIES_WORDS,
)
from .classify import classify
from .branding import resolve_brand
from .facts import Fact, NORMALIZED

D = {}


def _find_first(desc, *pats):
    for p in pats:
        m = re.search(p, desc, re.I)
        if m:
            return m
    return None


def _fact(label, m, value=None, uom="", group=1):
    """Build a NORMALIZED Fact from a regex match (evidence = matched span)."""
    v = value if value is not None else m.group(group)
    return Fact(label=label, value=str(v), uom=uom,
                evidence=m.group(0), status=NORMALIZED)


def extract_voltage(desc):
    m = _find_first(desc, r"(\d{2,3})\s*[- ]?\s*v(?:olts?)?\b", r"\bVAC\b")
    if m and m.group(1):
        v = m.group(1)
        if 100 <= int(v) <= 600:
            return _fact("Voltage Rating", m, uom="V")
    v = _find_first(desc, r"(\d{3})\b.*?\bVAC\b")
    if v:
        return _fact("Voltage Rating", v, uom="V")
    return None


def extract_amperage(desc):
    # Token-boundary guards on both sides: a rating must stand alone, never
    # inside a hyphenated identifier ('9A-570-240', 'TGI2-T36A') or glued to
    # letters/digits ('KPTDR050A', 'BATT4A'). A match that IS the leading
    # token is the part number itself ('37418A Kichler Bath Light'), not a
    # rating.
    m = _find_first(desc,
                    r"(?<![\w.\-/])(\d+(?:\.\d+)?)\s*[- ]?a(?:mps?|mp)\b(?![\w-])",
                    r"(?<![\w.\-/])(\d+(?:\.\d+)?)\s*A\b(?![\w-])")
    if m and m.group(1):
        if desc.split()[0].upper() == m.group(0).strip().upper():
            return None
        return _fact("Amperage Rating", m, uom="A")
    return None


def extract_wattage(desc):
    # multi-digit: spacing allowed ('60 W', '1500 watts')
    m = _find_first(desc, r"\b(\d{2,5})\s*w(?:atts?)?\b")
    # single-digit: must be attached ('9W') - a spaced form like 'LowE-2 w/'
    # is a code fragment, not a watt value
    if not m:
        m = _find_first(desc, r"\b(\d)w(?:atts?)?\b")
    if m and m.group(1) and 1 <= int(m.group(1)) <= 9999:
        return _fact("Wattage", m, uom="W")
    return None


def extract_sound_level(desc):
    m = _find_first(desc, r"(\d{2})\s*dba\b")
    if m:
        return _fact("Sound Level", m, uom="dBA")
    return None


def extract_color_temperature(desc):
    """Bulb CCT: '50k' -> 5000 K, '5000k' -> 5000 K (trade convention)."""
    m = _find_first(desc, r"\b(\d{4})\s*k\b", r"\b(\d{2})k\b")
    if m:
        return _fact("Color Temperature", m,
                     value=str(int(m.group(1)) * (1 if len(m.group(1)) == 4 else 100)),
                     uom="K")
    return None


def extract_lumens(desc):
    m = _find_first(desc, r"(\d{3,5})\s*lm\b")
    if m:
        return _fact("Lumens", m, uom="lm")
    return None


def extract_material(desc):
    low = desc.lower()
    for word, name in MATERIAL_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            return Fact(label="Material", value=name, status=NORMALIZED,
                        evidence=word)
    return None


def extract_color(desc):
    """Detect a color/finish from explicit words or trailing finish codes."""
    low = desc.lower()
    for word, name in COLOR_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            if word == "black" and "matte black" in low:
                continue
            return Fact(label="Color", value=name, status=NORMALIZED,
                        evidence=word)
    # trailing token style "SS - Display Only" or "WH"
    m = re.search(r"\s([A-Za-z0-9]+)\s*$", desc.strip())
    if m:
        tok = m.group(1).upper()
        if tok in COLOR_CODES and COLOR_CODES[tok]:
            return Fact(label="Color", value=COLOR_CODES[tok],
                        evidence=tok, status=NORMALIZED)
    return None


def extract_finish(desc):
    """Explicit FINISH_TOKENS embedded mid-description."""
    for tok in FINISH_TOKENS:
        if tok in COLOR_CODES and COLOR_CODES[tok] and re.search(
                r"\b" + re.escape(tok) + r"\b", desc, re.I):
            return Fact(label="Finish", value=COLOR_CODES[tok],
                        evidence=tok, status=NORMALIZED)
    return None


def extract_series(desc):
    low = desc.lower()
    for w in sorted(SERIES_WORDS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            return Fact(label="Series", value=w.title(),
                        evidence=w, status=NORMALIZED)
    return None


def extract_size(desc):
    """Best-effort Size attribute from dimension tokens."""
    from .normalize import parse_dimensions
    _, dims = parse_dimensions(desc)
    if "diameter" in dims and dims["diameter"]:
        v = dims["diameter"]
        return Fact(label="Size", value="%s in" % v, status=NORMALIZED,
                    evidence=str(dims))
    if "d1" in dims:
        # unit-aware pair ('12 in x 20 mm', '4 ft x 65 ft'); legacy rows
        # without fmt keys keep the inches assumption
        v = " x ".join([dims.get("d1_fmt", "%s in" % dims["d1"]),
                        dims.get("d2_fmt", "%s in" % dims["d2"])])
        return Fact(label="Size", value=v,
                    status=NORMALIZED, evidence=str(dims))
    if "dual_in" in dims:
        ev = '%s"/%smm' % (dims["dual_in"], dims["dual_mm"])
        return Fact(label="Size", value="%s in" % dims["dual_in"],
                    status=NORMALIZED, evidence=ev)
    if "mm_size" in dims:
        return Fact(label="Size", value="%s mm" % dims["mm_size"],
                    status=NORMALIZED, evidence=str(dims))
    if "single_in" in dims:
        return Fact(label="Size", value="%s in" % dims["single_in"],
                    status=NORMALIZED, evidence=str(dims))
    return None


def extract_grit(desc):
    m = _find_first(desc, r"(\d{2,4})\s*-(?:grit|\s*grit\b)", r"\b(\d{2,4})\s*grit\b")
    if m and m.group(1):
        return _fact("Abrasive Grit", m)
    m = _find_first(desc, r"\bP(\d{2,4})\b")
    if m:
        return _fact("Abrasive Grit", m, value="P" + m.group(1))
    return None


def extract_pack(desc):
    for pat, uom in PACK_PATTERNS:
        m = re.search(pat, desc, re.I)
        if m:
            return _fact("Package Quantity", m, uom=uom)
    # explicit word form: 'Two Pack' - 'pack' establishes package semantics;
    # a bare count word without 'pack' is never a quantity.
    m = re.search(r"\b(two|three|four|five|six)[ -]pack\b", desc, re.I)
    if m:
        words = {"two": "2", "three": "3", "four": "4",
                 "five": "5", "six": "6"}
        return Fact(label="Package Quantity",
                    value=words[m.group(1).lower()], uom="pk",
                    evidence=m.group(0), status=NORMALIZED)
    return None


def extract_cycle_count(desc):
    m = _find_first(desc, r"(\d+)[ -]wash[ -]?cycle", r"(\d+)\s*cycles\b")
    if m:
        return _fact("Number of Wash Cycles", m)
    return None


def extract_gauge(desc):
    """Wire/nail gauge: '15GA', '18Ga', '16 gauge' -> Gauge = N ga."""
    m = _find_first(desc, r"\b(\d{1,2})\s*[- ]?\s*ga(?:uge)?\b")
    if m and m.group(1) and 1 <= int(m.group(1)) <= 50:
        return _fact("Gauge", m, uom="ga")
    return None


def extract_horsepower(desc):
    """Motor rating: '1.75HP', '3HP', '1/2 HP' -> Horsepower = N hp.

    Never touches voltage: '115V' / '1PH' carry no hp token.
    """
    m = _find_first(desc, r"\b(\d{1,3}(?:\.\d+)?(?:\s*/\s*\d+)?)\s*hp\b")
    if not m or not m.group(1):
        return None
    raw = m.group(1).replace(" ", "")
    if "/" in raw:
        a, _, b = raw.partition("/")
        ok = a.isdigit() and b.isdigit() and 0 < int(a) <= 20 <= 100 * int(b)
    else:
        ok = float(raw) <= 100
    if ok:
        return _fact("Horsepower", m, value=raw, uom="hp")
    return None


def extract_speed(desc):
    """'2-Speed' / '3 speed' -> Speed = N. Bare numbers never emit."""
    m = _find_first(desc, r"\b(\d{1,2})[\s-]speed\b")
    if m and m.group(1):
        return _fact("Speed", m)
    return None


def extract_range(desc):
    """Operating/reach range ONLY when the word 'range' anchors the token:
    '30ft Range' or 'Range of 50 ft'. A bare '100ft' is ambiguous (line
    length? product length?) and is deliberately refused."""
    m = _find_first(
        desc,
        r"\b(\d{1,4})\s*(?:ft|feet|foot)\s+range\b",
        r"\brange\s+(?:of\s+)?(\d{1,4})\s*(?:ft|feet|foot)\b")
    if m and m.group(1):
        return _fact("Range", m, uom="ft")
    return None


# a container noun must co-occur with the oz token; without it '16oz' on a
# hammer would be head weight in lb-oz, not this attribute.
_CONTAINER_RE = re.compile(
    r"\b(?:bottle|jug|canister|jar|drum|pail|tub|bucket|canteen|thermos"
    r"|flask)\b", re.I)


def extract_weight(desc):
    """Explicit container capacity in oz: '24oz Bottle' -> Weight = 24 oz."""
    if not _CONTAINER_RE.search(desc):
        return None
    m = _find_first(desc, r"\b(\d{1,4}(?:\.\d+)?)\s*(?:oz|ounces?)\b")
    if m and m.group(1):
        return _fact("Weight", m, uom="oz")
    return None


def extract_mounting(desc):
    low = desc.lower()
    checks = [(r"\bbuilt[- ]?in\b", "Built-in"), (r"\bleg(?: mount)?\b", "Leg"),
              (r"\bwall[- ]??mount\b", "Wall"), (r"\bceiling\b", "Ceiling")]
    for pat, val in checks:
        m = re.search(pat, low)
        if m:
            return Fact(label="Mounting Type", value=val,
                        evidence=m.group(0), status=NORMALIZED)
    return None


def extract_product_name(desc):
    """Product Name column = item type (the classifier's product)."""
    return classify(desc)["product"]


def extract_all(desc, mpn="", brand=""):
    """Run all extractors, dedupe by label, return list of Facts.

    Order follows the fixed extractor sequence below, so the same input
    always produces the same attribute ordering.
    """
    funcs = [
        extract_series, extract_voltage, extract_amperage, extract_wattage,
        extract_sound_level, extract_color_temperature, extract_lumens,
        extract_cycle_count, extract_mounting,
        extract_size, extract_material, extract_color, extract_finish,
        extract_grit, extract_pack,
        # Phase 6: appended (stable order - existing slots never shift)
        extract_gauge, extract_horsepower, extract_speed, extract_range,
        extract_weight,
    ]
    attrs = []
    seen = set()
    for fn in funcs:
        try:
            r = fn(desc)
        except Exception:
            r = None
        if r is not None and r.label not in seen:
            seen.add(r.label)
            attrs.append(r)
    return attrs
