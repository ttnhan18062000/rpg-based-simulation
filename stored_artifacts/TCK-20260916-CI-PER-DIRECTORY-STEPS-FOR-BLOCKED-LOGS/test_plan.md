# Test Plan — TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS

| Case | Verification |
|---|---|
| `unit-infra`'s steps name their own directories, identifiable without log access | Read the edited workflow directly: 17 steps named `Run: tests/unit/<path>` |
| Every split step carries `if: always()` | Read the edited YAML directly: confirmed on all 17 `Run:` steps plus the `Merge JUnit XML` step |
| Before/after counts match | Baseline (combined): 2696 passed, 1 skipped, 0 failed. Per-directory summed: 2696 passed, 1 skipped, 0 failed — exact match |
| CLAUDE.md documents the technique, only after authorization | `AskUserQuestion` asked and answered "Yes, proceed with the edit" before any CLAUDE.md edit; addition pinned by `tests/docs/test_ci_per_directory_steps_documented.py` (3 tests) |
| YAML stays valid | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — valid; 24 total steps in the `unit-infra` job |

Executed: `pytest tests/docs/test_ci_per_directory_steps_documented.py tests/docs/test_ci_triage_absent_run_branch.py -v` — 11 passed, no collision with the pre-existing precedent tests.
