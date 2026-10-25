"""PREREG_ESTRESSE: o kit continua honesto quando os mapas sao fracos (como num rolo novo)?
Degrada o RENDER de entrada com ruido gaussiano (sigma = nivel x desvio padrao do render nos voxels mapeados, zeros
continuam zero), roda os 3 modelos nas duas ordens (koine, como no fase5) e aplica o kit.
Segmentos: os 3 do PHercParis4 com o menor render (H x W), regra fixa aqui. Niveis: 0.5 e 1.0.
  1) render ruidoso -> ink9 / rv2 / rv3, forward e reverse                         (sem rotulo)
  2) triangulo com --core-from na ordem prevista (forward)                          (sem rotulo)
  3) check por janela v12 nos mapas da ordem prevista (piso = mesmo modelo na ordem errada)  (sem rotulo)
  4) letras falsas no rv2 ruidoso previsto (mesma funcao e semente do fase5) e check v12   (sem rotulo)
  5) so agora: AUC de todos os mapas; separacao pura/mista; alucinacao natural x tinta real
uso: python -u fase8.py
"""
import os, sys, json, subprocess, glob, zlib
import numpy as np, zarr
H_ = os.path.expanduser('~/challenges/vesuvius')
I = f'{H_}/inkcheck'; KO = f'{H_}/villa_ink/ink-detection'; PY = sys.executable; IK = f'{I}/inkcheck_v12.py'
CK = {'ink9': f'{H_}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H_}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H_}/reader_v3/reader-v3.pth'}
M = tuple(CK); OUT = f'{I}/fase8'; os.makedirs(OUT, exist_ok=True)
LEVELS = (0.5, 1.0); NSEG = 3
LETTER_MM, STROKE_MM, WIN_MM, FAKE_FRAC = 2.5, 0.2, 2.5, 0.02
V12 = ['--score', 'both', '--null', 'swap', '--n', '19', '--min-null', '10', '--tol-px', '6', '--ink-rel', '0.5',
       '--min-ink', '0.005', '--u-k', '3.0', '--u-min', '0.20', '--stroke', 'floor', '--floor-k', '2.0']
sys.path.insert(0, I)
import inkcheck_v12 as ik
from scipy.ndimage import uniform_filter, binary_dilation, gaussian_filter
src = open(f'{I}/fase5.py').read()
exec(src[src.index('def glyph'):src.index('def local')])   # glyph() e plant() identicos ao fase5


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:5]), r.stderr[-1500:]); sys.exit(1)
    return r.stdout


def noisy_render(ren, out, level, seed):
    if os.path.exists(f'{out}/.done'):
        return
    a = arr(ren); N = a.shape[0]
    mid = np.asarray(a[N // 2]).astype(np.float32); sd = float(mid[mid > 0].std())
    g = zarr.open_group(out, mode='w'); z = g.create_dataset('0', shape=a.shape, chunks=a.chunks, dtype=a.dtype)
    rng = np.random.default_rng(seed); top = np.iinfo(a.dtype).max if np.issubdtype(a.dtype, np.integer) else None
    for k in range(N):
        x = np.asarray(a[k]).astype(np.float32); m = x > 0
        y = x + rng.standard_normal(x.shape).astype(np.float32) * (level * sd)
        y = np.where(m, np.clip(y, 1 if top else y.min(), top if top else y.max()), 0)
        z[k] = y.astype(a.dtype)
    open(f'{out}/.done', 'w').write(f'level {level} sigma {level * sd:.3f} (render sd {sd:.3f})\n')


res5 = json.load(open(f'{I}/fase5/resultado.json'))
rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/geometria_paris4.tsv')][1:]
segs = sorted([(r[0], r[1]) for r in rows if r[5] == 'forward'], key=lambda s: int(np.prod(arr(s[1]).shape[1:])))[:NSEG]
print('segmentos (menor render):', [s for s, _ in segs], flush=True)
for seg, ren in segs:
    for lv in LEVELS:
        o = f'{OUT}/{seg}/L{lv}'; os.makedirs(o, exist_ok=True); src5 = f'{I}/fase5/{seg}'
        nr = f'{OUT}/{seg}/render_L{lv}.zarr'; noisy_render(ren, nr, lv, zlib.crc32(f'{seg}{lv}'.encode()))
        N = arr(nr).shape[0]; ls = (N - 17) // 2
        for m, ck in CK.items():
            if not (os.path.exists(f'{o}/{m}.tif') and os.path.exists(f'{o}/{m}_reverse.tif')):
                sh(['uv', 'run', 'python', '-m', 'koine_machines.inference.infer', nr, ck, f'{o}/{m}.tif', '--model-type', 'auto',
                    '--resolution', '0', '--layer-start', str(ls), '--layer-end', str(ls + 17), '--overlap', '0.50',
                    '--blend-mode', 'hann', '--direction', 'both', '--batch-size', '4', '--num-workers', '4', '--no-compile'], cwd=KO)
        mask = f'{src5}/mask.npy'; win = int(res5[seg]['win_px'])
        maps = {**{f'{m}_f': f'{o}/{m}.tif' for m in M}, **{f'{m}_r': f'{o}/{m}_reverse.tif' for m in M}}
        tri = json.loads(sh([PY, IK, 'triangle'] + [f'{k}={v}' for k, v in maps.items()] +
                            ['--mask', mask, '--n', '300', '--min-ratio', '2.0', '--core-from'] + [f'{m}_f' for m in M], cwd=I))
        json.dump(tri, open(f'{o}/triangulo.json', 'w'), indent=1)
        print(f'\n== {seg} nivel {lv}: {open(nr + "/.done").read().strip()} | core {tri["core"]}', flush=True)
        for k, v in tri['verdict'].items():
            print(f'   {k:7s} {v}', flush=True)
        for m in M:
            j = json.loads(sh([PY, IK, 'local', f'{o}/{m}.tif', *[f'{o}/{q}.tif' for q in M if q != m], '--mask', mask,
                               '--win', str(win), '--floor', f'{o}/{m}_reverse.tif', '--out-npz', f'{o}/local_{m}.npz'] + V12, cwd=I))
            print(f'   local {m}: julgadas {j["judged"]}  nao-conf {j["unsupported"]}  sem-nulo {j["no_null_windows"]}', flush=True)
        if not os.path.exists(f'{o}/rv2_falsas.npy'):
            mk = np.load(mask) > 0
            fk, fm, h, sw, hi = plant(ik.load(f'{o}/rv2.tif'), mk, res5[seg]['px_um'], zlib.crc32(seg.encode()))
            np.save(f'{o}/rv2_falsas.npy', fk); np.save(f'{o}/fake_mask.npy', fm)
        j = json.loads(sh([PY, IK, 'local', f'{o}/rv2_falsas.npy', *[f'{o}/{q}.tif' for q in M if q != 'rv2'], '--mask', mask,
                           '--win', str(win), '--floor', f'{o}/rv2_reverse.tif', '--out-npz', f'{o}/local_rv2_falsas.npz'] + V12, cwd=I))
        print(f'   rv2+falsas: julgadas {j["judged"]}  nao-conf {j["unsupported"]}', flush=True)

print('\n######## SO AGORA OS ROTULOS ########', flush=True)
S = {lv: dict(fa_u=0, fa_j=0, pu=0, pn=0, mu=0, mn=0, nu=0, nn=0, ru=0, rn=0, tri_bad=0, tri_ok=0, tri_unres=0, auc=[]) for lv in LEVELS}
for seg, ren in segs:
    src5 = f'{I}/fase5/{seg}'; ink = f'{src5}/ink.npy'
    for lv in LEVELS:
        o = f'{OUT}/{seg}/L{lv}'; t = S[lv]
        auc = {f'{m}_{d}': json.loads(sh([PY, IK, 'label', f'{o}/{m}{"" if d == "f" else "_reverse"}.tif', ink, '--mask', f'{src5}/mask.npy',
                                          '--n', '200'], cwd=I))['auc'] for m in M for d in 'fr'}
        t['auc'].append(auc)
        v = json.load(open(f'{o}/triangulo.json'))['verdict']; core = json.load(open(f'{o}/triangulo.json'))['core']
        wrong_conf = [k for k in v if k.endswith('_r') and v[k] == 'consistent'] + [k for k in core if k.endswith('_r')]
        if wrong_conf:
            t['tri_bad'] += 1
        elif not core:
            t['tri_unres'] += 1
        else:
            t['tri_ok'] += 1
        for m in M:
            d = np.load(f'{o}/local_{m}.npz'); st = d['state']; t['fa_j'] += int((st > 0).sum()); t['fa_u'] += int((st == 2).sum())
            W = int(d['win_px'])
            fi = uniform_filter((np.load(ink) > 0).astype(np.float32), W, mode='constant')[np.ix_(np.minimum(d['cy'], np.load(ink).shape[0] - 1), np.minimum(d['cx'], np.load(ink).shape[1] - 1))]
            nat, real = (st > 0) & (fi < 0.005), (st > 0) & (fi >= 0.05)
            t['nu'] += int((nat & (st == 2)).sum()); t['nn'] += int(nat.sum()); t['ru'] += int((real & (st == 2)).sum()); t['rn'] += int(real.sum())
        d = np.load(f'{o}/local_rv2_falsas.npz'); st = d['state']; W = int(d['win_px'])
        def at(img):
            a = np.load(img) > 0; f = uniform_filter(a.astype(np.float32), W, mode='constant')
            return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]
        ff, fi = at(f'{o}/fake_mask.npy'), at(ink)
        pure, mixed = (ff > 0.02) & (fi < 0.01), (ff > 0.02) & (fi >= 0.02)
        t['pu'] += int((pure & (st == 2)).sum()); t['pn'] += int((pure & (st > 0)).sum())
        t['mu'] += int((mixed & (st == 2)).sum()); t['mn'] += int((mixed & (st > 0)).sum())
        print(f'{seg} nivel {lv}: ' + '  '.join(f'{k} {a:.3f}' for k, a in auc.items()) + f' | core {core}', flush=True)

s1 = all(S[lv]['tri_bad'] == 0 for lv in LEVELS)
print(f'\nS1 triangulo nunca da confianca falsa (nenhum mapa da ordem errada no nucleo ou "consistent"), todos os niveis: '
      f'{"PASS" if s1 else "FAIL"}')
for lv in LEVELS:
    t = S[lv]; fa = t['fa_u'] / max(t['fa_j'], 1)
    am = {k: np.mean([a[k] for a in t['auc']]) for k in t['auc'][0]}
    print(f'\n== nivel {lv}: AUC medio ' + '  '.join(f'{k} {v:.3f}' for k, v in am.items()))
    print(f'   triangulo: correto {t["tri_ok"]}  sem decisao {t["tri_unres"]}  confianca falsa {t["tri_bad"]}')
    print(f'   S2 falso alarme v12 nos mapas previstos: {t["fa_u"]}/{t["fa_j"]} = {fa:.3f} (criterio <= 0.10) -> {"PASS" if fa <= 0.10 else "FAIL"}')
    print(f'   (informativo) letras falsas puras {t["pu"]}/{t["pn"]}  mistas {t["mu"]}/{t["mn"]}; '
          f'alucinacao natural {t["nu"]}/{t["nn"]} x tinta real {t["ru"]}/{t["rn"]}')
