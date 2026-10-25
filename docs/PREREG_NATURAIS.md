# PREREG — does the windowed check flag the hallucinations the models make on their own? (ink-or-hallucination)

Date: 2026-10-24. Author: Paulo Sergio Camillo. Written while `fase7.py` (PREREG_V12) is still running, BEFORE any
of its .npz files is compared with a label, and before the Set A good-map windows of `calib_v12.py` were ever split
by label.

## Why

Every detection test so far used invented letters that we planted. This test uses the models' own mistakes.

- **Natural hallucination window.** A judged window (the map has strokes: energy ≥ 2 × the wrong-order floor, v12)
  where the ink label has almost no ink: label ink fraction in the window < 0.005, inside the supervision mask.
- **Real-ink window.** A judged window with label ink fraction ≥ 0.05.

If the check sees hallucinations, it should flag the first kind more often than the second.

## Data

- **Set B (PHercParis4, blind).** The v12 .npz files from `fase7.py`, for the predicted-order ink9, rv2 and rv3
  maps of the 8 segments.
- **Set A (12 segments).** The .npz files from `calib_v12.py` for the same three maps. Its U thresholds were scanned
  on invented letters and on false alarm counts. The split by label of these windows was never computed.

## Rule

The v12 rule, recomputed from the .npz files with the sealed settings: unsupported = corr ≤ null max (swap null)
OR U ≥ max(0.20, median + 3 × 1.4826 × MAD). Script: `naturais.py`, md5 below.

## Criterion (N1, for each set)

At least 20 natural-hallucination windows, AND their unsupported rate ≥ 2 × the unsupported rate of the real-ink
windows, AND a one-sided Fisher exact test with p < 0.01.

## Known limits, stated now

- **The labels are not complete.** Some "natural hallucination" windows will contain real ink nobody labelled, which
  works against the check.
- **Contamination.** The segments are in the training data, so natural mistakes may be rarer than on a new scroll.

Anything else is reported as it comes out.

`naturais.py` md5: 9deb1bc0bd1f213421a92dcfa4ef8e4a
