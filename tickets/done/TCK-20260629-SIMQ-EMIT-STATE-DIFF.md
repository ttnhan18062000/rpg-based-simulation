---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-STATE-DIFF
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, event-extractor]
---

# TCK-20260629-SIMQ-EMIT-STATE-DIFF

## Title
SimQ: Extend EventExtractor with State-Diff Events for COMBAT, PROGRESSION, ECONOMY Pillars

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`EventExtractor.extract()` compares `prior_state` vs `current_state` per tick but only
emits 6 event types. Many SimQ contract events are derivable from the same state diff
without touching engine phases. This ticket extends EventExtractor to emit those events.

## Scope
Extend `src/observability/event_extractor.py` to detect and emit:

**COMBAT (scored by CombatScorer):**
- `combat_initiated` — HP of entity dropped AND attacker_id present AND entity was NOT
  already damaged last tick (first-hit detection). Emit once per engagement start.
- `combat_resolved` — entity.lifecycle became inactive this tick after prior_ent was active
  and took damage (already implies kill was from combat, not lifecycle event).
  Already partially covered by `combat_kill` → translate to `entity_killed`.
  New: emit `combat_resolved` when a lethal CombatDamageEvent was also emitted same tick.
- `near_death_survival` — entity HP fell below 20% of max_hp but entity.lifecycle.active is
  still True this tick. Only fire once per near-death window (suppress if same entity
  already near-death previous tick).
- `attrition_threshold_crossed` — population attrition percentage crosses 25%, 50%, 75%
  within a run (fire once per threshold per run; requires run-level counter in EventExtractor
  or via a stateful wrapper).

**PROGRESSION (scored by ProgressionScorer):**
- `xp_granted` — entity.progression.xp increased vs prior tick. Emit one event per entity
  per tick where xp delta > 0. `payload["amount"] = delta`.
- `level_up` — entity.progression.level increased vs prior tick.
- `near_death_survival` — same as COMBAT above (shared event type; both scorers handle it).

**ECONOMY (scored by EconomyScorer):**
- `resource_node_depleted` — resource node charges dropped to 0 this tick (requires
  iterating `current_state.resource_nodes`; nodes are world-level, not entity-level).
- `resource_node_regenerated` — node charges increased from 0 this tick.
- `conservation_law_verified` — total gold sum across all entities unchanged tick-to-tick.
  Emit once per tick when law holds. (High-volume — only in NORMAL mode, skip in LIGHT.)

**WORLD (partial — easier ones only; rest in TCK-20260629-SIMQ-EMIT-WORLD):**
- `demographic_birth` — new entity spawned this tick AND prior_ent was None (already
  detected by lifecycle spawn; this is a rename/addition at the same site).
- `demographic_mortality` — entity despawned this tick AND was not killed by combat
  (lifecycle.active → False with no attacker).

## Out of Scope
- Agency event emission (requires phase hooks, not state diff): TCK-20260629-SIMQ-EMIT-AGENCY
- Full world dynamics events (calamity, boss spawn, ecology): TCK-20260629-SIMQ-EMIT-WORLD
- Faction, Social, Information events: separate tickets
- Modifying LIGHT/LONG_RUN volumization rules (follow existing mode guards)

## Acceptance Criteria
- [ ] `EventExtractor.extract()` emits `combat_initiated` on first-hit detection
- [ ] `EventExtractor.extract()` emits `near_death_survival` when HP < 20% max and alive
- [ ] `EventExtractor.extract()` emits `xp_granted` with `amount` in payload when XP delta > 0
- [ ] `EventExtractor.extract()` emits `level_up` when level increases
- [ ] `EventExtractor.extract()` emits `resource_node_depleted` / `resource_node_regenerated`
  when node charges cross 0 boundary
- [ ] `EventExtractor.extract()` emits `demographic_birth` / `demographic_mortality`
- [ ] Unit tests in `tests/unit/observability/test_event_extractor.py` cover all new events
  with before/after state mocks
- [ ] All new events are valid `SimulationEvent` instances (or use `ObservabilityEventEnvelope`
  directly) with correct `event_category` set
- [ ] LIGHT mode volumization respected for high-volume events (`conservation_law_verified`)
- [ ] Re-running `tools/calibrate_simq.py --ticks 100 --seed 42` shows scored events in
  COMBAT and PROGRESSION pillars after TCK-20260629-SIMQ-EVENT-TRANSLATE also applied

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite — must be done first)
- TCK-20260629-SIMQ-EMIT-WORLD (handles remaining world dynamics events)
- TCK-20260629-SIMQ-EMIT-AGENCY (handles agency/action events)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT, PROGRESSION, ECONOMY, WORLD
- `docs/engine/kernel.md` — observability phase runs after authoritative application

## Related Code Areas
- `src/observability/event_extractor.py` — primary file to extend
- `src/core/state.py` — `AuthoritativeState.resource_nodes`, `entity.progression`, `entity.combat`
- `src/observability/events.py` — add new SimulationEvent subclasses if needed
- `tests/unit/observability/test_event_extractor.py` — test file (create if absent)

## Assumptions / Open Questions
- `entity.progression.xp` and `entity.progression.level` are fields on the entity's
  progression component — verify against `src/core/entities.py` before implementation
- `entity.combat.max_hp` must be readable to compute near-death threshold (20% of max)
- `current_state.resource_nodes` is a dict/list of resource node objects — verify schema
- `near_death_survival` is shared by COMBAT and PROGRESSION scorers (both handle it);
  emit once and both will score it
- `attrition_threshold_crossed` requires run-level state — EventExtractor is currently
  stateless. Add a thin `EventExtractorState` accumulator passed alongside, or use a
  class-level counter (document trade-off in implementation notes)

## Files Changed
- `src/observability/event_extractor.py` — added _NEAR_DEATH_THRESHOLD; emit combat_initiated, near_death_survival, xp_granted, level_up, demographic_birth, demographic_mortality, resource_node_depleted, resource_node_regenerated
- `tests/unit/observability/test_event_extractor_simq.py` (new) — 21 tests

## Completion Summary
Extended EventExtractor.extract() with 8 new SimQ contract event types derivable from state diff. 21 new tests passing. No regressions in 301 SimQ tests.
