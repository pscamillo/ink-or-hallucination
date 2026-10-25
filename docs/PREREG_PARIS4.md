# PREREG — PHercParis4: order rule, triangle and windowed check on dense real text (ink-or-hallucination)

Date: 2026-10-24. Author: Paulo Sergio Camillo. Written BEFORE any PHercParis4 label is read and before any
model is run on these segments.

## Why

Previous runs (RESULT_ORDEM, RESULT_V3, RESULT_V4) used PHerc0139, 0814 and 1667, where text is sparse. PHercParis4
(a different collection) has dense, legible Greek text, and the First Letters rules ask for external validation on it.
The windowed check was calibrated only on PHerc0343P (exploratory, declared): with the `corr` score it gave 0
unsupported windows on the clean maps and on windows away from planted letters, and flagged 16/28 windows of planted
letters with no real ink around; the `residual` score was rejected there (it flagged strong real ink).

## Data

The 8 labelled PHercParis4 segments in `labels_hf` (w00 w01 w02 w03 w05 w06 w07 w09; segment ids from
`roda_prep9_acc1_v2.py`), with the local render of the label's size (`renders/acc1/*_mean.zarr`, 21 layers).
Geometry from the public 2.4 um mesh of each segment and level 2 of CT 20260411134726 (coordinates / 4).
Known contamination: PHercParis4 is in the training data of all three models. This tests the order rule and the
mechanics of the checks, not model generalisation.

## Tools (fixed now)

`inkcheck.py` v10 md5 7fc712869ef89f66251e06993f3e0716; `geometria_p4.py` md5 213ebee70865e10c050923257a111403;
`fase5.py` md5 e33f511a3fb4ca2a7051368421a96a69; `curvatura.py` / `ordem_camadas.py` as in PREREG_ORDEM.
Models: ink_9um seed43 step 60000, Reader v2 step 40000, Reader V3 (koine, 17-layer window, both orders).

## Criteria

P1 and P2: exactly as in PREREG_ORDEM.md / PREREG_V3.md (order rule; triangle with `--core-from`, v7 null).

P3 (windowed check, `local --score corr --energy-k 1.25`, window = 2.5 mm from the mesh-derived pixel size):
- P3a false alarm: pooled over the 8 segments and the 3 predicted-order maps (each against the other two), the
  fraction of judged windows that come out "unsupported" is <= 0.05.
- P3b detection: invented letters (2.5 mm high, 0.2 mm stroke, ~2% of the mask, positions drawn inside the mask
  without labels, intensity = the map's own 99.5th percentile) are planted in the predicted-order Reader v2 map.
  Among windows with > 2% invented letter and < 1% real ink (real ink from the label, used only for this split
  after the run), the fraction flagged "unsupported" is >= 0.40.
- Reported, no criterion: the same fraction for mixed windows (invented letter + >= 2% real ink); the calibration
  says it will be low.

Anything else is reported as it comes out. No rule is changed after labels are read.
