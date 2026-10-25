"""Calibracao v12 (EXPLORATORIA, declarada): regra 'floor' para julgar + score de tracos nao explicados (U).
Dados: conjunto A do fase6 (12 segmentos, ja vistos no RESULT_V11) e PHerc0343P (camera do KLAVIS). NAO usa o Paris4,
que fica para o teste selado.
Passo 1 (pesado, uma vez): inkcheck_v12 local --score both em cada alvo; grava npz com U, corr, nulo e estado.
  conjunto A: alvos = ink9, rv2, rv3 (ordem prevista) e rv2+falsas (as do fase6); julgar com --stroke floor e
              --floor = o mesmo modelo na ordem errada (para rv2+falsas: rv2 na ordem errada).
  343P: alvos = rv2, rv3, hecate, v8, BASE, rv2+falsas (calib_local3); julgar com a regra de energia 1.25 (nao ha
        mapa na ordem errada para todos) -- so para ver U em mapas bons x cego x falsas.
Passo 2 (leve): varre limiares de U offline (u_k, u_min) e imprime falso alarme, deteccao em puras e mistas.
uso: python -u calib_v12.py      (refaz so o que faltar; passo 2 sempre)"""
import os, sys, json, subprocess, numpy as np
from scipy.ndimage import uniform_filter
I = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable; IK = f'{I}/inkcheck_v12.py'
O = f'{I}/calib_v12'; os.makedirs(O, exist_ok=True)
M = ('ink9', 'rv2', 'rv3')
sys.path.insert(0, I)
import inkcheck_v12 as ik


def run(out, target, others, mask, win, extra):
    if os.path.exists(out):
        return
    r = subprocess.run([PY, IK, 'local', target, *others, '--mask', mask, '--win', str(win), '--score', 'both',
                        '--null', 'swap', '--n', '19', '--min-null', '10', '--out-npz', out] + extra,
                       capture_output=True, text=True, cwd=I)
    if r.returncode:
        print('ERRO', out, r.stderr[-1500:]); sys.exit(1)


def frac(img, d):
    a = np.load(img) > 0 if img.endswith('.npy') else ik.load(img) > 0
    W = int(d['win_px']); f = uniform_filter(a.astype(np.float32), W, mode='constant')
    return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]


jobs = []   # (grupo, tag, npz, ink_label, fake_mask or None)
res6 = json.load(open(f'{I}/fase6/resultado.json'))
for key, r in res6.items():
    S, seg = key.split('/')
    if S != 'A':
        continue
    src = r['src']; o = f'{O}/A/{seg}'; os.makedirs(o, exist_ok=True); win = r['win_px']; mask = f'{src}/mask.npy'
    good = {m: f'{src}/{m}.tif' for m in M}; bad = {m: f'{src}/{m}_reverse.tif' for m in M}
    for m in M:
        run(f'{o}/{m}.npz', good[m], [good[q] for q in M if q != m], mask, win, ['--stroke', 'floor', '--floor', bad[m]])
        jobs.append(('A', f'{seg}:{m}', f'{o}/{m}.npz', f'{src}/ink.npy', None))
    fk = f'{I}/fase6/A/{seg}/rv2_falsas.npy'
    run(f'{o}/rv2_falsas.npz', fk, [good[q] for q in M if q != 'rv2'], mask, win, ['--stroke', 'floor', '--floor', bad['rv2']])
    jobs.append(('A', f'{seg}:rv2+falsas', f'{o}/rv2_falsas.npz', f'{src}/ink.npy', f'{I}/fase6/A/{seg}/fake_mask.npy'))
    print('A', seg, 'ok', flush=True)

K = f'{I}/p343/ir-truth-9um'; MK = f'{K}/data/valid.png'
p343 = {'v8': f'{I}/p343/v8in_no-reverse.npy', 'hecate': f'{K}/maps/hecate-9.6um.png',
        'rv2': f'{K}/maps/reader-v2.png', 'rv3': f'{K}/maps/reader-v3.png'}
o = f'{O}/p343'; os.makedirs(o, exist_ok=True)
for n, p in list(p343.items()) + [('BASE', f'{I}/p343/base/BASE.npy'), ('rv2+falsas', f'{I}/calib_local3/rv2_fake.npy')]:
    others = [q for nn, q in p343.items() if nn != n.replace('+falsas', '')]
    run(f'{o}/{n}.npz', p, others, MK, 288, ['--stroke', 'energy', '--energy-k', '1.25'])
    jobs.append(('343P', n, f'{o}/{n}.npz', f'{K}/data/truth_ink.png', f'{I}/calib_local3/fake_mask.npy' if 'falsas' in n else None))
print('343P ok', flush=True)

# ---------- passo 2: limiares de U offline ----------
data = []
for g, tag, f, ink, fm in jobs:
    d = np.load(f); st = d['state']; jj = st > 0
    corr_fail = jj & ~(d['real'] > np.where(np.isnan(d['nmax']), np.inf, d['nmax']))
    U = d['U']; fi = frac(ink, d); ff = frac(fm, d) if fm else np.zeros_like(fi)
    data.append(dict(g=g, tag=tag, jj=jj, cf=corr_fail, U=U, fi=fi, ff=ff, fake=fm is not None,
                     blind=tag in ('BASE',), good=(fm is None and tag != 'BASE')))


def flagsU(x, uk, umin):
    h = x['jj'] & np.isfinite(x['U'])
    if not h.any():
        return h
    u = x['U'][h]; med = np.median(u); mad = np.median(np.abs(u - med))
    return h & (x['U'] >= max(umin, med + uk * 1.4826 * mad))


print('\nlinha base (so corr, v11): ', end='')
for g in ('A', '343P'):
    G = [x for x in data if x['g'] == g]
    fa = sum(int(x['cf'].sum()) for x in G if x['good']) / max(1, sum(int(x['jj'].sum()) for x in G if x['good']))
    pure = [(x['cf'] & (x['ff'] > 0.02) & (x['fi'] < 0.01), x['jj'] & (x['ff'] > 0.02) & (x['fi'] < 0.01)) for x in G if x['fake']]
    mix = [(x['cf'] & (x['ff'] > 0.02) & (x['fi'] >= 0.02), x['jj'] & (x['ff'] > 0.02) & (x['fi'] >= 0.02)) for x in G if x['fake']]
    print(f'[{g}] FA {fa:.3f}  puras {sum(int(a.sum()) for a, _ in pure)}/{sum(int(b.sum()) for _, b in pure)}'
          f'  mistas {sum(int(a.sum()) for a, _ in mix)}/{sum(int(b.sum()) for _, b in mix)}   ', end='')
print()
print(f'{"u_k":>4s} {"u_min":>5s} | ' + ' | '.join(f'[{g}] FA bons  puras   mistas   alarme-fora' for g in ('A', '343P')) + ' | BASE')
for uk in (2.0, 3.0, 4.0):
    for umin in (0.10, 0.15, 0.20, 0.30):
        line = f'{uk:4.1f} {umin:5.2f} | '
        for g in ('A', '343P'):
            G = [x for x in data if x['g'] == g]
            ju = js = 0; pu = pn = mu = mn = ou = on = 0
            for x in G:
                un = x['cf'] | flagsU(x, uk, umin)
                if x['good']:
                    ju += int(un.sum()); js += int(x['jj'].sum())
                if x['fake']:
                    p = x['jj'] & (x['ff'] > 0.02) & (x['fi'] < 0.01); mx = x['jj'] & (x['ff'] > 0.02) & (x['fi'] >= 0.02)
                    o_ = x['jj'] & (x['ff'] == 0)
                    pu += int((un & p).sum()); pn += int(p.sum()); mu += int((un & mx).sum()); mn += int(mx.sum())
                    ou += int((un & o_).sum()); on += int(o_.sum())
            line += f'      {ju / max(js, 1):.3f}  {pu:3d}/{pn:<3d} {mu:3d}/{mn:<4d} {ou:3d}/{on:<4d}   | '
        b = [x for x in data if x['blind']]
        line += ' '.join(f'{int((x["cf"] | flagsU(x, uk, umin)).sum())}/{int(x["jj"].sum())}' for x in b)
        print(line, flush=True)

print('\nU por grupo (mediana das janelas julgadas): ' + '  '.join(
    f'{x["g"]}:{x["tag"].split(":")[-1]}={np.nanmedian(x["U"][x["jj"]]):.2f}' for x in data if x['g'] == '343P'))
