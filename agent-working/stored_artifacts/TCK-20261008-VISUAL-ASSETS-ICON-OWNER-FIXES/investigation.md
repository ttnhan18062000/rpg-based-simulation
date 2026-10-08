---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES

- Store route (adoption.py `_lineage`, cli `adopt`): `--source-asset-id <existing> --parent <latest unrevoked revision>` makes the next revision; `adopt-set` only creates new assets; `draft keep` refuses an existing source id; all six slots became adopted when the owner adopted `icons-v2`, so the ticket's `draft keep --replace` in `icons-v2` would have broken the adoption's recorded hash. Planner approved the new draft set route.
- A defect measured after drawing: the approved tent broke the 16x16 live-area rule (margins 1, 0, 1). Both options did. Refitted and re-confirmed by the owner before the final drawing.
- Compliance definitions corrected after seeing numbers (ruins stub detection by unbroken run from the ground; tent red area and doorway restated for the fitted tent). The bead's "lighter than the dark tiers" row first passed a recoloured slate bead (accents inflated the mean); the real slate bead is the planted case now.
- Blind round 4: bead, buff, rogue, toolbox named in free text; ruins ("document with arrow") and the enemy camp ("crossed tools on red mound") still flagged though the choice pass names both; unchanged icons flip between rounds (the shrine, once "stone tombstone"). The bead and tier D/E remain a shape twin at 25 XOR px.
- **Owner decision after the drafts (relayed by the planner, 2026-10-08), verbatim "Keep current versions":** the ruins arch and the tent camp are not revised and not proposed (the adopted brick wall and crossed swords stay; both drafts still misread in free text). The commit was amended: four revisions proposed (buff, rogue, tool, common), 8 owner commands, the two declined drafts left in the set as never-adopted drafts (the store has no command to drop a draft slot), specs for the ruins and the enemy camp restored to the adopted r0001. `owner_fixes_result.json` and `lookalike_proposed.json` are the evaluation of the set with the FOUR in place; the round-4 blind evidence for the other two is the adopted drawings' earlier rounds.
