# NOTE — second independent review: what it found and what changed (2026-10-27)

Date: 2026-10-27. Author: Paulo Sergio Camillo. An independent review of the repository at commit 58bf70f, given the
code and documents but not the list of earlier fixes. No sealed file is changed; no sealed result changes.

## Changed in the code (not sealed; the report's summary, not the checks)

- **The report trusted `--order`.** `segment.py` takes the layer order from the user and never re-decides it. If the
  maps read in the other order agreed among themselves as much as or more than the chosen ones, the report could
  still print the "pattern of real ink in the chosen order" line, and a note saying the chosen order was "the
  stronger one" even when it was not. Now, when the other-order maps agree among themselves at all (median corr
  ≥ 0.2), the report warns ("the maps do not support the chosen order") unless the chosen trio is ≥ 1.25 × the
  other (the tie-break's own bar), and the grey note appears only when that holds. A test
  covers it. `--order` no longer has a default on the command line.
- The report's reference line said good maps were at 0–3% "on the validation segments"; those were training
  segments. It now also gives the held-out range (0–7%).

## Corrected in the README and the submission text

- **Invented-letter counts are windows, not letters** (81/81, 4/4, 3/4, 10/11, 26–39.6%): windows overlap by half.
- **"Blind"** on PHercParis4 means blind for the windowed check: those segments are in the training data and their
  labels had been read in earlier runs (PREREG_V12).
- **Depth:** 0.646 on the second set is below the sealed 0.65 bar (RESULT_DIRECAO: FAIL); it had been rounded to 0.65.
- **What was sealed:** the core checks (layer order, triangle, windows, tie-break). The report's summary bars
  (5% / 20%, 20 windows) and the tie-break guard were not pre-registered.
- **Seal trail:** the README said "up to #10, each pre-registration cites the sha256 of the one before it, and all 13
  links match". Not every one does. The reviewer counted 25 sha256 citations across `docs/`; all match the files.
- **Missing files:** the run scripts of #2 (`geometria.py`, `fase2.py`) were never md5-sealed; they and the helper
  scripts the docs cite (`confere_trava.py`, `diag_local.py`, `diag_energia.py`, `teste_v11.py`, `calib_v11.py`) are
  now shipped in `scripts/`, without a seal to prove they are what ran (`confere_trava.py` does match the md5 its
  note cites). `prep_1667.sh`, cited in PREREG_V3, was not kept.

## Corrected here: one sentence in a sealed prereg

PREREG_V12 says `inkcheck_v12.py`'s "defaults equal the settings below". They do not: run by hand,
`inkcheck.py local` defaults to the older energy rule and correlation score. Every sealed run passed the v12 flags
explicitly (`fase7.py`, `fase10.py`, `fase11.py`, `fase12.py`, and `segment.py`'s `V12`), so no result is affected.
The README now states the flags.

## Checked by the reviewer and found correct

`sha256sum -c docs/SHA256SUMS` (all entries); every per-file `.sha256`; the 27 tool md5s in the prereg tables
against `scripts/` and `versions/`; every number in the README table, the trail rows #1–#14 and the submission
draft against the RESULT, NOTE and ERRATUM files; the thresholds in the code against the README; the tests.
