---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC
phase: done
date: 2026-10-05
tags: [testing]
---

# TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC

## Title
Skip the heavy CI jobs on a REGISTRY-only re-sync push when the previous commit passed

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
When a PR goes CONFLICTING on `docs/REGISTRY.yaml` alone, the fix is a sync merge from `origin/main` plus a regenerated REGISTRY, and that push reruns every CI job although the PR's own code did not change. Owner direction (2026-10-05, relayed by `test-architecture-reviewer`): "skip if the previous commit passed". Brief: `.claude/handover/test-architecture-reviewer.registry_resync_ci_skip_brief.md` on the main checkout (untracked).

## Scope
- A unit-tested module `tools/test_architecture/registry_resync_skip.py` deciding `pr_content_unchanged` (fail open): `pull_request`/`synchronize`, BEFORE present in the clone, same `git patch-id --stable` of the PR's own patch (REGISTRY excluded) before and after, and every `Tests` run on BEFORE green or skipped.
- A workflow gate output and `if:` conditions on the jobs whose result depends on nothing but the PR content; the decision and the BEFORE SHA written to `$GITHUB_STEP_SUMMARY`.
- Classification of which tests read the real `docs/REGISTRY.yaml` (measured, not guessed); jobs holding a real reader keep running, lint and the cheap docs/registry checks keep running.
- Per-job measured durations, the accepted-risk statement, doc updates, a live demonstration on a real PR with positive and negative controls.
- Folded in by the reviewer's request: the Epic C criterion 2 run 2 record paragraph in `agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING.md` (verbatim, docs only).

## Out of Scope
- Stopping PRs from committing `docs/REGISTRY.yaml` (a CLAUDE.md ticket-close rule owned by agent-working-design; the owner chose not to pursue it now).
- Any Mechanics Bible, parity-ledger, `src/` or RPG test change.

## Acceptance Criteria
1. Unit tests (temp git repo): identical patch true; code change false; REGISTRY-only change true; context shift caused by main false; previous run red / cancelled / in progress / API error false; missing BEFORE false.
2. Live demonstration, run IDs from the REST jobs API: (a) REGISTRY-only re-sync after a green run skips the heavy jobs; (b) a push changing a code file runs everything; (c) a re-sync after a red or cancelled run runs everything.
3. Docs state the accepted risk plainly (PR code combined with new main commits is untested before merge; the post-merge run on main always runs everything).
4. Every job that holds a measured real REGISTRY reader keeps running.

## Related Tickets
- `TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS`, `TCK-20260906-CI-FRONTEND-PATH-FILTER` (the existing path-based skip pattern)

## Related Docs
- `docs/testing/migration_ci_lanes.md` (path-based skip section)
- `docs/plans/test_architecture/roadmap.md` §11

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC/` (investigation.md, plan.md, test_plan.md)

## Related Code Areas
- `.github/workflows/test.yml`, `tools/test_architecture/`, `tests/unit/tools/`

## Assumptions / Open Questions
- The previous-run check uses the Actions runs/jobs REST API (`actions: read`) instead of `commits/{sha}/check-runs`, because a check run does not name its workflow.
- The decision runs in its own light job, not inside the `changed-files` gate, so the heavy jobs do not wait for that gate's full clone. Measured in the live run.

## Implementation Notes
- `tools/test_architecture/registry_resync_skip.py`: `decide()` never raises; every error is `false`. The patch id is `patch-id --stable` of the diff from `merge-base(base, commit)` to the commit with `docs/REGISTRY.yaml` excluded. The previous-run check reads the Actions runs/jobs REST API (`actions: read`), not `commits/{sha}/check-runs`, because a check run does not name its workflow.
- `resync-gate` is its own job (blobless full-history clone), 14-18 s measured, not a step of `changed-files` (about 100-120 s), so the heavy jobs do not wait on the full clone.
- Skipping jobs (11): unit-core-world, unit-gameplay, unit-infra, integration, api-cli-engine, agent-orchestration, simulation-quality, perf-cert-arena, migration-lanes, scenario-lane, frontend. Kept: tools-a-e, tools-f-z (real readers), arch-docs, typecheck, code-health (+SARIF).
- The REGISTRY-reader classification was measured with a `sys.addaudithook` `open` hook injected through `sitecustomize` into every pytest process and subprocess, one scope per CI job, at origin/main `9bf34765b`, with a positive control. Real reads: only `tests/tools/` and `tests/codebase/` (14 reads of the real file). Zero in unit, integration, api/agent, simulation_quality, architecture/docs/integrity/static/refactor, perf/cert/arena/mechanic_scenarios. Pytest only: Makefile targets run outside pytest were not audited, which is why arch-docs and code-health keep running.
- Run 1 on the PR went red for two reasons my local scope had missed: REGISTRY not yet regenerated (the Tools f-z drift check, which also proves that job holds a real reader) and three workflow-shape pins under `tests/static/` (`test_ci_narrow_path_filtered_jobs.py`, `test_ci_step_summary_reporting.py`, `test_ci_uv_install.py`), updated deliberately for the new job.
- Deviations from the brief: a separate gate job instead of an output on `changed-files` (latency); the Actions API instead of `commits/{sha}/check-runs`. The Epic C run 2 paragraph was folded in verbatim into `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING.md`.

Live demonstration, PR #338, REST jobs API as ground truth (`actions/runs/{id}/jobs`):
- Negative control, first push (event `opened`): run 37255927293, everything ran (red on the two causes above).
- Negative control, previous commit red and patch changed: run 37256809703 (commit 5bd5012ba), all jobs ran, green.
- (a) identical patch after a green run: run 37257429099 (commit 6d20f64e9). It is an empty commit because origin/main had not advanced, so the REGISTRY diff was zero: a degenerate case. Gate 18 s. Skipped: Unit core/world, gameplay, infra, Integration, API/CLI/engine, Agent orchestration, Simulation quality, Perf/cert/arena, Migration lanes, Scenario lane, Frontend. Ran and green: Tools a-e, Tools f-z, Architecture/docs, Type check, Code health, Code health SARIF, Changed files gate.
- (b) a code-file change (module docstring): run 37257718796 (commit 7f4c2bbd8). A snapshot after the gate finished showed Unit core/world, Simulation quality, Unit infra, API/CLI/engine, Agent orchestration, Integration and Unit gameplay in_progress, none skipped. That run was then cancelled by the push for (c), so it has no completed conclusion.
- (c) identical patch after a cancelled run: run 37257781454 (commit 7ed7727de, an empty commit after the cancelled run on 7f4c2bbd8): every heavy job ran, green.
- Not demonstrated live: a true REGISTRY-changing re-sync merge (origin/main had not advanced after the sync at ce6266f5b), and a red (not cancelled) previous run with an unchanged patch. The unit tests cover red, cancelled, timed out, in progress, API error and missing BEFORE.
- Measured savings: about 1,270 runner-seconds per skipped push; wall time barely moves (longest skipped job, Integration, about 7 min; the kept Tools jobs take 3-4.5 min).

## Test Summary
- tests/unit/tools/test_registry_resync_skip.py: 18 passed (temp git repo).
- tests/static, tests/architecture, tests/docs, tests/integrity, tests/refactor: 288 passed, 2 skipped, 2 xfailed.
- tests/tools/test_generate_registry.py: 68 passed after the REGISTRY regeneration.
- CI on PR #338: the runs above.

## Files Changed
- tools/test_architecture/registry_resync_skip.py, tests/unit/tools/test_registry_resync_skip.py
- .github/workflows/test.yml
- tests/static/test_ci_narrow_path_filtered_jobs.py, tests/static/test_ci_step_summary_reporting.py, tests/static/test_ci_uv_install.py
- docs/testing/migration_ci_lanes.md, docs/plans/test_architecture/roadmap.md
- agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING.md

## Completion Summary
Heavy CI jobs that read no real `docs/REGISTRY.yaml` now skip on a pull_request push whose own patch is unchanged and whose previous commit ran green, failing open on everything else. The accepted risk is stated in the docs: the PR code combined with new main commits is untested until the post-merge run on main. No Mechanics Bible, parity-ledger or src/ change.
