# PREREG — revised layer-order decision, blind test on PHerc0500P2 and PHerc0009B (ink-or-hallucination)

Date: 2026-10-26. Author: Paulo Sergio Camillo. Written BEFORE any model, order rule or check is run on these two
scrolls, and before any of their labels is opened. Only S3 listings and array sizes were read.

## Why

On PHerc0841 (RESULT_HELDOUT0841) the kit abstained on all three segments: the layer-order rule stopped at its CT-match
threshold (0.28–0.35 < 0.5) and the triangle found no unique core.

After that run, in **declared exploratory** work, I looked at why the triangle found no core: the three right-order maps
agree with each other, but so do the three wrong-order maps (the models are related). The triangle sees two "mirror"
cores and abstains. A candidate tie-break is to take the trio that agrees more strongly.

**PHerc0841 is now the calibration scroll.** It has been seen, with labels, and is no longer evidence. This test applies
the revised decision, sealed here, to two scrolls none of the models saw and that I have not looked at.

## The revised decision (what changes)

The layer order is decided in three steps. Steps 1 and 2 are **unchanged** from PREREG_HELDOUT0841:

1. **Order rule** (curvatura + ordem_camadas), unchanged. If it decides, that is the order.
2. **Triangle fallback** (unique core of size ≥ 3, all one order), unchanged. If it decides, that is the order.
3. **Trio-strength tie-break (NEW).** In the same 6-map triangle (n 300, min-ratio 2.0):
   - for each order, S = median of the 3 pairwise correlations among that order's three maps;
   - ratio = max(S_f, S_r) / max(min(S_f, S_r), 1e-6);
   - if ratio ≥ **1.25**, the order of the larger S; otherwise the segment is **unresolved** (no verdict there).

**Where 1.25 comes from** (stated now, so it cannot be read as tuned afterwards):
- On the 26 triangles already run on training segments (fase2/3/5/8), the right-order trio was the stronger one in 26
  of 26, with ratios 1.10 to 4.40. At 1.25: 25 decided, all right, 1 abstention (PHerc1667 w029, ratio 1.10).
- On PHerc0841 (calibration, seen with labels): it would have been right on all 3, ratios about 1.56–1.71.
- On PHerc1447 w058, the only labelled case where the right order is **reverse**: the right trio was also the stronger,
  but at ratio 1.16, so the rule would abstain.

**Known limit:** in every case the rule has decided so far, the right order was forward. It has not been shown to pick
reverse correctly.

## Data

One public segment from each scroll: the only labelled segment on each. Neither is among the 24 training segments of
the three models (all from PHerc0139, 0814, 1667 and Paris4).

| | PHerc0500P2 `20250825181859--1` | PHerc0009B `20250919125754-auto_grown_20250919055754487_inp_hr` |
|---|---|---|
| model input | official surface volume, 9.362 µm, 28 layers | official surface volume, 8.64 µm, 31 layers |
| mesh (order rule) | official 9.362 µm tifxyz | official 8.64 µm tifxyz |
| CT (order rule) | `volumes/20250820143440-9.362um-1.2m-113keV-masked.zarr/0` | `volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr/0` |
| labels | `ink-labels/2.215um-volume-20250526151718/20260918/` | `ink-labels/2.401um-volume-20250820154339/20260918/` |
| CT-vs-CT registration | 2.215 µm surface volume, level 2 | 2.401 µm surface volume, level 2 |

**Registration**, as for PHerc0841: labels are resampled to the model grid by the ratio of the array sizes. First, a
CT-against-CT check (centre layers of the two surface volumes, stroke band, correlation peak within ±20 px): a peak within
±3 px means no shift; otherwise the measured shift is applied to the labels and reported. No model and no label is
involved in this check.

**Mask** = label supervision area ∩ valid surface volume.

## Models (as in every sealed run)

ink_9um `hybrid_3d2d-seed43/step-060000`, Reader v2 `step040000`, Reader V3 (`ea405417…`). Both orders, the 17 centre
layers, koine `infer` with the settings of PREREG_HELDOUT0841.

## Procedure (`fase10.py` = `fase9.py` + step 3 above)

1. Registration check.
2. Order: step 1, then 2, then 3. Record **which step decided**.
3. Triangle with `--core-from` the predicted order.
4. Windowed check v12 (sealed settings), each predicted-order map against the other two.
5. Invented letters planted in the predicted-order Reader v2 map (fase5 planting, unchanged); windowed check on it.
6. Only then the labels: AUC per map, pure/mixed split of invented-letter windows, natural hallucinations.

`fase10.py` also prints NOT TESTABLE, not FAIL/PASS, for Q1 and Q2 when their count is 0/0 (the misleading line noted
in RESULT_HELDOUT0841).

## Criteria

**O1 — the revised decision (the main criterion of this test).** On the segments where the kit decides the order (by
any step), the decided order must be the one the labels prefer (≥ 2 of the 3 models have the higher AUC in it).
- PASS: at least 1 segment decided and none wrong.
- FAIL: any decided segment in the wrong order. The revised decision is then rejected.
- NOT TESTABLE: no segment decided.

There are at most 2 segments. 2 of 2 right is **consistent** with a rule that works; it does not measure an error rate,
and will be reported that way.

**The other criteria, as for PHerc0841 and with the same thresholds:** H1 layer order (needs 2 decided segments), H2
triangle, Q1 false alarm ≤ 0.10, Q2 no-null ≤ 0.05, Q3 pure invented-letter windows flagged ≥ 0.60, Q4 mixed ≥ 0.20, N1
natural hallucinations (≥ 20 windows).

## Known limits, stated now

- **The labels may come from a model.** Both segments carry an official prediction (`new_canon_autoresearch_recipe`),
  and the labels are from the same dated batch as PHerc0841's. If they were made from that prediction, O1 and H1 measure
  agreement with it, not with a human reading. It is a different (finer) scan and a different network.
- **Two segments, two scrolls.** A pass here is not every scroll.
- **Reverse stays untested** unless one of these segments reads in reverse.
- **The models are related**, as everywhere in the kit; the README says so.

Every number is reported as it comes out, pass or fail. No rule is changed after the seal. A crash is fixed in a dated
addendum before rerunning, as in PREREG_V11.

## Tools

Run with the ink-sdk environment's Python (zarr 3, for the official labels); inference runs in the villa environment
through `uv run`, as in fase9.py.

| Tool | md5 |
|---|---|
| `fase10.py` | `f71405f8523a0b0ecd116423abcfc794` |
| `baixa_heldout2.py` | `9c1d3f69cd377ff4061e38a0f13bbca6` |
| `inkcheck_v12.py` | `96c8d45f6404c3e46f7ab10c2cfac948` |
| `curvatura.py` | `4908428dd7b8ea6403c410caaa7e0ab0` |
| `ordem_camadas.py` | `fdf6a7c7b7fa470457231f9783a11b0b` |
