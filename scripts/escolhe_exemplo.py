"""Pick the mesh for the README's real example (a usage example, not evidence). The rule, written before looking:
  - meshes of the public package judged 'aprova' in data/index.csv, PHerc0800 left out (already shown);
  - for each, the published ink_9um maps in both layer orders (mapas_up/<scroll>/<z_w>.tif and _reverse.tif);
  - order dependence = stroke energy (std of the 2-20 px band, 4x downsampled, on pixels valid in both) of the
    stronger order / the weaker one; the mesh with the highest value is the example.
It uses one model only and never decides the layer order: the demo does that from geometry afterwards.
uso: python escolhe_exemplo.py
"""
import csv, json, os, sys
import numpy as np, tifffile

H = os.path.expanduser('~/challenges/vesuvius')
sys.path.insert(0, f'{H}/ink-or-hallucination')
import inkcheck as ik

P = f'{H}/pacote_malhas'; M = f'{H}/mapas_up'


def dn(a, f=4):
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    return a[:h, :w].reshape(h // f, f, w // f, f).mean((1, 3))


rows = []
for r in csv.DictReader(open(f'{P}/data/index.csv')):
    if r['gate_verdict'] != 'aprova' or r['scroll'] == 'PHerc0800':
        continue
    stem = os.path.basename(r['path']); a_p, b_p = f'{M}/{r["scroll"]}/{stem}.tif', f'{M}/{r["scroll"]}/{stem}_reverse.tif'
    if not (os.path.exists(a_p) and os.path.exists(b_p)):
        print(f'   no maps: {r["scroll"]} {stem}', flush=True); continue
    A, B = (dn(tifffile.imread(p).astype(np.float32)) for p in (a_p, b_p))
    v = (A > 0) & (B > 0)
    if v.sum() < 10000:
        continue
    eA, eB = (float(ik.band(x, v, 2, 20)[v].std()) for x in (A, B))
    ratio = max(eA, eB) / max(min(eA, eB), 1e-9)
    rows.append({'scroll': r['scroll'], 'mesh': stem, 'path': r['path'], 'area_cm2': float(r['area_cm2']),
                 'energy_file': eA, 'energy_file_reverse': eB, 'ratio': ratio,
                 'stronger': 'file' if eA > eB else 'file_reverse'})
    print(f'{r["scroll"]} {stem:16s} area {float(r["area_cm2"]):5.2f} cm2   ratio {ratio:.2f}', flush=True)

rows.sort(key=lambda x: -x['ratio'])
print('\ntop 5:')
for x in rows[:5]:
    print(f'   {x["scroll"]} {x["mesh"]:16s} ratio {x["ratio"]:.2f}  area {x["area_cm2"]:.2f} cm2  ({x["stronger"]} stronger)')
json.dump({'rule': __doc__, 'n': len(rows), 'ranked': rows}, open(f'{H}/escolha_exemplo.json', 'w'), indent=1)
print(f'\n{len(rows)} meshes scored -> example: {rows[0]["scroll"]} {rows[0]["mesh"]}  ({H}/escolha_exemplo.json)')
