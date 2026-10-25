# RESULT — PREREG_V12 (sha256 3a8f3c8a…), PREREG_V11 Set B (sha256 c0a27834…) and PREREG_NATURAIS (sha256 0083c589…)

Date: 2026-10-24. Author: Paulo Sergio Camillo.

Runs:
- `fase7.py` (md5 9d71482c…) with `inkcheck_v12.py` (md5 96c8d45f…);
- `fase6.py` (md5 4dab3cf9…) with `inkcheck_v11.py` (md5 ac5de45a…);
- `naturais.py` (md5 9deb1bc0…).

Data: the 8 PHercParis4 segments. No v11 or v12 windowed check had been run on them before. Labels were used only in
the last step: for the pure/mixed split of the invented letters and for the natural-hallucination split.

## v12 on PHercParis4 (PREREG_V12): 4/4 PASS

| criterion | result | threshold | verdict |
|---|---|---|---|
| Q1 false alarm, predicted-order maps | 365/13773 = 0.027 | ≤ 0.10 | **PASS** |
| Q2 windows with strokes but no valid null | 0/13773 = 0.000 | ≤ 0.05 | **PASS** |
| Q3 invented letters, pure windows flagged | 81/81 = 1.000 | ≥ 0.60 | **PASS** |
| Q4 invented letters inside real text (mixed windows) flagged | 274/1042 = 0.263 | ≥ 0.20 | **PASS** |

Reported, no criterion:
- Alarms outside the invented letters in the tampered map: 116/3288 = 0.035.
- Wrong-order maps checked against the two predicted-order maps: 4576/5608 = 0.82 unsupported.

| segment | pure flagged | mixed flagged |
|---|---|---|
| w00 | 8/8 | 23/70 |
| w01 | 5/5 | 25/90 |
| w02 | 4/4 | 19/64 |
| w03 | 1/1 | 11/78 |
| w05 | 54/54 | 121/358 |
| w06 | 4/4 | 28/121 |
| w07 | 1/1 | 31/195 |
| w09 | 4/4 | 16/66 |

## v11 on the same data (PREREG_V11, Set B): 3/3 PASS

| criterion | result | threshold | verdict |
|---|---|---|---|
| P4-1 false alarm | 0/2226 = 0.000 | ≤ 0.10 | **PASS** |
| P4-2 windows without a null | 0/2226 = 0.000 | ≤ 0.05 | **PASS** |
| P4-3 pure invented-letter windows flagged | 25/35 = 0.714 | ≥ 0.60 | **PASS** |

Reported, no criterion: mixed 7/532 = 0.013; alarms outside the invented letters 0/201; wrong-order maps 4575/5608.

The Set A rerun inside the same `fase6.py` call reproduced RESULT_V11 exactly: 1/851, 3/854 and 10/19.

## v11 vs v12 on PHercParis4

| | v11 | v12 |
|---|---|---|
| windows judged on the predicted-order maps | 2226 | 13773 (6.2×) |
| false alarm | 0.000 | 0.027 |
| pure invented-letter windows flagged | 25/35 | 81/81 |
| mixed invented-letter windows flagged | 7/532 (1.3%) | 274/1042 (26%) |

v12 judges six times more of the text, catches every isolated invented letter, and catches one in four invented
letters inside real text, against one in eighty for v11. The price is 2.7% false alarm, against 0%.

## Natural hallucinations (PREREG_NATURAIS): PASS on both sets

A natural-hallucination window is one where a model shows strokes above its own wrong-order floor, but the label
has < 0.5% ink.

| set | natural hallucination: unsupported | real ink (≥ 5% label ink): unsupported | ratio | Fisher p | N1 |
|---|---|---|---|---|---|
| B (PHercParis4, blind) | 104/367 = 0.283 | 202/12659 = 0.016 | 17.8× | 9.7e-87 | **PASS** |
| A (12 segments) | 4/30 = 0.133 | 69/4000 = 0.017 | 7.7× | 1.9e-3 | **PASS** |

Per model on Set B:

| model | natural hallucination | real ink |
|---|---|---|
| ink9 | 19/50 | 69/4173 |
| rv2 | 75/159 | 56/4239 |
| rv3 | 10/158 | 77/4247 |

This is the first test on mistakes the models made on their own, not on letters we planted. The windowed check
flags them 18 times more often than real ink.

**The labels are incomplete**, so some "natural hallucination" windows may hold real ink nobody labelled. That works
against the check, so the true separation can only be larger.

Most of these windows come from rv2. rv3's own strokes in no-label areas are mostly confirmed by the other models
(10/158). That may be unlabelled ink, or a pattern rv3 shares with the others. The check cannot tell these apart;
see the limits.

## Limits

- **Contamination.** All segments are in the models' training data.
- **Agreement, not truth.** A stroke all models share passes. rv3's confirmed no-label strokes above are exactly
  that case.
- **Most invented letters inside real text are still missed:** 74% of mixed windows.
