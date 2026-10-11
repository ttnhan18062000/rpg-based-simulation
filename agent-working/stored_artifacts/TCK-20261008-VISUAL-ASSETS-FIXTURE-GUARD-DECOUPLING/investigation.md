---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING
artifact_type: investigation
date: 2026-10-08
tags: [architecture, testing]
---

# Investigation

- Probe: a throwaway key in `visual_keys.yaml` breaks 10 tests: 2 rc-coupled (pilot check 1, terrainset), 8 inventory pins (test_registry exact key list, icon_draft_set, icon_recognition, icon_set_adoption, icon_specs x2, icon_v2_keys x2). Only the two rc-coupled ones forced candidates.
- The store refuses a candidate whose `registry_hash` differs from the live registry (`runtime_export.py:79-80`, `registry_mismatch`); that stays (`test_runtime_export.py:150`).
- `verify` requires an artifact record for each candidate digest (`_check_entry`) and hashes each tracked artifact PNG against its record, so a candidate's pixel hash reaches the PNG transitively; `derived_runtime.derive` also asserts it directly.
- After the change the same probe: both fixture guards pass; the 8 inventory pins still fail (by design).
