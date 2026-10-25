"""Small synthetic segments for the smoke test: three 'models', each in both layer orders.

ink=True : every model draws the same letter-like strokes (plus its own texture) in the right order;
           in the other order the strokes fade. That is what real ink looks like to the kit.
ink=False: only texture, the same in both orders (nothing depends on depth).
No real data, so the test runs anywhere in a few seconds.
"""
import os
import numpy as np
from scipy.ndimage import gaussian_filter
import tifffile


def _strokes(shape, rng, n=80):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.zeros(shape, np.float32)
    for _ in range(n):
        y0, x0 = rng.uniform(20, h - 20), rng.uniform(20, w - 20)
        ang, ln = rng.uniform(0, np.pi), rng.uniform(15, 40)
        y1, x1 = y0 + ln * np.sin(ang), x0 + ln * np.cos(ang)
        dy, dx = y1 - y0, x1 - x0
        t = np.clip(((yy - y0) * dy + (xx - x0) * dx) / (dy * dy + dx * dx), 0, 1)
        d = np.hypot(yy - (y0 + t * dy), xx - (x0 + t * dx))
        a = np.maximum(a, (d < 3).astype(np.float32))
    return gaussian_filter(a, 1.0)


def _texture(shape, rng):
    t = gaussian_filter(rng.standard_normal(shape).astype(np.float32), 4)
    return (t - t.min()) / (t.max() - t.min())


def make(out_dir, ink=True, shape=(768, 768), seed=0, invent=None):
    """invent='m2': that model also draws strokes no other model sees (an invented-letter model)."""
    rng = np.random.default_rng(seed)
    os.makedirs(out_dir, exist_ok=True)
    truth = _strokes(shape, rng) if ink else np.zeros(shape, np.float32)
    for k, m in enumerate(('m1', 'm2', 'm3')):
        r = np.random.default_rng(seed + 10 + k)
        tex = 0.35 * _texture(shape, r)
        extra = _strokes(shape, np.random.default_rng(seed + 99), n=40) if m == invent else 0
        fwd = np.clip(0.8 * np.maximum(truth, extra) + tex + 0.03 * r.standard_normal(shape), 0, 1)
        rev = np.clip(0.03 * np.maximum(truth, extra) + tex + 0.03 * r.standard_normal(shape), 0, 1)
        tifffile.imwrite(os.path.join(out_dir, f'{m}.tif'), (fwd * 255).astype(np.uint8))
        tifffile.imwrite(os.path.join(out_dir, f'{m}_reverse.tif'), (rev * 255).astype(np.uint8))
    return out_dir
