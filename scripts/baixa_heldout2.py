"""Download what PREREG_HELDOUT2 needs: the one labelled public segment of PHerc0500P2 and of PHerc0009B.
No model, no check, no label read. Per segment, into ~/challenges/vesuvius/heldout2/<seg>/ (same layout as heldout0841,
so the names say "9" for the models' scale even where it is 8.64 um):
  sv9.zarr      surface volume at the models' scale (9.362 / 8.64 um), level 0 only
  mesh_9um/     tifxyz at that scale (order rule, pixel size, window)
  labels/       inklabels, supervision, validation (fine grid, level 0 only) -- downloaded, NOT opened here
  sv2_l2.zarr   fine surface volume (2.215 / 2.401 um), level 2 only (CT-to-CT registration check, no labels)
uso: python baixa_heldout2.py
"""
import os, re, sys, time, socket, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

S3 = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
socket.setdefaulttimeout(60)        # a stalled S3 connection raises after 60 s, so retry() can try again
ROOT = os.path.expanduser('~/challenges/vesuvius/heldout2')
SEGS = {
    'PHerc0500P2/20250825181859--1': dict(
        SV9='surface-volumes/9.362um-1.2m-113keV-volume-20250820143440.zarr',
        SV2='surface-volumes/2.215um-0.4m-111keV-volume-20250526151718.zarr',
        LAB='ink-labels/2.215um-volume-20250526151718/20260918',
        MESH='mesh/20250825181859-on-20250820143440-9.362um.tifxyz/'),
    'PHerc0009B/20250919125754-auto_grown_20250919055754487_inp_hr': dict(
        SV9='surface-volumes/8.64um-1.2m-116keV-volume-20250521125136.zarr',
        SV2='surface-volumes/2.401um-0.35m-77keV-volume-20250820154339.zarr',
        LAB='ink-labels/2.401um-volume-20250820154339/20260918',
        MESH='mesh/20250919125754-on-20250521125136-8.64um.tifxyz/'),
}


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


def want(rel, SV9, SV2, LAB, MESH):
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
    if rel.startswith(MESH):
        return '/' not in rel[len(MESH):], 'mesh_9um/' + rel.split('/')[-1]
    return False, None


for name, P in SEGS.items():
    scroll, seg = name.split('/')
    SV9, SV2, LAB, MESH = P['SV9'], P['SV2'], P['LAB'], P['MESH']
    base = f'{scroll}/segments/{seg}/'
    jobs = []
    # list only what is needed: the full 2.403 um volume has tens of thousands of chunks we never use
    prefixes = [f'{SV9}/0/', f'{SV9}/.z', f'{SV9}/zarr.json', f'{SV2}/2/', f'{SV2}/.z', f'{SV2}/zarr.json', f'{LAB}/', MESH]
    for pre in prefixes:
        for k, s in keys(base + pre):
            ok, dst = want(k[len(base):], SV9, SV2, LAB, MESH)
            if ok:
                jobs.append((k, s, os.path.join(ROOT, seg, dst)))
    tot = sum(s for _, s, _ in jobs)
    print(f'{seg}: {len(jobs)} files, {tot / 1e6:.0f} MB', flush=True)
    with ThreadPoolExecutor(8) as ex:
        got = sum(ex.map(fetch, jobs))
    print(f'   downloaded {got / 1e6:.0f} MB', flush=True)
print('done')
