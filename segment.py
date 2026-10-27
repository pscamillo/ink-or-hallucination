#!/usr/bin/env python3
"""Run every ink-or-hallucination check on one segment and write a report (HTML + JSON + PNG).

Input: a folder with, for each model NAME, its map in the order you want to check (NAME.tif) and the same model
run in the other layer order (NAME_reverse.tif); .npy/.png also work. Optional: mask.npy (valid area).
Which order is the 'right' one comes from the layer-order rule (geometry) or from you: --order forward|reverse.

  python segment.py SEGMENT_DIR --models ink9 rv2 rv3 --px-um 9.6            # window = 2.5 mm
  python segment.py SEGMENT_DIR --models ink9 rv2 rv3 --win 260 --order reverse

Uses inkcheck.py unchanged (the sealed v12 core). Every check is run exactly as the command line would run it
(same random seed per call), so numbers match `inkcheck.py ...` run by hand.
"""
import argparse, base64, glob, html, io, json, os, sys, time
from types import SimpleNamespace
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import inkcheck as ik

MIN_JUDGED = 20   # below this, a 'not supported' fraction says nothing (1 of 3 is not 33% of anything)
V12 = dict(score='both', null='swap', n=19, min_null=10, tol_px=6.0, ink_rel=0.5, min_ink=0.005, u_k=3.0, u_min=0.20,
           floor_k=2.0, stroke='floor', energy_k=1.25, thr_z=4.0, min_frac=0.05, resid_k=1.5, band=[2, 20], out=None)


def find(d, name):
    for ext in ('.tif', '.tiff', '.npy', '.png'):
        p = os.path.join(d, name + ext)
        if os.path.exists(p):
            return p
    return None


def run_triangle(maps, mask, core_from, n=300):
    ik.rng = np.random.default_rng(0)
    a = SimpleNamespace(maps=[f'{k}={v}' for k, v in maps.items()], block=64, alpha=0.01, min_ratio=2.0,
                        core_from=core_from, band=[2, 20], mask=mask, n=n)
    return ik.check_triangle(a)


TIE_RATIO = 1.25   # PREREG_HELDOUT2 (sealed before the run; set from the training triangles)


def _agrees(v, a, mr):
    """A saved triangle pair agrees: p < alpha and corr >= min_ratio x null_max (missing or NaN values: no)."""
    try:
        return bool(v) and float(v['p']) < a and float(v['corr']) >= mr * float(v['null_max'])
    except (KeyError, TypeError, ValueError):
        return False


def trio_strength(tri, threshold=TIE_RATIO):
    """Layer order from a 6-map triangle (maps named <model>_f / <model>_r), as sealed in PREREG_HELDOUT2:
    S_side = median of the 3 pairwise corr among that side's maps; ratio = max(S_f, S_r) / max(min(S_f, S_r), 1e-6);
    the stronger side's order if ratio >= threshold, else None (no verdict). Used only when the order rule and the
    unique-core fallback both abstain.
    Safety guard added after the seal (docs/NOTE_2026-10-27_TIEBREAK_GUARD.md): no verdict either if min(S) <= 0
    (the ratio is then meaningless) or if the stronger side's 3 maps do not all agree pairwise (p < alpha and
    corr >= min_ratio x null_max): a trio that does not agree cannot fix the order."""
    S = {}
    for sd in 'fr':
        c3 = [v['corr'] for k, v in tri['pairs'].items() if all(n.endswith('_' + sd) for n in k.split(' x '))]
        if len(c3) != 3:
            raise ValueError(f'trio strength needs exactly 3 models per side, got {len(c3)} {sd}-side pairs')
        S[sd] = float(np.median(c3))
    ratio = max(S.values()) / max(min(S.values()), 1e-6)
    order = ('forward' if S['f'] > S['r'] else 'reverse') if ratio >= threshold else None
    guard = None
    if order is not None:
        a, mr = float(tri.get('alpha', 0.01)), float(tri.get('min_ratio', 2.0))
        sd = order[0]
        strong = [v for k, v in tri['pairs'].items() if all(n.endswith('_' + sd) for n in k.split(' x '))]
        if min(S.values()) <= 0:
            guard = 'weaker trio median corr <= 0'
        elif not all(_agrees(v, a, mr) for v in strong):
            guard = 'stronger trio does not all agree'
        if guard:
            order = None
    return {'S_forward': S['f'], 'S_reverse': S['r'], 'ratio': ratio, 'threshold': threshold, 'order': order,
            'guard': guard}


def run_local(target, others, floor, mask, win, out_npz):
    ik.rng = np.random.default_rng(0)
    a = SimpleNamespace(target=target, others=others, floor=floor, mask=mask, win=win, out_npz=out_npz, **V12)
    return ik.check_local(a)


def alignment(paths, mask, max_shift=20):
    """Shift (px) of each map against the mean of the others, from phase correlation of the stroke band.
    The windowed score U assumes pixel-aligned maps; a shift of a few px reads as disagreement everywhere."""
    M = {k: ik.load(p) for k, p in paths.items()}
    v = None
    for m in M.values():
        vm = ik.valid_mask(m, mask) if v is None else ik.valid_mask(m, None)
        v = vm if v is None else v & vm
    from scipy.ndimage import binary_erosion
    # keep only the inside of the valid area: the mask edge is identical in every map and would pin the peak at 0
    inner = binary_erosion(v, iterations=max_shift + 25)
    if inner.sum() < 10000:
        inner = v
    B = {}
    for k, m in M.items():
        b = np.where(inner, ik.band(m, v, 2, 20), 0).astype(np.float32)
        s = b[inner].std(); B[k] = np.where(inner, (b - b[inner].mean()) / (s if s > 0 else 1), 0)
    FT = {k: np.fft.fft2(b) for k, b in B.items()}

    def shift(a, b):   # how far map a is shifted against map b (plain cross-correlation peak within +-max_shift)
        c = np.fft.fftshift(np.real(np.fft.ifft2(FT[a] * np.conj(FT[b])))); cy0, cx0 = c.shape[0] // 2, c.shape[1] // 2
        w = c[cy0 - max_shift:cy0 + max_shift + 1, cx0 - max_shift:cx0 + max_shift + 1]
        y, x = np.unravel_index(np.argmax(w), w.shape); return int(y - max_shift), int(x - max_shift)
    names = list(B); pair = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pair[(a, b)] = shift(a, b); pair[(b, a)] = tuple(-s for s in pair[(a, b)])
    out = {}
    for k in names:
        to = {q: pair[(k, q)] for q in names if q != k}
        # aligned if it sits within 2 px of at least one other map; a single shifted map then stands out
        ok = any(abs(dy) <= 2 and abs(dx) <= 2 for dy, dx in to.values())
        med = tuple(int(np.median([s[i] for s in to.values()])) for i in (0, 1))
        out[k] = {'dy_px': med[0], 'dx_px': med[1], 'ok': bool(ok), 'pairs': {q: list(s) for q, s in to.items()}}
    return out


def direction_ratio(fwd, rev, mask, npz):
    """Per window: stroke energy in this map / in the same model's other-order map (D). Real ink has depth and fades
    when the stack is reversed. Informative only: on PHercParis4 (blind, RESULT_DIRECAO) model-made strokes with no
    label ink had median D 3.0 vs 6.6 for real ink (AUC 0.76); on 12 other segments the gap was smaller (AUC 0.65).
    No threshold has been validated, so it is shown, not used for a verdict."""
    from scipy.ndimage import uniform_filter
    d = np.load(npz); W = int(d['win_px']); cy, cx = d['cy'], d['cx']
    F, R = ik.load(fwd), ik.load(rev); v = ik.valid_mask(F, mask) & ik.valid_mask(R, None); w = v.astype(np.float32)
    n = np.maximum(uniform_filter(w, W, mode='constant'), 1e-9)
    def e(m):
        b = ik.band(m, v, 2, 20).astype(np.float32)
        m1 = uniform_filter(w * b, W, mode='constant') / n; m2 = uniform_filter(w * b * b, W, mode='constant') / n
        x = np.sqrt(np.maximum(m2 - m1 ** 2, 0)); return x[np.ix_(np.minimum(cy, x.shape[0] - 1), np.minimum(cx, x.shape[1] - 1))]
    D = e(F) / np.maximum(e(R), 1e-9); jj = d['state'] > 0
    return D, {'median_D': float(np.median(D[jj])) if jj.any() else float('nan'),
               'frac_D_below_1.5': float(np.mean(D[jj] < 1.5)) if jj.any() else float('nan'),
               'unsupported_with_D_below_1.5': int(((d['state'] == 2) & (D < 1.5)).sum())}


def overlay_png(map_path, npz, mask, max_w=1600, D=None):
    """Grey map with the window verdicts on top: green = supported, red = NOT supported, nothing = not judged.
    A yellow outline marks windows whose strokes barely fade in the other layer order (D < 1.5, informative).
    The picture is cropped to the area that has data."""
    from PIL import Image, ImageDraw
    m = ik.load(map_path); d = np.load(npz)
    v = ik.valid_mask(m, mask)
    ys, xs = np.nonzero(v) if v.any() else (np.array([0, m.shape[0] - 1]), np.array([0, m.shape[1] - 1]))
    pad = int(0.02 * max(m.shape))
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad + 1)
    lo, hi = np.percentile(m[v], [1, 99.5]) if v.any() else (0, 1)
    g = np.clip((m - lo) / max(hi - lo, 1e-6), 0, 1); g[~v] = 0; g = g[y0:y1, x0:x1]
    s = min(1.0, max_w / g.shape[1])
    base = (np.stack([g * 236, g * 228, g * 210], -1) + np.stack([~v[y0:y1, x0:x1]] * 3, -1) * 0).astype(np.uint8)
    img = Image.fromarray(base).resize((max(1, int(g.shape[1] * s)), max(1, int(g.shape[0] * s))))
    dr = ImageDraw.Draw(img, 'RGBA'); st = d['state']; W = int(d['win_px']); h = W / 2 * s
    for i, y in enumerate(d['cy']):
        for j, x in enumerate(d['cx']):
            if st[i, j] == 0:
                continue
            col = (47, 160, 95, 75) if st[i, j] == 1 else (225, 45, 45, 140)
            cxp, cyp = (x - x0) * s, (y - y0) * s
            box = [cxp - h / 2, cyp - h / 2, cxp + h / 2, cyp + h / 2]
            dr.rectangle(box, fill=col)
            if D is not None and D[i, j] < 1.5:
                dr.rectangle(box, outline=(245, 200, 40, 255), width=max(2, int(3 * s)))
    buf = io.BytesIO(); img.save(buf, 'PNG', optimize=True); return buf.getvalue()


def run(seg_dir, models, order='forward', mask=None, win=None, px_um=None, win_mm=2.5, out_dir=None, log=None):
    log = log or (lambda msg: print(msg, flush=True))
    t0 = time.time()
    out_dir = out_dir or os.path.join(seg_dir, 'inkcheck_report'); os.makedirs(out_dir, exist_ok=True)
    mask = mask or find(seg_dir, 'mask')
    if win is None:
        if not px_um:
            raise SystemExit('give --win (px) or --px-um (pixel size of the maps, to get a 2.5 mm window)')
        win = int(round(win_mm * 1000 / px_um))
    good, bad = {}, {}
    for m in models:
        f, r = find(seg_dir, m), find(seg_dir, m + '_reverse')
        if not f or not r:
            raise SystemExit(f'missing {m}.tif or {m}_reverse.tif in {seg_dir}')
        good[m], bad[m] = (f, r) if order == 'forward' else (r, f)
    if len(models) < 3:
        raise SystemExit('need 3+ models (the triangle is the point)')
    R = {'segment': os.path.abspath(seg_dir), 'models': models, 'order': order, 'win_px': win, 'mask': mask}

    log('1/3 alignment check'); R['alignment'] = alignment(good, mask)
    log('2/3 triangle (all maps, both orders)')
    allm = {**{f'{m}_ok': good[m] for m in models}, **{f'{m}_other': bad[m] for m in models}}
    R['triangle'] = run_triangle(allm, mask, [f'{m}_ok' for m in models])
    log('3/3 windowed check (each map against the others) + depth check'); R['local'] = {}
    for m in models:
        npz = os.path.join(out_dir, f'local_{m}.npz')
        j = run_local(good[m], [good[q] for q in models if q != m], bad[m], mask, win, npz)
        R['local'][m] = {k: j[k] for k in ('judged', 'supported', 'unsupported', 'unsupported_frac', 'no_null_windows', 'u_flagged')}
        D, dstat = direction_ratio(good[m], bad[m], mask, npz); R['local'][m]['direction'] = dstat
        with open(os.path.join(out_dir, f'windows_{m}.png'), 'wb') as fh:
            fh.write(overlay_png(good[m], npz, mask, D=D))
        log(f'   {m}: judged {j["judged"]}, NOT supported {j["unsupported"]}')
    R['seconds'] = round(time.time() - t0, 1)
    with open(os.path.join(out_dir, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(R, fh, indent=1, default=float)
    with open(os.path.join(out_dir, 'report.html'), 'w', encoding='utf-8') as fh:   # the report has µ, ≈, →
        fh.write(to_html(R, out_dir))
    log(f'report: {os.path.join(out_dir, "report.html")}')
    return R


def summary(R):
    """One plain sentence per check, for people who will not read the numbers."""
    tri = R['triangle']; lines = []
    ok = [m for m in R['models'] if tri['verdict'].get(f'{m}_ok') == 'consistent']
    other_ok = [m for m in R['models'] if tri['verdict'].get(f'{m}_other') == 'consistent']
    def pc(a, b):
        p = tri['pairs'].get(f'{a} x {b}') or tri['pairs'].get(f'{b} x {a}')
        return p['corr'] if p else float('nan')
    okn = [f'{m}_ok' for m in R['models']]; otn = [f'{m}_other' for m in R['models']]
    c_in = float(np.nanmedian([pc(a, b) for i, a in enumerate(okn) for b in okn[i + 1:]]))
    c_x = float(np.nanmedian([pc(a, b) for a in okn for b in otn]))
    if not tri['core']:
        lines.append(('warn', f'Triangle: unresolved: {next(iter(tri["verdict"].values()))}. No group of 3 models agrees.'))
    elif len(ok) == len(R['models']) and not other_ok:
        rel = max(0.0, c_x) / c_in if c_in > 0 else float('nan')
        how = 'strongly' if c_in >= 0.5 else 'moderately' if c_in >= 0.2 else 'weakly'
        txt = (f'Triangle: the {len(ok)} models agree {how} in the chosen layer order (median corr {c_in:.2f}); maps read in '
               f'the other order agree with them only weakly (median corr {max(0.0, c_x):.2f}, {rel:.0%} of that). ')
        if rel < 0.2:
            lines.append(('good', txt + 'This is the pattern of real ink in the chosen order. (A small leftover in the other '
                                        'order is normal on segments the models were trained on.)'))
        else:
            lines.append(('warn', txt + 'The other order keeps a lot of the same structure; check the layer order.'))
    else:
        lines.append(('warn', f'Triangle: core = {tri["core"]}. Check the layer order and the maps outside the core.'))
    c_ot = float(np.nanmedian([pc(a, b) for i, a in enumerate(otn) for b in otn[i + 1:]]))
    if c_ot >= 0.2:
        lines.append(('note', f'Other order, among themselves: the maps read in the other order also agree with each other '
                              f'(median corr {c_ot:.2f}; chosen order {c_in:.2f}, ratio {c_in / c_ot:.2f}), on a pattern that barely '
                              f'matches the chosen-order maps. Two shared patterns are common because the models are related '
                              f'(same architecture and training data). The chosen order is the stronger one by that ratio; '
                              f'what the other-order pattern is (another sheet, texture, a shared model habit) the kit cannot say.'))
    bad_al = [m for m, a in R['alignment'].items() if not a['ok']]
    if bad_al:
        lines.append(('warn', 'Alignment: ' + ', '.join(f'{m} is shifted by ({R["alignment"][m]["dy_px"]}, {R["alignment"][m]["dx_px"]}) px'
                                                       for m in bad_al) + ' against the others. The windowed check will read that '
                              'as disagreement; register the maps first.'))
    for m, L in R['local'].items():
        if L['judged'] == 0:
            lines.append(('warn', f'Windows, {m}: no window judged (no strokes above the wrong-order floor).'))
            continue
        if L['judged'] < MIN_JUDGED:
            lines.append(('warn', f'Windows, {m}: only {L["judged"]} windows with strokes above the wrong-order floor, too few '
                                  f'to judge ({L["unsupported"]} not supported). This model sees almost nothing here.'))
            continue
        fr = L['unsupported'] / L['judged']
        kind = 'good' if fr <= 0.05 else 'warn' if fr <= 0.20 else 'bad'
        lines.append((kind, f'Windows, {m}: {L["unsupported"]} of {L["judged"]} windows with strokes are NOT supported by the '
                            f'other models ({fr:.0%}). On the validation segments, good maps were at 0-3%.'))
    return lines


def overall(R):
    """One overall status from the summary lines: the worst of them. 'none' when no map has any stroke above its
    other-order floor: there is nothing ink-like to check, which is an answer, not a failure."""
    if all(L['judged'] == 0 for L in R['local'].values()):
        return 'none'
    kinds = [k for k, _ in summary(R) if k != 'note']   # notes inform, they do not change the verdict
    return 'bad' if 'bad' in kinds else 'warn' if 'warn' in kinds else 'good'


def to_html(R, out_dir):
    def b64(name):
        p = os.path.join(out_dir, name)
        return base64.b64encode(open(p, 'rb').read()).decode() if os.path.exists(p) else ''
    seg = html.escape(os.path.basename(R['segment'].rstrip('/')))
    st = overall(R)
    head = {'good': ('Consistent with real ink', 'The models agree, in the right layer order, and almost every '
                     'stroke is seen by more than one model.'),
            'warn': ('Look closer', 'Some checks raised a flag. Read the points below before trusting this map.'),
            'bad': ('Not supported', 'A large share of this map is not seen by the other models.'),
            'none': ('No ink signal here', 'No map shows strokes that fade when the layer order is reversed, so there is '
                     'nothing ink-like to check. What the models show here does not depend on depth (papyrus texture, '
                     'not writing), or the ink is too faint for these models.')}[st]
    items = ''.join(f'<li class="{k}"><span class="dot"></span><span>{html.escape(t)}</span></li>' for k, t in summary(R))
    cards = ''
    for m, L in R['local'].items():
        fr = L['unsupported'] / L['judged'] if L['judged'] >= MIN_JUDGED else None
        kind = 'muted' if fr is None else 'good' if fr <= 0.05 else 'warn' if fr <= 0.20 else 'bad'
        d = L.get('direction') or {}
        dtxt = (f'<div class="sub">depth D median {d["median_D"]:.1f} · D&lt;1.5 in {d["frac_D_below_1.5"]:.0%}</div>'
                if d and L['judged'] >= MIN_JUDGED else '')
        big = f'{fr:.0%}' if fr is not None else '—'
        lbl = 'not supported' if fr is not None else ('nothing to judge' if not L['judged'] else f'only {L["judged"]} windows')
        img = b64(f'windows_{m}.png')
        cards += f"""<figure class="card {kind}">
  <figcaption><span class="model">{html.escape(m)}</span>
    <span class="big">{big}</span><span class="lbl">{lbl}</span></figcaption>
  <div class="sub">{L['unsupported']} of {L['judged']} windows with strokes · no null {L['no_null_windows']}</div>{dtxt}
  <img class="zoom" src="data:image/png;base64,{img}" alt="windows of {html.escape(m)}" title="click to enlarge">
</figure>"""
    tri = R['triangle']
    def vclass(v):
        return 'good' if v == 'consistent' else 'bad' if v.startswith('isolated') else 'warn' if v.startswith(('suspect', 'unresolved')) else 'muted'
    tri_rows = ''.join(f'<tr><td>{html.escape(k)}</td><td><span class="tag {vclass(v)}">{html.escape(v)}</span></td></tr>'
                       for k, v in tri['verdict'].items())
    pair_rows = ''.join(f'<tr><td>{html.escape(k)}</td><td class="n">{p["corr"]:.3f}</td><td class="n">{p["null_max"]:.3f}</td>'
                        f'<td class="n">{p["ratio"]:.1f}×</td></tr>' for k, p in tri['pairs'].items())
    al = ''.join(f'<tr><td>{m}</td><td class="n">{a["dy_px"]}, {a["dx_px"]}</td><td><span class="tag {"good" if a["ok"] else "bad"}">'
                 f'{"aligned" if a["ok"] else "shifted"}</span></td></tr>' for m, a in R['alignment'].items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ink or hallucination? · {seg}</title><style>
:root{{--bg:#f5f0e6;--paper:#fffdf8;--ink:#221d17;--soft:#6b6257;--line:#e3dacb;--accent:#a24a22;
--good:#2f7d4f;--good-bg:#e5f2e9;--warn:#9a6400;--warn-bg:#fbf0d9;--bad:#b3261e;--bad-bg:#fbe4e1;--muted:#6b6257;--muted-bg:#efe9df}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16130f;--paper:#1f1b16;--ink:#efe8dc;--soft:#a99f91;--line:#352e26;--accent:#e08a5c;
--good:#7fd19b;--good-bg:#1d3326;--warn:#f0c062;--warn-bg:#3a2e14;--bad:#f2897f;--bad-bg:#3d1d1a;--muted:#a99f91;--muted-bg:#29241e}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 16px}}
header{{background:linear-gradient(180deg,var(--paper),var(--bg));border-bottom:1px solid var(--line);padding:34px 0 26px}}
.kicker{{color:var(--accent);font-weight:600;letter-spacing:.08em;text-transform:uppercase;font-size:12px}}
h1{{font:600 38px/1.1 Georgia,"Iowan Old Style","Palatino Linotype",serif;margin:6px 0 8px}}
h1 em{{color:var(--accent);font-style:italic}}
.meta{{color:var(--soft);font-size:13px;display:flex;flex-wrap:wrap;gap:6px 14px}}
.pill{{background:var(--muted-bg);border:1px solid var(--line);border-radius:999px;padding:2px 10px;color:var(--ink)}}
.verdict{{margin:26px 0 8px;border-radius:14px;padding:18px 20px;display:flex;gap:16px;align-items:flex-start;border:1px solid var(--line)}}
.verdict.none{{background:var(--muted-bg)}} .verdict.good{{background:var(--good-bg)}} .verdict.warn{{background:var(--warn-bg)}} .verdict.bad{{background:var(--bad-bg)}}
.badge{{flex:none;width:44px;height:44px;border-radius:50%;display:grid;place-items:center;color:#fff;font:700 22px/1 system-ui}}
.none .badge{{background:var(--muted)}} .good .badge{{background:var(--good)}} .warn .badge{{background:var(--warn)}} .bad .badge{{background:var(--bad)}}
.verdict h2{{margin:0 0 4px;font:600 22px/1.2 Georgia,serif}} .verdict p{{margin:0;color:var(--soft)}}
h3{{font:600 19px/1.3 Georgia,serif;margin:30px 0 10px}}
ul.points{{list-style:none;padding:0;margin:0;display:grid;gap:8px}}
ul.points li{{display:flex;gap:10px;background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:10px 14px}}
.dot{{flex:none;width:10px;height:10px;border-radius:50%;margin-top:7px}}
li.good .dot{{background:var(--good)}} li.warn .dot{{background:var(--warn)}} li.bad .dot{{background:var(--bad)}} li.note .dot{{background:#8a8378}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--soft);font-size:13px;margin:8px 0 14px}}
.sw{{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin-right:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.grid.rows{{grid-template-columns:1fr}}
.bar{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
.toggle{{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--paper)}}
.toggle button{{border:0;background:none;color:var(--soft);padding:5px 12px;font:13px system-ui;cursor:pointer}}
.toggle button.on{{background:var(--ink);color:var(--paper)}}
#lb{{position:fixed;inset:0;background:rgba(10,8,6,.92);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out;padding:16px}}
#lb.on{{display:flex}} #lb img{{max-width:100%;max-height:100%;border-radius:6px}}
#lb span{{position:fixed;top:12px;right:18px;color:#eee;font:14px system-ui}}
.card{{margin:0;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:14px;border-top:4px solid var(--good)}}
.card.warn{{border-top-color:var(--warn)}} .card.bad{{border-top-color:var(--bad)}} .card.muted{{border-top-color:var(--line)}}
.card figcaption{{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}}
.model{{font-weight:600;font-size:16px;margin-right:auto}} .big{{font:600 30px/1 Georgia,serif}}
.card.muted .big{{color:var(--soft)}} .card.good .big{{color:var(--good)}} .card.warn .big{{color:var(--warn)}} .card.bad .big{{color:var(--bad)}}
.lbl,.sub{{color:var(--soft);font-size:13px}} .sub{{margin-top:2px}}
.card img{{display:block;width:100%;margin-top:10px;border-radius:8px;background:#000;cursor:zoom-in}}
details{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:10px 16px;margin:12px 0}}
summary{{cursor:pointer;font-weight:600}} .tw{{overflow-x:auto}}
table{{border-collapse:collapse;margin:10px 0;font-size:14px}} td,th{{border-bottom:1px solid var(--line);padding:6px 12px;text-align:left}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.tag{{border-radius:999px;padding:2px 9px;font-size:12.5px;white-space:nowrap}}
.tag.good{{background:var(--good-bg);color:var(--good)}} .tag.warn{{background:var(--warn-bg);color:var(--warn)}}
.tag.bad{{background:var(--bad-bg);color:var(--bad)}} .tag.muted{{background:var(--muted-bg);color:var(--muted)}}
.note{{color:var(--soft);font-size:13.5px;max-width:860px}}
footer{{color:var(--soft);font-size:12.5px;border-top:1px solid var(--line);margin-top:36px;padding:16px 0 30px}}
</style></head><body>
<header><div class="wrap"><div class="kicker">Label-free ink-map check</div>
<h1>Ink or <em>hallucination?</em></h1>
<div class="meta"><span class="pill">{seg}</span><span>models {', '.join(map(html.escape, R['models']))}</span>
<span>layer order checked: {R['order']}</span><span>window {R['win_px']} px (≈ one letter)</span><span>{R['seconds']} s</span></div></div></header>
<main class="wrap">
<section class="verdict {st}"><div class="badge">{ {'good': '✓', 'warn': '!', 'bad': '✕', 'none': '–'}[st] }</div>
<div><h2>{head[0]}</h2><p>{head[1]}</p></div></section>
<h3>What the checks found</h3><ul class="points">{items}</ul>
<div class="bar"><h3>Window by window</h3><div class="toggle" role="group" aria-label="layout">
<button id="b-side" class="on">side by side</button><button id="b-rows">one per row</button></div></div>
<div class="legend"><span><i class="sw" style="background:rgba(47,160,95,.55)"></i>seen by the other models</span>
<span><i class="sw" style="background:rgba(225,45,45,.75)"></i>only this map shows it</span>
<span><i class="sw" style="border:3px solid #f5c828"></i>barely fades in the other layer order (depth, informative)</span>
<span>no colour: not judged (no strokes above the other-order floor)</span></div>
<div class="grid" id="grid">{cards}</div>
<p class="note">An alarm means "the other models do not see this", not "this is fake". These checks measure agreement between
models, so an ink pattern that every model shares passes (and models trained on the same data share more). Real ink has depth and usually fades when the same model
reads the layers in the other order; that depth measure is shown for information only, no threshold has been validated.
Click a map to see it full screen.</p>
<details><summary>Triangle: verdicts and pairwise agreement</summary><div class="tw">
<table><tr><th>map</th><th>verdict</th></tr>{tri_rows}</table>
<table><tr><th>pair</th><th>corr</th><th>null max</th><th>ratio</th></tr>{pair_rows}</table></div></details>
<details><summary>Alignment between maps</summary><div class="tw"><table><tr><th>map</th><th>shift (dy, dx) px</th><th></th></tr>{al}</table></div></details>
</main>
<footer><div class="wrap">ink-or-hallucination · core inkcheck v12 (validated with sealed pre-registrations on PHerc0139, 0814, 1667 and
PHercParis4) · by Paulo Sergio Camillo</div></footer>
<div id="lb" title="click or Esc to close"><span>click or Esc to close</span><img alt=""></div>
<script>
const g=document.getElementById('grid'),bs=document.getElementById('b-side'),br=document.getElementById('b-rows');
function lay(r){{g.classList.toggle('rows',r);bs.classList.toggle('on',!r);br.classList.toggle('on',r);try{{localStorage.setItem('ioh-rows',r?'1':'0')}}catch(e){{}}}}
bs.onclick=()=>lay(false);br.onclick=()=>lay(true);
try{{if(localStorage.getItem('ioh-rows')==='1')lay(true)}}catch(e){{}}
const lb=document.getElementById('lb'),li=lb.querySelector('img');
document.querySelectorAll('img.zoom').forEach(i=>i.onclick=()=>{{li.src=i.src;lb.classList.add('on')}});
lb.onclick=()=>lb.classList.remove('on');document.addEventListener('keydown',e=>{{if(e.key==='Escape')lb.classList.remove('on')}});
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('segment_dir'); ap.add_argument('--models', nargs='+', required=True)
    ap.add_argument('--order', choices=['forward', 'reverse'], default='forward',
                    help='which file holds the right layer order: NAME.tif (forward) or NAME_reverse.tif (reverse)')
    ap.add_argument('--mask'); ap.add_argument('--win', type=int); ap.add_argument('--px-um', type=float)
    ap.add_argument('--win-mm', type=float, default=2.5); ap.add_argument('--out')
    a = ap.parse_args()
    run(a.segment_dir, a.models, a.order, a.mask, a.win, a.px_um, a.win_mm, a.out)


if __name__ == '__main__':
    main()
