---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY

## Title
Epic A — Test baseline and reliability: an honest core-RPG test report, and fixes for the known progression order leak and tracked-file write

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary

There is no reproducible picture of the test system. Two known reliability defects also undermine
any combined-run measurement:

1. **Progression order leak.** 7 tests in `tests/unit/domains/progression/` fail after any of 8
   catalog/registry/content-mode test files and pass alone. CI is green only because it runs that
   directory on its own. Re-checked at `origin/main` `5d4e4a237`.
2. **Tracked-file write.** Running the fast test tiers in a clean checkout modified the tracked
   `docs/brainstorm/mechanism_verification_view.md`. The writer is not yet identified.

This epic produces the baseline and fixes those two **known** defects. It does **not** claim that all
order dependence is eliminated.

Roadmap: `docs/plans/test_architecture/roadmap.md` §3.

## Scope

- **Core-RPG test report v0**, report-only:
  - test classification (heuristic, with `uncertain` kept);
  - CI lanes;
  - execution from supplied JUnit, with **`no-junit-artifact` ≠ `not-run` ≠ outcome**;
  - package-level coverage **only from an available coverage artifact**, if one is supplied (e.g. a
    local run via a repaired `make test-cov`); otherwise the report shows `no-coverage-artifact`;
  - read-only states for SimQ (`skipped-no-data`), census (`unstable`) and parity evidence.
- **Known progression leak:** fix at the source; add a regression guard; verify against the
  identified polluters, the combined fast suite, and a random-order run of the affected set at one
  SHA (after checking random ordering against the RNG contract).
- **Known tracked-file write (scoped repair):** find the test that rewrites the **observed** tracked
  file `docs/brainstorm/mechanism_verification_view.md`, and stop it writing that file (e.g. use
  `tmp_path` or check-only mode).
- **Optional general guard, advisory only:** report tracked-file changes after a test run.
  - It must distinguish test-caused writes from legitimate tool or hook updates, such as
    agent-monitoring shards.
  - It is **never a blocking CI gate** in this epic.
  - It is not required to close the epic.
- **Test-effectiveness baseline** (roadmap §4.7; a narrowed form of the D4 direction approved
  2026-09-28):
  - one local, on-demand `mutmut` run on **one declared target**: the resource-conservation code if
    the feature team confirms a stable window, otherwise a labelled synthetic target. A synthetic
    run is reported as a **tooling exercise**, not as evidence of core-RPG test strength;
  - recorded with the target, selected tests, SHA, date, runtime and result categories
    (killed / survived / timeout / equivalent), shown in its own report layer, and `stale` after the
    target changes or 30 days;
  - **no CI job**.
- **Escaped-defect tracking:** register an `escaped-defect` ticket tag (via
  `tools/tag_registry.py`) for defects that reached `main` past green tests, recorded with a failure
  class. The report counts them per month.
- **Post-repair baseline:** the same report after the fixes, with every difference explained and
  remaining unknowns listed.

## Out of Scope

- Claiming that all order dependence or all test-side writes are gone.
- Mutation testing beyond one target, or scheduled mutation runs (deferred to the post-pilot
  review).
- Any gate or blocking use of the report.
- **A new CI coverage job.** Later work, only after its runtime is measured and its information
  judged useful (roadmap §5). This is not an owner-decision gate.
- A repository-wide cleanliness check as a blocking CI gate.
- Proof layers, review records, metadata markers (Epic B), and CI rule changes (Epic B).
- Fixing SimQ's silent anchor skip (SimQ owner).
- Product-code fixes. If the leak source is feature code under rework, route it to the feature team
  and mark this part blocked.

## Acceptance Criteria

1. The report regenerates identically from the **same input artifacts**. Every count shows its
   denominator; missing data shows an explicit state, never 0. A fixture proves that the execution
   states `no-junit-artifact`, `not-run` and outcome are distinct, and that coverage shows
   `no-coverage-artifact` when none is supplied.
2. The report states its v0 limits, e.g. only `api-tools` uploads JUnit in CI.
3. **Known leak:**
   - each identified polluter + the 3 progression files → 0 failures in the 7 nodes;
   - the combined fast suite → 0 failures in the 7 nodes;
   - `tests/unit/domains` alone still passes;
   - a random-order run of the affected set passes at the same SHA.

   If random ordering is blocked by the RNG-contract check, this part closes as `provisional`, and
   says so.
4. **Known tracked-file write:** after the fast tiers in a clean checkout,
   `docs/brainstorm/mechanism_verification_view.md` is unchanged. If the optional advisory guard is
   built, it reports a seeded test-caused write and ignores a seeded hook/tool update.
5. **Effectiveness:**
   - a mutation record exists for one declared target, with full provenance, and appears in the
     report as its own layer. No score threshold; surviving mutants are listed for review, not
     auto-fixed;
   - the `escaped-defect` tag is registered, and the report shows its monthly count, including 0 as
     a real count once the tag exists.
6. The post-repair baseline lists **remaining unknowns**, e.g. order dependence outside the verified
   set.

## Related Tickets
- Parent of child tickets to be created by the detail planner.
- Feeds Epics B, C, D.

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/current_test_system_overview.md` §4.2 (polluter list,
  timings)
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (M0a, R1, M0b; non-binding)

## Related Stored Artifacts
None.

## Related Code Areas
`tests/conftest.py`; `tests/unit/{content,core}/` (polluters); `tests/unit/domains/progression/`;
`tools/mechanism_registry/generate_mechanism_verification_view.py`; `Makefile` (`test-cov`);
`.github/workflows/test.yml` (read-only for the report; **no CI job added** by this epic).

## Assumptions / Open Questions

- Deferred: JUnit upload from every CI job (trigger: manual input becomes the bottleneck) and
  per-test coverage contexts (trigger: a recorded selection miss).
- Non-binding ideas for child breakdown are in the reference notes; the detail planner decides.

## Implementation Notes
Local costs observed at `5d4e4a237` (6 cores):
- polluter reproducer under 1 s;
- `tests/unit` 263 s;
- combined fast suite 563 s;
- a fast-tier coverage run took about 17 min at `04f911110`, which is relevant only if a coverage job
  is later considered.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
