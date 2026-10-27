"""Every saved 6-map triangle (3 models x 2 orders): sealed tie-break vs tie-break with the post-seal guard.
Read-only. Run from the ink-or-hallucination repo root, after guarda_desempate.py."""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.getcwd())
import segment as sg

ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/challenges/vesuvius')


def sealed(tri, th=1.25):          # PREREG_HELDOUT2, byte-for-byte logic of the sealed version
    S = {}
    for sd in 'fr':
        c3 = [v['corr'] for k, v in tri['pairs'].items() if all(n.endswith('_' + sd) for n in k.split(' x '))]
        if len(c3) != 3:
            return None
        S[sd] = float(np.median(c3))
    r = max(S.values()) / max(min(S.values()), 1e-6)
    return ('forward' if S['f'] > S['r'] else 'reverse') if r >= th else None, r


n = changed = 0
for f in sorted(glob.glob(os.path.join(ROOT, '**', 'triangulo*.json'), recursive=True)):
    if '/workspace' in f:
        continue
    try:
        tri = json.load(open(f))
    except Exception:
        continue
    if not isinstance(tri, dict) or 'pairs' not in tri:
        continue
    old = sealed(tri)
    if old is None:
        continue
    new = sg.trio_strength(tri)
    n += 1
    flag = '' if old[0] == new['order'] else '   <-- CHANGED'
    changed += bool(flag)
    print(f'{os.path.relpath(f, ROOT):70s} ratio {old[1]:6.2f}  sealed {str(old[0]):8s} guarded {str(new["order"]):8s} '
          f'{new["guard"] or ""}{flag}')
print(f'\n{n} six-map triangles; {changed} decisions changed by the guard')
