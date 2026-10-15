---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS
artifact_type: investigation
tags: [architecture, testing, mcp]
---

# Compliance table: measured from the pixels, 18 object markers (2026-10-14)

| key | rev | size | bbox (w x h) | margin to edge (px) | silhouette cells covered | extra opaque cells | colours / budget | lint warnings | spec 'fits live area' |
|---|---|---|---|---|---|---|---|---|---|
| `icon.building.healer_hut` | r0002 | 24 | 17 x 18 | 2 | 156 of 156 | 0 | 9 / 12 | value_separation [('#854b4d', '#4a6030'), ('#4a6030', '#555961'), ('#717e8f', '#a1766c'), ('#48b858', '#91a2ab')] | yes |
| `icon.building.mine_entrance` | r0003 | 24 | 20 x 19 | 2 | 102 of 102 | 0 | 4 / 12 | none | yes |
| `icon.building.town_hall` | r0002 | 24 | 20 x 19 | 2 | 173 of 173 | 91 | 5 / 12 | none | yes |
| `icon.building.watchtower` | r0003 | 24 | 16 x 20 | 2 | 188 of 188 | 3 | 5 / 12 | none | yes |
| `icon.marker.nest` | r0003 | 16 | 12 x 7 | 2 | 63 of 63 | 0 | 6 / 8 | none | yes |
| `icon.node.berry_thicket` | r0007 | 16 | 12 x 11 | 2 | 96 of 96 | 0 | 5 / 8 | value_separation [('#4a6030', '#d04030')] | yes |
| `icon.node.cover_patch_high` | r0003 | 16 | 14 x 13 | 1 | 96 of 96 | 54 | 4 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.cover_patch_low` | r0005 | 16 | 14 x 7 | 1 | 39 of 39 | 29 | 4 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.cover_patch_medium` | r0003 | 16 | 14 x 9 | 1 | 59 of 59 | 36 | 4 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.crystal_outcrop` | r0004 | 16 | 12 x 11 | 2 | 87 of 87 | 0 | 6 / 8 | none | yes |
| `icon.node.frost_shard_cluster` | r0003 | 16 | 12 x 10 | 2 | 38 of 38 | 40 | 4 / 8 | none | yes |
| `icon.node.healing_flower_patch` | r0004 | 16 | 13 x 13 | 1 | 49 of 49 | 38 | 7 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.herb_patch` | r0003 | 16 | 13 x 12 | 1 | 48 of 48 | 60 | 4 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.iron_vein` | r0005 | 16 | 12 x 10 | 2 | 88 of 88 | 0 | 6 / 8 | none | yes |
| `icon.node.moon_resin_tree` | r0002 | 16 | 10 x 11 | 2 | 51 of 51 | 0 | 5 / 8 | none | yes |
| `icon.node.silver_vein` | r0003 | 16 | 12 x 10 | 2 | 75 of 75 | 0 | 6 / 8 | none | yes |
| `icon.node.spirit_wisp` | r0006 | 16 | 9 x 12 | 1 | 48 of 48 | 29 | 6 / 8 | none | 1 px outline in the margin (fill-mode outline outside the approved shape) |
| `icon.node.wood_node` | r0002 | 16 | 10 x 11 | 2 | 72 of 72 | 0 | 3 / 8 | none | yes |

Notes: 'silhouette cells covered' is 100 % for all 18: every pixel of the owner-approved silhouette is drawn. 'Extra opaque cells' are (a) the outline drawn OUTSIDE the silhouette for the six thin-plant sprites in fill mode (herb_patch, the three cover patches, healing_flower_patch, spirit_wisp; they use one of the two margin pixels, so the live area is 14 x 14 instead of 12 x 12 and no pixel touches the canvas edge), (b) frost_shard_cluster's outside outline (margin stays 2), and (c) the town hall's parchment face (the enclosed hole of the scroll filled with parchment, 91 cells) and the watchtower's arrow slit (3 cells, dark). Finer proportions of the specs (a 17-px-tall pestle bulb, 11/7/4 px grass heights, 3 egg tops) were checked by eye on the review sheets, not measured. Lint warnings that remain: healer_hut (a wood pestle and green herb beside grey stone: shape, not hue, carries it) and berry_thicket (red berries on dark green: decorative detail, the bush shape and the berry shapes carry it); both are justified, not tuned away.
