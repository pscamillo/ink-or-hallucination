"""Download what PREREG_HELDOUT0841 needs, for the three public PHerc0841 segments. No model, no check, no label read.
Per segment, into ~/challenges/vesuvius/heldout0841/<seg>/:
  sv9.zarr      9.366 um surface volume, level 0 only (the models' input)
  mesh_9um/     9.366 um tifxyz (pixel size and window)
  labels/       inklabels, supervision, validation (2.403 um grid, level 0 only) -- downloaded, NOT opened here
  sv2_l2.zarr   2.403 um surface volume, level 2 only (CT-to-CT registration check, no labels involved)
uso: python baixa_0841.py
"""
import os, re, sys, time, socket, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

S3 = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
socket.setdefaulttimeout(60)        # a stalled S3 connection raises after 60 s, so retry() can try again
ROOT = os.path.expanduser('~/challenges/vesuvius/heldout0841')
SEGS = ['20260220213127-w00', '20260220214732-auto_grown_20260220144552896', '20260221022814-auto_grown_20260220174252405']
SV9 = 'surface-volumes/9.366um-1.2m-113keV-volume-20250821151531.zarr'
SV2 = 'surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr'
LAB = 'ink-labels/2.403um-volume-20260319124803/20260918'


def retry(f, *a):
    for k in range(8):                     # S3 sometimes drops a connection; wait and try again
        try:
            return f(*a)
        except Exception as e:
            if k == 7:
                raise
            time.sleep(2 * (k + 1))


def keys(prefix):
    out, tok = [], None
    while True:
        q = f'?list-type=2&prefix={urllib.parse.quote(prefix)}' + (f'&continuation-token={urllib.parse.quote(tok)}' if tok else '')
        xml = retry(lambda u: urllib.request.urlopen(u, timeout=60).read().decode(), S3 + q)
        out += list(zip(re.findall(r'<Key>([^<]+)</Key>', xml), map(int, re.findall(r'<Size>(\d+)</Size>', xml))))
        m = re.search(r'<NextContinuationToken>([^<]+)</NextContinuationToken>', xml)
        if not m:
            return out
        tok = m.group(1)


def fetch(job):
    key, size, dst = job
    if os.path.exists(dst) and os.path.getsize(dst) == size:
        return 0
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + '.part'
    retry(urllib.request.urlretrieve, S3 + urllib.parse.quote(key), tmp); os.replace(tmp, dst)
    return size


def want(rel):
    if rel.startswith(SV9 + '/'):
        r = rel[len(SV9) + 1:]
        return r.startswith('0/') or '/' not in r, 'sv9.zarr/' + r
    if rel.startswith(SV2 + '/'):
        r = rel[len(SV2) + 1:]
        return r.startswith('2/') or '/' not in r, 'sv2_l2.zarr/' + r
    if rel.startswith(LAB + '/'):
        r = rel[len(LAB) + 1:]                       # inklabels.zarr/0/..., inklabels.zarr/zarr.json
        parts = r.split('/')
        return len(parts) == 2 or parts[1] == '0', 'labels/' + r
    if rel.startswith('mesh/') and '-9.366um.tifxyz/' in rel:
        return True, 'mesh_9um/' + rel.split('/')[-1]
    return False, None


for seg in SEGS:
    base = f'PHerc0841/segments/{seg}/'
    jobs = []
    # list only what is needed: the full 2.403 um volume has tens of thousands of chunks we never use
    prefixes = [f'{SV9}/0/', f'{SV9}/.z', f'{SV9}/zarr.json', f'{SV2}/2/', f'{SV2}/.z', f'{SV2}/zarr.json', f'{LAB}/', 'mesh/']
    for pre in prefixes:
        for k, s in keys(base + pre):
            ok, dst = want(k[len(base):])
            if ok:
                jobs.append((k, s, os.path.join(ROOT, seg, dst)))
    tot = sum(s for _, s, _ in jobs)
    print(f'{seg}: {len(jobs)} files, {tot / 1e6:.0f} MB', flush=True)
    with ThreadPoolExecutor(8) as ex:
        got = sum(ex.map(fetch, jobs))
    print(f'   downloaded {got / 1e6:.0f} MB', flush=True)
print('done')
