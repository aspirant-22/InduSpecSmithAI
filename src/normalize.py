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


# Number fragment shared by the dimension patterns below.
# Decimal-first ordering: '3.2' must be consumed whole, never as '3' + '.2'.
_NUM = r"(\d+\.\d+|\d+(?:-\d+/\d+)?|\d+/\d+|\.\d+)"
# Unit suffix after a dimension number: a quote mark OR a bare in/inches form.
_UNIT_SUFFIX = r'(?:\s*["\u2033]|\s*(?:in(?:ch(?:es)?)?)\.?)?'


def parse_dimensions(desc):
    """
    Extract a dimensional summary from a description.
    Returns (size_string, dims_dict) where dims_dict has keys like
    'length','width','height','diameter','thickness','arbor','dual_in',
    'single_in' etc.

    Supported evidence forms (all explicit-unit; bare numbers are ignored):
      4-1/2" x 1/8" x 7/8"   triple quoted
      1/2in x 18in           double with explicit in-suffix
      12"/300mm              dual imperial/metric single dimension
      300mm                  metric single
      7-1/4in.               single explicit-inch dimension
    """
    d = str(desc)
    # dual imperial/metric: 12"/300mm (one dimension expressed twice)
    dual = re.search(
        r"(?<![\w.\-/])" + _NUM + r'\s*["\u2033]\s*/\s*(\d{2,4})\s*mm\b',
        d, re.I)
    # Pattern A: full triple like 4-1/2" x 1/8" x 7/8", 1/2"x18"
    triple = re.search(
        r"(?<![\w.\-/])" + _NUM + _UNIT_SUFFIX + r"\s*x\s*"
        + _NUM + _UNIT_SUFFIX + r"\s*x\s*"
        + _NUM + _UNIT_SUFFIX + r">?",
        d, re.I)
    # Pattern B: double like 4-1/2" x 1/8" or 1/2in x 18in
    double = re.search(
        r"(?<![\w.\-/])" + _NUM + _UNIT_SUFFIX + r"\s*x\s*"
        + _NUM + _UNIT_SUFFIX,
        d, re.I)
    # size hints
    mm = re.search(r"(\d+(?:\.\d+)?)\s*mm", d, re.I)

    # single explicit-inch dimension, e.g. '7-1/4in.' blade diameter.
    # Guards: the unit must be ATTACHED to the number ('7-1/4in.', '18in') -
    # a spaced form ('4 in', '12345 in stock') stays ambiguous and is
    # refused; a period-abbreviated form ('in.') is accepted even when a
    # code follows ('24T'); the bare form is rejected when a number follows
    # ('3 in 1' style traps); value capped at 200 like the other branches.
    single = re.search(
        r"(?<![\w.\-/])" + _NUM +
        r"(?:in(?:ch(?:es)?)?)\.(?!\d)",
        d, re.I)
    if not single:
        single = re.search(
            r"(?<![\w.\-/])" + _NUM +
            r"(?:in(?:ch(?:es)?)?)\b(?!\.?\s*\d)",
            d, re.I)
    if single:
        try:
            sane = float(single.group(1).split("-")[0].split("/")[0]) <= 200
        except ValueError:
            sane = False
        if not sane:
            single = None

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
    elif dual:
        a, b = dual.groups()
        parts = [inch_fraction_wrap(a)]
        dims["dual_in"] = a
        dims["dual_mm"] = b
    if mm:
        dims["mm_size"] = mm.group(1)
    if single and not (triple or double or dual):
        dims["single_in"] = single.group(1)
        if not parts:
            parts = [inch_fraction_wrap(single.group(1))]
    size = ""
    if parts:
        size = " in x ".join(parts) + " in"
    return size, dims


def clean_token(s):
    return normalize_ws(s).strip(" ,-")


def normalize_desc_for_attrs(desc):
    """Lower-normalized description used by attribute extraction rules."""
    return normalize_ws(desc).strip()