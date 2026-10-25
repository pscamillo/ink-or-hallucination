# RESULT — triangle check on PHerc1447 w058 (prereg PREREG_TRIANGULO.md, sha256 e4a97de5…)

Date: 2026-10-23. Author: Paulo Sergio Camillo.
Code: `inkcheck.py` md5 5e43074cfdd2ee982071f99129c54127 (`triangle --min-ratio 2.0 --n 300`, band 2 20, mask `mask.png`).
Maps (4512 x 8184, 24 layers, window 3-20): v8-in, ink_9um official, Reader v2, Reader V3, each in both layer orders.
Labels were read only after the triangle had printed its verdict.

## Outcome: FAIL (as defined in the prereg)

Every map came out "unresolved": two different groups of 4 maps agree pairwise, so no unique core.
The prereg says "unresolved for all maps counts as a fail of usefulness". It is reported as a fail.

## What the data shows

| group | maps | pairwise corr / null_max | label AUC |
|---|---|---|---|
| A | v8, ink9_inv, rv2_inv, rv3_inv | 6.1x - 16.2x | 0.76, 0.86, 0.84, 0.85 |
| B | v8_inv, ink9, rv2, rv3 | 3.4x - 13.4x | 0.49, 0.48, 0.48, 0.46 |

Cross-group pairs: all below 2x (most negative), except ink9 x ink9_inv at exactly 2.0x.

- The split itself is perfect: the label-free check put every seeing map in one group and every blind map
  in the other. It cannot say which group is the ink.
- The blind group is not noise. Four wrong-order maps from three model families agree with each other as
  strongly as the seeing maps do (rv2 x rv3 wrong order: corr 0.80). Agreement between models, even
  across families, is not evidence of ink by itself.
- Cause: every model was given in both orders, so the wrong orders form a mirror-image group that is
  just as self-consistent. The 343P calibration had only one reversed map, so this failure did not show there.
- Side note: on these layers the koine "forward" output is the wrong order for all three koine models
  (the same way v8-in needs `--reverse` here).

## Not done

No tie-break rule is applied after the fact (e.g. "the stronger group wins": group A is somewhat stronger,
but that rule was not sealed). Any fix (such as fixing the layer order from the mesh geometry before
comparing) needs a new prereg and a segment other than w058, which is now spent.
