---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH
phase: done
date: 2026-08-18
tags: [testing, bug]
---

# TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH

## Title
Take the "Slow regression" CI job off the per-PR-push path — run it on `main` push, nightly
schedule, and manual dispatch instead

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
This session spent extensive time (multiple hours across many iterations) fixing real bugs the
"Slow regression" job's first-ever-completed run surfaced (it had been gated behind every other
CI job succeeding first, and those had never all succeeded together before this session). Once
unblocked, the job itself takes ~45-90 minutes end-to-end (corpus-diversity isolated suite ~15-20
min, broad slow/extra_slow suite ~25 min, legacy regression ~2 min) and was gated to run on
**every push to a PR targeting `main`** (`github.base_ref == 'main'`) — meaning every iteration
of ongoing work on a long-lived PR branch (like `agent-working`) paid this full cost on every
single commit.

User-requested tradeoff, discussed and explicitly approved: move the slow suite off the per-push
iteration path (trading away per-push visibility into slow-lane regressions) in exchange for fast
feedback (a few minutes) on every push — while keeping the slow suite as a real, still-required
safety net rather than removing it.

## Scope
- `.github/workflows/test.yml`: add `schedule` (nightly, `0 3 * * *`) and `workflow_dispatch`
  triggers at the workflow level.
- Change the `slow` job's `if:` condition from `github.ref == 'refs/heads/main' ||
  github.base_ref == 'main'` to `github.ref == 'refs/heads/main' || github.event_name ==
  'schedule' || github.event_name == 'workflow_dispatch'` — removing the per-PR-push trigger
  while keeping: (a) push to `main` itself (post-merge safety net), (b) nightly schedule, (c)
  manual dispatch for on-demand pre-merge confidence.
- Update 2 historical audit/roadmap doc entries (`docs/audits/D18_ci_release_pipeline.md`,
  `docs/plans/long_term_development_roadmap.md`) for parity — both had "RESOLVED"/"DONE" notes
  describing the now-changed "gated to PRs targeting main" behavior as current; appended (not
  rewrote) a dated correction note to each, per this repo's established historical-record
  convention.

## Out of Scope
- Any change to the `slow` job's own steps, `needs:` dependency chain, or the fast-lane jobs'
  trigger conditions — all unchanged, still run on every PR push as before.
- Any change to what the slow suite actually tests, or any of the real bugs it already surfaced
  and this session already fixed separately.
- Branch protection rules on GitHub itself (requiring the `slow` job as a merge-blocking required
  check) — outside this repo's own files; noted as a recommendation, not configured here.

## Acceptance Criteria
- [x] `.github/workflows/test.yml` YAML validated (`python3 -c "import yaml;
      yaml.safe_load(open('.github/workflows/test.yml'))"`).
- [x] `slow` job's `if:` condition no longer includes `github.base_ref == 'main'`.
- [x] `schedule` and `workflow_dispatch` triggers added at the workflow level.
- [x] 2 historical docs updated for parity via appended (not rewritten) dated notes.

## Related Tickets
- All of this session's `TCK-20260817-*`/`TCK-20260818-*` slow-suite investigation and fix
  tickets (the real bugs this job surfaced) — unaffected by this ticket, which only changes when
  the job runs, not what it tests.

## Related Docs
- `docs/audits/D18_ci_release_pipeline.md` (F1 finding, updated)
- `docs/plans/long_term_development_roadmap.md` (P0-1 CI Test Automation, updated)
- `docs/testing/migration_ci_lanes.md` (describes `make lane-*` targets themselves, not GitHub
  Actions trigger conditions — checked, no stale content found needing an update)

## Related Stored Artifacts
`stored_artifacts/TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH/`

## Related Code Areas
- `.github/workflows/test.yml`

## Assumptions / Open Questions
- Whether GitHub's own branch-protection "required checks" configuration for `agent-working`'s
  target PR currently lists the `slow` job as required — if so, removing it from the per-PR-push
  path means it will simply never satisfy that requirement anymore (since it won't run on PR
  pushes at all), which could either unblock merges entirely (if required-check enforcement
  degrades gracefully for jobs that don't run) or block them permanently (if GitHub still expects
  a status that will never arrive). This is a GitHub repository-settings concern outside this
  ticket's own files — flagged for the user/repo owner to check separately, not resolved here.

## Implementation Notes
Chose `github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'` explicitly
(rather than trying to infer from `github.ref`) since neither event type sets `base_ref`, and
using explicit event-name checks is clearer than ref-based inference for these two trigger kinds.
Kept `github.ref == 'refs/heads/main'` unchanged — pushes landing on `main` (i.e., a merge
completing) still trigger the slow job as a real post-merge safety net.

## Test Summary
- YAML syntax validated.
- Manual review of the resulting trigger matrix: `pull_request` events → `slow` job's `if:` is
  false (skipped, matching intent); `push` to `main` → true (unchanged); `schedule` → true (new);
  `workflow_dispatch` → true (new).
- Did not (and could not, from this sandbox) trigger a real `schedule`/`workflow_dispatch` GitHub
  Actions run to observe it firing — this is a GitHub-side event type this environment cannot
  simulate locally. Documented as a real, disclosed verification gap rather than claimed as
  fully tested.

## Files Changed
- `.github/workflows/test.yml`
- `docs/audits/D18_ci_release_pipeline.md`
- `docs/plans/long_term_development_roadmap.md`

## Completion Summary
Implemented the user-approved tradeoff: the "Slow regression" job no longer runs on every PR
push (removing ~45-90 minutes from every development iteration on a long-lived PR branch), while
remaining a real safety net via `main`-push, nightly schedule, and manual-dispatch triggers.
Updated 2 historical docs for parity without rewriting their original historical record.
