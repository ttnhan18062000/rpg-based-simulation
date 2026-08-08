---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS

## Ordered Steps

1. Add `WorldDynamicsShaper` to `src/observability/event_shapers.py`, register in
   `PHASE2_SHAPER_REGISTRY`. No `reset_run_state()` needed (no per-run state).
   - Files: `src/observability/event_shapers.py`
2. Verify via real, non-mocked kernel runs across 3 worlds: default (no leak), `SHADOW`
   (constructs, 0 WorldDynamics-specific deliveries), `ON` (exact parity per event type that
   fired).
   - No file changes.
3. Add unit tests per event (fire + non-fire) in
   `tests/unit/observability/test_event_shapers_world_dynamics.py`.
   - Files: `tests/unit/observability/test_event_shapers_world_dynamics.py` (new)
4. Update `docs/parity_ledger/world_dynamics.yaml` (new entry) and `infrastructure.yaml`
   (`INFRA-324`, update in place — closes the `demographic_mortality` deferral).
   - Files: as listed.

## Files to Change

- `src/observability/event_shapers.py`
- `tests/unit/observability/test_event_shapers_world_dynamics.py` (new)
- `docs/parity_ledger/world_dynamics.yaml`, `infrastructure.yaml`

## Scope Guards

- Do NOT touch `event_extractor.py`'s old branches — Cutover's job.
- Do NOT touch `resource_node_depleted`/`resource_node_regenerated`/`node_recharged`/
  `conservation_law_verified`/`faction_extinct` — Child 6's scope (genuinely needs new
  instrumentation).
- Do NOT touch `StrategyShaper`/`ProgressionShaper`/Phase 1 shapers.

## Dependency Map

Steps 1-2 coupled (verification is part of building it correctly). Step 3 depends on 1. Step 4
depends on all prior steps.

## Acceptance Criteria Map

- AC "field mapping confirmed with citations" → investigation.md's table
- AC "WorldDynamicsShaper implements all 15 events" (14 distinct types, `narrative_milestone`
  fires from 2 sites) → step 1
- AC "unit tests cover fire + non-fire per event" → step 3
- AC "real kernel run confirms correctly-shaped SHADOW output" → step 2
- AC "parity ledger updated; INFRA-324 updated in place" → step 4
