---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

- `test_registry.py` (+6): class/fallback required (fixture keys exempt), kind/class consistency (8 refusals, 4 accepts), icon label rules, variant_axes rejected (also fixtures), `fallback_problems` on a hand-built registry, the committed registry (62 keys, classes, 35 labels).
- `test_release.py`, `test_runtime_export.py` (+1 each): `fallback_missing` at release and export time, asked about exactly the keys with images (an extra optional key without an image makes the wrong-set mutants fail).
- `test_record_bounds.py`: the maximal registry through the real read path, now without axes and with fields.
- Mutants J-T (`mutant_proof.txt`). Scoped suites 2023 passed; `store verify` ok; icon fixtures identical; vitest `src/visualAssets` 270 passed.
