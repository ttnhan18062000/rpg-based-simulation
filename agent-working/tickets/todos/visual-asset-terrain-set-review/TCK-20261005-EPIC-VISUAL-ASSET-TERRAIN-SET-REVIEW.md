---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW
phase: open
date: 2026-10-05
tags: [architecture, live-map, planning]
---

# TCK-20261005-EPIC-VISUAL-ASSET-TERRAIN-SET-REVIEW

## Title
Terrain set review: a predeclared colour-vision rule for whole sets, terrain-v1 redrawn to it, the owner's adopt-set, then the deferred M5 rerun

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The user (2026-10-05) asked for the next asset batch and chose, by blocking question each:
- **The M5 detail rerun** (`TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`) over new asset kinds or staying paused.
- **Fix the set, then rerun.** The rerun was deferred by the user on 2026-10-04 until a full draft set is reviewed and
  adopted (`adopt-set`), so one review covers a whole map. `terrain-v1` (22 drafts) is not adopted and carries an open
  colour-vision finding (`cvd_pairs.txt`: 30 pair-vision cases where the drafts are harder to tell apart than the flat
  fills, mostly `dungeon_entrance`, then grassland/farmland, desert/ruins; closest pair forest/volcanic, protan).
  So: predeclare a set rule, redraw to it, the owner reviews and adopts the whole set, then rerun M5 against it.

This lifts the asset pause for this batch only (user, 2026-10-05). Icons and other kinds stay parked.

## Scope
Children (order and gates in `SEQUENCE.md`):
1. `TCK-20261005-VISUAL-ASSETS-SET-COLOUR-VISION-RULE`: a committed, tested colour-vision check for a whole draft set,
   its pass rule and the whole-map M5 scene criteria predeclared and owner-approved before any redraw; baseline
   measured on today's `terrain-v1`.
2. `TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW`: redraw the failing drafts (`draft keep --replace`),
   re-measure, record the result as measured.
3. `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT` (added 2026-10-06 by the user's choice): terrain priority, `crisp` set,
   C6 borders criterion, pure compositor `borderOverlays`, `border.*` mask key family, decorative fallback.
4. `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS` (added 2026-10-06): draw the shared masks, keep them in `terrain-v1`,
   preview-page borders toggle, evidence.
5. **Owner gate (no ticket), held until borders exist:** the user reviews the whole map with borders and runs `adopt-set`
   (tiles and masks) themselves.
6. `TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION` (added 2026-10-06): record the user's adoption of `terrain-v1` (31 adoptions) and re-point the guards that described the pre-adoption catalog.
7. `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` (moved here, re-scoped): rerun M5 against the adopted set (W03-SET with C6 and a
   missing-mask fallback check), record, refresh the handoff snapshots, close the batch.

## Out of Scope
- Adoption by an agent (adopt, adopt-set, revoke are the user's). Charter signing, any `AM-M6` authorization.
- Forest's adopted slots (plain, bush, tree): never redrawn; a pair involving forest is fixed on the other side.
- Any `src/` change, simulation or API change; the normal Live Map.
- Icons, entities, buildings, items, UI (parked, no tickets).

## Acceptance Criteria
- [ ] All children done or explicitly deferred by the user; `SEQUENCE.md` status line states the outcome.
- [ ] Every gate result recorded as measured (rule never reworded to pass).

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET (done; the set and the finding)
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (done; parent of the rerun)
- TCK-20261004-VISUAL-ASSETS-M5-RERUN-AND-M6-CHARTER (done; the method)

## Related Docs
- docs/assets/pilot_terrain_m5_criteria.md, docs/assets/pilot_terrain_m5_results.md, docs/assets/store_contract.md
- docs/assets/fallback_safety.md, docs/assets/m2_evidence_charter.md, docs/assets/session_handoff/

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/ (cvd_pairs.txt, tile_generator.py)

## Related Code Areas
- visual_assets/drafts/terrain-v1/, visual_assets/store/drafts.py, tests/visual_assets/pilot_colour_vision.py,
  frontend/src/visualAssets/

## Assumptions / Open Questions
- The rule's thresholds are the user's to approve (child 1 asks before fixing them).
- Whether the rerun needs a new release (`pilot/rc-0004`) holding the adopted set is decided in child 4 against what
  landed; if yes, assembling it is asked of the user first.

## Implementation Notes
Epic-tier: not implemented directly.

## Test Summary

## Files Changed

## Completion Summary
