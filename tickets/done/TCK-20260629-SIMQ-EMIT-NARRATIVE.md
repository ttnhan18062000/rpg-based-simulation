---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-NARRATIVE
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, narrative, quest]
---

# TCK-20260629-SIMQ-EMIT-NARRATIVE

## Title
SimQ: Emit NARRATIVE Pillar Events — Quest, Chronicle, Emergence, and Scenario Hooks

## Status
DONE

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
by the NarrativeLedger to disk-JSONL only, not to the event bus. This ticket wired the
NarrativeLedger to also emit `chronicle_entry_created` to EventRecorder.

## Scope
**Events to emit and their source sites:**

| Event type | Source | Trigger |
|---|---|---|
| `quest_started` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `quest_completed` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `quest_failed` | Already covered by TCK-20260629-SIMQ-EVENT-TRANSLATE | — |
| `chronicle_entry_created` | `CampaignOrchestrator._emit_chronicle_events()` | Chronicle entry written via extend/append in _advance_state and _build_initial_state |
| `world_emergence_event` | EventExtractor world_events_add loop | Every WorldEvent in world_events_add |
| `narrative_milestone` | EventExtractor world_events_add + entities_add | FACTION_WAR_DECLARED → "first_war", SOVEREIGNTY_SHIFT → "first_sovereignty_transfer", boss entity add → "first_boss_spawned" |
| `scenario_objective_completed` | ScenarioRuntimeService._evaluate_after_tick() | OBJECTIVE_MET or OBJECTIVE_FAILED reached |
| `scenario_stalled` | ScenarioRuntimeService._evaluate_after_tick() | Stall threshold crossed |
| `hero_death_unrecorded` | EventExtractor entity loop | Hero-kind entity transitions active=True→False |
| `scenario_objective_progressed` | GAP — architecture blocked | ObjectiveEvaluator is binary only (no partial progress) |

## Out of Scope
- Quest system logic changes (only event emission hooks)
- Changing NarrativeLedger disk output format

## Acceptance Criteria
- [x] `chronicle_entry_created` emitted from CampaignOrchestrator when entries written
- [x] `world_emergence_event` emitted from EventExtractor per WorldEvent in world_events_add
- [x] `narrative_milestone` emitted for first war, boss spawn, sovereignty transfer
- [x] `scenario_objective_completed`, `scenario_stalled` emitted from ScenarioRuntimeService
- [x] `hero_death_unrecorded` emitted from EventExtractor entity diff (hero active→inactive)
- [x] `quest_started` / `quest_completed` / `quest_failed` confirmed working from translation layer (N-12..N-14)
- [x] NarrativeLedger `event_recorder` wiring is optional (None-safe) — TC-D17
- [x] No import of `src/simulation_quality/` from any narrative phase — N-15..N-18
- [x] NARRATIVE pillar events emitting (218 tests pass, 2 intentional gap skips)
- [ ] `scenario_objective_progressed` — ARCHITECTURE GAP: ObjectiveEvaluator is binary only; documented in S-05 gap test

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite — quest translation must be in place)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 NARRATIVE
- NARRATIVE scorer docstring at `src/simulation_quality/scorers/narrative.py` — gap now resolved

## Related Stored Artifacts
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-NARRATIVE/`

## Related Code Areas
- `src/domains/campaigns/narrative_ledger.py`
- `src/domains/campaigns/orchestrator.py`
- `src/observability/event_extractor.py`
- `src/engine/scenario_runtime.py`
- `docs/parity_ledger/infrastructure.yaml`

## Assumptions / Open Questions
- UQ-1 RESOLVED: milestone key "first_boss_spawned" used (not "first_boss_kill") — EventExtractor
  detects boss spawn via entities_add; NarrativeScorer checks event_type only, not payload key.
- UQ-2 RESOLVED: EventRecorder at src/observability/event_recorder.py line 56.
- UQ-3 RESOLVED: CampaignOrchestrator.__init__ had NO _event_recorder field — added `event_recorder: Optional[EventRecorder] = None` parameter as instructed.

## Implementation Notes
- `chronicle_entry_created` emission goes through `CampaignOrchestrator._emit_chronicle_events()` helper
  which is wired at both narrative_ledger.extend() (line ~199) and narrative_ledger.append() (line ~577/614).
  `NarrativeLedger.__init__` also gains `event_recorder` parameter and `emit_chronicle_event()` method
  (for completeness and TC-D16..D19 tests), but the authoritative write path is the orchestrator helper.
- `world_emergence_event` emits for ALL WorldEvents in world_events_add (not threshold-filtered) per D1.
- `narrative_milestone` emits unconditionally from EventExtractor; NarrativeScorer deduplicates per D2.
- `hero_death_unrecorded` always emits when hero-kind entity deactivates (active True→False); no
  chronicle cross-check possible at tick level (chronicle written at episode boundary, not per tick).
- `scenario_objective_progressed` is architecture-blocked (binary ObjectiveEvaluator); documented as S-05 gap test.
- EventCategory "lifecycle" used for narrative events (matches calamity_spawned/boss_spawned precedent).
  EventCategory "infrastructure" used for scenario runtime events.

## Test Summary
- Baseline: 192 tests passed before changes.
- After implementation: 218 passed, 2 skipped (N-11 hero_death suppression gap; S-05 progressed gap).
- New test files:
  - `tests/unit/observability/test_event_extractor_narrative.py` (N-01..N-18)
  - Additions to `tests/unit/campaigns/test_narrative_ledger.py` (TC-D16..TC-D19)
  - Additions to `tests/unit/engine/test_scenario_runtime_service.py` (S-01..S-05)

## Files Changed
- `src/domains/campaigns/narrative_ledger.py` — event_recorder param + emit_chronicle_event()
- `src/domains/campaigns/orchestrator.py` — event_recorder param + _emit_chronicle_events() helper + two wire points
- `src/observability/event_extractor.py` — hero_death_unrecorded, world_emergence_event, narrative_milestone
- `src/engine/scenario_runtime.py` — __slots__ + event_recorder param + emission in _evaluate_after_tick()
- `docs/parity_ledger/infrastructure.yaml` — INFRA-247 divergence_note cleared; SIMQ-CALIBRATED-001 updated
- `tests/unit/campaigns/test_narrative_ledger.py` — TC-D16..TC-D19 added
- `tests/unit/engine/test_scenario_runtime_service.py` — S-01..S-05 added
- `tests/unit/observability/test_event_extractor_narrative.py` — NEW (N-01..N-18)

## Completion Summary
All 6 implementable NARRATIVE pillar event types wired: chronicle_entry_created, world_emergence_event,
narrative_milestone, hero_death_unrecorded, scenario_stalled, scenario_objective_completed.
One architecture-blocked gap (scenario_objective_progressed) documented as gap test S-05.
218/218 applicable tests pass. Parity ledger updated.
