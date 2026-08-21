"""Shared helpers: cleaning, placeholders, case handling, misc string ops."""
import re

PLACEHOLDER_EXACT = {
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "-",
    "",
    "nan",
    "none",
    "n/a",
    "na",
    "0",
}
PLACEHOLDER_PREFIX = ("--",)


def clean(v):
    """Return stripped string; None -> ''."""
    if v is None:
        return ""
    return str(v).strip()


def is_placeholder(v):
    """True if value is a known placeholder or empty."""
    s = clean(v)
    if not s:
        return True
    if s.lower() in PLACEHOLDER_EXACT:
        return True
    if s.startswith(PLACEHOLDER_PREFIX):
        return True
    return False


def non_placeholder(v):
    return "" if is_placeholder(v) else clean(v)


def title_each(word):
    """Title case a single lowercase-ish word, preserving already-capped acronyms."""
    if not word:
        return word
    if word.isupper() and len(word) <= 4:
        return word  # keep acronyms like LED, FSA
    if word.upper() in {"II", "III", "IV", "XL", "XS", "XXL", "SS", "CCT", "WASH"}:
        return word.upper()
    if re.fullmatch(r"[\d.\-/]+", word):
        return word
    return word[0].upper() + word[1:]


def to_sentence(s):
    """Sentence case: capitalize first letter, keep rest as-is."""
    s = clean(s)
    if not s:
        return s
    return s[0].upper() + s[1:]


def normalize_ws(s):
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", clean(s))


def strip_brand_prefix(desc, brand_tokens):
    """Remove leading tokens that duplicate the MPN at the start of descriptions."""
    parts = normalize_ws(desc).split(" ", 1)
    if len(parts) > 1 and parts[0] in brand_tokens:
        return parts[1]
    return desc


def safe_int(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


def is_within(s, lo, hi):
    s = clean(s)
    return s and lo <= len(s) <= hi