---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260627-P2E-FEATURE-FLAG-TEST
phase: done
date: 2026-06-27
tags: [p2, feature-flags, testing, scenario, per-scenario-defaults, integration]
---

# TCK-20260627-P2E-FEATURE-FLAG-TEST

## Title
Add per-scenario feature flag default assertions in integration tests

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
8 pipeline phases are gated behind `FeatureMode` flags in `src/domains/optimization/feature_flags.py`. No test verifies that the correct default flag values are set per scenario type. A misconfigured scenario silently loses features. Source: D09 Finding 4, Risk 9/15.

## Scope
- Add a test in `tests/integration/` or `tests/certification/` that:
  1. Loads each simulation scenario definition (from `data/content/simulation_scenarios/` or wherever scenarios are defined).
  2. Asserts that the flags required for that scenario's content type are `ON` or `SHADOW`.
- At minimum assert: scenarios that include adventure routing content have `ENABLE_ADVENTURE_ROUTING` set to a non-OFF state.
- Use the D19 domain-phase inventory (P1-E) once available to identify which phases require which flags.

## Out of Scope
- Changing flag defaults (P0-A).
- Creating new scenarios.
- Testing flag runtime behavior (just default configuration assertions).

## Acceptance Criteria
- [x] Test file exists in `tests/integration/` or `tests/certification/`.
- [x] Each loaded scenario is checked for its expected flag states.
- [x] At minimum: `ENABLE_ADVENTURE_ROUTING` flag assertion per scenario.
- [x] Test is deterministic and does not require a running simulation.
- [x] `pytest tests/ -k "scenario_flags or feature_flag_default" -m "not slow"` passes.

## Related Tickets
- TCK-20260627-P0A-ADVENTURE-FLAG (the decision on default flag values — implement that first so these tests have known-good expected values)
- TCK-20260627-P1E-DOMAIN-INVENTORY (provides the phase → flag mapping needed to write complete assertions)

## Related Docs
- `docs/audits/D09_system_wiring.md` Finding 4
- `docs/simulation/domains/adventure_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260627-P2E-FEATURE-FLAG-TEST/`

## Related Code Areas
- `src/domains/optimization/feature_flags.py`
- `data/content/simulation_scenarios/` (confirmed: 4 YAML files, 14 scenario definitions)
- `tests/integration/test_scenario_feature_flag_defaults.py` (new)

## Assumptions / Open Questions
- Scenario definitions confirmed in YAML files under `data/content/simulation_scenarios/` (not src/scenarios/templates.py).
- D19 domain-phase inventory (P1-E) still pending. Per-scenario mapping derived from `perspective` field (`hero_guild_perspective` → adventure routing) as interim approach.

## Implementation Notes
- Loaded 14 scenario definitions from 4 YAML files (dungeon_crawl, frontier, urban_political, wilderness_survival).
- No feature_flags field is embedded in any scenario YAML — flags derived from `perspective` field.
- `hero_guild_perspective` used as the adventure-routing content type marker (10 of 14 scenarios).
- All 10 flags are intentionally OFF by default (DEV-002, TCK-P0A Option B). Tests assert OFF default + working opt-in override.
- Registered `scenario_flags` and `feature_flag_default` pytest marks in `pyproject.toml`.
- Updated INFRA-221 in `docs/parity_ledger/infrastructure.yaml` to reference new test file.
- No production code changes — `FeatureFlagManager` API already supported all test scenarios.

## Test Summary
- 45 tests, all passing.
- 9 test functions (T1–T9), parametrized across 14 scenarios for T3/T4/T6 and 11 hero_guild scenarios for T6.
- Run: `pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow" -v`
- Acceptance invocation: `pytest tests/ -k "scenario_flags or feature_flag_default" -m "not slow"` → 45 passed.

## Files Changed
- `tests/integration/test_scenario_feature_flag_defaults.py` (new) — 45 tests across 9 functions
- `pyproject.toml` — registered `scenario_flags` and `feature_flag_default` pytest marks
- `docs/parity_ledger/infrastructure.yaml` — updated INFRA-221 test_path and text

## Completion Summary
Created `tests/integration/test_scenario_feature_flag_defaults.py` with 9 test functions (45 collected tests) covering: YAML file discoverability (T1, T2, T9), all 10 flags OFF per scenario parametrized over 14 loaded scenarios (T3), ENABLE_ADVENTURE_ROUTING OFF per scenario (T4), flag stability across instances (T5), adventure routing opt-in mechanism for all 11 hero_guild_perspective scenarios (T6), override isolation (T7), and SHADOW semantics (T8). All 45 tests pass. Two new pytest marks registered in pyproject.toml. Parity ledger INFRA-221 updated to reference both the existing sentinel and the new per-scenario test suite.
