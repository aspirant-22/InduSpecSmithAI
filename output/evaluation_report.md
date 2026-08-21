# Evaluation report (Phase 5)

Only 2 rows are available for direct output-level ground-truth evaluation. This is NOT statistically representative of the 1,000-row evaluation dataset.

## A. Header parity - PASS
- expected 252 / actual 252 / missing 0 / extra 0 / order mismatch False

## B. Row count - PASS
- input 1000 / output 1000 / missing 0 / extra 0

## C. Input field preservation (positional) - PASS
- 6000/6000 cells preserved verbatim (0 mismatches)
- Mfg_Part_Num   placeholders     0 -> preserved     0
- Part_Desc      placeholders     0 -> preserved     0
- E1_Brand       placeholders   799 -> preserved   799
- Unilog_Brand   placeholders  1000 -> preserved  1000
- DIB_Brand      placeholders   755 -> preserved   755
- Part_Manuf     placeholders    41 -> preserved    41

## D/E. Ground-truth accuracy (2 GT rows)
- row matching: PDSH4816AF=MATCHED, WDTS7024RZ=MATCHED
- fields with ground truth: 79 / without: 173 (unevaluable)
- expected populated cells: 134 | predicted populated: 80 | exact: 67 | incorrect: 13 | missing predictions: 54
- field-level exact-match accuracy: 50.0% | populated-field accuracy: 83.8%

### Per-field detail (GT-populated fields)
- MFR URL                       0/ 2 exact (  0.0%) missing:2
- PART_NUMBER                   0/ 2 exact (  0.0%) missing:2
- Dept                          2/ 2 exact (100.0%) missing:0
- Class                         2/ 2 exact (100.0%) missing:0
- Fine                          2/ 2 exact (100.0%) missing:0
- SKU - MY_PART_NUMBER          0/ 2 exact (  0.0%) missing:2
- Mfg_Part_Num                  2/ 2 exact (100.0%) missing:0
- Part_Desc                     2/ 2 exact (100.0%) missing:0
- E1_Brand                      2/ 2 exact (100.0%) missing:0
- Unilog_Brand                  2/ 2 exact (100.0%) missing:0
- DIB_Brand                     2/ 2 exact (100.0%) missing:0
- Part_Manuf                    2/ 2 exact (100.0%) missing:0
- MANUFACTURER_NAME             1/ 2 exact ( 50.0%) missing:0 e.g. [{'expected': 'Rheem Manufacturing', 'got': 'Electrolux Home Products Inc'}]
- BRAND_NAME                    2/ 2 exact (100.0%) missing:0
- MANUFACTURER_PART_NUMBER      2/ 2 exact (100.0%) missing:0
- Classpath                     2/ 2 exact (100.0%) missing:0
- MOBILE_DESC                   0/ 2 exact (  0.0%) missing:0 e.g. [{'expected': 'Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF', 'got': 'Electrolux Home Products Inc, FRIGIDAIRE®, Dishwasher, PDSH4816AF'}]
- INVOICE_DESC                  0/ 2 exact (  0.0%) missing:0 e.g. [{'expected': 'DISHWASHER LEG 5 SST 120V 15A 50-1/4IN', 'got': 'DISHWASHER SST'}]
- SHORT_DESC                    0/ 2 exact (  0.0%) missing:0 e.g. [{'expected': 'FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost™, Leg Mounting, 5-Wash Cycle, Stainless Steel', 'got': 'FRIGIDAIRE® PDSH4816AF Dishwasher With Stainless Steel'}]
- LONG_DESC1                    0/ 2 exact (  0.0%) missing:0 e.g. [{'expected': 'FRIGIDAIRE® Dishwasher With CleanBoost™, Professional Series, 5 Wash Cycles, 120 V, 15 A, Leg Mounting, 24 in W x 24-1/4 in D, 50-1/4 in Depth With Door Open, 8-1/2 in Upper Rack, 11-1/4 in Lower Rack Minimum Height, 10-3/8 in Upper Rack, 13-1/4 in Lower Rack Maximum Height, 47 dBA Sound Level, Stainless Steel, Additional Information: 240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours', 'got': 'FRIGIDAIRE® Dishwasher, Stainless Steel'}]
- RETAIL_DESC                   0/ 2 exact (  0.0%) missing:0 e.g. [{'expected': 'Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel', 'got': 'Dishwasher, Stainless Steel'}]
- With                          0/ 2 exact (  0.0%) missing:2
- Product Name                  2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 1             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 1             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 2             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 3             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 4             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 4             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_UOM 4               0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 5             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 5             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_UOM 5               0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 6             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 6             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 7             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 8             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 8             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 9             2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 9             0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_UOM 9               0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 10            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 10            0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 11            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 12            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 12            0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_UOM 12              0/ 2 exact (  0.0%) missing:2
- ATTRIBUTE_LABEL 13            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 13            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 14            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_LABEL 15            2/ 2 exact (100.0%) missing:0
- ATTRIBUTE_VALUE 15            0/ 2 exact (  0.0%) missing:2
- Product Image                 2/ 2 exact (100.0%) missing:0
- Specification Sheet           2/ 2 exact (100.0%) missing:0
- Actual Image (Yes/No)         0/ 2 exact (  0.0%) missing:2
- Standard/Approvals            0/ 1 exact (  0.0%) missing:1
- ATTRIBUTE_VALUE 3             0/ 1 exact (  0.0%) missing:1
- ATTRIBUTE_VALUE 11            0/ 1 exact (  0.0%) missing:1
- Warranty                      0/ 1 exact (  0.0%) missing:1
- Alternate Image 1             1/ 1 exact (100.0%) missing:0
- Alternate Image 2             1/ 1 exact (100.0%) missing:0
- Alternate Image 3             1/ 1 exact (100.0%) missing:0
- Alternate Image 4             1/ 1 exact (100.0%) missing:0
- Ref URL 1                     0/ 1 exact (  0.0%) missing:1
- Ref URL 2                     0/ 1 exact (  0.0%) missing:1
- MARKETING_DESCRIPTION         0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_1               0/ 1 exact (  0.0%) missing:0 e.g. [{'expected': '3rd rack with extra wash action', 'got': 'Material: Stainless Steel'}]
- ITEM_FEATURES_2               0/ 1 exact (  0.0%) missing:0 e.g. [{'expected': 'Adjustable 2nd Rack', 'got': 'Finish: Stainless Steel'}]
- ITEM_FEATURES_3               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_4               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_5               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_6               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_7               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_8               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_9               0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_10              0/ 1 exact (  0.0%) missing:1
- ITEM_FEATURES_11              0/ 1 exact (  0.0%) missing:1
- ATTRIBUTE_UOM 10              0/ 1 exact (  0.0%) missing:1
- ATTRIBUTE_VALUE 14            0/ 1 exact (  0.0%) missing:1

## F. Output coverage by category
- identifiers/input      populated    6000 / blank    2000 ( 75.0%)
- manufacturer/brand     populated    2913 / blank    2087 ( 58.3%)
- taxonomy               populated    5000 / blank       0 (100.0%)
- descriptions           populated    5000 / blank    1000 ( 83.3%)
- attributes             populated    3051 / blank  146949 (  2.0%)
- features/marketing     populated    1278 / blank   23722 (  5.1%)
- assets                 populated    5580 / blank    1420 ( 79.7%)
- urls/documents         populated       0 / blank   20000 (  0.0%)
- commercial/logistics   populated       0 / blank   21000 (  0.0%)
- other                  populated       0 / blank    5000 (  0.0%)

## G. Character-limit compliance - PASS
- MOBILE_DESC 60-80: 465 compliant | 535 NON-COMPLIANT (<60, evidence-short, left honest) | 0 violations (>80)
- INVOICE_DESC <=40 CAPS: 0 over-length | 0 not-uppercase

## H. Unsupported / inferred value detection - PASS
- INFERRED emitted: 0 (must be 0)
- filler phrases: 0 | fabricated URLs: 0 | asset-existence claims: 0 | blanket warranty claims: 0

## I. Blank-field analysis
- 223178/252000 cells blank (88.6%); 198 columns always blank; 34000 blanks are intentional (no source data)
- blank in identifiers/input         2000
- blank in manufacturer/brand        2087
- blank in taxonomy                     0
- blank in descriptions              1000
- blank in attributes              146949
- blank in features/marketing       23722
- blank in assets                    1420
- blank in urls/documents           20000
- blank in commercial/logistics     21000
- blank in other                     5000

## J. Data-quality flags (flags only - no auto-correction)
- duplicate MPNs: 1 {'AVM6EV': 2}
- MPN/desc leading-token mismatches: 24 | near-misses: 35 [{'mpn': 'G1941-UPC', 'desc_token': 'G1941UPC', 'similarity': 0.94}, {'mpn': 'D23LP-R02-1RW', 'desc_token': 'D23LPR021RW', 'similarity': 0.92}, {'mpn': '55226BKLFU', 'desc_token': '55226BKFLU', 'similarity': 0.9}, {'mpn': '576397', 'desc_token': '576394', 'similarity': 0.83}, {'mpn': 'GT-CB-100C', 'desc_token': 'GTCB100C', 'similarity': 0.89}]
- suspected typos: 8 rows, 6 kinds {'brakcet': 1, 'outet': 1, 'mocrowave': 1, 'trox': 1, 'rachet': 3, 'indudtrial': 1}
- placeholder brands: {'E1_Brand': 799, 'Unilog_Brand': 1000, 'DIB_Brand': 755}
- missing manufacturer: 41 | missing resolved brand: 70
- sparse descriptions (<20 ch): 8 | duplicate description groups: 1 (+2 copies)

## K. Ground-truth sample size
Only 2 rows are available for direct output-level ground-truth evaluation. This is NOT statistically representative of the 1,000-row evaluation dataset.

## Provenance summary
- COPIED=0, NORMALIZED=1269, DERIVED=0, INFERRED=0, UNKNOWN=137

## Overall verdict: PASS