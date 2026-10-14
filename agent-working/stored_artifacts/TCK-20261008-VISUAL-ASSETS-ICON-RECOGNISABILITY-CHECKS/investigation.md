---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

- The first run of the check is in `blind_check_results.md`. Headline: it found five real v2 misreads (ruins as mountain peaks, trinket as a medal, tool as a war hammer, ranger bow as a crossbow, common bead as a square) and, on calibration, that the adopted buff and debuff frames are not read as arrows at a glance. It did **not** flag the sword the owner objected to: that complaint is about quality and a cross-family twin with the dagger, which only the look-alike report saw (55 XOR px, next nearest 152).
- Substring scoring wrongly accepted "crossbow" for the synonym "bow"; the tool uses whole-word matching and a test pins it.
- Whether the fresh agents had no project context cannot be verified (the harness may attach the repository's instructions); the record says so.
- Reference study could only view previews of two CC0 Kenney packs; game-icons.net and Shikashi were not examined.
