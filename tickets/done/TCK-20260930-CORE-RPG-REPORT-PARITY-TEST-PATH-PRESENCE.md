---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE

## Title
Core-RPG report: show parity test_path presence, so a P0 entry gaining a test_path changes the report

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child of `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`. Found by the core-RPG pilot (`docs/testing/core_rpg_test_pilot_2026-09-30.md`) and fixed in the same batch. The report's parity layer counted ledger statuses only, so parity TOWN-122 gaining a `test_path` was invisible.

## Scope
1. `parity_layer` adds a `test_path` block: P0 with and without a `test_path`, other priorities the same, and per-file ids of P0 entries without one. A `test_path` counts as present only if it is a non-empty string other than `null`/`None`.
2. The markdown report shows the counts and the per-file totals; ids are in the JSON.
3. The block states that a `test_path` is a recorded path, not evidence that the test exists or passes; the v0 limits text says so.
4. Test: a P0 entry gaining a `test_path` changes the counts and the list.

## Out of Scope
- Verifying that recorded paths exist or pass (a separate check). - Changing any threshold or gate; the report stays report-only.

## Acceptance Criteria
1. The parity layer reports P0 and other-priority counts with and without a `test_path`, and the P0 ids without one.
2. Adding a `test_path` to a P0 entry changes the output (test).
3. On the real ledger, `TOWN-122` moves from listed to not listed (pilot artifact `cap6b_parity_test_path_visible_after_fix.json`).

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (parent)
- `TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING` (evidence)

## Related Docs
- None (report tooling; the limits text in `core_rpg_report.py` is updated).

## Related Stored Artifacts
None.

## Related Code Areas
`tools/test_architecture/core_rpg_report.py`, `tests/unit/tools/test_core_rpg_report.py`.

## Assumptions / Open Questions
None.

## Implementation Notes
On the real ledger 1562 P0 entries have no `test_path` (145 in town_resource.yaml before the pilot, 144 after). The JSON lists all of them; the markdown shows per-file counts only.

## Test Summary
1 new test in `tests/unit/tools/test_core_rpg_report.py`.
`pytest tests/unit/tools/test_impact_report.py tests/unit/tools/test_core_rpg_report.py tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_marker_check.py`: pass.

## Files Changed
- `tools/test_architecture/core_rpg_report.py`
- `tests/unit/tools/test_core_rpg_report.py`

## Completion Summary
The report now shows parity test_path presence.
