"""PREREG_DIRECAO: um sinal FISICO por janela, que nao depende de os modelos concordarem.
Tinta real tem profundidade: o traco some quando a ordem das camadas e invertida. Para cada janela julgada (v12) de
cada mapa da ordem prevista: D = energia do traco (banda 2-20 px) no mapa da ordem prevista / a mesma energia no mapa
do MESMO modelo na ordem errada. Compara D entre 'alucinacao natural' (rotulo < 0.5% de tinta) e 'tinta real'
(rotulo >= 5%), com as mesmas definicoes de naturais.py.
  conjunto B: PHercParis4 (npz do fase7, mapas de fase5/)   conjunto A: 12 segmentos (npz do calib_v12)
uso: python direcao.py"""
import os, sys, json, numpy as np
from scipy.ndimage import uniform_filter
from scipy.stats import mannwhitneyu
I = os.path.expanduser('~/challenges/vesuvius/inkcheck'); sys.path.insert(0, I)
import inkcheck_v12 as ik
M = ('ink9', 'rv2', 'rv3'); NAT, REAL = 0.005, 0.05


def wenergy(path, v, win, cy, cx):
    b = ik.band(ik.load(path), v, 2, 20).astype(np.float32); w = v.astype(np.float32)
    n = np.maximum(uniform_filter(w, win, mode='constant'), 1e-9)
    m1 = uniform_filter(w * b, win, mode='constant') / n; m2 = uniform_filter(w * b * b, win, mode='constant') / n
    e = np.sqrt(np.maximum(m2 - m1 ** 2, 0))
    return e[np.ix_(np.minimum(cy, e.shape[0] - 1), np.minimum(cx, e.shape[1] - 1))]


def frac(img, win, cy, cx):
    a = np.load(img) > 0
    f = uniform_filter(a.astype(np.float32), win, mode='constant')
    return f[np.ix_(np.minimum(cy, a.shape[0] - 1), np.minimum(cx, a.shape[1] - 1))]


items = {'B (PHercParis4, cego)': [], 'A (12 segmentos)': []}
for s in sorted(os.listdir(f'{I}/fase7')):
    if s.startswith('phercparis4'):
        for m in M:
            items['B (PHercParis4, cego)'].append((f'{I}/fase7/{s}/local_{m}.npz', f'{I}/fase5/{s}/{m}.tif',
                                                   f'{I}/fase5/{s}/{m}_reverse.tif', f'{I}/fase5/{s}/mask.npy', f'{I}/fase5/{s}/ink.npy'))
r6 = json.load(open(f'{I}/fase6/resultado.json'))
for k, v in r6.items():
    if k.startswith('A/'):
        s = k.split('/')[1]; src = v['src']
        for m in M:
            items['A (12 segmentos)'].append((f'{I}/calib_v12/A/{s}/{m}.npz', f'{src}/{m}.tif', f'{src}/{m}_reverse.tif',
                                              f'{src}/mask.npy', f'{src}/ink.npy'))
for name, its in items.items():
    Dn, Dr = [], []
    for npz, fw, rv, mask, ink in its:
        d = np.load(npz); jj = d['state'] > 0
        if not jj.any():
            continue
        W = int(d['win_px']); cy, cx = d['cy'], d['cx']
        v = ik.valid_mask(ik.load(fw), mask) & ik.valid_mask(ik.load(rv), None)
        D = wenergy(fw, v, W, cy, cx) / np.maximum(wenergy(rv, v, W, cy, cx), 1e-9)
        fi = frac(ink, W, cy, cx)
        Dn += D[jj & (fi < NAT)].tolist(); Dr += D[jj & (fi >= REAL)].tolist()
    Dn, Dr = np.array(Dn), np.array(Dr)
    if len(Dn) < 20 or len(Dr) < 20:
        print(f'\n== {name}: poucas janelas (natural {len(Dn)}, real {len(Dr)}) -> D1 sem decisao'); continue
    U, p = mannwhitneyu(Dn, Dr, alternative='less'); auc = 1 - U / (len(Dn) * len(Dr))
    ok = p < 0.01 and auc >= 0.65
    print(f'\n== conjunto {name}')
    print(f'   D (ordem prevista / ordem errada, mesmo modelo): natural n={len(Dn)} mediana {np.median(Dn):.2f} '
          f'[p25 {np.percentile(Dn, 25):.2f}, p75 {np.percentile(Dn, 75):.2f}] | real n={len(Dr)} mediana {np.median(Dr):.2f} '
          f'[p25 {np.percentile(Dr, 25):.2f}, p75 {np.percentile(Dr, 75):.2f}]')
    print(f'   AUC (D menor nas naturais) {auc:.3f}  Mann-Whitney p {p:.2e}  ->  D1 {"PASS" if ok else "FAIL"}'
          f'  (criterio: >= 20 janelas em cada grupo, AUC >= 0.65, p < 0.01)')
    for t in (1.5, 2.0, 3.0):
        print(f'      D < {t}: naturais {np.mean(Dn < t):.2f}  real {np.mean(Dr < t):.2f}')
