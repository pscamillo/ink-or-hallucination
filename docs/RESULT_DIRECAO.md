# RESULT — PREREG_DIRECAO.md (sha256 8a218a8f…): a per-window physical signal

Date: 2026-10-25. Author: Paulo Sergio Camillo. Run: `direcao.py` (md5 84e9f724…).

**Measure.** D = stroke energy in the predicted-order map / stroke energy in the same model's wrong-order map, per
window judged by v12. It uses one model at a time and does not depend on the models agreeing.

**Groups.** As in PREREG_NATURAIS:
- natural hallucination: label ink < 0.5%;
- real ink: label ink ≥ 5%.

## D1 per set

| set | natural: n, median D [p25, p75] | real ink: n, median D [p25, p75] | AUC | Mann-Whitney p | D1 |
|---|---|---|---|---|---|
| B (PHercParis4, blind) | 367, 3.04 [1.82, 5.09] | 12659, 6.55 [3.57, 11.56] | 0.755 | 1.5e-62 | **PASS** |
| A (12 segments) | 30, 4.00 [2.06, 5.26] | 4000, 4.55 [2.71, 8.47] | 0.646 | 2.9e-3 | **FAIL** (AUC just below 0.65) |

Fraction of each group below a D threshold. These are reported only; no threshold was chosen.

| set | D < 1.5 natural / real | D < 2 natural / real | D < 3 natural / real |
|---|---|---|---|
| B | 0.17 / 0.02 | 0.28 / 0.07 | 0.48 / 0.19 |
| A | 0.17 / 0.04 | 0.23 / 0.11 | 0.47 / 0.30 |

## What this says

There is a physical signal, independent of model agreement. Strokes the models produce where the label has no ink
lose less when the layer order is reversed than real ink does.

On the blind set the separation is clear: AUC 0.76; 17% of natural hallucinations have D < 1.5, against 2% of real
ink. On Set A it points the same way but misses the AUC bar (0.646). That set has only 30 natural-hallucination
windows, and its p is still 0.003.

This is evidence for a third, independent check, not yet a rule. A D threshold, and whether D catches hallucinations
that the agreement checks miss, need their own sealed test on data not used here.

## Limits

- Contamination: the wrong-order maps keep some ink signal, which compresses D.
- Unlabelled ink inside the natural group works against the separation.
