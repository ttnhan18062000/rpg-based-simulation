# Investigation — TCK-20260627-P2E-FEATURE-FLAG-TEST

## Date
2026-06-27

## Summary
Feature flag default test coverage gap identified in D09 Finding 4. All 10 Phase 10
flags live in `src/domains/optimization/feature_flags.py`. The related P0-A decision
(TCK-20260627-P0A-ADVENTURE-FLAG) kept all flags at `FeatureMode.OFF` by default
(intentional divergence DEV-002). No existing test checks flag defaults per loaded
scenario — only a single sentinel in test_balance_regression.py covers one flag
(`ENABLE_ADVENTURE_ROUTING`).

## Findings

### Flag Structure
- File: `src/domains/optimization/feature_flags.py`
- 10 flags, all default to `FeatureMode.OFF`:
  ENABLE_WORLD_CAPABILITY_LAYER, ENABLE_SELF_MODEL_COGNITION, ENABLE_ADVENTURE_ROUTING,
  ENABLE_COMBAT_ENGAGEMENT, ENABLE_BELIEF_ASSIMILATION, ENABLE_PROGRESSION_EVOLUTION,
  ENABLE_SOCIAL_COOPERATION, ENABLE_WORLD_EMERGENCE, ENABLE_LIFE_ARC_CAMPAIGNS,
  ENABLE_ENHANCED_TRACE_EVENTS
- `FeatureMode` enum: OFF, SHADOW, ON, STRICT
- `is_enabled()` returns True for ON and STRICT only
- `is_shadow()` returns True for SHADOW only
- Supports `overrides` dict in constructor for per-instance customisation

### Existing Test Coverage
- `tests/unit/config/test_phase10_feature_flags.py` — 5 tests, all passing.
  Covers: defaults OFF/SHADOW, OFF skip semantics, SHADOW non-mutation, ON enables,
  STRICT serialisation. All tests are flag-centric, not scenario-centric.
- `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off` —
  sentinel test asserting ENABLE_ADVENTURE_ROUTING == FeatureMode.OFF. Single-flag, single-instance.
- No test loads scenario YAML files and checks flags per scenario.

### Scenario Definitions
Location: `data/content/simulation_scenarios/`
Files (4):
  - `dungeon_crawl_scenarios.yaml` — 2 scenarios (hero_guild_perspective)
  - `frontier_scenarios.yaml` — 8 scenarios (hero_guild/merchant/dwarven perspectives)
  - `urban_political_scenarios.yaml` — 2 scenarios (merchant/hero perspectives)
  - `wilderness_survival_scenarios.yaml` — 2 scenarios (hero_guild_perspective)

Total: 14 scenario definitions in YAML.

YAML format fields: id, world_composition, focus_modules, perspective, initial_conditions.
**No feature_flags field is embedded in any scenario YAML** — flags must be derived
from content type.

### Scenario Template System
`src/scenarios/templates.py` — 10 templates with `required_world_features`.
`src/scenarios/schema.py` — `SimulationScenarioDefinition` schema (no feature_flags field).
`src/scenarios/feature_validator.py` — `ScenarioWorldFeatureValidator` checks world features
vs composition, NOT feature flag states.

### Adventure-Routing Content Type
Scenarios with `perspective: "hero_guild_perspective"` are the primary consumer of
`ENABLE_ADVENTURE_ROUTING` — the adventure decision pipeline (AdventureDecisionPhase)
applies to hero agents choosing routes. 10 of 14 scenarios use this perspective.

### P0-A Decision (Done Ticket)
TCK-20260627-P0A-ADVENTURE-FLAG decided Option B: all 10 flags remain OFF by default.
Documented in:
- `docs/engine/known_limitations.md` §1.5
- `docs/guidelines/intentional_divergences.md` DEV-002 (rationale: Stabilized)
- `docs/parity_ledger/infrastructure.yaml` INFRA-221

### D09 Finding 4 Annotation
Finding 4 states: "The default mode for all flags is ON unless a rollout_profile or
feature_flags state attribute overrides them." This text reflects the audit's
understanding at audit-time, which was BEFORE TCK-P0A documented the intentional OFF
default. The actual code (`feature_flags.py:13–24`) has all defaults as OFF. The audit
annotation and the P0-A ticket resolve this discrepancy.

## Gap Identified
No test:
1. Loads scenario YAML files and verifies per-scenario flag states
2. Verifies flag stability across multiple FeatureFlagManager instances
3. Verifies the opt-in mechanism (explicit override) produces the expected enabled state
   for adventure-routing scenarios

## Conclusion
Test file `tests/integration/test_scenario_feature_flag_defaults.py` must be created.
Tests are pure configuration assertions — no simulation run required.
