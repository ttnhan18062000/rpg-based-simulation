---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-NARRATIVE
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, narrative, quest]
---

# TCK-20260629-SIMQ-EMIT-NARRATIVE

## Title
SimQ: Emit NARRATIVE Pillar Events — Quest, Chronicle, Emergence, and Scenario Hooks

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The NARRATIVE pillar scores 10 event types. `quest_started`, `quest_completed`,
`quest_failed` are partially covered by the translation layer (TCK-20260629-SIMQ-EVENT-TRANSLATE
remaps `quest_event` by payload status). The remaining 7 types — `chronicle_entry_created`,
`world_emergence_event`, `narrative_milestone`, `scenario_objective_progressed`,
`scenario_objective_completed`, `scenario_stalled`, `hero_death_unrecorded` — require
direct emission hooks in PP-23 (world_emergence), PP-24 (quest_rewards), PP-33 (lifecycle),
and the NarrativeLedger.

A known gap (documented in NarrativeScorer docstring): `chronicle_entry_created` is emitted
by the NarrativeLedger to disk-JSONL only, not to the event bus. This ticket must wire the
NarrativeLedger to also emit `chronicle_entry_created` to EventRecorder.

## Scope
**Events to emit and their source sites:**

| Event type | Source | Trigger |
|---|---|---|
| `quest_started` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `quest_completed` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `quest_failed` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `chronicle_entry_created` | `NarrativeLedger.record()` | Chronicle entry written to disk — add simultaneous EventRecorder call |
| `world_emergence_event` | PP-23 | World emergence threshold crossed |
| `narrative_milestone` | PP-23 / PP-08 / PP-33 | First war declaration, first boss kill, first sovereignty transfer |
| `scenario_objective_progressed` | Scenario runtime (PP-23 or ScenarioRuntimeService) | Scenario objective incremented |
| `scenario_objective_completed` | Scenario runtime | Scenario objective fully completed |
| `scenario_stalled` | Scenario runtime | Scenario has had zero progress for N ticks |
| `hero_death_unrecorded` | PP-33 lifecycle | Hero-class entity died with no chronicle entry this tick |

**Chronicle gap fix (critical):** `NarrativeLedger` currently writes to
`chronicle_entries.jsonl` via disk-only path. Add an optional `event_recorder` parameter to
`NarrativeLedger.__init__()` or `NarrativeLedger.record()` — when provided, also calls
`event_recorder.record(chronicle_entry_created_event)`. Kernel wires this at NarrativeLedger
construction time.

**`hero_death_unrecorded` detection:** In PP-33, after a hero-class entity lifecycle event,
check whether the NarrativeLedger received a chronicle entry for this entity in the current
tick. If not, emit `hero_death_unrecorded`.

## Out of Scope
- Quest system logic changes (only event emission hooks)
- Changing NarrativeLedger disk output format

## Acceptance Criteria
- [ ] `chronicle_entry_created` emitted from NarrativeLedger when entry written to disk
- [ ] `world_emergence_event` emitted from PP-23 at emergence threshold
- [ ] `narrative_milestone` emitted for first war, first boss kill, first sovereignty transfer
- [ ] `scenario_objective_progressed`, `scenario_objective_completed`, `scenario_stalled`
  emitted from ScenarioRuntimeService
- [ ] `hero_death_unrecorded` emitted from PP-33 when hero dies without chronicle entry
- [ ] `quest_started` / `quest_completed` / `quest_failed` confirmed working from translation
  layer (assert non-zero in calibration run)
- [ ] NarrativeLedger `event_recorder` wiring is optional (None-safe) — not required for tests
  that don't use EventRecorder
- [ ] No import of `src/simulation_quality/` from any narrative phase
- [ ] NARRATIVE pillar shows non-zero events in calibration run (including quest events from translation)

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite — quest translation must be in place)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 NARRATIVE
- NARRATIVE scorer docstring at `src/simulation_quality/scorers/narrative.py` — documents chronicle gap

## Related Code Areas
- `src/domains/chronicle/` (NarrativeLedger)
- PP-23 (world_emergence), PP-24 (quest_rewards), PP-33 (lifecycle)
- `src/engine/scenario_runtime.py` (ScenarioRuntimeService — scenario objective tracking)
- `src/observability/events.py` — may need new event classes

## Assumptions / Open Questions
- `NarrativeLedger.record()` has a clear call site that can accept an optional event_recorder
- `ScenarioRuntimeService` has objective progress tracking with discrete "progressed" and
  "completed" outcome states
- `hero_death_unrecorded` detection in PP-33 requires knowing whether NarrativeLedger was
  called for this entity this tick — may need a set of "chronicled this tick" entity IDs
  passed between PP-23 and PP-33
- `narrative_milestone` "first X" events require run-level tracking of whether the milestone
  has already fired — use a stateful set in the PP-23 phase or kernel-level milestone tracker
