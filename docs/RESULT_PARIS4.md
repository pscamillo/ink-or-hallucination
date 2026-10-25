# RESULT — PREREG_PARIS4.md (sha256 327693bc…): PHercParis4, dense real text

Date: 2026-10-24. Author: Paulo Sergio Camillo. Run: `geometria_p4.py`, `fase5.py` (md5 e33f511a…), inkcheck v10
(md5 7fc71286…). Labels read only in the last step.

## Coverage: 8/8

All eight labelled segments (w00 w01 w02 w03 w05 w06 w07 w09) got a prediction from geometry. All predicted
"forward".

## P1 (order rule): PASS — 24/24

| segment | ink9 f / r | rv2 f / r | rv3 f / r |
|---|---|---|---|
| w00 | 0.991 / 0.627 | 0.991 / 0.636 | 0.994 / 0.614 |
| w01 | 0.987 / 0.620 | 0.987 / 0.629 | 0.992 / 0.604 |
| w02 | 0.989 / 0.569 | 0.988 / 0.569 | 0.993 / 0.544 |
| w03 | 0.973 / 0.611 | 0.972 / 0.589 | 0.982 / 0.593 |
| w05 | 0.962 / 0.583 | 0.959 / 0.573 | 0.980 / 0.560 |
| w06 | 0.961 / 0.590 | 0.960 / 0.591 | 0.976 / 0.565 |
| w07 | 0.962 / 0.557 | 0.960 / 0.566 | 0.976 / 0.558 |
| w09 | 0.973 / 0.583 | 0.967 / 0.614 | 0.981 / 0.552 |

The wrong-order AUCs (0.54–0.64) are a little higher than on the other scrolls (0.44–0.61). PHercParis4 is in the
training data, so a wrong-order stack still keeps some ink signal.

## P2 (triangle, order fixed): PASS — 8/8

In all eight segments the core was the three predicted-order maps. The wrong-order maps printed as "suspect (agrees
with part of the core only)". By the prereg rule (starts with "suspect" or "isolated") that counts as correct.

## P3 (windowed check, v10): FAIL

| criterion | result | threshold | verdict |
|---|---|---|---|
| P3a false alarm | 217/2226 = 0.097 | ≤ 0.05 | **FAIL** |
| P3b invented letters, pure windows flagged | 20/138 = 0.145 | ≥ 0.40 | **FAIL** |

Mixed windows: 67/1087 flagged (reported, no criterion).

**Why it failed.** The cause was found label-free, before any label was read, with `diag_local.py` on w00. The
"unsupported" windows had corr 0.87–0.98 between the models but a null of +inf. The supervision mask is a narrow
band, so every far shift of the v10 null landed outside it, the null had no valid draw, and the window was read as
unsupported. This is a bug in the check, not model disagreement in dense text.

It is fixed in v11 (swap null, fail closed: no null → not judged; PREREG_V11). The v11 and v12 windowed checks have
not yet been run on these segments; they are the blind test in PREREG_V12.

## Combined record

- **Order rule from geometry: 60/60** (segment, model) pairs correct, over 20 segments of 4 scrolls: PHerc0139,
  PHerc0814, PHerc1667 and PHercParis4 (a different collection, dense text). The w058 calibration (reverse) is not
  counted. Every test segment was "forward"; the reverse case rests on the w058 calibration.
- **Triangle, after the null fix (v7): 14/14 segments correct** (PHerc1667 6/6, PHercParis4 8/8). Before the fix it
  scored 3/6 on PHerc0139/0814 (RESULT_ORDEM).

## Limits

All segments are in the models' training data (contamination). This validates the order rule and the triangle
mechanics, not model generalisation.
