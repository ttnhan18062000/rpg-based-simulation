---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation: Sample-map renderer

Question: how far does the adopted art go on those worlds? The renderer ports `terrainBorders.ts`, `pickDetail.ts` and the resolver order to Python (the TS is not imported or edited) and draws two labelled views per world: exact (primary) and alias (unconfirmed, #519). The client's per-world colour-code problem is rpg's (#523) and is not worked around. The store's PNG decoder refuses images over `MAX_DECODED_BYTES`, a bound, so big sheets are checked through their header. All 23 terrain keys have art in rc-0009.
