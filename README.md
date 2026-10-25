# ink-or-hallucination

[![test](https://github.com/pscamillo/ink-or-hallucination/actions/workflows/test.yml/badge.svg)](https://github.com/pscamillo/ink-or-hallucination/actions/workflows/test.yml)

Label-free checks for 2.5D ink maps: does a map show ink, or something a model made up?

New 9 µm ink models keep coming, each with cleaner-looking maps, and someone reviewing a claimed letter cannot tell
from the map alone whether it is ink or something the model drew. This kit gives a label-free answer from what the
models do: read the same segment with three models, each in both layer orders, and it tells you whether they agree
in the right order, and window by window where one map shows strokes the others do not. Every check was tested with
a sealed pre-registration on public labelled segments before being trusted.

| clean map | the same map with invented letters |
|---|---|
| ![report, clean map](figures/report_clean.png) | ![report, tampered map](figures/report_tampered.png) |

*The HTML report on PHercParis4 w02. Left: the three models as they came out. Right: the same segment with invented
letters planted in Reader v2. Only that map goes up (1–2% → 13%), and its red windows land on the planted letters:*

![overview](figures/overview.png)

## What it checks, and how well

| check | question | record (sealed, public data) |
|---|---|---|
| **layer order** | which way should the render's layers be stacked for the 9 µm models? (mesh + CT only, before running any model) | **60/60** (segment, model) pairs, 20 segments, 4 scrolls |
| **triangle** | do 3+ models agree on this map beyond chance, in that order and not in the other? | **14/14** segments; never put a wrong-order map in the core, even with maps degraded to AUC 0.79 |
| **windows** | where does one map show strokes the other models do not? | blind on PHercParis4: **2.7%** false alarm, **81/81** isolated invented letters, **26%** of invented letters inside real text |
| **natural hallucinations** | does it flag the mistakes models make on their own? | where a model draws strokes and the label has no ink: flagged **28%** vs **1.6%** on real ink (18×, p ≈ 1e-87, blind) |
| **depth** (informative) | does a stroke fade when the same model reads the layers in the other order? | real ink fades more than model-made strokes (AUC 0.76 blind; 0.65 on another set). Shown, not used for a verdict |

## Scope and limits

- **It measures agreement, not truth.** An ink pattern that every model shares passes.
- **The three models are not independent.** All three are villa's hybrid 3D/2D network trained on the same 24
  segments of four scrolls (PHerc0139, 0814, 1667, Paris4); Reader v2 has its own labels and was trained separately,
  and Reader V3 is Reader v2 trained further. Their agreement rules out chance, not a pattern all three learned from
  the same data. (Read from the checkpoints' own configs.)
- **All labelled test segments are in the models' training data.** The stress test (maps degraded to AUC 0.79) is
  the closest we can get to a new scroll. Below that the kit is untested, and it should say "unresolved" rather
  than be trusted.
- **Most invented letters sitting on real strokes are missed:** about 3 in 4.
- **A model that draws differently from the others gets more alarms.** An alarm means "the other models do not see
  this", not "this is fake".
- **The windowed score assumes pixel-aligned maps.** The report measures the shift between maps and warns.
- **Scope.** Tested with the 9 µm koine models (ink_9um, Reader v2, Reader V3); the layer-order rule's "reverse"
  case rests on one calibration segment plus symmetry. Tested on Linux with real data; the checks and the report
  also pass on Windows and macOS (CI on synthetic segments, every push); the end-to-end demo needs
  `vc_render_tifxyz` and a CUDA GPU.

## On a scroll with no labels

`demo_unlabelled.py` on a public mesh of PHerc0800 (z5664, w020): the layer-order rule abstained (CT match 0.46,
below 0.5), and with the order unknown the triangle found no group of maps that agree in one order only. The
report says so instead of guessing:

![report, no ink signal](figures/report_noink.png)

*"No ink signal here" is a result, not a failure: on this segment the kit cannot tell ink from what the models
would draw anyway.*

<details>
<summary><b>Quick start</b></summary>

```bash
pip install -r requirements.txt                     # + streamlit for the app
# a folder per segment: NAME.tif and NAME_reverse.tif for each model, optional mask.npy
python segment.py SEGMENT_DIR --models ink9 rv2 rv3 --px-um 9.6 --order forward
#   -> SEGMENT_DIR/inkcheck_report/report.html (+ report.json, one PNG per map)
streamlit run app.py                                  # the same, point and click
```

Choosing the order (`--order`): use the layer-order rule before looking at any map.

```bash
python scripts/curvatura.py MESH_TIFXYZ --D 1000                 # which side the sheet curves to
python scripts/ordem_camadas.py MESH_TIFXYZ RENDER.zarr CT.zarr/0 # which way the stored layers grow
# the 9 um koine models want the stack from the OUTER face to the INNER face
```

`demo_unlabelled.py` does everything on one mesh of an eligible scroll: render (`vc_render_tifxyz`, public CT),
order rule, the three models in both orders, and the report.

As a library: `import inkcheck` (the sealed core: `check_triangle`, `check_local`, …) or `segment.run(...)`, which
returns everything as a dict.
</details>

<details>
<summary><b>How each check works</b></summary>

**Layer order.**
- `curvatura.py` measures, from the mesh alone, which side of the sheet is concave: the median sagitta at
  1000 voxels gives the outward normal.
- `ordem_camadas.py` samples the CT along that normal and matches each stored layer to a depth. The slope says
  which way the layers grow.
- The 9 µm models want outer → inner. The rule abstains if the sheet is too flat or the CT match is weak
  (median corr < 0.5).

**Triangle.**
- Every pair of maps is correlated at stroke scale (2–20 px band) against a null that shuffles blocks inside the
  valid area.
- The core is the unique largest group of 3+ maps that all agree, with p < 0.01 and corr ≥ 2 × the null maximum.
- With `--core-from` fixed to the predicted order, every other map is judged against that core.

**Windows** (window = one letter, about 2.5 mm).
- **Judged:** a window is judged if its stroke energy is ≥ 2 × the median energy of the same model in the wrong
  order (the "no ink" floor).
- **Correlation test:** the window is unsupported if its correlation with the mean of the other maps does not beat
  every one of 19 swaps with far windows of the same mask.
- **Unexplained strokes U:** the window is also unsupported if U is an outlier for that map. U is the fraction of
  this map's stroke pixels with no stroke of any other map within 6 px.
- **No null:** a window without a valid null is "not judged", never "unsupported".
- **Too few windows:** a map with fewer than 20 judged windows is reported as "too few to judge"; its fraction does
  not count toward the verdict (1 of 3 is not 33% of anything).

**Depth (informative).** D = stroke energy in the chosen order / in the other order, same model, per window.
</details>

<details>
<summary><b>Pre-registration trail</b></summary>

Every test was written down and sha256-sealed **before** it was run. Results were sealed as they came out,
failures included. Each fix went into a new pre-registration on data the check had not seen.

| # | prereg | data | outcome |
|---|---|---|---|
| 1 | TRIANGULO | PHerc1447 w058 | triangle alone failed (mirror group) → led to the order rule |
| 2 | ORDEM | PHerc0139 ×5, 0814 ×1 | order 18/18 PASS; triangle 3/6 FAIL (null bug: NaN draws) |
| 3 | V3 | PHerc1667 ×6 | order 18/18 PASS; triangle 6/6 PASS after the fix |
| 4 | V4 | PHerc1667 ×6 | blind probes isolated 6/6; partial invented letters not caught at map level |
| 5 | PARIS4 | PHercParis4 ×8 | order 24/24 PASS; triangle 8/8 PASS; windows v10 FAIL (null bug: +inf) |
| 6 | V11 (+ addendum) | 12 segments | windows v11: false alarm 1/851 PASS; no-null 0.4% PASS; invented letters 10/19 FAIL |
| 7 | V12 | PHercParis4 ×8 (blind) | windows v12: 4/4 PASS; v11 on the same data 3/3 PASS |
| 8 | NATURAIS | PHercParis4 + 12 segments | natural hallucinations flagged 18× / 7.7× more than real ink: PASS, PASS |
| 9 | DIRECAO | PHercParis4 + 12 segments | depth separates them: PASS (AUC 0.76) / FAIL (AUC 0.646) |
| 10 | ESTRESSE | PHercParis4 ×3, noisy renders | fail-safe triangle 6/6 PASS; false alarm 4.1% / 3.5% PASS |

Every file and its sha256 is in `docs/`. Each pre-registration cites the sha256 of the one before it, and all 13
links match the files in `docs/`. The natural-hallucination results (#8) are in `RESULT_V12.md`.

Two gaps, stated plainly:
- The `inkcheck.py` cores used in #1 (md5 149b7fd6, 5e43074c) were not kept. That test failed, and it only led to
  the order rule; no result below it rests on that code.
- The first `fase6.py` (md5 85bd1f37) crashed on its first segment and was replaced by 4dab3cf9, as the V11
  addendum records.
</details>

<details>
<summary><b>Repository layout</b></summary>

```
inkcheck.py        sealed core (v12, md5 96c8d45f…): direction, label, witness, triangle, local
segment.py         one command for a whole segment -> HTML/JSON report
app.py             Streamlit front end
demo_unlabelled.py end-to-end demo on an unlabelled mesh of an eligible scroll
scripts/           order-rule tools and every sealed run script, byte-identical to what the preregs hash
versions/          the cores the sealed runs used (v6, v7, v10 = inkcheck.py, v11, v12), byte-identical
docs/              PREREG_*.md, RESULT_*.md and their sha256
figures/           the README figures
LICENSE            MIT
requirements.txt   numpy scipy tifffile imagecodecs pillow zarr
tests/             synthetic smoke tests (ink, texture only, one model inventing strokes)
.github/           CI: the tests on Linux, Windows and macOS
```

The run scripts in `scripts/` keep their original Portuguese comments and output, so their md5 still match the
pre-registrations.
</details>

---

By Paulo Sergio Camillo. Models: `ink_9um` and the Reader models (Vesuvius Challenge / villa ink-detection).
Data: Vesuvius Challenge open data; meshes for the demo from
[vesuvius-eligible-meshes](https://github.com/pscamillo/vesuvius-eligible-meshes). MIT license.
