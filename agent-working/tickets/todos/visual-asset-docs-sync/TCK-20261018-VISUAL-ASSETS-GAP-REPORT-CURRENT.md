---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT
phase: open
date: 2026-10-18
tags: [architecture, documentation]
---

# TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT

## Title
Sample-map gap report: say what is open now, and record the owner's 2026-10-18 answers on G6 (16 px building glyph) and G4 (variant offsets)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/assets/sample_map/gap_report.md` is the doc that rpg and the owner read for asset status. It still presents two sections as open questions, and both were answered and shipped:
- "The owner's art-priority question (drafted; asset-planner asks it)": terrain variants shipped in rc-0010 (#545) and map markers in rc-0011 (#596).
- "Input list for candidate A (entity and object markers)": the object half shipped in rc-0011; the entity half moved to `agent-working/tickets/todos/visual-asset-entity-markers/`.

The owner answered two further questions on 2026-10-18, through lead-planner, with neutral options:
- **G6**, "Keep scaled icons": no 16 x 16 building map glyph. Buildings stay 24 x 24 panel icons scaled to one cell.
- **G4**, "Leave as is": no grassland redraw with different feature offsets per variant.

## Scope
- Add an update section dated 2026-10-18 at the top (same shape as the 2026-10-13 and 2026-10-14 updates). It holds:
  - the two owner decisions above, worded as decisions, dated, with "via lead-planner";
  - a short **"Open now"** list, one line per gap, naming the owner and the blocker:
    - G5 connecting tiles: rpg-designer design question, #519.
    - G7 multi-tile structures: rpg-designer design question, client support.
    - G10 entities: gated on #523 and the owner's role-id vs species+size choice; tickets in `todos/visual-asset-entity-markers/`.
    - G11 chests: no data.
    - G12 world shape: rpg's.
    - Client alias resolution: registry-only, Known gap, #523.
- Mark G6 and G4 **closed by owner choice (2026-10-18)** in their table rows. Keep the old text; append the decision, the way G6/G8/G9 were marked closed in rc-0011.
- Mark the "owner's art-priority question" and the "Input list for candidate A" sections **answered**, with one line each saying what happened (rc-0010, rc-0011, entity batch) and where. Do not delete them; they are the record of what was asked.
- Check every PR, issue and rc number you write against git log and `gh` (read only). Write no number from memory.

## Out of Scope
- No re-render, no new measurement, no number in the tables changed (nothing was re-measured).
- No change to `docs/assets/sample_map/README.md` beyond one link line, if the README points readers at a section this ticket renames.
- No `visual_assets/`, store, registry or test change. The registry comment nit rides the entity-marker batch.
- No answer on rpg's behalf (#523, #519, G12).

## Acceptance Criteria
- [ ] A reader of the report's first screen can tell what is open, whose it is, and what blocks it, without reading the 2026-10-13 and 2026-10-14 updates.
- [ ] The G4 and G6 rows and the update section record the owner's 2026-10-18 answers in the owner's words ("Keep scaled icons", "Leave as is").
- [ ] Both answered sections are marked answered and not deleted.
- [ ] Every PR, issue, rc and set-adoption id you cite is checked; the ticket lists the check.
- [ ] Frontmatter and docs checks pass, scoped: `python3 tools/validate_frontmatter.py` on the changed doc and on this ticket, plus the docs tests that cover `docs/assets/` (find them; run scoped, under the MemoryMax cap).

## Related Tickets
- `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT` (wrote the report)
- `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS` (rc-0011 update), the terrain-variants batch (#545, rc-0010 update)
- `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS` (G10, gated)
- Same batch: `TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS`

## Related Docs
- `docs/assets/sample_map/gap_report.md`, `docs/assets/sample_map/README.md`, `docs/assets/store_contract.md` (Known gap: aliases)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`

## Related Code Areas
- None (docs only).

## Assumptions / Open Questions
- Assumed: the owner's two answers are final for now. Either can reopen on the owner's word; say so in one clause, not more.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
