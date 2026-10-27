"""Re-read every saved triangle (label-free): for each map whose printed verdict starts with 'suspect', does it in fact
agree with EVERY core map (the v7-v10 printing bug), or only with part of it (a true 'suspect')?
Agreement = p < alpha and corr >= min_ratio x null_max, the rule inkcheck itself uses (values saved in each json).
No label, no model. uso: python relê_triangulos.py
"""
import glob, json, os

I = os.path.expanduser('~/challenges/vesuvius/inkcheck')
rows = []
for p in sorted(glob.glob(f'{I}/**/triangulo*.json', recursive=True)):
    try:
        t = json.load(open(p))
    except Exception:
        continue
    core, verdict, pairs = t.get('core') or [], t.get('verdict') or {}, t.get('pairs') or {}
    if not core or not verdict:
        continue
    a, mr = float(t.get('alpha', 0.01)), float(t.get('min_ratio', 2.0))

    def agree(x, y):
        v = pairs.get(f'{x} x {y}') or pairs.get(f'{y} x {x}')
        return bool(v) and v['p'] < a and v['corr'] >= mr * v['null_max']
    for m, v in verdict.items():
        if not v.startswith('suspect'):
            continue
        n_ok = sum(agree(m, c) for c in core)
        rows.append((os.path.relpath(p, I), m, n_ok, len(core)))

print(f'{"triangle file":62s} {"map":16s} agrees with core maps')
for f, m, k, n in rows:
    tag = 'ALL (printing bug: should read "agrees with the whole core")' if k == n else 'part (true suspect)'
    print(f'{f[:62]:62s} {m:16s} {k}/{n}  {tag}')
allc = sum(k == n for _, _, k, n in rows)
print(f'\n{len(rows)} "suspect" verdicts; {allc} agreed with the whole core, {len(rows) - allc} with part of it')
by = {}
for f, m, k, n in rows:
    by.setdefault(f.split('/')[0], [0, 0])[k == n] += 1
for d, (part, full) in sorted(by.items()):
    print(f'  {d:20s} true suspect {part:3d}   agreed with whole core {full:3d}')
