---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION
phase: done
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION

## Title
Delete `src/domains/optimization/diagnostics.py` — confirmed superseded, no unique behavior

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found and determined during `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION` (`stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION/investigation.md`, section 6). One of 5 follow-up tickets that ticket's own
determination filed — this is the one of the 8 original modules with a clean disposition, filed
separately from the other 7 (which are all partially superseded with orphaned unique capability)
so its simpler reasoning isn't diluted.

`DeveloperDiagnostics`/`DiagnosticIssue` is a simple record-issue/generate-report aggregator, zero
real callers anywhere (confirmed by the origin audit). A much richer, confirmed-live, load-bearing
observability system already does the same job: `AlertsManager`/`AlertRouter`/`AlertSink`
(`src/observability/alerts/`), with real routing, deduplication, and multiple sinks — directly
observed firing (`[ALERT] type=WatchdogTrip`) during the determination ticket's own instrumentation
runs. No unique behavior in `DeveloperDiagnostics` was found that isn't already better-served live.

## Scope
- Delete `src/domains/optimization/diagnostics.py` in full (`DeveloperDiagnostics`,
  `DiagnosticIssue`).
- Confirm (grep) zero remaining references anywhere in `src/`/`tests/` before deleting.

## Out of Scope
- The other 4 follow-up tickets from the same determination
  (`TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION`,
  `TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION`,
  `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION`,
  `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION`) — each has its own scope
  and reasoning, not this ticket's to fold in.

## Acceptance Criteria
- [x] `src/domains/optimization/diagnostics.py` deleted.
- [x] Grep confirms zero remaining references to `DeveloperDiagnostics`/`DiagnosticIssue` anywhere.
- [x] No regression in any test suite touching `src/domains/optimization/` or
      `src/observability/alerts/`.

## Related Tickets
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (origin — the full
  8-module determination)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C1)

## Related Docs
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/
  investigation.md` (section 6, full evidence)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/domains/optimization/diagnostics.py`
- `src/observability/alerts/` (the confirmed-live replacement)

## Assumptions / Open Questions
None — disposition is clean and already evidenced by the origin ticket's own investigation.

## Implementation Notes
Re-verified the origin determination's own claim at the code, per peer instruction ("verify both
claims hold at the code rather than inheriting them from the determination; they were made in a
survey pass, not with deletion in hand"), not inherited: `grep -rln "DeveloperDiagnostics\|
DiagnosticIssue" src/ tests/` returned only the module's own file and its own dedicated test file
— zero production callers, exactly as claimed. Read the module in full (31 lines): a plain
record-issue/generate-report aggregator with no side effects, no state shared with anything else,
no unique capability riding along with the "dead" label (C1 guard).

Deleted `src/domains/optimization/diagnostics.py` and its own dedicated test file
(`tests/unit/diagnostics/test_phase10_developer_diagnostics.py`, 5 self-contained unit tests, no
shared fixtures, nothing else in the file referenced elsewhere). The containing test package
(`tests/unit/diagnostics/`) had only an empty `__init__.py` left after removing its one real test
file, so removed the whole now-hollow package rather than leaving an empty directory.

## Test Summary
Post-deletion: `grep -rln "DeveloperDiagnostics\|DiagnosticIssue" --include="*.py" src/ tests/`
returns zero matches (exit code 1). `pytest tests/unit/domains/optimization/ tests/observability/
tests/unit/observability/ -q -m "not slow and not extra_slow"`: 1215 passed, 1 skipped — no
regression.

## Files Changed
- `src/domains/optimization/diagnostics.py` — deleted.
- `tests/unit/diagnostics/test_phase10_developer_diagnostics.py` — deleted.
- `tests/unit/diagnostics/__init__.py` — deleted (now-empty test package).

## Completion Summary
Confirmed at the code, not inherited from the origin survey: `DeveloperDiagnostics`/
`DiagnosticIssue` had zero production callers, and its own dedicated test file was self-contained
with nothing else depending on it. Deleted cleanly along with the now-hollow test package. No
unique capability found riding along with the deletion (C1 guard satisfied). No regression.
