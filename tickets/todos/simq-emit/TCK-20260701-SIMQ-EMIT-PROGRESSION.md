---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-PROGRESSION
phase: open
date: 2026-07-01
tags: [simq, event-emission, progression, scoring]
---

# TCK-20260701-SIMQ-EMIT-PROGRESSION

## Title
SimQ: Emit PROGRESSION pillar signal events from engine

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The PROGRESSION pillar scorer has complete scoring infrastructure for 5 event types that
the engine never emits. These are the richest remaining signal gap for PROGRESSION: current
calibration shows PROGRESSION=C in most worlds (A only in combat-heavy dungeon_crawl /
frontier_extended where xp_granted and level_up fire at high rate). Adding the missing
progression signals would make PROGRESSION sensitive to skill and trait advancement, not
only raw XP accumulation.

Missing events (from `docs/simulation_quality/event_type_coverage.md §3.6`):
- `skill_unlocked` — no engine emitter found
- `trait_expressed` — no engine emitter found
- `pillar_trait_unlocked` — no engine emitter found
- `progression_conversion_applied` — no engine emitter found
- `progression_plateau_detected` — no engine emitter found

## Scope
1. Investigate where skill acquisition, trait expression, and progression conversion occur
   in the engine (likely `src/domains/progression/`, `src/engine/apply.py`,
   `src/systems/strategic_systems/intelligence.py`, or `src/core/state.py` attribute diffs)
2. Add `skill_unlocked` emitter: fires when an entity gains a new skill entry that was not
   previously present (detect via state diff on `AttributeComponent.skills`)
3. Add `trait_expressed` emitter: fires when a trait's expression fires and produces a
   measurable behavioral modifier (detect via `PersonalityComponent` active-trait-trigger events
   or mood threshold crossings; see TCK-20260627-P2O-ENTITY-PERSONALITY-OBS for snapshot hook)
4. Add `pillar_trait_unlocked` emitter: fires when an entity's class pillar trait becomes
   active (check `AttributeComponent.pillar_trait` state diff)
5. Add `progression_conversion_applied` emitter: fires when XP is converted to a permanent
   stat increase (find conversion logic in progression domain)
6. Add `progression_plateau_detected` emitter: fires when an entity's XP accumulation rate
   drops below a threshold for N consecutive ticks (requires lightweight per-entity
   accumulation rate tracker)
7. Wire all new event types through `event_extractor.py` or the appropriate domain emitter
8. Update `docs/simulation_quality/event_type_coverage.md §3.6` to remove resolved gaps
9. Add unit tests: each emitter fires under the correct condition and produces correct payload
10. Run calibration on dungeon_crawl and frontier_extended — verify PROGRESSION grade moves

## Out of Scope
- Changing ProgressionScorer thresholds or scoring weights
- Adding new progression mechanics to the engine
- Modifying AttributeComponent or skill schemas

## Acceptance Criteria
- [ ] All 5 event types emitted by the engine under correct conditions
- [ ] Each event reaches ProgressionScorer (verify via unit test)
- [ ] `event_type_coverage.md §3.6` updated — 5 entries removed from emission gaps
- [ ] Calibration: at least one world shows PROGRESSION grade improvement in a 500-tick run
- [ ] No regression in existing progression tests

## Related Tickets
- TCK-20260629-SIMQ-EMIT-STATE-DIFF — prior state-diff emitter work (reference pattern)
- TCK-20260629-SIMQ-EMIT-COGNITION — prior emit ticket (lead_certainty_changed pattern)
- TCK-20260627-P2O-ENTITY-PERSONALITY-OBS — personality snapshot hook (trait_expressed reference)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.6` — gap definitions
- `docs/simulation_quality/quality_scoring_contract.md §5` — ProgressionScorer contract
- `docs/mechanics/01_entity_anatomy.md` — XP scaling and attribute definitions

## Related Code Areas
- `src/simulation_quality/scorers/progression_scorer.py` — EVENT_TYPES tuple
- `src/observability/event_extractor.py` — where most state-diff emitters live
- `src/domains/progression/` — progression domain logic
- `src/core/state.py AttributeComponent` — skill, pillar_trait fields

## Assumptions / Open Questions
- `progression_plateau_detected` requires a per-entity XP rate tracker. Simplest approach:
  store `last_xp_grant_tick` on entity and flag as plateau if delta > 50 ticks with no XP.
  Confirm this fits within state.py durable state rules before implementing.
- `trait_expressed` definition is ambiguous — clarify with personality snapshot whether
  "expressed" means mood threshold crossed or active-trait-modifier applied.

## Implementation Notes
- Follow the pattern from TCK-20260629-SIMQ-EMIT-STATE-DIFF: read state before/after apply,
  diff fields, emit events for non-zero deltas
- `skill_unlocked` and `pillar_trait_unlocked` are binary (present/absent in snapshot):
  emit once on first appearance, not on every tick the skill exists
- Payload should include: `entity_id`, `skill_id`/`trait_id`, `tick`, `source` (reason for unlock)

## Test Summary
- Unit: each emitter fires exactly once under correct condition, not on repeat ticks
- Unit: payload fields match ProgressionScorer expected schema
- Integration: dungeon_crawl 200-tick run produces > 0 skill_unlocked events
- Regression: existing 141 worldassembly + progression tests pass

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
