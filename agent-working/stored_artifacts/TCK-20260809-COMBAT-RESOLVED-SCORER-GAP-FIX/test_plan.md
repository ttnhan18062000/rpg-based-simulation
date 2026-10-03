---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX

## New tests (`tests/unit/observability/test_event_shapers.py`)

1. `test_combat_resolved_fires_alongside_kill` — `combat_resolved` fires alongside
   `combat_engagement_ended(KILL)`, same tick, same entity pair.
2. `test_combat_resolved_fires_alongside_escaped` — `combat_resolved` fires alongside
   `combat_engagement_ended(ESCAPED)` (the `movement.py` `combat_escape` tag path).
3. `test_combat_resolved_not_emitted_for_caught_fleeing` — a non-lethal real opportunity attack
   must NOT trigger `combat_resolved` (no clear winner established).
4. `test_combat_resolved_not_emitted_for_pursuit_abandoned` — a `LEASH_RETURN`-triggered
   disengagement must NOT trigger `combat_resolved` (inconclusive, not a clear resolution).

## Regression coverage

`tests/unit/observability/test_event_shapers.py`'s full existing suite (all prior
`combat_engagement_started`/`ended` gates, plus the original `combat_damage`/`combat_initiated`/
`entity_killed`/`near_death_survival`/`hazard_drain_applied` gates) — confirms the new emission
sites don't change any existing event's own gate condition.
`tests/simulation_quality/test_combat_scorer.py` — confirms `CombatScorer`'s own real,
pre-existing `combat_resolved` handler scores correctly now that a real producer exists.

## Real corpus re-verification

A live `Kernel.tick_once()` loop, 2000 ticks, against `dungeon_crawl_seed42` and
`urban_political_seed42` under corpus-default feature flags, with all 3 of this session's own
combat fixes active (identity-resolver, pursuit-tracking, and this ticket's own
`combat_resolved` producer). See `investigation.md`/the closed ticket's own Test Summary for the
full breakdown: `combat_resolved` fired 1x in `dungeon_crawl` (matching its 1 real `KILL`) and 4x
in `urban_political` (matching its 4 real `ESCAPED` occurrences) — an exact 1:1 correlation,
confirming zero double-counting and zero leakage into the deliberately-excluded
`CAUGHT_FLEEING`/`PURSUIT_ABANDONED` outcomes.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/observability/ tests/simulation_quality/test_combat_scorer.py -q`
