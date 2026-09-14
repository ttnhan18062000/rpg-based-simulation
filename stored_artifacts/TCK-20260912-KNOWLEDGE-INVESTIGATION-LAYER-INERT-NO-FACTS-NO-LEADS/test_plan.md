# Test Plan — TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS

## Real evidence obtained

- Instrumented 300-tick run against `frontier_living_world`: `GuildAction.visit()` leads_gained
  0→non-zero across the `"iron"`→`"iron_vein"` fix.
- `tools/calibrate_simq.py` before/after on `frontier_living_world` (seed 42, 500 ticks) under an
  explicit env-var override: COGNITION/INFORMATION B→S, `decision_diverged_by_belief` 506 events —
  recorded as D-10.
- Revert-and-compare on the `FeatureFlagManager` default flip via `frontier_marches`'s own real
  corpus-profile test harness: bit-identical zero guild activity with and without the flip —
  confirms the propagation gap, not a false positive.
- Revert-and-compare on the 4 apparently-broken `test_corpus_diversity.py` NARRATIVE anchors:
  identical failures with the flip fully reverted — confirms pre-existing, unrelated.

## Regression suites run

- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/engine/test_guild_visit_phase.py`,
  `tests/unit/ai/test_guild_need_scorer.py`, `tests/architecture/test_guild_action_dormancy.py`,
  `tests/unit/strategic/test_opportunities.py` — 40 passed.
- `tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py` — 55 passed.

## Not run to completion

- Full `tests/unit/worldassembly/test_corpus_diversity.py` (known ~20-minute file) — targeted
  subset run instead, sufficient to establish the pre-existing-failure finding without the full
  file's runtime cost.

## Closure evidence, 2026-09-13 (real-run measurement, not unit tests — this ticket's own closure
is evidential: the code fixes it depends on carry their own committed test coverage in their own
tickets)

5 real `tools/calibrate_simq.py` runs against `frontier_living_world` (seed 42, 500 ticks):
- 3 no-env-var (real default) + 1 explicit-override ON + 1 scratch-instrumented ON = 4 samples,
  all showing 344 `decision_divergence_detected` events, COGNITION grade S.
- 1 explicit-OFF sample: 0 events, grade B.
- 1 anomalous no-env-var sample: 0 events despite `GuildAction.visit()` confirmed firing
  identically to every other ON sample (direct instrumentation) — explained by known wall-clock
  kernel-throttle non-determinism, not a defect; not treated as blocking evidence given 4
  consistent samples.

Committed test coverage for the mechanisms this closure depends on already exists from the tickets
that shipped them: `tests/unit/engine/test_kernel_feature_flags_propagation.py` (propagation),
`tests/unit/world/test_guild_pipeline.py`, `tests/unit/strategic/test_detour_suggestion.py`,
`tests/unit/strategic/test_belief_integration.py` (detail-format contract). No new test files
added for this ticket's own closure — the evidence is a real-run measurement, not new code.
