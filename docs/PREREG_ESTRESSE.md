# PREREG — stress test: does the kit stay honest when the maps are weak? (ink-or-hallucination)

Date: 2026-10-25. Author: Paulo Sergio Camillo. Written BEFORE any degraded render or map exists.

## Why

Every test segment is in the models' training data, so the maps the kit has seen are unusually clean, with AUC
0.96–1.00. On a new scroll the maps will be weaker. We cannot get unlabelled-by-training labelled data before the
deadline, so we make the maps weaker on purpose: we degrade the model INPUT, the render, and run the real models on
it.

The property that matters most is fail-safe behaviour. With weak maps the kit may say "unresolved", but it must
not give false confidence.

## Data and degradation

- **Segments.** The 3 PHercParis4 segments with the smallest render (H × W), chosen by that rule in `fase8.py`.
  All three are predicted "forward" (RESULT_PARIS4).
- **Noise.** Gaussian noise added to every layer of the render at two levels, σ = 0.5 and σ = 1.0 × the render's
  std over mapped voxels (middle layer). Unmapped voxels (0) stay 0. The seed is fixed per segment and level.
- **Models.** ink9, Reader v2, Reader V3, in both orders, with exactly the `fase5.py` inference settings.

## Kit settings

- Triangle (v12 core) with `--core-from` the forward maps.
- Windowed check v12 as sealed in PREREG_V12 (floor = same model, wrong order).
- Invented letters in the noisy forward rv2: same `plant()` and seed as `fase5.py`.

Labels are read only in the last step: AUC, the pure/mixed split, and the natural-hallucination split.

## Criteria

- **S1 (fail-safe triangle), all levels.** In no (segment, level) is a wrong-order map in the core or printed
  "consistent". "Unresolved" is allowed and is not a failure.
- **S2 (windowed false alarm), each level.** Unsupported / judged on the forward maps ≤ 0.10.

## Reported, no criterion

- Mean AUC per map and level, which shows how weak the maps got.
- Triangle outcome counts: correct / unresolved / false confidence.
- Invented letters: pure and mixed windows flagged.
- Natural hallucination vs real ink: unsupported rates.

## Known limits, stated now

- Gaussian noise on the render is only one kind of "harder scroll". Real new scrolls differ in texture, ink
  contrast and model familiarity.
- 3 segments × 2 levels.

Script: `fase8.py`, md5 062c7b846b07668e0039852fcdb7967b. Core: `inkcheck_v12.py`, md5 96c8d45f…
