---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE
artifact_type: investigation
tags: [testing]
---

# Investigation

## Current Behavior
The report's parity layer counted ledger statuses only, so parity TOWN-122 gaining a `test_path` was invisible.

## Mechanics / Engine Constraints
`docs/mechanics/03_economic_laws.md` §1, §2 (conservation and inventory are economic laws). Ownership map: `docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1.

## Docs Requiring Update
- None (report tooling; the limits text in `core_rpg_report.py` is updated).

## Parity Ledger Overlap
None (`town_resource.yaml` TOWN-011/012 cited as evidence for the ownership).

## Risks and Open Questions
Tests importing `src.core.conservation`/`inventory` now carry a gameplay-import signal in the core-RPG report classification; counts in older baseline documents are dated snapshots and are not rewritten.
