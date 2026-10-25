# RESULT — PREREG_V4.md (sha256 e3907455…): hallucination in the right layer order, PHerc1667

Date: 2026-10-24. Author: Paulo Sergio Camillo. Run: `fase4.py` (md5 018bfb72…), inkcheck v7 (md5 21398ee4…).

## H1: PASS — 6/6

In every segment the three good maps stayed "consistent" and every blind probe was "isolated":

| segment | cego_letras AUC -> verdict | embaralhado AUC -> verdict |
|---|---|---|
| w013 | 0.544 -> isolated | — |
| w018 | 0.545 -> isolated | — |
| w023 | 0.537 -> isolated | — |
| w028 | 0.509 -> isolated | 0.501 -> isolated |
| w029 | 0.600 -> isolated | 0.615 -> isolated |
| w031 | 0.533 -> isolated | 0.587 -> isolated |

The blind probes do not agree with any core map (e.g. w013: corr -0.02 to -0.01; w028 embaralhado: 1.0-1.8x null_max),
so "isolated" here is a real disagreement, not a labelling effect.

## H2: the prediction held, the printed verdict was misleading

`parcial` (good ink9 map + invented strokes over ~30% of its ink area, AUC 0.919-0.938) was printed as "suspect (agrees
with part of the core only)" in all six segments. The pair statistics show it AGREES with every core map
(w013: 20-24x null_max; w028: 4.6-12.4x). The "suspect" text comes from the verdict logic: with `--core-from`, a map
outside the eligible set can never be "consistent", so a probe that agrees with the whole core falls into the
"part of the core" branch. This is a wording/logic bug in v7, found after the run; it does not affect H1.

So the limit predicted in the prereg is confirmed: the triangle judges whole maps and does NOT catch invented letters
inside a map that is mostly right. A windowed (local) check is needed for that.

## Caveats

- Same contamination as v3 (segments in the training data). The planted letters were sized to the analysis band
  (40 px high, 6 px stroke at f = 1), much smaller than real letters; behaviour at real letter size is untested.
- `parcial` is built from ink9_f itself, so its agreement with ink9_f is partly by construction; its agreement with
  rv2_f and rv3_f (independent models) is what shows the planted strokes went unnoticed.

## To fix in the next version (not applied to this result)

With `--core-from`, report a non-eligible map that agrees with ALL core maps as "agrees with the whole core
(not eligible for core)", and keep "suspect" only for partial agreement.
