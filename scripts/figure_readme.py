#!/usr/bin/env python3
"""README figure: the same Reader v2 map of PHercParis4 w02, clean (left) and with invented letters planted (right).
Window verdicts from segment.py (green = seen by the other models, red = only this map). On the right the planted
letters are outlined in blue, so you can see the red windows land on them. Public data only.
usage: python scripts/figure_readme.py CLEAN_REPORT_DIR TAMPERED_REPORT_DIR FAKE_MASK.npy MAP_CLEAN MAP_TAMPERED MASK OUT.png"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_dilation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import inkcheck as ik

clean_dir, tamp_dir, fake_p, map_c, map_t, mask_p, out = sys.argv[1:8]
fake = np.load(fake_p) > 0; mask = ik.load(mask_p) > 0
# crop to the planted letters plus a margin of ~1.5 letters, inside the image
ys, xs = np.nonzero(fake if fake.any() else mask); pad = 400
y0, y1 = max(0, ys.min() - pad), min(mask.shape[0], ys.max() + pad)
x0, x1 = max(0, xs.min() - pad), min(mask.shape[1], xs.max() + pad)
W_OUT = 900


def panel(map_path, npz, outline=None, title=''):
    m = ik.load(map_path); v = ik.valid_mask(m, mask_p)
    lo, hi = np.percentile(m[v], [1, 99.5]); g = np.clip((m - lo) / max(hi - lo, 1e-6), 0, 1); g[~v] = 0
    g = g[y0:y1, x0:x1]; s = W_OUT / g.shape[1]
    img = Image.fromarray(np.stack([g * 236, g * 228, g * 210], -1).astype(np.uint8)).resize((W_OUT, int(g.shape[0] * s)))
    dr = ImageDraw.Draw(img, 'RGBA'); d = np.load(npz); st = d['state']; h = int(d['win_px']) / 2 * s
    for i, y in enumerate(d['cy']):
        for j, x in enumerate(d['cx']):
            if st[i, j]:
                c = (47, 160, 95, 80) if st[i, j] == 1 else (225, 45, 45, 150)
                cx_, cy_ = (x - x0) * s, (y - y0) * s
                dr.rectangle([cx_ - h / 2, cy_ - h / 2, cx_ + h / 2, cy_ + h / 2], fill=c)
    if outline is not None:
        o = outline[y0:y1, x0:x1]; edge = binary_dilation(o, iterations=6) & ~binary_dilation(o, iterations=2)
        e = np.array(Image.fromarray((edge * 255).astype(np.uint8)).resize(img.size)) > 60
        a = np.array(img); a[e] = (70, 150, 255); img = Image.fromarray(a)
    bar = Image.new('RGB', (W_OUT, 46), (31, 27, 22)); bd = ImageDraw.Draw(bar)
    try:
        f = ImageFont.truetype('DejaVuSans.ttf', 22)
    except OSError:
        f = ImageFont.load_default()
    bd.text((14, 10), title, fill=(239, 232, 220), font=f)
    full = Image.new('RGB', (W_OUT, img.height + 46)); full.paste(bar, (0, 0)); full.paste(img, (0, 46)); return full


L = panel(map_c, f'{clean_dir}/local_rv2.npz', None, 'Reader v2, as it came out of the model')
R = panel(map_t, f'{tamp_dir}/local_rv2.npz', fake, 'same map + invented letters (blue outline)')
gap = 12; fig = Image.new('RGB', (2 * W_OUT + gap, max(L.height, R.height)), (22, 19, 15))
fig.paste(L, (0, 0)); fig.paste(R, (W_OUT + gap, 0)); fig.save(out, optimize=True)
print('saved', out, fig.size)
