# PREREG — windowed check v12 on PHercParis4, blind for the windowed check (ink-or-hallucination)

Date: 2026-10-24. Author: Paulo Sergio Camillo. Written BEFORE any v11 or v12 windowed check is run on PHercParis4.

## Why

RESULT_V11 (Set A) found two weaknesses in v11, and v12 changes one thing for each.

1. **Almost no windows were judged when the mask hugs the text.** The stroke rule judged a window only if its energy
   was ≥ 1.25 × the map's own median. Inside such a mask every window has ink, so the energies are flat.
   - v12 change, `--stroke floor`: a window is judged if its energy is ≥ 2 × the median window energy of the same
     model run in the wrong layer order. That map is the same model with no readable ink, and the kit already
     produces it (the order rule needs both orders).
2. **Invented letters inside real text were missed** (mixed windows: 2/180). The real text around them keeps the
   window correlation high.
   - v12 change, `--score both`, adds an "unexplained strokes" score U. Each map's strokes are its pixels
     ≥ 0.5 × its own 99th percentile. U is the fraction of the target's stroke pixels in the window that have no
     stroke of any other map within 6 px.
   - A window is flagged if U ≥ max(0.20, median + 3 × 1.4826 × MAD of U over the judged windows of that map).
     This is an outlier relative to the map's own windows, so it is scale-free and does not depend on intensity. v10's
     residual score did depend on intensity and was rejected.
   - Final rule: unsupported = (corr test of v11 fails) OR (U flag).

## Exploratory calibration (declared; `calib_v12.py`, md5 8f4d772f…)

**Data.** Set A (12 segments, already seen in RESULT_V11) and PHerc0343P. U thresholds were scanned offline over
u_k ∈ {2, 3, 4} and u_min ∈ {0.10, 0.15, 0.20, 0.30}.

**Set A** (floor rule; FA = false alarms on the predicted-order maps):

| setting | FA | pure invented-letter windows flagged | mixed windows flagged | alarms outside the invented letters |
|---|---|---|---|---|
| corr only (= v11 with floor rule) | 0.003 | 31/55 | 3/355 | — |
| **v12, u_k 3, u_min 0.20 (chosen)** | **0.023** | **54/55** | **113/355** | **35/998** |
| u_min 0.10 | 0.049 | 54/55 | 173/355 | 63/998 |
| u_min 0.30 | 0.014 | 52/55 | 65/355 | 25/998 |

u_k barely matters; u_min sets the trade-off. The middle value u_min 0.20 was chosen, not the best-looking one.

**PHerc0343P** (energy rule, since the wrong-order maps are not available):
- U adds almost nothing there: pure 19/21 → 20/21, mixed 1/13 → 3/13, FA 0.115 → 0.115. The 343P invented letters
  were planted only where the camera shows no ink, so there are almost no mixed windows to gain.
- Median U is 0.00 for rv2, rv3, hecate and BASE, but **0.98 for v8**. v8's strokes almost never sit within 6 px of
  the other maps' strokes on 343P, which looks like a registration or scale offset of that map. It is reported as a
  limit: U assumes the maps are pixel-aligned.

## Data (blind for the windowed check)

The 8 PHercParis4 segments in `fase5/` (w00 w01 w02 w03 w05 w06 w07 w09), all predicted and confirmed "forward"
(RESULT_PARIS4). Maps, masks and the invented letters (`rv2_falsas.npy`, `fake_mask.npy`) are the ones `fase5.py`
wrote.

**Known.**
- The labels were read in `fase5.py`, for AUC and for the v10 pure/mixed split.
- The v10 windowed results are known and were buggy.
- No v11 or v12 windowed result exists for these maps.
- Labels are used here only in the last step, to split invented-letter windows into pure and mixed.
- All segments are in the models' training data (contamination).

## Tools (fixed now)

| Tool | md5 | Notes |
|---|---|---|
| `inkcheck_v12.py` | `96c8d45f6404c3e46f7ab10c2cfac948` | its defaults equal the settings below |
| `fase7.py` | `9d71482c768f2f621850d66edf99183d` | v12 run |
| `fase6.py` | `4dab3cf9…` | v11 run on the same data (Set B of PREREG_V11, criteria P4-1..3 sealed there) |
| `inkcheck_v11.py` | `ac5de45a…` | unchanged |

## Settings

```
local --stroke floor --floor <same model, wrong order> --floor-k 2.0 --score both --null swap --n 19 --min-null 10
      --tol-px 6 --ink-rel 0.5 --min-ink 0.005 --u-k 3.0 --u-min 0.20
```

Window: as in `fase5.py` (2.5 mm, from the mesh).

## Criteria (v12, PHercParis4)

- **Q1 false alarm**: pooled over 8 segments × 3 predicted-order maps, unsupported / judged ≤ 0.10.
- **Q2 fail-closed coverage**: windows with strokes but no valid null ≤ 0.05.
- **Q3 pure invented-letter windows flagged** ≥ 0.60.
- **Q4 mixed invented-letter windows flagged** ≥ 0.20. This is the new claim; Set A gave 113/355 = 0.32.

## Reported, no criterion

- Alarms outside the invented letters in the tampered map.
- Wrong-order maps as targets (judged by the 1.25 energy rule, since they have no floor).
- Per-segment numbers.
- v11 vs v12 on the same data.

Anything else is reported as it comes out. No rule is changed after the run.
