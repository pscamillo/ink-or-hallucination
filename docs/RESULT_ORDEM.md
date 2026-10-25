# RESULT — PREREG_ORDEM.md (sha256 ea2d3b10…): layer order from geometry, then triangle

Date: 2026-10-23. Author: Paulo Sergio Camillo. Run: `geometria.py` then `fase2.py`; labels read only in the last step.

## Coverage

8 labelled segments had a local render matching the label and a public mesh (PHerc0139 w028 w029 w035 w039 w040
w041 w043, PHerc0814 46527). 6 got a prediction; w028 and w029 did not (CT match corr 0.05: render and mesh do not
correspond). PHerc1667 (6 segments) was not run: its 7.91 um CT is no longer public.
All 6 predictions were "forward" (stored layers grow towards the inside), the opposite of the w058 calibration.

## P1 (order rule): PASS

18/18 (segment, model) pairs: the order predicted from geometry is the one that sees ink.
Predicted order AUC 0.966-1.000; other order 0.442-0.564. No segment with all three models against the prediction.
Contamination as stated in the prereg: these segments were in the training data, hence the very high AUCs.

| segment | ink9 f / r | rv2 f / r | rv3 f / r |
|---|---|---|---|
| 0139 w035 | 0.997 / 0.559 | 0.993 / 0.540 | 0.995 / 0.557 |
| 0139 w039 | 0.998 / 0.529 | 0.995 / 0.522 | 0.997 / 0.550 |
| 0139 w040 | 0.991 / 0.522 | 0.966 / 0.498 | 0.981 / 0.482 |
| 0139 w041 | 0.999 / 0.538 | 0.995 / 0.544 | 0.998 / 0.509 |
| 0139 w043 | 0.999 / 0.537 | 0.997 / 0.525 | 0.998 / 0.547 |
| 0814 46527 | 1.000 / 0.564 | 0.985 / 0.477 | 0.995 / 0.442 |

## P2 (triangle with the order fixed): FAIL

3/6 eligible segments correct (w035, w040, 0814: the three predicted-order maps "consistent", all wrong-order maps
"isolated"). w039, w041, w043: "unresolved (no 3 maps agree pairwise)", although the predicted-order maps
correlate at 0.90-0.97 with each other.

## Diagnosis (after the fact; does not change the verdict)

In the three failed segments `null_max` is NaN for every pair, so no pair can meet "corr >= 2 x null_max".
Cause: the block-shuffle null permutes blocks over the WHOLE image, while the supervision mask covers only part of
it. Draws where only empty (outside-mask, zero) blocks land in the valid area have zero variance, so corr = NaN,
and `max` propagates the NaN. Even where it does not produce NaN, mixing in empty blocks makes the null too easy.
This did not show on 343P or w058, where the valid area covers most of the image.

This is a bug in the null, not in the maps. A fix (shuffle only blocks inside the valid area; ignore NaN draws)
needs a new prereg and segments whose labels have not been read. PHerc1667 (6 labelled segments) is the candidate,
via its public 2.4 um mesh and CT.
