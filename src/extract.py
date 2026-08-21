"""Attribute extraction from descriptions.

Each extractor returns either None or a (label, value, uom) triple.
The pipeline layers them in a canonical attribute order per product family.
"""
import re

from .knowledge import (
    COLOR_CODES, COLOR_WORDS, FINISH_TOKENS, MATERIAL_WORDS, PACK_PATTERNS,
    UNIT_STANDARD, SERIES_WORDS,
)
from .classify import classify
from .branding import resolve_brand

D = {}


def _find_first(desc, *pats):
    for p in pats:
        m = re.search(p, desc, re.I)
        if m:
            return m
    return None


def extract_voltage(desc):
    m = _find_first(desc, r"(\d{2,3})\s*[- ]?\s*v(?:olts?)?\b", r"\bVAC\b")
    if m and m.group(1):
        v = m.group(1)
        if 100 <= int(v) <= 600:
            return ("Voltage Rating", v, "V")
    v = _find_first(desc, r"(\d{3})\b.*?\bVAC\b")
    if v:
        return ("Voltage Rating", v.group(1), "V")
    return None


def extract_amperage(desc):
    m = _find_first(desc, r"(\d+(?:\.\d+)?)\s*[- ]?a(?:mps?|mp)\b",
                    r"(\d+(?:\.\d+)?)\s*A\b")
    if m and m.group(1):
        return ("Amperage Rating", m.group(1), "A")
    return None


def extract_wattage(desc):
    m = _find_first(desc, r"(\d{2,5})\s*w(?:atts?)?\b")
    if m and m.group(1):
        return ("Wattage", m.group(1), "W")
    return None


def extract_sound_level(desc):
    m = _find_first(desc, r"(\d{2})\s*dba\b")
    if m:
        return ("Sound Level", m.group(1), "dBA")
    return None


def extract_material(desc):
    low = desc.lower()
    for word, name in MATERIAL_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            return ("Material", name, "")
    return None


def extract_color(desc):
    """Detect a color/finish from explicit words or trailing finish codes."""
    low = desc.lower()
    for word, name in COLOR_WORDS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            if word == "black" and "matte black" in low:
                continue
            return ("Color", name, "")
    # trailing token style "SS - Display Only" or "WH"
    m = re.search(r"\s([A-Za-z0-9]+)\s*$", desc.strip())
    if m:
        tok = m.group(1).upper()
        if tok in COLOR_CODES and COLOR_CODES[tok]:
            return ("Color", COLOR_CODES[tok], "")
    return None


def extract_finish(desc):
    """Explicit FINISH_TOKENS embedded mid-description."""
    for tok in FINISH_TOKENS:
        if tok in COLOR_CODES and COLOR_CODES[tok] and re.search(
                r"\b" + re.escape(tok) + r"\b", desc, re.I):
            return ("Finish", COLOR_CODES[tok], "")
    return None


def extract_series(desc):
    low = desc.lower()
    for w in sorted(SERIES_WORDS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            name = w.title()
            return ("Series", name, "")
    return None


def extract_size(desc):
    """Best-effort Size attribute from dimension tokens."""
    from .normalize import parse_dimensions
    _, dims = parse_dimensions(desc)
    if "diameter" in dims and dims["diameter"]:
        v = dims["diameter"]
        return ("Size", "%s in" % v, "")
    if "d1" in dims:
        return ("Size", "%s in x %s in" % (dims["d1"], dims["d2"]), "")
    if "mm_size" in dims:
        return ("Size", "%s mm" % dims["mm_size"], "")
    return None


def extract_grit(desc):
    m = _find_first(desc, r"(\d{2,4})\s*-(?:grit|\s*grit\b)", r"\b(\d{2,4})\s*grit\b")
    if m and m.group(1):
        return ("Abrasive Grit", m.group(1), "")
    m = _find_first(desc, r"\bP(\d{2,4})\b")
    if m:
        return ("Abrasive Grit", "P" + m.group(1), "")
    return None


def extract_pack(desc):
    for pat, uom in PACK_PATTERNS:
        m = re.search(pat, desc, re.I)
        if m:
            return ("Package Quantity", m.group(1), uom)
    return None


def extract_cycle_count(desc):
    m = _find_first(desc, r"(\d+)[ -]wash[ -]?cycle", r"(\d+)\s*cycles\b")
    if m:
        return ("Number of Wash Cycles", m.group(1), "")
    return None


def extract_mounting(desc):
    low = desc.lower()
    if re.search(r"\bbuilt[- ]?in\b", low):
        return ("Mounting Type", "Built-in", "")
    if re.search(r"\bleg(?: mount)?\b", low):
        return ("Mounting Type", "Leg", "")
    if re.search(r"\bwall[- ]??mount\b", low):
        return ("Mounting Type", "Wall", "")
    if re.search(r"\bceiling\b", low):
        return ("Mounting Type", "Ceiling", "")
    return None


def extract_product_name(desc):
    """Product Name column = item type (the classifier's product)."""
    return classify(desc)["product"]


ORDER_BY = {
    "dishwasher": ["Series", "Number of Wash Cycles", "Voltage Rating",
                   "Amperage Rating", "Mounting Type", "Size",
                   "Depth With Door Open", "Minimum Height", "Maximum Height",
                   "Sound Level", "Material", "Color", "Finish",
                   "Additional Information"],
    "coffee maker": ["Series", "Voltage Rating", "Amperage Rating", "Material",
                     "Color", "Capacity", "Additional Information"],
}


def extract_all(desc, mpn="", brand=""):
    """Run all extractors, dedupe by label, return list of (label, value, uom)."""
    funcs = [
        extract_series, extract_voltage, extract_amperage, extract_wattage,
        extract_sound_level, extract_cycle_count, extract_mounting,
        extract_size, extract_material, extract_color, extract_finish,
        extract_grit, extract_pack,
    ]
    attrs = []
    seen = set()
    for fn in funcs:
        try:
            r = fn(desc)
        except Exception:
            r = None
        if r and r[0] not in seen:
            seen.add(r[0])
            attrs.append(r)
    return attrs