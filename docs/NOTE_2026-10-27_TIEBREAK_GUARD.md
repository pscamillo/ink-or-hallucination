# NOTE — a safety guard on the trio-strength tie-break, added after the seal (2026-10-27)

Date: 2026-10-27. Author: Paulo Sergio Camillo. The tie-break was sealed in PREREG_HELDOUT2 (sha256 bcb14c8e…).
This note records a change made after that seal; no sealed file is changed. Prompted by an independent review.

## The change

The sealed rule: S_side = median of the 3 pairwise correlations among one order's maps; ratio = max(S) / max(min(S),
1e-6); the stronger order wins if ratio ≥ 1.25.

Two holes: if the weaker trio's median is ≤ 0 the ratio is meaningless (it can be huge on noise), and the rule never
asked whether the stronger trio actually agrees. Now `segment.trio_strength` also gives **no verdict** when:

- min(S) ≤ 0; or
- the stronger order's three maps do not all agree pairwise, by the triangle's own rule (p < alpha and corr ≥
  min_ratio × null_max; a missing or NaN value counts as no agreement).

The output records which guard fired (`guard`). Two tests cover it (`tests/test_trio_strength.py`).

## Check on every saved triangle

`confere_trava.py` (md5 `1f9532fee772fb4ed54bdf1a2b15e8cf`, read-only) ran the sealed rule and the guarded rule on
every saved six-map triangle (3 models × 2 orders): 32 triangles.

- **The decisions the tie-break actually made are unchanged:** PHerc0500P2 (ratio 1.31, forward) and PHerc0009B
  (2.56, forward) in HELDOUT2.
- PHerc0841 (the calibration scroll, ratios about 1.56–1.71 in PREREG_HELDOUT2): `fase9.py` kept the maps but not
  the triangle's pair statistics, so these three were **not re-checked**. No verdict rests on them.
- PHerc1447 w060 / w062 (HELDOUT3, where the geometry rule decided first): unchanged, reverse.
- **3 changed, all in the ORDEM run (PHerc0139 w039, w041, w043):** the sealed rule would have said forward, the
  guarded rule says no verdict. Those triangles were made with the v6 null, whose bug gave `null_max = NaN`
  (RESULT_ORDEM), so no pair can count as agreeing. The tie-break did not exist in that run and decided nothing
  there. Abstaining on a triangle whose null failed is the intended behaviour.
- On the training triangles that set the 1.25 threshold (PREREG_HELDOUT2: 25 of 26 decided, all right), the guarded
  rule decides 22 of 26, all right, and abstains on 4 (PHerc1667 w029 and the three above). The threshold itself is
  unchanged.

## What it means

The guard makes the tie-break abstain in cases it should never have decided, and changes no sealed result. It has
not been tested on new data; the next blind test will use the guarded version.
