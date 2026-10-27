"""Teste sintetico da v11 do check por janela (sem dado real).
Texto denso sintetico (tracos), 3 mapas = mesmo texto + ruido independente. Mascara: (a) larga, (b) faixa estreita
como no Paris4. Alvo com e sem letras inventadas so nele. Compara --null shift (v10) e --null swap (v11).
uso: python teste_v11.py"""
import os, sys, json, subprocess, numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation
I = os.path.dirname(os.path.abspath(__file__)); O = f'{I}/teste_v11'; os.makedirs(O, exist_ok=True)
r = np.random.default_rng(7); H, W = 1400, 2600


def strokes(n, hmin=0):
    m = np.zeros((H, W), bool)
    for _ in range(n):
        y, x = r.integers(hmin + 40, H - 40), r.integers(40, W - 40); a = r.uniform(0, np.pi); L = r.integers(20, 60)
        t = np.arange(L); yy = (y + t * np.sin(a)).astype(int).clip(0, H - 1); xx = (x + t * np.cos(a)).astype(int).clip(0, W - 1)
        m[yy, xx] = True
    return binary_dilation(m, iterations=3)


text = strokes(2500).astype(np.float32)
amp = gaussian_filter(r.standard_normal((H, W)), 120); amp = (amp - amp.min()) / (amp.max() - amp.min())
text = text * (0.15 + 0.85 * amp)   # forca da tinta varia por regiao, como num mapa real
fk = np.zeros((H, W), np.float32)
for (y, x) in [(500, 600), (560, 1500), (760, 2100)]:
    for k in range(25):
        y0, x0 = y + r.integers(-90, 90), x + r.integers(-90, 90); a = r.uniform(0, np.pi)
        t = np.arange(50); fk[(y0 + t * np.sin(a)).astype(int), (x0 + t * np.cos(a)).astype(int)] = 1
fk = binary_dilation(fk > 0, iterations=3)
# apaga o texto real em volta das letras falsas (janela "pura")
from scipy.ndimage import distance_transform_edt
clear = distance_transform_edt(~fk) < 160


def mk(seed, base):
    q = np.random.default_rng(seed)
    return np.clip(gaussian_filter(base, 1.5) + 0.25 * gaussian_filter(q.standard_normal((H, W)), 1.0), 0.01, 1).astype(np.float32)


base = np.where(clear, 0, text)
maps = {n: mk(s, base) for n, s in (('a', 1), ('b', 2), ('c', 3))}
maps['a_fake'] = mk(1, np.maximum(base, fk.astype(np.float32)))
for n, m in maps.items():
    np.save(f'{O}/{n}.npy', m)
wide = np.ones((H, W), np.uint8); wide[:, :60] = 0
narrow = np.zeros((H, W), np.uint8); narrow[380:900, :] = 1           # faixa de ~2 janelas de altura
np.save(f'{O}/wide.npy', wide); np.save(f'{O}/narrow.npy', narrow)


def run(t, mask, null):
    out = f'{O}/{t}_{mask}_{null}.npz'
    p = subprocess.run([sys.executable, f'{I}/inkcheck_v11.py', 'local', f'{O}/{t}.npy', f'{O}/b.npy', f'{O}/c.npy',
                        '--mask', f'{O}/{mask}.npy', '--win', '256', '--energy-k', '1.25', '--null', null,
                        '--out-npz', out], capture_output=True, text=True)
    if p.returncode:
        print(p.stderr[-1500:]); sys.exit(1)
    j = json.loads(p.stdout); d = np.load(out)
    from scipy.ndimage import uniform_filter
    ff = uniform_filter(fk.astype(np.float32), int(d['win_px']))[np.ix_(d['cy'], d['cx'])]
    fi = uniform_filter((base > 0.05).astype(np.float32), int(d['win_px']))[np.ix_(d['cy'], d['cx'])]
    st = d['state']; onf = (ff > 0.02) & (fi < 0.01)   # janelas PURAS: falsa sem tinta real
    return j, int((onf & (st == 2)).sum()), int((onf & (st > 0)).sum()), int(((ff == 0) & (st == 2)).sum()), int(((ff == 0) & (st > 0)).sum())


for mask in ('wide', 'narrow'):
    for null in ('shift', 'swap'):
        j, fu, fj, cu, cj = run('a', mask, null)
        j2, fu2, fj2, cu2, cj2 = run('a_fake', mask, null)
        print(f'{mask:6s} {null:5s} | alvo limpo: julgadas {j["judged"]:3d} nao-conf {j["unsupported"]:2d} sem-nulo {j["no_null_windows"]:2d}'
              f' | alvo com falsas: puras marcadas {fu2}/{fj2}, alarme fora delas {cu2}/{cj2}, sem-nulo {j2["no_null_windows"]}')
