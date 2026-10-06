---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION
phase: done
date: 2026-10-06
tags: [architecture, testing, documentation]
---

# TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION

## Title
Record the user's adoption of icons-key-v1, re-point the guards, refresh the handoff snapshots and close the batch

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 6 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`, **only if the user adopts `icons-key-v1`** (owner gate after child 5). Same pattern as
`TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION`.

## Scope
- Commit the user's adoption files byte for byte; re-point guards that describe the pre-adoption catalog by equality
  (`tests/visual_assets/adopted_facts.py`), never loosened.
- Docs state that no release candidate covers the new slots.
- Refresh `docs/assets/session_handoff/` snapshots; `SEQUENCE.md` status line.

## Out of Scope
- A release candidate. Panel wiring (next batch).

## Acceptance Criteria
- [ ] Adoption files committed unchanged; guards pinned to exact facts and passing.
- [ ] Handoff snapshots refreshed; batch status recorded.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION (pattern)

## Related Docs
- docs/assets/session_handoff/

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION/ (plan, investigation, test_plan)

## Related Code Areas
- visual_assets/catalog/, tests/visual_assets/adopted_facts.py

## Assumptions / Open Questions
- If the user does not adopt, this ticket stays open and the PR carries children 1-5 only, by the user's choice. The user DID adopt (2026-10-06T15:21:47Z); verified in the store itself before recording (`store verify` ok, `audit` chain ok, the set adoption record present), not taken from the relayed message.

## Implementation Notes
- **The adoption (the user's, not mine):** `adopt-set icons-key-v1` run by the user in their own terminal: set adoption `sa-b4bb738d6b5526f0`, decided 2026-10-06T15:21:47Z, approver nhan (owner), draft set hash `sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd`, 14 entries. Committed byte for byte: 14 `provenance/adoptions/ad-*.json`, 28 `provenance/intake/` files (14 records and 14 reviews), 1 `provenance/set-adoptions/sa-b4bb738d6b5526f0.json` and 14 `sources/icon_*/` directories. Nothing was edited.
- **Guards re-pointed by equality (nothing loosened):** `tests/visual_assets/adopted_facts.py` keeps every terrain-era fact (renamed `TERRAIN_ERA_SOURCES`, 34) and adds the icon facts (`ICON_SOURCES` 14, the set adoption id, hash, time, approver); `ADOPTED_SOURCES` is now everything the catalog holds (48), `ADOPTION_COUNT` 48, `INTAKE_FILE_COUNT` 96, `SET_ADOPTION_IDS` two; `GENERATED` stays the 34 terrain-era artifacts. Re-pointed: `test_adoption` (set adoptions count from the facts), `test_store_tools_stdio` (48 sources, 34 artifacts), `test_server_stdio` and `test_registry` and `test_catalog_integrity` (the source list), the set-adoption test (now both records, each against its own draft set), `test_detail_axis` (icons name no detail), `test_terrain_draft_set` (comment). New: `test_icon_set_adoption.py` (draft set hash, every entry adopted with the same intake, key and source id, icon keys optional with no axis, no artifact and no release candidate covers an icon slot, no revocation).
- **The `icondraft` fixture needed no refresh.** I had predicted (and told the planner) that adoption changes the draft export's adopted references. It does not: `_adopted_references` skips every slot the set holds (a draft always wins) and every adopted slot that is not built, so the export is identical (`icon_draft_fixture --check`). The three places where I had written the prediction were corrected (the fixture test docstring, the DRAFT-SET ticket and its investigation).
- **Docs:** state that no release candidate covers the 14 slots (rc-0006 has 34): `docs/assets/store_contract.md`, `docs/assets/pilot_terrain_key.md`, `docs/assets/icon_key_set_review.md`. `docs/assets/session_handoff/` snapshots refreshed from the two gitignored handovers. `SEQUENCE.md` status line and the epic closed; the folder moved to `agent-working/tickets/done/`.

## Test Summary
- `pytest tests/visual_assets tests/docs tests/static`: all passed (visual_assets 1600; after the adoption eight guards failed exactly where expected and were re-pointed; the new `test_icon_set_adoption.py` adds 4).
- `store verify` ok, `audit` chain ok. `icon_draft_fixture --check` identical.

## Files Changed
- visual_assets/catalog/{provenance/adoptions,provenance/intake,provenance/set-adoptions,sources/icon_*} (the user's files, unchanged), tests/visual_assets/{adopted_facts,test_adoption(store/unit),test_catalog_integrity,test_terrain_draft_set,test_icon_draft_fixture,test_icon_set_adoption}.py and the stdio/detail/registry guards, docs/assets/{store_contract,pilot_terrain_key,icon_key_set_review}.md, docs/assets/session_handoff/*, the DRAFT-SET ticket notes, SEQUENCE.md and the epic.

## Completion Summary
The user's adoption of icons-key-v1 is recorded; every guard describing the catalog is pinned to the exact new facts; no release candidate covers the 14 icon slots; the batch is closed locally.
