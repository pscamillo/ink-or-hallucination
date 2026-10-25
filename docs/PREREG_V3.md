# PREREG v3 — order rule replication + triangle with fixed null, on PHerc1667 (ink-or-hallucination)

Date: 2026-10-23. Author: Paulo Sergio Camillo. Written BEFORE any PHerc1667 label is read.
Follows PREREG_ORDEM.md (sha256 ea2d3b10…) and RESULT_ORDEM.md (sha256 41c29ed3…): P1 passed 18/18 on PHerc0139/0814,
P2 failed 3/6 because the block-shuffle null produced NaN when the mask covered ~1% of the image.

## What changed (only this)

`inkcheck.py` v7, md5 21398ee4cfb909e3c5fbf221f4482eeb: the null permutes only blocks that are >= 50% inside the
valid area, among themselves; real and null correlations use the same pixels (those blocks); NaN draws are dropped
and counted. Development check on PHerc0139 w041 (already seen, NOT evidence): 0 NaN draws, 135 blocks, core formed.
Rule, thresholds, models and criteria are those of PREREG_ORDEM.md, unchanged.

## Test data

PHerc1667 segments in `labels_hf` (w013 w018 w023 w028 w029 w031) with a local render of the label's size.
The 7.91 um CT is no longer public, so geometry uses the public 2.399 um mesh of each segment
(`*-on-20251217075048-2.399um.tifxyz`) with coordinates divided by 4, and level 2 of that CT (scale 4).
Scripts: `prep_1667.sh`, `geometria_v3.py` md5 87255f38a9203d3800dd55460af7c203, `fase3.py` md5 b4964c949feba87da7fdb522e03e45bb
(same logic as `geometria.py`/`fase2.py`; label/mask = max over the zarr slices).
Known contamination: PHerc1667 segments were in the training data of ink_9um and probably the Readers.

## Criteria (copied from PREREG_ORDEM.md)

No prediction if |median sagitta| < 2% of D, or CT match median corr < 0.5, or |slope| < 0.5.
P1: for every (segment, model) pair with |dAUC| >= 0.05 between orders, the predicted order is higher; PASS if
>= 90% of such pairs AND no segment has all three models against the prediction.
P2: core only from predicted-order maps (`--core-from`); PASS if, in every segment where all three predicted-order
maps have AUC >= 0.70, those three are "consistent" and every map with AUC < 0.60 is "suspect" or "isolated".
Anything else is a FAIL and is reported as such.
