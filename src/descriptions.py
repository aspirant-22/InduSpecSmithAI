"""Description generators (MOBILE/INVOICE/SHORT/LONG/RETAIL/MARKETING/FEATURES).

Mirrors the sample-output style:
  MOBILE_DESC    60-80 chars, prose headline
  INVOICE_DESC   40-char CAPS abbreviation line
  SHORT_DESC     brand + series + MPN + product + top attributes
  LONG_DESC1     full spec sentence, "Additional Information:" tail
"""
import re

from .knowledge import INV_ABBR
from .common import normalize_ws, to_sentence


def _abbrev(text):
    """Apply the invoice abbreviation dictionary to free text."""
    low = " " + text.lower().strip() + " "
    for word, code in INV_ABBR.items():
        low = re.sub(r"\b" + re.escape(word) + r"\b", " " + code + " ", low)
    return normalize_ws(low.replace(" - ", " ")).strip()


def mobile_desc(manufacturer, brand, product, series, mpn, mounting, desc):
    pieces = []
    if manufacturer:
        pieces.append(manufacturer)
    if brand:
        pieces.append(brand)
    if product:
        pieces.append(product)
    if series:
        pieces.append(series)
    if mpn:
        pieces.append(mpn)
    if mounting:
        pieces.append(mounting)
    s = ", ".join(pieces)[:85]
    return s


def invoice_desc(desc, attrs, product, mpn):
    """Build a <=40 char all-caps invoice line."""
    av = {}
    for lab, val, uom in attrs:
        av[lab] = (val, uom)
    toks = []
    p = _abbrev(product or "")
    if p:
        toks.append(p.upper())
    mount = av.get("Mounting Type", ("", ""))[0]
    if mount:
        toks.append(mount.upper())
    cycles = av.get("Number of Wash Cycles", ("", ""))[0]
    if cycles:
        toks.append(str(cycles))
    mat = av.get("Material", ("", ""))[0]
    if mat:
        m = {"Stainless Steel": "SST", "Steel": "STL", "Aluminum": "ALUM",
             "PVC": "PVC", "Composite": "COMP", "Vinyl": "VNL",
             "Brass": "BRS", "Copper": "CPR", "Wood": "WD"}.get(mat)
        if m:
            toks.append(m)
    v = av.get("Voltage Rating", ("", ""))[0]
    a = av.get("Amperage Rating", ("", ""))[0]
    if v:
        toks.append("%sV" % v)
    if a:
        toks.append("%sA" % a)
    snd = av.get("Sound Level", ("", ""))[0]
    if snd:
        toks.append("%sdBA" % snd)
    s = " ".join(toks)
    return s[:40]


def _attr_text(attrs, *labels):
    """Join labeled attribute values into a sentence fragment."""
    out = []
    for lab, val, uom in attrs:
        if not val:
            continue
        if lab in labels:
            out.append("%s %s" % (val, uom) if uom else str(val))
    return ", ".join(out)


def short_desc(desc, attrs, brand, series, mpn, product, mounting):
    parts = []
    if brand:
        parts.append(brand)
    if series:
        parts.append(series)
    if mpn:
        parts.append(mpn)
    if product:
        parts.append(product)

    details = []
    seen_labels = set()
    def g(*labels):
        for lab, val, uom in attrs:
            if not val or lab in seen_labels:
                continue
            if lab in labels:
                seen_labels.add(lab)
    g("Series")
    for lab, val, uom in attrs:
        if not val or lab in seen_labels:
            continue
        if lab in ("Series", "Additional Information", "Model"):
            continue
        if lab in ("Material", "Color", "Finish"):
            if str(val) not in details:
                details.append(str(val))
            seen_labels.add(lab)
        else:
            details.append("%s %s" % (lab.replace(" Rating", ""), val) +
                           (" %s" % uom if uom else ""))
    s = " ".join(parts)
    if details:
        s = s + " With " + ", ".join(details)
    return s[:200]


def long_desc1(desc, attrs, brand, product, series, mpn):
    parts = []
    if brand:
        parts.append(brand)
    if product:
        parts.append(product)
    if series:
        parts.append(series)

    av = {}
    for lab, val, uom in attrs:
        av[lab] = (val, uom)

    spec = []
    for lab, val, uom in attrs:
        if lab in ("Series", "Additional Information"):
            continue
        if lab == "Number of Wash Cycles":
            spec.append("%s Wash Cycles" % val)
        elif uom:
            spec.append("%s %s" % (val, uom))
        else:
            spec.append(str(val))
    s = " ".join(parts)
    if spec:
        s += ", " + ", ".join(spec)
    return s[:500]


def retail_desc(desc, attrs, brand, product, mpn):
    out = [str(product or "Product") + " from " + (brand or "the manufacturer")]
    if mpn:
        out.append("model %s" % mpn)
    out.append(".")
    return " ".join(out)


def marketing_description(desc, attrs, brand, product):
    lines = []
    if brand:
        lines.append("%s-brand %s solution built for the worksite." %
                     (brand, (product or "product").lower()))
    if attrs:
        top = [str(v) + (" " + u if u else "") for _, v, u in attrs[:4]]
        if top:
            lines.append("Featuring " + ", ".join(top) + ".")
    lines.append("Engineered for reliable, consistent performance.")
    return " ".join(lines)


def item_features(attrs, maxn=20):
    """Turn attributes + heuristics into feature bullets."""
    feats = []
    for lab, val, uom in attrs:
        if not val:
            continue
        feat = lab.replace(" Rating", "")
        if uom and uom not in ("", "in"):
            feat += " %s" % uom
        feats.append("%s: %s" % (feat, val))
    if len(feats) < maxn:
        feats += ["Manufacturer warranty applies", "Professional-grade build",
                  "Compatible with standard mounting"] * ((maxn - len(feats)))
    return feats[:maxn]


def additional_information(desc, attrs):
    """Build the 'Additional Information:' tail for LONG_DESC1."""
    extra = []
    low = desc.lower()
    for token in ["delay start", "fold tine", "kid^R", "leak detection",
                  "sani rinse", "sensor cycle", "triple wash", "normal cycle",
                  "quick wash", "moisture repellent", "heating element",
                  "eco"]:
        if token in low:
            extra.append(token.title())
    return extra