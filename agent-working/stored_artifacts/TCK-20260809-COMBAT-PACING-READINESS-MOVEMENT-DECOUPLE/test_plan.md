---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE

## Normal flow
- `test_successful_move_no_longer_costs_readiness`
  (`tests/unit/movement/test_phase4_movement.py`): a successful move leaves `readiness_delta ==
  0.0` while still applying the real stamina cost (`-hero.stamina.MOVE_COST`).
- `test_mutual_adjacent_position_swap_succeeds` (`tests/unit/movement/test_position_swap.py`,
  extended): a position-swap move leaves both entities' `combat.readiness` unchanged (100.0).

## Real corpus re-verification (not unit-test-only)
Live `is_attack_legal` probe (same methodology this whole session's investigation chain used),
`dungeon_crawl` and `urban_political`, 600 real ticks each, before/after:
- `dungeon_crawl`: 1.3% → 28.5% legal; `INSUFFICIENT_READINESS` eliminated from the reason
  breakdown entirely.
- `urban_political`: 36.6% legal (not separately baselined pre-fix in this exact probe run, but
  consistent with the sibling ticket's own established low baseline).

## Failure modes / regression-prone paths
Full scoped pytest run across every domain touching movement, combat, or entity generation:
`tests/unit/movement/`, `tests/unit/combat/`, `tests/unit/core/`, `tests/unit/kernel/`,
`tests/unit/tactical/`, `tests/unit/optimization/`, `tests/unit/worldbuilding/`,
`tests/unit/worldassembly/`, `tests/unit/strategic/`, `tests/unit/entities/`,
`tests/unit/content/`, `tests/unit/resource/`, `tests/unit/social/`, plus
`tests/integration/combat/`, `tests/integration/pipeline/`,
`tests/integration/kernel/test_determinism_suite.py`,
`tests/integration/kernel/test_seed_stability.py` (both determinism-critical given `movement.py`
is a hot, frequently-exercised path).

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/movement/ tests/unit/combat/ tests/unit/core/ \
  tests/unit/kernel/ tests/unit/tactical/ tests/unit/optimization/ tests/unit/worldbuilding/ \
  tests/unit/worldassembly/ tests/unit/strategic/ tests/unit/entities/ tests/unit/content/ \
  tests/unit/resource/ tests/unit/social/ tests/integration/combat/ tests/integration/pipeline/ \
  tests/integration/kernel/test_determinism_suite.py \
  tests/integration/kernel/test_seed_stability.py -q -m "not slow"
```
Result: 1453 passed in the primary combined run, 3 failures — all confirmed pre-existing and
unrelated via `git stash` bisection (identical failures reproduce with this ticket's own
`movement.py`/`pipeline_phases/movement.py` changes fully reverted): `test_module_family_anchored`
(missing world data directory), `test_normal_move_triggers_oa` (pre-existing, confirmed back in
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`), and a newly-encountered third
one, `tests/unit/strategic/test_registries.py::test_referential_integrity`
(`ItemRegistry.contains('stone')` False when a real `ResourceDef` expects it True) — passes in
isolation, a real, separate test-isolation issue similar in class to
`TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET`'s own fix but for a different registry
interaction, not caused by or fixed in this ticket. Zero new regressions from this ticket's own
changes.
