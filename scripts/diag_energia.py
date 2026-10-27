"""Por que o check por janela quase nao julga janelas no fase6? Diagnostico SEM rotulo de tinta.
Le so os .npz do fase6 e a mascara das letras falsas (plantadas por nos, nao e rotulo).
Por segmento: quantas janelas tem cobertura >= 0.5, a energia das janelas (mediana, p90, max) relativa a mediana,
quantas passariam de 1.25x, a energia do mapa da ordem ERRADA nas mesmas janelas (piso 'sem tinta' do mesmo
modelo), e a energia das janelas com letra falsa no rv2+falsas relativa a mediana.
uso: python diag_energia.py fase6/A/*/"""
import sys, os, numpy as np
from scipy.ndimage import uniform_filter
for d in sys.argv[1:]:
    d = d.rstrip('/'); seg = os.path.basename(d)
    if not os.path.exists(f'{d}/local_rv2.npz'):
        continue
    print(f'== {seg}')
    for m in ('ink9', 'rv2', 'rv3'):
        g, b = np.load(f'{d}/local_{m}.npz'), np.load(f'{d}/local_{m}_errado.npz')
        ok = g['cov'] >= 0.5; e = g['energy'][ok]; eb = b['energy'][ok]; med = np.median(e)
        print(f'   {m:5s} janelas com cobertura>=0.5: {ok.sum():3d} de {ok.size:3d} | energia/mediana p90 {np.percentile(e, 90) / med:.2f}'
              f' max {e.max() / med:.2f} | >=1.25x: {(e >= 1.25 * med).sum():3d} | ordem errada/certa (mediana) {np.median(eb) / med:.2f}'
              f' | certa >= 2x mediana da errada: {(e >= 2 * np.median(eb)).sum():3d}')
    if os.path.exists(f'{d}/local_rv2_falsas.npz') and os.path.exists(f'{d}/fake_mask.npy'):
        z = np.load(f'{d}/local_rv2_falsas.npz'); fm = np.load(f'{d}/fake_mask.npy') > 0; W = int(z['win_px'])
        ff = uniform_filter(fm.astype(np.float32), W, mode='constant')[np.ix_(np.minimum(z['cy'], fm.shape[0] - 1), np.minimum(z['cx'], fm.shape[1] - 1))]
        ok = z['cov'] >= 0.5; med = np.median(z['energy'][ok]); on = ok & (ff > 0.02)
        print(f'   rv2+falsas: janelas com falsa {on.sum():3d} | energia delas / mediana: '
              f'{np.round(np.sort(z["energy"][on] / med)[::-1][:8], 2).tolist()} | julgadas {int((z["state"][on] > 0).sum())}')
