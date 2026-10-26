"""Which config field holds each segment id, per model, and which scroll each id belongs to (by S3 segment name).
Read-only: checkpoints' configs + S3 listings. No label is opened.
uso (villa python): python onde_treino.py
"""
import json, os, re, socket, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import torch

socket.setdefaulttimeout(60)
H = os.path.expanduser('~/challenges/vesuvius')
CK = {'ink9': f'{H}/ink-lens/gate_fibras_1447/checkpoints/ink_9um/hybrid_3d2d-seed43/step-060000.pth',
      'rv2': f'{H}/reader_v2/reader-v2-step040000.pth', 'rv3': f'{H}/reader_v3/reader-v3.pth'}
S3 = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
PAT = re.compile(r'(\d{14}(?:[-_][A-Za-z0-9_]+)?|\bw\d{3}\b)')


def walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f'{path}.{k}' if path else str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from walk(v, f'{path}[{i}]')
    elif isinstance(o, str):
        for m in PAT.findall(o):
            yield path, m, o


def ls(prefix):
    out, tok = [], None
    while True:
        q = f'?list-type=2&delimiter=/&prefix={urllib.parse.quote(prefix)}' + (f'&continuation-token={urllib.parse.quote(tok)}' if tok else '')
        x = urllib.request.urlopen(S3 + q).read().decode()
        out += re.findall(r'<Prefix>([^<]+)</Prefix>', x)
        m = re.search(r'<NextContinuationToken>([^<]+)</NextContinuationToken>', x)
        if not m:
            return [o for o in out if o != prefix]
        tok = m.group(1)


seg_scroll = {}
for sc in ls(''):
    try:
        for s in ls(sc + 'segments/'):
            seg_scroll[s.split('/')[-2]] = sc.rstrip('/')
    except Exception:
        pass
by_stamp = {k[:14]: v for k, v in seg_scroll.items() if k[:14].isdigit()}

for m, p in CK.items():
    cfg = torch.load(p, map_location='cpu', weights_only=False).get('config', {})
    print(f'\n===== {m}: config keys with segment ids')
    groups = {}
    for path, sid, full in walk(cfg):
        key = re.sub(r'\[\d+\]', '[]', path)
        sc = seg_scroll.get(sid) or by_stamp.get(sid[:14]) or ('?' if not sid.startswith('w') else '(w-name)')
        hint = re.search(r'(PHerc\w+|pherc\w+|Paris4|500P2|9B|1447|0139|0814|1667)', full)
        groups.setdefault(key, set()).add((sid, sc, hint.group(1) if hint else ''))
    for key, ids in sorted(groups.items()):
        scrolls = sorted({s for _, s, _ in ids} | {h for _, _, h in ids if h})
        print(f'  {key}  ({len(ids)} ids)  scrolls/hints: {scrolls}')
        for sid, sc, h in sorted(ids):
            if sc in ('?', 'PHerc0500P2', 'PHerc0009B', 'PHerc1447', 'PHerc0841') or h in ('500P2', '9B', '1447'):
                print(f'      {sid:55s} {sc} {h}')
