---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION
phase: done
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION

## Title
Icon style decision: the research in the repo, ADR D20 and an icon style guide

## Status
DONE

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
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION/ (plan, investigation, test_plan)

## Related Code Areas
- docs/ only

## Assumptions / Open Questions
- The tier ladder's exact pip/frame/star split is the planner's proposal from the research; the user confirmed the direction, and child 5's art is reviewed against it.

## Implementation Notes
- Research moved with `git mv`-equivalent into `docs/assets/icon_research/` (frontmatter added; one path note added to the synthesis; UNVERIFIED mark counts equal the originals: 7, 9, 5, 1).
- D20 added to the ADR with the user's decisions as given; the tier ladder and the rule thresholds are explicitly not part of the row.
- Style guide fixes sizes and margins and leaves glyph/plate layering to child 2; the tier ladder follows the ticket and notes the research's different proposal.

## Test Summary
- `tools/validate_frontmatter.py`: research, guide, artifacts, ticket clean.
- `pytest tests/docs tests/static`: 134 passed, 2 skipped, 1 xfailed.

## Files Changed
- docs/assets/icon_research/*.md (4, moved), docs/assets/icon_style_guide.md, docs/architecture/visual_asset_foundation_adr.md, ticket and stored artifacts.

## Completion Summary
Research committed under docs/assets/icon_research/, ADR D20 and docs/assets/icon_style_guide.md written, no art/key/palette/code. Open for the planner: glyph/plate layering (child 2) and the ladder split (child 5 review).
