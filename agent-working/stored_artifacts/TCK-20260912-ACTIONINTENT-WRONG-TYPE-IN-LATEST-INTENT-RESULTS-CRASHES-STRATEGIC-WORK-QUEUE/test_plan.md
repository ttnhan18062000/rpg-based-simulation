# Test Plan — TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE

## Updated tests (encoded the old intent_results-based shape)
- `tests/unit/engine/test_information_intent_execution_phase.py` — fully rewritten: constructs
  `pending_action_intent=` instead of mixing `ActionIntent` into `intent_results`; asserts the
  field is cleared after execution and `intent_results` is never touched by this phase at all.
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — 3 assertions
  updated from `eu.intent_results[0]` to `eu.pending_action_intent`.
- `tests/integration/domains/information/test_phase5_branch_b_realworld.py` — 1 assertion updated
  the same way.

## New regression test
- `test_routed_action_intent_never_reaches_durable_latest_intent_results_flag_off`
  (`test_phase5_information_belief_phase.py`) — real end-to-end reproduction of the exact crashing
  condition: `ENABLE_INFORMATION_INTENT_EXECUTION` OFF (shipped default), Branch B routes a real
  query, the resulting `EntityUpdate` is materialized through the real `extract_patches()` →
  `IdentityPatch.apply()` path (not a mock), and `StrategicWorkQueue.build()` is called on the
  resulting entity with a real (non-None) `DirtySet` so it reaches the `.accepted` check rather
  than taking its own early-return path. Asserts no `ActionIntent` in `latest_intent_results` and
  no crash.

## Methodology validation (not itself a committed test)
Standalone script reproducing the OLD write shape (`intent_results=[ActionIntent(...)]`) through
the identical real materialization path confirmed it still crashes with the identical
`AttributeError` — proving the new regression test's own methodology would have caught the
original bug, not passing vacuously regardless of the fix.

## Direct verification against the originally-crashing test
`pytest tests/unit/worldassembly/test_corpus_diversity.py::
test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability -q` — now passes
(a real 200-tick run, previously crashed with the `AttributeError`).

## Regression suites
- `tests/unit/domains/information/`, `tests/integration/domains/information/`,
  `tests/unit/engine/test_information_intent_execution_phase.py`,
  `tests/unit/domains/optimization/test_strategic_work_queue.py`,
  `tests/unit/config/test_phase10_feature_flags.py`,
  `tests/integration/test_world_profile_feature_flag_guardrail.py` — 133 passed.
- `tests/unit/core/`, `tests/integration/pipeline/`, `tests/unit/domains/optimization/` (broader
  sweep for anything touching `EntityUpdate` generally) — 471 passed.
- `tests/helpers/assertions.py`, `tests/unit/strategic/test_rejection_backoff.py`,
  `tests/unit/strategic/test_strategic_lifecycle.py`, `tests/unit/strategic/
  test_strategic_memory_v2.py`, `tests/integration/kernel/test_phase10_replay.py`,
  `tests/integration/kernel/test_p1_replay_fidelity.py` (the remaining files referencing
  `latest_intent_results`/`pending_action_intent`) — 17 passed.
- `tests/api tests/cli tests/tools tests/logging tests/engine tests/observability` (covers
  `state_presenter.py:128`, the API-boundary read site) — 2700 passed (run as part of the sibling
  count-expansion ticket's own CI-failure triage, same suite, unaffected by this ticket's diff).

## Acceptance criteria mapping
- Fix-approach determination with evidence, peer-reviewed before implementation → investigation.md.
- `latest_intent_results` can no longer contain a non-`IntentResult` object → new regression test.
- Originally-crashing test passes on its own real assertions → direct verification above.
- CI-blind-spot gap written down → this ticket's own Request Summary/Implementation Notes, plus a
  `docs/testing/regression_policy.md` pointer.
- No regression in the named information/feature-flag suites → regression suites above.
