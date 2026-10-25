"""PREREG_NATURAIS: o check por janela v12 marca as alucinacoes que os modelos produzem SOZINHOS?
'Alucinacao natural' = janela julgada (o mapa tem traco: energia >= 2x o piso da ordem errada) onde o rotulo de
tinta diz que nao ha tinta (fracao de tinta do rotulo na janela < 0.005, dentro da mascara de supervisao).
'Tinta real' = janela julgada com fracao de tinta do rotulo >= 0.05.
Compara a taxa de 'nao confirmada' nos dois grupos, mapas da ordem prevista (ink9, rv2, rv3), regra v12 recalculada
do npz com os parametros selados (u_k 3.0, u_min 0.20; corr contra o nulo swap).
  conjunto B: PHercParis4, npz do fase7.py (teste cego)
  conjunto A: os 12 segmentos, npz do calib_v12.py (a separacao por rotulo dos mapas bons nunca foi olhada)
uso: python naturais.py"""
import os, sys, json, numpy as np
from scipy.ndimage import uniform_filter
from scipy.stats import fisher_exact
I = os.path.expanduser('~/challenges/vesuvius/inkcheck'); M = ('ink9', 'rv2', 'rv3')
UK, UMIN, NAT, REAL = 3.0, 0.20, 0.005, 0.05


def unsupported(d):
    st = d['state']; jj = st > 0
    nmax = np.where(np.isnan(d['nmax']), np.inf, d['nmax'])
    cf = jj & ~(d['real'] > nmax)
    U = d['U']; h = jj & np.isfinite(U); fu = np.zeros_like(jj)
    if h.any():
        u = U[h]; med = np.median(u); mad = np.median(np.abs(u - med))
        fu = h & (U >= max(UMIN, med + UK * 1.4826 * mad))
    return jj, cf | fu


def frac(img, d):
    a = np.load(img) > 0; W = int(d['win_px'])
    f = uniform_filter(a.astype(np.float32), W, mode='constant')
    return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]


sets = {'B (PHercParis4, cego)': [(f'{I}/fase7/{s}/local_{m}.npz', f'{I}/fase5/{s}/ink.npy')
                                  for s in sorted(os.listdir(f'{I}/fase7')) if s.startswith('phercparis4') for m in M]}
r6 = json.load(open(f'{I}/fase6/resultado.json'))
sets['A (12 segmentos)'] = [(f'{I}/calib_v12/A/{k.split("/")[1]}/{m}.npz', f'{v["src"]}/ink.npy')
                            for k, v in r6.items() if k.startswith('A/') for m in M]
verd = {}
for name, items in sets.items():
    nu = nn = ru = rn = 0; per = {}
    for f, ink in items:
        if not os.path.exists(f):
            print('falta', f); continue
        d = np.load(f); jj, un = unsupported(d); fi = frac(ink, d)
        nat, real = jj & (fi < NAT), jj & (fi >= REAL)
        nu += int((un & nat).sum()); nn += int(nat.sum()); ru += int((un & real).sum()); rn += int(real.sum())
        m = os.path.basename(f).replace('local_', '').replace('.npz', '')
        p = per.setdefault(m, [0, 0, 0, 0]); p[0] += int((un & nat).sum()); p[1] += int(nat.sum()); p[2] += int((un & real).sum()); p[3] += int(real.sum())
    a = nu / max(nn, 1); b = ru / max(rn, 1)
    _, p = fisher_exact([[nu, nn - nu], [ru, rn - ru]], alternative='greater') if nn and rn else (None, 1.0)
    ok = nn >= 20 and a >= 2 * b and p < 0.01
    print(f'\n== conjunto {name}')
    print(f'   alucinacao natural (julgada, rotulo sem tinta): nao confirmadas {nu}/{nn} = {a:.3f}')
    print(f'   tinta real (julgada, rotulo >= 5% tinta):       nao confirmadas {ru}/{rn} = {b:.3f}')
    print(f'   razao {a / b if b else float("inf"):.2f}  Fisher p {p:.2e}  ->  N1 {"PASS" if ok else "FAIL"}'
          f'  (criterio: >= 20 janelas naturais, taxa >= 2x a da tinta real, p < 0.01)')
    for m, (x1, x2, x3, x4) in per.items():
        print(f'      {m:5s} natural {x1}/{x2}  real {x3}/{x4}')
