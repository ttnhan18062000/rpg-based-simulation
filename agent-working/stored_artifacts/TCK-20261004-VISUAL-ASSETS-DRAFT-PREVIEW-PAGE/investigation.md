---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE
artifact_type: investigation
tags: [architecture, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE

- Drafts keep the 8x preview, not a 1x tile; export is pure Python, so the page draws the preview at 1/scale (nearest, exact).
- `TILE_NAMES` has 23 codes; one explicit key table is the contract for the terrain draft set.
- An entry without `detail` on an axis key is the default slot; the resolver keys slots by value, so the adapter normalizes it.
- A widest preview manifest at 256 entries is 154837 B: over MAX_RECORD_BYTES, so it uses the existing manifest bound (a derived export).
