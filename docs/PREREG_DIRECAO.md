# PREREG — a per-window physical signal that does not depend on models agreeing (ink-or-hallucination)

Date: 2026-10-24. Author: Paulo Sergio Camillo. Written BEFORE D has been computed for any window.

## Why

The triangle and the windowed check measure agreement between models. A stroke that every model shares passes them,
even if it is not ink. Real ink has depth, though: it sits on one face of the sheet, so a 2.5D model sees it only
when the layers are stacked in the right order. A pattern that comes from papyrus texture, or from the model
itself, has no reason to vanish when the stack is reversed.

## Measure

For each window judged by v12, on each predicted-order map (ink9, rv2, rv3):

> D = stroke energy in the predicted-order map / stroke energy in the **same model's** wrong-order map

Stroke energy is the windowed std of the 2–20 px band. D uses one model only.

## Groups

The groups have the same definitions as PREREG_NATURAIS (sha256 0083c589…):
- natural hallucination: label ink < 0.5% in the window;
- real ink: label ink ≥ 5%.

The windows are the same .npz windows: Set B = PHercParis4 (`fase7/`), Set A = 12 segments (`calib_v12/A/`).

The labels were read for the natural-hallucination split in RESULT_V12. D itself has not been computed.

## Criterion (D1, per set)

At least 20 windows in each group, AND D lower in natural hallucinations than in real ink: one-sided Mann-Whitney
p < 0.01 and AUC ≥ 0.65.

Reported: medians and quartiles of D, and the fraction of each group with D < 1.5, 2 and 3. No D threshold is
chosen here; turning D into a rule would need its own test.

## Known limits, stated now

- The wrong-order map still keeps some ink signal on contaminated data. Wrong-order AUC is 0.54–0.64 on
  PHercParis4, so D is compressed.
- Unlabelled real ink inside the "natural" group works against the criterion.

Script: `direcao.py`, md5 84e9f724a464bbda4765d7fab78aa4f1.
