# ADDENDUM to PREREG_V11.md (sha256 c0a27834…)

Date: 2026-10-24, written after the first launch crashed and before any criterion was computed.
Author: Paulo Sergio Camillo.

## What happened

The first launch of `fase6.py` (md5 85bd1f37…) crashed on the first segment (PHerc0139 w035) at the planting
step, with `NameError: binary_dilation`. `glyph()` and `plant()`, reused from `fase5.py`, need `binary_dilation` and
`gaussian_filter`, and `fase6.py` did not import them.

## The fix

One import line:

```python
from scipy.ndimage import uniform_filter, binary_dilation, gaussian_filter
```

`fase6.py` is now md5 `4dab3cf982d4f51f6380165f51c7925f`. Nothing else changed: no setting, threshold, criterion,
data or seed. `inkcheck_v11.py` is unchanged (ac5de45a…).

## What was seen before the fix

These lines were printed for PHerc0139 w035 before the crash. No label was read and no criterion was computed:

```
ink9 previsto: julgadas 0  nao-conf 0  sem-nulo 0
rv2 previsto: julgadas 0  nao-conf 0  sem-nulo 0
rv3 previsto: julgadas 2  nao-conf 0  sem-nulo 0
ink9 ordem errada: julgadas 16  nao-conf 16  sem-nulo 0
rv2 ordem errada: julgadas 20  nao-conf 20  sem-nulo 0
rv3 ordem errada: julgadas 16  nao-conf 16  sem-nulo 0
```

The run is restarted from scratch with the fixed script. The w035 numbers above are recomputed, with the same seed.
