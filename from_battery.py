#!/usr/bin/env python3
"""Run the kit on the maps of an ink-sdk battery (github.com/LimeGS/ink-sdk), at one depth centre and width.

The battery writes cells/<profile>/c<centre>_s<step>/probability.npy (forward) and probability_reverse.npy for every
9 um profile it ran. This script collects one cell per chosen profile, puts every map on one grid (the largest map's;
resampled profiles come out on a coarser grid), adds maps from other tools if you have them (--extra), writes a kit
segment folder and runs segment.py on it. ink-sdk is not needed to run this; only its output folder.

Layer order: --order forward|reverse if you know it. Otherwise the kit decides from the maps alone: the triangle's
unique core of 3+ maps on one side, else (with exactly 3 models) the trio-strength tie-break sealed in PREREG_HELDOUT2.
If neither decides, it stops without a verdict. The geometry rule (mesh + CT) is not available from a battery folder.

  python from_battery.py BATTERY_DIR OUT_DIR --centre 0 --step 1 --models reader-v3 reader-v2 dense-native
  python from_battery.py BATTERY_DIR OUT_DIR --models reader-v3 reader-v2 --extra base=base_f.npy,base_r.npy
"""
import argparse, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import inkcheck as ik
import segment


def resize(a, shape):
    """Bilinear resize, pixel-centre aligned (the same rule as ink-sdk's ensemble)."""
    a = np.asarray(a, np.float32)
    if a.shape == tuple(shape):
        return a
    def axis(n_in, n_out):
        x = np.clip((np.arange(n_out) + 0.5) * n_in / n_out - 0.5, 0, n_in - 1)
        i0 = np.floor(x).astype(int); return i0, np.minimum(i0 + 1, n_in - 1), (x - i0).astype(np.float32)
    y0, y1, fy = axis(a.shape[0], shape[0]); x0, x1, fx = axis(a.shape[1], shape[1])
    top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx
    bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
    return (top * (1 - fy[:, None]) + bot * fy[:, None]).astype(np.float32)


def short(profile):
    """ink_9um@reader-v2-step040000 -> reader-v2; ink_9um@scrollprize-seed43-step75000 -> seed43."""
    s = profile.split('@')[-1]
    s = re.sub(r'^scrollprize-', '', s); s = re.sub(r'-step\d+$', '', s)
    return re.sub(r'[^A-Za-z0-9_-]', '_', s)


def collect(battery, centre, step, wanted):
    rep = json.load(open(os.path.join(battery, 'BATTERY.json'), encoding='utf-8'))
    rows = [r for r in rep['cells'] if r.get('ok') and r['centre'] == centre and r['step'] == step]
    have = {short(r['profile']): r for r in rows}
    if not wanted:
        wanted = sorted(have)
    missing = [w for w in wanted if w not in have]
    if missing:
        raise SystemExit(f'no ok cell at centre {centre:+d} step {step} for {missing}; available: {sorted(have)}')
    maps = {}
    for w in wanted:
        d = have[w]['dir']
        if not os.path.isdir(d):                                     # battery moved: use the path under BATTERY_DIR
            d = os.path.join(battery, 'cells', os.path.basename(os.path.dirname(d)), os.path.basename(d))
        f, r = os.path.join(d, 'probability.npy'), os.path.join(d, 'probability_reverse.npy')
        if not (os.path.isfile(f) and os.path.isfile(r)):
            raise SystemExit(f'{w}: needs probability.npy and probability_reverse.npy in {d} (a both-direction profile)')
        maps[w] = (np.load(f), np.load(r))
    return rep, maps


def valid_mask(rep, shape):
    """CT > 0 in every layer of the battery's surface volume, on the map grid; None if the volume is not readable."""
    try:
        import zarr
        g = zarr.open(rep['surface_volume'], mode='r')
        a = g['0'] if not hasattr(g, 'shape') else g
        v = np.ones(a.shape[1:], bool)
        for r0 in range(0, a.shape[1], 256):
            v[r0:r0 + 256] = (np.asarray(a[:, r0:r0 + 256, :]) > 0).all(0)
        return resize(v.astype(np.float32), shape) > 0.5, a.shape[2]
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('battery'); ap.add_argument('out')
    ap.add_argument('--centre', type=int, default=0); ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--models', nargs='*', help='short profile names (reader-v3, reader-v2, dense-native, seed42, seed43); default: all')
    ap.add_argument('--extra', nargs='*', default=[], help='NAME=forward_map,reverse_map from another tool (.npy/.tif/.png)')
    ap.add_argument('--order', choices=['forward', 'reverse'])
    ap.add_argument('--win-mm', type=float, default=2.5)
    a = ap.parse_args()

    rep, maps = collect(a.battery, a.centre, a.step, a.models)
    for e in a.extra:
        name, paths = e.split('=', 1); f, r = paths.split(',')
        maps[name] = (ik.load(f), ik.load(r))
    if len(maps) < 3:
        raise SystemExit('need 3+ models (the triangle is the point)')
    shape = max((m[0].shape for m in maps.values()), key=lambda s: s[0] * s[1])
    os.makedirs(a.out, exist_ok=True)
    for name, (f, r) in maps.items():
        np.save(os.path.join(a.out, f'{name}.npy'), resize(f, shape))
        np.save(os.path.join(a.out, f'{name}_reverse.npy'), resize(r, shape))
    mask, sv_w = valid_mask(rep, shape)
    if mask is not None:
        np.save(os.path.join(a.out, 'mask.npy'), mask.astype(np.uint8) * 255)
    px = float(rep['pixel_um']) * (sv_w / shape[1] if sv_w else 1.0)
    names = list(maps)
    prov = {'battery': os.path.abspath(a.battery), 'centre': a.centre, 'step': a.step, 'models': names,
            'extra': a.extra, 'grid': list(shape), 'px_um': px, 'mask_from_surface_volume': mask is not None}

    order, how = a.order, 'given (--order)'
    if order is None:
        mp = os.path.join(a.out, 'mask.npy') if mask is not None else None
        tri = segment.run_triangle({**{f'{n}_f': os.path.join(a.out, f'{n}.npy') for n in names},
                                    **{f'{n}_r': os.path.join(a.out, f'{n}_reverse.npy') for n in names}}, mp, None)
        core = tri['core']; side = {c[-1] for c in core}
        order = 'forward' if side == {'f'} and len(core) >= 3 else 'reverse' if side == {'r'} and len(core) >= 3 else None
        how = f'triangle core {core}'
        if order is None and len(names) == 3:
            ts = segment.trio_strength(tri); order = ts['order']; prov['trio_strength'] = ts
            how = f'trio strength (ratio {ts["ratio"]:.2f}, threshold {ts["threshold"]})'
        elif order is None:
            how += '; trio strength is sealed for exactly 3 models: rerun with 3 --models, or give --order'
    prov['order'] = order; prov['order_from'] = how
    json.dump(prov, open(os.path.join(a.out, 'from_battery.json'), 'w', encoding='utf-8'), indent=1)
    print(f'{len(names)} models {names} on grid {shape}, {px:.2f} um/px | order: {order} ({how})', flush=True)
    if order is None:
        raise SystemExit('no layer order: the kit cannot say whether these maps show ink; stopping here')
    segment.run(a.out, names, order, px_um=px, win_mm=a.win_mm)


if __name__ == '__main__':
    main()
