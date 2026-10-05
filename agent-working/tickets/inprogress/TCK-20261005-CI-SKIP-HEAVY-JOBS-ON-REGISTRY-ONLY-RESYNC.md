---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC
phase: open
date: 2026-10-05
tags: [testing]
---

# TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC

## Title
Skip the heavy CI jobs on a REGISTRY-only re-sync push when the previous commit passed

## Status
INPROGRESS

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
- None yet.

## Related Code Areas
- `.github/workflows/test.yml`, `tools/test_architecture/`, `tests/unit/tools/`

## Assumptions / Open Questions
- The previous-run check uses the Actions runs/jobs REST API (`actions: read`) instead of `commits/{sha}/check-runs`, because a check run does not name its workflow.
- The decision runs in its own light job, not inside the `changed-files` gate, so the heavy jobs do not wait for that gate's full clone. Measured in the live run.

## Implementation Notes
- To be filled at close.

## Test Summary
- To be filled at close.

## Files Changed
- To be filled at close.

## Completion Summary
- To be filled at close.
