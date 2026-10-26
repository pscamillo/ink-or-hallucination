# RESULT — PREREG_HELDOUT0841.md (sha256 b8bdc63d…): the kit on PHerc0841, a scroll none of the models saw

Date: 2026-10-26. Author: Paulo Sergio Camillo. Run: `fase9.py` (md5 6664f731…), started automatically when the download
finished (night of 2026-10-25), log `fase9.log`. Nothing was changed after the seal.

## Outcome in one line

**The kit abstained on all three segments.** It gave no verdict on PHerc0841, so every sealed criterion is NOT TESTABLE.
It made no wrong call, but it also stayed silent on segments where the three models read real ink well.

## What happened, per segment

| segment | registration (CT vs CT) | order rule | triangle fallback | kit |
|---|---|---|---|---|
| w00 | shift (−6, −7) px, peak 0.856 → applied | abstained: sagitta −190.8 vx, slope −1.00, **CT match 0.34** (< 0.5) | no core | unresolved |
| auto_grown …144552896 | (−6, −7), 0.859 → applied | abstained: −184.0, −1.02, **0.28** | no core | unresolved |
| auto_grown …174252405 | (−6, −7), 0.855 → applied | abstained: −194.4, −1.01, **0.35** | no core | unresolved |

- The CT-against-CT check found the same real shift on all three segments and applied it to the labels, as sealed.
- The geometry was clear (|sagitta| ≈ 190 vx, |slope| ≈ 1.0); the rule abstained only on its CT-match threshold.
- With the order unresolved, the sealed procedure runs no windowed check, plants no letters and computes no natural
  split. That is why Q1–Q4 and N1 have no data.

## The labels, read last (AUC per map, official labels, registered)

| segment | ink9 fwd / rev | rv2 fwd / rev | rv3 fwd / rev |
|---|---|---|---|
| w00 | 0.743 / 0.551 | 0.864 / 0.568 | 0.910 / 0.547 |
| auto_grown …144552896 | 0.705 / 0.536 | 0.816 / 0.540 | 0.825 / 0.546 |
| auto_grown …174252405 | 0.731 / 0.569 | 0.819 / 0.565 | 0.854 / 0.536 |

All three models read PHerc0841 in the forward order and almost nothing in the other, on every segment. There was signal
for the kit to work with.

## Criteria

| criterion | result |
|---|---|
| H1 layer order | NOT TESTABLE (0 of 3 segments decided; needs ≥ 2) |
| H2 triangle | NOT TESTABLE (no decided segment) |
| Q1 false alarm | NOT TESTABLE (0 judged windows). **The script printed "FAIL"**: its line marks FAIL whenever the count is 0/0. By the prereg it is not testable. |
| Q2 no-null | NOT TESTABLE (0/0). The script printed "PASS"; it means nothing here. |
| Q3, Q4 invented letters | NOT TESTABLE (no windowed check ran) |
| N1 natural hallucinations | NOT TESTABLE (no windowed check ran) |

## What it means

- **Fail-closed held.** On a scroll the models never saw, the kit made no wrong verdict. It said "cannot tell" three
  times.
- **It is too cautious on new data.** Readable ink (rv3 AUC up to 0.91) was there and the kit could not even fix the
  layer order. On an unseen scroll today the kit is safe but silent. This is the most important limit found so far and
  goes in the README.

## Observed after the run (not evidence)

- Had the rule not abstained, its geometry and slope would have predicted **forward** on all three segments, the order
  the labels prefer. Only the CT-match threshold (0.5) stopped it. This was seen after the labels, so it supports no
  claim. A revised rule would need its own sealed test on another unseen scroll.
- Why the triangle found no core is not yet known. It needs no labels to check, and the maps are on disk.
