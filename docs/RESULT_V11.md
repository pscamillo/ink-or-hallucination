# RESULT — PREREG_V11.md (sha256 c0a27834…) + ADDENDUM (sha256 3d67eb91…): windowed check v11, Set A

Date: 2026-10-24. Author: Paulo Sergio Camillo. Run: `fase6.py` (md5 4dab3cf9…), `inkcheck_v11.py` (md5 ac5de45a…).
Ink labels were read only in the last step, to split invented-letter windows into pure and mixed.
Set B (PHercParis4) has not been run yet; it waits for `fase5.py` to finish.

## Criteria (Set A: 12 segments, PHerc0139 / 0814 / 1667)

| criterion | result | threshold | verdict |
|---|---|---|---|
| P1 false alarm, predicted-order maps | 1/851 = 0.001 | ≤ 0.10 | **PASS** |
| P2 windows with strokes but no valid null | 3/854 = 0.004 | ≤ 0.05 | **PASS** |
| P3 invented letters, pure windows flagged | 10/19 = 0.526 | ≥ 0.60 | **FAIL** |

Reported, no criterion:
- Mixed windows (invented letter + ≥ 2% real ink) flagged: 2/180.
- False alarms outside the invented letters in the tampered map: 0/102.
- Wrong-order maps checked against the two predicted-order maps: 1762/1878 = 0.94 unsupported.

Per segment, invented letters:

| segment | pure flagged | mixed flagged |
|---|---|---|
| 0139 w035 | 0/0 | 0/3 |
| 0139 w039 | 0/0 | 0/0 |
| 0139 w040 | 0/0 | 0/1 |
| 0139 w041 | 0/0 | 0/1 |
| 0139 w043 | 0/0 | 0/0 |
| 0814 46527 | 0/0 | 0/2 |
| 1667 w013 | 0/0 | 0/16 |
| 1667 w018 | 10/17 | 1/88 |
| 1667 w023 | 0/1 | 0/40 |
| 1667 w028 | 0/0 | 1/8 |
| 1667 w029 | 0/0 | 0/9 |
| 1667 w031 | 0/1 | 0/12 |

## What this says

- The fix did what it was for. Windows without a null went from "unsupported" (v10) to 0.4% and "not judged".
- On the predicted-order maps there was one false alarm in 851 judged windows.
- Wrong-order maps are flagged almost everywhere (94%).
- Invented letters are missed when they sit inside real text. In these segments the supervision mask hugs the text,
  so 180 of the 199 judged invented-letter windows were mixed.

## Diagnosis (after the run, label-free: `diag_energia.py`, reads only the .npz files and our own fake mask)

**The stroke rule judges almost nothing on most of these segments.** A window is judged if its energy is
≥ 1.25 × the map's median window energy. Inside a text-hugging mask almost every window has text, so energies are
flat: in PHerc0139 the strongest window is only 1.18–1.34 × the median, and invented-letter windows sit at
1.0–1.3 ×. Judged windows per map: 0–3 on PHerc0139/0814; 2–189 on PHerc1667, where energy varies more.

**The same model in the wrong order gives a usable "no ink" floor.** Its median window energy is 0.07–0.48 of the
predicted-order map. "Energy ≥ 2 × the wrong-order median" would judge nearly every window with text, for example
50/53, 28/28, 70/70 and 182/186.

**Judging more windows would not by itself catch letters inside text.** Window correlation is dominated by the real
text around an invented letter. That needs a different score. This points to a v12 with a new prereg, tested on data
the windowed check has not seen (PHercParis4).

## Limits

- Contamination: all segments are in the models' training data.
- P3 rests on 19 pure windows, 17 of them in one segment.
- The labels of these segments had been read before (for AUC in PREREG_ORDEM / PREREG_V3), though not with this check.
