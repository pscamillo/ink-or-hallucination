"""PREREG_V12: check por janela v12 (piso pelo mapa na ordem errada + tracos nao explicados) no PHercParis4 (fase5/),
o teste cego: nenhuma versao v11/v12 do check por janela rodou nesses mapas. Sem rodar modelo.
  1) cada mapa da ordem prevista (ink9, rv2, rv3) contra os outros dois; piso = o mesmo modelo na ordem errada
  2) o mesmo, com a v11 selada (PREREG_V11, conjunto B) -- feito pelo fase6.py, nao aqui
  3) rv2+falsas (as letras que o fase5 ja plantou), piso = rv2 na ordem errada
  4) mapas da ordem errada como alvo (informativo; julgados pela regra de energia 1.25, pois nao ha piso para eles)
  5) so agora: rotulo de tinta, SO para separar janelas puras e mistas
uso: python -u fase7.py
"""
import os, sys, json, subprocess
import numpy as np
from scipy.ndimage import uniform_filter
H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; PY = sys.executable; IK = f'{I}/inkcheck_v12.py'; OUT = f'{I}/fase7'
M = ('ink9', 'rv2', 'rv3')
V12 = ['--score', 'both', '--null', 'swap', '--n', '19', '--min-null', '10', '--tol-px', '6', '--ink-rel', '0.5',
       '--min-ink', '0.005', '--u-k', '3.0', '--u-min', '0.20']


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=I)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:5]), r.stderr[-1500:]); sys.exit(1)
    return json.loads(r.stdout)


res5 = json.load(open(f'{I}/fase5/resultado.json'))
rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/geometria_paris4.tsv')][1:]
segs = [(r[0], r[5]) for r in rows if r[5] in ('forward', 'reverse')]
for seg, pred in segs:
    src = f'{I}/fase5/{seg}'; o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True)
    win = int(res5[seg]['win_px']); mask = f'{src}/mask.npy'
    suf, oth = ('', '_reverse') if pred == 'forward' else ('_reverse', '')
    good = {m: f'{src}/{m}{suf}.tif' for m in M}; bad = {m: f'{src}/{m}{oth}.tif' for m in M}
    print(f'\n== {seg}  prev {pred}  janela {win} px', flush=True)
    for m in M:
        j = sh([PY, IK, 'local', good[m], *[good[q] for q in M if q != m], '--mask', mask, '--win', str(win),
                '--stroke', 'floor', '--floor', bad[m], '--floor-k', '2.0', '--out-npz', f'{o}/local_{m}.npz'] + V12)
        print(f'   {m} previsto: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d} (U {j["u_flagged"]})  sem-nulo {j["no_null_windows"]}', flush=True)
    for m in M:
        j = sh([PY, IK, 'local', bad[m], *[good[q] for q in M if q != m], '--mask', mask, '--win', str(win),
                '--stroke', 'energy', '--energy-k', '1.25', '--out-npz', f'{o}/local_{m}_errado.npz'] + V12)
        print(f'   {m} ordem errada: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d}', flush=True)
    j = sh([PY, IK, 'local', f'{src}/rv2_falsas.npy', *[good[q] for q in M if q != 'rv2'], '--mask', mask, '--win', str(win),
            '--stroke', 'floor', '--floor', bad['rv2'], '--floor-k', '2.0', '--out-npz', f'{o}/local_rv2_falsas.npz'] + V12)
    print(f'   rv2+falsas: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d} (U {j["u_flagged"]})  sem-nulo {j["no_null_windows"]}', flush=True)

print('\n######## SO AGORA OS ROTULOS (so para separar janelas puras e mistas) ########', flush=True)
t = dict(j=0, u=0, nn=0, cand=0, bj=0, bu=0, pu=0, pn=0, mu=0, mn=0, ou=0, on=0)
for seg, pred in segs:
    src = f'{I}/fase5/{seg}'; o = f'{OUT}/{seg}'
    for m in M:
        d = np.load(f'{o}/local_{m}.npz'); st = d['state']
        t['j'] += int((st > 0).sum()); t['u'] += int((st == 2).sum()); t['nn'] += int(d['no_null'].sum())
        t['cand'] += int((st > 0).sum() + d['no_null'].sum())
        st = np.load(f'{o}/local_{m}_errado.npz')['state']; t['bj'] += int((st > 0).sum()); t['bu'] += int((st == 2).sum())
    d = np.load(f'{o}/local_rv2_falsas.npz'); st = d['state']; W = int(d['win_px'])
    def at(img):
        a = np.load(img) > 0
        f = uniform_filter(a.astype(np.float32), W, mode='constant')
        return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]
    ff, fi = at(f'{src}/fake_mask.npy'), at(f'{src}/ink.npy')
    pure, mixed, clean = (ff > 0.02) & (fi < 0.01), (ff > 0.02) & (fi >= 0.02), ff == 0
    t['pu'] += int((pure & (st == 2)).sum()); t['pn'] += int((pure & (st > 0)).sum())
    t['mu'] += int((mixed & (st == 2)).sum()); t['mn'] += int((mixed & (st > 0)).sum())
    t['ou'] += int((clean & (st == 2)).sum()); t['on'] += int((clean & (st > 0)).sum())
    print(f'{seg:16s} falsas puras {int((pure & (st == 2)).sum())}/{int((pure & (st > 0)).sum())}'
          f'  mistas {int((mixed & (st == 2)).sum())}/{int((mixed & (st > 0)).sum())}', flush=True)
fa = t['u'] / max(t['j'], 1); nn = t['nn'] / max(t['cand'], 1); det = t['pu'] / max(t['pn'], 1); mix = t['mu'] / max(t['mn'], 1)
print(f'\nQ1 falso alarme, mapas da ordem prevista: {t["u"]}/{t["j"]} = {fa:.3f} (criterio <= 0.10) -> {"PASS" if fa <= 0.10 else "FAIL"}')
print(f'Q2 janelas com traco e sem nulo: {t["nn"]}/{t["cand"]} = {nn:.3f} (criterio <= 0.05) -> {"PASS" if nn <= 0.05 else "FAIL"}')
print(f'Q3 letras falsas, janelas puras marcadas: {t["pu"]}/{t["pn"]} = {det:.3f} (criterio >= 0.60) -> '
      f'{"PASS" if t["pn"] and det >= 0.60 else "FAIL" if t["pn"] else "sem janela pura"}')
print(f'Q4 letras falsas, janelas MISTAS marcadas: {t["mu"]}/{t["mn"]} = {mix:.3f} (criterio >= 0.20) -> {"PASS" if t["mn"] and mix >= 0.20 else "FAIL"}')
print(f'   (informativo) alarme fora das falsas no rv2+falsas {t["ou"]}/{t["on"]}; mapas da ordem errada: nao-conf {t["bu"]}/{t["bj"]}')
