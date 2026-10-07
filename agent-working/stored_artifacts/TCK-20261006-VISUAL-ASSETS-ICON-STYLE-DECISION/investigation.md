---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION
artifact_type: investigation
tags: [architecture, documentation, hud]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION

- Context scan: `search_docs` and `graphify query` surfaced the ADR (D1-D19), the store contract and the foundation plan; no earlier icon decision exists, so nothing conflicts. D17 (no variant axes) is respected: tier and marker state are separate keys.
- Research files: 4 files, 506 lines; UNVERIFIED marks 7 (games), 9 (packs), 5 (craft), 1 (synthesis), same as the committed originals.
- Ticket vs landed: ticket and decisions agree. Two points left to the planner: (a) the ticket's "map glyph 16, plate 16" does not say how glyph and plate share a canvas, so the guide fixes sizes and leaves layering to child 2; (b) the tier ladder follows the ticket (E-D plain, C-B pips, A frame, S+ stars), while `research_icon_craft.md` section 4 proposed bevelled/shield frames; both are recorded.
- Draft tooling: the 16x16 assumption check is for child 5; the MCP server states a 128x128 maximum, so 24x24 sprites are not blocked by that cap.
