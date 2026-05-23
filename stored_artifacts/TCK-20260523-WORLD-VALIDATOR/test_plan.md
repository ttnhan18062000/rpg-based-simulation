# Test Plan: World Validation Layer

We will implement two separate unit test suites to isolate validation rule testing from the high-level orchestration testing.

## 1. Rule Unit Tests (`tests/unit/worldbuilding/test_world_validation_rules.py`)
Isolate checks for individual rule logic.
- **Reference Validation Rules**:
  - `WORLD-REF-001`: Entity faction reference check. Verify it reports an ERROR if population group refers to a non-existent faction.
  - `WORLD-REF-002`: Entity spawn region check. Verify it reports an ERROR if a population group refers to a non-existent region ID.
  - `WORLD-REF-003`: Resource region check. Verify it reports an ERROR if a resource node refers to a non-existent region ID.
  - `WORLD-REF-004`: Building region check. Verify it reports an ERROR if a building refers to a non-existent region ID.
- **Topology & Geometry Containment Rules**:
  - `WORLD-TOPO-001`: Region bounds containment. Verify it reports an ERROR if any region bounds overlap or fall outside the map topology coordinates.
- **Sanity / Warning Rules**:
  - `WORLD-WARN-001`: Zero resources check. Verify it reports a WARNING if `resources` list is empty.
  - `WORLD-WARN-002`: High density spawn check. Verify it reports a WARNING if combined population entity count exceeds 50% of the topology tile area.

## 2. Validator Orchestrator Tests (`tests/unit/worldbuilding/test_world_validator.py`)
Verify high-level validation behavior.
- **Valid World Scenario**: Runs without any ERRORs or WARNINGs.
- **Determinism**: Asserts that running validation multiple times on the same spec returns identical, ordered issues.
- **Strict Mode**: If `strict=True`, any generated WARNING is elevated or blocks verification, raising a validation failure.
- **Unknown Section Policies**: Verifies that passing a raw data dictionary with extra/unknown top-level sections is caught and flagged according to defined warning policies.
- **Non-fixing Behavior**: Verifies that the validator does not secretly modify or auto-fix any parameters in the `WorldSpec` model.
