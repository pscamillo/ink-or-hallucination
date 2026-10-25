"""v3 (PHerc1667): igual ao geometria.py do PREREG_ORDEM, com malha 2.4 um dividida por 4 e CT no nivel 2.
Fase de geometria do PREREG_ORDEM (sem rotulo: do rotulo so se le o TAMANHO, para casar com o render).
Para cada segmento de labels_hf com render local do mesmo tamanho e malha publica:
  curvatura.py --D 1000  -> +n fora/dentro
  ordem_camadas.py       -> camadas guardadas crescem ao longo de +n ou -n
  regra (calibrada no w058): o modelo quer a pilha de FORA para DENTRO -> preve forward ou reverse.
Grava geometria.tsv. uso: python geometria.py
"""
import os, re, glob, subprocess, sys, json
import numpy as np, zarr

H = os.path.expanduser('~/challenges/vesuvius')
LAB = f'{H}/villa_ink/ink-detection/labels_hf'
REN = f'{H}/villa_ink/ink-detection/renders'
MAL = f'{H}/inkcheck/malhas_1667/L2'
PY = sys.executable
B = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
CT = {'pherc0139': f'{B}/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/0',
      'pherc0814': f'{B}/PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/0',
      'pherc1667': f'{B}/PHerc1667/volumes/20251217075048-2.399um-0.2m-78keV-masked.zarr/2'}


def shape(p):
    g = zarr.open(p, mode='r')
    return (g['0'] if not hasattr(g, 'shape') else g).shape


# coords da malha foram divididas por 4 (prep_1667.sh): a densidade da grade por voxel do nivel 2 fica 4x maior
for s in os.listdir(MAL):
    mp = f'{MAL}/{s}/meta.json'; m = json.load(open(mp))
    if not m.get('scale_fixed'):
        m['scale'] = [v * 4 for v in m['scale']]; m['scale_fixed'] = True; json.dump(m, open(mp, 'w'), indent=1)

rows = []
for seg in sorted(os.listdir(LAB)):
    if not seg.startswith('pherc1667'):
        continue
    m = re.match(r'(pherc\d+)-(\w+)', seg)
    if not m or not os.path.isdir(f'{MAL}/{seg}'):
        continue
    rolo, w = m.groups()
    lab = glob.glob(f'{LAB}/{seg}/*inklabels.zarr')
    if not lab:
        continue
    ls = shape(lab[0])[1:]
    num = rolo.replace('pherc', '')
    cands = [f'{REN}/acc1/{seg}_mean.zarr'] + sorted(glob.glob(f'{REN}/{num}_{w}_prep9*.zarr'))
    ren = next((c for c in cands if os.path.exists(c) and shape(c)[1:] == ls), None)
    if ren is None:
        print(f'{seg:18s} sem render do tamanho do rotulo {ls}'); continue
    if not CT[rolo]:
        print(f'{seg:18s} sem URL do CT ({rolo})'); continue
    cu = subprocess.run([PY, f'{H}/inkcheck/curvatura.py', f'{MAL}/{seg}', '--D', '1000'], capture_output=True, text=True).stdout
    fl = float(re.search(r'flecha media\s+([-+0-9.]+)vx', cu).group(1))
    fora = fl < 0          # flecha negativa: a folha se curva para -n, logo +n aponta para FORA
    decide_c = abs(fl) >= 0.02 * 1000
    oc = subprocess.run([PY, f'{H}/inkcheck/ordem_camadas.py', f'{MAL}/{seg}', ren, CT[rolo]], capture_output=True, text=True)
    out = oc.stdout
    try:
        b = float(re.search(r'inclinacao t por camada = ([-+0-9.]+)', out).group(1))
        cs = [float(x) for x in re.findall(r'->\s*t\s*[-+]\d+\s+\(([-0-9.]+)\)', out)]
        cmed = float(np.median(cs))
    except Exception:
        print(f'{seg:18s} ordem_camadas falhou:\n{out[-400:]}{oc.stderr[-600:]}'); continue
    decide_o = cmed >= 0.5 and abs(b) >= 0.5
    cresce_para_fora = (b > 0) == fora
    pred = ('reverse' if cresce_para_fora else 'forward') if (decide_c and decide_o) else 'sem previsao'
    print(f'{seg:18s} render {os.path.basename(ren):28s} flecha {fl:+7.1f} (+n {"fora" if fora else "dentro"})  '
          f'inclinacao {b:+.2f} corr_med {cmed:.2f}  camadas crescem para {"fora" if cresce_para_fora else "dentro"}  ->  {pred}')
    rows.append([seg, ren, f'{fl:.1f}', f'{b:.2f}', f'{cmed:.2f}', pred])
with open(f'{H}/inkcheck/geometria_1667.tsv', 'w') as f:
    f.write('segmento\trender\tflecha\tinclinacao\tcorr_med\tprevisao\n')
    for r in rows:
        f.write('\t'.join(r) + '\n')
print('gravado geometria_1667.tsv com', len(rows), 'segmentos')
