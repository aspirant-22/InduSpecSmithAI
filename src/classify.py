"""Taxonomy classification: maps a raw row to Dept/Class/Fine/Classpath.

Rule list is ordered most-specific-first.  Each rule has:
  keys   : list of (regex, weight) applied to the lowercased description
  dept/class/fine/classpath/product : output taxonomy + item type
"""
import re

# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------
def _cp(*parts):
    return ">".join(p for p in parts if p)


# Common leaf table for fine -> (dept, class, fine, classpath, product)
# ---------------------------------------------------------------------------
RULES = []


def rule(keys, dept, cls, fine, cp, product, priority=100):
    RULES.append({
        "keys": [(re.compile(k, re.I), 1.0) for k in keys],
        "dept": dept, "class": cls, "fine": fine, "classpath": cp,
        "product": product, "priority": priority,
    })


# ===========================================================================
# APPLIANCES
# ===========================================================================
rule(["dishwasher"], "Appliances", "Large Appliances", "Dishwashers",
      _cp("Appliances & Consumer Electronics", "Kitchen Appliances", "Built-In Dishwashers"),
      "Dishwasher", priority=100)
rule(["\\bdryer\\b", "\\belect dry", "\\belec dry", "gas dry"], "Appliances", "Large Appliances", "Dryers",
      _cp("Appliances & Consumer Electronics", "Laundry Appliances", "Dryers"),
      "Dryer", priority=100)
rule(["\\bwasher\\b", "wash - display", "elect washer", "sq washer"], "Appliances", "Large Appliances", "Washers",
      _cp("Appliances & Consumer Electronics", "Laundry Appliances", "Washers"),
      "Washer", priority=90)
rule(["laundry center"], "Appliances", "Large Appliances", "Laundry Centers",
      _cp("Appliances & Consumer Electronics", "Laundry Appliances", "Laundry Centers"),
      "Laundry Center", priority=100)
rule(["\\bfridge\\b", "refrigerat"], "Appliances", "Large Appliances", "Refrigerators",
      _cp("Appliances & Consumer Electronics", "Refrigeration", "Refrigerators"),
      "Refrigerator", priority=100)
rule(["freezer"], "Appliances", "Large Appliances", "Freezers",
      _cp("Appliances & Consumer Electronics", "Refrigeration", "Freezers"),
      "Freezer", priority=100)
rule(["beverage center"], "Appliances", "Large Appliances", "Beverage Centers",
      _cp("Appliances & Consumer Electronics", "Refrigeration", "Beverage Centers"),
      "Beverage Center", priority=100)
rule(["\\brange\\b", "\\brng\\b", "stove"], "Appliances", "Large Appliances", "Ranges",
      _cp("Appliances & Consumer Electronics", "Cooking Appliances", "Ranges"),
      "Range", priority=80)
rule(["cooktop"], "Appliances", "Large Appliances", "Cooktops",
      _cp("Appliances & Consumer Electronics", "Cooking Appliances", "Cooktops"),
      "Cooktop", priority=100)
rule(["microwave", "otr mocrowave", "otr microwave", "microwave drawer"], "Appliances", "Large Appliances", "Microwave Ovens",
      _cp("Appliances & Consumer Electronics", "Cooking Appliances", "Microwave Ovens"),
      "Microwave Oven", priority=100)
rule(["coffee maker", "drip coffee", "coffee"], "Appliances", "Large Appliances", "Coffee Makers",
      _cp("Appliances & Consumer Electronics", "Kitchen Appliances", "Coffee & Espresso"),
      "Coffee Maker", priority=50)
rule(["espresso"], "Appliances", "Large Appliances", "Espresso Machines",
      _cp("Appliances & Consumer Electronics", "Kitchen Appliances", "Coffee & Espresso"),
      "Espresso Machine", priority=100)
rule(["toast oven", "toaster"], "Appliances", "Small Appliances", "Toasters & Toaster Ovens",
      _cp("Appliances & Consumer Electronics", "Small Appliance", "Toasters & Toaster Ovens"),
      "Toaster", priority=100)
rule(["range grill"], "Appliances", "Large Appliances", "Range Grills",
      _cp("Appliances & Consumer Electronics", "Cooking Appliances", "Range Grills"),
      "Range Grill", priority=100)
rule(["wall oven", "\\boven\\b"], "Appliances", "Large Appliances", "Wall Ovens",
      _cp("Appliances & Consumer Electronics", "Cooking Appliances", "Wall Ovens"),
      "Wall Oven", priority=100)
rule(["heater kit"], "Appliances", "Parts & Accessories", "Appliance Parts",
      _cp("Appliances & Consumer Electronics", "Parts & Accessories", "Heating Elements"),
      "Appliance Part", priority=100)

# ===========================================================================
# POWER TOOLS
# ===========================================================================
PT_DEPT = "Power Tools"
ACC_CP_PREFIX = _cp("Building & Hardware", "Power Tools", "Accessories")

rule(["impact driver", "1/4\\\" hex.*driver", "hex hydraulic driver"], PT_DEPT, "Power Tools", "Impact Drivers",
      _cp("Building & Hardware", "Power Tools", "Impact Wrenches & Drivers"), "Impact Driver", priority=100)
rule(["impact wrench", "impact - wrench", "impact wrench", "\\bimpact\\b", "angle impact",
      "impact - bare tool"],
     PT_DEPT, "Power Tools", "Impact Wrenches",
     _cp("Building & Hardware", "Power Tools", "Impact Wrenches & Drivers"), "Impact Wrench", priority=80)
rule(["impact drill", "hammer drill", "\\bdrill\\b", "drill driver", "drill/drv", "drill driver", "combo kit"],
     PT_DEPT, "Power Tools", "Drills & Drivers",
     _cp("Building & Hardware", "Power Tools", "Drills & Drivers"), "Drill Driver", priority=50)
rule(["\\bdrill press\\b"], PT_DEPT, "Power Tools", "Drill Presses",
      _cp("Building & Hardware", "Power Tools", "Drill Presses"), "Drill Press", priority=100)
rule(["rotary tool"], PT_DEPT, "Power Tools", "Rotary Tools",
      _cp("Building & Hardware", "Power Tools", "Rotary Tools"), "Rotary Tool", priority=100)
rule(["framing nailer", "roofing nailer", "brad nailer", "\\bnailer\\b", "finish nailer"], PT_DEPT, "Power Tools", "Nailers",
      _cp("Building & Hardware", "Power Tools", "Nailers & Staplers"), "Nailer", priority=100)
rule(["stapler"], PT_DEPT, "Power Tools", "Staplers",
      _cp("Building & Hardware", "Power Tools", "Nailers & Staplers"), "Stapler", priority=100)
rule(["angle grinder", "\\bgrinder\\b", "die grinder", "cut and grind", "cut n grind"], PT_DEPT, "Power Tools", "Angle Grinders",
      _cp("Building & Hardware", "Power Tools", "Grinders"), "Grinder", priority=70)
rule(["circular saw", "circ saw", "\\bcirc\\b"], PT_DEPT, "Power Tools", "Circular Saws",
      _cp("Building & Hardware", "Power Tools", "Circular Saws"), "Circular Saw", priority=100)
rule(["miter saw", "mitre saw", "miter saw"], PT_DEPT, "Power Tools", "Miter Saws",
      _cp("Building & Hardware", "Power Tools", "Miter Saws"), "Miter Saw", priority=100)
rule(["table saw"], PT_DEPT, "Power Tools", "Table Saws",
      _cp("Building & Hardware", "Power Tools", "Table Saws"), "Table Saw", priority=100)
rule(["band saw", "bandsaw"], PT_DEPT, "Power Tools", "Band Saws",
      _cp("Building & Hardware", "Power Tools", "Band Saws"), "Band Saw", priority=100)
rule(["jig saw", "jigsaw"], PT_DEPT, "Power Tools", "Jig Saws",
      _cp("Building & Hardware", "Power Tools", "Jig Saws"), "Jig Saw", priority=100)
rule(["recip saw", "reciprocating saw", "sawzall"], PT_DEPT, "Power Tools", "Reciprocating Saws",
      _cp("Building & Hardware", "Power Tools", "Reciprocating Saws"), "Reciprocating Saw", priority=100)
rule(["track saw", "plunge cut saw", "plunge-cut saw"], PT_DEPT, "Power Tools", "Track Saws",
      _cp("Building & Hardware", "Power Tools", "Track Saws"), "Track Saw", priority=100)
rule(["\\bfence\\b", "xtender", "t-glide", "align-a-saw", "table assembly", "miter sled",
      "stealthstop", "stock feeder", "rail? set"],
     PT_DEPT, "Power Tool Accessories", "Table Saw Fences & Accessories",
     _cp("Building & Hardware", "Power Tools", "Table Saw Accessories"), "Table Saw Fence", priority=60)
rule(["\\bsaw blade\\b", "saw blade", "\\bblade\\b", "dado"], PT_DEPT, "Power Tool Accessories", "Saw Blades",
      ACC_CP_PREFIX + ">" + "Saw Blades", "Saw Blade", priority=60)
rule(["\\bsander\\b", "orbit sander", "orbital"], PT_DEPT, "Power Tools", "Sanders & Polishers",
      _cp("Building & Hardware", "Power Tools", "Sanders & Polishers"), "Sander", priority=80)
rule(["polisher"], PT_DEPT, "Power Tools", "Sanders & Polishers",
      _cp("Building & Hardware", "Power Tools", "Sanders & Polishers"), "Polisher", priority=100)
rule(["\\brouter\\b"], PT_DEPT, "Power Tools", "Routers",
      _cp("Building & Hardware", "Power Tools", "Routers"), "Router", priority=100)
rule(["planer", "planing"], PT_DEPT, "Power Tools", "Planers",
      _cp("Building & Hardware", "Power Tools", "Planers"), "Planer", priority=100)
rule(["power source", "heated gear"], PT_DEPT, "Power Tool Accessories", "Batteries & Chargers",
      ACC_CP_PREFIX + ">" + "Batteries & Chargers", "Charger", priority=60)
rule(["paper bag", "\\bbag\\b"], PT_DEPT, "Power Tool Accessories", "Vacuum Bags & Filters",
      ACC_CP_PREFIX + ">" + "Vacuums & Dust Collection", "Vacuum Bag", priority=70)
rule(["\\bsystainer\\b", "system.*storage"], PT_DEPT, "Power Tool Accessories", "Tool Storage & Organization",
      ACC_CP_PREFIX + ">" + "Tool Storage & Organization", "Tool Storage", priority=70)
rule(["\\bgr pro\\b", "granat", "festool.*gr\\b"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Sheets & Discs",
      ACC_CP_PREFIX + ">" + "Abrasive Sheets & Discs", "Abrasive Sheet", priority=80)
rule(["jointer"], PT_DEPT, "Power Tools", "Jointers",
      _cp("Building & Hardware", "Power Tools", "Jointers"), "Jointer", priority=100)
rule(["\\bshaper\\b"], PT_DEPT, "Power Tools", "Shapers",
      _cp("Building & Hardware", "Power Tools", "Shapers"), "Shaper", priority=100)
rule(["\\bblower\\b"], PT_DEPT, "Power Tools", "Blowers",
      _cp("Building & Hardware", "Power Tools", "Blowers & Vacuums"), "Blower", priority=100)
rule(["vacuum", "dust extractor"], PT_DEPT, "Power Tools", "Vacuums & Dust Extractors",
      _cp("Building & Hardware", "Power Tools", "Blowers & Vacuums"), "Vacuum", priority=100)
rule(["string trimmer", "\\btrimmer\\b", "grass trimmer"], PT_DEPT, "Outdoor Power Tools", "String Trimmers",
      _cp("Building & Hardware", "Outdoor Power Tools", "String Trimmers"), "String Trimmer", priority=90)
rule(["hedge trimmer", "hedge"], PT_DEPT, "Outdoor Power Tools", "Hedge Trimmers",
      _cp("Building & Hardware", "Outdoor Power Tools", "Hedge Trimmers"), "Hedge Trimmer", priority=100)
rule(["grease gun"], PT_DEPT, "Power Tools", "Grease Guns",
      _cp("Building & Hardware", "Power Tools", "Grease Guns"), "Grease Gun", priority=100)
rule(["screwdriver"], PT_DEPT, "Power Tools", "Screwdrivers",
      _cp("Building & Hardware", "Power Tools", "Screwdrivers"), "Screwdriver", priority=80)
rule(["laser level", "laser - green", "laser level", "line laser", "cross line laser", "cross line", "\\blaser\\b"],
     PT_DEPT, "Power Tools", "Lasers & Levels",
     _cp("Building & Hardware", "Power Tools", "Lasers & Levels"), "Laser Level", priority=70)
rule(["battery", "batt "], PT_DEPT, "Power Tool Accessories", "Batteries & Chargers",
      ACC_CP_PREFIX + ">" + "Batteries & Chargers", "Battery", priority=50)
rule(["charger", "power supply - charger", "power supply", "surge kit"], PT_DEPT, "Power Tool Accessories", "Batteries & Chargers",
      ACC_CP_PREFIX + ">" + "Batteries & Chargers", "Charger", priority=60)
rule(["starter kit", "2pc kit", "combo kit"], PT_DEPT, "Power Tools", "Cordless Tool Kits",
      _cp("Building & Hardware", "Power Tools", "Cordless Tool Kits"), "Cordless Tool Kit", priority=80)
rule(["screw matcher", "screwdriver"], PT_DEPT, "Power Tools", "Screwdrivers",
      _cp("Building & Hardware", "Power Tools", "Screwdrivers"), "Screwdriver", priority=70)
rule(["voltage detector"], PT_DEPT, "Power Tools", "Voltage Detectors",
      _cp("Building & Hardware", "Power Tools", "Testing & Detection"), "Voltage Detector", priority=100)

# ===========================================================================
# CUTTING & ABRASIVES (accessories)
# ===========================================================================
rule(["cut.?off disc", "metal cut off", "masonry cut off", "steel demon", "speed demon",
      "cut.?off and grind", "metal cut.?off"],
     PT_DEPT, "Cutting & Abrasive Accessories", "Cut-Off Discs",
     ACC_CP_PREFIX + ">" + "Cut-Off Discs", "Cut-Off Disc", priority=100)
rule(["cut.?off blade", "metal cut.?off disc"], PT_DEPT, "Cutting & Abrasive Accessories", "Cut-Off Discs",
      ACC_CP_PREFIX + ">" + "Cut-Off Discs", "Cut-Off Disc", priority=90)
rule(["diamond.*blade", "tile blade", "rim glass", "diamond blade"], PT_DEPT, "Cutting & Abrasive Accessories", "Diamond Blades",
      ACC_CP_PREFIX + ">" + "Diamond Blades", "Diamond Blade", priority=90)
rule(["grinding wheel", "grinding disc"], PT_DEPT, "Cutting & Abrasive Accessories", "Grinding Wheels",
      ACC_CP_PREFIX + ">" + "Grinding Wheels", "Grinding Wheel", priority=100)
rule(["grinding"], PT_DEPT, "Cutting & Abrasive Accessories", "Grinding Wheels",
      ACC_CP_PREFIX + ">" + "Grinding Wheels", "Grinding Wheel", priority=40)
rule(["sanding belt"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Belts",
      ACC_CP_PREFIX + ">" + "Abrasive Belts", "Abrasive Belt", priority=100)
rule(["sanding sponge"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Sponges",
      ACC_CP_PREFIX + ">" + "Abrasive Sponges", "Abrasive Sponge", priority=100)
rule(["stikit film", "775l", "sanding film", "abrasive film"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Films & Sheets",
      ACC_CP_PREFIX + ">" + "Abrasive Films & Sheets", "Abrasive Film", priority=100)
rule(["abranet", "hiolit", "iridium"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Sheets & Discs",
      ACC_CP_PREFIX + ">" + "Abrasive Sheets & Discs", "Abrasive Sheet", priority=90)
rule(["\\bdozer\\b", "hole dozer", "hole saw", "hole drilling"], PT_DEPT, "Power Tool Accessories", "Hole Saws",
      ACC_CP_PREFIX + ">" + "Hole Saws & Kits", "Hole Saw", priority=100)
rule(["sanding"], PT_DEPT, "Cutting & Abrasive Accessories", "Abrasive Sheets & Discs",
      ACC_CP_PREFIX + ">" + "Abrasive Sheets & Discs", "Abrasive Sheet", priority=40)

# ===========================================================================
# TOOL ACCESSORIES
# ===========================================================================
rule(["router bit"], PT_DEPT, "Power Tool Accessories", "Router Bits",
      ACC_CP_PREFIX + ">" + "Router Bits", "Router Bit", priority=100)
rule(["plug cutter", "countersink"], PT_DEPT, "Power Tool Accessories", "Router Bits & Cutters",
      ACC_CP_PREFIX + ">" + "Router Bits & Cutters", "Router Bit", priority=100)
rule(["planer blade", "planer knives"], PT_DEPT, "Power Tool Accessories", "Planer Blades",
      ACC_CP_PREFIX + ">" + "Planer Blades", "Planer Blade", priority=100)
rule(["dado"], PT_DEPT, "Power Tool Accessories", "Dado Sets",
      ACC_CP_PREFIX + ">" + "Dado Sets", "Dado Set", priority=100)
rule(["tpi.*saw blade", "jig saw blade"], PT_DEPT, "Power Tool Accessories", "Saw Blades",
      ACC_CP_PREFIX + ">" + "Saw Blades", "Saw Blade", priority=100)
rule(["saw blade"], PT_DEPT, "Power Tool Accessories", "Saw Blades",
      ACC_CP_PREFIX + ">" + "Saw Blades", "Saw Blade", priority=80)
rule(["\\bbit\\b", "drive bit", "phillips.*bit", "torx drive bit", "square drive bit",
      "impact.*bit", "torsion bit"],
     PT_DEPT, "Power Tool Accessories", "Screwdriver Bits",
     ACC_CP_PREFIX + ">" + "Screwdriver Bits", "Screwdriver Bit", priority=60)
rule(["socket adapter", "drive universal joint", "impact.*socket", "\\bsocket\\b"],
     PT_DEPT, "Power Tool Accessories", "Sockets & Adapters",
     ACC_CP_PREFIX + ">" + "Sockets & Adapters", "Socket", priority=60)
rule(["wrench set", "mechanics set", "socket set"], PT_DEPT, "Power Tool Accessories", "Wrenches",
      ACC_CP_PREFIX + ">" + "Wrenches", "Wrench Set", priority=100)
rule(["ratchet", "rachet", "\\brtch\\b"], PT_DEPT, "Power Tool Accessories", "Ratchets",
      ACC_CP_PREFIX + ">" + "Ratchets & Sockets", "Ratchet", priority=100)
rule(["chalk & reel", "chalk"], PT_DEPT, "Power Tool Accessories", "Chalk Lines",
      ACC_CP_PREFIX + ">" + "Chalk Lines", "Chalk Line Reel", priority=100)
rule(["battery mount"], PT_DEPT, "Power Tool Accessories", "Tool Storage & Organization",
      ACC_CP_PREFIX + ">" + "Tool Storage & Organization", "Battery Mount", priority=100)
rule(["organizer"], PT_DEPT, "Power Tool Accessories", "Tool Storage & Organization",
      ACC_CP_PREFIX + ">" + "Tool Storage & Organization", "Tool Organizer", priority=100)
rule(["tool chest", "tool box", "toolbox"], PT_DEPT, "Power Tool Accessories", "Tool Storage & Organization",
      ACC_CP_PREFIX + ">" + "Tool Storage & Organization", "Tool Chest", priority=100)
rule(["mason line", "string line"], PT_DEPT, "Hand Tools", "Mason Lines",
      _cp("Building & Hardware", "Hand Tools", "Measuring & Layout"), "Mason Line", priority=100)
rule(["speaker", "\\bspks?\\b"], PT_DEPT, "Power Tool Accessories", "Jobsite Radios & Speakers",
      _cp("Building & Hardware", "Power Tools", "Jobsite Radios & Speakers"), "Jobsite Speaker", priority=100)
rule(["pruning", "pole prun"], PT_DEPT, "Outdoor Power Tools", "Pruners & Shears",
      _cp("Building & Hardware", "Outdoor Power Tools", "Pruners & Shears"), "Pruning Shear", priority=100)
rule(["framing magazine", "collated attach"], PT_DEPT, "Power Tools", "Nailer Accessories",
      _cp("Building & Hardware", "Power Tools", "Nailers & Staplers"), "Nailer Accessory", priority=100)

# ===========================================================================
# HAND TOOLS
# ===========================================================================
rule(["folding knife", "utility knife", "\\bknife\\b"], "Hand Tools", "Hand Tools", "Knives",
      _cp("Building & Hardware", "Hand Tools", "Knives"), "Knife", priority=80)
rule(["file bstd", "\\bfile\\b"], "Hand Tools", "Hand Tools", "Files & Rasps",
      _cp("Building & Hardware", "Hand Tools", "Files & Rasps"), "File", priority=90)
rule(["snip"], "Hand Tools", "Hand Tools", "Snips",
      _cp("Building & Hardware", "Hand Tools", "Snips & Shears"), "Snip", priority=100)
rule(["mechanical pencil", "\\bpencil\\b"], "Hand Tools", "Hand Tools", "Marking Tools",
      _cp("Building & Hardware", "Hand Tools", "Marking Tools"), "Marking Pencil", priority=100)
rule(["riding square", "rafter square", "raftersquare", "rafter.?square", "\\bsquare\\b"], "Hand Tools", "Hand Tools", "Squares",
      _cp("Building & Hardware", "Hand Tools", "Measuring & Layout"), "Square", priority=80)
rule(["t-square", "t square", "BigCal"], "Hand Tools", "Hand Tools", "Measuring Tools",
      _cp("Building & Hardware", "Hand Tools", "Measuring & Layout"), "Measuring Tool", priority=100)
rule(["carrying bit holder", "bit holder"], "Hand Tools", "Hand Tools", "Bit Holders",
      _cp("Building & Hardware", "Hand Tools", "Screwdriving"), "Bit Holder", priority=100)
rule(["screwdriver"], "Hand Tools", "Hand Tools", "Screwdrivers",
      _cp("Building & Hardware", "Hand Tools", "Screwdrivers"), "Screwdriver", priority=60)
rule(["phone holster", "holster"], "Hand Tools", "Hand Tools", "Tool Holders",
      _cp("Building & Hardware", "Hand Tools", "Tool Holders"), "Tool Holster", priority=100)

# ===========================================================================
# CUT-OFF ABRASIVES that look like 'graining'
# ===========================================================================

# ===========================================================================
# FASTENERS
# ===========================================================================
rule(["finish nail", "collated nail", "coil.*nail", "senco.*\\.131", "\\bnail\\b"], "Hardware", "Fasteners", "Nails",
      _cp("Building & Hardware", "Fasteners", "Nails & Staples"), "Fastener", priority=60)
rule(["staple"], "Hardware", "Fasteners", "Staples",
      _cp("Building & Hardware", "Fasteners", "Nails & Staples"), "Staple", priority=100)

# ===========================================================================
# ELECTRICAL
# ===========================================================================
EL_PREFIX = "Electrical"
rule(["load center", "load cntr"], "Electrical", "Power Distribution", "Load Centers",
      _cp("Electrical", "Power Distribution", "Load Centers"), "Load Center", priority=100)
rule(["outlet", "receptacle", "rcpt", "outet"], "Electrical", "Outlets & Receptacles", "Outlets",
      _cp("Electrical", "Outlets & Receptacles", "Outlets"), "Outlet", priority=70)
rule(["gfci", "gfi outlet"], "Electrical", "Outlets & Receptacles", "GFCI Outlets",
      _cp("Electrical", "Outlets & Receptacles", "GFCI Outlets"), "GFCI Outlet", priority=100)
rule(["wall tap", "usb outlet"], "Electrical", "Outlets & Receptacles", "USB & Charging Outlets",
      _cp("Electrical", "Outlets & Receptacles", "USB & Charging Outlets"), "Wall Tap", priority=100)
rule(["switch / pilot", "\\bswitch\\b", "3-way switch", "toggle"], "Electrical", "Switches", "Switches",
      _cp("Electrical", "Switches", "Wall Switches"), "Switch", priority=60)
rule(["dimmer"], "Electrical", "Switches", "Dimmers",
      _cp("Electrical", "Switches", "Dimmers"), "Dimmer", priority=100)
rule(["\\btimer\\b"], "Electrical", "Switches", "Timers",
      _cp("Electrical", "Switches", "Timers"), "Timer", priority=100)
rule(["box cover", "box\\b", "oct box", "octagon box", "square box"], "Electrical", "Electrical Boxes", "Electrical Boxes & Covers",
      _cp("Electrical", "Electrical Boxes & Fittings", "Electrical Boxes & Covers"), "Electrical Box", priority=60)
rule(["wallplate", "wall plate", "cover wh", "cover sw", "decor plate", "port decor plate"], "Electrical", "Wall Plates", "Wall Plates",
      _cp("Electrical", "Wall Plates", "Wall Plates"), "Wall Plate", priority=80)
rule(["cord connector", "plug", "cord grip", "receptacle cord"], "Electrical", "Wiring", "Cord Connectors",
      _cp("Electrical", "Wiring & Cable", "Cord Connectors & Plugs"), "Cord Connector", priority=80)
rule(["\\bcord\\b", "\\bwire\\b", "cable", "cat5e", "triplex", "entrance cable"], "Electrical", "Wiring", "Wire & Cable",
      _cp("Electrical", "Wiring & Cable", "Wire & Cable"), "Wire", priority=70)
rule(["hanger"], "Electrical", "Electrical Boxes", "Box Hangers",
      _cp("Electrical", "Electrical Boxes & Fittings", "Boxes & Accessories"), "Box Hanger", priority=100)
rule(["electric tape", "elect tape", "vinyl tape"], "Electrical", "Wiring", "Electrical Tape",
      _cp("Electrical", "Wiring & Cable", "Tape & Marking"), "Electrical Tape", priority=100)

# ===========================================================================
# LIGHTING
# ===========================================================================
rule(["led flat panel", "flat panel light"], "Lighting", "Commercial Lighting", "LED Panels",
      _cp("Lighting", "Commercial Lighting", "LED Panel Lights"), "LED Panel Light", priority=100)
rule(["highbay", "high bay"], "Lighting", "Commercial Lighting", "High Bay Lights",
      _cp("Lighting", "Commercial Lighting", "High Bay Lights"), "High Bay Light", priority=100)
rule(["tape light", "strip light", "led strip"], "Lighting", "Indoor Lighting", "LED Tape & Strip Lights",
      _cp("Lighting", "Indoor Lighting", "LED Tape & Strip Lights"), "LED Strip Light", priority=100)
rule(["wrap light", "wrap lt", "led wrap"], "Lighting", "Indoor Lighting", "LED Wrap Lights",
      _cp("Lighting", "Indoor Lighting", "LED Wrap Lights"), "LED Wrap Light", priority=100)
rule(["downlight", "down light", "down lt", "dwn lt", "recessed"], "Lighting", "Indoor Lighting", "Recessed Downlights",
      _cp("Lighting", "Indoor Lighting", "Recessed Lighting"), "Downlight", priority=90)
rule(["chandelier", "chand"], "Lighting", "Indoor Lighting", "Chandeliers",
      _cp("Lighting", "Indoor Lighting", "Chandeliers"), "Chandelier", priority=100)
rule(["pendant"], "Lighting", "Indoor Lighting", "Pendants",
      _cp("Lighting", "Indoor Lighting", "Pendant Lights"), "Pendant Light", priority=100)
rule(["ceiling light", "ceiling lt", "ceiling lamp"], "Lighting", "Indoor Lighting", "Ceiling Lights",
      _cp("Lighting", "Indoor Lighting", "Ceiling Lights"), "Ceiling Light", priority=100)
rule(["sconce"], "Lighting", "Indoor Lighting", "Wall Sconces",
      _cp("Lighting", "Indoor Lighting", "Wall Sconces"), "Wall Sconce", priority=100)
rule(["wall light", "wall lt", "wall lamp", "bath light"], "Lighting", "Indoor Lighting", "Wall Lights",
      _cp("Lighting", "Indoor Lighting", "Wall Lights"), "Wall Light", priority=100)
rule(["ext wall", "outdoor wall", "post light", "post lt", "flood"], "Lighting", "Outdoor Lighting", "Outdoor Wall & Post Lights",
      _cp("Lighting", "Outdoor Lighting", "Outdoor Wall & Post Lights"), "Outdoor Light", priority=80)
rule(["\\bbulb\\b", "\\bincan\\b", "led med", "led.+"], "Lighting", "Light Bulbs", "LED Light Bulbs",
      _cp("Lighting", "Light Bulbs", "LED Light Bulbs"), "LED Bulb", priority=60)
rule(["halogen", "sodium", "flor", "fluorescent"], "Lighting", "Light Bulbs", "Specialty Bulbs",
      _cp("Lighting", "Light Bulbs", "Specialty Bulbs"), "Light Bulb", priority=60)
rule(["motion light", "motion lt", "flashlight", "flashlt", "flash light", "headlight", "work light", "clip light", "nano clip", "shop light", "rechargeable.*lt", "rechargeable.*light", "light.*rechargeable", "\\bheadlt\\b", "\\btask light\\b"],
     "Lighting", "Task Lighting", "Work & Task Lights",
     _cp("Lighting", "Portable & Task Lighting", "Work Lights & Flashlights"), "Work Light", priority=60)
rule(["\\bbulb\\b", "\\bincan\\b", "\\binc\\b", "a15", "a19", "\\bmed\\b.*base", "adj base",
      "\\b40w\\b", "\\b60w\\b", "\\b100w\\b", "led med", "led.+"],
     "Lighting", "Light Bulbs", "LED Light Bulbs",
     _cp("Lighting", "Light Bulbs", "LED Light Bulbs"), "LED Bulb", priority=60)
rule(["motion drive"], "Lighting", "Outdoor Lighting", "Motion Sensors & Alerts",
      _cp("Lighting", "Outdoor Lighting", "Motion Sensors"), "Motion Alert", priority=100)

# ===========================================================================
# BUILDING MATERIALS
# ===========================================================================
def _bm(dep, cls, fine, cp, product, keys, p=100):
    rule(keys, dep, cls, fine, cp, product, priority=p)


_bm("Building Materials", "Structural Building Materials", "Insulated Sheathing",
    _cp("Building Materials", "Structural", "Insulated Sheathing"),
    "Insulated Sheathing Board", ["r-sheathing", "zip r"])
_bm("Building Materials", "Structural Building Materials", "Sheathing & Panels",
    _cp("Building Materials", "Structural", "Sheathing & Paneling"),
    "Sheathing Panel", ["osb", "plywood", "sheathing"])
_bm("Building Materials", "Structural Building Materials", "Rainscreens",
    _cp("Building Materials", "Structural", "Rainscreens & Ventilated Systems"),
    "Rainscreen", ["rainscreen"])
_bm("Building Materials", "Drywall & Gypsum", "Drywall Panels",
    _cp("Building Materials", "Drywall & Gypsum", "Drywall Sheets"),
    "Drywall Panel", ["drywall", "easi-lite", "firelite", "gypsum"])
_bm("Building Materials", "Siding & Trim", "Fiber Cement Siding",
    _cp("Building Materials", "Exterior", "Fiber Cement Siding"),
    "Fiber Cement Panel", ["hardie", "hardiplank", "hardiepanel"])
_bm("Building Materials", "Siding & Trim", "Engineered Wood Siding",
    _cp("Building Materials", "Exterior", "Engineered Wood Siding"),
    "Siding Panel", ["smart lap", "smart pan", "smartside"])
_bm("Building Materials", "Roofing & Waterproofing", "Metal Roofing",
    _cp("Building Materials", "Roofing", "Metal Roofing"),
    "Metal Roofing Panel", ["premier rib", "rib xl"])
_bm("Building Materials", "Roofing & Waterproofing", "Ice & Water Shield",
    _cp("Building Materials", "Roofing", "Ice & Water Shield"),
    "Underlayment", ["ice guard", "eaveguard", "weathr lk", "weather lock"])
_bm("Building Materials", "Roofing & Waterproofing", "Underlayment",
    _cp("Building Materials", "Roofing", "Underlayment"),
    "Roofing Felt", ["\\bbdl\\b", "underlayment"])
_bm("Building Materials", "Concrete & Masonry", "Mortar Mixes",
    _cp("Building Materials", "Concrete & Masonry", "Mortar"),
    "Mortar Mix", ["mortar"])
_bm("Building Materials", "Decking & Railing", "Composite Decking Boards",
    _cp("Building & Hardware", "Decking & Railing", "Decking Boards"),
    "Decking Board", ["decking", "\\bdeck\\b"], p=40)
_bm("Building Materials", "Decking & Railing", "PVC Decking Boards",
    _cp("Building & Hardware", "Decking & Railing", "PVC Decking"),
    "PVC Decking Board", ["azek.*decking", "pvc decking"])
_bm("Building Materials", "Decking & Railing", "Fascia Boards",
    _cp("Building & Hardware", "Decking & Railing", "Fascia"),
    "Fascia Board", ["fascia"])
_bm("Building Materials", "Decking & Railing", "Deck Railing Kits",
    _cp("Building & Hardware", "Decking & Railing", "Railing Systems"),
    "Railing Kit", ["rail kit", "t-rail", "railing"], p=90)
_bm("Building Materials", "Decking & Railing", "Deck Railing Panels",
    _cp("Building & Hardware", "Decking & Railing", "Railing Systems"),
    "Railing Panel", ["rail panel"])
_bm("Building Materials", "Decking & Railing", "Balusters",
    _cp("Building & Hardware", "Decking & Railing", "Balusters"),
    "Baluster", ["balusters", "baluster"])
_bm("Building Materials", "Decking & Railing", "Posts & Post Sleeves",
    _cp("Building & Hardware", "Decking & Railing", "Posts & Post Sleeves"),
    "Post Sleeve", ["post sleeve", "post wraap", "post cap", "post trim", "post wrap", "support post", "post\\b"], p=70)
_bm("Building Materials", "Decking & Railing", "Railing Gates",
    _cp("Building & Hardware", "Decking & Railing", "Railing Gates"),
    "Railing Gate", ["gate"])
_bm("Building Materials", "Decking & Railing", "ADA Railing",
    _cp("Building & Hardware", "Decking & Railing", "ADA Railing"),
    "ADA Railing", ["ada"])
_bm("Building Materials", "Decking & Railing", "Decking Tape & Protection",
    _cp("Building & Hardware", "Decking & Railing", "Decking Accessories"),
    "Deck Joist Tape", ["joist tape", "protecto wrap"])
_bm("Building Materials", "Trim & Molding", "Post Wraps",
    _cp("Building Materials", "Exterior", "Columns & Post Wraps"),
    "Post Wrap", ["post wrap"])
_bm("Building Materials", "Decking & Railing", "Composite Decking Boards",
    _cp("Building & Hardware", "Decking & Railing", "Decking Boards"),
    "Composite Decking Board", ["\\btrex\\b", "\\blineage\\b", "\\bharvest\\b",
                                "\\btransc\\b", "\\benhance\\b"])
_bm("Building Materials", "Siding & Trim", "Wood Siding",
    _cp("Building Materials", "Exterior", "Wood Siding"),
    "Wood Siding Board", ["doug fir", "stk smooth", "1s2e", "stk lang",
                          "smart vented", "\\bsoffit\\b"])
_bm("Building Materials", "Drywall & Gypsum", "Ceiling Tiles",
    _cp("Building Materials", "Ceiling Systems", "Ceiling Tiles"),
    "Ceiling Tile", ["fine fissured", "1728", "ceiling tile", "ceiling tle"])
_bm("Building Materials", "Roofing & Waterproofing", "Tapes & Seals",
    _cp("Building Materials", "Roofing", "Sealants & Tapes"),
    "Construction Tape", ["emseal tape", "\\btape\\b"], p=40)
_bm("Electrical", "Wiring", "Power Supplies",
    _cp("Electrical", "Wiring & Cable", "Power Supplies"),
    "Power Supply", ["jumpstart", "power supply", "pwr supply"], p=100)

# ===========================================================================
# DOORS & WINDOWS
# ===========================================================================
DW = "Windows & Doors"
rule(["skylight", "skylt", "fixed skylight"], DW, "Skylights", "Fixed Skylights",
      _cp("Doors & Windows", "Skylights", "Fixed Skylights"), "Skylight", priority=100)
rule(["patio door", "gliding patio", "sliding patio"], DW, "Doors", "Patio Doors",
      _cp("Doors & Windows", "Doors", "Patio Doors"), "Patio Door", priority=100)
rule(["\\bslider\\b", "sliding window"], DW, "Windows", "Sliding Windows",
      _cp("Doors & Windows", "Windows", "Sliding Windows"), "Sliding Window", priority=100)
rule(["hopper"], DW, "Windows", "Hopper Windows",
      _cp("Doors & Windows", "Windows", "Hopper Windows"), "Hopper Window", priority=100)
rule(["attic access"], DW, "Doors", "Attic Access Doors",
      _cp("Doors & Windows", "Doors", "Access Panels"), "Attic Access Door", priority=100)
rule(["cas vin", "window.*wrap", "inside cas"], DW, "Windows", "Window Trim & Casing",
      _cp("Doors & Windows", "Windows", "Window Trim & Casing"), "Window Casing", priority=100)
rule(["threshold"], "Hardware", "Door Hardware", "Thresholds",
      _cp("Building & Hardware", "Door Hardware", "Thresholds & Weather Stripping"), "Threshold", priority=100)

# ===========================================================================
# FANS
# ===========================================================================
rule(["\\bfan\\b"], "Home Improvement", "Fans & Ventilation", "Ceiling Fans",
      _cp("Appliances & Consumer Electronics", "Fans & Ventilation", "Ceiling Fans"), "Ceiling Fan", priority=100)

# ===========================================================================
# SAFETY
# ===========================================================================
rule(["safety glasses", "safety glass", "polarized", "\\bframe\\b.*len"], "Safety", "Eye Protection", "Safety Glasses",
      _cp("Janitorial & Sanitation", "Safety", "Eye Protection"), "Safety Glasses", priority=100)
rule(["hoodie"], "Safety", "Clothing", "Workwear",
      _cp("Janitorial & Sanitation", "Safety", "Clothing & Workwear"), "Heated Hoodie", priority=100)
rule(["glove", "gloves"], "Safety", "Hand Protection", "Gloves",
      _cp("Janitorial & Sanitation", "Safety", "Hand Protection"), "Gloves", priority=100)
rule(["hearing protector", "hearing prot"], "Safety", "Hearing Protection", "Hearing Protectors",
      _cp("Janitorial & Sanitation", "Safety", "Hearing Protection"), "Hearing Protector", priority=100)
rule(["fire extinguisher", "extinguisher"], "Safety", "Fire Safety", "Fire Extinguishers",
      _cp("Janitorial & Sanitation", "Safety", "Fire Extinguishers"), "Fire Extinguisher", priority=100)
rule(["smoke & co alarm", "smoke.*alarm", "co alarm", "\\balarm\\b"], "Safety", "Fire Safety", "Smoke & CO Alarms",
      _cp("Janitorial & Sanitation", "Safety", "Smoke & CO Alarms"), "Smoke & CO Alarm", priority=100)

# ===========================================================================
# MISCELLANEOUS
# ===========================================================================
rule(["kneeling pad", "bttl opener", "bottle opener"], "Hardware", "Worksite Supplies", "Kneeling Pads",
      _cp("Building & Hardware", "Worksite Supplies", "Kneeling Pads"), "Kneeling Pad", priority=100)
rule(["tire pressure", "inflator gauge"], "Hardware", "Worksite Supplies", "Tire Gauges",
      _cp("Building & Hardware", "Worksite Supplies", "Air & Tire Tools"), "Tire Pressure Gauge", priority=100)
rule(["48\\\" bottle", "bottle"], "Hardware", "Worksite Supplies", "Work Bottles",
      _cp("Building & Hardware", "Worksite Supplies", "Drinkware"), "Insulated Bottle", priority=80)
rule(["masonry line", "decorator line"], "Hardware", "Measuring & Layout", "Masonry Lines",
      _cp("Building & Hardware", "Hand Tools", "Measuring & Layout"), "Masonry Line", priority=100)
rule(["grid.*tape", "eaveguard"], "Building Materials", "Roofing & Waterproofing", "Roofing Tapes & Seals",
      _cp("Building Materials", "Roofing", "Sealants & Tapes"), "Roofing Tape", priority=100)


def classify(desc):
    """Return taxonomy dict based on description."""
    d = (desc or "").lower()
    best = None
    for r in RULES:
        score = 0.0
        for rx, w in r["keys"]:
            if rx.search(d):
                score += w
        if score > 0:
            prio = r.get("priority", 0)
            if best is None or score > best["score"] or (
                    score == best["score"] and prio > best["prio"]):
                best = {"score": score, "prio": prio, "meta": r}
    if best is not None:
        m = best["meta"]
        return {
            "dept": m["dept"],
            "class": m["class"],
            "fine": m["fine"],
            "classpath": m["classpath"],
            "product": m["product"],
        }
    return {"dept": "Hardware", "class": "General", "fine": "General Merchandise",
            "classpath": _cp("Building & Hardware", "General", "General Merchandise"),
            "product": "Component"}