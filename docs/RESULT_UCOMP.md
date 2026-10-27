# RESULT — PREREG_UCOMP.md (sha256 fd3aed06…): component-level unexplained strokes (v13), blind, six segments off the training data

Date: 2026-10-27. Author: Paulo Sergio Camillo. Prereg sealed 2026-10-27 09:35:57 -03. Run: `fase12.py` (md5
7d292819…), `inkcheck_v13.py` (md5 d313e1df…), started right after the seal, finished without interruption. Nothing
was changed after the seal.

## Outcome in one line

**FAIL. v13 does not replace v12.** It caught more invented letters inside real text (39.6% vs 33.7%), but by less
than the 10 points required (C1 FAIL), and it raised the false alarm to 6.4%, above the 5% bar (C2 FAIL).

## Layer order (before any check)

| segment | order | how |
|---|---|---|
| PHerc0841 w00 | forward | guarded tie-break, ratio 1.70 (S_f 0.450, S_r 0.265), guard did not fire |
| PHerc0841 auto_grown_…144552896 | forward | guarded tie-break, ratio 1.71, guard did not fire |
| PHerc0841 auto_grown_…174252405 | forward | guarded tie-break, ratio 1.56, guard did not fire |
| PHerc0500P2, PHerc0009B | forward | sealed in RESULT_HELDOUT2 |
| PHerc1447 w060 | reverse | sealed in RESULT_HELDOUT3 |

All six were decided; on PHerc0841 the labels prefer forward (RESULT_HELDOUT0841).

## Criteria (pooled over the six segments)

| criterion | v12 | v13 | threshold | verdict |
|---|---|---|---|---|
| **C1** mixed invented letters | 57/169 = 0.337 | 67/169 = **0.396** | ≥ 0.35 and ≥ v12 + 0.10 | **FAIL** (+0.059) |
| **C2** false alarm, untouched maps | 43/928 = 0.046 | 59/928 = **0.064** | ≤ 0.05 and ≤ v12 + 0.02 | **FAIL** (above 0.05) |
| C3 pure invented letters | 10/11 | 10/11 = 0.909 | ≥ 0.60 | PASS |

The script's last line prints the adoption rule in brackets ("C1 and C2 PASS, C3 not FAIL"); that is the rule, not
the outcome. The outcome is "does NOT replace".

Informative: worst single map 0.200 for both (PHerc0009B, ink_9um, 5 of 25 windows). Natural hallucinations vs real
ink: v12 0.350 vs 0.037 (Fisher p 9e-6), v13 0.350 vs 0.055 (p 1e-4).

## Per segment

| segment | false alarm v12 → v13 | pure | mixed v12 → v13 |
|---|---|---|---|
| 0841 w00 | 7/121 → 7/121 | 2/2 | 7/25 → 9/25 |
| 0841 …144552896 | 5/100 → 7/100 | – | 2/9 → 2/9 |
| 0841 …174252405 | 0/70 → 4/70 | – | 6/22 → 7/22 |
| 0500P2 | 7/218 → 17/218 | 4/4 | 13/32 → 15/32 |
| 0009B | 23/321 → 23/321 | 1/1 | 15/41 → 18/41 |
| 1447 w060 | 1/98 → 1/98 | 3/4 | 14/40 → 16/40 |

## Why it failed

- **The new flags fell mostly on Reader V3's untouched maps** (B flag 4 + 4 + 14 + 8 = 30 windows), and they made all
  16 of the extra false alarms. Reader V3 draws strokes the other two models do not. On PHercParis4, a training
  scroll where the three agree closely, this cost under 1 point; off the training data, where they agree less, it
  cost 1.8 points.
- **The starting point was different.** On these segments v12's false alarm was already 4.6% (PHercParis4: 2.7%),
  so there was little room under 5%, and v12 already caught 33.7% of the mixed windows (PHercParis4: 26%), so a
  10-point gain was harder.
- The development set did not predict this. The minimum area chosen there was the right kind of control, but it
  was set on a scroll where the models agree more than they do on new scrolls.

## What it means

- **v12 stays in the kit, unchanged.** The weak spot it has (most invented letters inside real text are missed) is
  still there; this attempt did not fix it under the sealed bar.
- On new scrolls the direction of the effect held (more letters caught in 5 of 6 segments), but it came with a cost
  in false alarms that the sealed criteria do not accept.
- **Side result, on the tie-break guard (NOTE_2026-10-27_TIEBREAK_GUARD):** the three PHerc0841 triangles that note
  could not re-check were recomputed here: the guard did not fire on any of them and the order is forward, as the
  labels prefer. PHerc0841 is the tie-break's calibration scroll, so this checks the guard, not the tie-break.
- One planting per segment and small counts per segment (9–41 mixed windows): these are window counts, not
  independent letters.
