---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION
artifact_type: test_plan
tags: [world, content, root-cause]
---

# Test Plan — TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION

## Test Cases
- Unit: colliding region ids get a namespace; bare-id owner is independent of selection order; no collision leaves namespace unset.
- Integration (real content): generated `generated_frontier_3_42` composition assembles, and each module's populations spawn in that module's own region (bounds check).

## Proof Plan
### AC2 / AC2b
- **level**: integration (real content) + unit
- **proof kind**: regression (fails on unfixed generator)
- **oracle source**: `docs/mechanics/06_worldbuilding_foundation.md` integrity validation; world rules `ID-01`, `LOC-01`; parity `SUBSTRATE-NEW-010`
- **expected effect**: assembly succeeds; every population's `spawn_region` bounds equal its own module's region bounds; non-empty check precedes the loop
- **selected commands**: `pytest tests/integration/worldassembly/test_real_content_world_compositions.py tests/unit/worldgeneration/test_composition_generator.py -q`
### AC2a
- **level**: unit
- **proof kind**: invariant (order independence)
- **oracle source**: ticket RULING Condition 1; `ID-01`
- **expected effect**: same module keeps the bare id under reversed module order
- **selected commands**: `pytest tests/unit/worldgeneration/test_composition_generator.py -q -k Namespacing`
### AC3
- **level**: integration
- **proof kind**: regression
- **oracle source**: ticket AC-3
- **expected effect**: two strict xfail marks removed (DEFERRED: marks exist only on #328)
- **selected commands**: `pytest tests/integration/worldassembly/test_real_content_world_compositions.py -q`
### AC4
- **level**: docs
- **proof kind**: parity record
- **oracle source**: `docs/guidelines/intentional_divergences.md`
- **expected effect**: DEV-008 and ledger rule (6) present; `codebase.gates.parity_ledger_schema check` reports no new errors
- **selected commands**: `python3 -m codebase.gates.parity_ledger_schema check`
