# Test Plan — TCK-20260627-P2E-FEATURE-FLAG-TEST

## Scope
Pure configuration validation. No simulation ticks, no kernel, no world compilation.
Only `FeatureFlagManager` instantiation and YAML scenario file parsing.

## Target File
`tests/integration/test_scenario_feature_flag_defaults.py` (new)

## Test Cases

### T1 — `test_all_scenario_yaml_files_discoverable`
- Walk `data/content/simulation_scenarios/` directory
- Assert 4 YAML files are found (dungeon_crawl, frontier, urban_political, wilderness_survival)
- Guards against silent YAML removal breaking the parametrize fixture

### T2 — `test_scenario_yaml_parses_to_list_of_dicts`
- Load each YAML file
- Assert result is a list
- Assert each item has `id`, `world_composition`, `perspective` keys
- Confirms YAML structure is stable

### T3 — `test_all_flags_default_off_for_every_loaded_scenario` (parametrized)
- Parametrized over all 14 loaded scenario dicts
- For each scenario: create `FeatureFlagManager()` with no overrides
- Assert ALL 10 flags == `FeatureMode.OFF`
- Catches any accidental default change per flag
- pytest mark: `scenario_flags`

### T4 — `test_adventure_routing_flag_defaults_off_per_scenario` (parametrized)
- Parametrized over all 14 scenarios
- For each: assert `manager.get_flag_mode("ENABLE_ADVENTURE_ROUTING") == FeatureMode.OFF`
- Focused check complementing the existing sentinel in test_balance_regression.py
- Acceptance criterion: "At minimum: ENABLE_ADVENTURE_ROUTING flag assertion per scenario"
- pytest mark: `scenario_flags`, `feature_flag_default`

### T5 — `test_feature_flag_defaults_are_stable_across_instances`
- Instantiate `FeatureFlagManager()` three times without any modification
- Assert all three instances serialize identically
- Verifies no module-level mutable state / import-time side-effects alter defaults
- pytest mark: `feature_flag_default`

### T6 — `test_adventure_routing_opt_in_enables_for_hero_guild_scenarios` (parametrized)
- Parametrized over scenarios where `perspective == "hero_guild_perspective"`
- For each: create `FeatureFlagManager(overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON})`
- Assert `manager.is_enabled("ENABLE_ADVENTURE_ROUTING")` is True
- Assert `manager.get_flag_mode("ENABLE_ADVENTURE_ROUTING") == FeatureMode.ON`
- Verifies the per-scenario opt-in mechanism works for adventure content
- pytest mark: `scenario_flags`

### T7 — `test_non_adventure_flags_unchanged_by_routing_override`
- Create `FeatureFlagManager(overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.ON})`
- Assert all 9 remaining flags are still OFF
- Verifies override isolation — enabling one flag does not cascade to others

### T8 — `test_shadow_mode_is_not_enabled_for_scenario_run`
- Create `FeatureFlagManager(overrides={"ENABLE_ADVENTURE_ROUTING": FeatureMode.SHADOW})`
- Assert `is_shadow("ENABLE_ADVENTURE_ROUTING")` is True
- Assert `is_enabled("ENABLE_ADVENTURE_ROUTING")` is False (shadow != enabled)
- Verifies SHADOW semantics are correct if a scenario opts into shadow rollout

### T9 — `test_total_scenario_count_from_yaml_files`
- Load all YAML files and collect scenario IDs
- Assert total count >= 14 (catches silent YAML pruning)
- Assert all IDs are unique (no duplicate scenario IDs across files)

## pytest Invocation
```
pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow" -v
pytest tests/ -k "scenario_flags or feature_flag_default" -m "not slow"
```

## Coverage Targets
- All 10 FeatureMode flags: checked via T3 (all 14 scenarios × 10 flags = 140 assertions)
- Adventure flag per scenario: T4 (14 assertions)
- Stability: T5
- Opt-in mechanism: T6 (hero_guild scenarios)
- Override isolation: T7
- Shadow semantics: T8
- YAML integrity: T1, T2, T9

## Non-Goals
- No simulation ticks
- No kernel initialisation
- No world compilation
- No new production code (flag logic is already correct)
