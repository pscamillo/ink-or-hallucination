"""Fase 2 do PREREG_ORDEM (sha256 ea2d3b10...). Le geometria.tsv (previsoes ja gravadas).
Por segmento com previsao:
  1) ink9, Reader v2, Reader V3 nas duas ordens (koine, janela de 17 centrada)
  2) triangulo com --core-from = mapas na ordem prevista  (SEM rotulo)
  3) so depois: AUC de cada mapa contra o rotulo (max das fatias do zarr; mascara = supervision mask)
  4) P1 e P2 avaliados exatamente como no prereg.
uso: python fase2.py   (log em fase2/)
"""
import os, sys, json, subprocess, glob
import numpy as np, zarr

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; LAB = f'{H}/villa_ink/ink-detection/labels_hf'; KO = f'{H}/villa_ink/ink-detection'
PY = sys.executable
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
OUT = f'{I}/fase2'; os.makedirs(OUT, exist_ok=True)


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:4]), r.stderr[-800:]); sys.exit(1)
    return r.stdout


rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/geometria.tsv')][1:]
segs = [(r[0], r[1], r[5]) for r in rows if r[5] in ('forward', 'reverse')]
print('segmentos com previsao:', [(s, p) for s, _, p in segs])
print('sem previsao:', [r[0] for r in rows if r[5] not in ('forward', 'reverse')])
res = {}
for seg, ren, pred in segs:
    o = f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True)
    N = arr(ren).shape[0]; ls = (N - 17) // 2
    for m, ck in CK.items():
        if os.path.exists(f'{o}/{m}.tif') and os.path.exists(f'{o}/{m}_reverse.tif'):
            continue
        sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', ren, ck, f'{o}/{m}.tif', '--model-type', 'auto',
            '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
            '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'], cwd=KO)
    maps = {}
    for m in CK:
        maps[f'{m}_f'] = f'{o}/{m}.tif'; maps[f'{m}_r'] = f'{o}/{m}_reverse.tif'
    suf = '_f' if pred == 'forward' else '_r'
    core_from = [f'{m}{suf}' for m in CK]
    # mascara (nao e rotulo de tinta): supervision mask
    if not os.path.exists(f'{o}/mask.npy'):
        sm = glob.glob(f'{LAB}/{seg}/*supervision_mask.zarr')[0]
        np.save(f'{o}/mask.npy', (np.asarray(arr(sm)).max(0) > 0).astype(np.uint8) * 255)
    tri = json.loads(sh([PY, f'{I}/inkcheck.py', 'triangle'] + [f'{k}={v}' for k, v in maps.items()] +
                        ['--mask', f'{o}/mask.npy', '--n', '300', '--min-ratio', '2.0', '--core-from'] + core_from, cwd=I))
    json.dump(tri, open(f'{o}/triangulo.json', 'w'), indent=1)
    print(f'\n== {seg}  previsao {pred}  core {tri["core"]}')
    for k, v in tri['verdict'].items():
        print(f'   {k:7s} {v}')
    res[seg] = {'pred': pred, 'verdict': tri['verdict'], 'core_from': core_from}

print('\n######## SO AGORA OS ROTULOS ########')
P1_pairs = []; P1_allwrong = []; P2 = []
for seg, ren, pred in segs:
    o = f'{OUT}/{seg}'
    if not os.path.exists(f'{o}/ink.npy'):
        lz = glob.glob(f'{LAB}/{seg}/*inklabels.zarr')[0]
        np.save(f'{o}/ink.npy', (np.asarray(arr(lz)).max(0) > 0).astype(np.uint8) * 255)
    auc = {}
    for k in res[seg]['verdict']:
        m, d = k.rsplit('_', 1)
        p = f'{o}/{m}.tif' if d == 'f' else f'{o}/{m}_reverse.tif'
        auc[k] = json.loads(sh([PY, f'{I}/inkcheck.py', 'label', p, f'{o}/ink.npy', '--mask', f'{o}/mask.npy', '--n', '200'], cwd=I))['auc']
    res[seg]['auc'] = auc
    suf, oth = ('f', 'r') if pred == 'forward' else ('r', 'f')
    contra = 0
    for m in CK:
        a_p, a_o = auc[f'{m}_{suf}'], auc[f'{m}_{oth}']
        if abs(a_p - a_o) >= 0.05:
            P1_pairs.append(a_p > a_o)
        contra += a_p < a_o
    P1_allwrong.append(contra == 3)
    # P2
    v = res[seg]['verdict']
    if all(auc[f'{m}_{suf}'] >= 0.70 for m in CK):
        ok = all(v[f'{m}_{suf}'] == 'consistent' for m in CK) and \
             all(v[k].startswith(('suspect', 'isolated')) for k in auc if auc[k] < 0.60)
        P2.append(ok)
    print(f'{seg:18s} prev {pred:8s} ' + '  '.join(f'{k} {auc[k]:.3f}' for k in auc))

p1 = (np.mean(P1_pairs) >= 0.90 if P1_pairs else False) and not any(P1_allwrong)
print(f'\nP1: {sum(P1_pairs)}/{len(P1_pairs)} pares (|dAUC|>=0.05) com a ordem prevista melhor; '
      f'segmentos com os 3 modelos contra: {sum(P1_allwrong)}  ->  {"PASS" if p1 else "FAIL"}')
print(f'P2: {sum(P2)}/{len(P2)} segmentos elegiveis corretos  ->  {"PASS" if P2 and all(P2) else "FAIL" if P2 else "sem segmento elegivel"}')
print(f'cobertura: {len(segs)}/{len(rows)} segmentos com previsao (geometria.tsv)')
json.dump(res, open(f'{OUT}/resultado.json', 'w'), indent=1)
