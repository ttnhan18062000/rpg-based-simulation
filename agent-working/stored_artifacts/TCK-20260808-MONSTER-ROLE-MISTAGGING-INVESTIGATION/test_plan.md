---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
artifact_type: test_plan
tags: [content, world]
---

# Test Plan: TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION

## New Tests
`tests/unit/worldbuilding/test_world_repository.py`:
- `test_load_world_with_context_non_composition_returns_none_context`
- `test_load_world_with_context_composition_loads_real_role_mapping` — the exact bug
  reproduction: a composition world's own `compile_context.json` must be loaded and returned.
- `test_load_world_with_context_composition_missing_compile_context_degrades_to_none`
- `test_load_world_with_context_unresolved_composition_raises`

All 4 confirmed via git-stash bisection to genuinely fail pre-fix.

## Regression Scope
`tests/unit/worldbuilding/`, `tests/simulation_quality/`, `tests/unit/content_semantics/`,
`tests/unit/core/`, `tests/unit/entities/`, `tests/unit/world/`, `tests/unit/tactical/`,
`tests/unit/combat/`, `tests/unit/engine/`, `tests/unit/kernel/`,
`tests/integration/worldassembly/`, `tests/integration/kernel/test_determinism_suite.py` — broad
sweep given the fix touches a shared loading path used by multiple domains' own tests.

## Real Corpus Verification
Direct compiled-state inspection (role/faction distributions) on `dungeon_crawl_seed42` and
`urban_political_seed42`, before and after the fix. Real SimQ calibration re-run on both worlds
(`tools/calibrate_simq.py`) to measure the real, material downstream scoring impact.
