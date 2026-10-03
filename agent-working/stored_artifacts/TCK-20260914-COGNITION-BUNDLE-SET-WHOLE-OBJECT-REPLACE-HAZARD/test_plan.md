# Test Plan — TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD

## New tests

- `tests/unit/domains/memory/test_memory_update_phase_apply.py::
  test_memory_update_reads_through_an_earlier_same_tick_cognition_write` — proves the Step 1 fix:
  an earlier phase's staged `cognition_bundle_set` survives `MemoryUpdatePhase.apply()` rather than
  being clobbered.
- `tests/unit/core/test_cognition_write.py` (7 cases) — direct unit coverage of
  `read_through_cognition()`: no candidates, all-`None` candidates, an empty `EntityUpdate`, a
  single staged write, priority order across multiple candidates, fall-through when the first
  candidate has no write yet, and `None` candidates being skipped without error.
- `tests/architecture/test_cognition_bundle_set_read_through_guard.py` (2 cases) — the Option 3
  guardrail itself: (1) no function under `src/` stages a `cognition_bundle_set` write while
  reading `.cognition` raw, outside the one documented allowlist entry; (2) the allowlist entry
  still actually matches the raw pattern it exists to suppress (catches the entry going stale).
  Detection logic sanity-checked directly against a synthetic violating snippet (not committed) to
  confirm it actually fires before trusting a real-repo pass as meaningful.

## Regression coverage for every migrated call site

Ran under `.venv313` (CI parity — matches the repo's declared `python-version: "3.13"`), scoped to
`-m "not slow and not extra_slow"`:

| Migrated site | Suite | Result |
|---|---|---|
| `memory/phase.py` | `tests/unit/domains/memory/`, `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` | pass |
| `combat_engagement/phase.py` | `tests/unit/domains/combat_engagement/`, `tests/integration/domains/combat_engagement/`, `tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py` | 104 passed |
| `habit_phase.py` | `tests/unit/domains/emotion/test_phase16_habit_bias_service.py`, `test_phase16_habit_memory_model.py`, `tests/unit/tactical/test_habit_bias_action_style_wiring.py`, `tests/architecture/test_habit_bias_personality_frozen.py`, `tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py`, `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` | pass (bundled below) |
| `hardening.py` | `tests/unit/engine/test_near_death_hardening_emotion.py` | pass (bundled below) |
| `lifecycle.py` (`_seed_dying_wish`) | `tests/unit/progression/test_lifecycle.py`, `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` | 44 passed |
| `role_model_phase.py` | `tests/unit/strategic/test_role_model_state.py` | pass (bundled below) |
| `movement.py` (`route_movement_intent`) | `tests/unit/movement/test_movement_spatial_regression.py` | pass (bundled below) |
| `quests.py` (`enforce`, ESCORT reputation) | `tests/unit/domains/information/test_information_provider_accumulation.py`, `tests/unit/quest/test_quest_rewards.py`, `tests/integration/kernel/test_resource_conservation.py`, `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`, `tests/integrity/test_logic_guards.py` | 35 passed, 1 deselected, 1 xfailed |

Combined bundle (memory/movement/emotion/strategic/lifecycle-adjacent, run together): **46 passed**.

## Full fast-tier sweep

`tests/unit tests/integration tests/architecture -m "not slow and not extra_slow"`: **6518 passed,
9 skipped, 95 deselected, 7 failed**. The 7 failures are all in
`tests/unit/domains/progression/test_material_possession_predicate.py`,
`test_phase6_growth_gap_evaluator.py`, `test_phase6_possession_understanding_service.py` — recipe/
material-lookup tests with zero relation to `cognition_bundle_set`/`CognitionModel` and no touched
file in this batch's diff. Re-ran all 7 in isolation: **18 passed** — a pre-existing full-suite
cross-test-pollution issue (unrelated shared registry state, not this ticket's own regression),
confirmed and disclosed, not fixed here (out of scope).

`tests/architecture/` in full: **111 passed** (includes the new guardrail test).
