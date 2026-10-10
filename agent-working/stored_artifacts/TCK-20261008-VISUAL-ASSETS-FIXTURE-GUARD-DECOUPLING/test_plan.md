---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING
artifact_type: test_plan
date: 2026-10-08
tags: [architecture, testing]
---

# Test plan

- `test_derived_runtime.py`: drift guard (derive == export_runtime byte for byte, hermetic catalog), registry-only change (store refuses, derived export unchanged), artifact bytes != recorded pixel hash fails, dropped artifact fails.
- `test_pilot_fixture.py`, `test_terrainset_fixture.py` now use `derived_runtime.write`.
- Mutants M1-M8 (`mutant_proof.txt`): flipped PNG byte (pilot, terrainset), dropped slot, changed entry detail, changed registry_hash field, artifact swapped for another valid PNG, helper dropping a field, and the probe.
- Scoped run: `pytest tests/visual_assets tests/docs tests/static tests/architecture`.
