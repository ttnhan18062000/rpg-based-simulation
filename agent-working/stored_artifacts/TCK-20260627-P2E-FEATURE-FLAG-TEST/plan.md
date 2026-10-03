# Plan — TCK-20260627-P2E-FEATURE-FLAG-TEST

## Goal
Write integration tests that verify per-scenario feature flag default states.

## Constraints
- No production code changes (flags are intentionally OFF per TCK-P0A DEV-002).
- Test-only work. New file: `tests/integration/test_scenario_feature_flag_defaults.py`.
- Tests must be deterministic and require no simulation run.
- pytest marks: `scenario_flags`, `feature_flag_default` (match acceptance criteria invocation).

## Key Context
- All 10 Phase 10 flags default to `FeatureMode.OFF` — intentional per TCK-P0A, DEV-002.
- Scenario YAMLs do NOT embed feature_flags; flags are derived from content type.
- Adventure-routing content type == `perspective: "hero_guild_perspective"` scenarios.
- INFRA-221 in infrastructure.yaml parity ledger covers the global default; needs test_path
  updated to include the new per-scenario test.
- Existing sentinel `test_adventure_routing_defaults_off` in test_balance_regression.py
  covers a single instance; new tests cover per-scenario parametrized assertions.

## Implementation Steps

### Step 1: Write test file
Create `tests/integration/test_scenario_feature_flag_defaults.py` with:
  - Module-level YAML loader that walks `data/content/simulation_scenarios/`
  - Parametrize fixture that produces `(scenario_id, scenario_dict)` pairs
  - 9 test functions matching the test plan (T1–T9)
  - pytest marks: `scenario_flags`, `feature_flag_default`

### Step 2: Update parity ledger
`docs/parity_ledger/infrastructure.yaml` INFRA-221: update `test_path` to reference both
the existing sentinel and the new per-scenario test file.

### Step 3: Verify no production code changes needed
The `FeatureFlagManager` API (`get_flag_mode`, `is_enabled`, `is_shadow`, `serialize`,
`overrides` constructor arg) already supports all test scenarios. No new production code.

## Architecture Validation
- Tests read `FeatureFlagManager` state — they do NOT mutate authoritative state.
- YAML loading is read-only.
- Tests align with the "read-only validation" pattern used in test_scenario_catalog_matrix.py
  and test_scenario_setup_resolver.py.
- No imports of kernel, pipeline, or world compilation.

## Unresolved Questions
None. All required context is available:
- P0-A decision is done (all flags OFF, intentional)
- Scenario YAML locations confirmed
- FeatureFlagManager API fully understood
- D09 Finding 4 requirement is clear

## APPROVED — proceed to implementation.
