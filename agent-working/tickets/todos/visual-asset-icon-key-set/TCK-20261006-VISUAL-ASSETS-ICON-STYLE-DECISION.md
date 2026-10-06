---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION
phase: open
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION

## Title
Icon style decision: the research in the repo, ADR D20 and an icon style guide

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. The research lives only in the planner's session scratchpad, which is not durable. User decisions (blocking questions, 2026-10-06, after the research): style **B + tier badges** (16x16 map glyph
  on a shared per-category plate, 24x24 panel icons, an 8x8 tier badge whose shape escalates, status frames that differ
  in shape with up/down chevrons); palette **terrain-v1 base + 3-4 step ramps + a small accent set**, checked sheet-wide;
  outside art **reference only** (recorded as title/author/source/licence), **no AI generators**; map zoom **snaps to
  whole-number scales**.
Record the decisions and their evidence before anything is drawn, so later tickets cite a committed source.

## Scope
- Move the four research files from `agent-working/staging_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION/research/` (committed by the planner) into `docs/assets/icon_research/` with frontmatter
  (`layer: architecture`, registered tags), unchanged in substance; keep every source URL and every UNVERIFIED mark.
- ADR `docs/architecture/visual_asset_foundation_adr.md`: row **D20** (icon style, sizes, palette basis, reference-only
  outside art with TASL records, no AI generators, integer map zoom), status "decided (user, 2026-10-06, blocking
  questions)", with its revisit trigger. Note how it respects D17: tier and marker state are **separate keys**, not variant axes.
- `docs/assets/icon_style_guide.md`: the per-icon and per-set checklist (from `research_icon_craft.md`), sizes per family
  (map glyph 16, plate 16, panel 24, tier badge 8, status 16 with a 1 px margin rule per size), one light direction
  (top-left), one outline policy, one view angle per family, the tier badge ladder (E-D plain, C-B pips, A frame,
  S/SS/SSS stars; the letter stays as text beside it), buff/debuff frame shapes with chevrons, labels for abstract
  concepts, and how outside references are recorded (title, author, source, licence; reference only).
- `make knowledge-index-update` after the docs land.

## Out of Scope
- Any art, key, palette or code. Changing D17.

## Acceptance Criteria
- [ ] Research files committed with sources intact; frontmatter valid.
- [ ] D20 written with the user's decisions as given (no additions presented as decided).
- [ ] Style guide states every size and the tier ladder; it cites the research section for each rule.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic)

## Related Docs
- docs/architecture/visual_asset_foundation_adr.md, docs/assets/pixel_art_technique.md

## Related Stored Artifacts


## Related Code Areas
- docs/ only

## Assumptions / Open Questions
- The tier ladder's exact pip/frame/star split is the planner's proposal from the research; the user confirmed the direction, and child 5's art is reviewed against it.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

