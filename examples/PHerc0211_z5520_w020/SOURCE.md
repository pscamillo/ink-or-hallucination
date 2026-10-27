# PHerc0211_z5520_w020

Maps for the README's ready-to-run example: no labels, so a usage example, not evidence.

- Mesh: `meshes/PHerc0211/z5520_w020` of the public [mesh package](https://github.com/pscamillo/vesuvius-eligible-meshes),
  picked by the rule in `scripts/escolhe_exemplo.py` before running.
- Made by `demo_unlabelled.py`: render with `vc_render_tifxyz` (public CT, no `--flip-normals`), then ink_9um,
  Reader v2 and Reader V3 on the render (`NAME.tif`) and on the same render with its layers in the other order
  (`NAME_reverse.tif`). uint8, 1120 x 2880 px, 9.4 um per pixel.
- Layer order: the geometry rule abstained (CT match 0.35); the trio-strength tie-break chose forward (1.28).
  `order_rule.json` is the demo's own record.
