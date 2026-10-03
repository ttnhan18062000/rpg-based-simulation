---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY
artifact_type: test_plan
tags: [combat, observability, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY

## New tests (`tests/unit/observability/test_event_shapers.py`)

1. `test_combat_entity_snapshot_returns_real_fields` / `_none_entity_returns_none` /
   `_unmapped_role_falls_back_to_str` — the new `_combat_entity_snapshot()` helper.
2. `test_combat_engagement_started_fires_alongside_combat_initiated_goal_engage` /
   `_trigger_reason_opportunity_attack` / `_not_emitted_when_already_damaged` — the
   `combat_engagement_started` gate and its `trigger_reason` derivation.
3. `test_combat_engagement_ended_kill_fires_alongside_entity_killed` — outcome KILL.
4. `test_combat_engagement_ended_caught_fleeing_for_non_lethal_opportunity_attack` /
   `_not_emitted_for_deliberate_attack` / `_not_emitted_when_also_a_kill` — outcome
   CAUGHT_FLEEING and its two negative cases (deliberate attack, lethal OA is reported as KILL
   only, not double-counted).
5. `test_combat_engagement_ended_pursuit_abandoned_leash_return` / `_stalemate_break` /
   `_not_emitted_for_other_reasons` — outcome PURSUIT_ABANDONED, read from a task-only
   `EntityUpdate` with no `combat` field, and its reason-string discriminant.
6. `test_combat_engagement_ended_escaped_reads_movement_escape_tag` /
   `_not_emitted_without_the_tag` — outcome ESCAPED, reading `movement.py`'s new
   `combat_escape`/`combat_escape_evaded_ids` `property_updates` tag.

All 6 real trigger conditions (2 for `combat_engagement_started`, 4 for
`combat_engagement_ended`) get direct coverage via this repo's own established
hand-constructed-mock precedent for `CombatShaper` (`_entity`/`_update`/`_real_combat_upd`
builders, extended with identity/personality/task fields for this ticket).

## Regression coverage

`tests/unit/observability/test_event_shapers.py`'s full existing suite (registry mechanism,
`combat_damage`/`combat_initiated`/`near_death_survival`/`entity_killed`/`hazard_drain_applied`
gates, volumization rules, non-combat HP-loss exclusion, SHADOW-mode inertness) — confirms the
restructured loop (PURSUIT_ABANDONED/ESCAPED checks moved before the `combat_upd is None`
early-continue) did not change any existing event's gate condition.

`tests/unit/movement/` — confirms the new, purely additive `combat_escape` `property_updates`
tag in `resolve_move()` does not change `skip_oa`/opportunity-attack resolution itself.

## Real corpus re-verification

A live `Kernel.tick_once()` loop, 2000 ticks, against `dungeon_crawl_seed42` (32 entities) and
`urban_political_seed42` (30 entities), reading `kernel._event_recorder`'s real recorded events
directly. See `investigation.md`'s "Real corpus re-verification" section for the full breakdown:
`PURSUIT_ABANDONED`/`ESCAPED` confirmed firing at real, non-zero volume under corpus-default
feature flags; `combat_engagement_started`/`KILL`/`CAUGHT_FLEEING` (all gated behind
`ENABLE_COMBAT_ENGAGEMENT`) did not fire at this corpus/scale — verified this is a pre-existing
condition shared by the sibling events they ride alongside (`combat_initiated`/`entity_killed`
also recorded zero occurrences in the same runs), not a gap this ticket introduced.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/observability/ tests/unit/movement/ tests/unit/combat/ -q`
