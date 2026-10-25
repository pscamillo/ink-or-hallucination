#!/usr/bin/env python3
"""inkcheck: is this ink map real ink or a hallucination?

Map-level checks (no model needed, works on any 2D ink map):

  direction  forward vs reversed-stack map of the same model.
             Real ink is depth-ordered: the reversed map should lose it.
  label      AUC against an ink label (when one exists), with a null from
             random placements of the same label on the same map.
  witness    agreement between two different models, with a null from
             block-shuffling one of them. Also forward-vs-reversed agreement.
  triangle   all pairs among 3+ models. Only a group of 3+ that all agree
             pairwise counts: one witness can share non-ink structure (e.g.
             papyrus texture) with a blind model and agree with it anyway.

Usage
  inkcheck.py direction FWD REV [--mask M] [--label L]
  inkcheck.py label     MAP LABEL [--mask M] [--n 500]
  inkcheck.py witness   A B [--b-rev BREV] [--mask M] [--n 500] [--block 64]
  inkcheck.py triangle  NAME=MAP NAME=MAP NAME=MAP [...] [--mask M] [--n 500] [--alpha 0.01]
  (witness/triangle compare maps at stroke scale only: --band LO HI px, default 2 20)

Maps: .npy, .png, .tif/.tiff. uint8 maps are scaled to [0,1].
Labels/masks: nonzero = ink / valid. If a label has a 'no-ink' file,
pass it with --noink; otherwise every valid non-ink pixel counts as no-ink.
Prints one JSON object. Exit code is always 0; read the numbers.
"""
import argparse, json, sys
import numpy as np
from scipy.stats import rankdata


# ---------- io ----------
def load(path):
    p = str(path).lower()
    if p.endswith('.npy'):
        a = np.load(path)
    elif p.endswith(('.tif', '.tiff')):
        import tifffile
        a = tifffile.imread(path)
    else:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        a = np.asarray(Image.open(path))
    a = np.asarray(a)
    if a.ndim == 3:            # RGB(A) image -> first channel
        a = a[..., 0]
    if a.dtype == np.uint8:
        return a.astype(np.float32) / 255.0
    if a.dtype == np.uint16:
        return a.astype(np.float32) / 65535.0
    return a.astype(np.float32)


def same_shape(*arrs):
    s = arrs[0].shape
    for a in arrs[1:]:
        if a is not None and a.shape != s:
            sys.exit(f'shape mismatch: {s} vs {a.shape}')


def valid_mask(m, mask_path):
    v = np.isfinite(m)
    if mask_path:
        v &= load(mask_path) > 0
    else:
        v &= m != 0           # zero = no coverage in most pipelines
    return v


# ---------- stats ----------
rng = np.random.default_rng(0)


def auc(pos, neg, cap=2_000_000):
    if pos.size == 0 or neg.size == 0:
        return float('nan')
    if pos.size > cap:
        pos = rng.choice(pos, cap, replace=False)
    if neg.size > cap:
        neg = rng.choice(neg, cap, replace=False)
    r = rankdata(np.concatenate([pos, neg]))
    return float((r[:pos.size].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


def describe(m, v):
    x = m[v]
    k = max(1, int(0.01 * x.size))
    return {'mean': float(x.mean()), 'frac_gt_0.5': float((x > 0.5).mean()),
            'top1pct_mean': float(np.sort(x)[-k:].mean())}


def corr(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else float('nan')


def down(m, f):
    if f <= 1:
        return m
    H, W = (m.shape[0] // f) * f, (m.shape[1] // f) * f
    return m[:H, :W].reshape(H // f, f, W // f, f).mean((1, 3))


def band(m, v, lo, hi):
    """Keep only the stroke scale: difference of Gaussians (sigma lo..hi px),
    computed inside the valid area. Large smooth brightness patterns (dense
    papyrus, coverage edges) are shared by blind and seeing models alike and
    would otherwise dominate any correlation. lo=hi=0 disables."""
    if hi <= 0:
        return np.where(v, m, 0)
    from scipy.ndimage import gaussian_filter as g
    x = np.where(v, m, 0).astype(np.float32)
    w = v.astype(np.float32)
    def sm(s):                              # normalized convolution: ignores invalid pixels
        return g(x, s) / np.maximum(g(w, s), 1e-6)
    out = (sm(lo) if lo > 0 else x) - sm(hi)
    return np.where(v, out, 0)


def block_grid(vd, block, min_frac=0.5):
    """Blocks of the null: only blocks whose valid fraction >= min_frac take part (v7).
    Returns the pixel mask covered by those blocks (used for BOTH the real and the null corr)."""
    H, W = (vd.shape[0] // block) * block, (vd.shape[1] // block) * block
    frac = vd[:H, :W].reshape(H // block, block, W // block, block).mean((1, 3))
    elig = frac >= min_frac
    use = np.zeros_like(vd)
    use[:H, :W] = np.repeat(np.repeat(elig, block, 0), block, 1) & vd[:H, :W]
    return elig, use


def block_shuffle(m, block, elig=None):
    """Permute blocks. With elig (v7): only eligible (mostly valid) blocks are permuted, among themselves,
    so empty outside-mask blocks never land in the valid area."""
    H, W = (m.shape[0] // block) * block, (m.shape[1] // block) * block
    t = m[:H, :W].reshape(H // block, block, W // block, block).swapaxes(1, 2).reshape(-1, block, block)
    if elig is None:
        t = t[rng.permutation(len(t))]
    else:
        idx = np.flatnonzero(elig.ravel())
        t = t.copy(); t[idx] = t[idx[rng.permutation(len(idx))]]
    out = m.copy()
    out[:H, :W] = t.reshape(H // block, W // block, block, block).swapaxes(1, 2).reshape(H, W)
    return out


def null_stats(real, null):
    """Drop NaN draws (v7); report how many."""
    null = np.asarray(null, float); bad = int(np.isnan(null).sum()); null = null[~np.isnan(null)]
    if null.size == 0:
        return {'null_max': float('inf'), 'null_mean': float('nan'), 'p': 1.0, 'null_nan': bad}
    return {'null_max': float(null.max()), 'null_mean': float(null.mean()),
            'p': float((1 + (null >= real).sum()) / (1 + null.size)), 'null_nan': bad}


# ---------- checks ----------
def check_direction(a):
    f, r = load(a.fwd), load(a.rev)
    same_shape(f, r)
    v = valid_mask(f, a.mask) & np.isfinite(r)
    out = {'check': 'direction', 'valid_px': int(v.sum()),
           'forward': describe(f, v), 'reversed': describe(r, v)}
    for k in ('mean', 'frac_gt_0.5', 'top1pct_mean'):
        out[f'ratio_{k}'] = out['forward'][k] / max(out['reversed'][k], 1e-6)
    if a.label:
        L = load(a.label) > 0
        same_shape(f, L)
        neg = (load(a.noink) > 0) if a.noink else ~L
        out['auc_forward'] = auc(f[v & L], f[v & neg])
        out['auc_reversed'] = auc(r[v & L], r[v & neg])
    return out


def check_label(a):
    m = load(a.map); L = load(a.label) > 0
    same_shape(m, L)
    v = valid_mask(m, a.mask)
    neg = (load(a.noink) > 0) if a.noink else ~L
    real = auc(m[v & L], m[v & neg])
    H, W = m.shape
    n_ink = (v & L).sum()
    # move the whole label to other spots of the same map; keep a placement only
    # if at least half of its ink still lands on valid pixels and it really moved
    min_shift = max(16, int(0.02 * min(H, W)))
    c = 8                               # coarse grid to screen placements fast
    vc, Lc = down(v.astype(np.float32), c) > 0.5, down(L.astype(np.float32), c) > 0
    n_c = (vc & Lc).sum()
    null, tries = [], 0
    while len(null) < a.n and tries < 200 * a.n:
        tries += 1
        dy, dx = c * int(rng.integers(-H // (2 * c), H // (2 * c))), c * int(rng.integers(-W // (2 * c), W // (2 * c)))
        if abs(dy) < min_shift and abs(dx) < min_shift:
            continue
        if (vc & np.roll(Lc, (dy // c, dx // c), (0, 1))).sum() < 0.5 * n_c:
            continue
        Ls, Ns = np.roll(L, (dy, dx), (0, 1)), np.roll(neg, (dy, dx), (0, 1))
        if (v & Ls).sum() < 0.5 * n_ink:
            continue
        null.append(auc(m[v & Ls], m[v & Ns], cap=300_000))
    if not null:
        sys.exit('no valid random placement found (label too large for the valid area?)')
    null = np.array(null)
    return {'check': 'label', 'ink_px': int((v & L).sum()), 'noink_px': int((v & neg).sum()),
            'auc': real, 'null_n': int(null.size), 'null_mean': float(null.mean()),
            'null_max': float(null.max()), 'p': float((1 + (null >= real).sum()) / (1 + null.size))}


def check_witness(a):
    A, B = load(a.a), load(a.b)
    same_shape(A, B)
    v = valid_mask(A, a.mask) & valid_mask(B, None)
    f = max(1, int(np.sqrt(v.sum() / 1_000_000)))   # keep ~1M px
    lo, hi = a.band
    Ad, Bd, vd = down(band(A, v, lo, hi), f), down(band(B, v, lo, hi), f), down(v.astype(np.float32), f) > 0.99
    blk = max(4, a.block // f)
    elig, vd = block_grid(vd, blk)
    real = corr(Ad[vd], Bd[vd])
    ns = null_stats(real, [corr(Ad[vd], block_shuffle(Bd, blk, elig)[vd]) for _ in range(a.n)])
    out = {'check': 'witness', 'downsample': f, 'band_px': [lo, hi], 'corr': real, 'null_n': a.n,
           'null_mean': ns['null_mean'], 'null_max': ns['null_max'], 'p': ns['p'], 'null_nan': ns['null_nan']}
    if a.b_rev:
        Br = load(a.b_rev)
        same_shape(A, Br)
        Brd = down(band(Br, v & np.isfinite(Br), lo, hi), f)
        out['corr_with_b_reversed'] = corr(Ad[vd], Brd[vd])
    return out


def check_triangle(a):
    """All pairs among >=3 maps. A map is 'consistent' only if it agrees
    (corr above its pair's block-shuffle null, p<alpha) with EVERY other map.
    One witness can be fooled by shared non-ink structure; a triangle cannot
    be fooled as easily."""
    names = [n.split('=', 1)[0] if '=' in n else n for n in a.maps]
    paths = [n.split('=', 1)[1] if '=' in n else n for n in a.maps]
    if len(paths) < 3:
        sys.exit('triangle needs at least 3 maps')
    M = [load(p) for p in paths]
    same_shape(*M)
    v = valid_mask(M[0], a.mask)
    for m in M[1:]:
        v &= valid_mask(m, None)
    f = max(1, int(np.sqrt(v.sum() / 1_000_000)))
    vd = down(v.astype(np.float32), f) > 0.99
    lo, hi = a.band
    D = [down(band(m, v, lo, hi), f) for m in M]
    blk = max(4, a.block // f)
    vd0 = int(vd.sum()); elig, vd = block_grid(vd, blk)
    area = {'valid_px': vd0, 'null_blocks': int(elig.sum()), 'used_px': int(vd.sum())}
    from itertools import combinations
    n_m = len(M)
    agree = np.zeros((n_m, n_m), bool)
    pairs = {}
    for i, j in combinations(range(n_m), 2):
        real = corr(D[i][vd], D[j][vd])
        ns = null_stats(real, [corr(D[i][vd], block_shuffle(D[j], blk, elig)[vd]) for _ in range(a.n)])
        p, nmax = ns['p'], ns['null_max']
        pairs[f'{names[i]} x {names[j]}'] = {'corr': real, 'null_max': nmax, 'p': p, 'null_nan': ns['null_nan'],
                                             'ratio': real / max(nmax, 1e-9)}
        agree[i, j] = agree[j, i] = (p < a.alpha) and real >= a.min_ratio * nmax
    # core = largest group (3+) in which every pair agrees. Correlation strength is NOT
    # used to break ties: a blind map can agree strongly with one witness through shared
    # papyrus structure, so the strongest pair is not evidence of ink.
    # --core-from: only these maps may form the core (e.g. maps in the layer order fixed by geometry);
    # the others are probes judged against it.
    elig = list(range(n_m)) if not a.core_from else [i for i, n in enumerate(names) if n in a.core_from]
    cores = []
    for k in range(len(elig), 2, -1):
        cores = [g for g in combinations(elig, k) if all(agree[i, j] for i, j in combinations(g, 2))]
        if cores:
            break
    if len(cores) != 1:
        why = ('no 3 maps agree pairwise' if not cores else
               f'{len(cores)} different groups of {len(cores[0])} close; cannot tell which one is ink')
        return {'check': 'triangle', 'downsample': f, 'area': area, 'alpha': a.alpha, 'min_ratio': a.min_ratio, 'pairs': pairs, 'core': [],
                'verdict': {n: f'unresolved ({why})' for n in names},
                'note': 'add another independent model, or use a label/camera truth if one exists'}
    core = cores[0]
    verdict = {}
    for i, n in enumerate(names):
        if i in core:
            verdict[n] = 'consistent'
        elif any(agree[i, j] for j in core):
            verdict[n] = 'suspect (agrees with part of the core only)'
        else:
            verdict[n] = 'isolated (agrees with none of the core)'
    return {'check': 'triangle', 'downsample': f, 'area': area, 'alpha': a.alpha, 'min_ratio': a.min_ratio, 'pairs': pairs,
            'core': [names[i] for i in core], 'verdict': verdict,
            'note': 'core = largest set of maps that all agree pairwise (corr above block-shuffle null). '
                    'A single witness can share non-ink structure with a map; a core of 3+ independent '
                    'models is much harder to fool.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    d = sp.add_parser('direction'); d.add_argument('fwd'); d.add_argument('rev')
    l = sp.add_parser('label'); l.add_argument('map'); l.add_argument('label')
    w = sp.add_parser('witness'); w.add_argument('a'); w.add_argument('b'); w.add_argument('--b-rev')
    w.add_argument('--block', type=int, default=64)
    t = sp.add_parser('triangle', help='all pairs among 3+ maps, given as NAME=PATH')
    t.add_argument('maps', nargs='+'); t.add_argument('--block', type=int, default=64)
    t.add_argument('--alpha', type=float, default=0.01)
    t.add_argument('--min-ratio', type=float, default=2.0,
                   help='pair agrees only if corr >= MIN_RATIO x null_max (PREREG: 2.0)')
    t.add_argument('--core-from', nargs='+', metavar='NAME',
                   help='only these maps may form the core; the rest are judged against it')
    for p in (w, t):
        p.add_argument('--band', type=float, nargs=2, default=[2, 20], metavar=('LO', 'HI'),
                       help='stroke-scale band in px (difference of Gaussians); 0 0 = off. '
                            'Default 2 20 suits ~8-9 um maps (strokes ~0.1-0.4 mm)')
    for p in (d, l, w, t):
        p.add_argument('--mask')
    for p in (d, l):
        p.add_argument('--noink')
    d.add_argument('--label')
    for p in (l, w, t):
        p.add_argument('--n', type=int, default=500)
    a = ap.parse_args()
    out = {'direction': check_direction, 'label': check_label, 'witness': check_witness,
           'triangle': check_triangle}[a.cmd](a)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
