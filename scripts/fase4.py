"""PREREG_V4: o triangulo pega um mapa que alucina NA ORDEM CERTA?
Usa os 6 segmentos do PHerc1667 (fase3/, ordem prevista forward). Os 3 mapas bons ja existem (ink9_f rv2_f rv3_f).
Sondas novas (nenhuma usa rotulo para ser criada):
  cego_letras : ink9_r (cego) + letras falsas plantadas dentro da mascara (area ~ area de ink9_f > 0.5)
  parcial     : ink9_f + letras falsas plantadas dentro da mascara (area ~ 30% da area de ink9_f > 0.5)
  embaralhado : ink9 forward rodado numa pilha com as camadas em ordem aleatoria (so w028 w029 w031, menores)
Letras: 2-4 tracos (retas e arcos), altura 40*f px e traco 6*f px, f = downsample que o triangulo usa
(sqrt(area valida / 1e6)), para cair na banda 2-20 px da analise. Semente fixa por segmento.
Etapas: 1) cria sondas  2) triangulo --core-from ink9_f rv2_f rv3_f (SEM rotulo)  3) so depois AUC das sondas.
uso: python -u fase4.py
"""
import os, sys, json, subprocess, zlib
import numpy as np, zarr, tifffile

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; F3 = f'{I}/fase3'; OUT = f'{I}/fase4'; KO = f'{H}/villa_ink/ink-detection'
PY = sys.executable
CK9 = f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth'
SEGS = ['pherc1667-w013', 'pherc1667-w018', 'pherc1667-w023', 'pherc1667-w028', 'pherc1667-w029', 'pherc1667-w031']
SHUF = {'pherc1667-w028', 'pherc1667-w029', 'pherc1667-w031'}
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, I)
import inkcheck as ik
from scipy.ndimage import binary_dilation


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:5]), r.stderr[-1500:]); sys.exit(1)
    return r.stdout


def glyph(rng, h, sw):
    """uma letra falsa: 2-4 tracos (retas/arcos) numa caixa h x 0.7h, traco de largura sw"""
    w = int(0.7 * h); c = np.zeros((h + 2 * sw, w + 2 * sw), bool)
    for _ in range(rng.integers(2, 5)):
        if rng.random() < 0.6:
            (y0, x0), (y1, x1) = rng.random(2) * [h, w], rng.random(2) * [h, w]
            t = np.linspace(0, 1, 4 * h); ys, xs = y0 + (y1 - y0) * t, x0 + (x1 - x0) * t
        else:
            cy, cx = rng.random(2) * [h, w]; r = (0.2 + 0.3 * rng.random()) * h
            a0 = rng.random() * 2 * np.pi; a = a0 + np.linspace(0, (0.8 + rng.random()) * np.pi, 4 * h)
            ys, xs = cy + r * np.sin(a), cx + r * np.cos(a)
        ys = np.clip(ys, 0, h - 1).astype(int) + sw; xs = np.clip(xs, 0, w - 1).astype(int) + sw
        c[ys, xs] = True
    yy, xx = np.mgrid[-sw // 2:sw // 2 + 1, -sw // 2:sw // 2 + 1]
    return binary_dilation(c, structure=(yy ** 2 + xx ** 2) <= (sw / 2) ** 2)


def plant(base, mask, target_px, f, seed):
    rng = np.random.default_rng(seed); out = base.copy(); h, sw = 40 * f, max(2, 6 * f)
    ys, xs = np.nonzero(mask[::8, ::8]); ys, xs = ys * 8, xs * 8
    done = 0; tries = 0
    while done < target_px and tries < 20000:
        tries += 1; k = rng.integers(len(ys)); y, x = ys[k], xs[k]
        g = glyph(rng, h, sw); gh, gw = g.shape
        if y + gh >= base.shape[0] or x + gw >= base.shape[1] or mask[y:y + gh, x:x + gw].mean() < 0.9:
            continue
        out[y:y + gh, x:x + gw][g] = 0.9
        done += int(g.sum())
    return out, done


res = {}
for seg in SEGS:
    d3, o = f'{F3}/{seg}', f'{OUT}/{seg}'; os.makedirs(o, exist_ok=True)
    mask = np.load(f'{d3}/mask.npy') > 0
    f = max(1, int(np.sqrt(mask.sum() / 1_000_000)))
    seed = zlib.crc32(seg.encode())
    good = ik.load(f'{d3}/ink9.tif'); area = int(((good > 0.5) & mask).sum())
    if not os.path.exists(f'{o}/cego_letras.npy'):
        blind = ik.load(f'{d3}/ink9_reverse.tif')
        p, n = plant(blind, mask, area, f, seed); np.save(f'{o}/cego_letras.npy', p.astype(np.float32))
        p2, n2 = plant(good, mask, int(0.3 * area), f, seed + 1); np.save(f'{o}/parcial.npy', p2.astype(np.float32))
        print(f'{seg}: f={f} area ink9_f>0.5 = {area} px; plantado cego {n} px, parcial {n2} px', flush=True)
    del good
    if seg in SHUF and not os.path.exists(f'{o}/embaralhado.tif'):
        ren = [l.split('\t')[1] for l in open(f'{I}/geometria_1667.tsv') if l.startswith(seg)][0]
        g = zarr.open(ren, mode='r'); a = g['0'] if not hasattr(g, 'shape') else g
        perm = np.random.default_rng(seed).permutation(a.shape[0])
        z = zarr.open_group(f'{o}/emb.zarr', mode='w')
        b = z.create_dataset('0', shape=a.shape, chunks=(a.shape[0], 128, 128), dtype=a.dtype, dimension_separator='/')
        for k, pk in enumerate(perm):
            b[k] = a[int(pk)]
        try:
            z.attrs.update(g.attrs.asdict())
        except Exception:
            pass
        N = a.shape[0]; ls = (N - 17) // 2
        sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', f'{o}/emb.zarr', CK9, f'{o}/embaralhado.tif',
            '--model-type', 'auto', '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17),
            '--overlap', '0.50', '--blend-mode', 'hann', '--direction', 'forward', '--batch-size', '4',
            '--num-workers', '4', '--no-compile'], cwd=KO)
        print(f'{seg}: embaralhado pronto (permutacao {perm.tolist()})', flush=True)
    maps = {'ink9_f': f'{d3}/ink9.tif', 'rv2_f': f'{d3}/rv2.tif', 'rv3_f': f'{d3}/rv3.tif',
            'cego_letras': f'{o}/cego_letras.npy', 'parcial': f'{o}/parcial.npy'}
    if os.path.exists(f'{o}/embaralhado.tif'):
        maps['embaralhado'] = f'{o}/embaralhado.tif'
    tri = json.loads(sh([PY, f'{I}/inkcheck.py', 'triangle'] + [f'{k}={v}' for k, v in maps.items()] +
                        ['--mask', f'{d3}/mask.npy', '--n', '300', '--min-ratio', '2.0', '--core-from', 'ink9_f', 'rv2_f', 'rv3_f'], cwd=I))
    json.dump(tri, open(f'{o}/triangulo.json', 'w'), indent=1)
    print(f'\n== {seg}  core {tri["core"]}', flush=True)
    for k, v in tri['verdict'].items():
        print(f'   {k:12s} {v}', flush=True)
    res[seg] = {'maps': maps, 'verdict': tri['verdict']}

print('\n######## SO AGORA OS ROTULOS ########', flush=True)
H1 = []
for seg in SEGS:
    d3 = f'{F3}/{seg}'; v = res[seg]['verdict']; auc = {}
    for k in ('cego_letras', 'parcial', 'embaralhado'):
        if k in res[seg]['maps']:
            auc[k] = json.loads(sh([PY, f'{I}/inkcheck.py', 'label', res[seg]['maps'][k], f'{d3}/ink.npy',
                                    '--mask', f'{d3}/mask.npy', '--n', '200'], cwd=I))['auc']
    core_ok = all(v[m] == 'consistent' for m in ('ink9_f', 'rv2_f', 'rv3_f'))
    probes_ok = all(v[k].startswith(('suspect', 'isolated')) for k in ('cego_letras', 'embaralhado') if k in auc and auc[k] < 0.60)
    H1.append(core_ok and probes_ok)
    res[seg]['auc'] = auc
    print(f'{seg:16s} ' + '  '.join(f'{k} AUC {auc[k]:.3f} -> {v[k].split(" ")[0]}' for k in auc) +
          f'   nucleo {"ok" if core_ok else "NAO"}', flush=True)
print(f'\nH1 (cego/embaralhado com AUC<0.60 marcados, nucleo intacto): {sum(H1)}/{len(H1)} -> {"PASS" if all(H1) else "FAIL"}')
print('H2 (parcial, previsto "consistent" = limite do triangulo por mapa inteiro): ' +
      ', '.join(f'{s.split("-")[1]} {res[s]["verdict"]["parcial"].split(" ")[0]}' for s in SEGS))
json.dump(res, open(f'{OUT}/resultado.json', 'w'), indent=1)
