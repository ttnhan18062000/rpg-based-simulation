---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
phase: open
date: 2026-10-09
tags: [architecture, delivery]
---

# TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

## Title
Measure `test.yml` on `ubuntu-26.04` before `ubuntu-latest` begins migrating

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`ubuntu-latest` begins migrating to Ubuntu 26.04 on 2026-10-19 (rolling out to 2026-11-19; actions/runner-images issue 14748). All 26 `runs-on` entries in `.github/workflows/` are `ubuntu-latest`. Only `Code health` and `Type check` have run on `ubuntu-26.04` (throwaway PR #331, both passed). Measure the whole of `test.yml` on a throwaway probe, then recommend: no pin, or pin only the named jobs. Owner-approved 2026-10-09 ("go with it"), brief by codebase-planner.

## Scope
- Throwaway branch `ci-runner-26-probe` off main: every `runs-on: ubuntu-latest` in `.github/workflows/test.yml` becomes `ubuntu-26.04`, nothing else. Draft PR only after an owner yes; never merged
- Read every job of the probe run (conclusion, failing step, summaries and annotations for advisory jobs); list path-skipped jobs as "not checked"; compare with main's run on the same base; explain each difference as a 26.04 difference or a flake (one re-run)
- List workflows other than `test.yml` as not probed, unless dispatchable from the branch without side effects (never `deploy-docs`)
- Write `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`: run links, per-job table, recommendation

## Out of Scope
- Adding any `ubuntu-24.04` pin (reported, not made; the owner decides)
- Any edit to `src/**`, `tests/**` or workflows on the batch branch
- Dispatching `deploy-docs`

## Acceptance Criteria
- [ ] Probe branch exists with only the `runs-on` change; its sha was reported to the planner before any push
- [ ] Every job of the probe run is accounted for in the doc (result or "not checked" with the reason)
- [ ] Every difference from main's run has a cause (26.04 difference or flake, re-run once)
- [ ] The doc has valid frontmatter, run links, the per-job table and a recommendation (pins named with ticket + dated exit if any)
- [ ] The doc says "begins migrating" and never "switches"
- [ ] `git diff --stat` on the batch branch lists no path under `src/` or `tests/`

## Related Tickets
- TCK-20261009-HANDOFF-TESTING-METRICS-EXPORT-FLAKE
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT (same date, 2026-10-19)

## Related Docs
- docs/plans/codebase_health/python_code_craft_gates_soak_review.md ("Ubuntu 26 pre-check", PR #331)
- docs/testing/migration_ci_lanes.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261009-UBUNTU-26-RUNNER-PRECHECK/

## Related Code Areas
- .github/workflows/test.yml (probe only)

## Assumptions / Open Questions
- Branches are based on `origin/main` `0c3a5654b` (the brief named `20af2959a`; #471 touches nothing under `.github`), and main has a green `test.yml` run on it.
- A static test pinning `ubuntu-latest` in `test.yml` that fails on the probe is an artifact of the probe, not a 26.04 problem.

## Implementation Notes
- Probe commit `a5ce529e7` on `ci-runner-26-probe` (21 `runs-on` lines in `test.yml`). The other four workflows hold 5 more `ubuntu-latest` entries and are not touched.

## Test Summary

## Files Changed

## Completion Summary
