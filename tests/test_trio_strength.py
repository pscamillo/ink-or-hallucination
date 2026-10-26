"""The sealed tie-break (PREREG_HELDOUT2) on hand-made triangle pairs."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import segment as sg


def _tri(f, r, cross=0.1):
    names = [f'{m}_{s}' for m in ('a', 'b', 'c') for s in 'fr']
    pairs = {}
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            same = x[-1] == y[-1]
            pairs[f'{x} x {y}'] = {'corr': (f if x[-1] == 'f' else r) if same else cross}
    return {'pairs': pairs}


def test_stronger_forward_trio_decides():
    t = sg.trio_strength(_tri(0.385, 0.294))          # PHerc0500P2 in RESULT_HELDOUT2: ratio 1.31
    assert t['order'] == 'forward' and abs(t['ratio'] - 0.385 / 0.294) < 1e-9


def test_stronger_reverse_trio_decides():
    assert sg.trio_strength(_tri(0.2, 0.5))['order'] == 'reverse'


def test_close_trios_give_no_verdict():
    assert sg.trio_strength(_tri(0.45, 0.39))['order'] is None   # PHerc1447 w058-like ratio 1.16


def test_needs_three_models_per_side():
    t = _tri(0.4, 0.2)
    t['pairs'] = {k: v for k, v in t['pairs'].items() if 'c_' not in k}
    with pytest.raises(ValueError):
        sg.trio_strength(t)
