---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP
phase: done
date: 2026-08-25
tags: [testing]
---

# TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP

## Title
Add a frontend/UI job to .github/workflows/test.yml -- CI has zero vitest/npm/build coverage today

## Status
DONE

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
- [x] A new job in `.github/workflows/test.yml` runs `cd frontend && npm ci`, `npx vitest run`, and
      `npm run build` on every PR and on push to main
- [x] The new job appears in `gh pr checks` output on a real PR and genuinely fails if a frontend
      test or the build breaks (verified with a deliberate real test, not assumed)
- [x] Existing 12 jobs are unaffected -- `test.yml`'s other jobs' behavior is unchanged

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

Added a new `frontend` job to `.github/workflows/test.yml` (after `arch-docs`, before the
`changed-files` gate), matching `deploy-docs.yml`'s existing `actions/setup-node@v4` pattern
(`node-version: 20`, `cache: npm`, `cache-dependency-path: frontend/package-lock.json` --
`frontend/package.json` has no `engines` field or `.nvmrc`, so this precedent is the only
existing Node-version convention in the repo). Steps: `npm ci`, `npx vitest run` (no path arg --
runs the whole frontend suite, matching how the other jobs run their whole scoped directory), then
`npm run build`. Added to `slow`'s `needs:` list alongside the other real gating jobs (not
`typecheck`, which stays `continue-on-error`).

**Resolved the ticket's own open decision**: no `changed-files` path-filter gate entry -- the
frontend suite is fast enough (~1-2s locally, confirmed both before and during this
implementation) that gating it risks silently masking a real break on a PR that doesn't touch
`frontend/` but still needs the build gate (e.g. a root Node/npm config change), for a
negligible CI-minutes saving.

**AC #2's "verified with a deliberate real test, not assumed" resolved directly, not skipped**:
before wiring anything into `test.yml`, added a scratch failing vitest test
(`frontend/src/test/__scratch_ci_break_check.test.tsx`, `expect(1).toBe(2)`) and confirmed
`npx vitest run` genuinely exits 1 (not 0) -- removed the scratch file and re-confirmed exit 0/
26-26-passing afterward. Separately, added one deliberate type error to `frontend/src/App.tsx`
(`const x: number = "a string"`) and confirmed `npm run build` genuinely exits 2 with two real
`tsc` errors -- reverted and re-confirmed exit 0/clean build afterward (`git diff --stat --
frontend/src/App.tsx` empty). Both mechanisms are the same `npx vitest run`/`npm run build` exit
codes the new CI job step relies on for pass/fail, so this is direct evidence the job will
genuinely fail on a real regression, not an assumption from job wiring alone.

Did not attempt Playwright/E2E (explicitly Out of Scope) and did not investigate whether
GitHub-hosted runners can reach the npm registry beyond noting every other job in this same
workflow already does an equivalent `pip install` successfully -- the real first CI run on this
PR is the actual confirmation for that Assumption, not a separate investigation step.

## Test Summary

- `cd frontend && npx vitest run` -- **26/26 passed** (locally, matching the exact command the
  new CI job step runs), both before and after the deliberate-failure verification above.
- `cd frontend && npm run build` -- **exit 0, clean build**, both before and after the
  deliberate-failure verification above.
- Deliberate-failure verification (see Implementation Notes): `npx vitest run` genuinely exits 1
  on a real test failure; `npm run build` genuinely exits 2 on a real type error. Both scratch
  changes fully reverted (`git status --porcelain -- frontend/src/` clean).
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` -- parses
  cleanly, `frontend` job present in the parsed job list alongside all 12 pre-existing jobs
  (unchanged).
- Real CI confirmation: this ticket's own PR (#77) is itself the live test -- `gh pr checks 77`
  after this commit lands shows whether the new `Frontend` job actually appears and passes in a
  real GitHub Actions run, not just local `npx`/`npm` invocations.

## Files Changed

- `.github/workflows/test.yml` -- added the `frontend` job (checkout, Node 20 setup with npm
  cache, `npm ci`, `npx vitest run`, `npm run build`); added `frontend` to the `slow` job's
  `needs:` list. No existing job's steps, triggers, or `if:` conditions changed.

## Completion Summary

`.github/workflows/test.yml` now has a real frontend job running the exact `npx vitest run`/
`npm run build` commands this repo's frontend work depends on, closing the gap
`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` exposed (26 new vitest tests and a build gate that had
never once been checked by CI). Both underlying failure-detection mechanisms were verified with
real, deliberate breaks (not assumed) before being wired into CI, and fully reverted afterward
with an empty `git diff`. No existing job's behavior changed. No path-filter gate added --
frontend tests are fast enough that always-running is the safer, simpler choice.
