---
status: historical
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260824-ROUTE-KIND-COUNT-FIX
phase: done
date: 2026-08-24
tags: [adventure, documentation]
---

# TCK-20260824-ROUTE-KIND-COUNT-FIX

## Title
Fix Stale Route/Activity Kind Count in Adventure Routing Docs

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
docs/mechanics/adventure_routing_contract.md's table of route/activity kinds is stale by exactly 3 entries (documents 13, actual is 16). This is a straightforward doc correction.

## Scope
- Update docs/mechanics/adventure_routing_contract.md's Route Family Taxonomy table to contain exactly 16 rows matching the RouteFamily enum
- Add the 3 missing rows (QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL) with accurate Meaning descriptions
- Correct the prose "All 13 families" to "All 16 families"

## Out of Scope
- The Regression Tests section's reference to a nonexistent tests_v2/ directory (separate staleness issue)
- The Source Areas table's omission of src/domains/adventure/mapper.py (separate staleness issue)
- Implying all 16 families map to a project -- RouteToProjectMapper._MAP intentionally has only 15 entries (DEFER_WITH_REASON excluded by design)

## Acceptance Criteria
- [x] Route Family Taxonomy table contains exactly 16 rows matching the RouteFamily enum
- [x] QUEST_OPPORTUNITY, PROTECT_TARGET, and OWN_SURVIVAL rows are added with accurate Meaning descriptions
- [x] Prose is corrected from "All 13 families" to "All 16 families"
- [x] No src/ file is modified; tests/unit/domains/adventure/test_phase3_route_families.py::test_route_family_definitions_are_unique continues to pass unchanged, confirming 16 as ground truth

## Related Tickets
- TCK-20260619-E23D-HERO-MATCHING
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Related Docs
- docs/mechanics/adventure_routing_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/mechanics/adventure_routing_contract.md
- src/domains/adventure/schema.py
- src/domains/adventure/mapper.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
None.

## Implementation Notes
Corrected the "Route Family Taxonomy" table in `docs/mechanics/adventure_routing_contract.md`
(lines 76-98) to list all 16 `RouteFamily` enum members in exact declaration order, matching
`src/domains/adventure/schema.py:16-33`. Three rows were missing (`QUEST_OPPORTUNITY`,
`PROTECT_TARGET`, `OWN_SURVIVAL`) and the header prose read "All 13 families" — both fixed.

Meaning descriptions for the three new rows were cross-checked directly against source, not
inferred from the enum names alone:
- `QUEST_OPPORTUNITY`: verified against `src/domains/adventure/scoring.py:169-200` (HERO capability-match
  scaling of benefit vs. non-HERO 0.5x attractiveness) and `mapper.py:44` (maps to
  `ProjectKind.QUEST`/`ObjectiveKind.ACCEPT_QUEST`).
- `PROTECT_TARGET` / `OWN_SURVIVAL`: verified against the "Escort Scoring (SOC-230)" block in
  `scoring.py:357-368` — flat `+3.0` bonus to `PROTECT_TARGET` and `-1.0` penalty (floored at 0.0) to
  `OWN_SURVIVAL`, gated on `group.escort_target_id is not None and entity.id != group.escort_target_id`.
  `schema.py:32-33`'s own inline comments label both as "E41D", which the doc prose retains for
  consistency with the rest of the file's E41D references.

No `src/` file was touched — confirmed via `git status`/`git diff --stat` showing only
`docs/mechanics/adventure_routing_contract.md` (plus the auto-updated `agent-monitoring/tools.jsonl`)
changed. Out-of-scope staleness issues (tests_v2/ reference in Regression Tests, mapper.py omission
in Source Areas, RouteToProjectMapper._MAP's intentional 15-entry count) were left untouched per
ticket scope.

Ran the ground-truth test named in AC #4 against the project's venv interpreter
(`.venv/bin/python3` — bare `python3` lacks `pydantic` per this repo's known environment gap):
`pytest tests/unit/domains/adventure/test_phase3_route_families.py -k
test_route_family_definitions_are_unique` → 1 passed, confirming 16 is the correct enum count.

## Test Summary
`tests/unit/domains/adventure/test_phase3_route_families.py::test_route_family_definitions_are_unique`
— 1 passed, 0 failed (run via `.venv/bin/python3 -m pytest`). This is a read-only verification test
(asserts enum member count/uniqueness); no test changes were needed since this ticket made no
source-level change.

## Files Changed
- docs/mechanics/adventure_routing_contract.md — added 3 missing Route Family Taxonomy rows, corrected "All 13 families" to "All 16 families"
- tickets/inprogress/TCK-20260824-ROUTE-KIND-COUNT-FIX.md — this ticket, filled in during Implement

## Completion Summary
Fixed a stale documentation table: `docs/mechanics/adventure_routing_contract.md`'s Route Family
Taxonomy table was missing 3 of the 16 `RouteFamily` enum members (`QUEST_OPPORTUNITY`,
`PROTECT_TARGET`, `OWN_SURVIVAL`) and its prose still said "All 13 families". Added the 3 rows in
correct enum order with Meaning descriptions verified against the actual scoring and mapping logic
in `src/domains/adventure/scoring.py` and `mapper.py`, and corrected the prose to "All 16 families".
This is a pure documentation correction — zero source or behavior change, no parity ledger impact.
The named ground-truth test (`test_route_family_definitions_are_unique`) was run and passes,
confirming 16 as the correct count.
