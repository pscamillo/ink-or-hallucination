# PREREG — windowed check v11 (swap null) on maps it has never been run on (ink-or-hallucination)

Date: 2026-10-24. Author: Paulo Sergio Camillo. Written BEFORE the v11 windowed check is run on any of the maps below.

## Why

In the PHercParis4 run (PREREG_PARIS4) the v10 windowed check called windows "unsupported" where the three models
agreed at corr 0.87–0.98. A label-free diagnosis (`diag_local.py`) showed the cause: the shift null had no valid draw
in those windows. The supervision mask is a narrow band, so every far shift fell outside it. v10 then read the null as
infinite and the window as unsupported. This was a bug in the null, not model disagreement.

v11 changes two things:
- **Swap null.** The target's window is compared with the other maps at other valid windows of the same mask, at least
  2 windows away. Windows where the other maps have strokes are preferred. There are 19 draws, and the bar is
  "corr above all draws", which is p < 0.05.
- **Fail closed.** A window with fewer than 10 valid null draws is "not judged", never "unsupported", and is counted.

Exploratory checks, declared:
- Synthetic test (`teste_v11.py`, narrow mask). The v10 null left 36 windows without a null. With v11: 0/36 false
  alarms and 10/10 invented-letter windows flagged.
- PHerc0343P (`calib_v11.py`, KLAVIS camera as reference, same invented letters as calibration 3), shift null →
  swap null:
  - invented-letter windows with no real ink nearby, flagged: 7/9 → 19/21;
  - mixed windows (invented letter next to real ink), flagged: 0/4 → 1/13;
  - false alarm on the good maps: rv2 0/62, rv3 4/62, hecate 13/62;
  - the blind BASE map: 47/61 windows unsupported.
- No parameter was tuned on the data below.

## Data

- **Set A (test).** 12 segments already run through the models in earlier preregs. All 12 have the order predicted
  "forward", and that order was confirmed by AUC:
  - PHerc0139 w035, w039, w040, w041, w043 and PHerc0814 46527 (folder `fase2/`, PREREG_ORDEM);
  - PHerc1667 w013, w018, w023, w028, w029, w031 (folder `fase3/`, PREREG_V3).

  The windowed check (any version) has never been run on them.
- **Set B (dense text).** The 8 PHercParis4 segments of `fase5/`, run only after `fase5.py` has finished. The v10
  windowed-check results there are known and buggy. The v11 results are not.
- **Known about this data.**
  - The ink labels of all these segments were read earlier, for AUC only. In this run they are used only in the last
    step, to split invented-letter windows into pure (no real ink) and mixed.
  - All segments are in the training data of the three models (contamination). This tests the mechanics of the
    check, not model generalisation.

## Tools (fixed now)

| Tool | md5 |
|---|---|
| `inkcheck_v11.py` | `ac5de45a09228fc0772c42c9980a8319` |
| `fase6.py` | `85bd1f3769fad813be2fd140f428d2ac` |

`fase6.py` reuses `glyph()`/`plant()` from `fase5.py` (md5 e33f511a…) with the same seeds.

v11 also corrects a wording bug in `triangle`. A map that agrees with the whole core but was not allowed into it by
`--core-from` printed "suspect"; it now prints "agrees with the whole core". Triangle verdicts are not used in this
prereg.

## Settings

`local --score corr --energy-k 1.25 --null swap --n 19 --min-null 10`. Window = 2.5 mm, with the pixel size derived
from the mesh. Each predicted-order map (ink9, rv2, rv3) is checked against the other two. Invented letters are 2.5 mm
high with a 0.2 mm stroke, cover ~2% of the mask, and use the map's own 99.5th percentile. They are planted in the
predicted-order Reader v2 map.

## Criteria — Set A

- **P1 false alarm.** Pooled over the 12 segments and the 3 predicted-order maps, unsupported / judged ≤ 0.10.
- **P2 fail-closed coverage.** Windows with strokes but no valid null / all windows with strokes ≤ 0.05.
- **P3 detection.** Among invented-letter windows with > 2% invented letter and < 1% real ink, fraction flagged
  unsupported ≥ 0.60.

## Criteria — Set B (PHercParis4, dense text)

P4-1, P4-2, P4-3: the same three criteria with the same thresholds. The invented letters are the ones `fase5.py`
already planted (`rv2_falsas.npy`).

## Reported, no criterion

- Mixed windows flagged. The calibration says this will be low.
- False alarms outside the invented letters in the tampered map.
- Wrong-order maps checked against the two predicted-order maps.
- Per-segment numbers.

Anything else is reported as it comes out. No rule is changed after the run.
