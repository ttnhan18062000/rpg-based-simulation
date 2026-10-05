---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION
phase: open
date: 2026-10-06
tags: [architecture, testing, live-map]
---

# TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION

## Title
Record the user's adoption of draft set terrain-v1 and re-point the seven guards that described the pre-adoption catalog

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The user ran `adopt-set` on `terrain-v1` themselves (set adoption `sa-f4c541f25f112221`, approver nhan / owner, decided_at 2026-10-05T18:17:03Z, `draft_set_hash` `sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2`),
after reviewing the whole map with borders. The store wrote 125 untracked files under `visual_assets/catalog/` (31 adoptions, 31 sources, 62 intake provenance files, one set adoption). Seven tests that assert the
pre-adoption world ("the catalog holds only the forest", "nothing is adopted") now fail. Nothing in the code regressed: the owner's adoption is a legitimate state change, so the tests must describe the new truth.

## Scope
- Commit the user's adoption files **exactly as `adopt-set` wrote them, byte for byte** (no edit, no re-run). If `verify` flags anything afterwards, stop and tell the planner.
- Re-point the seven guards, **as strict as before and pinned to exact facts, never loosened** (no `>=`, no "at least", no skipping): set adoption id `sa-f4c541f25f112221`, the draft_set_hash, 31 adoptions and 31 sources
  (22 terrain + 9 border), forest's three adoptions unchanged. The guards: `test_catalog_integrity`, `store/unit/test_registry::test_committed_catalog_holds_only_the_pilot_asset`,
  `store/unit/test_detail_axis` (committed catalog fills each declared slot), `store/unit/test_adoption::test_the_committed_catalog_is_never_touched_by_these_tests` (keep its intent: a before/after snapshot, file list and hashes,
  of the committed catalog, not a count), `test_terrain_draft_set::test_the_drafts_are_unadopted...` (the drafts stay as history; assert the adoption record points at them, not "unadopted"),
  `drawing/test_store_tools_stdio::test_store_list_and_show...` and `drawing/integration/test_server_stdio` (pin what `store_list` / `show` now return).
- Docs where they say "nothing adopted" (`store_contract`, pilot docs, `session_handoff` snapshots that are not refreshed by the rerun ticket); the m1 register and charter only if a clause's evidence changed. State plainly that
  **no release candidate covers the 31 new slots** (`pilot/rc-0004` holds the forest only).
- The commit message says which assertions changed and why: "the user adopted terrain-v1 on 2026-10-05T18:17:03Z".

## Out of Scope
- A release candidate (`rc-0005`) or a runtime export of the new slots: `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` asks the user if the rerun needs it.
- Changing any adopted art, the registry, the compositor or the AM5 rules. Revocation. Any `src/` change.

## Acceptance Criteria
- [ ] Adoption files committed unchanged (the committed bytes equal what the store wrote; catalog `verify` clean, `draft verify` clean).
- [ ] The seven guards pass, each pinned to exact facts (adoption id, hash, counts, per-slot facts); none loosened or skipped; the snapshot guard compares file list and hashes.
- [ ] Docs say what is adopted and that no release candidate covers the new slots.
- [ ] Commit message names the changed assertions and the adoption timestamp.

## Related Tickets
- TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW (epic), TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS (previous), TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN (next)

## Related Docs
- docs/assets/store_contract.md, docs/assets/pilot_terrain_key.md, docs/assets/retention_and_rollback.md, docs/assets/session_handoff/

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS/ (the draft set and render-match evidence)

## Related Code Areas
- visual_assets/catalog/ (provenance, sources), tests/visual_assets/

## Assumptions / Open Questions
- The gitignored quarantine is untouched by this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
