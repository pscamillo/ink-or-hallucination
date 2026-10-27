"""PREREG_HELDOUT3: the kit on PHerc1447 w060 (labelled) and w062 (no labels, informative), a scroll none of the three
models was trained on, where the 9 um models read the layers reversed; plus v8-in as a witness of another architecture.
The order decision, triangle, windowed check and invented letters are fase10.py's (PREREG_HELDOUT2), unchanged:
  1) order: a) order rule (curvatura + ordem_camadas), b) triangle fallback (unique core >= 3, one side),
     c) trio strength over the 3 villa models (ratio >= 1.25), else unresolved
  2) triangle --core-from the predicted order; windowed check v12 for each villa map; invented letters in Reader v2
  3) NEW witness: v8-in (Youssef Nader, public weights, never trained on PHerc1447) in both layer orders.
     8-map triangle with --core-from the 3 villa maps in the predicted order -> v8-in's verdict (W1a);
     windowed check of v8-in's predicted-order map against the 3 villa maps, floor = v8-in in the other order (W1b)
  4) only now, w060's labels (certainty mask): AUC per map (8 maps), O1, the label splits
Data: Youssef Nader's public release (hf YoussefMoNader/ink-8um-pherc1447-surfaces): 24 layers at 8.64 um, labels on
the same grid (no registration needed: checked by shape). Layers NN.tif = normal offset NN - 11.5 voxels, stored
ascending; "forward" here = the stored order, as for every surface volume in the kit.
uso: python -u fase11.py      (ink-sdk python; koine in the villa env via uv run; v8-in in its own venv)
"""
import os, sys, json, subprocess, re, zlib
import numpy as np, zarr, tifffile
from PIL import Image
from scipy.ndimage import binary_dilation, gaussian_filter, uniform_filter

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; KO = f'{H}/villa_ink/ink-detection'; V8 = f'{H}/v8in'; S = f'{V8}/surfaces'; OUT = f'{I}/fase11'
IK = f'{I}/inkcheck_v12.py'; PY = sys.executable
CT = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr/0'
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
M = tuple(CK)
V8PY, V8PRED = f'{V8}/.venv/bin/python', f'{V8}/ink-8um-v8in/predict.py'
SEGS = ['w060', 'w062']                      # w060 labelled; w062 informative (no labels)
VOX_UM = 8.64
TIE = 1.25                                   # PREREG_HELDOUT2, unchanged
V12 = ['--score', 'both', '--null', 'swap', '--n', '19', '--min-null', '10', '--tol-px', '6', '--ink-rel', '0.5',
       '--min-ink', '0.005', '--u-k', '3.0', '--u-min', '0.20']        # = fase7.py
LETTER_MM, STROKE_MM, WIN_MM, FAKE_FRAC = 2.5, 0.2, 2.5, 0.02          # = fase5.py
UK, UMIN, NAT, REAL = 3.0, 0.20, 0.005, 0.05                           # = naturais.py
os.makedirs(OUT, exist_ok=True)


def sh(cmd, cwd=I, js=True):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:6]), r.stderr[-1500:], flush=True); sys.exit(1)
    return json.loads(r.stdout) if js else r.stdout


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


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




def um_per_px(mesh, w_render):
    P = np.stack([tifffile.imread(f'{mesh}/{c}.tif') for c in 'xyz'], -1).astype(np.float64); ok = (P > 0).all(-1)
    d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    return float(np.median(d)) * VOX_UM / (w_render / P.shape[1])


def order_rule(mesh, sv_path):
    cu = sh([PY, f'{I}/curvatura.py', mesh, '--D', '1000'], js=False)
    mfl = re.search(r'flecha media\s+([-+0-9.]+)vx', cu)
    if not mfl:                                   # no sagitta measured: the rule abstains (fase10 would have crashed)
        return {'prediction': None, 'why': 'curvatura gave no sagitta: ' + cu.strip()[-120:]}
    fl = float(mfl.group(1)); out_n = fl < 0; decide_c = abs(fl) >= 20
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


def png_gray(p):
    a = np.asarray(Image.open(p)); return a[..., 0] if a.ndim == 3 else a


res = {}
for seg in SEGS:
    o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True); src_d = f'{S}/{seg}'; svp = f'{o}/sv.zarr'
    if not os.path.exists(f'{svp}/0/.zarray'):
        st = np.stack([tifffile.imread(f'{src_d}/layers/{i:02d}.tif') for i in range(24)], 0)
        g = zarr.open_group(svp, mode='w', zarr_format=2)
        g.create_array('0', data=st, chunks=(24, 128, 128))
        del st
    sv = arr(svp); N = sv.shape[0]; ls = (N - 17) // 2
    mesh = f'{src_d}/tifxyz'; px = um_per_px(mesh, sv.shape[2]); win = int(round(WIN_MM * 1000 / px))
    print(f'\n== {seg}  {tuple(sv.shape)}  pixel {px:.2f} um  window {win} px  (labels on the same grid: no registration)', flush=True)
    rule = order_rule(mesh, svp); print('   order rule (before any model):', rule, flush=True)
    for m, ck in CK.items():
        if not (os.path.exists(f'{o}/{m}.tif') and os.path.exists(f'{o}/{m}_reverse.tif')):
            sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', svp, ck, f'{o}/{m}.tif', '--model-type', 'auto',
                '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
                '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'],
               cwd=KO, js=False)
    for sfx, flag in (('', []), ('_reverse', ['--reverse'])):          # v8-in: stored order, and reversed (its own convention)
        if not os.path.exists(f'{o}/v8in{sfx}.npy'):
            env = dict(os.environ, PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True')
            r = subprocess.run([V8PY, V8PRED, *flag, '--batch-size', '8', '--layers', f'{src_d}/layers',
                                '--output', f'{o}/v8in{sfx}.png', f'{o}/v8in{sfx}.npy'], capture_output=True, text=True, env=env, cwd=V8)
            if r.returncode:
                print('ERRO v8-in', r.stderr[-1500:], flush=True); sys.exit(1)
    if not os.path.exists(f'{o}/mask.npy'):
        valid = np.asarray(sv[ls + 8]) > 0
        if os.path.exists(f'{src_d}/labels/mask.png'):
            cm = png_gray(f'{src_d}/labels/mask.png') > 0
            assert cm.shape == valid.shape, f'mask {cm.shape} != render {valid.shape}'
            valid &= cm
        np.save(f'{o}/mask.npy', valid.astype(np.uint8) * 255)
    maps = {}
    for m in M:
        maps[f'{m}_f'] = f'{o}/{m}.tif'; maps[f'{m}_r'] = f'{o}/{m}_reverse.tif'
    v8 = {'v8in_f': f'{o}/v8in.npy', 'v8in_r': f'{o}/v8in_reverse.npy'}
    pred, how = rule['prediction'], 'rule'
    if pred is None:
        t0 = sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in maps.items()] + ['--mask', f'{o}/mask.npy', '--n', '300', '--min-ratio', '2.0'])
        side = {c[-1] for c in t0['core']}
        pred = 'forward' if side == {'f'} and len(t0['core']) >= 3 else 'reverse' if side == {'r'} and len(t0['core']) >= 3 else None
        how = 'triangle fallback'
        print(f'   triangle fallback: core {t0["core"]} -> {pred}', flush=True)
        json.dump(t0, open(f'{o}/triangulo_6.json', 'w', encoding='utf-8'), indent=1)
        if pred is None:
            Sd = {}
            for sd in 'fr':
                c3 = [v['corr'] for k, v in t0['pairs'].items() if all(n.endswith('_' + sd) for n in k.split(' x '))]
                assert len(c3) == 3, f'expected 3 {sd}-side pairs, got {len(c3)}'
                Sd[sd] = float(np.median(c3))
            ratio = max(Sd.values()) / max(min(Sd.values()), 1e-6)
            strong = 'forward' if Sd['f'] > Sd['r'] else 'reverse'
            pred = strong if ratio >= TIE else None
            how = 'trio strength'
            rule['tie_break'] = {'S_forward': Sd['f'], 'S_reverse': Sd['r'], 'ratio': ratio, 'threshold': TIE}
            print(f'   trio strength: S_f {Sd["f"]:.3f}  S_r {Sd["r"]:.3f}  ratio {ratio:.2f} (>= {TIE}?) -> {pred}', flush=True)
    res[seg] = {'shape': list(sv.shape), 'px_um': px, 'win_px': win, 'rule': rule, 'pred': pred, 'pred_from': how,
                'maps': {**maps, **v8}}
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
    # witness of another architecture (v8-in), in the order the kit decided from the villa models only
    vg, vb = v8['v8in' + suf], v8['v8in' + oth]
    tw = sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in {**maps, **v8}.items()] + ['--mask', f'{o}/mask.npy', '--n', '300',
            '--min-ratio', '2.0', '--core-from'] + [m + suf for m in M])
    json.dump(tw, open(f'{o}/triangulo_v8in.json', 'w', encoding='utf-8'), indent=1)
    res[seg]['w1a'] = tw['verdict'].get('v8in' + suf)
    jw = local(vg, list(good.values()), f'{o}/mask.npy', win, vb, f'{o}/local_v8in.npz')
    res[seg]['w1b'] = {k: jw[k] for k in ('judged', 'unsupported', 'u_flagged', 'no_null_windows')}
    print(f'   v8-in witness: triangle verdict "{res[seg]["w1a"]}" | windows judged {jw["judged"]}  unsupported {jw["unsupported"]}', flush=True)
json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'maps'} for k, v in res.items()},
          open(f'{OUT}/antes_dos_rotulos.json', 'w', encoding='utf-8'), indent=1)

print('\n######## ONLY NOW THE LABELS (w060) ########', flush=True)
seg = 'w060'; o = f'{OUT}/{seg}'; r = res[seg]
if not os.path.exists(f'{o}/ink.npy'):
    ink = png_gray(f'{S}/{seg}/labels/inklabels.png') > 127
    assert ink.shape == tuple(r['shape'][1:]), f'labels {ink.shape} != render {r["shape"][1:]}'
    np.save(f'{o}/ink.npy', ink.astype(np.uint8) * 255)
auc = {k: sh([PY, IK, 'label', p, f'{o}/ink.npy', '--mask', f'{o}/mask.npy', '--n', '200'])['auc'] for k, p in r['maps'].items()}
lab_ord = 'forward' if sum(auc[f'{m}_f'] > auc[f'{m}_r'] for m in M) >= 2 else 'reverse'
print('  '.join(f'{k} {auc[k]:.3f}' for k in auc) + f' | labels prefer {lab_ord} | kit said {r["pred"]} ({r["pred_from"]})', flush=True)
r['auc'] = auc; r['label_order'] = lab_ord
o1 = 'NOT TESTABLE (unresolved)' if r['pred'] is None else 'PASS' if r['pred'] == lab_ord else 'FAIL'
print(f'\nO1 order decision on a scroll no model saw: kit {r["pred"]} via {r["pred_from"]}, labels {lab_ord} -> {o1}')
if r['pred'] is not None:
    s, x = ('f', 'r') if r['pred'] == 'forward' else ('r', 'f')
    w1a = r.get('w1a') or ''
    print(f'W1a v8-in triangle verdict: "{w1a}" -> {"PASS" if w1a.startswith("agrees with the whole core") or w1a == "consistent" else "FAIL"}')
    jb = r['w1b']; fr = jb['unsupported'] / max(jb['judged'], 1)
    w1b = 'NOT TESTABLE (< 20 judged windows)' if jb['judged'] < 20 else 'PASS' if fr <= 0.10 else 'FAIL'
    print(f'W1b v8-in windows not supported by the 3 villa maps: {jb["unsupported"]}/{jb["judged"]} = {fr:.3f} (<= 0.10) -> {w1b}')
    print(f'   (informative) v8-in AUC in the kit order {auc["v8in_" + s]:.3f}, other order {auc["v8in_" + x]:.3f}')
    t = dict(j=0, u=0, nn=0, cand=0, pu=0, pn=0, mu=0, mn=0, ou=0, on=0, bj=0, bu=0); nat_u = nat_n = real_u = real_n = 0
    v = r['verdict']
    h2 = None
    if all(auc[f'{m}_{s}'] >= 0.70 for m in M):
        h2 = all(v[f'{m}_{s}'] == 'consistent' for m in M) and all(v[k].startswith(('suspect', 'isolated')) for k in v if k in auc and auc[k] < 0.60)
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
    print(f'H2 triangle: {"NOT TESTABLE (not all 3 kit-order maps >= 0.70)" if h2 is None else "PASS" if h2 else "FAIL"}')
    fa = t['u'] / max(t['j'], 1); nn = t['nn'] / max(t['cand'], 1); det = t['pu'] / max(t['pn'], 1); mix = t['mu'] / max(t['mn'], 1)
    print(f'Q1 false alarm: {t["u"]}/{t["j"]} = {fa:.3f} (<= 0.10) -> {"NOT TESTABLE (0 judged)" if not t["j"] else "PASS" if fa <= 0.10 else "FAIL"}')
    print(f'Q2 strokes but no null: {t["nn"]}/{t["cand"]} = {nn:.3f} (<= 0.05) -> {"NOT TESTABLE (0 candidates)" if not t["cand"] else "PASS" if nn <= 0.05 else "FAIL"}')
    print(f'Q3 pure invented-letter windows flagged: {t["pu"]}/{t["pn"]} = {det:.3f} (>= 0.60) -> {"PASS" if t["pn"] and det >= 0.60 else "FAIL" if t["pn"] else "NOT TESTABLE"}')
    print(f'Q4 mixed invented-letter windows flagged: {t["mu"]}/{t["mn"]} = {mix:.3f} (>= 0.20) -> {"PASS" if t["mn"] and mix >= 0.20 else "FAIL" if t["mn"] else "NOT TESTABLE"}')
    from scipy.stats import fisher_exact
    a_, b_ = nat_u / max(nat_n, 1), real_u / max(real_n, 1)
    p = fisher_exact([[nat_u, nat_n - nat_u], [real_u, real_n - real_u]], alternative='greater')[1] if nat_n and real_n else 1.0
    n1 = 'NOT TESTABLE (< 20 natural windows)' if nat_n < 20 else 'PASS' if (a_ >= 2 * b_ and p < 0.01) else 'FAIL'
    print(f'N1 natural hallucinations: {nat_u}/{nat_n} = {a_:.3f} vs real ink {real_u}/{real_n} = {b_:.3f}, Fisher p {p:.2e} -> {n1}')
    print(f'   (informative) alarms outside invented letters {t["ou"]}/{t["on"]}; wrong-order maps unsupported {t["bu"]}/{t["bj"]}')
print(f'\n(informative, no labels) w062: kit {res["w062"]["pred"]} via {res["w062"]["pred_from"]}; the dataset author reads these layers reversed')
json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'maps'} for k, v in res.items()}, open(f'{OUT}/resultado.json', 'w', encoding='utf-8'), indent=1)
