# Review report (Phase 8)

Sidecar reporting only. The 252-column delivery CSV is not modified; no rows are merged, removed, reordered or altered.

## What the confidence score is (and is not)
- Evidence-completeness proxy per row, computed from signals already used by the evaluation harness (sections G and J).
- It is NOT a prediction-accuracy estimate: no row-level ground truth exists for the 1,000-row dataset, so none is assumed.
- All emitted attribute values remain NORMALIZED or blank; INFERRED stays 0. The score never invents content.

## Scoring rules
- Every row starts at 100; each fired rule subtracts its weight once; the score floors at 0.
- Rules and weights (fixed evaluation order = reason order):
  - no_attributes            -25  no attribute slots populated
  - mobile_desc_short        -15  MOBILE_DESC below the strict 60-char floor
  - duplicate_mpn_group      -15  Mfg_Part_Num appears on more than one row
  - manufacturer_unresolved  -10  MANUFACTURER_NAME blank in output
  - sparse_input_desc        -10  Part_Desc shorter than 20 characters
  - suspected_typo           -10  known typo pattern in Part_Desc
  - brand_unresolved         -5  BRAND_NAME blank in output
  - mpn_desc_mismatch        -5  leading desc token does not match Mfg_Part_Num
- Bands: HIGH >= 80, MEDIUM 60-79, LOW < 60.
- needs_human_review = score < 60 (the LOW band).
- Threshold rationale: a LOW row fails at least the attribute-evidence and description-length checks together or carries a hard data-quality flag (duplicate MPN, typo, sparse description), i.e. a human should confirm the record before commerce use.

## Summary
- rows scored: 1000
- bands: HIGH 665 | MEDIUM 289 | LOW 46
- needs human review: 46 of 1000 (4.6%)
- reason frequency (rule fires across rows):
  - mobile_desc_short       535  (MOBILE_DESC below the strict 60-char floor)
  - no_attributes           318  (no attribute slots populated)
  - brand_unresolved         70  (BRAND_NAME blank in output)
  - mpn_desc_mismatch        59  (leading desc token does not match Mfg_Part_Num)
  - manufacturer_unresolved   17  (MANUFACTURER_NAME blank in output)
  - sparse_input_desc         8  (Part_Desc shorter than 20 characters)
  - suspected_typo            8  (known typo pattern in Part_Desc)
  - duplicate_mpn_group       2  (Mfg_Part_Num appears on more than one row)

## Duplicate MPN groups (report-only)
- `AVM6EV` -> data rows [783, 784] (2 copies); both/all rows remain in place in input and output

## Duplicate description groups (report-only)
- rows [352, 353, 354] share description: '4x4 1g box cover'

## Positional integrity
- review rows are aligned 1:1 with input data-row order (row column = 1-based data row number); verified against Mfg_Part_Num per position.
