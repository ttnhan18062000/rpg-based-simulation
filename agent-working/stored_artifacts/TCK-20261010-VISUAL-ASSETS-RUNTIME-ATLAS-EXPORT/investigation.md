---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RUNTIME-ATLAS-EXPORT
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation
rc-0008 families: border 9 (masks, 16x16), icon 36 (16/24 px), terrain 25. All three fit one shelf: sheets 172x20, 725x28, 476x20. The decoder bound `MAX_DECODED_BYTES` (1024 x 1024 RGBA) is what limits a verifiable sheet, so `MAX_ATLAS_DIM` is 1024, not the 2048 first imagined. Canvas 2D in the client has no use for atlases today; this is an export option only. A new `MAX_` bound needs an owner decision: the budgets row is PROPOSED.
