"""Normalizers: units, fractions, dimensions, attribute-style text cleanup."""
import re

from .knowledge import UNIT_STANDARD, decimal_to_fraction, format_inch_number
from .common import clean, normalize_ws

# ---------------------------------------------------------------------------
# Unit normalization
# ---------------------------------------------------------------------------
def norm_unit(u):
    """Normalize a unit token to the approved form."""
    key = (u or "").strip().lower().rstrip(".")
    if key in UNIT_STANDARD:
        return UNIT_STANDARD[key]
    return u.strip()


def normalize_dim_string(s):
    """
    Convert a raw dimensional string like '4-1/2"x1/8"x7/8"' or '5" x'
    into '4-1/2 in x 1/8 in x 7/8 in'. Preserves units (mm, ft) as-is.
    """
    if not s:
        return ""
    s = str(s).strip()
    # Replace double-quote and foot marks with unit tokens
    s = s.replace('"', " in").replace('\u2033', " in").replace('\u2032', " ft")
    s = s.replace("'", " ft")
    # normalize multiplication markers
    s = s.replace("*", "x").replace("\u00d7", "x").replace("\u2a09", "x")
    # '24x48' type compact -> '24 in x 48 in'  (handled by caller when units are inches)
    s = re.sub(r"\s*,\s*", " x ", s)
    # ensure space after number before unit: '50-1/4in' -> '50-1/4 in'
    s = re.sub(r"(\d)([a-zA-Z\u00c0-\u024f]+)", r"\1 \2", s)
    # collapse spaces around 'x'
    s = re.sub(r"\s*[xX]\s*", " x ", s)
    # convert decimals to inch fractions where exact
    parts = s.split(" x ")
    out = []
    for p in parts:
        p = p.strip()
        m = re.match(r"^(\d+)([- ]\d+/\d+)?\s+(in|ft|mm|cm)$", p)
        if m:
            out.append(p)
            continue
        # numbers without unit -> assume inches if value < 200 and came from inches context
        out.append(p)
    s = " x ".join(out)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def inch_fraction_wrap(value):
    """Wrap a numeric string into an inch number formatted with house style."""
    v = str(value).strip()
    if re.fullmatch(r"\d+-\d+/\d+", v) or re.fullmatch(r"\d+/\d+", v):
        return v
    return format_inch_number(v)


def parse_dimensions(desc):
    """
    Extract a dimensional summary from a description.
    Returns (size_string, dims_dict) where dims_dict has keys like
    'length','width','height','diameter','thickness','arbor' etc.
    """
    d = str(desc)
    # Pattern A: full triple like 4-1/2" x 1/8" x 7/8", 1/2"x18"
    triple = re.search(
        r"(\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)\s*[\"\u2033]?\s*x\s*"
        r"(\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)\s*[\"\u2033]?\s*x\s*"
        r"(\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)\s*[\"\u2033]?>?",
        d, re.I)
    double = re.search(
        r"(\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)\s*[\"\u2033]?\s*x\s*"
        r"(\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)\s*[\"\u2033]?(?:x\s*\d+)?",
        d, re.I)
    # size hints
    mm = re.search(r"(\d+(?:\.\d+)?)\s*mm", d, re.I)
    ft = re.search(r"(\d+(?:[-/]\d+)?)\s*(?:ft|'|')", d, re.I)

    parts = []
    dims = {}
    if triple:
        a, b, c = triple.groups()
        parts = [inch_fraction_wrap(a), inch_fraction_wrap(b), inch_fraction_wrap(c)]
        dims["diameter"] = a
        dims["thickness"] = b
        dims["arbor"] = c
        # summarized
    elif double:
        a, b = double.groups()
        parts = [inch_fraction_wrap(a), inch_fraction_wrap(b)]
        dims["d1"] = a
        dims["d2"] = b
    if mm:
        dims["mm_size"] = mm.group(1)
    size = ""
    if parts:
        size = " in x ".join(parts) + " in"
    return size, dims


def clean_token(s):
    return normalize_ws(s).strip(" ,-")


def normalize_desc_for_attrs(desc):
    """Lower-normalized description used by attribute extraction rules."""
    return normalize_ws(desc).strip()