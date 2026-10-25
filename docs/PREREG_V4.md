# PREREG v4 — does the triangle catch a map that hallucinates in the RIGHT layer order? (ink-or-hallucination)

Date: 2026-10-23. Author: Paulo Sergio Camillo. Written BEFORE any probe map below is computed.
Follows RESULT_V3.md (sha256 baf3e9d0…): on PHerc1667 the triangle rejected wrong-order maps 6/6, but it was never
asked to reject a blind or hallucinating map in the correct order.

## Data and honesty note

The six PHerc1667 segments of v3 (labels already read in v3). The three good maps (ink9, Reader v2, Reader V3,
forward = predicted order) are reused unchanged from v3. The probes are new and are built without labels; labels are
used only at the end, to measure each probe's AUC. Tools: `inkcheck.py` v7 md5 21398ee4cfb909e3c5fbf221f4482eeb,
`fase4.py` md5 018bfb7214d681f4d1650ec8aff3e447, `triangle --min-ratio 2.0 --n 300 --core-from ink9_f rv2_f rv3_f`.

## Probes

- `cego_letras`: the wrong-order ink9 map (blind) with synthetic letter-like strokes planted inside the mask, total
  stroke area ~ the area where the good ink9 map is > 0.5. A blind model that "writes" plausible letters.
- `embaralhado` (w028, w029, w031 only): ink9 run in the predicted order on the stack with its layers in a fixed random
  order. A real model, right order of the call, wrong input.
- `parcial`: the GOOD ink9 map plus planted strokes covering ~30% of its ink area. Real ink plus invented letters.

Letters: 2-4 strokes (lines, arcs), height 40*f px, stroke 6*f px (f = the triangle's downsample), fixed seed per segment.

## Criteria

H1 (PASS/FAIL): in every segment the three good maps stay "consistent", and every `cego_letras` / `embaralhado` map
with label AUC < 0.60 is "suspect" or "isolated".

H2 (stated prediction of a limit, not pass/fail for the kit): `parcial` will come out "consistent", because the
triangle judges whole maps and 70% real ink still agrees with the core. If so, the kit must say plainly that it does
not catch local invented letters inside a map that is mostly right; that needs a windowed check.

Anything else is reported as it comes out. No rule is changed after the run.
