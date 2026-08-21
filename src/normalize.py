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
# Ordering matters: decimal and fraction forms must be tried before bare
# digits so '3.2' is never split into '3' + '.2' and '3/8' into '3' + '/8'.
_NUM = r"(\d+\.\d+|\d+/\d+|\d+(?:-\d+/\d+)?|\.\d+)"
# Second-slot variant that also accepts a space-separated fraction tail
# ('x1 1/8"' staple lengths). Kept out of the shared fragment on purpose:
# a spaced fraction after an unrelated number must not start a dimension.
_NUM_XS = r"(\d+\.\d+|\d+/\d+|\d+(?:-\d+/\d+|\s\d+/\d+)?|\.\d+)"
# Unit suffix after a dimension number: quote mark, metric/foot markers,
# OR a bare in/inches form. Captures the marker so callers can tell
# inches from mm/ft instead of assuming every dimension is inches.
_UNIT_SUFFIX = r'(?:\s*(["\u2033]|mm\b|[\'\u2032]|ft\b|feet\b|in(?:ch(?:es)?)?\.?))?'


def _dim_text(num, unit):
    """Format one captured dimension honoring its explicit unit marker."""
    u = (unit or "").strip().lower()
    if u.startswith("mm"):
        return "%s mm" % num
    if u in ("'", "\u2032") or u.startswith("ft"):
        return "%s ft" % num
    return "%s in" % inch_fraction_wrap(num)


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
    # Pattern B: double like 4-1/2" x 1/8" or 1/2in x 18in; the second
    # slot also accepts a space-fraction tail ('x1 1/8"')
    double = re.search(
        r"(?<![\w.\-/])" + _NUM + _UNIT_SUFFIX + r"\s*x\s*"
        + _NUM_XS + _UNIT_SUFFIX,
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
        a, _, b, _, c, _ = triple.groups()
        parts = [inch_fraction_wrap(a) + " in",
                 inch_fraction_wrap(b) + " in",
                 inch_fraction_wrap(c) + " in"]
        dims["diameter"] = a
        dims["thickness"] = b
        dims["arbor"] = c
        # summarized
    elif double:
        a, ua, b, ub = double.groups()
        dims["d1"] = a
        dims["d2"] = b
        v1 = _dim_text(a, ua)
        v2 = _dim_text(b, ub)
        # foot-inch composite tail on a foot-marked second dim: 8'-6"
        if (ub or "").strip() in ("'", "\u2032"):
            comp = re.match(r"\s*-\s*(\d+)\s*(?:[\"\u2033]|in\.?\b)",
                            d[double.end():], re.I)
            if comp:
                v2 = "%s ft %s in" % (b, comp.group(1))
        parts = [v1, v2]
        dims["d1_fmt"] = v1
        dims["d2_fmt"] = v2
    elif dual:
        a, b = dual.groups()
        parts = [inch_fraction_wrap(a) + " in"]
        dims["dual_in"] = a
        dims["dual_mm"] = b
    if mm:
        dims["mm_size"] = mm.group(1)
    if single and not (triple or double or dual):
        dims["single_in"] = single.group(1)
        if not parts:
            parts = [inch_fraction_wrap(single.group(1)) + " in"]
    size = ""
    if parts:
        size = " x ".join(parts)
    return size, dims


def clean_token(s):
    return normalize_ws(s).strip(" ,-")


def normalize_desc_for_attrs(desc):
    """Lower-normalized description used by attribute extraction rules."""
    return normalize_ws(desc).strip()