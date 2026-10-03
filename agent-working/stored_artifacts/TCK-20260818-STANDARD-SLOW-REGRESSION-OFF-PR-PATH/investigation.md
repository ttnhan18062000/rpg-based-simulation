---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH
tags: [testing, bug]
---

# Investigation — TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH

## Trigger
User asked, exploratively: "for fast development, do you think the slow regression should not
included in the PR check ?" — following a long session of real, direct experience with the
"Slow regression" job's actual per-run cost (multiple ~45-90 minute waits this session alone,
once the job was finally unblocked from its own upstream gating).

## Current behavior (before this ticket)
`.github/workflows/test.yml`'s `slow` job: `if: github.ref == 'refs/heads/main' ||
github.base_ref == 'main'`. `github.base_ref` is set for `pull_request` events to the PR's target
branch — so this condition is true on **every push** to any PR targeting `main`, in addition to
direct pushes to `main` itself. Given `agent-working` is a long-lived branch with an open PR
targeting `main`, every commit on it re-triggered the full slow job.

## Original design intent (found during investigation)
`docs/plans/long_term_development_roadmap.md`'s own P0-1 "What" description (written when the
job was first added, 2026-06-25) already said: "`make lane-legacy-regression` on `main` push
only (slow path)" — the per-PR-push gating that actually shipped was a drift from this original
plan, not a deliberate choice documented anywhere. This ticket's change restores that original
intent rather than introducing a new, undiscussed policy.

## Recommendation given to the user (and approved)
Move the slow job off the per-PR-push path, replacing it with: (a) push to `main` (post-merge
safety net — still catches anything that slipped through before it's live), (b) nightly schedule
(catches regressions with bounded latency without blocking iteration), (c) manual
`workflow_dispatch` (on-demand pre-merge confidence when actually wanted). This preserves the
job's role as a real regression gate while removing its cost from the fast iteration loop.

## Verification performed
- YAML syntax validated.
- Trigger-matrix reasoning verified by hand for all 4 relevant event types (`pull_request`,
  `push` to `main`, `schedule`, `workflow_dispatch`).
- Could not trigger a real `schedule`/`workflow_dispatch` GitHub Actions event from this sandbox
  to observe it firing live — disclosed as a real verification gap in the ticket's Test Summary,
  not silently assumed to work.
