---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260824-ROLLOUT-FLAG-DECISIONS
phase: done
date: 2026-08-24
tags: [feature-flags]
---

# TCK-20260824-ROLLOUT-FLAG-DECISIONS

## Title
Decide the Eight Rollout Flags on Purpose

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
Eight real, correctly-built systems (Self-Model, World Emergence, Progression Conversion, Combat Engagement, Social Cooperation, Belief Assimilation, Information Intent Execution, Guild Quest Generation) sit flag-gated OFF. The author wants a deliberate per-flag keep/cut/flip decision made now, not left as accumulating debt, because 38 more flagged ideas land on top of this precedent in M2 onward. This is a decision-only ticket, not new code, and must land before any other M1 ticket that adds new flag-gated behavior.

## Scope
- Produce a decision artifact recording keep/cut/flip verdict, with rationale citing evidence, for each of the 8 flags: ENABLE_SELF_MODEL_COGNITION, ENABLE_WORLD_EMERGENCE, ENABLE_PROGRESSION_EVOLUTION, ENABLE_COMBAT_ENGAGEMENT, ENABLE_SOCIAL_COOPERATION, ENABLE_BELIEF_ASSIMILATION, ENABLE_INFORMATION_INTENT_EXECUTION, ENABLE_GUILD_QUEST_GENERATION
- Reconcile FeatureFlagManager's all-OFF defaults (src/domains/optimization/feature_flags.py) against real per-world profiles that already turn 2 of the 8 flags ON (config/simulation_quality/profiles/urban_political.yaml, sandbox_world.yaml)
- Resolve what to do with the orphaned RolloutProfileManager (src/domains/optimization/rollout_profiles.py), which encodes a conflicting default matrix with zero callers found
- For each 'flip ON' verdict: implement the code default flip plus the required tests/unit/config/test_phase10_feature_flags.py::_DELIBERATE_ON_DEFAULT_FLAGS allowlist entry with backing ticket ref, or explicitly defer to a named follow-up ticket
- For each 'cut' verdict: remove the dead phase/call site, or document explicitly why the code stays, with a rationale class
- Add a docs/guidelines/intentional_divergences.md entry for every flip

## Out of Scope
- New gameplay content or scenario wiring for any of the 8 systems beyond the flag-default/dead-code decision itself
- Resolving the untested ENABLE_SELF_MODEL_COGNITION + ENABLE_ADVENTURE_ROUTING combination beyond flagging it as an assumption
- Any other M1 ticket that introduces new flag-gated behavior -- those must wait until this ticket closes

## Acceptance Criteria
- [x] Decision artifact records a keep/cut/flip verdict with rationale for all 8 named flags
- [x] For every 'flip ON' verdict, either the code default changed with a corresponding _DELIBERATE_ON_DEFAULT_FLAGS allowlist entry, or an explicit deferral to a named follow-up ticket is recorded
- [x] For every 'cut' verdict, the dead phase/call site is removed or an explicit rationale-class note is added for why it stays
- [x] Decision artifact explicitly reconciles FeatureFlagManager's all-OFF defaults against urban_political.yaml/sandbox_world.yaml's already-ON flags
- [x] This ticket is closed before any other M1 ticket that adds new flag-gated behavior begins

## Related Tickets
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
- TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md
- docs/brainstorm/rpg_feature_atlas.html
- src/domains/optimization/feature_flags.py
- src/domains/optimization/rollout_profiles.py
- src/domains/optimization/degradation.py
- src/engine/pipeline.py
- src/engine/pipeline_phases/guild_visit.py
- src/engine/pipeline_phases/information_intent_execution.py
- src/ai/goals/scorers.py
- src/cognition/self_model_phase.py
- config/simulation_quality/profiles/urban_political.yaml
- config/simulation_quality/profiles/sandbox_world.yaml

## Assumptions / Open Questions
- 'Progression Conversion' in the proposal's naming maps to the actual flag ENABLE_PROGRESSION_EVOLUTION -- needs confirming as part of the decision writeup
- Whether the untested combination of ENABLE_SELF_MODEL_COGNITION + ENABLE_ADVENTURE_ROUTING is safe to flip both ON simultaneously is an open question, unlike the already-fixed ENABLE_SELF_MODEL_COGNITION + ENABLE_BELIEF_ASSIMILATION combination
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ (C20) is sequenced strictly after this ticket's ENABLE_BELIEF_ASSIMILATION verdict lands

## Implementation Notes
Full decision trail lives in `staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md`
and the durable summary in `docs/architecture/rollout_flag_decisions_m1.md`. Summary:
- `ENABLE_BELIEF_ASSIMILATION` and `ENABLE_SOCIAL_COOPERATION` flipped `ON` by default — real,
  live corpus-profile evidence (`config/simulation_quality/profiles/sandbox_world.yaml`,
  `urban_political.yaml`). Recorded as `docs/guidelines/intentional_divergences.md` DEV-003.
- `ENABLE_GUILD_QUEST_GENERATION` kept `OFF` — its existing DEV-002 rationale comment formalized,
  not re-litigated.
- `ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`,
  `ENABLE_PROGRESSION_EVOLUTION`, `ENABLE_INFORMATION_INTENT_EXECUTION` kept `OFF, deferred` — each
  got a named follow-up ticket (see Related Tickets) whose job is to produce the missing evidence.
- `src/domains/optimization/rollout_profiles.py` (`RolloutProfileManager`) deleted — confirmed
  orphaned (zero real application callers, its own default matrix conflicted with
  `FeatureFlagManager`'s real defaults). Its one real test dependent,
  `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`, was kept and had its
  `tick_budget_ms`/`max_trace_events` constants inlined locally; its dedicated TDD suite,
  `tests/unit/config/test_phase10_rollout_profiles.py`, was deleted outright (tested nothing but
  the dead class).
- Three independent, hardcoded copies of the `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist were found
  across the test suite (`tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py`) and all three updated with the
  2 new flags — disclosed as a real architectural smell worth a future consolidation ticket, not
  fixed here (out of this ticket's scope).
- `tests/integration/test_scenario_feature_flag_defaults.py` had two tests
  (`test_all_flags_default_off_for_every_loaded_scenario`,
  `test_non_adventure_flags_unchanged_by_routing_override`) doing an unconditional all-OFF
  assertion with no allowlist awareness at all; both rewritten to compare each flag's actual mode
  against `ON if flag in _DELIBERATE_ON_DEFAULT_FLAGS else OFF`.
- `docs/mechanics/README.md`'s stale wound-threshold divergence note and the
  `LifecycleSystem.resolve_lifecycle()` PERMADEATH lifecycle bug were investigated and fixed as
  pre-work under separate hotfix tickets (`TCK-20260826-HOTFIX-MECHANICS-README-STALE-DIVERGENCE`,
  `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX`), both already `DONE`, ahead of this ticket per
  user decision — not part of this ticket's own Files Changed.

## Test Summary
Targeted regression suite (the 3 test files carrying `_DELIBERATE_ON_DEFAULT_FLAGS` plus the
`test_phase10_integrated_enhanced_stack_budget.py` `RolloutProfileManager` replacement, plus the
world-profile guardrail test that a different, unaffected mechanism was correctly left alone) were
run individually to green during implementation:
- `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`: 5/5 passed
- `tests/unit/config/test_phase10_feature_flags.py`: 7/7 passed
- `tests/integration/test_scenario_feature_flag_defaults.py`: 45/45 passed (was 15 failed/30 passed
  before the allowlist + T3/T7 rewrite fix)
- `tests/certification/test_phase10_enhanced_determinism_parity.py`: 5/5 passed
- `tests/integration/test_world_profile_feature_flag_guardrail.py`: 67/67 passed (confirmed
  unaffected — separate per-world YAML-override mechanism)

Broader regression sweep run after the above (`tests/unit/config/`, `tests/unit/domains/`,
`tests/certification/`, `tests/integration/`, `tests/simulation_quality/ -m "not slow"`):
796+1371 passed. 4 failures found, all diagnosed as pre-existing environment/sandbox noise, **not**
caused by this ticket's flag flip:
- `tests/certification/test_cert_long_run_stability.py::{test_long_run_pure_stability,
  test_long_run_runtime_stability, test_long_run_determinism_parity}` — each failed with
  `TimeoutError: Test execution exceeded the resource time limit` (a sandbox resource cap on a
  5000-tick/1000-entity `extra_slow` certification run, not an assertion or hash-parity failure).
  `docs/testing/regression_policy.md` §3 already lists this exact file as a Soft Monitor
  ("Long-running; infrastructure-sensitive; failures are investigated but don't block fast
  iteration"), and each test is `@pytest.mark.skipif(CI == "true", ...)` — never run on real CI at
  all.
- `tests/integration/world/test_long_run_stability.py::test_long_run_stability` — same
  `TimeoutError`; the test's own `skipif` reason documents it as wall-clock-timing-dependent and
  non-deterministic outside CI ("Mid-tick throttle fires at wall-clock-dependent moments").
- `tests/certification/test_world_compile_determinism.py::test_compile_report_contents` — not a
  real failure in that test; a session-scoped `_observability_worker_thread_sentinel` fixture
  (`tests/conftest.py:213`) reported 6 leaked `QueueDrainWorker` threads at session teardown,
  attributed to whichever test ran last. Root cause: the 3 timed-out long-run harness runs above
  left `Kernel`/`EventRecorder` instances without a clean `shutdown()` call when the sandbox killed
  them mid-run — a downstream artifact of the timeouts, not a separate regression.

None of the 4 failures is an assertion, invariant, hash-parity, or law-violation failure (the kind
`docs/testing/regression_policy.md` §4 treats as a real regression); all 4 are resource-timeout /
timeout-fallout on tests already documented as infra-sensitive or wall-clock non-deterministic.
Per that doc's triage discipline, these are reported as environment noise, not code-fixed, and the
tests were left untouched.

## Files Changed
- `src/domains/optimization/feature_flags.py` (2 flags flipped ON, comments added for all 8)
- `src/domains/optimization/rollout_profiles.py` (deleted)
- `tests/unit/config/test_phase10_rollout_profiles.py` (deleted)
- `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` (inlined `_HardwareBudget` replacing
  `RolloutProfileManager`/`HardwareClass` import)
- `tests/unit/config/test_phase10_feature_flags.py` (`_DELIBERATE_ON_DEFAULT_FLAGS` +2)
- `tests/integration/test_scenario_feature_flag_defaults.py` (`_DELIBERATE_ON_DEFAULT_FLAGS` +2,
  T3/T7 rewritten to per-flag expected-value comparison)
- `tests/certification/test_phase10_enhanced_determinism_parity.py` (`_DELIBERATE_ON_DEFAULT_FLAGS`
  +2)
- `docs/guidelines/intentional_divergences.md` (new entry DEV-003)
- `docs/architecture/rollout_flag_decisions_m1.md` (new decision artifact)
- `staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/{investigation.md,plan.md,test_plan.md}`
  (new)
- 5 new follow-up tickets in `tickets/todos/`: `TCK-20260826-{COMBAT-ENGAGEMENT,
  SELF-MODEL-COGNITION, WORLD-EMERGENCE, PROGRESSION-EVOLUTION,
  INFORMATION-INTENT-EXECUTION}-FLAG-VALIDATION.md`

## Completion Summary
All 8 rollout flags now have a recorded, evidence-backed keep/cut/flip decision instead of sitting
as accumulating debt: 2 flipped ON with live corpus evidence (DEV-003), 1 kept OFF with a
formalized existing rationale, 5 kept OFF with named follow-up tickets whose job is to produce the
missing evidence. The orphaned, conflicting `RolloutProfileManager` was cut outright. A real,
disclosed architectural smell (three unsynchronized copies of the same test allowlist) was found
and fixed in all three locations, with a note that consolidating them is a separate future ticket.
This ticket is the first landed in the `m1-quick-wins` batch, per the M1 epic plan's own explicit
acceptance signal that it must land before any other M1 ticket adding new flag-gated behavior.
