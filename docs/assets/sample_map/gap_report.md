---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-12
tags: [architecture, documentation, live-map]
---

# Sample map gap report

What the adopted art (rc-0009) does and does not cover on three real compiled worlds, from `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`. Read it with the [README](README.md) (what was rendered, the commands,
the committed crops). Every number says which view it comes from: **exact** (the primary evidence: only exact key names draw) or **alias** (UNCONFIRMED: asset-planner proposals for rpg-planner, see below).
Sources: the data files `reports/visual_assets/sample_map/<world>/world_data.json` and `render_stats.json` (`python -m tools.visual_assets_sample_map data --all` and `render --all`, seed 42,
`src/api/engine_manager.py:133-136`), the registry `visual_assets/catalog/definitions/visual_keys.yaml` and the rc-0009 runtime export.

## Where rpg stands (reconciled, nothing re-rendered)

- **[#519](https://github.com/ttnhan18062000/rpg-based-simulation/issues/519)** (read-only questions to rpg-planner) has ANSWERED (rpg-planner comment 2026-10-11): tile codes are per world and the client's colour table is fixed (so key on terrain
  strings, as this batch does); the live API world is not the authored world (it spawns 1 hero and 9 goblins and `present_static` returns `locations: []`, so places and entities are read from the compiled
  world, as done here); buildings are one tile each; the client draws buildings as tinted squares with a letter, resource nodes as inset squares and entities as circles; multi-tile structures, terrain variants and
  connecting tiles are not supported live; design questions go to rpg-designer. Nothing in the answer contradicts a number here. rpg's counts over ALL worlds (not re-measured by this batch): buildings shop 24, inn 24,
  healer_hut 21, blacksmith 20, town_hall 19, mine_entrance 7, watchtower 4; places CITY 20, CAMP 11, NEST 10, RUIN 9, LAIR 2 (DUNGEON and LANDMARK exist, unused). rpg suggested other sample worlds
  (`sandbox_world`, `wilderness_survival`); per the lead's order (#519 does not gate this batch) the three here stay.
- **[#523](https://github.com/ttnhan18062000/rpg-based-simulation/issues/523)** (rpg bug, filed by lead-planner): the Live Map colours terrain by a per-world sorted index into the FIXED `TILE_COLORS` table, so the colour depends on where a terrain
  name falls in that world's sort order (read from the code, not yet reproduced at runtime), and V2 world terrain names are not the 23-code set the keys follow. This report is evidence for #523; the picture here draws by NAME and
  does not work around the bug. Decisions that are rpg's, not made here: the fix shape (a stable server vocabulary, or the client colouring by name through the manifest) and whether asset keys follow V2 names or V2 maps onto the 23-code set.
  Rows that depend on that answer say "unconfirmed by rpg-planner (#519, #523)".

## Evidence for #523: cells per terrain name (exact names as the presenter emits them)

`PLAIN` and `plain` are kept separate: they are two terrain names in the same world (the compiler fills `PLAIN`; region painting uses `plain`). 87.9 % of the 73,808 cells (64,872) have no exact key.

| terrain name | `frontier_living_world` | `highland_traverse` | `dungeon_crawl` | all three | exact key | proposed alias (unconfirmed: asset-planner proposal for rpg-planner, #519) |
|---|---|---|---|---|---|---|
| `PLAIN` | 8,670 | 36,567 | 9,424 | 54,661 | **none** | `terrain.grassland` |
| `plain` | 2,257 | 3,321 | - | 5,578 | **none** | `terrain.grassland` |
| `forest` | 1,455 | 1,681 | 1,116 | 4,252 | `terrain.forest` | - |
| `ruin` | 1,681 | - | 1,681 | 3,362 | **none** (near `terrain.ruins`, not applied) | `terrain.ruins` |
| `cave` | 1,886 | - | - | 1,886 | `terrain.cave` | - |
| `mountain` | - | 1,681 | - | 1,681 | `terrain.mountain` | - |
| `river` | - | 1,271 | - | 1,271 | **none** | `terrain.shallow_water` (`terrain.water` is the alternative) |
| `road` | 947 | - | - | 947 | `terrain.road` | - |
| `swamp` | 170 | - | - | 170 | `terrain.swamp` | - |
| total cells | 17,066 | 44,521 | 12,221 | 73,808 | | |

Cells with art / in the gap, by view: `frontier_living_world` exact 4,458 / 12,608, alias 17,066 / 0; `highland_traverse` exact 3,362 / 41,159, alias 44,521 / 0; `dungeon_crawl` exact 1,116 / 11,105, alias 12,221 / 0. All 23 terrain keys
have art in rc-0009, so no key falls back to the Live Map flat fill; the alias view is therefore the upper bound of what the existing tiles can cover.

## The gaps (each sized and given a "needed by")

Read G12 first: no amount of terrain art makes these maps look rich, because the worlds themselves are a few rectangles over one default fill. G12 is rpg's to judge and does not change the options of the owner's question below.

Needed-by classes: **vocabulary** (rpg's #523 decision, no art), **terrain variants**, **connecting tiles**, **multi-tile structures**, **A markers** (candidate A, entity and object markers), **rpg world generation** (not art). Estimates count tiles or
sprites to draw at the sizes the store already holds (terrain tiles 16 x 16, building icons 24 x 24, markers 16 x 16); they are order-of-magnitude inputs for the owner's question, not commitments, and they do not include the
registry growth a new key or a detail axis causes (see "Input list for candidate A").

| # | gap | evidence (view) | estimate | needed by | status |
|---|---|---|---|---|---|
| G1 | `PLAIN` and `plain` have no key | 60,239 of 73,808 cells (81.6 %) draw as gap in the exact view; both fill the whole world outside regions | 0 tiles if both alias to `terrain.grassland`; 1 tile (16 x 16), or 3 with a forest-style detail axis, for a new `terrain.plain` | vocabulary, terrain variants | unconfirmed by rpg-planner (#519, #523); the `PLAIN`/`plain` duplicate is rpg's to resolve |
| G2 | `ruin` is not `ruins` | 3,362 cells (frontier 1,681, dungeon 1,681) | 0 tiles: a name mapping | vocabulary | unconfirmed by rpg-planner (#523) |
| G3 | `river` has no key | 1,271 cells (highland, one 41 x 31 rectangle) | 0 tiles if it aliases to `terrain.shallow_water` or `terrain.water`; 1 tile for a new `terrain.river` | vocabulary | unconfirmed by rpg-planner (#523) |
| G4 | one tile repeated: no terrain variants outside forest | in the alias view `terrain.grassland` repeats one 16 x 16 tile over 60,239 cells; only `terrain.forest` declares a detail axis (3 values); visible as a regular texture in the renders | 2 extra tiles per key for the 7 terrains the samples use (grassland, ruins, mountain, water or shallow_water, cave, road, swamp) = 14 tiles, plus one detail axis per key | terrain variants | not an rpg question (the client supports no variants live, #519); the axis needs the registry budget review first |
| G5 | no connecting tiles (roads, rivers, coasts) | `road` 947 cells and `river` 1,271 cells appear as plain rectangles (regions painted as rectangles), so the data does not yet need them; the client cannot draw them live (#519) | 16 edge-connection tiles (a 4-side mask) per family x 3 families (road, river or water, coast) = 48 tiles; the 9 border masks cover rank fringes only | connecting tiles | design question for rpg-designer (#519); unconfirmed |
| G6 | building kinds with no icon | healer_hut (2 in the samples; 21 in all worlds per rpg), town_hall (1; 19), mine_entrance (1; 7), watchtower (1; 4) have no `icon.building.*`; `shop` (3; 24) has none exactly (alias `icon.building.store`, unconfirmed); `blacksmith` 2 and `inn` 3 draw | 4 icons (24 x 24) exact; 4 if the `shop` alias holds; 5 if it does not | A markers | `guild`, `hero_house`, `class_hall` exist but no world uses them; rpg: hero retires in M1 (D63), do not invest |
| G7 | every building is one tile, no multi-tile structures | the town of the frontier world is 8 buildings on one flat terrain (`frontier_town_*` crops); the data gives each building one position; the client draws a lettered square (#519) | 7 structure sprites at 32 x 32 (a 2 x 2 footprint), one per building kind in the samples (town_hall, shop, blacksmith, inn, healer_hut, mine_entrance, watchtower), if structures are to span cells | multi-tile structures | design question for rpg-designer; not supported live; unconfirmed |
| G8 | resource-node kinds have no marker | 9 kinds, 15 nodes in the samples (berry_thicket 2, crystal_outcrop 1, frost_shard_cluster 1, healing_flower_patch 1, herb_patch 3, iron_vein 3, silver_vein 1, spirit_wisp 1, wood_node 2); no exact or aliased key | 9 icons (16 x 16), or one shared grove glyph plus per-kind variants; `icon.marker.resource_grove` exists but nothing maps to it (rpg: no world produces it) | A markers | unconfirmed by rpg-planner (#519) |
| G9 | place kinds: CITY and NEST have no glyph; CAMP and RUIN only by alias | CITY 2, NEST 1 (no key); CAMP 1, RUIN 2 (alias `enemy_camp`, `ruins`, unconfirmed); LAIR, DUNGEON, LANDMARK unused in the samples; the live API puts no places on the map (`locations: []`) | 1 glyph for NEST (CITY may be the plate alone); LAIR to `boss_arena` and DUNGEON to `dungeon_entrance` are rpg's suggestions with a question mark | A markers | unconfirmed by rpg-planner (#519) |
| G10 | no entity markers | 10 kinds, 79 entities in the samples (alpha, blacksmith, guard, leader, merchant, predator_hunter, raider, scout, sentinel, worker); `icon.class.*` holds warrior, ranger, mage and rogue only | 10 role markers, or about 4 to 6 property markers (diet, size) if rpg's M1 moves kinds to properties | A markers | waits on the vocabulary answer (#523); not drawn in the picture, counted in the data |
| G12 | the sample worlds are rectangular regions over one default fill | 87.9 % of cells carry no exact key, and what is left is flat: the Hometown crop is eight building icons scattered over one terrain, River Ford is one 41 x 31 rectangle of `river`, the ruin and forest blocks are rectangles (`frontier_town_*`, `highland_river_*`, `dungeon_ruin_*` crops); region painting fills rectangles over `PLAIN` (rpg, #519, `compiler.py:380-426`) | 0 art: more tiles do not change the shape of the maps | rpg world generation, not art | rpg's to judge (#519, #523); recorded so the ranking of terrain variants (G4) is read next to it |
| G11 | chests | `present_static` carries `treasure_chests` but the three worlds hold 0 | not estimated: no evidence | A markers | no data |

Objects in the exact view (drawn / in the gap, from `render_stats.json`): `frontier_living_world` 3 / 21, `highland_traverse` 2 / 7, `dungeon_crawl` 0 / 1; in the alias view 7 / 17, 3 / 6, 1 / 0. The per-kind lists
are in each `render_stats.json` (`objects_gap`) and on the page.

Not gaps (stock to know about): 18 of the 23 terrain keys have art that no sample world draws in the exact view; `guild`, `hero_house` and `class_hall` icons are unused by every world.

## The owner's art-priority question (drafted; asset-planner asks it)

> The sample map shows the art covering 12.1 % of the sampled cells by exact name and all of them by the proposed aliases, and lists what is missing (and, in G12, that the sampled worlds are a few rectangles over one default fill, which is rpg's to judge). Which should the next asset batch draw first, given the
> counts above? (Options in a fixed order, none recommended.)
> 1. **Terrain variants** (G4: about 14 tiles, plus the registry budget review) and a name decision for `PLAIN`/`plain` (G1) if rpg wants new keys.
> 2. **Map markers** (A: building icons G6, resource nodes G8, places G9, entities G10: about 4 + 9 + 1 + 4 to 10 icons).
> 3. **Connecting tiles** (G5: about 48 tiles; needs rpg-designer's design first).
> 4. **Multi-tile structures** (G7: about 7 sprites; needs rpg-designer's design and client support first).
> 5. Wait for rpg's vocabulary decision (#523) before drawing anything that depends on terrain or entity names.

## Input list for candidate A (entity and object markers)

- The vocabulary decision (#523): asset terrain and entity keys follow V2's names, or V2 maps onto the 23-code set. A should not start before it.
- The kinds and counts above (G6, G8, G9, G10) and rpg's counts over all worlds (#519); rpg's note that markers keyed on diet and size outlast markers keyed on role (M1 moves kinds to properties).
- `MAX_REGISTRY_BYTES` budget review FIRST (`docs/assets/budgets.md`): the registry is at 29,525 B of 458,752 B after rc-0009 (6.4 %), and about 18 to 24 new marker keys (G6 to G10) and any detail axes (G4) are what the review has to size; a new key
  is optional and cheap, a new per-key field is not.
- A new key needs a runtime release (any registry edit makes older candidates unexportable, `store_contract.md` Known gaps), so A ends with its own candidate and the tests that export the committed one re-pointed.
- The frame-1-only build (`TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY`) matters only if a marker is animated.
- Process rule (style guide): spec, reference study, owner-approved silhouette sheet, draw, compliance table, checks, owner gate with the review folder.

## What was not measured

The picture shows how far the art goes, not whether it looks good. Three worlds at one seed are three samples; rpg's other worlds (and its suggested `sandbox_world`, `wilderness_survival`) were not rendered. The
client's real colouring (#523) was read from code, not observed at runtime. Entity positions are in the data but not drawn. Estimates are counts of tiles or sprites, not hours.
