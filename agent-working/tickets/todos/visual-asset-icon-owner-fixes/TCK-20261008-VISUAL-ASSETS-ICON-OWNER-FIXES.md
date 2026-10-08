---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES
phase: open
date: 2026-10-08
tags: [architecture, hud, testing]
---

# TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES

## Title
Owner review fixes before PR #418 merges: ruins, common bead, buff frame, blade motifs and the tool icon, through the recognisability process

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Follow-up to `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`, on the same branch and PR. PR #418 (icon set v2) is CI-green and planner-approved, but the owner held the merge ("Don't merge yet") and then
asked to "finish what blocks the PR". The planner's readiness comment on #418 listed five owner-judgement items; the owner
chose (blocking question, 2026-10-08) to fix ALL of them before the merge: the ruins glyph, the common rarity bead, the
adopted buff frame, and the blade motifs + the unmatched spirit lantern.

## Scope
Follow the style guide's recognisability process for every changed icon, in order:
1. **Specs** (update `visual_assets/icons/icon_specs.yaml`, before drawing). Planner proposals, the owner may change them
   at step 3:
   - `icon.marker.ruins` (v2): a new idea, e.g. a broken stone arch with rubble at its feet.
   - `icon.rarity.common` (v2): a lighter silver-grey round bead with a highlight, so it no longer resembles the dark
     tier E/D badges; the rarity I2 ladder must still pass.
   - `icon.status.frame_buff` (adopted key set): a solid up arrow, the mirror of the redrawn debuff's down arrow, in the
     unchanged round green frame, so it stops reading as a gem.
   - Blades: the sword stays only on `icon.item.weapon`. `icon.class.rogue` (v2) becomes a hooded cowl or mask;
     `icon.marker.enemy_camp` (adopted key set) becomes a tent with crossed spears; `icon.class.warrior` keeps its shield
     (the shield is its silhouette).
   - `icon.item.tool` (v2): a toolbox (covers `repair_kit`; one family icon cannot also depict `spirit_lantern`; say so).
2. **Reference study** per changed glyph (reference only, TASL recorded).
3. **One-colour silhouette sheet** of the changed icons next to their neighbours, shown to the owner on the preview page;
   the owner approves or changes it by blocking question BEFORE any full drawing.
4. **Draw** the approved silhouettes (palette icons-v1, own pixels, worktree CLI intakes).
   - v2 slots: `draft keep --replace` in `icons-v2`.
   - Key-set slots (buff frame, enemy camp): find the store's supported route for a new revision of an adopted source
     (`adoption.py` lineage, `parent_revision`); a new draft set for the two is acceptable. Report the route to the
     planner before using it.
5. **Checks:** sheet rule (thresholds unchanged), measured spec compliance table, blind recognition check, whole-sheet
   look-alike report; before/after in the review doc. Refresh fixtures and the preview page.
6. Merge origin/main into the branch first (26 commits behind as of 2026-10-08) and keep it current.
7. Hand the owner the preview URL and the exact adopt-set command(s) (own terminal; licence placeholder).

## Out of Scope
- Wiring icons into the app. Changing any user threshold. Icons not listed above.

## Acceptance Criteria
- [ ] Specs updated and the silhouette sheet approved by the owner before drawing (answer recorded verbatim).
- [ ] Every listed icon redrawn; rule PASS; compliance tables met; blind check and look-alike report re-run and recorded.
- [ ] The re-adoption route for adopted key-set slots is the store's own, reported before use.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (done; PR #418), TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS (the process)

## Related Docs
- docs/assets/icon_style_guide.md (process rule), icon_set_v2_review.md, icon_key_set_review.md; PR #418 readiness comment

## Related Stored Artifacts


## Related Code Areas
- visual_assets/icons/icon_specs.yaml, visual_assets/drafts/, visual_assets/store/adoption.py (read), frontend/src/visualAssets/

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

