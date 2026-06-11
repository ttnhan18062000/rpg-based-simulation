---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-TEST-STRATEGY
artifact_type: plan
tags: [world, test, strategy]
---

# Implementation Plan — Milestone 73 Worldbuilding Test Strategy

We will build a comprehensive, dedicated validation and test suite to satisfy all anti-misdirection requirements and smoke simulation objectives of Milestone 73.

## Proposed Changes

### Tests

#### [NEW] [test_worldbuilding_strategy.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldbuilding/test_worldbuilding_strategy.py)
This new file will implement:
- **Anti-misdirection checks**:
  - `test_validation_must_fail_before_compilation`: Induces an error in the spec and asserts that using the CLI compile or standard validation routines rejects compilation cleanly.
  - `test_compiler_does_not_drop_invalid_references`: Verifies that if invalid references are present in quests, warnings are emitted, and the compile report captures them.
  - `test_compiler_does_not_autocreate_factions_or_regions`: Verifies that compilation does not dynamically synthesize objects that are not in the spec schema.
  - `test_generated_entity_count_matches_requested`: Spawns complex multiple population groups and verifies the exact counts mapped into `AuthoritativeState`.
  - `test_same_seed_produces_identical_state_hash`: Asserts mathematical parity under multiple compilations with same seeds.
  - `test_warnings_visible_in_report`: Validates warning string checks in output reports.
  - `test_unknown_schema_version_fails_clearly`: Tests that calling validator or repository with unknown schemas raises custom errors.
  - `test_future_fields_preserved_or_rejected`: Asserts that unrecognized metadata fields are parsed and safely held under Pydantic schemas.
- **Smoke Simulation suite**:
  - `test_smoke_simulation_run`: Runs the compiled world inside the authoritative V2 engine pipeline for 10 ticks, proving lack of structural degradation.
- **Observatory Integration suite**:
  - `test_observatory_integration_smoke`: Runs the compiled state under the engine and verifies that the `StateFingerprinter` and standard telemetry components output correctly, ensuring the telemetry layers are functional.
