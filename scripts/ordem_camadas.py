"""Em que sentido da normal as camadas de um render foram empilhadas?

Pega uma janela da malha tifxyz, amostra o CT em p + t*n (t = -T..T voxels, n = (dP/dcol) x (dP/dlin)),
e correlaciona cada amostra com cada camada do render (reduzida para a grade da malha).
Se a camada i casa com t = a + b*i, b > 0 quer dizer: camada cresce ao longo de +n.

uso: python ordem_camadas.py TIFXYZ LAYERS_DIR_OU_ZARR CT_ZARR_URL [--win 48] [--T 16] [--at I J]
CT_ZARR_URL: o nivel 0 do volume (array z,y,x), ex. .../20250521151220-8.640um-1.2m-116keV-masked.zarr/0
"""
import sys, os, glob, json, argparse
import numpy as np, tifffile, zarr

ap = argparse.ArgumentParser()
ap.add_argument('tifxyz'); ap.add_argument('layers'); ap.add_argument('ct')
ap.add_argument('--win', type=int, default=48); ap.add_argument('--T', type=int, default=16)
ap.add_argument('--at', type=int, nargs=2)
a = ap.parse_args()

P = np.stack([tifffile.imread(os.path.join(a.tifxyz, c + '.tif')).astype(np.float64) for c in 'xyz'], -1)
ok = (P > 0).all(-1)
sc = json.load(open(os.path.join(a.tifxyz, 'meta.json')))['scale'][0]
H, W = ok.shape
w = a.win
if a.at:
    i0, j0 = a.at
else:  # janela toda valida mais perto do centro
    from scipy.ndimage import uniform_filter
    full = uniform_filter(ok.astype(float), w) > 0.999
    ii, jj = np.nonzero(full)
    k = np.argmin((ii - H / 2) ** 2 + (jj - W / 2) ** 2); i0, j0 = ii[k] - w // 2, jj[k] - w // 2
Pw = P[i0 - 1:i0 + w + 1, j0 - 1:j0 + w + 1]
n = np.cross(Pw[1:-1, 2:] - Pw[1:-1, :-2], Pw[2:, 1:-1] - Pw[:-2, 1:-1])
n /= np.linalg.norm(n, axis=-1, keepdims=True)
p = Pw[1:-1, 1:-1]
print(f'janela grade [{i0}:{i0+w}, {j0}:{j0+w}]  centro xyz {p[w//2, w//2].round(0)}  n {n[w//2, w//2].round(3)}')

# CT: le a caixa uma vez
T = a.T
lo = np.floor(np.minimum((p - T * np.abs(n)).reshape(-1, 3).min(0), (p + T * np.abs(n)).reshape(-1, 3).min(0)) - 2).astype(int)
hi = np.ceil(np.maximum((p - T * np.abs(n)).reshape(-1, 3).max(0), (p + T * np.abs(n)).reshape(-1, 3).max(0)) + 2).astype(int)
ct = zarr.open_array(a.ct, mode='r')
print('CT', ct.shape, ct.dtype, 'caixa xyz', lo, hi)
box = np.asarray(ct[lo[2]:hi[2], lo[1]:hi[1], lo[0]:hi[0]]).astype(np.float32)
print('caixa lida', box.shape, 'media', box.mean().round(1))
from scipy.ndimage import map_coordinates
ts = np.arange(-T, T + 1)
S = []
for t in ts:
    q = p + t * n - lo  # xyz relativo
    S.append(map_coordinates(box, [q[..., 2].ravel(), q[..., 1].ravel(), q[..., 0].ravel()], order=1).reshape(w, w))
S = np.array(S)

# camadas: pasta de tifs ou zarr (array ou grupo com '0'), eixo 0 = camada.
# O render pode ter outra resolucao que a grade: usa a razao de tamanhos (render / grade) em cada eixo.
from scipy.ndimage import zoom
if os.path.isdir(a.layers) and glob.glob(os.path.join(a.layers, '*.tif')):
    fs = sorted(glob.glob(os.path.join(a.layers, '*.tif')))
    get = lambda k, sl: tifffile.imread(fs[k])[sl]
    nl, Hr, Wr = len(fs), *tifffile.imread(fs[0]).shape
else:
    g = zarr.open(a.layers, mode='r')
    arr = g['0'] if not hasattr(g, 'shape') else g
    get = lambda k, sl: np.asarray(arr[(k,) + sl])
    nl, Hr, Wr = arr.shape
fy, fx = Hr / H, Wr / W
print(f'render {nl} camadas {Hr}x{Wr}; pixels por ponto de grade {fy:.3f} x {fx:.3f}')
sl = (slice(int(round(i0 * fy)), int(round((i0 + w) * fy))), slice(int(round(j0 * fx)), int(round((j0 + w) * fx))))
L = []
for k in range(nl):
    im = get(k, sl).astype(np.float32)
    L.append(zoom(im, (w / im.shape[0], w / im.shape[1]), order=1)[:w, :w])
L = np.array(L)


def z(x):
    x = x.reshape(len(x), -1); x = x - x.mean(1, keepdims=True); return x / (x.std(1, keepdims=True) + 1e-6)
C = z(L) @ z(S).T / (w * w)  # camada x t
best = ts[C.argmax(1)]
print('camada -> t de maior correlacao (corr):')
for i in range(len(L)):
    print(f'  {i:2d} -> t {best[i]:+3d}  ({C[i].max():.2f})')
b = np.polyfit(np.arange(len(L)), best, 1)[0]
print(f'inclinacao t por camada = {b:+.2f}  =>  camadas crescem ao longo de {"+n" if b > 0 else "-n"}'
      f'  (camada 0 do lado {"-n" if b > 0 else "+n"})')
