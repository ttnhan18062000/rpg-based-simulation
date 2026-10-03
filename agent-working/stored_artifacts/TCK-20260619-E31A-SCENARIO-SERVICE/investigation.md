---
status: active
artifact_type: investigation
ticket_id: TCK-20260619-E31A-SCENARIO-SERVICE
date: 2026-06-20
---

# Investigation: TCK-20260619-E31A-SCENARIO-SERVICE

## Current Behavior (file:line refs)

### Kernel (`src/engine/kernel.py:L35`)
- `Kernel.__init__` takes: `profile: RuntimeProfile`, `state: AuthoritativeState`, `rng: DeterministicRNG`, plus optional `scheduler`, `governor`, `status`, `replay`, `executor`, `flags`, `run_id`, and several path strings.
- `Kernel.tick_once()` (L278): the main tick dispatch; calls `_tick_once_inner()` which runs 6 phases: init, scheduling, collection, resolution, cleanup, advancement, persistence.
- `Kernel.shutdown(timeout_s=5.0)` (L827): sets `_stopped = True`, drains workers, finalises replay, updates manifest. Returns `ShutdownResult`.
- `Kernel._stopped` (L74): checked at the top of `tick_once()` — if `True`, returns immediately. This is the only built-in "halt" mechanism.
- **No native pause/resume**: Kernel has no `pause()` or `resume()` method. The service must manage the tick loop externally.
- **`kernel.state` property** (L957): returns the current `AuthoritativeState`. Safe to call post-tick.
- **`kernel.state.entities`**: dict of `entity_id → EntityState`. `alive_entity_count` can be derived as `len(kernel.state.entities)`.

### CampaignRunner pattern (`src/domains/campaigns/runner.py:L29`)
- Constructs `Kernel(profile, state, rng, flags=...)`, runs `for tick in range(1, spec.ticks+1): kernel.tick_once()`, calls `kernel.shutdown()`. This is the reference pattern for external tick loop control.
- No threading — uses a simple synchronous loop. The service should follow the same approach (synchronous, no thread management).

### SimulationScenarioDefinition (`src/scenarios/schema.py:L20`)
- Frozen Pydantic model with `extra="forbid"`. Fields: `id`, `display_name`, `world_composition`, `perspective`, `focus_modules`, `initial_conditions`, `setup_tags`, `template_id`.
- **No `victory_conditions` field** — this needs to be added.
- The `initial_conditions` validator rejects unknown categories. Adding `victory_conditions` as a top-level field (not inside `initial_conditions`) avoids touching the validator.
- `ALLOWED_INITIAL_CONDITION_CATEGORIES` (L8) must NOT be expanded — `victory_conditions` is a separate named field.

### Scenario YAML files (`data/content/simulation_scenarios/*.yaml`)
- Current structure: `id`, `world_composition`, `focus_modules`, `perspective`, `initial_conditions`.
- `victory_conditions` is not present in any existing scenario YAML.
- Adding it as an optional field (with `Optional[List[VictoryCondition]] = None`) means existing YAMLs continue to parse without error.

### Existing enums (`src/core/enums.py`)
- Contains `EntityRole`, `Faction`, `Direction`, `MovementIntention`, `ActionType`, `ActionStyle`, `ReasonCode`, `Domain`.
- No scenario-state enum exists. `ScenarioObjectiveState` should live in `src/engine/scenario_runtime.py` to keep engine-layer concerns co-located.

### ObjectiveState (`src/core/strategic.py:L214`)
- A different `ObjectiveState` class exists in strategic.py — this is for individual entity strategic objectives. The new `ScenarioObjectiveState` is a top-level scenario-execution concept, distinct enough to not conflict.

### Test patterns (`tests/unit/engine/test_lifecycle_supervisor.py`)
- `_make_kernel()` helper creates a minimal Kernel with `AuthoritativeState(tick=0, seed=42)` and `flags={"no_replay": True}`.
- `_make_profile()` uses `RuntimeProfile(name=..., hardware_class=HardwareClass.CLASS_B, ...)`.
- Tests use `k.shutdown()` after running ticks. Same pattern applies to `ScenarioRuntimeService`.

### ScenarioRunner (`src/testing/scenario_runner.py:L8`)
- An older, lower-level runner that parses YAML directly and drives `ApplyPath` without a full Kernel. This is NOT the reference pattern for the new service. Use `CampaignRunner` pattern instead.

## Mechanics / Engine Constraints

- **Kernel 6-phase loop** (`docs/engine/kernel.md`): Init → Scheduling → Collection → Resolution → Cleanup → Advancement → Persistence. The service wraps `tick_once()` — it does not reach inside phases.
- **Durable state rule**: The service reads `kernel.state` read-only to derive `alive_entity_count`. It never mutates state directly.
- **Authoritative pipeline**: All state mutation goes through `kernel.tick_once()` which calls `AuthoritativeApplyPipeline.refine()` internally.
- **No threading required**: Kernel tick is synchronous. `pause()` simply stops calling `tick_once()`. `resume()` restarts the call loop. No threads, no locks.

## Parity Ledger Overlap

- **INFRA-003** (`infrastructure.yaml`): `test_rng` — kernel init uses RNG. Verified. Not affected.
- **INFRA-004** (`infrastructure.yaml`): `test_entity` — entity state. Not affected by this ticket.
- No existing parity entry covers `ScenarioRuntimeService` — a new entry (INFRA-118) will be added upon completion.

## Prior Work

- **TCK-20260609-SCENARIO-SETUP-RESOLVER** (done): `ScenarioSetupResolver` converts `SimulationScenarioDefinition` → `ResolvedScenarioSetup`. The service wraps a spec, not a resolver — resolver is downstream.
- **TCK-20260610-SCENARIO-WORLD-VALIDATION** (done): `ScenarioWorldFeatureValidator`. Out of scope for this ticket.
- **TCK-20260619-E13D-SCENARIOS** (stored_artifacts): Established that `victory_conditions` is NOT currently in the YAML schema. Confirmed `SimulationScenarioDefinition` is the right place to extend.

## Risks and Open Questions

1. **Kernel construction requires real state/rng**: In tests, `ScenarioRuntimeService.start()` must build these. The service should accept an optional `kernel_factory` callable or build the Kernel internally using a lightweight state. Resolved: build Kernel internally using `AuthoritativeState(tick=0, seed=0)` and a mock-friendly RNG (tests can inject via `_kernel` override or factory).
2. **`ScenarioSpec` vs `SimulationScenarioDefinition`**: The ticket uses `ScenarioSpec` in the class signature but this type does not exist. The correct type is `SimulationScenarioDefinition`. The service's `__init__` should accept `SimulationScenarioDefinition`.
3. **Kernel construction complexity**: `Kernel.__init__` needs `profile`, `state`, `rng`. For the service's `start()`, use the same minimal pattern as `CampaignRunner`: build a `RuntimeProfile`, `AuthoritativeState`, and `DeterministicRNG(seed=0)`.
4. **Thread safety**: `pause()`/`resume()` are synchronous — no threads. Not a risk.

## Anti-Drift Hazards

- Do NOT add `victory_conditions` to `ALLOWED_INITIAL_CONDITION_CATEGORIES` — it is a separate top-level field.
- Do NOT rename `SimulationScenarioDefinition` — it is the canonical scenario schema type.
- Do NOT implement objective evaluation logic (that is E31B scope).
- The `_stopped` flag on Kernel controls tick suppression. The service uses a separate `_paused` flag — these are orthogonal.
