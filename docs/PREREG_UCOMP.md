# PREREG — component-level unexplained strokes (windowed check v13), blind on six segments off the training data (ink-or-hallucination)

Date: 2026-10-27. Author: Paulo Sergio Camillo. Written BEFORE v13 is run on any of the test segments, and before
the new invented letters are planted in them.

## Why

The windowed check v12 misses most invented letters that sit on real text: 26% caught on PHercParis4 (RESULT_V12),
29% on PHerc0500P2 + 0009B (RESULT_HELDOUT2), 26% on PHerc1447 w060 (RESULT_HELDOUT3). Its U score is the
*fraction* of a window's stroke pixels that no other map explains, so the real strokes around an invented letter
dilute it.

## What changes (only this)

v13 adds one flag to v12. Per judged window, **B = the area of the largest connected piece** (8-connected) of the
target's stroke pixels that no other map explains: the same strokes, the same 6 px tolerance and the same "ink
window" rule as v12's U. A window is flagged if B ≥ max(**0.04** × window area, median + **3** × 1.4826 MAD of B over
that map's ink windows). Final: unsupported = v12 unsupported OR the B flag. Everything else is v12 unchanged.

**Where 0.04 comes from** (development, `ucomp_dev.py`, PHercParis4 only, seen many times; not evidence):

| min. area | false alarm | pure | mixed | worst single map |
|---|---|---|---|---|
| v12 | 0.027 | 81/81 | 0.263 | |
| 0.02 | 0.066 | 81/81 | 0.655 | 0.149 |
| 0.03 | 0.045 | 81/81 | 0.535 | 0.121 |
| **0.04** | **0.035** | 81/81 | **0.417** | 0.107 |
| 0.05 | 0.030 | 81/81 | 0.360 | 0.100 |
| 0.08 | 0.027 | 81/81 | 0.287 | 0.082 |

k (3 to 6) made almost no difference once the minimum area was ≥ 0.02. 0.04 was chosen as the value that keeps
the false alarm within 1 point of v12 and still raises the mixed detection by more than 10 points. The choice was
made by looking at this table; the test below is on data v13 has not seen.

## Test data: six labelled segments, four scrolls, off the training data

| segment | scroll | maps already on disk | layer order |
|---|---|---|---|
| w00, auto_grown_…144552896, auto_grown_…174252405 | PHerc0841 | `fase9/` | decided by the kit as it now stands (rule, triangle fallback, guarded tie-break); if unresolved, the segment is skipped |
| `20250825181859--1` | PHerc0500P2 | `fase10/` | forward (RESULT_HELDOUT2, tie-break) |
| `20250919125754-auto_grown_…` | PHerc0009B | `fase10/` | forward (RESULT_HELDOUT2, tie-break) |
| w060 | PHerc1447 | `fase11/` | reverse (RESULT_HELDOUT3, geometry rule) |

None of the three villa models trained on these segments (Reader v2/V3 saw other segments of 0500P2 and 0009B,
ERRATUM_HELDOUT2). The windowed check never ran on PHerc0841. On the other five, v12 ran once with **other**
invented letters; v13 never ran on any of them.

**New invented letters:** the same `plant()` and parameters as fase5/fase10 (2.5 mm high, 0.2 mm stroke, 2% of
the mask, intensity = the map's 99.5th percentile), in Reader v2 in the decided order, with a **new seed**:
crc32(segment name + "|ucomp"). Nothing is planted twice; no planting from the earlier runs is reused.

## Procedure (`fase12.py`)

1. Layer order as in the table (PHerc0841: the kit's own decision, recorded before step 2).
2. For each decided segment: v12 and v13 on each decided-order map against the other two (floor = the same model in
   the other order); then v12 and v13 on the tampered Reader v2. v13 reports v12's state as well, from the same run.
3. Only then the labels, used **only** to split the planted-letter windows into pure (label ink < 1%) and mixed
   (label ink ≥ 2%), and windows into natural-hallucination / real-ink, exactly as fase10.py.

## Criteria (pooled over the decided segments)

- **C1 (main), mixed invented letters:** v13 flags ≥ 0.35 of the judged mixed windows **and** ≥ v12 + 0.10 on the
  same windows: PASS; else FAIL. Fewer than 20 judged mixed windows: NOT TESTABLE.
- **C2, false alarm on the untouched decided-order maps:** v13 ≤ 0.05 **and** ≤ v12 + 0.02: PASS; else FAIL.
- **C3, pure invented letters:** v13 ≥ 0.60 of the judged pure windows: PASS; else FAIL. Fewer than 10: NOT TESTABLE.
- Informative, no criterion: the worst single map's false alarm (v12 and v13); natural hallucinations vs real ink
  (v12 and v13); per-segment counts.

**What follows from it:** v13 replaces v12 in the kit only if C1 and C2 both PASS (and C3 is not FAIL). Otherwise v12
stays, and the result is published as it comes out.

## Known limits, stated now

- **The letters are synthetic.** Strokes drawn at the map's own 99.5th percentile; real hallucinations can be fainter
  or shaped like real letters. C1 measures planted letters, not model hallucinations.
- **The minimum area was chosen on PHercParis4**, a training scroll with dense text, by looking at the table above.
- **Five of the six segments were seen** by v12 and their labels were read in earlier runs. The new letters, their
  positions and the v13 flag are new; the maps are not.
- One planting per segment: the counts are windows, not independent letters, and neighbouring windows overlap.

Every number is reported as it comes out, pass or fail. No rule is changed after the seal. A crash is fixed in a
dated addendum before rerunning.

## Tools

| Tool | md5 |
|---|---|
| `fase12.py` | `7d292819193b1da6f007fe3124c4f6fb` |
| `inkcheck_v13.py` | `d313e1df4394a55874d8f28dee1e9370` (= inkcheck_v12.py + the B flag; with --blob-min 0 it gives v12's state exactly, checked on a synthetic segment) |
| `ucomp_dev.py` (development only) | `099be01fdb6df9899167016ebe5f9127` |
