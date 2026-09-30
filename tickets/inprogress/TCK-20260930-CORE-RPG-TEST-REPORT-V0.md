---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-REPORT-V0
phase: open
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-CORE-RPG-TEST-REPORT-V0

## Title
Core-RPG test report v0: a deterministic, report-only producer with honest states

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Epic A (`TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`) criteria A.1, A.2, and the reporting halves of A.5
(mutation layer, monthly escaped-defect count). One producer, `tools/test_architecture/core_rpg_report.py`,
writes versioned JSON plus markdown. It reads only what it is given: it never runs tests, and nothing
uses it as a gate.

## Scope
- Layers, kept separate: classification, CI lanes, execution (supplied JUnit), package coverage
  (supplied coverage JSON), parity evidence (read-only), SimQ/census states, mutation, escaped defects,
  manifest, v0 limits.
- Explicit states, never 0 for missing data: `no-junit-artifact`, `not-run`, an outcome, `no-coverage-artifact`,
  `skipped-no-data`, `unstable`, `not-derived`, `uncertain`, `stale`, `fresh`, `tag-not-registered`.
- A denominator on every count; an input manifest (sha256 per supplied artifact); `as_of` as an input, so
  the report regenerates identically from the same inputs.
- Fixture tests proving the three execution states are distinct and `no-coverage-artifact` appears when
  none is supplied.

## Out of Scope
- Any CI job, gate or blocking use; running tests or mutation from the producer.
- Domain coverage (stays `not-derived`); parity/SimQ/census computation beyond reading existing state.
- Changing the mutation record, the parity ledger or any RPG oracle.

## Acceptance Criteria
1. Same inputs -> byte-identical JSON (A.1). Every count carries its denominator; missing data shows a state.
2. A fixture proves `no-junit-artifact`, `not-run` and an outcome are distinct, and `no-coverage-artifact` shows when none is supplied (A.1).
3. The report states its v0 limits, including: only `api-tools` uploads JUnit in CI; `mutmut` is not a project dependency; equivalent mutants are unclassified; `mutmut` 3.x cannot run on `src.` import paths (A.2).
4. The mutation layer reads `tests/mutation/baselines/` and shows `fresh`/`stale` from the target's content sha256 and the record's own `stale_after.days`, against the supplied `as_of` (A.5).
5. The escaped-defect layer counts tagged tickets per month, with 0 as a real count once the tag is registered (A.5).
6. Report-only: no exit-code gate, no CI change.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3, §4.2, §4.7
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (M0a; non-binding)

## Related Stored Artifacts
`stored_artifacts/TCK-20260930-CORE-RPG-TEST-REPORT-V0/` (after close)

## Related Code Areas
`tools/test_architecture/core_rpg_report.py`; `tests/unit/tools/`; `tests/mutation/baselines/`; `.github/workflows/test.yml` (read-only).

## Assumptions / Open Questions
- Output goes to `reports/test_architecture/<sha>/` (gitignored: generated output, not durable evidence). Durable inputs (the mutation record) are tracked.
- Classification is heuristic (directory + import signals, `uncertain` kept); no author declarations exist yet (Epic B).

## Implementation Notes
See `staging_artifacts/TCK-20260930-CORE-RPG-TEST-REPORT-V0/plan.md`.

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
