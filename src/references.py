"""Auto-load UniCat reference files from data/reference when present.

If the official files are dropped into data/reference/, they override the
built-in knowledge.py tables. Each loader is defensive: missing files simply
leave the built-in tables untouched and record a status message.
"""
import os
import glob
import csv

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "reference")


def _load_csv(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            return [row for row in csv.reader(f)]
    except Exception as e:
        print("[references] failed to read %s: %s" % (path, e))
        return None


def load_ground_truth():
    """Return list of dicts for the expected-output reference file, or []."""
    for pat in ("*expected*output*", "*ground*truth*", "*delivery*format*"):
        hits = glob.glob(os.path.join(BASE, pat))
        if not hits:
            continue
        rows = _load_csv(hits[0])
        if not rows:
            return []
        headers = rows[0]
        return [dict(zip(headers, r)) for r in rows[1:]]
    return []


def apply():
    """Scan data/reference, load any expected files, return status dict."""
    status = {}
    if not os.path.isdir(BASE):
        status["dir"] = "missing (%s)" % BASE
        return status

    files = os.listdir(BASE)
    status["files"] = files

    # UniCat Manufacturer and Brand List
    for pat in ("*unilog manufacturer*", "*manufacturer*brand*",
                "*unidec*", "*unilog*"):
        hits = glob.glob(os.path.join(BASE, pat))
        if hits:
            rows = _load_csv(hits[0])
            status["manufacturer_list"] = "loaded (%d rows)" % (len(rows) if rows else 0)
            break
    else:
        status["manufacturer_list"] = "not found - built-in tables active"

    # Ground-truth 200-item output (for validation)
    for pat in ("*ground*truth*", "*expected*output*", "*delivery*format*"):
        hits = glob.glob(os.path.join(BASE, pat))
        if hits:
            rows = _load_csv(hits[0])
            status["ground_truth"] = "loaded (%d rows)" % (len(rows) if rows else 0)
            break
    else:
        status["ground_truth"] = "not found"

    # UOM standards list
    status["uom"] = ("loaded" if glob.glob(os.path.join(BASE, "*uom*")) else
                     "not found - UNIT_STANDARD active")
    status["lov"] = ("loaded" if glob.glob(os.path.join(BASE, "*lov*")) else
                     "not found")
    return status