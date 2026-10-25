# RESULT — PREREG_V3.md (sha256 3257845f…): PHerc1667

Date: 2026-10-23. Author: Paulo Sergio Camillo. Run: `prep_1667.sh`, `geometria_v3.py`, `fase3.py`; inkcheck v7
(md5 21398ee4…). Labels read only in the last step.

## Coverage: 6/6

All six labelled PHerc1667 segments got a prediction (CT match median corr 0.69-0.79, slope -1.00; median sagitta
-245 to -366 vx). All six predictions: "forward".

## P1 (order rule): PASS — 18/18

| segment | ink9 f / r | rv2 f / r | rv3 f / r |
|---|---|---|---|
| w013 | 0.998 / 0.562 | 0.997 / 0.536 | 0.998 / 0.528 |
| w018 | 0.980 / 0.524 | 0.963 / 0.510 | 0.979 / 0.519 |
| w023 | 0.996 / 0.536 | 0.988 / 0.519 | 0.996 / 0.525 |
| w028 | 0.999 / 0.497 | 0.898 / 0.543 | 0.940 / 0.491 |
| w029 | 0.999 / 0.606 | 0.871 / 0.572 | 0.924 / 0.556 |
| w031 | 0.998 / 0.537 | 0.997 / 0.500 | 0.998 / 0.533 |

## P2 (triangle with the order fixed): PASS — 6/6

In every segment the three predicted-order maps formed the core ("consistent") and all three wrong-order maps were
"isolated". No NaN null draws.

## Combined record (three prereg runs)

- Order rule from geometry: 36/36 (segment, model) pairs correct over 12 segments of 3 scrolls (PHerc0139, 0814,
  1667), with predictions in both directions across runs (w058 calibration: reverse; all tests: forward).
- Triangle: failed on w058 without the order rule (mirror group); failed 3/6 on PHerc0139/0814 because of the null
  bug; passed 6/6 on PHerc1667 after the fix.

## Limits (stated plainly)

- Contamination: these segments are in the training data of ink_9um and probably the Readers (AUC ~0.9-1.0).
  This validates the order rule and the triangle mechanics, not that the models generalise.
- Within this run every prediction was "forward"; the reverse case rests on the w058 calibration only.
- The maps the triangle had to reject were wrong-order maps. It has not yet been tested on a map that is blind or
  hallucinating in the right order (e.g. a weak model, or ink invented by a large window). That is the next test.
