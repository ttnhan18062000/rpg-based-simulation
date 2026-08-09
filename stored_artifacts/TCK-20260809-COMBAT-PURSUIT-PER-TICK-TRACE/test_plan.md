---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE

## New tests (`tests/unit/movement/test_pursuit_target_refresh.py`)

1. `test_pursuit_target_refreshes_to_live_position_not_stale_snapshot` — a pursuer with a stale
   `navigation.target` in one direction and a real `task.payload["target_id"]` pointing to a live
   entity now positioned in the *opposite* direction steps toward the live position, not the
   stale one.
2. `test_fixed_point_errand_not_refreshed_without_target_id` — no `target_id` in payload (the real
   signature of `WANDER`/`RETREAT`/objective-pursuit) means the fix is a no-op; the entity still
   walks toward its static target even with an irrelevant live entity nearby.
3. `test_dead_target_id_falls_back_to_stale_snapshot_without_crashing` — a `target_id` pointing to
   a dead entity is not tracked; falls back to the stale snapshot safely.
4. `test_missing_target_id_entity_falls_back_to_stale_snapshot_without_crashing` — a `target_id`
   that no longer resolves in `state.entities` (already despawned) is handled safely.

## Regression coverage

Full scoped re-run: `tests/unit/movement/`, `tests/unit/tactical/`, `tests/unit/combat/`,
`tests/unit/kernel/`, `tests/unit/strategic/` — confirms no existing movement-routing behavior
changed for any non-entity-tracking movement mode.

## Real corpus re-verification

Direct instrumentation confirmed the fix fires 176 times in a 2000-tick `dungeon_crawl` run
(cases where the live target genuinely differed from the stale snapshot). The real,
direct measure — `is_attack_legal` rate for genuine hostile pairs — improved from 0% (100%
`OUT_OF_RANGE`, pre-fix) to 44% (69/156 real checks, post-fix). See investigation.md's own "Real
fix implemented and verified" section for the full breakdown and the honest disclosure that the
final aggregate kill count in this specific short run stayed flat despite the large legal-rate
improvement.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/movement/ tests/unit/tactical/ tests/unit/combat/ tests/unit/kernel/ tests/unit/strategic/ -q`
