---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC

Written at close from what was done; the work was hand-orchestrated from the reviewer's brief, so this records findings, not a pre-implementation plan.

## Findings
- The `changed-files` gate in `.github/workflows/test.yml` diffs `base.sha...head.sha`, the whole PR, so it cannot tell what the latest push changed. Only frontend, perf-cert-arena, scenario-lane and migration-lanes had an `if:`; the other jobs always ran. Branch protection on main is disabled, so a skipped job blocks nothing.
- `changed-files` takes about 100-120 s (full clone), so making the heavy jobs wait on it would add that latency to every push. A separate `resync-gate` job with a blobless full-history clone takes 14-18 s.
- A check run does not name its workflow, so "every check run of Tests on BEFORE" is read through the Actions runs/jobs API instead (`actions: read`).

## Which tests read the real docs/REGISTRY.yaml (measured)
- Method: a `sys.addaudithook` `open` hook injected through `sitecustomize` into every pytest process and subprocess, tagged with `PYTEST_CURRENT_TEST`, one pytest scope per CI job, at origin/main `9bf34765b`. Positive control: a known read of the real file was logged.
- Result: real reads (14) only in `tests/tools/` and `tests/codebase/`: `test_generate_registry.py::TestRealDocsTree`, `test_premise_staleness_check.py`, `test_post_native_run_check.py`, `test_registry_query.py`, `test_tools_orphan_check.py`, `test_codebase_health_baseline.py`, `test_codebase_health_snapshot.py`. Zero in unit, integration, api/agent, simulation_quality, arch-docs scopes, perf/cert/arena/mechanic_scenarios. `tests/integrity/test_registry_merge_driver.py` read temp copies.
- Limit: pytest only. Makefile targets run outside pytest were not audited; arch-docs and code-health therefore keep running.
- The local audit run had 46 failures in the tools/codebase scope and 2 in integration (for example `tests/codebase/test_ast_grep_rules.py` errors and `test_executor_determinism`). They were not investigated: the audit only needs which files were opened, and CI ran those jobs green on the PR.

## Job durations (3 recent PR runs, seconds)
Unit core/world 134/113/130; gameplay 42/41/38; infra 201/163/163; Integration 408/419/349; API/CLI/engine 170/174/197; Agent orchestration 42/43/41; Simulation quality 36/39/47; Perf/cert/arena 113; Migration lanes 123; Scenario lane 28; Tools a-e 195/197/160; Tools f-z 225/258/265; Arch/docs 74/72/63.

## Risks found
- Three tests under `tests/static/` pin the workflow shape and failed until updated deliberately (the first PR run was red on them and on REGISTRY drift).
- A skipped re-sync leaves the PR code combined with new main commits untested before merge; the post-merge push to main always runs everything. Owner-accepted.
