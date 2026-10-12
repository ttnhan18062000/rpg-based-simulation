---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-DRAFTS
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation: Draw the three proof sources, intake, owner adopts

Question: can real animated and 9-slice art pass the pipeline within every bound? The aseprite MCP server of the session was stale (Lua pin guard), so the sources were drawn by calling the drawing api from the worktree with small deterministic scripts (kept in `scripts/`). Measured sizes are in the ticket (largest source 10,154 B of 102,400). Planted: a campfire handoff declaring 2 slices is QUARANTINED with `SLICE_COUNT_MISMATCH`. Adoption of 3 sources moves 14 catalog pins and the two no-animation/no-slices guards.
