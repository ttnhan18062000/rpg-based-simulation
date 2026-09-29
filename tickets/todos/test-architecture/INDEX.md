# Test Architecture — Epic Index

**Status: DRAFT for owner review (2026-09-29).** This folder holds **four epic-tier tickets only**.
Child tickets are created later by the detail planner, not here. This file is deliberately **not**
named `SEQUENCE.md`, because `implement-epic` reads that name as a child-ticket order.

Binding plan: `docs/plans/test_architecture/roadmap.md`. All decisions (D-R2, D-MF, D-M2, D-P, D-PR)
are **pending**.

| Order | Epic | Starts when | Gated parts |
|---|---|---|---|
| 1 | `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (A) | now | none |
| 2 | `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (B) | now; its report-dependent criterion needs A's report v0 | CI scenario-lane rule ← D-R2 |
| 3 | `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (C) | after B's taxonomy doc | oracle-review step ← D-M2; quarantine policy ← D-MF |
| 4 | `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT` (D) | minimum usable workflow: A report v0 + A known-leak fix (≥ provisional) + B taxonomy doc + C test-plan fields + C triage procedure | surface confirmation at start |

A and B can run in parallel. D does not wait for optional parts of A–C.
