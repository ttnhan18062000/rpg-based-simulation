---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS
phase: done
date: 2026-08-17
tags: [testing, ai, bug]
---

# TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS

## Title
Wire 16 test directories (440 tests, never run by any CI job) into `.github/workflows/test.yml`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
User question this session: "is there any missing tests run in the workflow/action?" —
investigation found 16 directories with 440 real, collectible tests that no CI job ever
referenced by path, all traced to commit `29d78798` ("Simulation quality #20", 2026-08-14), which
added the directories but never updated the workflow file in the same PR. 439 of 440 had never
executed in CI, ever, in any lane (only 1 carries `@pytest.mark.slow`/`@pytest.mark.extra_slow`
and so would have incidentally run via the `slow` job's blanket scan).

A local run of all 440 before this session's fixes found 9 real failures — each root-caused and
fixed as its own separate ticket in this session's larger batch (Integration/API CI-job failures)
before this wiring ticket, so no known-red coverage was ever wired into CI.

## Scope
- `.github/workflows/test.yml`:
  - `tests/unit/actions`, `tests/unit/ai` added to `unit-gameplay`.
  - `tests/unit/tools` added to `unit-infra`.
  - `tests/regression` needs no explicit placement — its only test is `extra_slow`, already
    covered by the `slow` job's existing blanket `pytest tests/` scan.
  - New dedicated job `agent-orchestration` ("Agent orchestration / codex / replay") for the 12
    `agent_codex_*`/`agent_orchestration*`/`agent_replay*` directories (83 files) — not folded
    into the already-large `api-tools` job. Added to the `slow` job's `needs:` list.

## Out of Scope
- Fixing the 7-of-8 fast-lane jobs' `-m "not slow"`-only filter (missing `and not extra_slow`) —
  a separate, real inconsistency found while writing this ticket's new job correctly; filed as its
  own follow-up (`TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY`), not fixed here.
- The 9 real test failures found within these directories — each already fixed as its own
  standalone ticket before this one; this ticket only wires the (now-green) directories into CI.
- Any other ticket in this session's batch.

## Acceptance Criteria
- [x] `.github/workflows/test.yml` remains valid YAML.
- [x] Every modified/new job's FULL real pytest scope (not just the newly-added paths) passes
      clean, verified locally.
- [x] No known-red test was wired into CI while still failing.

## Related Tickets
All 9 of this session's tickets that fixed real failures found within these 16 directories,
notably: `TCK-20260817-HOTFIX-PHASE-TIER-MATRIX-WORKFLOW-VERSION-STALE`,
`TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS`,
`TCK-20260817-HOTFIX-SIMQ-AUDIT-GAPS-ISOLATED-ANCHOR-FALSE-POSITIVE`,
`TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION`.
Follow-up filed: `TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER-INCONSISTENCY`.

## Related Docs
None.

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS/`

## Related Code Areas
- `.github/workflows/test.yml`

## Assumptions / Open Questions
None.

## Implementation Notes
Placed the 3 small `tests/unit/` subdirectories into their most thematically-consistent existing
jobs (matching sibling directories already present), left `tests/regression` uncovered by any
fast-lane job (correctly — 100% of its content is `extra_slow`, already covered by the `slow`
job's blanket scan), and gave the 12 substantial `agent_codex_*`/`agent_orchestration*`/
`agent_replay*` directories their own dedicated job given the real volume (83 files) relative to
existing job sizes. The new job's own `-m` filter correctly excludes both `slow` and `extra_slow`
from the start, rather than repeating the pre-existing 7-job inconsistency found while writing it.

## Test Summary
- New `agent-orchestration` job's real scope: 385 passed, 5 skipped.
- `unit-gameplay`'s full real scope (all pre-existing dirs + the 2 newly-added): 1187 passed, 2
  deselected.
- `unit-infra`'s full real scope (all pre-existing dirs + `tests/unit/tools`): 1870 passed, 6
  skipped.
- YAML validity confirmed via `yaml.safe_load()`.

## Files Changed
- `.github/workflows/test.yml`

## Completion Summary
Closed the CI coverage gap that motivated the user's original question. All 440 previously-orphaned
tests are now reachable by a real CI job, every real failure discovered within them was fixed
first (never wiring in known-red coverage), and every modified/new job was verified against its
complete real pytest scope, not just the newly-added directories in isolation.
