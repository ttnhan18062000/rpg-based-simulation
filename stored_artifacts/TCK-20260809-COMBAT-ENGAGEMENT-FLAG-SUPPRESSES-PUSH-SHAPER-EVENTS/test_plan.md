---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS
artifact_type: test_plan
tags: [combat, simulation-quality, feature-flags]
---

# Test Plan — TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS

## New tests (`tests/unit/domains/combat_engagement/test_combat_engagement_phase_merge.py`)

1. `test_combat_engagement_preserves_prior_phase_updates_when_flag_on` — a hand-injected,
   pre-existing `EntityUpdate` (simulating an earlier real phase's own output, e.g.
   `action_routing`) for an entity `CombatEngagementPhase.apply()` itself won't touch (isolated,
   no real neighbors) must survive a full real `AuthoritativeApplyPipeline.refine()` call with
   `ENABLE_COMBAT_ENGAGEMENT=ON`. Confirmed via `git stash` bisection to genuinely fail against
   the pre-fix code with exactly the expected assertion message ("prior phase's own real
   EntityUpdate for entity 1 was lost...").
2. `test_combat_engagement_disabled_still_preserves_prior_phase_updates` — regression guard:
   the flag-OFF (real corpus-default) path was never affected; confirms this fix changes nothing
   for the currently-shipped configuration.

## Regression coverage

Targeted: `tests/unit/domains/combat_engagement/ tests/integration/domains/combat_engagement/
tests/unit/combat/ tests/unit/tactical/ tests/unit/kernel/` — 187 passed.
Broader (pipeline-chaining risk surface, since this fix touches a shared 32-phase chain used by
every real tick): `tests/unit/ -k "pipeline or phase"` — 575 passed. `tests/unit/movement/
tests/unit/strategic/ tests/unit/entities/ tests/unit/actions/ tests/unit/observability/` —
1286 passed, 1 pre-existing unrelated failure (`test_normal_move_triggers_oa`, confirmed via
this session's own earlier bisection to predate all of today's combat work).

## Real corpus re-verification

A live `Kernel.tick_once()` loop, 2000 ticks, against `dungeon_crawl_seed42` and
`urban_political_seed42`, with `ENABLE_COMBAT_ENGAGEMENT=ON` explicitly forced — the exact
condition that previously showed total, deterministic suppression. Post-fix: real
`combat_engagement_started/ended`, `combat_resolved`, `combat_damage`, `entity_killed` all fire
alongside `combat_kill` for both worlds, matching the corpus-default (flag-off) baseline's own
real event presence.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/domains/combat_engagement/ tests/integration/domains/combat_engagement/ tests/unit/combat/ tests/unit/tactical/ tests/unit/kernel/ -q`
