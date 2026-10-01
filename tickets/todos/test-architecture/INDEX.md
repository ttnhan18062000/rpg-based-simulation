# Test Architecture — Epic Index

**Status: owner decisions recorded 2026-09-30; epics A–D remain open (see the table).** This folder holds **four epic-tier tickets only**.
Child tickets are created later by the detail planner, not here. This file is deliberately **not**
named `SEQUENCE.md`, because `implement-epic` reads that name as a child-ticket order.

Binding plan: `docs/plans/test_architecture/roadmap.md`. Decisions (2026-09-30): D-R2, D-MF and D-M2
approved with changes; D-P deferred; D-PERF assigned when its trigger fires; D-PR resolved (plan PR #256).

| Order | Epic | Starts when | Status (2026-09-30) |
|---|---|---|---|
| 1 | `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (A) | now | parts done; see the epic |
| 2 | `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (B) | now; its report-dependent criterion needs A's report v0 | part 2 (CI scenario-lane rule, D-R2 approved): in progress (this batch); criterion 4 open |
| 3 | `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (C) | after B's taxonomy doc | criterion 1 met with a caveat (done-checker advisory, PR #268), criterion 2 not met (partially demonstrated: checklist ran only with an added prompt sentence); criterion 4 open, criterion 5 met (text only); part 5 and 6 text landed (part 5 oracle rule and part 6 quarantine text land in this batch, text only) |
| 4 | `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT` (D) | minimum usable workflow: A report v0 + A known-leak fix (≥ provisional) + B taxonomy doc + C test-plan fields + C triage procedure | open: real-pipeline gap closed by capability 7 (with interventions); CI scenario execution recorded from this change's own CI |

A and B can run in parallel. D does not wait for optional parts of A–C.

**Hold rule:** `HOLD` items may be described by detail planners, but no implementation child ticket
may be activated and no gated work may start until the owner approves the named decision. Ungated
work is independently startable. **No HOLD is open as of 2026-09-30**; D-P (deferred) and D-PERF
(trigger-based) gate nothing in A–D. Approval lifts a HOLD; it does not close an epic.
