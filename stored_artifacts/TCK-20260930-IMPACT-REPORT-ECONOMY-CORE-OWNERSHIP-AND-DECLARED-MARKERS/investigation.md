---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS
artifact_type: investigation
tags: [testing]
---

# Investigation

## Current Behavior
The impact report mapped `src/core/conservation.py` to substrate only, with no `mechanic_scenario` level, although conservation is the ch03 economic law; and for a changed test file it named no domain or level.

## Mechanics / Engine Constraints
`docs/mechanics/03_economic_laws.md` §1, §2 (conservation and inventory are economic laws). Ownership map: `docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1.

## Docs Requiring Update
- `docs/plans/test_architecture/reference/architecture_design_notes.md`: §3.1 Economy row names the two dual-owned files.

## Parity Ledger Overlap
None (`town_resource.yaml` TOWN-011/012 cited as evidence for the ownership).

## Risks and Open Questions
Tests importing `src.core.conservation`/`inventory` now carry a gameplay-import signal in the core-RPG report classification; counts in older baseline documents are dated snapshots and are not rewritten.
