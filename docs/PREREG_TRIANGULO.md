# PREREG — triangle check with effect-size threshold (ink-or-hallucination)

Date: 2026-10-23. Author: Paulo Sergio Camillo. Written BEFORE any run on the test data below.

## What was seen on the calibration data (PHerc0343P, KLAVIS camera truth)

`inkcheck.py` (md5 149b7fd6e24a431c750ddc94f159996f), `triangle`, `--band 2 20`, `--n 300`, mask `valid.png`.
Models: v8-in (our run, correct order), Hecate 9.6 um, BASE (our run), Reader v2, team 2.2 um map.

- Pairs among the four maps that see ink (camera AUC 0.72-0.91): corr 0.14-0.46, i.e. 4.4x-10x the
  block-shuffle null max.
- BASE (camera AUC 0.539, chance): corr with v8-in 3.6x the null max, with Hecate 1.3x, Reader v2 1.5x,
  team 2.2 um 1.5x.
- With p < 0.01 alone, every pair passes (millions of pixels make tiny effects significant), so the
  core wrongly includes BASE. The criterion below is chosen from this calibration data.

## Criterion fixed now (not to be changed after seeing the test data)

A pair AGREES if p < 0.01 AND corr >= 2.0 x null_max (same block-shuffle null, same band 2 20 px).
Core = the unique largest set of 3+ maps that all agree pairwise; ties or no set of 3 -> "unresolved".
Verdicts: in core = consistent; agrees with part of the core = suspect; with none = isolated.

## Test (independent data, run after this file is hashed)

Data: PHerc1447 w058 (human ink labels, `v8in/surfaces/w058/labels/inklabels.png`, mask `mask.png`).
Maps: whichever of v8-in, Hecate, Reader v2, BASE can be run on the w058 layers, both orders where possible.
Truth used only AFTER the triangle verdict: per-map AUC vs the label (`inkcheck.py label`).

Pass (the label-free verdict matches the truth):
- every map with label AUC >= 0.70 and p < 0.01 is "consistent", AND
- every map with label AUC < 0.60 (or a reversed-order map) is "suspect" or "isolated".
Anything else is a FAIL and is reported as such. "unresolved" for all maps counts as a fail of usefulness.

Known caveat, stated in advance: some models may have seen PHerc1447 in training (BASE family likely).
A seeing-but-contaminated model passing is not evidence for the check; a blind map being flagged is.
