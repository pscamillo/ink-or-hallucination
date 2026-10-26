# PREREG — the whole kit on a scroll none of the models was trained on: PHerc0841 (ink-or-hallucination)

Date: 2026-10-25. Author: Paulo Sergio Camillo. Written BEFORE any model, order rule or check is run on PHerc0841, and
before any of its labels is opened. The data were only downloaded and their sizes read.

## Why

Every labelled test so far ran on segments the three models were trained on (PHerc0139, 0814, 1667, Paris4). The
checkpoints' own configs list the same 24 training segments for ink_9um, Reader v2 and Reader V3, and PHerc0841 is
not among them, nor in any other field of the three configs. This test runs the sealed kit, unchanged, on PHerc0841.

## Data

Three public segments of PHerc0841 (Vesuvius Challenge open data), every one that has labels:
`20260220213127-w00`, `20260220214732-auto_grown_20260220144552896`, `20260221022814-auto_grown_20260220174252405`.

- **Model input:** the official surface volume at 9.366 µm (28 layers), level 0.
- **Mesh:** the official 9.366 µm tifxyz (layer-order rule, pixel size, window).
- **CT for the order rule:** `PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/0`, read remotely
  (the rule reads one small box).
- **Labels:** the official `ink-labels/2.403um-volume-20260319124803/20260918/` (inklabels, supervision), on the
  2.403 µm grid. Their provenance is not documented in the files. They are used as given.

**Registration.** Both meshes of a segment sample the same surface on grids of the same step (0.05). The 2.403 µm
grid is the 9.366 µm grid scaled by the voxel ratio: 16460/4220 = 3.900, 18560/4760 = 3.899, 9.366/2.403 = 3.898.
The valid areas overlap with IoU 0.976 at zero shift (w00, measured before this prereg). The labels are therefore
resampled to the 9.366 µm grid by that scale only (area-weighted, then > 0.5).
- A second check, CT against CT, runs first in `fase9.py`: the centre layers of the two surface volumes, stroke band,
  cross-correlation peak within ±20 px. If the peak is within ±3 px, no shift is applied. Otherwise the measured
  shift is applied to the labels and reported. No model and no label is involved in this check.

**Mask** = the label supervision area (as in PREREG_PARIS4 and PREREG_V12) ∩ the valid surface volume. It says where
labels exist, not where ink is.

## Models (as in every sealed run)

ink_9um `hybrid_3d2d-seed43/step-060000`, Reader v2 `step040000`, Reader V3 (`ea405417…`). Both orders, centred 17
of the 28 layers, koine `infer` with the settings of `fase5.py`.

## Procedure (`fase9.py`)

1. Registration check (above).
2. Layer-order rule (`curvatura.py` + `ordem_camadas.py`, as in `demo_unlabelled.py`). If it abstains, the triangle
   fallback of `demo_unlabelled.py` decides (core all one order, size ≥ 3), else the segment is **unresolved**: the kit
   gives no verdict there, and the segment is reported, not dropped silently.
3. Triangle with `--core-from` the predicted order (n 300, min-ratio 2.0).
4. Windowed check v12, sealed settings (PREREG_V12), each predicted-order map against the other two, floor = the same
   model in the other order. Wrong-order maps as targets: informative.
5. Invented letters planted in the predicted-order Reader v2 map, with `fase5.py`'s planting unchanged (2.5 mm
   letters, 0.2 mm strokes, 2 % of the mask, seed = crc32 of the segment name). Windowed check on the tampered map.
6. Only then the labels: AUC per map (`inkcheck label`, n 200), pure/mixed split of invented-letter windows,
   natural-hallucination split.

## Criteria (the same thresholds as the earlier preregs)

- **H1 layer order** (PREREG_PARIS4 P1): over the decided segments, in ≥ 90 % of (segment, model) pairs with
  |ΔAUC| ≥ 0.05 the kit's order has the higher AUC, and no segment has all 3 models against it. Needs ≥ 2 decided
  segments, else NOT TESTABLE.
- **H2 triangle** (P2): on every segment where all 3 predicted-order maps have AUC ≥ 0.70, the three are
  "consistent" and every map with AUC < 0.60 is "suspect" or "isolated". No such segment → NOT TESTABLE.
- **Q1 false alarm** ≤ 0.10; **Q2 no-null** ≤ 0.05; **Q3 pure invented-letter windows flagged** ≥ 0.60;
  **Q4 mixed** ≥ 0.20 (PREREG_V12).
- **N1 natural hallucinations** (PREREG_NATURAIS): ≥ 20 natural windows, their unsupported rate ≥ 2 × that of
  real-ink windows, one-sided Fisher p < 0.01. Fewer than 20 natural windows → NOT TESTABLE.

## Known limits, stated now

- **The labels may come from a model.** If they were made from the team's 2.4 µm prediction, H1 and the label splits
  measure agreement with that prediction, not with a human reading. It is a different scan (3.9× finer) and a
  different network from the three under test.
- **Three segments of one scroll.** A pass here is one held-out scroll, not every scroll.
- **The models are related** (same architecture and training data; V3 descends from v2). That is the case for the
  kit everywhere and is stated in the README.

Every number is reported as it comes out, pass or fail. No rule is changed after the run. A crash is fixed in a dated
addendum before rerunning, as in PREREG_V11.

## Tools

Run with the ink-sdk environment's Python (zarr 3, needed for the official labels); model inference runs in the villa
environment through `uv run`, as in `fase5.py`.

| Tool | md5 |
|---|---|
| `fase9.py` | `6664f7312e3dc31f5a770be1c7e38407` |
| `baixa_0841.py` | `b7d5bb9ca15b8ba587ac4674630d6c89` |
| `inkcheck_v12.py` | `96c8d45f6404c3e46f7ab10c2cfac948` |
| `curvatura.py` | `4908428dd7b8ea6403c410caaa7e0ab0` |
| `ordem_camadas.py` | `fdf6a7c7b7fa470457231f9783a11b0b` |
