"""Exploratory analysis of the UniHack sample input CSV."""
import csv
import collections
import os
import re
from pathlib import Path

INPUT = str(Path(__file__).resolve().parent.parent / "data" / "input" / "Unihack_ Sample Dataset - Input.csv")

PLACEHOLDERS = {"-- unbranded --", "-- no unilog brand --", "-- no dib brand --", "-", "", "nan", "none"}


def clean(v):
    return "" if v is None else str(v).strip()


def is_placeholder(v):
    return v.lower() in PLACEHOLDERS or v.lower().startswith("--")


rows = []
with open(INPUT, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({k: clean(v) for k, v in r.items()})

print(f"Total rows: {len(rows)}")

# Placeholder stats
for col in ["E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf"]:
    missing = sum(1 for r in rows if is_placeholder(r[col]))
    print(f"{col}: {missing}/{len(rows)} are placeholders/empty ({missing/len(rows)*100:.1f}%)")

# Distinct Part_Manuf values
manuf = collections.Counter(r["Part_Manuf"] for r in rows)
print(f"\nDistinct Part_Manuf values: {len(manuf)}")
for name, cnt in manuf.most_common(40):
    print(f"  {cnt:4d}  {name}")

# Distinct E1_Brand
brands = collections.Counter(r["E1_Brand"] for r in rows)
print(f"\nDistinct E1_Brand values: {len(brands)}")
for name, cnt in brands.most_common(40):
    print(f"  {cnt:4d}  {name}")

# Non-empty Unilog/DIB brands
uni_brands = collections.Counter(r["Unilog_Brand"] for r in rows if not is_placeholder(r["Unilog_Brand"]))
dib_brands = collections.Counter(r["DIB_Brand"] for r in rows if not is_placeholder(r["DIB_Brand"]))
print(f"\nNon-placeholder Unilog_Brand values ({sum(uni_brands.values())} rows):")
for name, cnt in uni_brands.most_common(40):
    print(f"  {cnt:4d}  {name}")
print(f"\nNon-placeholder DIB_Brand values ({sum(dib_brands.values())} rows):")
for name, cnt in dib_brands.most_common(40):
    print(f"  {cnt:4d}  {name}")

# Brand-like tokens inside Part_Desc (search for known patterns)
desc_brand_hits = collections.Counter()
mapping = {
    "milw": "Milwaukee", "dewalt": "DEWALT", "makita": "Makita", "diablo": "Diablo",
    "kreg": "Kreg", "festool": "Festool", "satco": "Satco", "philips": "Philips",
    "kichler": "Kichler", "leviton": "Leviton", "southwire": "Southwire", "senco": "Senco",
    "irwin": "Irwin", "prebena": "Prebena", "grizzly": "Grizzly", "whiteside": "Whiteside",
    "hirsch": "Hirsch", "velux": "Velux", "provia": "ProVia", "bosch": "Bosch",
    "3m": "3M", "abranet": "Mirka", "hiolit": "Mirka", "meguiar": "Meguiar",
    "speed queen": "Speed Queen", "frigidaire": "Frigidaire", "kitchen aid": "KitchenAid",
    "café": "Cafe", "cafe": "Cafe", "lg ": "LG", "beko": "Beko", "element": "Element",
    "whirlpool": "Whirlpool", "ge ": "GE",
}
tokens = ["Milw", "Dewalt", "Makita", "Diablo", "Kreg", "Festool", "Satco", "Philips", "Kichler",
          "Leviton", "Southwire", "Senco", "Irwin", "Prebena", "Grizzly", "Whiteside", "Velux",
          "ProVia", "Bosch", "3M", "Abranet", "HIOLIT", "Speed Queen", "Frigidaire", "Kitchen Aid",
          "Caf", "Whirlpool", "Beko", "Element", "Feit", "Wiz", "Dremel", "GT-Lite", "Carlon",
          "Prime", "Lutron", "Police", "Schumacher", "Nicholson", "Vessel", "Wera", "Mafell",
          "Paslode", "Hunter", "Senco", "Makita", "Gilmour", "Voyager", "Xidane", "Cassius",
          "Anisten", "Slyde", "Finyline", "Trex", "Azek", "Hardie", "Huber", "Zip", "Easi-Lite",
          "Firelite", "Certainteed", "Huber", "Smart", "ProVia", "45100"]
for r in rows:
    d = r["Part_Desc"]
    dl = d.lower()
    for t in tokens:
        if t.lower() in dl:
            desc_brand_hits[t] += 1
print("\nBrand tokens found in Part_Desc (top 40):")
for t, c in desc_brand_hits.most_common(40):
    print(f"  {c:4d}  {t}")

# Category sniffing - look for key product keywords
cats = collections.Counter()
keywords = {
    "Abrasive/disc": ["sanding", "abranet", "hiolit", "stikit", "grit", "disc", "belt", "grinding", "sponge", "cut-off", "cut off", "cutoff", "dozer", "flap", "finish disc", "sheet"],
    "Power tool": ["drill", "saw", "grinder", "hammer", "impact", "driver", "nailer", "stapler", "router", "sander", "blower", "trimmer", "hedge", "vacuum", "laser", "screwdriver", "ratchet", "cutter", "planer", "jointer", "shaper", "drill press", "charger", "battery", "grease gun", "miter"],
    "Tool accessory": ["bit", "blade", "wrench", "socket", "chuck", "holster", "organizer", "pencil", "knife", "adapter", "fence", "insert", "bushing", "mount", "clip", "holder"],
    "Appliance": ["dishwasher", "dryer", "washer", "fridge", "freezer", "range", "stove", "oven", "microwave", "cooktop", "coffee", "espresso", "toaster", "beverage", "refrigerator", "laundry"],
    "Electrical": ["outlet", "switch", "box", "cover", "wire", "cord", "cable", "timer", "dimmer", "plug", "connector", "battery", "charger", "load", "breaker", "entrance"],  # fixed, remove battery/charger dupes later
    "Lighting": ["light", "lamp", "bulb", "downlight", "fixture", "pendant", "chandelier", "ceiling", "sconce", "wrap", "panel", "highbay", "flood", "tape light", "lantern", "led", "halogen", "incan", "sodium"],
    "Decking/fence": ["deck", "rail", "railing", "baluster", "post", "fascia", "trestle", "decking", "gate", "stair"],
    "Building material": ["drywall", "osb", "sheathing", "rainscreen", "siding", "lumber", "mortar", "cement", "roof", "metal", "shingle", "ice", "tape", "thresh", "beams", "plywood", "panel", "osb"],
    "Fastener": ["nail", "staple", "screw", "tag", "fastener"],
    "Safety": ["glove", "glasses", "eyewear", "hearing", "extinguisher", "alarm", "goggle", "protection", "headlight"],
    "Window/door": ["window", "door", "skylight", "skylt", "hopper", "patio", "slider", "casement", "bay"],
    "Plumbing/pipe": ["pipe", "fitting", "hose", "coupling", "valve", "flange", "nipple", "tee", "elbow"],
    "Hand tool": ["screwdriver", "wrench", "plier", "hammer", "level", "square", "tape", "measur", "knife", "file", "snip", "chisel", "mall", "caliper", "chalk", "string", "line"],
}
for r in rows:
    d = r["Part_Desc"].lower()
    hit = []
    for cat, kws in keywords.items():
        for k in kws:
            if k in d:
                hit.append(cat)
                break
    cats[tuple(sorted(set(hit)))] += 1

print("\nCategory keyword clusters found:")
for k, v in cats.most_common(30):
    print(f"  {v:4d}  {'+'.join(k) if k else '(none)'}")