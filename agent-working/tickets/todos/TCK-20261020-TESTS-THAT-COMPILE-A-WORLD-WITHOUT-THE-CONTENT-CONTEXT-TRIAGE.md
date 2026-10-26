---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE

## Title
Triage the 24 tests and tools that compile a world without the content context, which gives a world with no starting purses or inventories

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
On 2026-10-20 Lane B found that `tests/regression/test_behavioral_5k.py` compiles its world with `repo.load_world` and `WorldCompiler.compile(spec, seed)` and no `context=`. With no context, `compiler.py:155` gives entities no starting inventory, so gold_avg read 0.0. That one is fixed separately (TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT). A read-only probe found 24 files under tests/ and tools/ with the same pattern; the list is in /mnt/data/scratch-rpg-implementer-2/load_world_no_context.txt. These are likely measuring a world with no purses:
- tests/integration/scenarios/test_balance_regression.py
- tests/integration/scenarios/test_content_foundation.py
- tests/unit/worldassembly/test_hero_guild_routing_population_stability.py
- tests/unit/worldassembly/test_throttled_kernel_smoke.py
- tests/engine/test_hard_law_monitor.py
- tests/integration/world/test_camp_raid_targeting.py
- tests/integration/world/test_lair_region_trauma_reachability.py
- tests/unit/engine/test_terrain_cost_from_content.py
- tests/simulation_quality/test_traceability_path.py
- tools/review_pipeline_check.py
The rest are rendering, visual and place-corpus tests.

## Scope
- For each file, decide whether its assertions depend on starting inventory or gold. If they do, move it to the shared world-build helper that the gate uses, from the behavioral_5k fix. If they don't, record why.
- Consider a guard that makes a context-less compile of a world that declares starting gold explicit, such as a required `context=` or an opt-out flag, so the trap can't come back silently.
- Re-check any expected values that move, and treat each one as a behaviour finding. Don't re-pin values to make tests pass.

## Out of Scope
- behavioral_5k (its own ticket). Changing compiler semantics.

## Acceptance Criteria
- Every listed file is classified with a reason. Each dependent file uses the shared helper, and its tests pass with any moved expectation explained.
- A decision on the guard is recorded.

## Related Tickets
- TCK-20261020-BEHAVIORAL-5K-BUILDS-ITS-WORLD-WITHOUT-THE-CONTENT-CONTEXT

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/load_world_no_context.txt

## Related Code Areas
- src/worldbuilding compiler.py:155
- tools/test_architecture rpg_gate_run.build_kernel (load_world_with_context)

## Assumptions / Open Questions
- Some tests may deliberately want a bare world. Record them, don't convert them.

## Implementation Notes
After v1.

## Test Summary

## Files Changed

## Completion Summary
