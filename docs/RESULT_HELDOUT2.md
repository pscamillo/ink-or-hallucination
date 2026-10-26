# RESULT — PREREG_HELDOUT2.md (sha256 bcb14c8e…): revised layer-order decision on PHerc0500P2 and PHerc0009B

Date: 2026-10-26. Author: Paulo Sergio Camillo. Prereg sealed 2026-10-26 13:17:08 -03. Run: `baixa_heldout2.py`
(md5 9c1d3f69…) then `fase10.py` (md5 f71405f8…), started right after the seal, log `fase10.log`. Nothing was changed
after the seal.

## Outcome in one line

**The revised decision decided both segments and was right on both (O1 PASS); H1 passed for the first time on scrolls
none of the models saw; Q1–Q4 passed; H2 FAILED on PHerc0009B; N1 was not testable.**

## Order decision, per segment (before any label)

| segment | registration (CT vs CT) | order rule | triangle fallback | trio strength (new) | kit |
|---|---|---|---|---|---|
| PHerc0500P2 `20250825181859--1` | shift (−8, −8) px, peak 0.889 → applied | abstained: sagitta 56.3 vx, slope −1.01, **CT match 0.265** | no core | S_f 0.385, S_r 0.294, **ratio 1.31** → forward | forward |
| PHerc0009B `…auto_grown_20250919055754487_inp_hr` | (−5, −8), 0.839 → applied | abstained: 13.9, −0.87, **0.16** | no core | S_f 0.452, S_r 0.177, **ratio 2.56** → forward | forward |

As on PHerc0841, the order rule abstained on its CT-match threshold and the triangle found no unique core. Both
segments were decided by the new step.

## The labels, read last (AUC per map, official labels, registered)

| segment | ink9 fwd / rev | rv2 fwd / rev | rv3 fwd / rev | labels prefer |
|---|---|---|---|---|
| PHerc0500P2 | 0.772 / 0.555 | 0.878 / 0.552 | 0.900 / 0.572 | forward |
| PHerc0009B | 0.812 / 0.544 | 0.927 / 0.578 | 0.947 / 0.589 | forward |

## Criteria

| criterion | result |
|---|---|
| **O1 revised decision** | **PASS**: 2 of 2 decided, both forward, both match the labels |
| H1 layer order | **PASS**: 6/6 (segment, model) pairs favour the kit's order; 0 segments with all 3 against; 2/2 decided |
| H2 triangle | **FAIL**: 1 of 2 eligible segments correct (below) |
| Q1 false alarm | **PASS**: 30/539 = 0.056 (≤ 0.10) |
| Q2 no-null | **PASS**: 0/539 = 0.000 (≤ 0.05) |
| Q3 pure invented-letter windows | **PASS**: 4/4 = 1.000 (≥ 0.60), on only 4 windows |
| Q4 mixed invented-letter windows | **PASS**: 20/69 = 0.290 (≥ 0.20) |
| N1 natural hallucinations | **NOT TESTABLE**: 16 natural windows (< 20). For the record: 5/16 = 0.312 unsupported vs 23/480 = 0.048 on real ink, Fisher p 1.1e-3 |

Informative: 0/173 alarms outside the invented letters; 215/280 wrong-order windows unsupported.

**Why H2 failed.** On PHerc0009B every predicted-order map was "consistent", but the Reader V3 reverse map (AUC 0.589,
below 0.60) came out as "agrees with the whole core", not "suspect" or "isolated" as H2 requires. On PHerc0500P2 H2
held. This is the same root as the mirror cores: the models are related, and a wrong-order map can still resemble
the right-order ones. The triangle verdict on a wrong-order map is therefore not reliable on its own; the order decision
and the windowed check are what carried this run.

## What it means

- **On these two unseen scrolls the kit is no longer silent.** Where PHerc0841 got no verdict at all, the revised
  decision fixed the layer order on both segments, correctly, and the windowed check then behaved as sealed (low false
  alarm, invented letters caught, nothing flagged outside them).
- **It is a small test.** Two segments, two scrolls: 2 of 2 is consistent with a rule that works and does not measure
  an error rate. PHerc0500P2 was decided at ratio 1.31, close to the 1.25 threshold.
- **Reverse is still untested.** Both segments read forward, like every case the tie-break has decided so far.
- **The labels may come from a model** (stated in the prereg), so O1 and H1 measure agreement with those labels.
- **H2 is a real failure** and stays in the record.
