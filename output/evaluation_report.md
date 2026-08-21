# Evaluation report

Rows: 1000
Header parity: True (252 cols vs expected 252)

NOTE: Only 2 rows are available for direct output-level ground-truth evaluation; this is NOT statistically representative of the 1,000-row evaluation dataset.

## Required-field emptiness
- Mfg_Part_Num           0
- Part_Desc              0
- Dept                   0
- Class                  0
- Fine                   0
- Classpath              0
- MOBILE_DESC            0
- INVOICE_DESC           0
- SHORT_DESC             0
- LONG_DESC1             0
- Product Name           0
- MANUFACTURER_NAME      17
- BRAND_NAME             70

## Length limits
- INVOICE_DESC > 40 chars: 0
- MOBILE_DESC   > 85 chars: 0

## Placeholder leakage in generated fields
none

## Attribute triples
- distinct labels used: 20
- labels without values: 137

## Attribute coverage & provenance (Phase 4)
- distinct labels used: 20
- rows with >=1 populated attribute: 683/1000 (68.3%)
- populated attribute slots: 1262
- labeled-but-blank slots (UNKNOWN): 137
- provenance of emitted values: COPIED=0, NORMALIZED=1262, DERIVED=0, INFERRED=0, UNKNOWN=137
- INFERRED values emitted: 0 (must be 0)

## Ground-truth scoring
reference ground-truth file not present in data/reference - skipped

## Taxonomy distribution
- depts: {'Power Tools': 311, 'Electrical': 54, 'Building Materials': 242, 'Appliances': 85, 'Hardware': 10, 'Windows & Doors': 12, 'Lighting': 222, 'Home Improvement': 9, 'Hand Tools': 17, 'Safety': 38}
- top fines: {'LED Light Bulbs': 125, 'Composite Decking Boards': 99, 'PVC Decking Boards': 45, 'Cut-Off Discs': 35, 'Screwdriver Bits': 28, 'Wall Lights': 22, 'Posts & Post Sleeves': 18, 'Abrasive Sheets & Discs': 17, 'Fascia Boards': 16, 'Chandeliers': 15, 'Pendants': 15, 'Gloves': 15}
