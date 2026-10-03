---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-SCENARIO-SCHEMA
artifact_type: plan
tags: [lab, scenario, schema]
---

# Implementation Plan — Milestone 75: ScenarioSpec Schema

Provide a robust, decoupled, and safe file-based schema and validation layer to model testing scenario intents separately from worlds, allowing test configurations to target compiled simulation environments.

## User Review Required

Document anything that requires user review or clarification:
- **Signals Permissive Warnings**: The validator performs permissive warnings checking for metric/event/cognition/anomaly keys against standard registries. Unrecognized values are permitted but raise a `WARNING` diagnostic to help catch typos (Option A/B alignment).
- **Injected World Verification**: Verifies the existence of the referenced `world_id` against the `WorldRepository` to prevent compile aborts at execution runtime.

## Proposed Changes

### Scenario Lab Package [NEW]

#### [NEW] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
Main entrypoint for the `src.lab` domain package. Exports:
- `ScenarioSpec` and `load_scenario_spec_from_yaml`
- `ScenarioValidator` and pluggable rule classes
- `ScenarioRepository`
- `InvalidScenarioSpecError` and `ScenarioRepositoryError`

#### [NEW] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/schema.py)
Implements all Pydantic models for the specification:
- `IntentSpec`
- `ExpectedLimitSpec` (including validation limits checking: `min <= max`)
- `RequiredSignalsSpec`
- `ScenarioSpec` (supporting frozen Pydantic structure with `extra="allow"` to preserve unknown fields)
- Custom exception `InvalidScenarioSpecError`
- Helper function `load_scenario_spec_from_yaml(path: Path) -> ScenarioSpec`

#### [NEW] [validator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/validator.py)
Implements pluggable rules verifying semantic criteria:
- `ScenarioValidationRule`
- `WorldExistenceRule` (`SCENARIO-REF-001` - ERROR): Verifies `world_id` exists in workspace via `WorldRepository`.
- `ExpectedBehaviorRule` (`SCENARIO-LIMIT-001` - WARNING): Validates expected limits and flags unrecognized metrics.
- `RequiredSignalsRule` (`SCENARIO-SIGNAL-001` - WARNING): Flags unrecognized metrics, events, and cognition keys.
- `AnomalyReferencesRule` (`SCENARIO-ANOMALY-001` - WARNING): Flags unrecognized critical or allowed anomalies.
- `ScenarioValidator`: Orchestrator class. Raises `InvalidScenarioSpecError` on validation errors. Includes strict mode support.

#### [NEW] [repository.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/repository.py)
Implements a safe directory loader under `data/scenarios/`:
- Aligned structure: each scenario in a separate directory (`data/scenarios/<scenario_id>/scenario.yaml`).
- safe path resolution comparing absolute ancestors to prevent path traversal attempts.
- Rebuilds and writes manifest registry `scenario_index.json` containing metadata, health status (`VALIDATED`, `BROKEN`), and tags.

---

## Verification Plan

### Automated Tests
We will add three robust test files:
- **`tests/unit/lab/test_scenariospec_schema.py`**
  - Verify valid ScenarioSpec loads cleanly.
  - Verify missing `scenario_id` and `world_id` are rejected with `ValidationError`.
  - Verify invalid expected behavior limits (e.g. `min > max`, or neither specified) are rejected.
  - Verify unrecognized fields are preserved under Pydantic extra properties.
- **`tests/unit/lab/test_scenariospec_validator.py`**
  - Verify `WorldExistenceRule` successfully matches a valid world in `WorldRepository`.
  - Verify `WorldExistenceRule` correctly errors on a missing world.
  - Verify unrecognized behavior metrics, signals, and anomalies yield appropriate warnings.
  - Verify strict mode validation rejects warning issues.
  - Verify that validation does not run the engine simulation or compile the world state.
- **`tests/unit/lab/test_scenario_repository.py`**
  - Verify listing, loading, and saving scenarios safely.
  - Verify safe manifest index rebuilds and listing operations.
  - Verify path traversal attempts are blocked via security boundaries.

### Manual Verification
- Run:
  `pytest tests/unit/lab/`
