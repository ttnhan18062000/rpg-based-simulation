---
status: active
layer: testing
authority: P2
audience: agent
tags: [testing]
---

# Core-RPG test baseline — before and after the Epic A repairs (2026-09-30)

Evidence for Epic A criterion A.6 (`docs/plans/test_architecture/roadmap.md` §4.2, §7). It compares
the core-RPG test report (`tools/test_architecture/core_rpg_report.py`, v0) generated at two SHAs from
real local runs, explains every difference, and lists what is still unknown. It states no gate and
proposes no threshold. The report's own v0 limits are in the `limits` section of its output and are not
repeated here.

## Inputs

| | Pre-repair | Post-repair |
|---|---|---|
| SHA | `35806b1ed` (`origin/main`) | `7e250faf7` (PR #259 head: `35806b1ed` plus the Epic A batch 1 commits) |
| Command | `pytest tests/ -m "not slow and not extra_slow" --junitxml` | same, under `coverage run --branch --source=src` |
| Started (UTC) | 2026-09-30T02:59:27Z | 2026-09-30T03:18:45Z |
| pytest runtime | 1153.87 s (19m13s) | 2074.01 s (34m34s, coverage overhead) |
| JUnit sha256 | `819277f80159…` | `7e9ddb85868e…` |
| Coverage sha256 | none supplied | `4e2a5c12d186…` |
| Report as-of | 2026-09-30 | 2026-09-30 |

Each run was one execution in a clean, detached worktree at a real path, run sequentially. The post-repair
SHA is the PR head, not merged `main`. Both reports regenerate byte-identically from these inputs and record
`worktree_dirty: false`: the suite's tracked-file writes touched only paths the report does not scan. The
producer takes about 5 s. A first attempt at these runs was killed when a session closed; both runs were
redone from a clean reset, and the figures here are from the redone runs only.

## Results

| | Pre-repair | Post-repair |
|---|---|---|
| JUnit testcases | 11773 | 11778 |
| passed / failed / errors / skipped (incl. xfail) | 11641 / 17 / 1 / 114 | 11649 / 14 / 1 / 114 |
| Test files scanned | 1503 | 1505 |
| Classification: classified / uncertain / unowned-domain / not-core-rpg | 69 / 114 / 7 / 1313 | 69 / 114 / 7 / 1315 |
| Core-RPG candidate files (classified + uncertain) | 183 | 183 |
| Candidate files: pass / fail / skipped / not-run (of 183) | 175 / 4 / 0 / 4 | 178 / 1 / 0 / 4 |
| Package coverage | `no-coverage-artifact` | `provisional-local`: 88.21% of 55877 statements (18674 branches) |
| Mutation layer | `not-run` | `recorded`, `fresh` |
| Escaped defects | `tag-not-registered` | `counting`: 2026-09 = 0 (a real count) |
| Lanes, parity, SimQ, census | identical | identical |

pytest's own summary counts one more pass than JUnit does in both runs (11642 and 11650). That is one test
that passed and then errored in teardown: pytest counts it as both, JUnit records it once, as an error.

Post-repair package line coverage for the core-RPG-relevant packages, provisional and local:
core 93.28, domains 95.77, economy 98.61, engine 91.78, entities 94.38, progression 93.14, quests 83.81,
systems 89.82. This is package coverage. It is not domain coverage, which stays `not-derived`.

## Differences and their causes

| Difference | Cause | Kind |
|---|---|---|
| 7 nodes in 3 files under `tests/unit/domains/progression/` go from fail to pass | The registry reset fixture from `TCK-20260929-CATALOG-REGISTRY-TEST-LEAK` | Batch 1 effect |
| +5 testcases, +2 test files, `not-core-rpg` 1313 → 1315 | The 2 new test files from batch 1: the registry guard (2 tests) and the mutation record shape test (3 tests) | Batch 1 effect |
| 17 → 14 failures | 7 fixed, 4 new (below); the other 10 are carried over unchanged | Net of the two rows |
| 4 new failures, post-repair only | Coverage overhead, see below; not a batch 1 effect | Input difference |
| Coverage `no-coverage-artifact` → `provisional-local` | Coverage was supplied only for the post-repair run; the pre-repair run was not instrumented | Input difference |
| Runtime 19m13s → 34m34s | Coverage instrumentation, not batch 1 | Input difference |
| Mutation `not-run` → `recorded` | `TCK-20260929-CONSERVATION-MUTATION-BASELINE` added the record | Batch 1 effect |
| Escaped defects `tag-not-registered` → `counting` | `TCK-20260929-ESCAPED-DEFECT-TAG` registered the tag; nothing has been tagged yet, so the count is a real 0 | Batch 1 effect |
| The pre-repair suite run modified `docs/brainstorm/mechanism_verification_view.md`; the post-repair run did not | `TCK-20260929-VERIFICATION-VIEW-TEST-TRACKED-WRITE` (A.4), confirmed at full-suite scale | Batch 1 effect |

### The 4 post-repair-only failures

All four pass when run without coverage at the post-repair SHA (4 passed in 147 s). Three fail with the
60 s resource-budget `TimeoutError` from `tests/conftest.py`; the fourth is a timing-sensitive assertion.
Two of them are the tests the overview already lists as the slowest fast-lane tests (60–80 s).

- `tests/tools/test_entity_lifecycle_score.py::TestRealIntegration::test_sandbox_world_800t_end_to_end_produces_sane_output`
- `tests/unit/observability/test_stream_consumer_resilience.py::test_reconnect_backoff_resets_after_success` (`assert 4616 == 1`)
- `tests/unit/tools/test_mechanism_state_caller_check.py::test_build_report_counts_checked_and_unchecked`
- `tests/unit/tools/test_mechanism_state_caller_check.py::test_real_registry_findings_pinned`

Attribution to coverage overhead is inferred from the three timeouts and the pass-without-coverage
result; the cause of the fourth's timing assertion is not separately established. A future coverage job
has to allow for the per-test time budget.

## Remaining unknowns

1. **11 combined-run failures carried over unchanged** (10 failures and 1 error), identical on untouched
   `origin/main` and after batch 1, and identical across four separate full-suite runs. Each passes when
   run alone. Their symptoms (`SURVIVAL` and `DEGRADED` runtime modes, replay and certification asserts)
   look like combined-run interference, but that is an inference and has not been verified.
   - `tests/arena/test_arena_startup.py::test_arena_5v5_startup`
   - `tests/certification/test_envelope_violations.py::test_harness_detects_missing_degradation_mode`
   - `tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift`
   - `tests/certification/test_resilience_recovery.py::test_harness_catches_failed_recovery`
   - `tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update`
   - `tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world`
   - `tests/unit/core/test_startup_validation.py::test_aggressive_budget_warning`
   - `tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative`
   - `tests/unit/observability/test_live_anomaly_worker.py::test_worker_lifecycle_in_process`
   - `tests/unit/resource/test_resource_governor_contract.py::test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure`
   - `tests/unit/worldmodules/test_schema_unified.py::test_worldmodulespec_accepts_any_schema_version_string` (error)
2. **Order dependence outside the verified set.** Only the 8 polluter files plus the progression
   directory were checked under random order (seeds 1–10, 80 tests, all passing). Nothing else was.
3. **Tracked-file writers still present.** Both full runs rewrote `docs/REGISTRY.yaml` and
   `tickets/working_log.csv` and touched agent-monitoring shards. Attributed at file level to
   `tests/tools/test_done_checker_static.py`; tracked as `TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`.
4. **4 candidate files (4 tests) never ran.** The fast marker filter deselects every test in them
   (`no tests collected (4 deselected)`): `tests/integration/optimization/test_cache_memory_bounds.py` and three
   `tests/perf/` budget files. They run only in the slow lane, so their outcome is unknown.
5. **Classification is uncertain for 114 of 183 candidate files.** Directory and import signals disagree or
   only one is present (79 directory-only, 35 import-only); no test declares its domain, level or size. The v0
   import rule takes its component roots from the ownership map (`architecture_design_notes.md` §3.1): pipeline,
   kernel and platform are shared substrate, so importing them is not a gameplay signal (626 files import only
   substrate), and party/group has no oracle or owner, so the 7 files that only import it are `unowned-domain`
   and outside the candidate set. The result, 183, is below the planner's 204 (2026-09-28; 89 files with both
   signals against 69 here). The two rules differ (the planner's import list ended in an ellipsis and included
   party, its directory rule for integration tests is not fully specified, and the tree now has 21 more test
   files). The rule was not tuned toward 204.
6. **Coverage is local and provisional,** from one run that also changed which tests pass (above). There is
   no CI coverage job.
7. **Mutation evidence covers one target** (`src/core/conservation.py`); 117 of 177 mutants survived and none
   are classified as equivalent. The survivors are untested guards, not known defects.
8. **Run-to-run variance is not measured.** Each SHA was run once for this document (the 11 carried
   failures did repeat across four runs, which is the only variance evidence).

## Handoff to Epic B

`tests/mutation/baselines/` is a new tree under `tests/` that holds data, not tests. It should be on
Epic B's taxonomy input list so the level and convention document classifies it on purpose. It has not
been restructured. Its shape check lives in `tests/unit/tools/` because that directory has a CI lane.

## Reproduce

```
# per SHA, in a clean worktree at a real path
pytest tests/ -m "not slow and not extra_slow" -q -p no:cacheprovider --junitxml=<run>.xml
# post-repair only: prefix with `coverage run --branch --source=src -m`, then `coverage json -o <cov>.json`
python3 tools/test_architecture/core_rpg_report.py --repo-root <worktree> --sha <sha> --as-of 2026-09-30 \
    --junit <run>.xml [--coverage <cov>.json] --out-dir <dir>
```
