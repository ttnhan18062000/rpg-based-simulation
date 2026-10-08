# Implementation Sequence — visual-asset-icon-owner-fixes

Follow-up to `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2` on the SAME branch `visual-asset-icon-set-v2` and PR #418 (worktree
`/home/vboxuser/Work/rpg-aseprite-mcp`), built by `asset-implementer`, reviewed by `asset-planner`. No `src/`, no app wiring.

## Order

1. `TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`: specs -> reference study -> **owner-approved silhouette sheet** -> draw -> checks -> owner commands.
1b. `TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER` (added 2026-10-08, owner request): review sheets as a folder of PNG canvases + README; generated for this gate.
2. **Owner gate, no ticket:** the owner reviews and re-adopts in their own terminal.
3. `TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION`: record, guards, PR notes, close.

## Decisions

- PR #418 (icon set v2) is CI-green and planner-approved, but the owner held the merge ("Don't merge yet") and then
asked to "finish what blocks the PR". The planner's readiness comment on #418 listed five owner-judgement items; the owner
chose (blocking question, 2026-10-08) to fix ALL of them before the merge: the ruins glyph, the common rarity bead, the
adopted buff frame, and the blade motifs + the unmatched spirit lantern.
- Owner, after seeing the drafts (planner's blocking question, 2026-10-08), verbatim: "Keep current versions" for the ruins arch and the spear-tent camp: not revised, not proposed. Four revisions remain.
- Planner proposals (owner may change at the silhouette step): ruins = broken arch + rubble; common = silver bead; buff =
  solid up arrow; rogue = hood/mask; enemy camp = tent + crossed spears; warrior keeps the shield; tool = toolbox.

## Status

IN PROGRESS (2026-10-08): the fixes ticket is done and reviewed; the owner kept the adopted ruins and enemy camp ("Keep current versions"), so four revisions are proposed (buff, rogue, tool, common) and the owner adopts them with 8 commands in the review doc; the recording ticket waits for that.
