"""Print full Part_Manuf list + sample rows per broad category."""
import csv, collections, re

INPUT = r"C:\Users\riyam\OneDrive\Desktop\InduSpecSmith_AI\data\input\Unihack_ Sample Dataset - Input.csv"
PLACE = {"-- unbranded --", "-- no unilog brand --", "-- no dib brand --", "-", "", "nan", "none"}


def clean(v):
    return "" if v is None else str(v).strip()


def is_ph(v):
    return v.lower() in PLACE or v.lower().startswith("--")


rows = []
with open(INPUT, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({k: clean(v) for k, v in r.items()})

manuf = collections.Counter(r["Part_Manuf"] for r in rows)
print("== ALL Part_Manuf values (%d) ==" % len(manuf))
for name, cnt in manuf.most_common():
    print("%4d  %s" % (cnt, name))

# Sample rows grouped by rough category keyword
print("\n== SAMPLES by keyword ==")
kw_groups = {
    "disc/blade": r"cut[-\s]?off|grinding|grind|diamond|blade|saw blade|metal cut|masonry",
    "abrasive": r"abranet|hiolit|stikit|sanding|sponge|grit|dozer|hole",
    "power_tool": r"drill|impact|hammer|nailer|stapler|router|sander|grinder|saw$|circ|laser|charger|battery|blower|trimmer|vacuum|grease gun|ratchet|die grinder",
    "appliance": r"dishwasher|dryer|washer|fridge|freezer|range|microwave|cooktop|coffee|espresso|toaster|beverage",
    "lighting": r"light|wall lt|pendant|chandelier|ceiling|bulb|wrap|downlight|panel|lantern|sconce|led|incan",
    "electrical": r"outlet|switch|box cover|oct box|square box|wire|cord|timer|dimmer|plug|load|entrance|cat5|gfi|gfci",
    "decking": r"decking|rail|baluster|post|fascia|fence|gate|lineage|select|enhance",
    "bldg": r"drywall|osb|sheathing|siding|rainscreen|mortar|roof|metal|shingle|ice|thresh|pan|hardie|smart",
    "fastener": r"nail|staple|senco|prebena|brad",
    "hand_tool": r"screwdriver|wrench|knife|file|snip|square|chalk|string|line|pencil|bit|socket|holster|organizer|ratchet|level|caliper",
    "safety": r"glove|glasses|eyewear|hearing|extinguisher|alarm|goggle|protection",
    "window/door": r"window|door|skyl|hopper|patio|slider",
    "misc": r"tape|mason line|hanger|threshold|grill|packout|mud|battery",
}
seen = set()
for label, pat in kw_groups.items():
    rx = re.compile(pat, re.I)
    print(f"\n--- {label} ---")
    n = 0
    for r in rows:
        if n >= 12:
            break
        if rx.search(r["Part_Desc"]):
            print("  [%s] mfg=%s | e1=%s | dinb=%s" % (r["Mfg_Part_Num"], r["Part_Manuf"], r["E1_Brand"], r["DIB_Brand"]))
            print("      desc: %s" % r["Part_Desc"])
            n += 1