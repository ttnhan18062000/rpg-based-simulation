---
ticket_id: TCK-20260619-E31-SCENARIO-RUNTIME
phase: investigation
date: 2026-06-20
---

# Investigation: Scenario Runtime Service

## Current State (verified 2026-06-20)

### Checkpoint infrastructure — `src/engine/checkpoint.py:L200`
`CanonicalHashScheduler` exists and stores `state.rng_checkpoint` (L105). This is hash-based state tracking, not full-state serialization. Checkpoint/restore of full `AuthoritativeState` requires a separate serialization path.

### CampaignRunner — `src/domains/campaigns/runner.py:L29`
Exists but is analysis-only (isolated shadowed state, no `Failed` state, no live `AuthoritativeState`). Per E32: must be renamed `SimulationAnalysisRunner` before E32 starts. E31 does NOT rename it (E32 does).

### ScenarioRuntimeService
Does NOT exist. No start/pause/resume/step/abort API. No `ScenarioObjectiveState` (RUNNING/OBJECTIVE_MET/OBJECTIVE_FAILED/STALLED/ABORTED).

### Scenario spec — `victory_conditions`
No `victory_conditions` array in current scenario YAML schema (E13D schema investigation: `id`, `world_composition`, `focus_modules`, `perspective`, `initial_conditions`). E31A must extend scenario schema.

### REST API
No `/api/v1/scenarios/{id}/status`, `/checkpoint`, `/restore` endpoints exist.

## Gap Summary

| Gap | Size |
|---|---|
| `ScenarioRuntimeService` class missing | ~80 lines |
| Objective state machine (5 states) missing | ~40 lines |
| `victory_conditions` in scenario YAML missing | schema extension |
| Full-state checkpoint serialization missing | ~50 lines |
| 3 REST endpoints missing | ~60 lines |
