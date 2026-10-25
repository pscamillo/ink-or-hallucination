# RESULT — PREREG_ESTRESSE.md (sha256 ed0bc890…): the kit with weakened maps

Date: 2026-10-25. Author: Paulo Sergio Camillo. Run: `fase8.py` (md5 062c7b84…), core `inkcheck_v12.py` (md5 96c8d45f…).

**Setup.**
- Segments: PHercParis4 w02, w00 and w03, the three smallest renders, chosen by the rule in `fase8.py`.
- Degradation: Gaussian noise on the render at σ = 0.5 and 1.0 × the render std (render std ≈ 35.5–36.3).
- The three models were run on the noisy render in both orders. Labels were read only in the last step.

## Criteria: 2/2 PASS

| criterion | result | verdict |
|---|---|---|
| S1 fail-safe triangle: no wrong-order map in the core or "consistent", any level | 0 of 6 (segment, level) cases; all 6 cores were the three forward maps | **PASS** |
| S2 windowed false alarm ≤ 0.10, level 0.5 | 93/2262 = 0.041 | **PASS** |
| S2 windowed false alarm ≤ 0.10, level 1.0 | 61/1757 = 0.035 | **PASS** |

## How weak the maps got (AUC)

| segment, level | ink9 f / r | rv2 f / r | rv3 f / r |
|---|---|---|---|
| w02, 0.5 | 0.955 / 0.530 | 0.976 / 0.557 | 0.991 / 0.576 |
| w02, 1.0 | 0.815 / 0.544 | 0.885 / 0.554 | 0.944 / 0.573 |
| w00, 0.5 | 0.974 / 0.565 | 0.984 / 0.568 | 0.993 / 0.554 |
| w00, 1.0 | 0.870 / 0.543 | 0.946 / 0.568 | 0.974 / 0.543 |
| w03, 0.5 | 0.922 / 0.528 | 0.949 / 0.532 | 0.974 / 0.525 |
| w03, 1.0 | 0.791 / 0.518 | 0.864 / 0.544 | 0.918 / 0.533 |

Mean forward AUC was 0.950 / 0.970 / 0.986 at level 0.5 and 0.825 / 0.898 / 0.945 at level 1.0. Before
degradation these segments were at 0.97–0.99. In all 18 (segment, level, model) cases the predicted order kept a
higher AUC than the other order.

## Reported, no criterion

| level | pure invented-letter windows flagged | mixed flagged | natural hallucination: unsupported | real ink: unsupported |
|---|---|---|---|---|
| 0.5 | 13/13 | 48/212 (23%) | 6/30 (20%) | 75/2113 (3.5%) |
| 1.0 | 13/13 | 42/212 (20%) | 6/31 (19%) | 45/1637 (2.7%) |

## What this says

With maps down to AUC 0.79–0.94, the kit kept its behaviour:
- the triangle never put a wrong-order map in the core;
- the windowed false alarm stayed under 5%;
- every isolated invented letter was still caught;
- about one in five invented letters inside real text was still caught;
- natural hallucinations were still flagged several times more often than real ink.

## Limits

- Noise on the render is one kind of "harder scroll", not all of them.
- The weakest map here (AUC 0.79) is still far better than a model that cannot read a scroll at all. Below this the
  kit is untested; there it should say "unresolved" rather than be trusted.
- 3 segments × 2 levels.
