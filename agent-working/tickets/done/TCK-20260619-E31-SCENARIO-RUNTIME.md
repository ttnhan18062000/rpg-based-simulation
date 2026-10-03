---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31-SCENARIO-RUNTIME
phase: done
date: 2026-06-19
tags: [scenario-runtime, checkpoint, objective-state, service-api, gameplay-loop, epic, phase-3]
---

# TCK-20260619-E31-SCENARIO-RUNTIME

## Title
Epic 3.1 · Scenario Runtime Service

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Only `CampaignRunner` (analysis-only) and sweep/CI batch runs exist. Neither has objective/win-loss-stall state, pause/resume, or checkpoint. There is no interactive product-shaped execution loop. This epic builds the service layer that turns the kernel into a controllable, inspectable scenario runner.

Score: 7/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § D

## Scope
- `ScenarioRuntimeService`: owns a running `Kernel` instance; exposes start/pause/resume/step/abort
- Objective state machine: `RUNNING → OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED / ABORTED`; stall detector fires when no meaningful events for N ticks
- Win/loss conditions defined in scenario spec (`victory_conditions` array in scenario YAML)
- Checkpoint system: serialize `AuthoritativeState` + RNG state to named checkpoint file; restore from checkpoint on resume
- REST API:
  - `GET /api/v1/scenarios/{id}/status` — live objective state, tick count, alive entity count, key metrics
  - `POST /api/v1/scenarios/{id}/checkpoint` — write checkpoint
  - `POST /api/v1/scenarios/{id}/restore/{checkpoint}` — restore
- Replay mode: run from checkpoint with different seed to explore counterfactuals
- Child tickets: (a) ScenarioRuntimeService + kernel lifecycle, (b) objective state machine, (c) checkpoint/restore, (d) REST API

## Out of Scope
- Multi-scenario campaign orchestration (Epic 3.2 — uses this as its execution primitive)
- Scenario UI / real-time streaming
- Player agency / interactive decision points

## Acceptance Criteria
- A scenario started via API reaches OBJECTIVE_MET or OBJECTIVE_FAILED state
- A scenario can be paused mid-run and resumed with identical subsequent outcomes
- A checkpoint/restore cycle produces the same outcomes as an uninterrupted run (determinism preserved)

## Related Tickets
- TCK-20260619-E23-QUEST-GENERATION (prerequisite: scenario needs meaningful objectives)
- TCK-20260619-E32-CAMPAIGN-RUNTIME (depends on this as execution primitive)

## Related Docs
- `docs/plans/long_term_development_roadmap.md` § Epic 3.1
- `docs/engine/kernel.md` (Kernel lifecycle — update to note ScenarioRuntimeService as the owning wrapper for production use)
- `docs/engine/authoritative_mutation_pipeline_contract.md`
- `docs/core/state.md` (checkpoint serializes full `AuthoritativeState` — immutability law must be preserved through serialize/restore cycle; read before designing checkpoint format)
- `docs/simulation/domains/campaigns_contract.md` (update boundary table — ScenarioRuntimeService is a new concept separate from CampaignRunner)
- `docs/parity_ledger/infrastructure.yaml` (checkpoint/replay entries — update to `verified` once checkpoint/restore implemented)
- New doc: `docs/engine/scenario_runtime_contract.md` (ScenarioRuntimeService lifecycle, objective state machine, checkpoint format, REST API contract)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260612-DOMAINS-ARCH-MAP/`
- `stored_artifacts/TCK-20260619-E31-SCENARIO-RUNTIME/`

## Related Code Areas
- `src/engine/kernel.py:L34` (Kernel)
- `src/engine/checkpoint.py:L200` (CanonicalHashScheduler — existing checkpoint infrastructure)
- `src/domains/campaigns/runner.py` (CampaignRunner — reference for pattern; will be renamed in Epic 3.2)
- `src/lab/workflows.py:L74` (GenerateSimulationSetupWorkflow — reference)

## Assumptions / Open Questions
- Does `CanonicalHashScheduler` already support full-state checkpoint serialization, or does it only hash? Read `src/engine/checkpoint.py` before implementing
- Where does the REST API layer live? Find existing FastAPI/Flask entrypoint before adding routes

## Implementation Notes
`CampaignRunner` in `src/domains/campaigns/runner.py` is analysis-only (shadowed state, no Failed state). `ScenarioRuntimeService` is a different concept — it owns live `AuthoritativeState`. Do not extend `CampaignRunner` for this; create a separate service. Epic 3.2 will rename `CampaignRunner` to `SimulationAnalysisRunner` to resolve the naming collision.

After implementation: create `docs/engine/scenario_runtime_contract.md` documenting the service lifecycle, objective state machine, checkpoint format, and REST API contract. Update `docs/simulation/domains/campaigns_contract.md` boundary table to add `ScenarioRuntimeService`. Update `docs/parity_ledger/infrastructure.yaml` checkpoint entries. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/integration/scenarios/test_scenario_runtime_service.py`:
  - `test_scenario_reaches_objective_met()` — configure a simple victory condition; run via service; assert OBJECTIVE_MET state
  - `test_scenario_pause_resume_identical_outcome()` — pause at tick 50, resume; assert same subsequent events as uninterrupted run
  - `test_checkpoint_restore_determinism()` — checkpoint at tick 50, restore to fresh service, run to tick 100; assert identical events to non-checkpoint run
  - `test_stall_detector_fires_on_no_events()` — run with all entities frozen; assert STALLED after N ticks
- New file `tests/api/test_scenario_runtime_api.py`:
  - `test_status_endpoint_returns_live_state()` — GET status mid-run; assert tick_count and alive_entity_count non-zero

## Files Changed
- `tickets/todos/TCK-20260619-E31A-SCENARIO-SERVICE.md` (new child ticket)
- `tickets/todos/TCK-20260619-E31B-OBJECTIVE-FSM.md` (new child ticket)
- `tickets/todos/TCK-20260619-E31C-CHECKPOINT.md` (new child ticket)
- `tickets/todos/TCK-20260619-E31D-REST-API.md` (new child ticket)
- `staging_artifacts/TCK-20260619-E31-SCENARIO-RUNTIME/investigation.md` (new)
- `staging_artifacts/TCK-20260619-E31-SCENARIO-RUNTIME/plan.md` (new)
- `staging_artifacts/TCK-20260619-E31-SCENARIO-RUNTIME/test_plan.md` (new)

## Completion Summary
Epic scoped into 4 child tickets (E31A → E31B → E31C → E31D). Key finding: `CanonicalHashScheduler` is hash-only — full-state serialization must be added in E31C. E31A creates `ScenarioRuntimeService` wrapping `Kernel`; E31B adds `ObjectiveEvaluator` + stall detector (STALL_THRESHOLD=50 ticks); E31C adds `ScenarioCheckpointer.save/load` with JSON serialization of `AuthoritativeState + rng_checkpoint`; E31D adds 3 REST endpoints in `src/api/routes/scenarios.py`.
