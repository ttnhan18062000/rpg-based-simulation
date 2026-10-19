---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
artifact_type: investigation
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Investigation — shared-state audit for xdist in Integration, Tools f–z and API/CLI/engine

Method: a static sweep of the three jobs' test sets (data/runs, reports/, data/calibration, chdir, ports, fixed /tmp, env writes, conftest autouse state), then an empirical run of each set under `pytest -n 3 --dist loadgroup` (6-core dev machine, 8 GB, load average 7-12 from other sessions), compared with a serial run for every failure. Counts are `--collect-only -q` with `-m "not slow and not extra_slow"` on origin/main df3cb7256.

## Baseline collect counts (AC2)
| Job | Command paths | Collected |
|---|---|---|
| Integration | tests/integration | 1083 (60 deselected) |
| Tools · f–z | tests/tools --ignore-glob='tests/tools/test_[a-e]*.py' | 3494 (28 deselected) |
| API / CLI / engine | tests/api cli logging engine observability visual_assets | 2780 (1 deselected) |

## Shared state that is already safe
- **Run directories.** `src/engine/run_identity.py::create_run_directory` never reuses a default run id: it takes a fresh id and retries, so two processes cannot share a run folder. `tests/conftest.py::_mocked_rng_kernel_output_goes_to_tmp_path` sends a mocked-rng kernel's output to `tmp_path`. No test in the three sets carries `real_data_runs`.
- **Registries and caches.** conftest's autouse fixtures reset the item, resource and catalog registries per test; each xdist worker is its own process, so module-level state is per worker, as it is in the serial run.
- **Environment.** No `os.environ[...] =` / `putenv` writes in the three sets (monkeypatch only). agent-working-planner's scan of tests/tools agrees: no raw `os.chdir`, fixed `/tmp` strings never written, `test_disk_warning` under `tmp_path`, `test_generate_registry` only reads docs/REGISTRY.yaml. agent-working-planner replied "known none" to the fyi (AC6).
- `data/calibration/` and `reports/`: no test in the three sets writes to either (grep hits are strings in assertions or `tmp_path` trees).

## Findings per job
**Integration (1083):** `-n 3` run: 1077 passed, 6 skipped, 0 failed (395 s on the loaded dev machine). No finding.

**API / CLI / engine (2780):** `-n 3`: 2778 passed, 1 skipped, 1 failed; repeated on tests/visual_assets alone, 1 failure in 4 runs, a different test of one file each time.
- **FINDING (fixed by serial step):** `visual_assets/store/lock.py::lock_path()` is `config.CATALOG_ROOT / ".store.lock"`, the real tracked catalog. The `roots` fixture (`tests/visual_assets/store/unit/conftest.py`) redirects only `QUARANTINE_ROOT` and `REVIEW_ROOT`. Every writing store command takes `LOCK_EX|LOCK_NB` on that file, so two workers collide: `GateError store_locked`, exit 2, empty stdout. Reproduced deterministically by holding the flock from another process: `test_the_clock_is_read_only_here` fails with `IndexError` at test_cli.py:49 and `test_intake_exit_codes` with `assert 2 == 0` at :38, the xdist signatures. **It is not a serial flake**: `test_cli.py` passes alone (9 passed) and in file order, and the whole visual_assets set passes serially.
- Handling: the files that take the lock (tests/visual_assets/store/, test_review_cli.py, test_key_usage.py) run in a separate **serial** step of the same job; the parallel step `--ignore`s exactly those paths. 1222 + 1329 = 2551 = the whole directory. The fixture fix is issue #657 (asset-planner, rpg-planner cc); the serial step and the three `--ignore` lines are removed once it is on main. Owner ticket id: to be recorded when filed.

**Tools · f–z (3494):** `-n 3`: 3460 passed, 27 skipped, 1 xfailed, 6 failed. Each failure re-run serially:
- `test_monitoring_integrity_backlog_check.py::test_real_corpus_is_at_or_below_all_five_conditions`, `test_run_dedup.py::test_real_corpus_duplicate_classification_matches_measured_baseline`, `test_security_gate_firing_check.py::test_live_corpus_matches_known_ground_truth`: **fail serially too** in this local checkout (they read the monitoring corpus, which differs here); they pass in CI serially and only read, so they are not caused by xdist. Not fixed here.
- `test_hand_closure_time.py::test_cli_*` (3): hit the 60 s per-test resource budget (`TimeoutError`) while the machine's load average was 12; the same file plus two neighbours then passed 3 of 3 times under `-n 3` at load 7-9 (about 2 s per test serially). Load, not shared state. Risk to watch on the 4-vCPU runner with `-n auto`: subprocess-heavy tests under the 60 s budget; AC3's three runs show it.

## Decisions
- `-n auto --dist loadgroup` on the five directory steps and the parallel visual_assets step of the API job, on Integration, and on Tools f–z. No `xdist_group` markers were needed beyond the serial step.
- No jobs are added (21 before, 21 after; pinned by `tests/static/test_ci_xdist_in_critical_path_jobs.py`). Optional lane merge (item 5): not done; each candidate lane saves under a minute and the job count must not matter more than the risk.
- JUnit: xdist writes one XML from the controller; `tools/ci_junit_summary.py` read a real `-n 3` XML correctly (counts and duration). The Aseprite note step now runs after the merge and reads the merged XML, so it counts both visual_assets steps.
- The base-branch collect-only step lists the same paths as the head steps (the three store-lock paths overlap the directory path; pytest collects a node once, 2551 either way).

## Finding 2, from CI (run 39202868037 attempt 3, job 117902609735): a fixed-name temp file in the real workflows directory
`tests/tools/test_implement_ticket_native_refusal.py::_run_with_unported_list` writes ONE fixed-name copy of `.claude/workflows/implement-ticket.js` (`_tmp_refusal_populated.js`) into the real repo directory and deletes it in `finally`. Its parametrized tests, spread over xdist workers, delete each other's copy: `FileNotFoundError` in one test (attempt 3; attempts 1 and 2 passed by timing). Reproduced locally: `pytest <file> -n 3` fails 2 of 9 tests on 3 of 3 tries; serially it passes 9 of 9. Handling: that file runs in its own **serial** step of Tools f–z (the parallel step `--ignore`s it; the base-branch collect step lists it too, so collect counts are unchanged); the two JUnit files are merged. Remove the step when the test uses `tmp_path` or a unique name: agent-working's file, no ticket yet (finding sent to testing-planner). Sequential steps also remove a second hazard: other tests glob `.claude/workflows/*.js` and could read the temp copy mid-write.

## Integration long pole, measured on CI (run 39202868037 attempt 1, `--durations=15`)
Pytest time 234.76 s (job 4.37 min). Top 15 (s): 122.80 `test_lair_region_trauma_reachability.py::test_moon_cave_region_records_zero_trauma_across_full_corpus_run`; 21.23 `test_camp_raid_targeting.py::test_a_matured_camp_raids_nothing_in_a_real_run`; 15.32 `test_decision_trace_determinism.py::test_decision_trace_identical_across_two_seeded_runs`; 10.17 `test_information_seeking_wiring.py::test_information_need_detector_fires_from_execute_brain`; 9.52 `test_recipe_reachability_under_real_kernel_tick.py::...learned_recipes_resolve...`; 4.00; 3.43; 3.37; 2.56; 2.41; 2.39; 2.17; 2.00; 1.71; 1.71. **One test is a long pole: 122.8 s, 52% of the 234.8 s.** It alone bounds the job at about 2 minutes of tests plus setup however many workers there are; with 4 workers the rest (about 112 s of the top 15, plus 1,000 fast tests) fits beside it. Follow-up, not part of this PR: split that test or ask its owner (world / observability) for a shorter corpus.
