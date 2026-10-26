# ERRATUM — PREREG_HELDOUT2 (sha256 bcb14c8e…) and RESULT_HELDOUT2 (sha256 b2e498ff…)

Date: 2026-10-26. Author: Paulo Sergio Camillo. Written after both files were sealed; they are not changed. This file
corrects one premise they state.

## What was wrong

PREREG_HELDOUT2 says the two test segments are "not among the 24 training segments of the three models (all from
PHerc0139, 0814, 1667 and Paris4)", and calls PHerc0500P2 and PHerc0009B "two scrolls none of the models saw".
That list was incomplete.

Reading every segment id in the three checkpoints' own configs, field by field (`onde_treino.py`, log
`onde_treino.log`), and matching each id to its scroll on the public S3:

- **ink_9um (seed43, step 60000):** no segment of PHerc0500P2 or PHerc0009B. For this model both scrolls are unseen.
- **Reader v2 and Reader V3:** `datasets[].sampling_physical_segment_keys` / `surface_volume_paths` list other
  segments of both scrolls: 15+ of PHerc0500P2 (among them `20250628074500-500P2_front`) and 14 of PHerc0009B
  (`20250510172804`, `20250511200236` and twelve from 2025-09-19). Their lists also hold segments of PHerc0343P,
  PHerc0172 and more of PHerc0814.
- **The two tested segments themselves,** `20250825181859--1` (PHerc0500P2) and
  `20250919125754-auto_grown_20250919055754487_inp_hr` (PHerc0009B), are in **no** model's list.

## What it changes

- The test was on **segments outside every model's training data, from scrolls that Reader v2 and Reader V3 had seen
  in other segments** and ink_9um had not. It is not a test on scrolls no model saw.
- The numbers, the criteria and their verdicts in RESULT_HELDOUT2 are unchanged.
- **PHerc0841** (PREREG/RESULT_HELDOUT0841) does not appear in any of the three configs: it remains a scroll none
  of the models saw.
- The README and every summary are corrected to say this.
