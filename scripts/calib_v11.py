"""Calibracao v11 (exploratoria, declarada): o nulo novo (--null swap) contra o antigo (--null shift) no PHerc0343P,
com as mesmas letras falsas da calibracao 3 (calib_local3/, so em area sem tinta na camera do KLAVIS).
Mede, para cada nulo: falso alarme nos mapas bons (rv2, rv3, hecate, v8), BASE (cego) como alvo, e no rv2+falsas
as janelas puras (falsa, sem tinta real) e mistas (falsa + tinta real) marcadas. Janela 288 px, energia 1.25.
uso: python -u calib_v11.py    (usa inkcheck_v11.py; NAO toca no inkcheck.py da rodada selada)"""
import os, sys, json, subprocess, numpy as np
I = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, I)
import inkcheck_v11 as ik
from scipy.ndimage import uniform_filter
K = f'{I}/p343/ir-truth-9um'; M = f'{K}/data/valid.png'
maps = {'v8': f'{I}/p343/v8in_no-reverse.npy', 'hecate': f'{K}/maps/hecate-9.6um.png',
        'rv2': f'{K}/maps/reader-v2.png', 'rv3': f'{K}/maps/reader-v3.png'}
O = f'{I}/calib_v11'; os.makedirs(O, exist_ok=True)
fake = np.load(f'{I}/calib_local3/fake_mask.npy'); rv2f = f'{I}/calib_local3/rv2_fake.npy'
ink = ik.load(f'{K}/data/truth_ink.png') > 0


def frac_at(m, cy, cx, w):
    f = uniform_filter(m.astype(np.float32), w, mode='constant')
    return f[np.ix_(np.minimum(cy, f.shape[0] - 1), np.minimum(cx, f.shape[1] - 1))]


def run(tag, target, others, null):
    out = f'{O}/{tag}_{null}.npz'
    r = subprocess.run([sys.executable, f'{I}/inkcheck_v11.py', 'local', target, *others, '--mask', M, '--win', '288',
                        '--energy-k', '1.25', '--null', null, '--out-npz', out], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:]); sys.exit(1)
    j = json.loads(r.stdout); d = np.load(out); W = int(d['win_px'])
    return j, d['state'], frac_at(ink, d['cy'], d['cx'], W), frac_at(fake, d['cy'], d['cx'], W)


for null in ('shift', 'swap'):
    print(f'\n== nulo {null}', flush=True)
    j, st, fi, ff = run('rv2_falsas', rv2f, [q for n, q in maps.items() if n != 'rv2'], null)
    sel = ff > 0.02; pure = sel & (fi < 0.01); mixed = sel & (fi >= 0.02); clean = ff == 0
    print(f'   rv2+falsas: puras marcadas {int((pure & (st == 2)).sum())}/{int((pure & (st > 0)).sum())}'
          f'  mistas {int((mixed & (st == 2)).sum())}/{int((mixed & (st > 0)).sum())}'
          f'  alarme sem falsa {int((clean & (st == 2)).sum())}/{int((clean & (st > 0)).sum())}  sem-nulo {j["no_null_windows"]}', flush=True)
    for n, p in list(maps.items()) + [('BASE', f'{I}/p343/base/BASE.npy')]:
        j, st, fi, _ = run(n, p, [q for nn, q in maps.items() if nn != n], null)
        jj = st > 0; u = st == 2
        print(f'   {n:7s} julgadas {int(jj.sum()):4d}  nao-conf {int(u.sum()):3d} ({u.sum() / max(1, jj.sum()):.2f})  sem-nulo {j["no_null_windows"]:3d}'
              f'  tinta real nas nao-conf {fi[u].mean() if u.any() else float("nan"):.3f}  nas conf {fi[st == 1].mean() if (st == 1).any() else float("nan"):.3f}', flush=True)
