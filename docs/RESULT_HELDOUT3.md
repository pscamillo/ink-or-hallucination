# RESULT — PREREG_HELDOUT3.md (sha256 c8aa6a0d…): PHerc1447 w060, a scroll no model saw, read reversed; v8-in witness

Date: 2026-10-27. Author: Paulo Sergio Camillo. Prereg sealed 2026-10-26 18:42:53 -03. Run: `fase11.py`
(md5 bcc1ce5d…), started right after the seal. Nothing was changed after the seal.

**Power cut.** The run stopped at about 20:48 during v8-in on w062 (log `fase11_parte1.log`). Every file it had written
was checked to load whole with the right shape; no v8-in file for w062 existed yet, and w060's labels had not been
opened. The same script, unchanged (same md5), was restarted at 23:30 (log `fase11_parte2.log`); it skips maps that
exist. Its w060 output before the labels is identical to part 1 (diff), except that the "invented letters" line is
not printed again because that file already existed.

## Outcome in one line

**The order was decided, before any model ran, by the geometry rule (reverse), and the labels prefer reverse: O1 PASS.
v8-in, another architecture that never saw PHerc1447, agrees with the core (W1a PASS). Q1–Q4 PASS. W1b, H2 and N1 were
not testable.** The trio-strength tie-break was not needed, so its "reverse" case is still untested.

## Order decision (before any label)

| segment | order rule | decided |
|---|---|---|
| w060 | sagitta −121.4 vx, slope +1.01, **CT match 0.81** | **reverse** (rule) |
| w062 (no labels) | sagitta −113.3 vx, slope +1.00, CT match 0.82 | reverse (rule); the dataset author also reads these layers reversed |

On PHerc0841, 0500P2 and 0009B the rule had abstained on CT match (0.16–0.35). Here the match was 0.81–0.82.

## The labels, read last (w060, certainty mask, AUC per map)

| map | stored order (forward) | reversed |
|---|---|---|
| ink_9um | 0.513 | **0.655** |
| Reader v2 | 0.524 | **0.768** |
| Reader V3 | 0.516 | **0.784** |
| v8-in (witness) | 0.489 | **0.810** |

Labels prefer **reverse** (3 of 3 villa models).

## Criteria (w060)

| criterion | result |
|---|---|
| **O1 order decision** | **PASS**: kit reverse (rule), labels reverse |
| **W1a v8-in triangle** | **PASS**: v8-in's reversed map "agrees with the whole core" of the 3 villa maps |
| W1b v8-in windows | **NOT TESTABLE**: 0 judged windows (none of v8-in's windows had stroke energy ≥ 2 × its other-order floor) |
| H2 triangle | **NOT TESTABLE**: not all 3 kit-order maps reach AUC 0.70 (ink_9um 0.655) |
| Q1 false alarm | **PASS**: 1/98 = 0.010 (≤ 0.10) |
| Q2 no-null | **PASS**: 0/98 (≤ 0.05) |
| Q3 pure invented-letter windows | **PASS**: 3/4 = 0.75 (≥ 0.60), on 4 windows |
| Q4 mixed invented-letter windows | **PASS**: 9/35 = 0.257 (≥ 0.20) |
| N1 natural hallucinations | **NOT TESTABLE**: 0 natural windows |

Informative: alarms outside the invented letters 0/20; wrong-order maps unsupported 130/175; v8-in AUC 0.810 in the
kit's order vs 0.489 in the other.

w062 (no labels, informative): order reverse by the rule; triangle core = the 3 reversed maps; windows not supported
ink_9um 1/11, Reader v2 12/281 (4.3%), Reader V3 23/431 (5.3%); v8-in "agrees with the whole core", 6 of 14 judged
windows not supported (too few to count).

## What it means

- **First case on a scroll none of the three models saw where the kit gave a verdict, and it read reversed.** The
  geometry rule decided the order before any model ran and was right. Until now its "reverse" case rested on one
  calibration segment plus symmetry.
- **A model of another architecture agrees.** v8-in, never trained on PHerc1447, falls in with the villa models'
  core in the decided order and reads the labels best of the four (0.810). Its window-level check could not be scored.
- **What it does not show.** One labelled segment. The tie-break was not used, so choosing "reverse" with it is still
  untested. The labels were drawn by the dataset author on these surfaces; whether over a model's prediction is not
  stated, so v8-in's AUC may be partly circular (W1a does not use labels).
