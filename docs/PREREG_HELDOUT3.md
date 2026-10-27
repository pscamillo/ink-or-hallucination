# PREREG — the kit on PHerc1447 w060, a scroll no model saw, read reversed; v8-in as a witness (ink-or-hallucination)

Date: 2026-10-26. Author: Paulo Sergio Camillo. Written BEFORE any model, order rule or check is run on w060 or w062
with these tools, and before w060's labels or any prediction image of the release is opened. Only file listings,
array shapes and the dataset card were read.

## Why

RESULT_HELDOUT2 left two gaps (with ERRATUM_HELDOUT2): its two segments come from scrolls Reader v2/V3 had seen in
other segments, and every case the trio-strength tie-break has decided was read forward. PHerc1447 closes both, for
one segment: it appears in none of the three checkpoints' training lists (`onde_treino.py`, read field by field),
and its layers are read **reversed** by the 9 µm models (the dataset author reads them reversed; on w058 the right
order was reverse, PREREG_TRIANGULO). That reverse order is known before the run; the kit does not use it: the test
is whether the kit, from the data alone, decides it.

It also adds a witness of another architecture: **v8-in** (Youssef Nader, public weights, MIT), a different recipe
from villa's hybrid network, trained without any PHerc1447 data (its card; its training list holds Scroll 1, Scroll 5,
PHerc1667, 0139, 0814, 0500P2, 0009B and fragments 1, 3, 4).

## Data

Youssef Nader's public release `YoussefMoNader/ink-8um-pherc1447-surfaces` (files as in its SHA256SUMS):
- **w060** (labelled): 24-layer render at 8.64 µm, 4536 × 8488 px, `NN.tif` = normal offset NN − 11.5 voxels,
  stored ascending; tifxyz geometry; `labels/inklabels.png` (> 127 = ink) and `labels/mask.png` (certainty mask), on
  the render's pixel grid (checked by shape; no registration).
- **w062** (no labels): the same, informative only.
- w058 is excluded: it was used in PREREG_TRIANGULO and in setting the tie-break threshold.
- CT for the order rule: `PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr/0`.
- "forward" = the stored layer order, as for every surface volume in the kit.

**Mask** = certainty mask ∩ valid render (w062: valid render only).

## Models

- The three sealed models, unchanged: ink_9um `hybrid_3d2d-seed43/step-060000`, Reader v2 `step040000`, Reader V3
  (`ea405417…`). Both orders, the 17 centre layers (3–19), koine `infer` with the settings of fase9/fase10.
- Witness: v8-in base (`YoussefMoNader/ink-8um-v8in`, weights sha256 `3b94548d…`, reproduced on 2026-09-29 at AUC
  0.8623 on w058), its own `predict.py`, the 24 layers, default stride, batch 8: once in the stored order, once with
  `--reverse`.

## Procedure (`fase11.py`)

The order decision, triangle, windowed check and invented-letter planting are those of fase10.py (PREREG_HELDOUT2),
unchanged. The order is decided from the three villa models only; v8-in never takes part in it.

1. Order: (a) order rule (curvatura + ordem_camadas); (b) triangle fallback (unique core of 3+, one side); (c) the
   trio-strength tie-break, ratio ≥ 1.25; else unresolved. One robustness change from fase10, stated now: if
   curvatura reports no sagitta, the rule abstains instead of crashing.
2. Triangle `--core-from` the decided order; windowed check v12 for each villa map; invented letters in Reader v2.
3. Witness: 8-map triangle (the 6 villa maps + v8-in both orders) with `--core-from` the 3 villa maps in the decided
   order, giving v8-in's verdict; and the windowed check of v8-in's decided-order map against the 3 villa maps, floor
   = v8-in in the other order.
4. Only then w060's labels: AUC of all 8 maps, the label order (≥ 2 of the 3 villa models better in it), the
   pure/mixed invented-letter split, natural hallucinations.

## Criteria

- **O1 (main), the order decision on a scroll no model saw:** w060 decided and equal to the label order: PASS;
  decided and different: FAIL (the tie-break, and the decision procedure, are rejected); unresolved: NOT TESTABLE.
- **W1a, witness triangle:** v8-in's decided-order map is "consistent" or "agrees with the whole core": PASS; any other
  verdict: FAIL.
- **W1b, witness windows:** the fraction of v8-in's judged windows not supported by the 3 villa maps ≤ 0.10: PASS;
  above: FAIL; fewer than 20 judged windows: NOT TESTABLE.
- **H2, Q1–Q4, N1:** the same definitions and thresholds as PREREG_HELDOUT2, on w060. H1 needs 2 decided labelled
  segments and is NOT TESTABLE here.
- Informative, no criterion: v8-in's AUC in both orders; w062's decision, against the order its author uses.

## Known limits, stated now

- **One labelled segment.** A pass is one case of a reverse-read, unseen scroll, not a rate.
- **The labels** were drawn by the dataset author on these saved surfaces and used to fine-tune his models. The card
  does not say whether they were drawn over a model's prediction; if over v8-in's, v8-in's AUC is partly circular.
  W1a/W1b do not use the labels.
- **v8-in is a witness of agreement, not of truth.** It was trained on data that overlaps the villa models' scrolls
  (0139, 0814, 1667), so independence is of architecture and recipe, not of every training scroll.
- **The reverse order is expected** from prior knowledge. O1 tests whether the kit reaches it without that knowledge.

Every number is reported as it comes out, pass or fail. No rule is changed after the seal. A crash is fixed in a
dated addendum before rerunning.

## Tools

Run with the ink-sdk environment's Python; koine in the villa environment through `uv run`; v8-in in its own venv.

| Tool | md5 |
|---|---|
| `fase11.py` | `bcc1ce5dd793b782732ff5c4480d47b9` |
| `inkcheck_v12.py` | `96c8d45f6404c3e46f7ab10c2cfac948` |
| `curvatura.py` | `4908428dd7b8ea6403c410caaa7e0ab0` |
| `ordem_camadas.py` | `fdf6a7c7b7fa470457231f9783a11b0b` |
