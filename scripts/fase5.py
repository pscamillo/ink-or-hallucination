"""PREREG_PARIS4: ordem pela geometria (P1), triangulo (P2) e check por janela (P3) no PHercParis4.
Le geometria_paris4.tsv (previsoes ja gravadas). Rotulos so no bloco final.
  1) ink9, Reader v2, Reader V3 nas duas ordens (koine, janela de 17 centrada)
  2) triangulo --core-from <ordem prevista>                                    (sem rotulo)
  3) check por janela (v10, score corr, energia 1.25x, janela ~2.5 mm), cada mapa da ordem prevista
     contra os outros dois                                                      (sem rotulo)
  4) letras falsas do tamanho real (2.5 mm, traco 0.2 mm) plantadas no rv2 da ordem prevista, em posicoes
     sorteadas dentro da mascara (sem rotulo); check por janela no mapa adulterado
  5) so agora: AUC (P1, P2) e, para P3, separacao das janelas sobre falsas em puras (sem tinta real) e mistas
uso: python -u fase5.py
"""
import os, sys, json, subprocess, glob, zlib
import numpy as np, zarr, tifffile

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; LAB = f'{H}/villa_ink/ink-detection/labels_hf'; KO = f'{H}/villa_ink/ink-detection'
MAL = f'{I}/malhas_paris4/raw'
PY = sys.executable
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
OUT = f'{I}/fase5'; os.makedirs(OUT, exist_ok=True)
LETTER_MM, STROKE_MM, WIN_MM, FAKE_FRAC = 2.5, 0.2, 2.5, 0.02
sys.path.insert(0, I)
import inkcheck as ik
from scipy.ndimage import binary_dilation, gaussian_filter, uniform_filter


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


def maxz(p):
    a = arr(p); out = np.zeros(a.shape[1:], bool)
    for k in range(a.shape[0]):
        out |= np.asarray(a[k]) > 0
    return out


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:5]), r.stderr[-1500:]); sys.exit(1)
    return r.stdout


def um_per_px(seg, ren_shape):
    """tamanho do pixel do render, so pela malha: passo da grade (voxels de 2.4 um) / pixels por ponto"""
    x = tifffile.imread(f'{MAL}/{seg}/x.tif'); y = tifffile.imread(f'{MAL}/{seg}/y.tif'); z = tifffile.imread(f'{MAL}/{seg}/z.tif')
    P = np.stack([x, y, z], -1).astype(np.float64); ok = (P > 0).all(-1)
    d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    step_um = float(np.median(d)) * 2.4
    return step_um / (ren_shape[2] / x.shape[1])


def glyph(rng, h, sw):
    w = int(0.7 * h); c = np.zeros((h + 2 * sw, w + 2 * sw), bool)
    for _ in range(rng.integers(2, 5)):
        if rng.random() < 0.6:
            (y0, x0), (y1, x1) = rng.random(2) * [h, w], rng.random(2) * [h, w]
            t = np.linspace(0, 1, 4 * h); ys, xs = y0 + (y1 - y0) * t, x0 + (x1 - x0) * t
        else:
            cy, cx = rng.random(2) * [h, w]; r = (0.2 + 0.3 * rng.random()) * h
            a0 = rng.random() * 2 * np.pi; a = a0 + np.linspace(0, (0.8 + rng.random()) * np.pi, 4 * h)
            ys, xs = cy + r * np.sin(a), cx + r * np.cos(a)
        c[np.clip(ys, 0, h - 1).astype(int) + sw, np.clip(xs, 0, w - 1).astype(int) + sw] = True
    yy, xx = np.mgrid[-sw // 2:sw // 2 + 1, -sw // 2:sw // 2 + 1]
    return binary_dilation(c, structure=(yy ** 2 + xx ** 2) <= (sw / 2) ** 2)


def plant(base, mask, px_um, seed):
    rng = np.random.default_rng(seed); h = int(LETTER_MM * 1000 / px_um); sw = max(2, int(STROKE_MM * 1000 / px_um))
    fake = np.zeros(base.shape, bool); ys, xs = np.nonzero(mask[::16, ::16]); target = FAKE_FRAC * mask.sum()
    for _ in range(20000):
        if fake.sum() >= target:
            break
        k = rng.integers(len(ys)); y, x = ys[k] * 16, xs[k] * 16; g = glyph(rng, h, sw); gh, gw = g.shape
        if y + gh >= base.shape[0] or x + gw >= base.shape[1] or mask[y:y + gh, x:x + gw].mean() < 0.95:
            continue
        if fake[max(0, y - h // 3):y + gh + h // 3, max(0, x - h // 3):x + gw + h // 3].any():
            continue
        fake[y:y + gh, x:x + gw] |= g
    hi = float(np.percentile(base[mask], 99.5))
    soft = gaussian_filter(fake.astype(np.float32), max(1, sw / 4)); soft /= max(soft.max(), 1e-6)
    return np.maximum(base, soft * hi).astype(np.float32), fake, h, sw, hi


def local(target, others, mask, win, out):
    return json.loads(sh([PY, f'{I}/inkcheck.py', 'local', target, *others, '--mask', mask, '--win', str(win),
                          '--energy-k', '1.25', '--score', 'corr', '--out-npz', out], cwd=I))


rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/geometria_paris4.tsv')][1:]
segs = [(r[0], r[1], r[5]) for r in rows if r[5] in ('forward', 'reverse')]
print('segmentos com previsao:', [(s, p) for s, _, p in segs]); print('sem previsao:', [r[0] for r in rows if r[5] not in ('forward', 'reverse')])
res = {}
for seg, ren, pred in segs:
    o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True)
    shp = arr(ren).shape; N = shp[0]; ls = (N - 17) // 2
    for m, ck in CK.items():
        if os.path.exists(f'{o}/{m}.tif') and os.path.exists(f'{o}/{m}_reverse.tif'):
            continue
        sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', ren, ck, f'{o}/{m}.tif', '--model-type', 'auto',
            '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
            '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'], cwd=KO)
    if not os.path.exists(f'{o}/mask.npy'):
        np.save(f'{o}/mask.npy', maxz(glob.glob(f'{LAB}/{seg}/*supervision_mask.zarr')[0]).astype(np.uint8) * 255)
    maps = {}
    for m in CK:
        maps[f'{m}_f'] = f'{o}/{m}.tif'; maps[f'{m}_r'] = f'{o}/{m}_reverse.tif'
    suf = '_f' if pred == 'forward' else '_r'
    good = {m: maps[f'{m}{suf}'] for m in CK}
    tri = json.loads(sh([PY, f'{I}/inkcheck.py', 'triangle'] + [f'{k}={v}' for k, v in maps.items()] +
                        ['--mask', f'{o}/mask.npy', '--n', '300', '--min-ratio', '2.0', '--core-from'] + [f'{m}{suf}' for m in CK], cwd=I))
    json.dump(tri, open(f'{o}/triangulo.json', 'w'), indent=1)
    px = um_per_px(seg, shp); win = int(round(WIN_MM * 1000 / px))
    print(f'\n== {seg}  previsao {pred}  pixel {px:.2f} um  janela {win} px  core {tri["core"]}', flush=True)
    for k, v in tri['verdict'].items():
        print(f'   {k:7s} {v}', flush=True)
    loc = {}
    for m in CK:
        loc[m] = local(good[m], [good[q] for q in CK if q != m], f'{o}/mask.npy', win, f'{o}/local_{m}.npz')
        print(f'   local {m}: julgadas {loc[m]["judged"]}  nao confirmadas {loc[m]["unsupported"]}', flush=True)
    if not os.path.exists(f'{o}/rv2_falsas.npy'):
        mask = np.load(f'{o}/mask.npy') > 0
        fk, fmask, h, sw, hi = plant(ik.load(good['rv2']), mask, px, zlib.crc32(seg.encode()))
        np.save(f'{o}/rv2_falsas.npy', fk); np.save(f'{o}/fake_mask.npy', fmask)
        print(f'   letras falsas: altura {h} px, traco {sw} px, intensidade {hi:.3f}, {fmask.sum()} px', flush=True)
    lf = local(f'{o}/rv2_falsas.npy', [good[q] for q in CK if q != 'rv2'], f'{o}/mask.npy', win, f'{o}/local_rv2_falsas.npz')
    print(f'   local rv2+falsas: julgadas {lf["judged"]}  nao confirmadas {lf["unsupported"]}', flush=True)
    res[seg] = {'pred': pred, 'verdict': tri['verdict'], 'px_um': px, 'win_px': win, 'maps': maps}

print('\n######## SO AGORA OS ROTULOS ########', flush=True)
P1p, P1all, P2, FA_j, FA_u, DET_pure, DET_pure_n, DET_mix, DET_mix_n = [], [], [], 0, 0, 0, 0, 0, 0
for seg, ren, pred in segs:
    o = f'{OUT}/{seg}'
    if not os.path.exists(f'{o}/ink.npy'):
        np.save(f'{o}/ink.npy', maxz(glob.glob(f'{LAB}/{seg}/*inklabels.zarr')[0]).astype(np.uint8) * 255)
    auc = {k: json.loads(sh([PY, f'{I}/inkcheck.py', 'label', p, f'{o}/ink.npy', '--mask', f'{o}/mask.npy', '--n', '200'], cwd=I))['auc']
           for k, p in res[seg]['maps'].items()}
    suf, oth = ('f', 'r') if pred == 'forward' else ('r', 'f')
    contra = 0
    for m in CK:
        a_p, a_o = auc[f'{m}_{suf}'], auc[f'{m}_{oth}']
        if abs(a_p - a_o) >= 0.05:
            P1p.append(a_p > a_o)
        contra += a_p < a_o
    P1all.append(contra == 3)
    v = res[seg]['verdict']
    if all(auc[f'{m}_{suf}'] >= 0.70 for m in CK):
        P2.append(all(v[f'{m}_{suf}'] == 'consistent' for m in CK) and
                  all(v[k].startswith(('suspect', 'isolated')) for k in auc if auc[k] < 0.60))
    for m in CK:
        st = np.load(f'{o}/local_{m}.npz')['state']; FA_j += int((st > 0).sum()); FA_u += int((st == 2).sum())
    d = np.load(f'{o}/local_rv2_falsas.npz'); st = d['state']; W = int(d['win_px'])
    def at(img):
        a = np.load(img) > 0
        f = uniform_filter(a.astype(np.float32), W, mode='constant')
        return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]
    ff, fi = at(f'{o}/fake_mask.npy'), at(f'{o}/ink.npy')
    pure, mixed = (ff > 0.02) & (fi < 0.01), (ff > 0.02) & (fi >= 0.02)
    DET_pure += int((pure & (st == 2)).sum()); DET_pure_n += int(pure.sum())
    DET_mix += int((mixed & (st == 2)).sum()); DET_mix_n += int(mixed.sum())
    print(f'{seg:16s} prev {pred:8s} ' + '  '.join(f'{k} {auc[k]:.3f}' for k in auc) +
          f' | falsas puras {int((pure & (st == 2)).sum())}/{int(pure.sum())} mistas {int((mixed & (st == 2)).sum())}/{int(mixed.sum())}', flush=True)

p1 = (np.mean(P1p) >= 0.90 if P1p else False) and not any(P1all)
fa = FA_u / max(FA_j, 1); det = DET_pure / max(DET_pure_n, 1)
print(f'\nP1: {sum(P1p)}/{len(P1p)} pares com a ordem prevista melhor; segmentos com os 3 contra: {sum(P1all)} -> {"PASS" if p1 else "FAIL"}')
print(f'P2: {sum(P2)}/{len(P2)} segmentos elegiveis corretos -> {"PASS" if P2 and all(P2) else "FAIL" if P2 else "sem segmento elegivel"}')
print(f'P3a falso alarme nos mapas limpos: {FA_u}/{FA_j} = {fa:.3f} (criterio <= 0.05) -> {"PASS" if fa <= 0.05 else "FAIL"}')
print(f'P3b deteccao em janelas puras de letra falsa: {DET_pure}/{DET_pure_n} = {det:.3f} (criterio >= 0.40) -> {"PASS" if det >= 0.40 else "FAIL"}')
print(f'    (informativo) janelas mistas: {DET_mix}/{DET_mix_n}')
json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'maps'} for k, v in res.items()}, open(f'{OUT}/resultado.json', 'w'), indent=1)
