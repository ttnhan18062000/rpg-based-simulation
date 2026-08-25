---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP
phase: open
date: 2026-08-25
tags: [testing]
---

# TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP

## Title
Add a frontend/UI job to .github/workflows/test.yml -- CI has zero vitest/npm/build coverage today

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`.github/workflows/test.yml` (the `Tests` workflow, 12 jobs) has zero references to `npm`,
`vitest`, or `frontend/` anywhere -- confirmed by grepping the entire file for those terms
(zero matches). Every job runs only Python (`pytest`) against `src/`/`tests/`. This means the
frontend's own test suite and build gate have never once been verified by CI, on any PR, ever --
they only get checked when a human or agent happens to run them locally.

Surfaced during `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (PR #76): that epic added 26 new/updated
vitest tests (`frontend/src/test/useSimulation.test.tsx`, `frontend/src/test/SimulationLoadingGate.test.tsx`)
and depends on `npm run build` staying clean (in particular `frontend/src/components/Header.tsx`'s
exhaustive `Record<SimStatus, string>`, which fails `tsc -b` if a future `SimStatus` change forgets
to update it) -- none of which CI would have caught if a future PR broke either, since nothing in
`test.yml` runs them. This is a real, pre-existing gap the epic's own frontend work exposed, not a
gap the epic itself introduced.

## Scope
- Add a new job to `.github/workflows/test.yml` (matching the existing jobs' structure: `actions/checkout@v5`,
  a Node setup step, `npm ci` in `frontend/`, then `npx vitest run` and `npm run build`).
- Wire it into the same `pull_request`/`push: [main]`/`schedule`/`workflow_dispatch` triggers the
  rest of the workflow already uses -- no new trigger config needed, just a new job under the
  existing `jobs:` block.
- Decide whether it needs its own `changed-files` path-filter gate entry (like `perf-cert-arena`/
  `migration-lanes` do) or should just always run given frontend tests are fast (~1-2s per the
  epic's own measured runs) -- investigate before assuming either way.

## Out of Scope
- Adding a real headless-browser/E2E job (Playwright etc.) -- that's a much bigger, separate
  undertaking (see `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s own experience: Playwright's Chromium
  download was blocked by a network filter in that ticket's implementing sandbox -- confirm this
  isn't also a problem in the actual GitHub Actions runner environment before assuming it'll work
  there, since GitHub-hosted runners are a different network environment than this session's
  sandbox).
- Any change to the frontend code itself, or to any existing job in `test.yml`.
- Fixing any test failure this new job might surface once wired in -- if it finds a real, currently-
  undetected frontend regression, that's a separate finding to report/ticket, not silently fixed
  here.

## Acceptance Criteria
- [ ] A new job in `.github/workflows/test.yml` runs `cd frontend && npm ci`, `npx vitest run`, and
      `npm run build` on every PR and on push to main
- [ ] The new job appears in `gh pr checks` output on a real PR and genuinely fails if a frontend
      test or the build breaks (verified with a deliberate real test, not assumed)
- [ ] Existing 12 jobs are unaffected -- `test.yml`'s other jobs' behavior is unchanged

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (the epic whose frontend work exposed this gap)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- frontend/package.json (for the exact `npm ci`/`vitest`/`build` script names already in use)

## Assumptions / Open Questions
- Whether GitHub-hosted `ubuntu-latest` runners can reach the npm registry / Node setup action
  without the kind of network filtering `TCK-20260821-LIVE-MAP-PERF-VALIDATION` hit in its own
  sandbox -- almost certainly yes (every other job already does `pip install` successfully), but
  worth a real first CI run to confirm rather than assuming.
- Node version to pin (`actions/setup-node@v4` with a specific version, matching whatever
  `frontend/package.json`'s `engines` field or `.nvmrc` specifies, if either exists -- check before
  picking one).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
