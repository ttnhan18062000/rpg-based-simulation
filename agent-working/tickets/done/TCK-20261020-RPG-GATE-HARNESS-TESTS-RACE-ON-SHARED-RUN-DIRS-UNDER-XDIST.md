---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-HARNESS-TESTS-RACE-ON-SHARED-RUN-DIRS-UNDER-XDIST
phase: done
date: 2026-10-20
tags: [testing, regression]
---

# TCK-20261020-RPG-GATE-HARNESS-TESTS-RACE-ON-SHARED-RUN-DIRS-UNDER-XDIST

## Title
The rpg gate harness unit tests stop racing each other on `data/runs/rpg-gate-sandbox_world-s<seed>-<sha8>*` under pytest-xdist.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
rpg-planner's Lane B, 2026-10-20: under `pytest -n 2 --dist loadgroup`, run 3 times on origin/main e52719485 and on rpg-pre-v1-fixes c4c03f3c9, two tests in `tests/unit/tools/test_rpg_gate_harness.py` fail intermittently:
- `::test_run_directories_are_removed_by_id_and_cost_is_recorded` fails intermittently. It globs `data/runs/<run_id_for(WORLD, seed, SHA)>*`, the prefix WITHOUT the per-invocation token. Every test in the file that calls `_run` (same WORLD, seeds and SHA) creates directories with that prefix. A parallel worker's live run directory then matches, and the "removed" assertion fails. The harness is correct; the test's glob is too wide.
- `::test_the_harness_hash_covers_the_metrics_module_source_and_name` errored in SETUP on 2 of 3 runs. Its only fixture is `tmp_path`, so the cause is not known yet.

Serial runs pass, and so does CI unit-infra today. This is a latent flake. rpg filed its own half separately (TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST), which excludes this file.

## Scope
1. **Test-only fix. Do NOT edit `tools/test_architecture/rpg_gate_harness.py`.** Its source is in the harness hash, and changing it moves the hash under rpg's v1 baseline. Choose one:
   - (a, preferred) mark the module `pytestmark = pytest.mark.xdist_group("rpg_gate_harness_runs")`, so every test that creates those directories runs on one worker under `--dist loadgroup`. First check how CI invokes xdist for this file. If CI does not use `--dist loadgroup` for unit-infra, (a) does nothing there; say so and use (b).
   - (b) make the glob exact for this invocation: monkeypatch the token source the harness uses (`os.getpid`/`time.time` at `run_matrix`), or read the run ids from the matrix if it already records them. Do not add fields to the harness.
2. **The setup error:** reproduce with `pytest -n 2 --dist loadgroup tests/unit/tools/test_rpg_gate_harness.py` repeated (`--count` or a loop, 10x). Quote the error. If its cause is outside this file (a conftest, a shared fixture, another team's autouse), stop and route it with `python3 -m tools.sessions.route <path>`; don't fix another team's file here.
3. Check the other rpg_gate test files (`test_rpg_gate_candidate.py`, `test_rpg_gate_report.py`, `test_rpg_gate_workflow_support.py`) for the same untokened glob over `data/runs`. Fix any you find the same way.

## Out of Scope
- rpg's half (TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST).
- Any harness source change.

## Acceptance Criteria
- [x] AC1: 10 repeats of `pytest -n 2 --dist loadgroup tests/unit/tools/test_rpg_gate_harness.py` pass. Also 10 repeats with the file run alongside `tests/unit/tools -k rpg_gate`. Quote the counts.
- [ ] AC2 (NOT MET, left unticked by testing-planner's ruling): the setup error is explained (quoted), and either fixed in this file or routed to its owner with a ticket or message id.
- [x] AC3: `git diff origin/main -- tools/test_architecture/rpg_gate_harness.py` is empty (the harness hash is unchanged).
- [x] AC4: CI on the PR is green.

## Related Tickets
- TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST (rpg's half)
- the CI-runtime epic, child 1 (xdist, #659); the serial-steps cleanup

## Related Docs
- (none)

## Related Stored Artifacts
- (none)

## Related Code Areas
- tests/unit/tools/test_rpg_gate_harness.py
- tools/test_architecture/rpg_gate_harness.py (read only: `run_id_for`, `run_matrix` token)

## Assumptions / Open Questions
- Order: not a v1 blocker. Any time; it is test-only and does not move the harness hash.

## Implementation Notes
- CI runs tests/unit/tools with `-n auto --dist loadgroup`, but a module xdist_group would only serialize this file, so I used option (b): the test spies on `h.run_one`, reads the invocation's token, and globs `run_id_for(WORLD, seed, SHA, token)*`. The harness is untouched (empty diff).
- Before the fix the failure reproduced 6 of 6 runs of `-n 2 --dist loadgroup` on this file (1 failed, 14 passed).
- After: 10 of 10 runs pass on the file (15 passed each); 10 of 10 pass with `tests/unit/tools -k rpg_gate` alongside (168 passed each).
- Other rpg_gate test files (candidate, report, workflow_support) have no `data/runs` glob.
- AC2 (setup error): NOT reproduced. 16 runs on this file and one full `pytest tests/unit -n 2 --dist loadgroup -m "not slow and not extra_slow"` (8347 passed, 1 failed, 5 skipped) gave no setup ERROR. The one failure was tests/unit/engine/test_run_manifest_signal_contract.py::test_a_canonical_run_records_its_contract_and_work_model, `FileNotFoundError: Manifest not found for run_id: sc_manifest_canonical`. That test uses a fixed run id under the shared data/runs, so it belongs to rpg's TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST, not this file.

## Test Summary
AC1: 10 of 10 green on the file and 10 of 10 alongside `tests/unit/tools -k rpg_gate`. AC3: harness diff empty. AC4: read from the PR's CI.

## Files Changed
- tests/unit/tools/test_rpg_gate_harness.py

## Completion Summary
The race is fixed in the test. AC2 not met: not reproduced (16 file runs + 1 full unit run); the symptom moved between tests across branches, which points at a worker-level cause; routed to rpg's TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST; closed by testing-planner's ruling; reopen if it recurs with a traceback.
