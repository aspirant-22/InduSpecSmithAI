"""Brand & manufacturer resolution from a raw row.

Sources of truth, in priority order:
  1. DIB_Brand / E1_Brand / Unilog_Brand  (cleaned, canonicalized)
  2. Manufacturer table via Part_Manuf
  3. Brand token found inside Part_Desc
  4. MPN brand prefix (appliance model codes, used by UniLog reference too)

All fallbacks are applied only where the official reference file (loaded by
src/references.py) does not already provide the value.
"""
import re

from .common import clean, non_placeholder, normalize_ws
from .knowledge import (
    MANUFACTURERS, DIB_BRAND_FIX, E1_BRAND_FIX, BRAND_ALIASES, APPLIANCE_PARENT,
)

# Small extra canonical names not in knowledge.py (kept in sync target)
_EXTRA_BRAND_FIX = {
    "FRIGIDAIRE": "FRIGIDAIRE®",
    "WHIRLPOOL": "Whirlpool®",
    "Whirlpool": "Whirlpool®",
    "KITCHENAID": "KitchenAid",
    "MAYTAG": "Maytag",
    "GE": "GE",
    "LG": "LG",
}


def canonical_brand(raw):
    """Return the canonical display brand for a raw brand string, or ''."""
    s = non_placeholder(raw)
    if not s:
        return ""
    s = s.strip()
    if s in DIB_BRAND_FIX:
        return DIB_BRAND_FIX[s]
    if s in E1_BRAND_FIX:
        return E1_BRAND_FIX[s]
    if s in _EXTRA_BRAND_FIX:
        return _EXTRA_BRAND_FIX[s]
    low = s.lower()
    for k, canon in BRAND_ALIASES.items():
        if low == k:
            return canon
    return s


def _brand_from_manufacturer(row):
    m = non_placeholder(row.get("Part_Manuf", ""))
    if m in MANUFACTURERS:
        return MANUFACTURERS[m][1]
    return ""


# Brand implied by description phrasing (appliance-heavy data)
DESC_BRAND_PATTERNS = [
    (r"\bge\b", "GE"),
    (r"\bspeed queen\b", "Speed Queen"),
    (r"\bsq\s+(?:elect|gas)?\s*(?:dryer|washer)", "Speed Queen"),
    (r"\bcaf[eé]\b", "Café"),
]


def _brand_from_desc(desc):
    """Find first brand alias appearing in the description text."""
    low = (desc or "").lower()
    for rx, canon in DESC_BRAND_PATTERNS:
        if re.search(rx, low):
            return canon
    # longest aliases first so 'fe electric' style multiword matches win
    for k, canon in sorted(BRAND_ALIASES.items(), key=lambda t: -len(t[0])):
        if " " not in k and re.search(r"\b" + re.escape(k) + r"\b", low):
            return canon
    return ""


# Appliance MPN brand prefixes (used heavily by APPDE appliance rows)
MPN_BRAND_PREFIX = [
    ("PDSH", "FRIGIDAIRE®"), ("EFDS", "FRIGIDAIRE®"), ("FFNC", "FRIGIDAIRE®"),
    ("FDB", "FRIGIDAIRE®"), ("FDST", "FRIGIDAIRE®"),
    ("WDTS", "Whirlpool®"), ("WDP", "Whirlpool®"), ("WR", "Whirlpool®"),
    ("WFW", "Whirlpool®"), ("WM", "Whirlpool®"), ("WS", "Whirlpool®"),
    ("KDPS", "KitchenAid"), ("KDT", "KitchenAid"), ("KDF", "KitchenAid"),
    ("KORS", "KitchenAid"),
    ("MHN", "Maytag"), ("MSD", "Maytag"), ("MED", "Maytag"),
    ("MVWP", "Maytag"),
    ("SLE", "Samsung"), ("SMC", "Samsung"), ("SMD", "Samsung"),
    ("XOU", "GE"),
    # single-letter family fallbacks (most specific prefixes listed first)
    ("P", "FRIGIDAIRE®"), ("K", "KitchenAid"),
]


def _brand_from_mpn(mpn):
    s = clean(mpn).upper()
    for prefix, canon in MPN_BRAND_PREFIX:
        if s.startswith(prefix):
            return canon
    return ""


def resolve_brand(row):
    """Chain all brand sources and return the best canonical brand."""
    brand = canonical_brand(row.get("DIB_Brand", ""))
    if not brand:
        brand = canonical_brand(row.get("E1_Brand", ""))
    if not brand:
        brand = canonical_brand(row.get("Unilog_Brand", ""))
    if not brand:
        # explicit brand token in description beats a distributor default
        brand = _brand_from_desc(row.get("Part_Desc", ""))
    if not brand:
        brand = _brand_from_manufacturer(row)
    if not brand:
        brand = _brand_from_mpn(row.get("Mfg_Part_Num", ""))
    return brand


def resolve_manufacturer(row, brand):
    """Best-effort manufacturer legal name from Part_Manuf or appliance parent."""
    m = non_placeholder(row.get("Part_Manuf", ""))
    if brand in APPLIANCE_PARENT and (m.lower().startswith("appliance") or
                                      "cooperative" in m.lower() or
                                      "appliance parts" in m.lower()):
        # distributor rows: the real OEM is the brand parent
        return APPLIANCE_PARENT[brand]
    if m in MANUFACTURERS:
        return MANUFACTURERS[m][0]
    if clean(m):
        return clean(m)
    if brand in APPLIANCE_PARENT:
        return APPLIANCE_PARENT[brand]
    if brand:
        # last-resort: brand name doubles as company name
        return re.sub(r"[®™©]", "", brand)
    return ""