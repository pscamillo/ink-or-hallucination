# PREREG v2 — layer order from geometry, then triangle (ink-or-hallucination)

Date: 2026-10-23. Author: Paulo Sergio Camillo. Written BEFORE any label is read on the test segments below.
Follows PREREG_TRIANGULO.md (sha256 e4a97de5…), which FAILED on PHerc1447 w058 (RESULT_TRIANGULO_w058.md):
the wrong-order maps of all models formed a second, equally self-consistent group.

## Calibration (already seen, PHerc1447 w058 only)

- Mesh normal n = (dP/dcol) x (dP/drow) of the tifxyz grid points AWAY from the scroll centre:
  curvature (median sagitta -130 vx at D=1000) and the public umbilicus (n towards centre at 0.7% of points) agree.
- The w058 layers 00..23 grow along +n (CT sampling along n, slope +1.01 layer/voxel, corr 0.75-0.85).
- Models only see ink with the stack reversed (v8-in `--reverse`, koine `_reverse`): label AUC 0.76-0.86 vs 0.46-0.49.
- Rule taken from this: **models want the stack ordered from the OUTER face of the sheet (away from the centre) to the INNER face.**

## Tools (fixed now)

`curvatura.py` md5 4908428dd7b8ea6403c410caaa7e0ab0 (side of n from median sagitta at --D 1000; no labels, no umbilicus),
`ordem_camadas.py` md5 fdf6a7c7b7fa470457231f9783a11b0b (direction of the stored layers along n, from the public CT; --win 48 --T 16),
`inkcheck.py` md5 61ac57dfad350aea62cc1f7671d327a3 (`triangle --min-ratio 2.0 --n 300 --core-from <predicted-order maps>`, `label --n 200`; label = max over the label zarr's slices, mask = supervision mask).
Models: ink_9um official (seed43 step 60000), Reader v2 (step 40000), Reader V3; koine inference, 17-layer window
centred in the stack, `--direction both`.

## Test segments

Every segment in `villa_ink/ink-detection/labels_hf` that has (a) a local render whose size equals its label,
and (b) a public tifxyz mesh. The list is printed in the run log before any AUC is computed.
Not w058. Known contamination: these segments were used to train ink_9um and probably the Readers, so label AUCs
will be high. This tests the ORDER RULE and the triangle mechanics, not model generalisation.

A segment gets "no prediction" if curvature is undecided (|median sagitta| < 2% of D) or the CT match is weak
(median best corr < 0.5 or |slope| < 0.5). No-prediction segments are reported and count against coverage.

## Predictions and pass criteria

For each segment with a prediction, the rule names one order (forward or reverse) as correct, before labels.

P1 (order rule). For every (segment, model) pair where the two orders differ by at least 0.05 in label AUC,
the predicted order has the higher AUC. PASS if this holds in >= 90% of such pairs AND in no segment do all
three models contradict the prediction. Coverage (segments with a prediction) is reported alongside.

P2 (triangle with the order fixed). Per segment, 6 maps (3 models x 2 orders). The core may only be formed by
maps in the predicted order; wrong-order maps are probes judged against that core. PASS if, in every segment
where all three predicted-order maps have label AUC >= 0.70, those three are "consistent" and every map with
label AUC < 0.60 is "suspect" or "isolated".

Anything else is a FAIL and is reported as such. No rule is changed after labels are read.
