"""PREREG_UCOMP: windowed check v13 (v12 + largest connected piece of unexplained strokes) vs v12, blind, on six
labelled segments off the training data: PHerc0841 x3 (fase9), PHerc0500P2 + 0009B (fase10), PHerc1447 w060 (fase11).
No model is run: the maps are on disk. Labels are read only in the last block, only to split windows.
  1) layer order: 0500P2/0009B forward and w060 reverse, as sealed in RESULT_HELDOUT2/3; PHerc0841 decided now by the
     kit as it stands (order rule from fase9 -> triangle fallback -> guarded trio-strength tie-break, segment.py)
  2) v13 (which also returns v12's state from the same run) on each decided-order map vs the other two
  3) NEW invented letters in Reader v2 (fase10's plant(), same parameters, seed crc32(segment + '|ucomp')), v13 on it
  4) only now: labels -> pure / mixed planted windows, natural hallucination / real ink windows; criteria C1-C3
uso: python -u fase12.py
"""
import os, sys, json, subprocess, zlib
import numpy as np, tifffile
from scipy.ndimage import binary_dilation, gaussian_filter, uniform_filter
from scipy.stats import fisher_exact

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; OUT = f'{I}/fase12'; IK = f'{I}/inkcheck_v13.py'; PY = sys.executable
REPO = f'{H}/ink-or-hallucination'
M = ('ink9', 'rv2', 'rv3')
LETTER_MM, STROKE_MM, FAKE_FRAC = 2.5, 0.2, 0.02                       # = fase5.py / fase10.py
V12 = ['--score', 'both', '--null', 'swap', '--n', '19', '--min-null', '10', '--tol-px', '6', '--ink-rel', '0.5',
       '--min-ink', '0.005', '--u-k', '3.0', '--u-min', '0.20']        # = fase7.py
V13 = V12 + ['--blob-min', '0.04', '--blob-k', '3.0']                  # PREREG_UCOMP
NAT, REAL = 0.005, 0.05                                                # = naturais.py
SEGS = [('fase9', '20260220213127-w00', None), ('fase9', '20260220214732-auto_grown_20260220144552896', None),
        ('fase9', '20260221022814-auto_grown_20260220174252405', None),
        ('fase10', '20250825181859--1', 'forward'),
        ('fase10', '20250919125754-auto_grown_20250919055754487_inp_hr', 'forward'),
        ('fase11', 'w060', 'reverse')]
os.makedirs(OUT, exist_ok=True)


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=I)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:6]), r.stderr[-1500:], flush=True); sys.exit(1)
    return json.loads(r.stdout)


def glyph(rng, h, sw):                                                   # = fase10.py
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


def plant(base, mask, px_um, seed):                                      # = fase10.py
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


def local(target, others, mask, win, floor, out):
    return sh([PY, IK, 'local', target, *others, '--mask', mask, '--win', str(win), '--stroke', 'floor', '--floor', floor,
               '--floor-k', '2.0', '--out-npz', out] + V13)


def order_0841(src, o, maps):
    sys.path.insert(0, REPO)
    import segment
    t0 = sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in maps.items()] + ['--mask', f'{src}/mask.npy', '--n', '300', '--min-ratio', '2.0'])
    json.dump(t0, open(f'{o}/triangulo_6.json', 'w', encoding='utf-8'), indent=1)
    side = {c[-1] for c in t0['core']}
    if len(t0['core']) >= 3 and side in ({'f'}, {'r'}):
        return ('forward' if side == {'f'} else 'reverse'), f'triangle fallback, core {t0["core"]}'
    ts = segment.trio_strength(t0)
    return ts['order'], (f'trio strength S_f {ts["S_forward"]:.3f} S_r {ts["S_reverse"]:.3f} ratio {ts["ratio"]:.2f}'
                         f' guard {ts["guard"]}')


res = {}
for ph, seg, sealed in SEGS:
    src = f'{I}/{ph}/{seg}'; o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True)
    prev = json.load(open(f'{I}/{ph}/antes_dos_rotulos.json'))[seg]
    win, px = int(prev['win_px']), float(prev['px_um'])
    maps = {}
    for m in M:
        maps[f'{m}_f'] = f'{src}/{m}.tif'; maps[f'{m}_r'] = f'{src}/{m}_reverse.tif'
    if sealed is None:
        print(f'\n== {seg}  ({ph})  order rule in {ph}: {prev["rule"].get("prediction")}', flush=True)
        pred, how = (prev['rule']['prediction'], 'order rule') if prev['rule'].get('prediction') else order_0841(src, o, maps)
    else:
        pred, how = sealed, f'sealed in {ph} ({prev.get("pred_from", "")})'
        assert prev.get('pred') == sealed, f'{seg}: {ph} says {prev.get("pred")}, expected {sealed}'
        print(f'\n== {seg}  ({ph})', flush=True)
    print(f'   order {pred}  ({how})  window {win} px  pixel {px:.2f} um', flush=True)
    res[seg] = {'phase': ph, 'pred': pred, 'pred_from': how, 'win_px': win, 'px_um': px}
    if pred is None:
        print('   order unresolved: skipped (no windowed check)', flush=True); continue
    suf, oth = ('', '_reverse') if pred == 'forward' else ('_reverse', '')
    good = {m: f'{src}/{m}{suf}.tif' for m in M}; bad = {m: f'{src}/{m}{oth}.tif' for m in M}
    mask = f'{src}/mask.npy'
    for m in M:
        j = local(good[m], [good[q] for q in M if q != m], mask, win, bad[m], f'{o}/local_{m}.npz')
        print(f'   {m}: judged {j["judged"]:4d}  unsupported v12 {j["unsupported_v12"]:3d}  v13 {j["unsupported"]:3d}'
              f'  (B flag {j["b_flagged"]})', flush=True)
    if not os.path.exists(f'{o}/rv2_falsas.npy'):
        fk, fmask, h, sw, hi = plant(load(good['rv2']), np.load(mask) > 0, px, zlib.crc32((seg + '|ucomp').encode()))
        np.save(f'{o}/rv2_falsas.npy', fk); np.save(f'{o}/fake_mask.npy', fmask)
        print(f'   new invented letters: height {h} px, stroke {sw} px, intensity {hi:.3f}, {int(fmask.sum())} px', flush=True)
    j = local(f'{o}/rv2_falsas.npy', [good[q] for q in M if q != 'rv2'], mask, win, bad['rv2'], f'{o}/local_rv2_falsas.npz')
    print(f'   rv2+invented: judged {j["judged"]:4d}  unsupported v12 {j["unsupported_v12"]:3d}  v13 {j["unsupported"]:3d}', flush=True)
json.dump(res, open(f'{OUT}/antes_dos_rotulos.json', 'w', encoding='utf-8'), indent=1)

print('\n######## ONLY NOW THE LABELS (only to split windows) ########', flush=True)


def at(img, d):
    a = np.load(img) > 0; W = int(d['win_px'])
    f = uniform_filter(a.astype(np.float32), W, mode='constant')
    return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]


K = ('v12', 'v13')
t = {k: dict(j=0, u=0, pn=0, pu=0, mn=0, mu=0, nat_n=0, nat_u=0, real_n=0, real_u=0, worst=0.0) for k in K}
for ph, seg, _ in SEGS:
    if res[seg]['pred'] is None:
        continue
    src = f'{I}/{ph}/{seg}'; o = f'{OUT}/{seg}'; ink = f'{src}/ink.npy'
    row = {k: dict(j=0, u=0, pn=0, pu=0, mn=0, mu=0) for k in K}
    for m in M:
        d = np.load(f'{o}/local_{m}.npz'); fi = at(ink, d)
        for k, st in (('v12', d['state_v12']), ('v13', d['state'])):
            jj, un = st > 0, st == 2
            nat, real = jj & (fi < NAT), jj & (fi >= REAL)
            for q, v in (('j', jj.sum()), ('u', un.sum()), ('nat_n', nat.sum()), ('nat_u', (un & nat).sum()),
                         ('real_n', real.sum()), ('real_u', (un & real).sum())):
                t[k][q] += int(v)
            row[k]['j'] += int(jj.sum()); row[k]['u'] += int(un.sum())
            t[k]['worst'] = max(t[k]['worst'], un.sum() / max(jj.sum(), 1))
    d = np.load(f'{o}/local_rv2_falsas.npz'); ff, fi = at(f'{o}/fake_mask.npy', d), at(ink, d)
    for k, st in (('v12', d['state_v12']), ('v13', d['state'])):
        jj, un = st > 0, st == 2
        pure, mixed = jj & (ff > 0.02) & (fi < 0.01), jj & (ff > 0.02) & (fi >= 0.02)
        for q, v in (('pn', pure.sum()), ('pu', (pure & un).sum()), ('mn', mixed.sum()), ('mu', (mixed & un).sum())):
            t[k][q] += int(v); row[k][q] += int(v)
    print(f'{seg[:44]:44s} ' + '   '.join(f'{k}: false alarm {row[k]["u"]}/{row[k]["j"]}  pure {row[k]["pu"]}/{row[k]["pn"]}'
                                           f'  mixed {row[k]["mu"]}/{row[k]["mn"]}' for k in K), flush=True)

fr = lambda a, b: a / b if b else float('nan')
for k in K:
    x = t[k]
    print(f'\n{k}: false alarm {x["u"]}/{x["j"]} = {fr(x["u"], x["j"]):.3f} (worst map {x["worst"]:.3f})   '
          f'pure {x["pu"]}/{x["pn"]} = {fr(x["pu"], x["pn"]):.3f}   mixed {x["mu"]}/{x["mn"]} = {fr(x["mu"], x["mn"]):.3f}   '
          f'natural {x["nat_u"]}/{x["nat_n"]} vs real ink {x["real_u"]}/{x["real_n"]}', flush=True)
a, b = t['v12'], t['v13']
mx12, mx13 = fr(a['mu'], a['mn']), fr(b['mu'], b['mn'])
fa12, fa13 = fr(a['u'], a['j']), fr(b['u'], b['j'])
c1 = 'NOT TESTABLE (< 20 mixed windows)' if b['mn'] < 20 else 'PASS' if (mx13 >= 0.35 and mx13 >= mx12 + 0.10) else 'FAIL'
c2 = 'NOT TESTABLE (0 judged)' if not b['j'] else 'PASS' if (fa13 <= 0.05 and fa13 <= fa12 + 0.02) else 'FAIL'
c3 = 'NOT TESTABLE (< 10 pure windows)' if b['pn'] < 10 else 'PASS' if fr(b['pu'], b['pn']) >= 0.60 else 'FAIL'
print(f'\nC1 mixed invented letters: v13 {mx13:.3f} vs v12 {mx12:.3f} (>= 0.35 and >= v12 + 0.10) -> {c1}')
print(f'C2 false alarm: v13 {fa13:.3f} vs v12 {fa12:.3f} (<= 0.05 and <= v12 + 0.02) -> {c2}')
print(f'C3 pure invented letters: v13 {fr(b["pu"], b["pn"]):.3f} (>= 0.60) -> {c3}')
adopt = c1 == 'PASS' and c2 == 'PASS' and c3 != 'FAIL'
print(f'\n=> v13 {"REPLACES" if adopt else "does NOT replace"} v12 in the kit (C1 and C2 PASS, C3 not FAIL)')
for k in K:
    x = t[k]
    if x['nat_n'] and x['real_n']:
        p = fisher_exact([[x['nat_u'], x['nat_n'] - x['nat_u']], [x['real_u'], x['real_n'] - x['real_u']]], alternative='greater')[1]
        print(f'   (informative) {k} natural hallucinations {fr(x["nat_u"], x["nat_n"]):.3f} vs real ink {fr(x["real_u"], x["real_n"]):.3f}, Fisher p {p:.2e}')
json.dump({'res': res, 'totals': t, 'C1': c1, 'C2': c2, 'C3': c3, 'adopt': adopt},
          open(f'{OUT}/resultado.json', 'w', encoding='utf-8'), indent=1)
