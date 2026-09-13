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

## The 16 flags

`FeatureFlagManager.__init__` (`feature_flags.py:13-33`) hardcodes exactly 16 flags. **11 of the
16 default to `FeatureMode.OFF`**; 5 default `ON`: 4 are real, documented, individually-reasoned
exceptions (`ENABLE_PUSH_EVENT_SHAPERS`, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`,
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`, `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` — cutover-validated
replacements of existing behavior, not speculative rollouts); the 5th,
`ENABLE_GUILD_QUEST_GENERATION`, was flipped `OFF`→`ON` on real before/after SimQ evidence
(`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`, 2026-09-13 — see its own
row below and `docs/plans/deferred_tuning_decisions_register.md` D-10).

| Flag | Default | Controls |
|---|---|---|
| `ENABLE_WORLD_CAPABILITY_LAYER` | OFF | World capability domain activation |
| `ENABLE_SELF_MODEL_COGNITION` | OFF | Self-model cognition pipeline |
| `ENABLE_ADVENTURE_ROUTING` | OFF | Adventure/route resolution |
| `ENABLE_COMBAT_ENGAGEMENT` | OFF | combat_engagement domain (Pre-Combat Assessment stage) |
| `ENABLE_BELIEF_ASSIMILATION` | OFF | information domain (Information / Belief Processing stage) |
| `ENABLE_INFORMATION_INTENT_EXECUTION` | OFF | information_intent_execution domain (executes self-model query-routing `ActionIntent`s via `ActionIntentAdapter.execute()`) |
| `ENABLE_PROGRESSION_EVOLUTION` | OFF | progression domain |
| `ENABLE_SOCIAL_COOPERATION` | OFF | cooperation domain |
| `ENABLE_WORLD_EMERGENCE` | OFF | World emergence domain activation |
| `ENABLE_LIFE_ARC_CAMPAIGNS` | OFF | Life-arc campaign domain |
| `ENABLE_ENHANCED_TRACE_EVENTS` | OFF | Enhanced trace/observability event emission |
| `ENABLE_PUSH_EVENT_SHAPERS` | **ON** | **Not routed through `FeatureFlagManager`/`run_phase()`** — the other flags gate pipeline *phases*; this one gates COMBAT/ECONOMY/FACTION event-emission delivery. `Kernel._phase_observability()` reads it directly from `prior_state.feature_flags` (bypassing `FeatureFlagManager` entirely — registering it in `__init__`'s dict is for documentation/consistency only). Flipped to `ON` (from `OFF`) by `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (Phase 1's cutover, DONE) — this is the live default path for COMBAT/ECONOMY/FACTION event emission via the apply-layer shaper registry (`src/observability/event_shapers.py`); `event_extractor.py`'s old diffing branches for these 3 domains remain, flag-gated to fire only when this is NOT `"ON"` — setting it `"OFF"` is a real, working rollback. |
| `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` | **ON** | Same mechanism as `ENABLE_PUSH_EVENT_SHAPERS` (bypasses `FeatureFlagManager`, read directly from `prior_state.feature_flags`, but internally by `event_shapers.py::run_shadow_shapers()` itself rather than `kernel.py`), governing Phase 2 domains (AGENCY/COGNITION/INFORMATION/PROGRESSION/WORLD/SOCIAL) in `PHASE2_SHAPER_REGISTRY`. Kept on a **separate** flag from `ENABLE_PUSH_EVENT_SHAPERS` specifically because that flag already defaults `ON` — a Phase 2 shaper added to the same registry/flag would have gone live immediately with no SHADOW-validation window (a real double-firing bug found and fixed by `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`). Flipped to `ON` (from `OFF`) by `TCK-20260806-PUSH-CUTOVER-PHASE2` (DONE) — this row was previously stale, not updated at that cutover's own doc-update step; corrected here while editing this same table for `ENABLE_GUILD_QUEST_GENERATION`. `event_extractor.py`'s old diffing branches for Phase 2's domains remain, flag-gated to fire only when this is NOT `"ON"` — setting it `"OFF"` is a real, working rollback. |
| `ENABLE_PUSH_EVENT_SHAPERS_QUEST` | **ON** | Same mechanism as the two flags above (bypasses `FeatureFlagManager`, read directly from `prior_state.feature_flags`, gated internally by `event_shapers.py::run_shadow_shapers()`), governing the single `narrative` domain (`quest_event`, entity-project quest lifecycle) in `QUEST_SHAPER_REGISTRY` (`NarrativeShaper`). Kept on its own separate flag rather than folded into `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` for the identical reason Phase 2 needed its own flag distinct from Phase 1's — that flag already defaults `ON`. Added and defaulted `ON` (verified via real-kernel-adjacent checks in both SHADOW and ON mode, no double-fire against `event_extractor.py`'s own rollback path) by `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION` — corrects a stale claim in `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`'s own closed record that `quest_event` "already come[s] from `quest_system`," which was never true. `event_extractor.py`'s old `quest_event`-only diffing branch (not `commitment_abandoned`, migrated separately below) remains, flag-gated to fire only when this is NOT `"ON"` — setting it `"OFF"` is a real, working rollback. |
| `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` | **ON** | Same mechanism as the three flags above, governing the single `agency` domain (`commitment_abandoned` + `rejection_cascade_tick`, both `AgencyScorer`) in `AGENCY_SHAPER_REGISTRY` (`AgencyShaper`) — the last 2 events found still diffing-based during `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own systematic sweep. Kept on its own separate flag rather than colocated with `NarrativeShaper`/`ENABLE_PUSH_EVENT_SHAPERS_QUEST` (despite sharing the same `_current_projects()` reconstruction helper) for the identical reason that flag already defaults `ON` — colocating would have delivered these two events live with no independent verification window. Added and defaulted `ON` (verified via real-kernel-adjacent checks in both SHADOW and ON mode, no double-fire, for both events independently) by `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`/`TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`. `event_extractor.py`'s old diffing/aggregation blocks for both events remain, flag-gated to fire only when this is NOT `"ON"` — setting it `"OFF"` is a real, working rollback. |
| `ENABLE_GUILD_QUEST_GENERATION` | OFF | Gates `GuildNeedScorer` (`src/ai/goals/scorers.py`, checked via `state.feature_flags` directly) and the `guild_visit` pipeline phase (`GuildVisitPhase`, `src/engine/pipeline_phases/guild_visit.py`, routed through `FeatureFlagManager`/`run_phase()` like the 12 phase-gating flags above — NOT the push-event-shaper bypass pattern). New gameplay behavior (entities can now visit a `town_hall` building to receive real quests/leads via `GuildAction.visit()`, previously fully unreachable — `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`), not a validated replacement of existing behavior, so it correctly defaults `OFF` per DEV-002. |
| `ENABLE_INFORMATION_HUB_ACCUMULATION` | OFF | Gates two independent mechanisms (idea 41, `TCK-20260903-INFORMATION-HUB-ACCUMULATION`): (1) the `InformationProviderState.knowledge_accumulated` increment inside `QuestResolutionSystem.enforce()`'s `is_newly_completed` branch (`src/engine/quests.py`, checked via `state.feature_flags` directly, matching `ENABLE_GUILD_QUEST_GENERATION`'s own convention) — structurally inert in live corpus runs today because the Guild hub's visit-completion path never populates `QuestState.source_entity_id`; and (2) the `information_propagation` pipeline phase (`InformationPropagationService`, `src/engine/faction_decision.py`, routed through `FeatureFlagManager`/`run_phase()`), which propagates critical (`severity >= 0.8`) `WorldEvent`s City-to-City and City-to-ALLIED-Country via `FactionState.territory`/`diplomatic_relations`. Brand-new mechanic, no corpus profile turns this on and no SHADOW-validation history exists, so it correctly defaults `OFF` per DEV-002. |

## Default-OFF policy

12 of the 16 flags start `OFF` by design — this is a deliberate rollout gate, not an oversight. To
exercise a flag-gated pipeline, a scenario or test must explicitly opt in via the
`overrides` constructor argument or `FeatureFlagManager.set_flag_mode()`. The canonical example is
`_build_kernel(enable_routing=True)` in `tests/integration/scenarios/test_balance_regression.py`.
`ENABLE_PUSH_EVENT_SHAPERS`, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`,
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`, and `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` (all `ON`, all
cutover-validated replacements of existing behavior) are the 4 documented exceptions — see the
table above and each flag's own row for the specific reasoning. `ENABLE_GUILD_QUEST_GENERATION`
is new gameplay behavior, not a replacement, so it correctly follows the standard default-OFF
policy rather than joining those 4 exceptions.

**Do not change a default to `ON` without first re-running `tools/balance_measure.py`** to
establish new baseline constants and updating `test_balance_regression.py` accordingly — see
[`known_limitations.md` §1.5](../engine/known_limitations.md) for the full policy text. This
applies to the 12 phase-gating flags; the 4 push-event-shaper flags are observability-only
(construct/deliver events, not pipeline phases) and are governed by their own cutover tickets'
validation instead, not `balance_measure.py`.

## DEV-002 — default-OFF decision record

The decision to keep all flags `OFF` by default (rationale class **Stabilized**) is recorded
in [`intentional_divergences.md` § DEV-002](../guidelines/intentional_divergences.md) (that entry
predates `ENABLE_PUSH_EVENT_SHAPERS`/`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`/
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`/`ENABLE_PUSH_EVENT_SHAPERS_AGENCY`/
`ENABLE_GUILD_QUEST_GENERATION` and cites "11 flags" — the same rationale applies to the 12
OFF-default flags unchanged; the 4 push-event-shaper flags are each individually-reasoned,
documented exceptions, not re-litigated here). The sentinel test
`test_adventure_routing_defaults_off()` in `test_balance_regression.py` guards this policy for the
12 phase-gating flags. See that entry for the full rationale and unblock condition — not
duplicated here.

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
