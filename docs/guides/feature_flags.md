---
status: active
layer: engine
authority: P1
audience: developer
title: Feature Flags — Getting Started Guide
tags: [feature-flags, documentation, rollout, guide]
---

# Feature Flags — Getting Started Guide

This guide explains the Phase 10 feature-rollout flag system: what the flags are, why they
default OFF, how per-world SimQ profiles can activate them, and how the `RolloutProfile`/
`HardwareClass` matrix relates to them. For the authoritative spec, see
[`optimization_contract.md`](../simulation/domains/optimization_contract.md) (the
`FeatureFlagManager` contract) and [`known_limitations.md` §1.5](../engine/known_limitations.md)
(the default-OFF policy).

---

## `FeatureMode` enum

`FeatureMode` (`src/domains/optimization/feature_flags.py:4-8`) is a 4-member `str, Enum`:

| Mode | Meaning |
|---|---|
| `OFF` | Feature disabled — domain must not be called on the tick path |
| `SHADOW` | Feature runs but output is discarded (parallel shadow execution) |
| `ON` | Feature active; output applied |
| `STRICT` | Feature active; any failure raises immediately (no silent degradation) |

## The 10 flags

`FeatureFlagManager.__init__` (`feature_flags.py:13-24`) hardcodes exactly 10 flags. **All 10
default to `FeatureMode.OFF`** (confirmed in `docs/engine/known_limitations.md` §1.5):

| Flag | Default | Controls |
|---|---|---|
| `ENABLE_WORLD_CAPABILITY_LAYER` | OFF | World capability domain activation |
| `ENABLE_SELF_MODEL_COGNITION` | OFF | Self-model cognition pipeline |
| `ENABLE_ADVENTURE_ROUTING` | OFF | Adventure/route resolution |
| `ENABLE_COMBAT_ENGAGEMENT` | OFF | combat_engagement domain (Pre-Combat Assessment stage) |
| `ENABLE_BELIEF_ASSIMILATION` | OFF | information domain (Information / Belief Processing stage) |
| `ENABLE_PROGRESSION_EVOLUTION` | OFF | progression domain |
| `ENABLE_SOCIAL_COOPERATION` | OFF | cooperation domain |
| `ENABLE_WORLD_EMERGENCE` | OFF | World emergence domain activation |
| `ENABLE_LIFE_ARC_CAMPAIGNS` | OFF | Life-arc campaign domain |
| `ENABLE_ENHANCED_TRACE_EVENTS` | OFF | Enhanced trace/observability event emission |

## Default-OFF policy

All 10 flags start `OFF` by design — this is a deliberate rollout gate, not an oversight. To
exercise a flag-gated pipeline, a scenario or test must explicitly opt in via the
`overrides` constructor argument or `FeatureFlagManager.set_flag_mode()`. The canonical example is
`_build_kernel(enable_routing=True)` in `tests/integration/scenarios/test_balance_regression.py`.

**Do not change a default to `ON` without first re-running `tools/balance_measure.py`** to
establish new baseline constants and updating `test_balance_regression.py` accordingly — see
[`known_limitations.md` §1.5](../engine/known_limitations.md) for the full policy text.

## DEV-002 — default-OFF decision record

The decision to keep all 10 flags `OFF` by default (rationale class **Stabilized**) is recorded
in [`intentional_divergences.md` § DEV-002](../guidelines/intentional_divergences.md). The
sentinel test `test_adventure_routing_defaults_off()` in `test_balance_regression.py` guards this
policy. See that entry for the full rationale and unblock condition — not duplicated here.

## SimQ profile activation

Per-world SimQ calibration profiles under `config/simulation_quality/profiles/*.yaml` may carry an
optional `feature_flags:` block. Example, from `urban_political.yaml`:

```yaml
feature_flags:
  ENABLE_SOCIAL_COOPERATION: "ON"
  ENABLE_BELIEF_ASSIMILATION: "ON"
```

Values are YAML strings (`"ON"`, not the bare token `ON`). The block is optional — profiles such
as `default.yaml` omit it entirely.

`tools/calibrate_simq.py::_load_profile_feature_flags()` (L44-64) reads this block and returns a
`{flag: value}` dict, tolerant of a missing file or missing key. Inside `_run_engine()`
(L207-220), the resulting overrides are combined with environment-variable overrides of the same
flag names: **profile YAML values apply first (lower priority), then env-var overrides apply
second and win (higher priority)**. The combined overrides are injected via
`dc_replace(state, feature_flags=...)` before `Kernel` construction.

This is a **separate mechanism** from `FeatureFlagManager`/`RolloutProfileManager` — no
`FeatureFlagManager` instance appears anywhere in `calibrate_simq.py`; it operates directly on
`AuthoritativeState.feature_flags`.

## `RolloutProfile` / `HardwareClass` matrix

`RolloutProfileManager` (`src/domains/optimization/rollout_profiles.py:36-86`) defines exactly 3
hardcoded profiles keyed by `HardwareClass`:

| Profile | Enabled | Shadow | Disabled | `max_ram_mb` | `tick_budget_ms` | `max_trace_events` |
|---|---|---|---|---|---|---|
| `CLASS_A` (low spec) | 2 | 1 | 7 | 512 | 10.0 | 1000 |
| `CLASS_B` (mid spec) | 6 | 2 | 2 | 2048 | 25.0 | 5000 |
| `CLASS_C` (high spec / full stack) | 10 | 0 | 0 | 8192 | 50.0 | 20000 |

`RolloutProfile` is a frozen dataclass (`name`, `hardware_class`, `enabled_phases`,
`shadow_phases`, `disabled_phases`, `max_ram_mb`, `tick_budget_ms`, `max_trace_events`).
`get_profile(hardware_class)` is a plain dict lookup that returns one of these 3 descriptors.

**Current reality:** `RolloutProfileManager` has no method that wires a profile's
`enabled_phases`/`shadow_phases` into a live `FeatureFlagManager` instance — there is no
`apply_profile()` or `activate()`. `get_profile()` has no side effect; it only returns a
declarative `RolloutProfile` descriptor. Applying a chosen profile's flags to a running
`FeatureFlagManager` is left to the caller.

## Cross-reference caveat: `rollout_hardening_rulebook.md`

[`docs/combat/rollout_hardening_rulebook.md`](../combat/rollout_hardening_rulebook.md) describes a
differently-named flag family — `SimulationConfig.overhaul_features` gating `use_legality_v2`,
`use_combat_interaction_v2`, `use_movement_model_v2`, and `use_tactical_evaluator_v2` — with
default `True` (the opposite polarity of the default-OFF `FeatureFlagManager`/`FeatureMode`
system documented above). This is **not** the same system. As of this writing, no implementation
of `overhaul_features` or any `use_*_v2` flag was found anywhere in `src/`.

## Constraints

`FeatureFlagManager` flag values must not be changed after kernel initialization — flags are set
once per run.
