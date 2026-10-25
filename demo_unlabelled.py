#!/usr/bin/env python3
"""End-to-end demo on an UNLABELLED segment of an eligible scroll, public data only:
  1) render the mesh into a 21-layer surface volume (vc_render_tifxyz, public CT), WITHOUT --flip-normals
  2) layer-order rule from geometry only (curvatura.py + ordem_camadas.py), written down BEFORE any model runs
  3) ink9 / Reader v2 / Reader V3 on the render, both layer orders (koine inference, as in the validation runs)
  4) segment.py report, with the order the rule chose
Usage: python demo_unlabelled.py MESH_DIR CT_URL OUT_DIR
  e.g. MESH_DIR = pacote_malhas/meshes/PHerc0800/z5664_w020
       CT_URL   = https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr
"""
import json, os, re, subprocess, sys
import numpy as np, tifffile, zarr

HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
H = os.path.expanduser('~/challenges/vesuvius'); I = f'{H}/inkcheck'; KO = f'{H}/villa_ink/ink-detection'
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
mesh, ct, out = os.path.abspath(sys.argv[1]), sys.argv[2].rstrip('/'), os.path.abspath(sys.argv[3])
os.makedirs(out, exist_ok=True); ren = f'{out}/render.zarr'


def run(cmd, **kw):
    print('$', ' '.join(cmd)[:200], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    return r.stdout


# 1) render
if not os.path.exists(f'{ren}/.zattrs') and not os.path.exists(f'{ren}/0'):
    cache = os.path.expanduser(f'~/challenges/vesuvius/ct_cache/{os.path.basename(ct.split("/volumes/")[0])}')
    os.makedirs(cache, exist_ok=True)   # vc_render_tifxyz needs --volume (local chunk cache) + --remote-url
    run(['vc_render_tifxyz', '--volume', cache, '--remote-url', ct, '--segmentation', mesh, '--group-idx', '0', '--scale', '1',
         '--num-slices', '21', '--slice-step', '1', '--cache-gb', '16', '--prefetch-remote', '--zarr-output', ren])
g = zarr.open(ren, mode='r'); a = g['0'] if not hasattr(g, 'shape') else g
print('render', a.shape, a.dtype, flush=True)

# 2) layer-order rule (same rule and thresholds as geometria.py, PREREG_ORDEM)
cu = run([PY, f'{I}/curvatura.py', mesh, '--D', '1000'])
fl = float(re.search(r'flecha media\s+([-+0-9.]+)vx', cu).group(1)); out_n = fl < 0; decide_c = abs(fl) >= 20
oc, oc_win = None, None
for w in (48, 32, 24):   # the validated runs used 48; small or holed meshes may have no fully valid 48x48 grid window
    r = subprocess.run([PY, f'{I}/ordem_camadas.py', mesh, ren, f'{ct}/0', '--win', str(w)], capture_output=True, text=True)
    if r.returncode == 0:
        oc, oc_win = r.stdout, w; break
    print(f'ordem_camadas --win {w}: no fully valid window ({r.stderr.strip().splitlines()[-1][:120]})', flush=True)
if oc is None:
    sys.exit('ordem_camadas found no valid window on this mesh')
b = float(re.search(r'inclinacao t por camada = ([-+0-9.]+)', oc).group(1))
cmed = float(np.median([float(x) for x in re.findall(r'->\s*t\s*[-+]\d+\s+\(([-0-9.]+)\)', oc)]))
decide_o = cmed >= 0.5 and abs(b) >= 0.5
grows_out = (b > 0) == out_n
pred = ('reverse' if grows_out else 'forward') if (decide_c and decide_o) else None
rule = {'sagitta_vx': fl, 'normal_points': 'out' if out_n else 'in', 'slope_layers': b, 'ct_match_median_corr': cmed,
        'layers_grow_towards': 'outside' if grows_out else 'inside', 'prediction': pred,
        'ordem_camadas_win': oc_win, 'note': 'validated runs used --win 48' if oc_win != 48 else ''}
json.dump(rule, open(f'{out}/order_rule.json', 'w', encoding='utf-8'), indent=1)
print('ORDER RULE (before any model):', rule, flush=True)
if pred is None:
    print('the rule abstains on this mesh (too flat or CT match too weak). Falling back to the triangle with no order '
          'fixed: whichever layer order gives 3 agreeing models is the one that reads ink.', flush=True)

# 3) models, both orders
N = a.shape[0]; ls = (N - 17) // 2
for m, ck in CK.items():
    if not (os.path.exists(f'{out}/{m}.tif') and os.path.exists(f'{out}/{m}_reverse.tif')):
        run(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', ren, ck, f'{out}/{m}.tif', '--model-type', 'auto',
             '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
             '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'], cwd=KO)

# 3b) rule abstained: let the unrestricted triangle pick the order (label-free)
sys.path.insert(0, HERE); import segment
if pred is None:
    maps = {**{f'{m}_f': f'{out}/{m}.tif' for m in CK}, **{f'{m}_r': f'{out}/{m}_reverse.tif' for m in CK}}
    tri = segment.run_triangle(maps, None, None)
    core = tri['core']; side = {c[-1] for c in core}
    pred = 'forward' if side == {'f'} and len(core) >= 3 else 'reverse' if side == {'r'} and len(core) >= 3 else None
    rule['triangle_fallback'] = {'core': core, 'verdict': tri['verdict'], 'order_from_triangle': pred}
    json.dump(rule, open(f'{out}/order_rule.json', 'w', encoding='utf-8'), indent=1)
    print('TRIANGLE FALLBACK (no order fixed): core', core, '->', pred, flush=True)
    if pred is None:
        sys.exit('no layer order gives 3 agreeing models: the kit cannot say this segment shows ink; stopping here')

# 4) report; pixel size from the mesh (grid step in voxels x voxel size / render px per grid point)
vox = float(re.search(r'([0-9.]+)um', ct).group(1))
P = np.stack([tifffile.imread(f'{mesh}/{c}.tif') for c in 'xyz'], -1).astype(np.float64); ok = (P > 0).all(-1)
step = float(np.median(np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]))
px = step * vox / (a.shape[2] / P.shape[1])
print(f'pixel {px:.2f} um -> window {round(2500 / px)} px', flush=True)
segment.run(out, list(CK), pred, None, None, px)
