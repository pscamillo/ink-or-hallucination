"""from_battery.py on a fake ink-sdk battery folder: two grids, three profiles, order decided from the maps."""
import json
import os
import subprocess
import sys

import numpy as np
import tifffile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import synthetic
import from_battery as fb


def _fake_battery(tmp_path):
    seg = synthetic.make(str(tmp_path / 'seg'), ink=True)
    bat = tmp_path / 'battery'; cells = []
    for k, (m, prof) in enumerate((('m1', 'ink_9um@reader-v3'), ('m2', 'ink_9um@reader-v2-step040000'),
                                   ('m3', 'ink_9um@scrollprize-seed43-step75000'))):
        d = bat / 'cells' / prof.replace('@', '_') / 'c+0_s1'; d.mkdir(parents=True)
        for src, dst in (('', 'probability'), ('_reverse', 'probability_reverse')):
            a = tifffile.imread(os.path.join(seg, f'{m}{src}.tif')).astype(np.float32) / 255
            if k == 2:
                a = fb.resize(a, (700, 700))                           # a resampled profile: coarser grid
            np.save(d / f'{dst}.npy', a)
        cells.append({'profile': prof, 'centre': 0, 'step': 1, 'ok': True, 'dir': str(d)})
    (bat / 'BATTERY.json').write_text(json.dumps({'surface_volume': str(tmp_path / 'none.zarr'), 'pixel_um': 9.6,
                                                  'cells': cells}), encoding='utf-8')
    return bat


def test_short_names():
    assert fb.short('ink_9um@reader-v2-step040000') == 'reader-v2'
    assert fb.short('ink_9um@scrollprize-seed43-step75000') == 'seed43'
    assert fb.short('ink_9um@dense-native-step016000') == 'dense-native'


def test_battery_folder_runs_and_picks_forward(tmp_path):
    bat = _fake_battery(tmp_path); out = tmp_path / 'kit'
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'from_battery.py'), str(bat), str(out), '--win-mm', str(96 * 9.6 / 1000)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    prov = json.load(open(out / 'from_battery.json'))
    assert prov['order'] == 'forward' and prov['grid'] == [768, 768]
    assert np.load(out / 'seed43.npy').shape == (768, 768)
    assert (out / 'inkcheck_report' / 'report.html').is_file()
