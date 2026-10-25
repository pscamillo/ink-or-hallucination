"""Para que lado a folha se curva, medido so pela malha (sem rotulo, sem umbilicus).

Normal da grade tifxyz: n = (dP/dcoluna) x (dP/dlinha), normalizada (convencao fixa deste script).
Para cada ponto p, olha vizinhos q a ~D voxels na grade: se a folha se curva para +n, (q-p).n > 0.
lado = fracao de pares com (q-p).n > 0. Perto de 1: +n aponta para o lado concavo (para dentro do rolo).
Perto de 0: +n aponta para fora. Perto de 0.5: plana demais para decidir.
Opcional --umb: compara com o umbilicus (fracao de pontos onde +n aponta para o centro).

uso: python curvatura.py PASTA_TIFXYZ [PASTA ...] [--D 300] [--umb UMBILICUS.json]
"""
import sys, json, glob, os, argparse
import numpy as np, tifffile

ap = argparse.ArgumentParser()
ap.add_argument('dirs', nargs='+'); ap.add_argument('--D', type=float, default=300)
ap.add_argument('--umb'); ap.add_argument('--seed', type=int, default=0)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)


def load_umb(path):
    d = json.load(open(path))
    pts = []
    def walk(o):
        if isinstance(o, (list, tuple)) and len(o) == 3 and all(isinstance(v, (int, float)) for v in o):
            pts.append(o)
        elif isinstance(o, dict):
            if all(k in o for k in ('x', 'y', 'z')):
                pts.append([o['x'], o['y'], o['z']])
            else:
                for v in o.values(): walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o: walk(v)
    walk(d)
    u = np.array(pts, float)
    print(f'umbilicus: {len(u)} pontos, faixa por coluna min {u.min(0).round(0)} max {u.max(0).round(0)}')
    return u


U = load_umb(a.umb) if a.umb else None

for d in a.dirs:
    P = np.stack([tifffile.imread(os.path.join(d, c + '.tif')).astype(np.float64) for c in 'xyz'], -1)
    ok = (P > 0).all(-1)
    meta = json.load(open(os.path.join(d, 'meta.json')))
    sc = meta.get('scale', [1, 1])[0]
    k = max(2, int(round(a.D * sc)))  # passos de grade ~ D voxels
    # normal por diferencas centrais
    dc = np.zeros_like(P); dr = np.zeros_like(P)
    dc[:, 1:-1] = P[:, 2:] - P[:, :-2]; dr[1:-1] = P[2:] - P[:-2]
    okn = ok.copy(); okn[:, 0] = okn[:, -1] = okn[0] = okn[-1] = False
    okn[:, 1:-1] &= ok[:, 2:] & ok[:, :-2]; okn[1:-1] &= ok[2:] & ok[:-2]
    n = np.cross(dc, dr); nn = np.linalg.norm(n, axis=-1, keepdims=True)
    n = n / np.maximum(nn, 1e-9); okn &= nn[..., 0] > 0
    H, W = ok.shape
    ii, jj = np.nonzero(okn)
    if len(ii) == 0:
        print(d, 'sem pontos validos'); continue
    s = rng.choice(len(ii), min(20000, len(ii)), replace=False); ii, jj = ii[s], jj[s]
    pos = tot = 0; vs = []
    for di, dj in [(k, 0), (-k, 0), (0, k), (0, -k)]:
        i2, j2 = ii + di, jj + dj
        m = (i2 >= 0) & (i2 < H) & (j2 >= 0) & (j2 < W)
        m[m] &= ok[i2[m], j2[m]]
        v = ((P[i2[m], j2[m]] - P[ii[m], jj[m]]) * n[ii[m], jj[m]]).sum(-1)
        pos += (v > 0).sum(); tot += len(v); vs.append(v)
    v = np.concatenate(vs); dist = k / sc
    forte = np.abs(v) > 0.02 * dist          # so pares com flecha clara (> 2% da distancia)
    lado = (v[forte] > 0).mean() if forte.any() else 0.5
    txt = '+n = DENTRO (concavo)' if lado > 0.6 else '+n = FORA' if lado < 0.4 else 'indeciso'
    out = (f'{os.path.basename(os.path.normpath(d)):28s} grade {H}x{W} D~{dist:.0f}vx  pares {tot:6d} fortes {forte.mean():.2f}'
           f'  flecha media {np.median(v):+6.1f}vx  lado {lado:.3f}  {txt}')
    if U is not None:
        p = P[ii, jj]; nv = n[ii, jj]
        zc = 2 if np.ptp(U[:, 2]) >= np.ptp(U[:, 0]) else 0  # coluna do eixo do rolo
        order = np.argsort(U[:, zc])
        c = np.stack([np.interp(p[:, 2], U[order, zc], U[order, q]) for q in range(3)], -1)
        if zc == 0:  # umbilicus em z,y,x
            c = c[:, ::-1]
        r = c - p; r[:, 2] = 0
        f = ((r * nv).sum(-1) > 0).mean()
        out += f'  | umbilicus: +n para o centro em {f:.3f} dos pontos'
    print(out)
