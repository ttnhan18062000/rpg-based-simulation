---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-PROCEDURAL-GENERATOR-KEPT
phase: open
date: 2026-08-21
tags: [world, documentation]
---

# TCK-20260821-PROCEDURAL-GENERATOR-KEPT

## Title
Confirm WorldProceduralGenerator is an intentionally preserved legacy path, not dead code

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The epic asked to investigate whether WorldProceduralGenerator is safe to delete as dead code, or whether it's intentionally kept for a reason not surfaced by the epic's own investigation. Investigation found the epic's premise was wrong: WorldProceduralGenerator is explicitly documented in docs/world/generator_contract.md as the intentionally preserved 'Spec-based (legacy, preserved)' generation path, and carries a live P0 parity claim (SUBSTRATE-NEW-002) in docs/parity_ledger/substrate.yaml. This ticket records that finding and closes the question with a decision to keep the class, rather than deleting it.

## Scope
- Document, in the ticket, the authoritative evidence that WorldProceduralGenerator (src/worldgeneration/generator.py) is an intentionally preserved 'Spec-based (legacy, preserved)' generation path per docs/world/generator_contract.md and a live P0 parity claim (SUBSTRATE-NEW-002 in docs/parity_ledger/substrate.yaml).
- Record that TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY invested real engineering effort in this class 13 days before this concern was raised, with full knowledge of its 'unwired to any CLI' status — and that the 'unwired' concern was itself root-caused to a predecessor's missing .load_all() call, not a defect in this class.
- Close the epic's Scope item 5 with a decision NOT to delete WorldProceduralGenerator, correcting the epic's own false 'confirmed dead code' premise.
- Name, as a process note, that call-site-only grep methodology for 'is X dead code' has now produced two false leads in this codebase's recent history (this one and the sibling rendering epic's C10), worth flagging for future investigations of this shape.

## Out of Scope
- Deleting WorldProceduralGenerator (src/worldgeneration/generator.py) or any of its files, tests, or references.
- Retiring Compliance IDs WORLD-GEN-003/004 — not applicable since the class is being kept, not removed.
- Editing .github/workflows/test.yml or removing any of the other 3 test files in tests/unit/worldgeneration/.

## Acceptance Criteria
- [ ] The ticket records the finding that WorldProceduralGenerator is documented (docs/world/generator_contract.md) and parity-tracked (docs/parity_ledger/substrate.yaml, SUBSTRATE-NEW-002, P0, status: verified) as an intentionally preserved legacy generation path.
- [ ] The ticket closes with an explicit decision NOT to delete WorldProceduralGenerator, correcting the epic's own 'likely dead code' premise.
- [ ] grep -rln "WorldProceduralGenerator" src/ tools/ tests/ continues to return only generator.py and test_generator.py at ticket close, confirming no call sites were missed or newly introduced during investigation.
- [ ] tests/unit/worldgeneration/ retains its other 3 test files regardless of outcome; .github/workflows/test.yml requires no edit.

## Related Tickets
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY
- TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION
- TCK-20260612-WORLDGEN-CONTRACT

## Related Docs
- docs/world/generator_contract.md
- docs/parity_ledger/substrate.yaml
- docs/plans/world_generation_organic_terrain_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldgeneration/generator.py
- tests/unit/worldgeneration/test_generator.py

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
