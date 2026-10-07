---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON
artifact_type: investigation
tags: [live-map, hud, testing]
---

# Investigation — TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

- GameCanvas zoom: 0.5 to 3.0 in steps of 0.15; canvases use CSS scale(zoom), the overlay scale(16 x zoom), all pixelated; CELL_SIZE 16.
- AM5-W08 isolation test forbids app files importing visualAssets and the reverse: the components live outside visualAssets (reported to the planner).
- Level list per DPR is in the ticket. Minimap deliberately unchanged.
- useCanvas hit-testing uses CELL_SIZE x zoom, so it follows the snapped zoom.
