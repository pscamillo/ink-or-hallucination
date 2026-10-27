"""DEVELOPMENT ONLY (not evidence): component-level unexplained strokes on PHercParis4 (fase5 maps, fase7 v12 npz).

Idea: v12's U is the FRACTION of a window's stroke pixels that no other map explains. An invented letter on top of
real text is diluted by the real strokes around it. Here, per window, B = area of the LARGEST CONNECTED blob of
unexplained stroke pixels (same strokes and same 6 px tolerance as v12). Real text that only one model draws tends to
leave small scattered fragments; an invented letter leaves one connected piece.
A window is flagged if B is an outlier among that map's ink windows: B >= max(bmin x win^2, median + k x 1.4826 MAD).
Final = v12 unsupported OR blob flag.

Reads only files that exist (no model is run). Labels are used only to split the planted-letter windows into
pure / mixed, exactly as fase7.py. PHercParis4 has been seen many times: this picks k and bmin, nothing more.
uso: python ucomp_dev.py
"""
import os, sys, json
import numpy as np
from scipy.ndimage import uniform_filter, binary_dilation, label

H = os.path.expanduser('~/challenges/vesuvius'); I = f'{H}/inkcheck'
sys.path.insert(0, I)
import inkcheck_v12 as ik                                                # the sealed core: same load/down/valid_mask

M = ('ink9', 'rv2', 'rv3')
TOL, INK_REL, MIN_INK, UK, UMIN = 6.0, 0.5, 0.005, 3.0, 0.20            # = V12
KS, BMINS = (3.0,), (0.02, 0.03, 0.04, 0.05, 0.06, 0.08)          # run 2: k did not matter at bmin 0.02 (run 1)


def geometry(target, others, mask):
    T = ik.load(target); O = [ik.load(p) for p in others]
    v = ik.valid_mask(T, mask)
    for m in O:
        v &= ik.valid_mask(m, None)
    f = max(1, int(np.sqrt(v.sum() / 4_000_000)))
    vd = ik.down(v.astype(np.float32), f) > 0.99
    def strokes(x):
        q = float(np.percentile(x[vd], 99)) if vd.any() else np.inf
        return vd & (x >= INK_REL * q)
    ST = strokes(ik.down(T, f)); SO = np.zeros_like(ST)
    for mm in O:
        SO |= strokes(ik.down(mm, f))
    r = max(1, int(round(TOL / f))); yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    DO = binary_dilation(SO, structure=(yy ** 2 + xx ** 2) <= r * r)
    return f, vd, ST, ST & ~DO


def blob(target, others, mask, npz):
    d = np.load(npz); st = d['state']
    cache = npz[:-4] + '_blob.npz'
    if os.path.exists(cache):
        c = np.load(cache); return d, c['B'], c['ink'], int(c['win'])
    f, vd, ST, E = geometry(target, others, mask)
    win = int(d['win_px']) // f; h = win // 2
    cy, cx = d['cy'] // f, d['cx'] // f
    lab, _ = label(E, structure=np.ones((3, 3), bool))
    Bv = np.zeros(st.shape, np.float32); ink = np.zeros(st.shape, bool)
    for i, y in enumerate(cy):
        for j, x in enumerate(cx):
            if st[i, j] == 0:
                continue
            sl = (slice(max(0, y - h), y - h + win), slice(max(0, x - h), x - h + win))
            nv = vd[sl].sum()
            ink[i, j] = nv > 0 and ST[sl].sum() / nv >= MIN_INK
            L = lab[sl]; L = L[L > 0]
            Bv[i, j] = np.bincount(L).max() if L.size else 0
    np.savez(cache, B=Bv, ink=ink, win=win)
    return d, Bv, ink, win


def v12_unsup(d):                                                        # = fase7.py: the sealed state map
    st = d['state']
    return st > 0, st == 2


def flag(Bv, ink, win, k, bmin):
    if not ink.any():
        return np.zeros_like(ink)
    b = Bv[ink]; med = np.median(b); mad = np.median(np.abs(b - med))
    return ink & (Bv >= max(bmin * win * win, med + k * 1.4826 * mad))


res5 = json.load(open(f'{I}/fase5/resultado.json'))
rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/geometria_paris4.tsv')][1:]
segs = [(r[0], r[5]) for r in rows if r[5] in ('forward', 'reverse')]
C = {(k, b): dict(j=0, u=0, pn=0, pu=0, mn=0, mu=0, worst=0.0) for k in KS for b in BMINS}
base = dict(j=0, u=0, pn=0, pu=0, mn=0, mu=0)
for seg, pred in segs:
    src = f'{I}/fase5/{seg}'; o = f'{I}/fase7/{seg}'; mask = f'{src}/mask.npy'
    suf = '' if pred == 'forward' else '_reverse'
    good = {m: f'{src}/{m}{suf}.tif' for m in M}
    for m in M:                                                          # false alarm on the untouched maps
        d, Bv, ink, win = blob(good[m], [good[q] for q in M if q != m], mask, f'{o}/local_{m}.npz')
        jj, un = v12_unsup(d)
        base['j'] += int(jj.sum()); base['u'] += int(un.sum())
        for kb, t in C.items():
            uu = int((un | flag(Bv, ink, win, *kb)).sum())
            t['j'] += int(jj.sum()); t['u'] += uu; t['worst'] = max(t['worst'], uu / max(int(jj.sum()), 1))
    d, Bv, ink, win = blob(f'{src}/rv2_falsas.npy', [good[q] for q in M if q != 'rv2'], mask, f'{o}/local_rv2_falsas.npz')
    jj, un = v12_unsup(d); W = int(d['win_px'])
    def at(img):
        a = np.load(img) > 0
        g = uniform_filter(a.astype(np.float32), W, mode='constant')
        return g[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]
    ff, fi = at(f'{src}/fake_mask.npy'), at(f'{src}/ink.npy')
    pure, mixed = jj & (ff > 0.02) & (fi < 0.01), jj & (ff > 0.02) & (fi >= 0.02)
    base['pn'] += int(pure.sum()); base['pu'] += int((pure & un).sum())
    base['mn'] += int(mixed.sum()); base['mu'] += int((mixed & un).sum())
    for kb, t in C.items():
        fl = un | flag(Bv, ink, win, *kb)
        t['pn'] += int(pure.sum()); t['pu'] += int((pure & fl).sum())
        t['mn'] += int(mixed.sum()); t['mu'] += int((mixed & fl).sum())
    print(f'{seg:16s} win {win} px (downsampled)  done', flush=True)

fr = lambda a, b: a / max(b, 1)
print(f'\nv12 as sealed: false alarm {base["u"]}/{base["j"]} = {fr(base["u"], base["j"]):.3f}   pure {base["pu"]}/{base["pn"]} = '
      f'{fr(base["pu"], base["pn"]):.3f}   mixed {base["mu"]}/{base["mn"]} = {fr(base["mu"], base["mn"]):.3f}')
print('\n   k   bmin   false alarm      pure            mixed            worst single map')
for (k, b), t in C.items():
    print(f'{k:4.1f}  {b:.3f}   {t["u"]:4d}/{t["j"]:4d} {fr(t["u"], t["j"]):.3f}   {t["pu"]:3d}/{t["pn"]:3d} {fr(t["pu"], t["pn"]):.3f}   '
          f'{t["mu"]:4d}/{t["mn"]:4d} {fr(t["mu"], t["mn"]):.3f}   {t["worst"]:.3f}')
