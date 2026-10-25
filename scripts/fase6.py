"""PREREG_V11: check por janela v11 (nulo por troca de janelas) em mapas ja calculados, sem rodar modelo.
Conjunto A (teste): os 12 segmentos de fase2/ (PHerc0139 w035 w039 w040 w041 w043, PHerc0814 46527) e fase3/
(PHerc1667 w013 w018 w023 w028 w029 w031), ordem prevista forward em todos (geometria.tsv, geometria_1667.tsv).
Conjunto B (texto denso): os 8 segmentos do PHercParis4 de fase5/ (so roda se fase5/resultado.json existir).
  1) cada mapa da ordem prevista (ink9, rv2, rv3) contra os outros dois                (sem rotulo)
  2) cada mapa da ordem ERRADA contra os dois outros da ordem prevista (informativo)    (sem rotulo)
  3) letras falsas (2.5 mm, traco 0.2 mm, 2% da mascara, intensidade p99.5 do proprio mapa) no rv2 previsto
     (mesma funcao e semente do fase5; no Paris4 reusa o rv2_falsas.npy ja gravado)     (sem rotulo)
  4) so agora: rotulo de tinta, usado SO para separar janelas puras (falsa sem tinta real) e mistas
Usa inkcheck_v11.py (nunca o inkcheck.py). Grava em fase6/<conjunto>/<segmento>/.
uso: python -u fase6.py
"""
import os, sys, json, subprocess, zlib
import numpy as np, zarr, tifffile

H = os.path.expanduser('~/challenges/vesuvius')
I = f'{H}/inkcheck'; PY = sys.executable; IK = f'{I}/inkcheck_v11.py'
OUT = f'{I}/fase6'
LETTER_MM, STROKE_MM, WIN_MM, FAKE_FRAC = 2.5, 0.2, 2.5, 0.02
M = ('ink9', 'rv2', 'rv3')
sys.path.insert(0, I)
import inkcheck_v11 as ik
from scipy.ndimage import uniform_filter, binary_dilation, gaussian_filter   # usados por glyph()/plant() do fase5
src = open(f'{I}/fase5.py').read()
exec(src[src.index('def glyph'):src.index('def local')])   # glyph() e plant() identicos ao fase5


def arr(p):
    g = zarr.open(p, mode='r'); return g['0'] if not hasattr(g, 'shape') else g


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=I)
    if r.returncode:
        print('ERRO', ' '.join(cmd[:5]), r.stderr[-1500:]); sys.exit(1)
    return r.stdout


def um_per_px(mesh, vox_um, ren_shape):
    x, y, z = (tifffile.imread(f'{mesh}/{c}.tif') for c in 'xyz')
    P = np.stack([x, y, z], -1).astype(np.float64); ok = (P > 0).all(-1)
    d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[ok[:, 1:] & ok[:, :-1]]
    return float(np.median(d)) * vox_um / (ren_shape[2] / x.shape[1])


def local(target, others, mask, win, out):
    return json.loads(sh([PY, IK, 'local', target, *others, '--mask', mask, '--win', str(win), '--energy-k', '1.25',
                          '--score', 'corr', '--null', 'swap', '--n', '19', '--min-null', '10', '--out-npz', out]))


def segs_from(tsv, src_dir, mesh_dir, vox_um):
    rows = [l.rstrip('\n').split('\t') for l in open(f'{I}/{tsv}')][1:]
    return [(r[0], r[1], r[5], f'{I}/{src_dir}/{r[0]}', f'{I}/{mesh_dir}/{r[0]}', vox_um) for r in rows if r[5] in ('forward', 'reverse')]


SETS = {'A': segs_from('geometria.tsv', 'fase2', 'malhas', 9.362) + segs_from('geometria_1667.tsv', 'fase3', 'malhas_1667/raw', 2.4)}
if os.path.exists(f'{I}/fase5/resultado.json'):
    SETS['B'] = segs_from('geometria_paris4.tsv', 'fase5', 'malhas_paris4/raw', 2.4)
else:
    print('fase5 ainda sem resultado.json: conjunto B (Paris4) fica de fora desta rodada', flush=True)

if '--dry' in sys.argv:   # so confere arquivos e tamanho do pixel; nao roda check, nao le rotulo
    for S, segs in SETS.items():
        for seg, ren, pred, src_d, mesh, vox in segs:
            falta = [p for p in [f'{src_d}/{m}{s}.tif' for m in M for s in ('', '_reverse')] + [f'{src_d}/mask.npy', f'{mesh}/x.tif']
                     if not os.path.exists(p)]
            px = um_per_px(mesh, vox, arr(ren).shape) if not falta else float('nan')
            print(f'[{S}] {seg:16s} prev {pred:8s} pixel {px:5.2f} um  janela {int(round(WIN_MM * 1000 / px)) if px == px else -1:4d} px'
                  f'  {"OK" if not falta else "FALTA " + str(falta)}')
    sys.exit(0)

res = {}
for S, segs in SETS.items():
    for seg, ren, pred, src_d, mesh, vox in segs:
        o = f'{OUT}/{S}/{seg}'; os.makedirs(o, exist_ok=True)
        suf, oth = ('', '_reverse') if pred == 'forward' else ('_reverse', '')
        good = {m: f'{src_d}/{m}{suf}.tif' for m in M}; bad = {m: f'{src_d}/{m}{oth}.tif' for m in M}
        mask = f'{src_d}/mask.npy'
        px = um_per_px(mesh, vox, arr(ren).shape)
        if not 5 <= px <= 15:
            print(f'ERRO {seg}: pixel {px:.2f} um fora de 5-15 um; parar'); sys.exit(1)
        win = int(round(WIN_MM * 1000 / px))
        print(f'\n== [{S}] {seg}  prev {pred}  pixel {px:.2f} um  janela {win} px', flush=True)
        r = {'set': S, 'px_um': px, 'win_px': win, 'good': {}, 'bad': {}}
        for m in M:
            j = local(good[m], [good[q] for q in M if q != m], mask, win, f'{o}/local_{m}.npz')
            r['good'][m] = j
            print(f'   {m} previsto: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d}  sem-nulo {j["no_null_windows"]}', flush=True)
        for m in M:
            j = local(bad[m], [good[q] for q in M if q != m], mask, win, f'{o}/local_{m}_errado.npz')
            r['bad'][m] = j
            print(f'   {m} ordem errada: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d}  sem-nulo {j["no_null_windows"]}', flush=True)
        if S == 'B':
            fk_p, fm_p = f'{src_d}/rv2_falsas.npy', f'{src_d}/fake_mask.npy'
        else:
            fk_p, fm_p = f'{o}/rv2_falsas.npy', f'{o}/fake_mask.npy'
            if not os.path.exists(fk_p):
                mk = np.load(mask) > 0
                fk, fm, h, sw, hi = plant(ik.load(good['rv2']), mk, px, zlib.crc32(seg.encode()))
                np.save(fk_p, fk); np.save(fm_p, fm)
                print(f'   letras falsas: altura {h} px, traco {sw} px, intensidade {hi:.3f}, {fm.sum()} px', flush=True)
        j = local(fk_p, [good[q] for q in M if q != 'rv2'], mask, win, f'{o}/local_rv2_falsas.npz')
        r['fake'] = j; r['fake_mask'] = fm_p; r['src'] = src_d
        print(f'   rv2+falsas: julgadas {j["judged"]:3d}  nao-conf {j["unsupported"]:3d}  sem-nulo {j["no_null_windows"]}', flush=True)
        res[(S, seg)] = r

print('\n######## SO AGORA OS ROTULOS (so para separar janelas puras e mistas) ########', flush=True)
tot = {}
for (S, seg), r in res.items():
    t = tot.setdefault(S, dict(j=0, u=0, nn=0, cand=0, bj=0, bu=0, pu=0, pn=0, mu=0, mn=0, ok_fk=0, ok_fn=0))
    o = f'{OUT}/{S}/{seg}'
    for m in M:
        d = np.load(f'{o}/local_{m}.npz'); st = d['state']
        t['j'] += int((st > 0).sum()); t['u'] += int((st == 2).sum()); t['nn'] += int(d['no_null'].sum())
        t['cand'] += int((st > 0).sum() + d['no_null'].sum())
        st = np.load(f'{o}/local_{m}_errado.npz')['state']; t['bj'] += int((st > 0).sum()); t['bu'] += int((st == 2).sum())
    d = np.load(f'{o}/local_rv2_falsas.npz'); st = d['state']; W = int(d['win_px'])
    def at(img):
        a = np.load(img) > 0
        f = uniform_filter(a.astype(np.float32), W, mode='constant')
        return f[np.ix_(np.minimum(d['cy'], a.shape[0] - 1), np.minimum(d['cx'], a.shape[1] - 1))]
    ff, fi = at(r['fake_mask']), at(f'{r["src"]}/ink.npy')
    pure, mixed, clean = (ff > 0.02) & (fi < 0.01), (ff > 0.02) & (fi >= 0.02), ff == 0
    t['pu'] += int((pure & (st == 2)).sum()); t['pn'] += int((pure & (st > 0)).sum())
    t['mu'] += int((mixed & (st == 2)).sum()); t['mn'] += int((mixed & (st > 0)).sum())
    t['ok_fk'] += int((clean & (st == 2)).sum()); t['ok_fn'] += int((clean & (st > 0)).sum())
    print(f'[{S}] {seg:16s} falsas puras {int((pure & (st == 2)).sum())}/{int((pure & (st > 0)).sum())}'
          f'  mistas {int((mixed & (st == 2)).sum())}/{int((mixed & (st > 0)).sum())}', flush=True)

for S, t in tot.items():
    fa = t['u'] / max(t['j'], 1); nn = t['nn'] / max(t['cand'], 1); det = t['pu'] / max(t['pn'], 1)
    tag = 'P' if S == 'A' else 'P4'
    print(f'\n== conjunto {S}')
    print(f'{tag}1 falso alarme, mapas da ordem prevista: {t["u"]}/{t["j"]} = {fa:.3f} (criterio <= 0.10) -> {"PASS" if fa <= 0.10 else "FAIL"}')
    print(f'{tag}2 janelas com traco e sem nulo: {t["nn"]}/{t["cand"]} = {nn:.3f} (criterio <= 0.05) -> {"PASS" if nn <= 0.05 else "FAIL"}')
    print(f'{tag}3 letras falsas, janelas puras marcadas: {t["pu"]}/{t["pn"]} = {det:.3f} (criterio >= 0.60)'
          f' -> {"PASS" if t["pn"] and det >= 0.60 else "FAIL" if t["pn"] else "sem janela pura"}')
    print(f'   (informativo) mistas {t["mu"]}/{t["mn"]}; alarme fora das falsas no rv2+falsas {t["ok_fk"]}/{t["ok_fn"]};'
          f' mapas da ordem errada: nao-conf {t["bu"]}/{t["bj"]}')
json.dump({f'{S}/{s}': {k: v for k, v in r.items()} for (S, s), r in res.items()}, open(f'{OUT}/resultado.json', 'w'), indent=1)
