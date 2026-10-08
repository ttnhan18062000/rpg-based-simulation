---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION
phase: done
date: 2026-10-07
tags: [architecture, testing, documentation]
---

# TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION

## Title
Record the owner's adoption of icons-v2, re-point the guards, refresh the handoff snapshots and close the batch

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 5 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`, only if the owner adopts `icons-v2`. Same pattern as `TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION`.

## Scope
- Commit the owner's adoption files byte for byte; re-point guards by equality; docs say no release candidate covers icon slots; refresh `docs/assets/session_handoff/`; `SEQUENCE.md` status; close the epic.

## Out of Scope
- A release candidate with icons; wiring.

## Acceptance Criteria
- [x] Adoption committed unchanged; guards exact and passing; batch closed.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic)

## Related Docs
- docs/assets/icon_set_v2_review.md, docs/assets/pilot_terrain_key.md (adoption paragraph), docs/assets/session_handoff/

## Related Stored Artifacts


## Related Code Areas
- visual_assets/catalog/, tests/visual_assets/adopted_facts.py

## Assumptions / Open Questions
- If not adopted, this stays open and the PR carries children 1-4 by the owner's choice.

## Implementation Notes
- The owner ran `adopt-set` in their own terminal: set adoption `sa-c9082d078b954f6b`, 2026-10-08T00:40:15Z, approver nhan/owner, 22 entries, draft set hash `sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4` (equals the template's); `store verify` ok. The 89 new files (22 adoptions, 44 intake provenance files, 1 set adoption, 22 sources) are committed byte for byte, not edited.
- Guards re-pointed by equality in `tests/visual_assets/adopted_facts.py` (ICON_V2_* facts; ADOPTED_SOURCES 70, ADOPTION_COUNT 70, INTAKE_FILE_COUNT 140, three set adoptions; GENERATED stays the 34 terrain-era artifacts) and in `test_icon_set_adoption.py` (new: the v2 draft set still hashes to the adoption and every entry is adopted; the set-adoption record's facts), `test_icon_v2_keys.py` (each v2 key adopted once, no artifact, no candidate slot), `test_detail_axis.py` (22 more sources, no detail axis), `test_store_tools_stdio.py` (70 sources; asks for limit 200 because the tool's default listing is 50).
- The `icondraft_v2` and `icondraft` fixtures did NOT change (both `--check` identical): adopted references skip slots a set holds and slots that are not built, as predicted last time.
- Docs: adoption paragraph in `pilot_terrain_key.md` (no release candidate covers an icon slot), adoption note in the review doc, `docs/assets/session_handoff/` snapshots refreshed (the planner's copy is their file as of its last update, 2026-10-07: they should refresh it), `SEQUENCE.md` status, epic closed, folder moved to done.


## Test Summary
- `pytest tests/visual_assets tests/docs tests/static`: 1819 passed, 2 skipped, 1 xfailed; `store verify` ok; vitest `src/visualAssets`: 261 passed. Before the guard edits: 10 failures, all adopted-source counts.


## Files Changed
- visual_assets/catalog/{sources,provenance} (89 owner-made files), tests/visual_assets/{adopted_facts,test_icon_set_adoption,test_icon_v2_keys,store/unit/test_detail_axis,drawing/test_store_tools_stdio}.py, docs/assets/{pilot_terrain_key,icon_set_v2_review}.md, docs/assets/session_handoff/*, tickets and SEQUENCE.


## Completion Summary
The owner's adoption of `icons-v2` is recorded and every guard that counted adopted sources now says 70 with equality; nothing is built or released for any icon.

