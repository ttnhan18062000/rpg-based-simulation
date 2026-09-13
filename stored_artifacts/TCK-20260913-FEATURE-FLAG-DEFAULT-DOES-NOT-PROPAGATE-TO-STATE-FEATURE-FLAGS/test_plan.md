# Test Plan — TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS

## New coverage (this ticket)
`tests/unit/engine/test_kernel_feature_flags_propagation.py` — covers the propagation *mechanism*,
not just that one flag's value ended up correct (a values-only test would pass even if seeding
worked via some other, narrower path than intended):

1. `test_kernel_seeds_every_manager_flag_when_state_declares_none` — every one of
   `FeatureFlagManager().serialize()`'s own flags (26, not just `ENABLE_GUILD_QUEST_GENERATION`)
   ends up in `state.feature_flags` after `Kernel.__init__`, starting from an empty dict.
2. `test_kernel_preserves_explicit_override_that_disagrees_with_manager_default` — a
   pre-existing `state.feature_flags` entry that disagrees with the manager's own default for that
   flag survives seeding untouched. Uses a real disagreement (`ENABLE_WORLD_CAPABILITY_LAYER`,
   manager default `OFF`, test override `ON`), confirmed via `FeatureFlagManager` directly rather
   than assumed.
3. `test_kernel_seeding_is_idempotent_across_repeated_construction` — constructing a second
   `Kernel` from the first `Kernel`'s own resulting state does not double-seed or corrupt.
4. `test_guild_quest_generation_fires_in_unmodified_corpus_profile_without_env_var` — the real
   acceptance signal: `tools.calibrate_simq._run_engine("frontier_marches", ...)` against a real,
   unmodified corpus profile YAML (confirmed the profile does not itself declare
   `ENABLE_GUILD_QUEST_GENERATION`), no env var, asserts `GuildAction.visit()` actually fires within
   200 ticks. Marked `corpus_flag_guardrail` + `e2e` (not `slow`/`extra_slow` — completes in ~10s).

All four pass. `kernel.shutdown(timeout_s=1.0)` called in `finally` for every constructed `Kernel`,
matching `tests/integration/kernel/test_kernel_boundaries.py`'s own pattern — otherwise the
session-scoped `QueueDrainWorker` thread-leak sentinel in `tests/conftest.py` fails the suite.

## Regression sweep run
- `tests/unit/world/test_guild_pipeline.py tests/unit/engine/test_guild_visit_phase.py
  tests/unit/ai/test_guild_need_scorer.py tests/architecture/test_guild_action_dormancy.py
  tests/unit/strategic/test_opportunities.py tests/unit/config/test_phase10_feature_flags.py
  tests/integration/test_scenario_feature_flag_defaults.py
  tests/certification/test_phase10_enhanced_determinism_parity.py
  tests/integration/kernel/test_kernel_boundaries.py` — 97 passed.
- `tests/unit/engine/ tests/integration/kernel/ tests/unit/domains/optimization/` (broader sweep,
  since `Kernel.__init__` is a central construction path) — 448 passed, 1 skipped (unrelated), 6
  deselected (`slow`/`extra_slow`).
- `-m "corpus_flag_guardrail or scenario_flags or feature_flag_default"` (repo-wide, since the fix
  seeds all 26 manager-default flags into every real run, not only the one this ticket targeted) —
  118 passed. Confirms seeding the other 17 non-dual-gated flags (read only through
  `FeatureFlagManager`'s own dispatch, never `state.feature_flags` directly) is inert for them, as
  expected — they don't read the dict this fix populates.

No regressions found in any sweep.
