"""README usage example (not evidence): the kit on PHerc1447 w062 (Youssef Nader's public release, no labels), with
the maps fase11.py (PREREG_HELDOUT3) already made: the three villa models + v8-in, both orders. No model is run.
Layer order: reverse, decided by the geometry rule before any model ran (RESULT_HELDOUT3). The report goes to a new
folder; fase11's files are only read.
uso: python exemplo_w062.py
"""
import json, os, sys

H = os.path.expanduser('~/challenges/vesuvius')
sys.path.insert(0, f'{H}/ink-or-hallucination')
import segment

SRC = f'{H}/inkcheck/fase11/w062'
OUT = f'{H}/exemplo0813/PHerc1447_w062'
r = json.load(open(f'{H}/inkcheck/fase11/antes_dos_rotulos.json'))['w062']
assert r['pred'] == 'reverse' and r.get('pred_from') == 'rule', r
print(f'w062: order {r["pred"]} ({r["pred_from"]}: CT match {r["rule"]["ct_match_median_corr"]:.2f}), '
      f'pixel {r["px_um"]:.2f} um', flush=True)
segment.run(SRC, ['ink9', 'rv2', 'rv3', 'v8in'], 'reverse', px_um=r['px_um'], out_dir=OUT)
