"""Curated knowledge base: manufacturers, brands, taxonomy, units, colors.

Built-in tables approximate UniCat canonical values so the pipeline runs
offline. Every table here is overridable by src/references.py when the official
reference files (UniCat_Manufacturer_and_Brand_List.xlsx etc.) are provided.
"""
import re

# ---------------------------------------------------------------------------
# Placeholders (kept in sync with common.py)
# ---------------------------------------------------------------------------
PLACEHOLDER_PATTERN = re.compile(r"^--.*--$", re.I)

# ---------------------------------------------------------------------------
# Brand token -> canonical BRAND_NAME (display form used in output).
# Symbols follow the sample output convention (FRIGIDAIRE®, Whirlpool®).
# ---------------------------------------------------------------------------
BRAND_ALIASES = {
    # tokens appearing in Part_Desc or DIB_Brand
    "milw": "MILWAUKEE®",
    "milwaukee": "MILWAUKEE®",
    "dewalt": "DEWALT",
    "de walt": "DEWALT",
    "makita": "Makita",
    "diablo": "Diablo",
    "freud": "FREUD",
    "3m": "3M",
    "abranet": "Mirka®",
    "hiolit": "Mirka®",
    "iridium": "Mirka®",
    "mirka": "Mirka®",
    "stikit": "3M",
    "cubitron": "3M",
    "kichler": "KICHLER",
    "satco": "Satco",
    "philips": "Philips",
    "wiz": "Wiz",
    "leviton": "Leviton",
    "southwire": "SOUTHWIRE",
    "prime": "Prime",
    "carlon": "Carlon",
    "square d": "Square D",
    "dremel": "Dremel",
    "kreg": "Kreg",
    "festool": "Festool",
    "senco": "SENCO",
    "paslode": "Paslode",
    "prebena": "Prebena",
    "irwin": "Irwin",
    "whiteside": "Whiteside",
    "vessel": "VESSEL",
    "wera": "Wera",
    "grizzly": "Grizzly",
    "bosch": "Bosch",
    "robert bosch": "Bosch",
    "mafell": "Mafell",
    "woodpeckers": "WOODPECKERS",
    "oliver": "Oliver",
    "jet": "Jet",
    "king canada": "King Canada",
    "hunter": "Hunter Fan",
    "gilmour": "Gilmour",
    "velux": "VELUX",
    "provia": "ProVia",
    "hardie": "James Hardie",
    "jameshardie": "James Hardie",
    "lp smartside": "LP® SmartSide®",
    "smartside": "LP® SmartSide®",
    "huber": "Huber Engineered Woods",
    "zip": "Huber Engineered Woods",
    "trex": "Trex",
    "timbertech": "TimberTech",
    "azek": "Azek",
    "finyline": "Finyline",
    "dsi westbury": "DSI Westbury",
    "andersen": "Andersen",
    "first alert": "FIRST ALERT",
    "brk": "BRK",
    "schumacher": "Schumacher",
    "stealthmounts": "StealthMounts",
    "police security": "Police Security",
    "police": "Police Security",
    "feit": "Feit Electric",
    "feit electric": "Feit Electric",
    "gt-lite": "GT-Lite",
    "nicholson": "Nicholson",
    "lutron": "Lutron",
    "streamlight": "Streamlight",
    "edge": "EDGE Eyewear",
    "maxsa": "Maxsa",
    "sabre": "Sabre",
    "radians": "Radians",
    "protecto": "Protecto Wrap",
    "premier": "Premier Metals",
    "certainteed": "CertainTeed",
    "heritage": "Heritage",
    "legacy": "Legacy",
    "element": "Element",
    "beko": "Beko",
    "caf": "Café",
    "kitchen aid": "KitchenAid",
    "kitchenaid": "KitchenAid",
    "whirlpool": "Whirlpool®",
    "frigidaire": "FRIGIDAIRE®",
    "speed queen": "Speed Queen",
    "lg": "LG",
    "haier": "Haier",
}

# Well-recognized brand display forms keyed by DIB_Brand raw value
DIB_BRAND_FIX = {
    "MILWAUKEE": "MILWAUKEE®",
    "Milwaukee": "MILWAUKEE®",
    "DEWALT": "DEWALT",
    "Philips": "Philips",
    "PHILIPS": "Philips",
    "Diablo": "Diablo",
    "Leviton": "Leviton",
    "Satco": "Satco",
    "Southwire": "SOUTHWIRE",
    "Prime": "Prime",
    "Wiz": "Wiz",
    "Feit Electric": "Feit Electric",
    "Square D": "Square D",
    "Dremel": "Dremel",
    "3M": "3M",
    "Schumacher": "Schumacher",
    "StealthMounts": "StealthMounts",
    "Carlon": "Carlon",
    "GT-Lite": "GT-Lite",
    "Police Security": "Police Security",
    "Hunter": "Hunter Fan",
    "First Alert": "FIRST ALERT",
    "BRK": "BRK",
    "Nicholson": "Nicholson",
    "Irwin": "Irwin",
    "SENCO": "SENCO",
}

# ---------------------------------------------------------------------------
# Manufacturer base table.
# Key: the exact Part_Manuf string. Value: (manufacturer_name, default_brand)
# manufacturer_name follows UniCat-style legal naming where known.
# ---------------------------------------------------------------------------
MANUFACTURERS = {
    "Phillips Lighting (5831)": ("Signify North America Corporation", "Philips"),
    "Milwaukee Accessory (4031)": ("Milwaukee Electric Tool Corporation", "MILWAUKEE®"),
    "Boise Cascade Building Materials (BOICA)": ("Boise Cascade Company", ""),
    "Appliance Dealers Cooperative (APPDE)": ("Appliance Dealers Cooperative (APPDE)", ""),
    "Kichler Lighting (KICLI)": ("Kichler Lighting LLC", "KICHLER"),
    "Parksite (6151)": ("Parksite Inc", ""),
    "Black & Decker/dewlt (2585)": ("Stanley Black & Decker Inc", "DEWALT"),
    "Freud Inc (2435)": ("Freud America Inc", "FREUD"),
    "U S Lumber (3073)": ("U.S. Lumber Group", ""),
    "Satco Prod Inc (5573)": ("Satco Products Inc", "Satco"),
    "Makita Usa Inc (5142)": ("Makita U.S.A. Inc.", "Makita"),
    "Southwire/g Turner (6603)": ("Southwire Company LLC", "SOUTHWIRE"),
    "Leviton Mfg Co (4927)": ("Leviton Manufacturing Co Inc", "Leviton"),
    "Festool USA (FESTO)": ("Festool USA", "Festool"),
    "Tech Gear 5.7 Inc (TECGE)": ("Tech Gear 5.7 Inc", ""),
    "Kreg Tool Company (KRETO)": ("Kreg Tool Company", "Kreg"),
    "Edge Eyewear Inc (EDGSA)": ("Edge Eyewear Inc", "EDGE Eyewear"),
    "U S Tape Company (6694)": ("U.S. Tape Company", ""),
    "Mirka Abrasives Inc (MIRUS)": ("Mirka USA Inc", "Mirka®"),
    "Palmer Donavin Mfg Company (PALDO)": ("Palmer Donavin Manufacturing Co", ""),
    "Hunter Fan Co (4381)": ("Hunter Fan Company", "Hunter Fan"),
    "Premier Metals (PREME)": ("Premier Metals Inc", "Premier Metals"),
    "Jam Industrial Supply LLC (JAMIN)": ("Jam Industrial Supply LLC", ""),
    "Vessel Tools USA Inc (VESTO)": ("Vessel Tools USA Inc", "VESSEL"),
    "Oliver Machinery Company (OLIMA)": ("Oliver Machinery Company", "Oliver"),
    "Prime Wire & Cable (3562)": ("Prime Wire & Cable Inc", "Prime"),
    "Bow Products (BOWPR)": ("Bow Products", ""),
    "Saw Stop LLC (SAWST)": ("SawStop LLC", "SawStop"),
    "Rees Cast Stone Company (REECA)": ("Rees Cast Stone Company Inc", ""),
    "United Window & Door Manufacturing (UNIWI)": ("United Window & Door Manufacturing LLC", "United Window & Door"),
    "Westwood Lumber Sales (WESLU)": ("Westwood Lumber Sales", ""),
    "Woodpeckers Inc (WOODP)": ("Woodpeckers Inc", "WOODPECKERS"),
    "Robt Bosch Tool Corp (6564)": ("Robert Bosch Tool Corporation", "Bosch"),
    "Velux America Inc (VELAM)": ("VELUX America Inc", "VELUX"),
    "Fenton Bros Electric Inc (FENBR)": ("Fenton Bros Electric Inc", ""),
    "Square D Con Prod Dv (6825)": ("Schneider Electric USA Inc", "Square D"),
    "Whiteside Machine & Repair Co (WHIMA)": ("Whiteside Machine & Repair Co", "Whiteside"),
    "CMT USA Inc (CMTUS)": ("CMT USA Inc", "CMT"),
    "JPW Industries (JPWIN)": ("JPW Industries Inc", "Jet"),
    "Wera Tools NA Inc (WERTO)": ("Wera Tools North America Inc", "Wera"),
    "ProVia (PRODO)": ("ProVia", "ProVia"),
    "Certainteed Gypsum (2765)": ("CertainTeed Gypsum Inc", "CertainTeed"),
    "Hager Hinge Co (4189)": ("Hager Hinge Company", "HAGER"),
    "Cooper Lighting (7638)": ("Cooper Lighting Solutions", ""),
    "Feit Electric (3468)": ("Feit Electric Company", "Feit Electric"),
    "ACG Brands (1154)": ("ACG Brands", ""),
    "Senco Products Inc (4650)": ("SENCO Products Inc", "SENCO"),
    "National Nail Corp (7439)": ("National Nail Corporation", ""),
    "Prebena (PREBE)": ("Prebena Inc", "Prebena"),
    "Marshalltown Trowel (5155)": ("Marshalltown Company", ""),
    "Ohio Firewatch Protection Inc (HOLFS)": ("Ohio Firewatch Protection Inc", ""),
    "First Alert - B R K Brands (2754)": ("BRK Brands Inc", "FIRST ALERT"),
    "Malco Prod (2370)": ("Malco Products Inc", "Malco"),
    "King Canada Inc (KINCA)": ("King Canada Inc", "King Canada"),
    "Woodstock Intl (3658)": ("Woodstock International Inc", "Grizzly"),
    "3 M Co (5293)": ("3M Company", "3M"),
    "Emseal Joint Systems Ltd (EMSJO)": ("EMS-CHEMIE (North America) Inc", ""),
    "V & V Appliance Parts Inc (VVAPP)": ("V & V Appliance Parts Inc", ""),
    "A J Manufacturing Inc (AJMAN)": ("A.J. Manufacturing Inc", "AJM"),
    "Huber Eng Wood LLC (3158)": ("Huber Engineered Woods LLC", "Huber Engineered Woods"),
    "MillerTech Energy Solutions (MILTE)": ("MillerTech Energy Solutions", ""),
    "Metalmark Industrial Inc (METIN)": ("Metalmark Industrial Inc", "StealthMounts"),
    "Thomas & Betts (7405)": ("ABB Installation Products Inc", "Carlon"),
    "Cooper Wiring Devices (3560)": ("Eaton Corporation", ""),
    "Lithonia Lighting (2776)": ("Lithonia Lighting", ""),
    "Keystone (5702)": ("Keystone Technologies", "GT-Lite"),
    "Maxsa Innovations (MAXIN)": ("Maxsa Innovations", ""),
    "Streamlight (7277)": ("Streamlight Inc", "Streamlight"),
    "Police Security (9470)": ("Police Security LLC", "Police Security"),
    "Woods Wire Southwire (7579)": ("Southwire Company LLC", "SOUTHWIRE"),
    "Sabre (9195)": ("Sabre", "Sabre"),
    "Radians (7363)": ("Radians Inc", "Radians"),
    "Amana Tool Corp (AMATO)": ("Amana Tool Corporation", "Amana Tool"),
    "Irwin Industrial Tools (5863)": ("Irwin Industrial Tool Company", "Irwin"),
    "J&G Machinery (JGMAC)": ("J&G Machinery Inc", ""),
}

# Appliance parent companies for APPDE rows (brand -> manufacturer name)
APPLIANCE_PARENT = {
    "FRIGIDAIRE®": "Electrolux Home Products Inc",
    "GE": "GE Appliances (Haier)",
    "LG": "LG Electronics USA Inc",
    "Whirlpool®": "Whirlpool Corporation",
    "KitchenAid": "Whirlpool Corporation",
    "Speed Queen": "Alliance Laundry Systems LLC",
    "Café": "GE Appliances (Haier)",
    "Beko": "Beko USA",
    "Element": "Element Electronics",
    "Maytag": "Whirlpool Corporation",
}

E1_BRAND_FIX = {
    "TREX": "Trex",
    "TIMBERTECH": "TimberTech",
    "United Window & Door": "United Window & Door",
    "LP SMARTSIDE": "LP® SmartSide®",
    "DSI Westbury": "DSI Westbury",
    "PROVIA": "ProVia",
    "HAGER": "HAGER",
    "JAMESHARDIE": "James Hardie",
    "AJM": "AJM",
    "ANDERSEN": "Andersen",
    "CENTURY COMPONENTS": "Century Components",
    "COMMODITY - UNBRANDED": "",
}

# ---------------------------------------------------------------------------
# Unit / UOM standard (house style). We normalize display forms to these.
# ---------------------------------------------------------------------------
UNIT_STANDARD = {
    "in": "in", "inch": "in", "inches": "in", "in.": "in", '"': "in",
    "ft": "ft", "foot": "ft", "feet": "ft", "'": "ft",
    "mm": "mm", "cm": "cm", "m": "m",
    "v": "V", "volt": "V", "volts": "V",
    "a": "A", "amp": "A", "amps": "A", "ampere": "A",
    "w": "W", "watt": "W", "watts": "W",
    "hp": "HP",
    "dba": "dBA",
    "kwhr": "kW-hr", "kwh": "kW-hr", "kw-hr": "kW-hr", "kwhr": "kW-hr",
    "hz": "Hz",
    "psi": "psi",
    "oz": "oz", "lb": "lb", "lbs": "lb", "lb.": "lb",
    "l": "L", "gal": "gal", "gallon": "gal",
    "cf": "CF", "cu ft": "CF", "cu. ft.": "CF",
    "sq ft": "sq ft",
    "rpm": "RPM",
    "mn": "MN",
    "cfm": "CFM",
    "w": "W",
    "ft-lb": "ft-lb",
    "nm": "N m",
    "min": "min", "hr": "hr",
    "": "",
}

# ---------------------------------------------------------------------------
# Fraction table: decimal (float) -> inch fraction string.
# 1/64 resolution, matching the Decimal_Fraction reference.
# ---------------------------------------------------------------------------
FRACTIONS = {}
for num in range(1, 64):
    val = num / 64.0
    reduced_num = num
    reduced_den = 64
    for g in (32, 16, 8, 4, 2):
        if reduced_num % g == 0 and reduced_den % g == 0:
            reduced_num //= g
            reduced_den //= g
            break
    FRACTIONS[val] = "%d/%d" % (reduced_num, reduced_den)
# common reductions (1/2, 1/4, ...) already covered; ensure slashes for halves/quarters/eighths handle correctly
FRACTIONS[0.5] = "1/2"
FRACTIONS[0.75] = "3/4"
# leave leading zero off
FRACTIONS[0.0] = "0"


def decimal_to_fraction(value):
    """Convert a decimal to its exact 1/64 inch fraction string if representable."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    nearest = round(v * 64) / 64.0
    if abs(nearest - v) < 1e-9 and nearest in FRACTIONS:
        return FRACTIONS[nearest]
    return None


def format_inch_number(num_str):
    """Return 'W-N/D' style for mixed numbers, fraction for <1, integer otherwise."""
    try:
        v = float(num_str)
    except (TypeError, ValueError):
        return num_str
    sign = "-" if v < 0 else ""
    v = abs(v)
    whole = int(v)
    frac = v - whole
    if frac == 0:
        return "%s%d" % (sign, whole)
    fs = decimal_to_fraction(frac)
    if fs is None:
        # no exact 1/64 fraction -> keep decimal, trimmed
        txt = ("%.4f" % v).rstrip("0").rstrip(".")
        return "%s%s" % (sign, txt)
    if whole == 0:
        return "%s%s" % (sign, fs)
    return "%s%d-%s" % (sign, whole, fs)


# ---------------------------------------------------------------------------
# Colors / finishes normalizer (code -> full word)
# ---------------------------------------------------------------------------
COLOR_CODES = {
    "SS": "Stainless Steel", "SST": "Stainless Steel", "BSS": "Black Stainless Steel",
    "WH": "White", "Wh": "White", "BK": "Black", "Bk": "Black", "BO": "Black",
    "BLK": "Black", "TBK": "Black", "MB": "Matte Black", "PMB": "Matte Black",
    "CPZ": "Chrome Packaged", "CH": "Chrome", "BN": "Bronze", "BRN": "Bronze",
    "DBK": "Dark Bronze", "BR": "Brown", "BNZ": "Bronze", "NI": "Nickel",
    "AVI": "Venetian Bronze", "BSL": "Brushed Steel", "BKCLR": "Black/Clear",
    "DG": "Dark Gray", "SL": "Slate", "JPN": "Juniper", "BDG": "Biscotti",
    "CLR": "Clear", "CL": "Clear", "ALM": "Almond", "CS": "Coastline",
    "EW": "English Walnut", "MH": "Mahogany", "WT": "Weathered Teak",
    "AW": "American Walnut", "CG": "Castle Gate", "FW": "French White Oak",
    "BS": "Brownstone", "SG": "Slate Gray", "GS": "Gamma Smoke",
    "OC": "Oil Rubbed Bronze", "1/2": "", "X": "", "A": "", "G": "",
}
COLOR_WORDS = {
    "black": "Black", "white": "White", "silver": "Silver", "gray": "Gray",
    "grey": "Gray", "brushed": "Brushed", "matte black": "Matte Black",
    "stainless steel": "Stainless Steel", "bronze": "Bronze", "nickel": "Nickel",
    "chrome": "Chrome", "charcoal": "Charcoal", "coastline": "Coastline",
    "slate": "Slate Gray", "brown": "Brown", "mahogany": "Mahogany",
    "juniper": "Juniper", "matador red": "Matador Red",
}

# ---------------------------------------------------------------------------
# Suffix tokens that indicate color after a size/type (appliance-heavy data)
# ---------------------------------------------------------------------------
FINISH_TOKENS = ["SS", "SST", "BSS", "WH", "BK", "BO", "BLK", "MB", "CPZ",
                 "CH", "BN", "BRN", "DBK", "NI", "AVI", "BSL", "DG", "SL",
                 "JPN", "CLR", "ALM", "OC", "X", "BG", "PG", "RS3", "RD3",
                 "RW3", "PD3", "PW3", "D3", "N1", "M1"]

# ---------------------------------------------------------------------------
# Packaging / quantity patterns
# ---------------------------------------------------------------------------
PACK_PATTERNS = [
    (r"(\d+)\s*(?:pc|pc\.|pcs)\b", "pc"),
    (r"(\d+)\s*ct\b", "ct"),
    (r"(\d+)\s*BL\b", "bl"),
    (r"(\d+)\s*PK\b", "pk"),
    (r"(\d+)\s*pack\b", "pk"),
    (r"(\d+)\s*ea(?:ch)?\b", "ea"),
]

DIMENSION_TOKEN = re.compile(
    r"(\d+[\w./-]*|\d+-\d+/\d+|\.\d+)\s*"
    r"[xX*]\s*"
    r"(\d+[\w./-]*|\d+-\d+/\d+|\.\d+)"
)

# Abbreviations for INVOICE_DESC generation
INV_ABBR = {
    "dishwasher": "DISHWASHER", "dryer": "DRYER", "washer": "WASHER",
    "stainless steel": "SST", "stainless": "SST",
    "with": "W/", "and": "&", "black": "BLK", "white": "WHT",
    "electric": "ELECT", "gas": "", "display": "DISP", "mounting": "MTG",
    "mount": "MTG", "cycle": "CYCL", "filter": "FLTR", "cartridge": "CTRG",
    "grinder": "GRNDR", "cut": "CUT", "off": "OFF", "disc": "DISC",
    "wheel": "WHL", "grinding": "GRIND", "masonry": "MAS", "metal": "MTL",
    "general": "GEN", "purpose": "PURP", "performance": "PERF", "plus": "+",
    "ceramic": "CER", "diamond": "DIA", "blade": "BLD", "saw": "SAW",
    "belt": "BLT", "sanding": "SNDG", "sponge": "SPNG", "film": "FILM",
    "box": "BOX", "count": "CT", "rated": "", "voltage": "", "amperage": "",
    "speed": "SPD", "king": "", "tool": "TOOL", "hammer": "HMR",
    "drill": "DRL", "impact": "IMP", "driver": "DRV", "nailer": "NLR",
    "brad": "BRAD", "finish": "FIN", "framing": "FRM", "roofing": "RFG",
    "coil": "COIL", "bare": "BARE", "kit": "KIT", "tool only": "TOOL",
    "battery": "BATT", "charger": "CHGR", "batteries": "BATT",
    "light": "LT", "lights": "LTS", "lamp": "LMP", "bulb": "BLB",
    "pendant": "PNDT", "chandelier": "CHAND", "ceiling": "CLG",
    "wall": "WALL", "sconce": "SCN", "sconce": "SCNC", "downlight": "DNLT",
    "down light": "DNLT", "wrap": "WRAP", "strip": "STRP", "panel": "PNL",
    "highbay": "HIBAY", "flood": "FLD", "motion": "MOTN", "led": "LED",
    "halogen": "HLGN", "incandescent": "INCAN", "incan": "INCAN",
    "sodium": "SOD", "fluorescent": "FLOR", "flor": "FLOR",
    "candelabra": "CAND", "cand": "CAND", "medium": "MED", "med": "MED",
    "base": "BASE", "adj": "ADJ", "adjustable": "ADJ", "socket": "SKT",
    "outlet": "OCL", "receptacle": "RCPT", "switch": "SW", "dimmer": "DIM",
    "timer": "TMR", "wire": "WIRE", "cord": "CORD", "cable": "CBL",
    "connector": "CONN", "plug": "PLUG", "gfi": "GFI", "gfci": "GFCI",
    "ground": "GND", "fault": "FLT", "circuit": "CKT", "interrupter": "INT",
    "box": "BOX", "cover": "CVR", "wallplate": "WPLT", "wallplate": "WPLT",
    "blank": "BLNK", "gang": "GNG", "decor": "DECOR", "toggle": "TGL",
    "3-way": "3WY", "single": "SGL", "duplex": "DPLX", "octagon": "OCT",
    "oct": "OCT", "square": "SQ", "rectang": "RECT", "bracket": "BRKT",
    "hanger": "HGR", "mount": "MNT", "sleeve": "SLV", "cap": "CAP",
    "post": "PST", "railing": "RLG", "rail": "RAIL", "baluster": "BALU",
    "decking": "DECK", "deck": "DECK", "fascia": "FSC", "fence": "FNC",
    "gate": "GATE", "stair": "STR", "kit": "KIT", "horizontal": "HORIZ",
    "stair": "STR", "aluminum": "ALUM", "alum": "ALUM", "black": "BLK",
    "composite": "COMP", "white": "WH", "height": "HGT", "width": "WDT",
    "depth": "DPT", "length": "LGT", "long": "LG", "large": "LRG",
    "faucet": "FCT", "sink": "SNK", "valve": "VLV", "pipe": "PIP",
    "fitting": "FTG", "hose": "HOS", "connection": "CONN", "temperature": "TEMP",
    "pressure": "PRS", "load": "LOAD", "center": "CTR", "entrance": "ENT",
    "aluminum": "ALUM", "alumi": "ALUM", "conduit": "CNDT", "cable": "CBL",
    "triplex": "TRPLX", "stranded": "STRND", "solid": "SLD", "jacket": "JKT",
    "cord": "CRD", "grip": "GRP", "strain": "STRN", "relief": "RLF",
    "knife": "KNF", "folding": "FOLD", "utility": "UTIL", "razor": "RZR",
    "retractable": "RETR", "screwdriver": "SCRDR", "screw": "SCR",
    "driver": "DRV", "setter": "STR", "phillips": "PH", "square": "SQ",
    "torx": "TX", "hex": "HX", "robertson": "RB", "straight": "STRT",
    "flat": "FLT", "slotted": "SLT", "drive": "DRV", "bit": "BIT",
    "holder": "HLDR", "impact": "IMP", "ball": "BAL", "torsion": "TRS",
    "socket adapter": "SKT ADPT", "adapter": "ADPT", "universal": "UNIV",
    "joint": "JNT", "ratchet": "RTCH", "wrench": "WRN", "set": "SET",
    "mechanics": "MECH", "sae": "SAE", "metric": "MET", "pcs": "PC",
    "pieces": "PC", "packout": "PKOUT", "toolbox": "TLOX", "drawer": "DRWR",
    "organizer": "ORG", "ruler": "RULE", "square": "SQ", "level": "LVL",
    "tape": "TPE", "measuring": "MSR", "chalk": "CHK", "reel": "REL",
    "line": "LIN", "mason": "MSN", "laying": "LYG", "string": "STRG",
    "standard": "STD", "replacement": "REPL", "spool": "SPL", "span": "SPN",
    "green": "GRN", "orange": "ORN", "yellow": "YLW", "pink": "PNK",
    "blue": "BLU", "red": "RED", "clear": "CLR", "glossy": "GLS",
    "gloss": "GL", "sheen": "SHN", "satin": "STN", "matte": "MTE",
    "flat": "FLT", "semi": "SEMI", "fire extinguisher": "EXTNGR", "lithium": "LITH",
    "extinguisher": "EXTNGR", "smoke": "SMK", "carbon monoxide": "CO",
    "alarm": "ALRM", "detector": "DET", "combination": "CMBO",
    "glove": "GLV", "gloves": "GLVS", "heated": "HTD", "work": "WRK",
    "liner": "LNR", "liners": "LNRS", "hoodie": "HDIE", "jacket": "JKT",
    "protective": "PRT", "safety": "SFY", "glasses": "GLS", "lens": "LNS",
    "lenses": "LNSS", "frame": "FRM", "polarized": "POL", "photochromic": "PHOTO",
    "hearing": "HNG", "protector": "PRTCT", "am/fm": "AM/FM", "radio": "RDO",
    "eyewear": "EYEWR", "goggle": "GGGL", "drill press": "DRL PRS",
    "table saw": "TBL SAW", "miter saw": "MITR SAW", "circular saw": "CRC SAW",
    "jig saw": "JIG SAW", "recip saw": "RECP SAW", "band saw": "BAND SAW",
    "track saw": "TRK SAW", "planer": "PLNR", "jointer": "JNTR",
    "shaper": "SHPR", "router": "RTR", "sander": "SNDR", "orbital": "ORB",
    "belt sander": "BLT SNDR", "polisher": "POLSH", "grinder": "GRNDR",
    "angle grinder": "ANG GRNDR", "die grinder": "DIE GRNDR", "cutoff": "CUTOFF",
    "cutting": "CUT", "wheel": "WHL", "blade": "BLD", "segmented": "SEGMT",
    "rim": "RIM", "tile": "TILE", "glass": "GLAS", "diamond": "DIA",
    "carbide": "CRB", "tooth": "T", "teeth": "T", "tpi": "TPI",
    "da": "", "fo": "", "ee": "", "dado": "DADO", "stack": "STK",
    "router bit": "RTR BIT", "bit": "BIT", "straight": "STRT", "spiral": "SPR",
    "upcut": "UPC", "downcut": "DNC", "flush": "FLSH", "trim": "TRM",
    "countersink": "CTSK", "plug cutter": "PLG CUT", "forstner": "FRSN",
    "drill bit": "DRL BIT", "twist": "TWST", "brad point": "BRAD PT",
    "auger": "AGR", "hole saw": "HL SAW", "hole dozer": "HL SAW",
    "magnet": "MAG", "magnetic": "MAG", "impactor": "IMP", "impact": "IMP",
    "nut driver": "NUT DRV", "screwdriver bit": "SCRDR BIT",
    "socket": "SKT", "socket": "SKT", "drive": "DRV", "point": "PT",
    "length": "LEN", "overall": "OVR", "mill": "MLL", "bastard": "BSTD",
    "file": "FILE", "flat file": "FLT FIL", "round file": "RND FIL",
    "half-round": "HALFRND", "triangular": "TRI", "rasp": "RSP",
    "handleneedle": "NDL", "needle": "NDL", "snips": "SNPS", "tin": "TIN",
    "aviation": "AVTN", "mini": "MINI", "offset": "OFST", "sheet metal": "SHT MTL",
    "metal": "MTL", "trowel": "TRWL", "float": "FLT", "margin": "MRG",
    "pointing": "PNT", "cutting": "CTNG", "duck": "DUCK", "hammer": "HMR",
    "claw": "CLW", "sledge": "SLDG", "mallet": "MLLT", "dead blow": "DDBL",
    "chisel": "CHSL", "cold": "CLD", "wood": "WD", "chisel": "CHSL",
    "pry bar": "PRY BAR", "nail bar": "NAIL BAR", "wonder bar": "WNDR BAR",
    "pencil": "PNCL", "mechanical": "MECH", "lead": "LD", "pack": "PK",
    "replacement": "REPL", "lead-color": "CLR LD", "marker": "MKR",
    "pen": "PEN", "sharpie": "SHRPY", "chalk": "CHK", "refill": "RFLL",
    "clamp": "CLMP", "bar clamp": "BAR CLMP", "spring clamp": "SPRG CLMP",
    "c-clamp": "C-CLMP", "f-clamp": "F-CLMP", "quick-grip": "QK-GRP",
    "vise": "VISE", "bench": "BEN", "grip": "GRP", "jaw": "JW",
    "pad": "PAD", "kneeling": "KNLG", "kneeler": "KNLR", "opener": "OPNR",
    "bottle": "BTL", "workstation": "WRKSTN", "creeper": "CRPR",
    "gauge": "GGE", "tire": "TIRE", "pressure": "PRS", "inflator": "INFL",
    "digital": "DIG", "analog": "ANA", "thermo": "THER", "infrared": "IR",
    "laser": "LSR", "temp": "TEMP", "gun": "GUN", "grease": "GRS",
    "zinc": "ZNC", "galv": "GLV", "galvanized": "GLV", "coated": "CTD",
    "hdg": "HDG", "ss": "SST", "brass": "BRS", "steel": "STL", "iron": "IRN",
    "stainless": "SST", "alum": "ALUM", "plastic": "PLS", "nylon": "NYL",
    "rubber": "RBR", "vinyl": "VNL", "pvc": "PVC", "wood": "WD",
    "fiberglass": "FBRG", "composite": "COMP", "carbon": "CRBN",
    "graphite": "GRPH", "titanium": "TTN", "cemented": "CMTD",
    "super": "SPR", "oz": "OZ", "imperial": "IMP", "metric": "MET",
    "length": "LEN", "width": "WDT", "thickness": "THK", "resin": "RSN",
    "bonded": "BND", "depressed": "DPRS", "center": "CTR", "hub": "HUB",
    "arbor": "ARBR", "bore": "BORE", "hole": "HLE", "threaded": "THRD",
    "insert": "INS", "sleeve": "SLV", "collar": "CLR", "flange": "FLG",
    "seal": "SEL", "o-ring": "ORG", "gasket": "GST", "washer": "WSHR",
    "nut": "NUT", "bolt": "BLT", "bold": "BLT", "screw": "SCR",
    "lag": "LAG", "eyebolt": "EYE BLT", "hexagon": "HEX", "hex": "HEX",
    "carriage": "CRRG", "machine": "MCH", "self-tapping": "SLF-TP",
    "self-drilling": "SLF-DR", "drywall": "DWRYL", "sheetrock": "SHTRK",
    "wood": "WOD", "deck": "DCK", "joist": "JST", "tape": "TPE",
    "butyl": "BYTL", "flash": "FLSH", "sealant": "SLNT", "membrane": "MBRN",
    "icf": "ICF", "adhesive": "ADHV", "glue": "GLU", "construction": "CONST",
    "adhesive": "ADHV", "panel": "PANL", "siding": "SDNG", "lap": "LAP",
    "cedar": "CDR", "shingle": "SHNGL", "starter": "STR", "hip": "HIP",
    "ridge": "RDG", "gable": "GAB", "rafter": "RFTR", "purlin": "PRLN",
    "batt": "BAT", "insulation": "INSL", "faced": "FCD", "unfaced": "UNFD",
    "paper": "PAP", "foil": "FOL", "fiber": "FBR", "glass": "GLAS",
    "mineral": "MINL", "wool": "WOL", "cellulose": "CELL", "foam": "FRM",
    "rigid": "RGD", "board": "BRD", "polystyrene": "POLY", "eps": "EPS",
    "xps": "XPS", "polyiso": "PISO", "reflect": "RFLC", "vapor": "VPR",
    "barrier": "BARR", "retarder": "RTDR", "membrane": "MBRN",
    "underlayment": "UNDL", "felt": "FLT", "asphalt": "ASPH", "tar": "TAR",
    "paper": "PAP", "roofing": "RFG", "shingle": "SHNGL", "cedar": "CDR",
    "shake": "SHK", "slate": "SLTE", "clay": "CLY", "concrete": "CNCRT",
    "tile": "TLE", "paver": "PVR", "brick": "BRK", "block": "BLK",
    "masonry": "MSNY", "stone": "STN", "cast": "CST", "mortar": "MRTR",
    "grout": "GRT", "cement": "CMNT", "lime": "LIM", "sand": "SND",
    "mix": "MIX", "preblended": "PRBLND", "type": "TYP", "portland": "PRTLD",
    "gypsum": "GYPS", "drywall": "DRWL", "sheetrock": "SHTRK", "board": "BRD",
    "wallboard": "WALLBRD", "plaster": "PLSR", "veneer": "VNR",
    "easi-lite": "EASI-LITE", "firelite": "FIRELITE", "dens": "DENS",
    "glass": "GLAS", "mat": "MAT", "faced": "FCD", "core": "CORE",
    "gypsum": "GYPS", "fire": "FIRE", "rated": "RTD", "resistant": "RST",
    "mold": "MOLD", "moisture": "MSTR", "resistant": "RST", "green": "GRN",
    "board": "BRD", "siding": "SDNG", "trims": "TRMS", "soffit": "SOFF",
    "fascia": "FSC", "plank": "PLNK", "panel": "PNL", "smooth": "SMTH",
    "primed": "PRMD", "prestige": "PRSTG", "country": "CNTRY", "cedar": "CDR",
    "shiplap": "SHPLP", "groove": "GRV", "grooved": "GRVD", "edge": "EDG",
    "square edge": "SQ EDG", "tongue": "TNG", "groove": "GRV", "t&g": "T&G",
    "vintage": "VNTG", "landmark": "LNDMRK", "harvest": "HRVST",
    "transcend": "TRNSC", "lineage": "LNG", "enhance": "ENHNC",
    "naturals": "NTRLS", "basics": "BSCS", "select": "SEL", "classic": "CLSC",
    "legacy": "LGCY", "signature": "SGNTR", "freedom": "FRDM", "frontier": "FRNTR",
    "coastline": "CSTLN", "english": "ENGL", "walnut": "WLNT", "weathered": "WTHR",
    "teak": "TEK", "american": "AMER", "castle": "CSTL", "french": "FRN",
    "oak": "OAK", "brownstone": "BRWNSTN", "malted": "MLTD", "barley": "BRLY",
    "millstone": "MLSTN", "whiskey": "WHSKY", "barrel": "BRRL", "hatteras": "HTTRS",
    "salt": "SLT", "flat": "FLT", "honey": "HNY", "grove": "GRV",
    "tide": "TDE", "pool": "PL", "cinnamon": "CNNMN", "cove": "CV",
    "golden": "GLDN", "hour": "HR", "pebble": "PBL", "beach": "BCH",
    "biscayne": "BSCNY", "carmel": "CRML", "island": "ISLND", "mist": "MST",
    "jasper": "JSPR", "rainier": "RNR", "charcoal": "CHRCL", "mount": "MNT",
    "ridge": "RDG", "valley": "VLLY", "composite": "CMPST", "pvc": "PVC",
    "vinyl": "VNL", "aluminum": "ALUM", "alum": "ALUM", "metal": "MTL",
    "painted": "PNTD", "galvanized": "GLV", "steel": "STL", "stucco": "STCC",
    "texture": "TXT", "profile": "PRFL", "rib": "RIB", "xl": "XL",
    "premier": "PRMR", "ansi": "ANSI", "cee": "CEE", "tier": "TIER",
    "qualified": "QLFD", "ul": "UL", "listed": "LST", "csa": "CSA",
    "certified": "CRTFD", "energy": "ENRG", "star": "STR",
    "prop": "PROP", "65": "65", "warning": "WRN", "rohs": "ROHS",
    "compliant": "CMPL", "reach": "REACH", "lead": "LD", "free": "FR",
    "paint": "PNT", "thread": "THRD", "sealant": "SLNT", "lubricant": "LBRC",
    "oil": "OIL", "grease": "GRS", "cutting": "CTNG", "fluid": "FLD",
    "coolant": "CLNT", "antifreeze": "ANTFRZ", "solvent": "SLVNT",
}


# Series / line names (decking, tools, appliances)
SERIES_WORDS = set([
    "professional", "signature", "classic", "elite", "prestige", "imperial",
    "vintage", "landmark", "harvest", "transcend", "lineage", "enhance",
    "naturals", "basics", "select", "legacy", "frontier", "heritage",
    "ecoliteplus", "series", "eco", "performance", "performance+", "ceramic+",
    "cubitron", "steel demon", "speed demon", "abranet", "hiolit", "stikit",
])

CERTIFICATIONS = [
    "ASSE 1006", "CEE Tier 2 Qualified", "cUL Listed", "ENERGY STAR Certified",
    "NSF Certified", "UL Listed", "CSA Listed", "ANSI", "EPA", "CARB",
]

MATERIAL_WORDS = {
    "aluminum": "Aluminum", "alum": "Aluminum", "alumin": "Aluminum",
    "steel": "Steel", "stainless": "Stainless Steel", "stainless steel": "Stainless Steel",
    "sst": "Stainless Steel", "ss": "Stainless Steel",
    "composite": "Composite", "pvc": "PVC", "vinyl": "Vinyl", "vinyl": "Vinyl",
    "wood": "Wood", "cedar": "Cedar", "oak": "Oak", "brass": "Brass",
    "bronze": "Bronze", "copper": "Copper", "nylon": "Nylon", "rubber": "Rubber",
    "plastic": "Plastic", "concrete": "Concrete", "stone": "Stone",
    "ceramic": "Ceramic", "glass": "Glass", "chrome": "Chrome",
    "zinc": "Zinc", "galvanized": "Galvanized Steel", "iron": "Iron", "mesh": "Mesh",
}