---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT
phase: done
date: 2026-10-18
tags: [architecture, documentation]
---

# TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT

## Title
Sample-map gap report: say what is open now, and record the owner's 2026-10-18 answers on G6 (16 px building glyph) and G4 (variant offsets)

## Status
DONE

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
- New section "Update 2026-10-18: what is open now, and the owner's two answers" at the top of the updates: the two owner decisions in the owner's words (G6 "Keep scaled icons", G4 "Leave as is", via lead-planner), an "Open now" list (G5, G7, G10, G11, G12, client alias resolution) with owner and blocker, and a one-line list of what is closed.
- G4 and G6 table rows keep their old text and append the owner's decision. The art-priority question and the "Input list for candidate A" headings are marked ANSWERED, each with one line saying what happened; neither was deleted. No table number was changed or re-measured.
- Wording correction to the dispatch: #519 is CLOSED (answered 2026-10-11), so G5 is described as a design question for rpg-designer, not as "open on #519".

## Test Summary
- Ids checked read-only with `gh` and `git log`: PR #545 MERGED 2026-10-13 (squash `06aa3a20c`, rc-0010); PR #596 MERGED 2026-10-14 (`51b044c69`, rc-0011); PR #608 MERGED 2026-10-16 (`d7831efab`, not cited in the report); issues #519 CLOSED, #523 OPEN, #548 OPEN, #543 CLOSED; `agent-working/tickets/todos/visual-asset-entity-markers/` exists.
- `tools/validate_frontmatter.py` on the report and on this ticket: no violations.
- Scoped under `systemd-run --user --scope -q -p MemoryMax=3G`: `tests/docs/test_doc_integrity.py`, `tests/docs/test_doc_path_existence.py`, `tests/visual_assets/test_sample_map_render.py`: 41 passed, 1 skipped, 1 xfailed.

## Files Changed
- `docs/assets/sample_map/gap_report.md`

## Completion Summary
The gap report opens with a 2026-10-18 section: the owner's G6 "Keep scaled icons" and G4 "Leave as is" answers (via lead-planner), an Open-now list (G5, G7, G10, G11, G12, client alias resolution) with owner and blocker, and the art-priority and candidate-A sections marked answered, not deleted. Every id checked with gh and git (#519 is closed, #523 and #548 open). No table number changed. Approved by asset-planner (178de1ea4, 21e465157).
