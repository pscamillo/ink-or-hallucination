# NOTE — re-reading every triangle verdict printed "suspect" (2026-10-27)

Date: 2026-10-27. Author: Paulo Sergio Camillo. Written after the results below were sealed; no sealed file is
changed. Prompted by an independent review of the repository.

## Why

RESULT_V4 found a wording bug in the triangle (inkcheck v7 to v10): with `--core-from`, a map outside the eligible set
can never be "consistent", so a map that agrees with **every** core map was printed "suspect (agrees with part of the
core only)". v11 fixed the wording. The question left open: which earlier "suspect" verdicts were really "agrees with
the whole core", and did any sealed result count on them?

## How

`scripts/rele_triangulos.py` (md5 `8eaf5cb98b1fd078c415c66ddb6475d5`) reads every saved `triangulo*.json` and, for
each map printed "suspect", counts the core maps it agrees with, from the saved pair statistics and with the kit's
own rule (p < alpha and corr ≥ min_ratio × null_max). No model was run again and no label was read.

## Result

47 "suspect" verdicts; 24 agree with the whole core, 23 with part of it.

| run | true "suspect" (part of core) | really "agrees with the whole core" |
|---|---|---|
| V4 (`fase4`, PHerc1667, map `parcial`) | 0 | 6 (already reported in RESULT_V4) |
| PARIS4 (`fase5`, PHercParis4, wrong-order maps) | 5 | **18** |
| ESTRESSE (`fase8`, noisy PHercParis4) | 10 | 0 |
| HELDOUT2 (`fase10`) | 2 | 0 |
| HELDOUT3 (`fase11`) | 6 | 0 |

From v11 on (ESTRESSE, HELDOUT2, HELDOUT3) the printed verdicts are right.

## What it changes: PARIS4 P2

PREREG_PARIS4 P2 used the PREREG_V3 rule: in each segment where the three predicted-order maps reach AUC ≥ 0.70,
they are "consistent", and every map with AUC < 0.60 is "suspect" or "isolated". RESULT_PARIS4 counted 8/8 because
every wrong-order map was printed "suspect".

Read correctly, a wrong-order map with AUC < 0.60 agrees with the whole core in 6 of 8 segments:

| segment | wrong-order maps with AUC < 0.60 that agree with the whole core |
|---|---|
| w00, w01 | none (P2 holds) |
| w02 | ink_9um (0.569) |
| w03 | Reader v2 (0.589), Reader V3 (0.593) |
| w05 | ink_9um (0.583), Reader v2 (0.573), Reader V3 (0.560) |
| w06 | ink_9um (0.590), Reader v2 (0.591) |
| w07 | ink_9um (0.557) |
| w09 | ink_9um (0.583) |

By the letter of the prereg (the printed text starts with "suspect") P2 passed 8/8. By its meaning it is **2/8:
FAIL**. This note records the second reading as the one that counts.

The three predicted-order maps did agree with each other in 8/8 segments; with `--core-from` no other map could
enter the core.

## What it means

- On PHercParis4, which is in the training data, a wrong-order stack keeps some ink signal (AUC 0.54–0.64), and the
  wrong-order maps agree with the right-order core. This is the same effect that failed H2 on PHerc0009B
  (RESULT_HELDOUT2): **the triangle's verdict on a wrong-order map is not a reliable alarm**.
- The order the kit uses does not come from that verdict: it comes from the geometry rule, else the triangle's unique
  core in one order, else the tie-break. None of those results changes.
- ESTRESSE S1 ("no wrong-order map in the core or printed consistent") cannot fail when the core is fixed with
  `--core-from`, so its PASS shows nothing about the triangle. It is withdrawn as evidence.
- The triangle record becomes: PHerc1667 (V3) 6/6, wrong-order maps "isolated"; PHercParis4 (PARIS4) 2/8.
  **8/14**, not 14/14.
- The README and the submission are corrected to say this.
