"""PREREG_HELDOUT0841: the whole kit on PHerc0841, a scroll none of the three models was trained on.
Same protocol as PREREG_PARIS4 / PREREG_V12 / PREREG_NATURAIS; labels are read only in the last block.
  0) registration check, CT against CT (2.403 um surface volume vs 9.366 um), no model, no label
  1) layer-order rule from the 9.366 um mesh + CT (curvatura + ordem_camadas); triangle fallback if it abstains
  2) ink9 (seed43 step 60000, as in every sealed run), Reader v2, Reader V3, both orders (koine, centred 17 layers)
  3) triangle --core-from <predicted order>
  4) windowed check v12 (sealed settings) for each predicted-order map; wrong-order maps as targets (informative)
  5) invented letters planted in rv2 (fase5.py's planting, same parameters), windowed check on the tampered map
  6) only now: labels -> AUC (H1, H2), pure/mixed split (Q3, Q4), natural hallucinations (N1)
uso: python -u fase9.py
"""
import os, sys, json, subprocess, re, zlib
import numpy as np, zarr, tifffile
from scipy.ndimage import binary_dilation, gaussian_filter, uniform_filter, map_coordinates
from scipy.stats import fisher_exact

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; KO = f'{H}/villa_ink/ink-detection'; R = f'{H}/heldout0841'; OUT = f'{I}/fase9'
IK = f'{I}/inkcheck_v12.py'; PY = sys.executable
CT = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/0'
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
M = tuple(CK)
SEGS = ['20260220213127-w00', '20260220214732-auto_grown_20260220144552896', '20260221022814-auto_grown_20260220174252405']
VOX_UM = 9.366
LETTER_MM, STROKE_MM, WIN_MM, FAKE_FRAC = 2.5, 0.2, 2.5, 0.02          # = fase5.py
V12 = ['--score', 'both', '--null', 'swap', '--n', '19', '--min-null', '10', '--tol-px', '6', '--ink-rel', '0.5',
       '--min-ink', '0.005', '--u-k', '3.0', '--u-min', '0.20']        # = fase7.py
UK, UMIN, NAT, REAL = 3.0, 0.20, 0.005, 0.05                           # = naturais.py
REG_MAX_PX = 3
os.makedirs(OUT, exist_ok=True)


def sh(cmd, cwd=I, js=True):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:6]), r.stderr[-1500:], flush=True); sys.exit(1)
    return json.loads(r.stdout) if js else r.stdout


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


def resample(a, shape):
    """area-weighted resample of a 2D array to `shape` (the two grids share origin and extent: the meshes say so)"""
    a = np.asarray(a, np.float32); ry, rx = a.shape[0] / shape[0], a.shape[1] / shape[1]
    a = uniform_filter(a, (max(1, int(round(ry))), max(1, int(round(rx)))), mode='nearest')
    yy = (np.arange(shape[0]) + 0.5) * ry - 0.5; xx = (np.arange(shape[1]) + 0.5) * rx - 0.5
    out = np.empty(shape, np.float32)
    for i0 in range(0, shape[0], 512):
        Y, X = np.meshgrid(yy[i0:i0 + 512], xx, indexing='ij')
        out[i0:i0 + 512] = map_coordinates(a, [Y, X], order=1, mode='nearest')
    return out


def um_per_px(seg, sv_shape):
    m = f'{R}/{seg}/mesh_9um'
    P = np.stack([tifffile.imread(f'{m}/{c}.tif') for c in 'xyz'], -1).astype(np.float64); ok = (P > 0).all(-1)
    d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    return float(np.median(d)) * VOX_UM / (sv_shape[2] / P.shape[1])


def registration(seg, sv):
    """CT vs CT: centre layers of the 9.366 um surface volume against the 2.403 um one (level 2), stroke band,
    cross-correlation peak within +-20 px. No model, no label."""
    a = np.asarray(sv[12:16]).astype(np.float32).mean(0)
    s2 = zarr.open_array(f'{R}/{seg}/sv2_l2.zarr/2', mode='r')
    c = s2.shape[0] // 2
    b = resample(np.asarray(s2[c - 6:c + 7]).astype(np.float32).mean(0), a.shape)
    v = (a > 0) & (b > 0)
    def bp(x):
        x = np.where(v, x, x[v].mean()); x = gaussian_filter(x, 2) - gaussian_filter(x, 12); x = np.where(v, x, 0)
        return (x - x[v].mean()) / (x[v].std() + 1e-6) * v
    A, B = np.fft.fft2(bp(a)), np.fft.fft2(bp(b))
    cc = np.fft.fftshift(np.real(np.fft.ifft2(A * np.conj(B)))); cy, cx = cc.shape[0] // 2, cc.shape[1] // 2
    w = cc[cy - 20:cy + 21, cx - 20:cx + 21]; y, x = np.unravel_index(np.argmax(w), w.shape)
    peak = float(w.max() / v.sum()); dy, dx = int(y - 20), int(x - 20)
    return dy, dx, peak


def order_rule(seg, sv_path):
    mesh = f'{R}/{seg}/mesh_9um'
    cu = sh([PY, f'{I}/curvatura.py', mesh, '--D', '1000'], js=False)
    fl = float(re.search(r'flecha media\s+([-+0-9.]+)vx', cu).group(1)); out_n = fl < 0; decide_c = abs(fl) >= 20
    oc = win = None
    for w in (48, 32, 24):
        r = subprocess.run([PY, f'{I}/ordem_camadas.py', mesh, sv_path, CT, '--win', str(w)], capture_output=True, text=True, cwd=I)
        if r.returncode == 0:
            oc, win = r.stdout, w; break
    if oc is None:
        return {'prediction': None, 'why': 'ordem_camadas found no valid window', 'sagitta_vx': fl}
    b = float(re.search(r'inclinacao t por camada = ([-+0-9.]+)', oc).group(1))
    cmed = float(np.median([float(x) for x in re.findall(r'->\s*t\s*[-+]\d+\s+\(([-0-9.]+)\)', oc)]))
    decide_o = cmed >= 0.5 and abs(b) >= 0.5; grows_out = (b > 0) == out_n
    pred = ('reverse' if grows_out else 'forward') if (decide_c and decide_o) else None
    return {'sagitta_vx': fl, 'slope_layers': b, 'ct_match_median_corr': cmed, 'win': win, 'prediction': pred}


def glyph(rng, h, sw):                                                   # = fase5.py
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


def plant(base, mask, px_um, seed):                                      # = fase5.py
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


def load(p):
    a = tifffile.imread(p) if p.endswith('.tif') else np.load(p)
    return a.astype(np.float32) / 255.0 if a.dtype == np.uint8 else a.astype(np.float32)


def local(target, others, mask, win, floor, out, stroke='floor'):
    extra = ['--stroke', 'floor', '--floor', floor, '--floor-k', '2.0'] if stroke == 'floor' else ['--stroke', 'energy', '--energy-k', '1.25']
    return sh([PY, IK, 'local', target, *others, '--mask', mask, '--win', str(win), *extra, '--out-npz', out] + V12)


res = {}
for seg in SEGS:
    o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True); svp = f'{R}/{seg}/sv9.zarr'; sv = arr(svp)
    N = sv.shape[0]; ls = (N - 17) // 2; px = um_per_px(seg, sv.shape); win = int(round(WIN_MM * 1000 / px))
    dy, dx, peak = registration(seg, sv)
    shift = (0, 0) if max(abs(dy), abs(dx)) <= REG_MAX_PX else (dy, dx)
    print(f'\n== {seg}  {sv.shape}  pixel {px:.2f} um  window {win} px  | CT-CT registration peak ({dy},{dx}) '
          f'strength {peak:.3f} -> labels shifted by {shift}', flush=True)
    rule = order_rule(seg, svp); print('   order rule (before any model):', rule, flush=True)
    for m, ck in CK.items():
        if not (os.path.exists(f'{o}/{m}.tif') and os.path.exists(f'{o}/{m}_reverse.tif')):
            sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', svp, ck, f'{o}/{m}.tif', '--model-type', 'auto',
                '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
                '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'],
               cwd=KO, js=False)
    if not os.path.exists(f'{o}/mask.npy'):
        sup = resample(np.asarray(arr(f'{R}/{seg}/labels/supervision.zarr')) > 0, sv.shape[1:]) > 0.5
        sup = np.roll(sup, shift, (0, 1)) & (np.asarray(sv[ls + 8]) > 0)
        np.save(f'{o}/mask.npy', sup.astype(np.uint8) * 255)
    maps = {}
    for m in M:
        maps[f'{m}_f'] = f'{o}/{m}.tif'; maps[f'{m}_r'] = f'{o}/{m}_reverse.tif'
    pred, how = rule['prediction'], 'rule'
    if pred is None:
        t0 = sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in maps.items()] + ['--mask', f'{o}/mask.npy', '--n', '300', '--min-ratio', '2.0'])
        side = {c[-1] for c in t0['core']}
        pred = 'forward' if side == {'f'} and len(t0['core']) >= 3 else 'reverse' if side == {'r'} and len(t0['core']) >= 3 else None
        how = 'triangle fallback'
        print(f'   triangle fallback: core {t0["core"]} -> {pred}', flush=True)
    res[seg] = {'shape': list(sv.shape), 'px_um': px, 'win_px': win, 'reg': [dy, dx, peak], 'shift': list(shift),
                'rule': rule, 'pred': pred, 'pred_from': how, 'maps': maps}
    if pred is None:
        print('   order unresolved: the kit gives no verdict on this segment (no windowed check)', flush=True); continue
    suf, oth = ('_f', '_r') if pred == 'forward' else ('_r', '_f')
    good = {m: maps[m + suf] for m in M}; bad = {m: maps[m + oth] for m in M}
    tri = sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in maps.items()] + ['--mask', f'{o}/mask.npy', '--n', '300',
             '--min-ratio', '2.0', '--core-from'] + [m + suf for m in M])
    json.dump(tri, open(f'{o}/triangulo.json', 'w', encoding='utf-8'), indent=1); res[seg]['verdict'] = tri['verdict']
    print(f'   predicted {pred} ({how})  core {tri["core"]}', flush=True)
    for k, v in tri['verdict'].items():
        print(f'      {k:7s} {v}', flush=True)
    for m in M:
        j = local(good[m], [good[q] for q in M if q != m], f'{o}/mask.npy', win, bad[m], f'{o}/local_{m}.npz')
        print(f'   {m} predicted: judged {j["judged"]:3d}  unsupported {j["unsupported"]:3d} (U {j["u_flagged"]})  no-null {j["no_null_windows"]}', flush=True)
        j = local(bad[m], [good[q] for q in M if q != m], f'{o}/mask.npy', win, None, f'{o}/local_{m}_errado.npz', stroke='energy')
        print(f'   {m} wrong order: judged {j["judged"]:3d}  unsupported {j["unsupported"]:3d}', flush=True)
    if not os.path.exists(f'{o}/rv2_falsas.npy'):
        mask = np.load(f'{o}/mask.npy') > 0
        fk, fmask, h, sw, hi = plant(load(good['rv2']), mask, px, zlib.crc32(seg.encode()))
        np.save(f'{o}/rv2_falsas.npy', fk); np.save(f'{o}/fake_mask.npy', fmask)
        print(f'   invented letters: height {h} px, stroke {sw} px, intensity {hi:.3f}, {int(fmask.sum())} px', flush=True)
    j = local(f'{o}/rv2_falsas.npy', [good[q] for q in M if q != 'rv2'], f'{o}/mask.npy', win, bad['rv2'], f'{o}/local_rv2_falsas.npz')
    print(f'   rv2+invented: judged {j["judged"]:3d}  unsupported {j["unsupported"]:3d} (U {j["u_flagged"]})', flush=True)
json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'maps'} for k, v in res.items()},
          open(f'{OUT}/antes_dos_rotulos.json', 'w', encoding='utf-8'), indent=1)

print('\n######## ONLY NOW THE LABELS ########', flush=True)


def unsupported(d):                                                     # = naturais.py
    st = d['state']; jj = st > 0
    nmax = np.where(np.isnan(d['nmax']), np.inf, d['nmax'])
    cf = jj & ~(d['real'] > nmax)
    U = d['U']; h = jj & np.isfinite(U); fu = np.zeros_like(jj)
    if h.any():
        u = U[h]; med = np.median(u); mad = np.median(np.abs(u - med))
        fu = h & (U >= max(UMIN, med + UK * 1.4826 * mad))
    return jj, cf | fu


def at(img, d):
    a = np.load(img) > 0; W = int(d['win_px'])
    f = uniform_filter(a.astype(np.float32), W, mode='constant')
    return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]


P1p, P1all, P2, abst = [], [], [], []
t = dict(j=0, u=0, nn=0, cand=0, pu=0, pn=0, mu=0, mn=0, ou=0, on=0, bj=0, bu=0)
nat_u = nat_n = real_u = real_n = 0
for seg in SEGS:
    o = f'{OUT}/{seg}'; r = res[seg]
    if not os.path.exists(f'{o}/ink.npy'):
        ink = resample(np.asarray(arr(f'{R}/{seg}/labels/inklabels.zarr')) > 0, tuple(r['shape'][1:])) > 0.5
        np.save(f'{o}/ink.npy', np.roll(ink, tuple(r['shift']), (0, 1)).astype(np.uint8) * 255)
    auc = {k: sh([PY, IK, 'label', p, f'{o}/ink.npy', '--mask', f'{o}/mask.npy', '--n', '200'])['auc'] for k, p in r['maps'].items()}
    lab_ord = 'forward' if sum(auc[f'{m}_f'] > auc[f'{m}_r'] for m in M) >= 2 else 'reverse'
    print(f'{seg[:40]:40s} ' + '  '.join(f'{k} {auc[k]:.3f}' for k in auc) + f' | labels prefer {lab_ord} | kit said {r["pred"]} ({r["pred_from"]})', flush=True)
    r['auc'] = auc
    if r['pred'] is None:
        abst.append(seg); continue
    s, x = ('f', 'r') if r['pred'] == 'forward' else ('r', 'f')
    contra = 0
    for m in M:
        if abs(auc[f'{m}_{s}'] - auc[f'{m}_{x}']) >= 0.05:
            P1p.append(auc[f'{m}_{s}'] > auc[f'{m}_{x}'])
        contra += auc[f'{m}_{s}'] < auc[f'{m}_{x}']
    P1all.append(contra == 3)
    v = r['verdict']
    if all(auc[f'{m}_{s}'] >= 0.70 for m in M):
        P2.append(all(v[f'{m}_{s}'] == 'consistent' for m in M) and all(v[k].startswith(('suspect', 'isolated')) for k in auc if auc[k] < 0.60))
    for m in M:
        d = np.load(f'{o}/local_{m}.npz'); st = d['state']
        t['j'] += int((st > 0).sum()); t['u'] += int((st == 2).sum()); t['nn'] += int(d['no_null'].sum()); t['cand'] += int((st > 0).sum() + d['no_null'].sum())
        jj, un = unsupported(d); fi = at(f'{o}/ink.npy', d)
        nat, real = jj & (fi < NAT), jj & (fi >= REAL)
        nat_u += int((un & nat).sum()); nat_n += int(nat.sum()); real_u += int((un & real).sum()); real_n += int(real.sum())
        st2 = np.load(f'{o}/local_{m}_errado.npz')['state']; t['bj'] += int((st2 > 0).sum()); t['bu'] += int((st2 == 2).sum())
    d = np.load(f'{o}/local_rv2_falsas.npz'); st = d['state']
    ff, fi = at(f'{o}/fake_mask.npy', d), at(f'{o}/ink.npy', d)
    pure, mixed, clean = (ff > 0.02) & (fi < 0.01), (ff > 0.02) & (fi >= 0.02), ff == 0
    t['pu'] += int((pure & (st == 2)).sum()); t['pn'] += int((pure & (st > 0)).sum())
    t['mu'] += int((mixed & (st == 2)).sum()); t['mn'] += int((mixed & (st > 0)).sum())
    t['ou'] += int((clean & (st == 2)).sum()); t['on'] += int((clean & (st > 0)).sum())

dec = len(SEGS) - len(abst)
h1 = dec >= 2 and bool(P1p) and np.mean(P1p) >= 0.90 and not any(P1all)
print(f'\nH1 layer order: {sum(P1p)}/{len(P1p)} (segment, model) pairs favour the kit\'s order, segments with all 3 against: '
      f'{sum(P1all)}, decided {dec}/{len(SEGS)} (abstained: {abst}) -> {"PASS" if h1 else "FAIL" if dec >= 2 else "NOT TESTABLE"}')
print(f'H2 triangle: {sum(P2)}/{len(P2)} eligible segments correct -> {"PASS" if P2 and all(P2) else "FAIL" if P2 else "NOT TESTABLE (no eligible segment)"}')
fa = t['u'] / max(t['j'], 1); nn = t['nn'] / max(t['cand'], 1); det = t['pu'] / max(t['pn'], 1); mix = t['mu'] / max(t['mn'], 1)
print(f'Q1 false alarm, predicted-order maps: {t["u"]}/{t["j"]} = {fa:.3f} (<= 0.10) -> {"PASS" if t["j"] and fa <= 0.10 else "FAIL"}')
print(f'Q2 strokes but no null: {t["nn"]}/{t["cand"]} = {nn:.3f} (<= 0.05) -> {"PASS" if nn <= 0.05 else "FAIL"}')
print(f'Q3 pure invented-letter windows flagged: {t["pu"]}/{t["pn"]} = {det:.3f} (>= 0.60) -> {"PASS" if t["pn"] and det >= 0.60 else "FAIL" if t["pn"] else "NOT TESTABLE"}')
print(f'Q4 mixed invented-letter windows flagged: {t["mu"]}/{t["mn"]} = {mix:.3f} (>= 0.20) -> {"PASS" if t["mn"] and mix >= 0.20 else "FAIL" if t["mn"] else "NOT TESTABLE"}')
a_, b_ = nat_u / max(nat_n, 1), real_u / max(real_n, 1)
p = fisher_exact([[nat_u, nat_n - nat_u], [real_u, real_n - real_u]], alternative='greater')[1] if nat_n and real_n else 1.0
n1 = 'NOT TESTABLE (< 20 natural windows)' if nat_n < 20 else 'PASS' if (a_ >= 2 * b_ and p < 0.01) else 'FAIL'
print(f'N1 natural hallucinations: {nat_u}/{nat_n} = {a_:.3f} vs real ink {real_u}/{real_n} = {b_:.3f}, Fisher p {p:.2e} -> {n1}')
print(f'   (informative) alarms outside invented letters {t["ou"]}/{t["on"]}; wrong-order maps unsupported {t["bu"]}/{t["bj"]}')
json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'maps'} for k, v in res.items()}, open(f'{OUT}/resultado.json', 'w', encoding='utf-8'), indent=1)
