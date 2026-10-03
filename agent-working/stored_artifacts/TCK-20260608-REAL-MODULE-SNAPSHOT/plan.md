---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-REAL-MODULE-SNAPSHOT
artifact_type: plan
tags: [real, module, snapshot]
---

# Plan — TCK-20260608-REAL-MODULE-SNAPSHOT

## Steps
1. Create tests/integration/worldassembly/test_real_module_normalized_snapshot.py
2. Load frontier_village_core via WorldModuleRepository (no synthetic construction)
3. Assert normalized shape: module_id, module_type, all *_refs as tuples of strings, count maps as str→int dicts
4. Assert no raw dicts in any *_refs tuple element

## Deviations
None.
