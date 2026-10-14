---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING
artifact_type: investigation
date: 2026-10-08
tags: [architecture, planning]
---

# Internal gap audit (2026-10-08, HEAD 48c9785c3) - summary kept by planner
Known: K1 adopt-set no revisions; K2 no draft drop; K3 MCP main checkout; K4 fixtures pinned to rc; K5 W02.7 class field
(Y activation); K6 W03.1; K7 W06.3 (Y); K8 F3 slow PNG decoder (budgets.md:80-91,100).
New: 1 tile_pixels first-PNG fragility (pilot_terrain_m5_results.md:85); 2 review tooling ad hoc in tests/ per set
(review_sheets 505 lines); 3 no committed Playwright capture config; 4 preview page lacks fallback reason; 5 harness
mounts repo files, no real bundling/serving (surface:116-120) Y; 6 client checks decoded size only (fallback_safety:111);
7 animation metadata missing + MAX_SOURCE_BYTES blocks dense multi-frame (store_contract:217-218, budgets:45,99) Y for
animated; 8 one scale class, no atlases; 9 W07.4 capabilities; 10 real-Aseprite tests local only (D10); 11 no crash test
mid-publish, per-sprite lock only; 12 no store lock/deletion audit, human gate unauthenticated; 13 revocation local only;
14 gc no typed roots; 15 RGBA only intake; 16 stale docs (drawing_tools.md:18, foundation README:70,106,150);
17 recognition check thin; 18 colour-vision AT/non-hue route (W05) Y; 19 no HUD fallback/text contract Y.
Top 5 new: #2, #3+#5, #1, #16, #7.
