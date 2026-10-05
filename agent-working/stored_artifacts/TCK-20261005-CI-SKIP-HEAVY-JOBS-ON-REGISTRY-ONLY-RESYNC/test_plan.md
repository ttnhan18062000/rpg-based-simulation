---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | pytest on a temp git repo with an injected fetcher | `git patch-id --stable` and the Actions run/job conclusions as the module defines them | identical patch true; code change, main context shift, red / cancelled / timed out / in progress / no jobs / API error / missing BEFORE / other events all false | `pytest tests/unit/tools/test_registry_resync_skip.py` |
| 2 | live CI | PR #338 runs, REST jobs API as ground truth | GitHub Actions `actions/runs/{id}/jobs` conclusions | (a) 11 jobs skipped after a green run; (b) code change runs everything; (c) identical patch after a cancelled run runs everything | `gh api repos/.../actions/runs/{id}/jobs` for runs 37257429099, 37257718796, 37257781454 |
| 3 | doc review | read | `docs/testing/migration_ci_lanes.md` "Registry re-sync skip" | accepted risk stated plainly | read the section |
| 4 | audit | `sys.addaudithook` open hook per CI job scope, with a positive control | actual file opens during pytest | no skipping job holds a real read of `docs/REGISTRY.yaml` | audit scripts run once at origin/main 9bf34765b (results in investigation.md) |

## Regression pins
- `tests/static/test_ci_narrow_path_filtered_jobs.py`, `test_ci_step_summary_reporting.py`, `test_ci_uv_install.py`: updated for the new job; `pytest tests/static tests/architecture tests/docs tests/integrity tests/refactor` must pass.
- `tests/tools/test_generate_registry.py`: the real-registry drift check, which also proves Tools f-z holds a real reader.
