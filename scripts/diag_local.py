"""Por que o check por janela da alarme em texto denso? Diagnostico SEM rotulo (so os .npz que o check gravou).
Para cada janela julgada: correlacao real, maximo do nulo, energia relativa, cobertura da mascara (borda) e
distancia ate a borda da mascara. Compara confirmadas x nao confirmadas.
uso: python diag_local.py fase5/phercparis4-w00 [mais pastas]"""
import sys, os, numpy as np
from scipy.ndimage import distance_transform_edt
for d in sys.argv[1:]:
    mask = np.load(f'{d}/mask.npy') > 0
    dist = distance_transform_edt(mask)
    for m in ('ink9', 'rv2', 'rv3'):
        f = f'{d}/local_{m}.npz'
        if not os.path.exists(f):
            continue
        z = np.load(f); st = z['state']; W = int(z['win_px'])
        cy, cx = z['cy'], z['cx']
        dd = dist[np.ix_(np.minimum(cy, mask.shape[0] - 1), np.minimum(cx, mask.shape[1] - 1))] / W
        base = np.median(z['energy'][z['cov'] >= 0.5])
        print(f'== {os.path.basename(d)} {m}: janela {W} px, julgadas {int((st > 0).sum())}, nao-conf {int((st == 2).sum())}')
        for nome, s in (('confirmadas', 1), ('NAO confirm', 2)):
            k = st == s
            if not k.any():
                continue
            print(f'   {nome}: corr {np.median(z["real"][k]):.3f}  nulo_max {np.median(z["nmax"][k]):.3f}'
                  f'  energia/mediana {np.median(z["energy"][k]) / base:.2f}  cobertura {np.median(z["cov"][k]):.2f}'
                  f'  dist. borda (janelas) {np.median(dd[k]):.2f}  [{np.round(dd[k], 2).tolist()[:8]}]')
        k = st == 2
        for i, j in list(zip(*np.nonzero(k)))[:6]:
            print(f'      nao-conf em y {cy[i]} x {cx[j]}: corr {z["real"][i, j]:.3f} vs nulo {z["nmax"][i, j]:.3f}, '
                  f'cobertura {z["cov"][i, j]:.2f}, borda a {dd[i, j]:.2f} janelas')
