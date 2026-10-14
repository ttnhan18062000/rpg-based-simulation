---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW
artifact_type: plan
tags: [architecture, testing, hud]
---

# Plan — TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW

Planner ruling (2026-10-08): redraw the sword, ruins, trinket, tool, ranger and common bead to their specs; keep the dagger unless the look-alike report still puts it within about 100 XOR px of the new sword; report-only for the adopted buff and debuff frames and tiers B, D, E.
1. Add the process-rule step "spec compliance table" and `icon_compliance.py` (every spec proportion measured from the pixels); revise the six specs before drawing (wrench for the tool family, ruined wall, teardrop chain loop, longbow, 7 px bead).
2. Prototype on the local canvas, look at renders, iterate (the ruins went through four ideas); draw via the drawing API, intake with the worktree CLI, `draft keep --replace` per slot.
3. Re-run the sheet rule, the compliance tables, the look-alike report and the blind check (fresh agents, free text and choice, all 36); refresh the fixture and the hash in the adopt template; before/after in the review doc.
