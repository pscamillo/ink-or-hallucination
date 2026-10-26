"""Smoke test: the whole report runs on every OS and reaches the expected verdicts on synthetic segments."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import segment as sg
import synthetic


def _run(tmp_path, ink, invent=None):
    seg = synthetic.make(str(tmp_path / 'seg'), ink=ink, invent=invent)
    R = sg.run(seg, ['m1', 'm2', 'm3'], order='forward', win=96, log=lambda m: None)
    out = os.path.join(seg, 'inkcheck_report')
    assert os.path.isfile(os.path.join(out, 'report.html'))
    assert os.path.isfile(os.path.join(out, 'report.json'))
    return R


def test_shared_depth_dependent_strokes_read_as_ink(tmp_path):
    assert sg.overall(_run(tmp_path, ink=True)) == 'good'


def test_texture_only_is_not_called_ink(tmp_path):
    assert sg.overall(_run(tmp_path, ink=False)) == 'none'


def test_strokes_only_one_model_draws_are_flagged_in_that_model(tmp_path):
    R = _run(tmp_path, ink=True, invent='m2')
    flagged = {m: R['local'][m]['unsupported'] for m in ('m1', 'm2', 'm3')}
    assert flagged['m2'] > max(flagged['m1'], flagged['m3'])


def test_mirror_note_does_not_change_the_verdict(tmp_path):
    R = _run(tmp_path, ink=True)
    tri = R['triangle']
    for k in list(tri['pairs']):                       # make the other-order maps agree strongly among themselves
        a, b = k.split(' x ')
        if a.endswith('_other') and b.endswith('_other'):
            tri['pairs'][k]['corr'] = 0.6
    lines = sg.summary(R)
    assert any(k == 'note' and 'among themselves' in t for k, t in lines)
    assert sg.overall(R) == 'good'
