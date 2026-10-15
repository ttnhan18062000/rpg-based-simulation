---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-13
tags: [architecture, documentation, live-map]
---

# Sample map: the adopted art (rc-0011) on three compiled worlds

What this is: an OFFLINE picture of how far the adopted visual art goes on three real, compiled worlds, made by `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP`
(`TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`, `-RENDER`, `-GAP-REPORT`). It is **evidence, not an asset**: nothing here is intaken, adopted or put in a release
candidate, nothing is wired into the app (activation stays parked until the RPG core lands), and no file under `src/`, `frontend/`, `data/` or the content registries
was written. The gaps it found, each sized and given a "needed by", are in [gap_report.md](gap_report.md).

## The three worlds (chosen from `make world-list`)

| world | size | role |
|---|---|---|
| `frontier_living_world` | 161 x 106 | town (town hall, 2 inns, 2 shops, blacksmith, healer hut) next to a mixed wilderness (forest, swamp, road, plain) and a dungeon area (cave, ruin, old mine) |
| `highland_traverse` | 211 x 211 | a wilderness with several terrains (mountain, river, forest, plain) and a watchtower |
| `dungeon_crawl` | 101 x 121 | a dungeon area (ruin, forest) with sentinels and scouts, and no buildings or resource nodes: thin, stated as such |

`swamp_border_world` was not used: it adds no terrain name the frontier world lacks.

## How the data is made (read-only)

The state is built exactly as the API builds it (`src/api/engine_manager.py:133-136`: `WorldRepository("data/worlds").load_world(id)`, then
`WorldCompiler.compile(spec, seed=42)`, seed 42 being `EngineManager`'s default) and shaped by `StatePresenter.present_map` / `present_static`
(`src/api/presenters/state_presenter.py:186`, `:221`). Nothing is written by that path (`compile` writes only when given `output_report_path`, which is never given; `world-compile`
and `world-list` are not run because they write into `data/worlds`). `present_map`'s integer codes are PER WORLD (`terrain_code_map`, `state_presenter.py:183`), so cells are
stored and drawn by terrain NAME, never by the integer. Every terrain name, building kind, place kind, resource-node kind and entity kind is mapped to a registered key by an
exact name rule (lower case, spaces to underscores, `terrain.<name>`, `icon.building.<kind>`, `icon.marker.<kind>`, `icon.class.<kind>`); a near key is listed and never applied.

## Two views, always named

- **Exact view (primary evidence)**: a terrain name draws when `terrain.<name>` is registered OR when the REGISTRY aliases it (`plain` and `PLAIN` to grassland, `ruin` to ruins, `river` to shallow water, since 2026-10-12; objects since 2026-10-14: building `shop` to store, place `CAMP` to enemy camp, place `RUIN` to ruins), resolved offline with `Registry.resolve`. **The live client does NOT resolve aliases** (registry-only; no release or runtime export carries them; a runtime consumer is needed at activation). A name with no key or alias is a plum, diagonal-striped gap cell; an object with no art is a checkered magenta and black marker. On rc-0011 every terrain name of the three worlds resolves (0 gap cells of 73,808) and every building, place and resource node draws (0 object gaps). A `CITY` place is the location plate alone (the owner's answer, 2026-10-13); resource nodes are their 16 x 16 `icon.node.<kind>` tiles; entities are counted, not drawn (the entity-marker batch).
- **Alias view (UNCONFIRMED: asset-planner proposal for rpg-planner, [#519](https://github.com/ttnhan18062000/rpg-based-simulation/issues/519))**: a name with no exact key draws with its proposed
  alias. **No proposal is left**: `shop`, `CAMP` and `RUIN` became registry aliases on 2026-10-14 (the exact view resolves them), so the alias view equals the exact view in all three worlds (same image
  hash) and only the exact crops are committed. The mechanism stays for a future proposal (`proposed_aliases` in the data).

Whenever a number or picture is quoted, it says which view it comes from.

## Commands (project venv; from the repository root)

```
python -m tools.visual_assets_sample_map data --all        # reports/visual_assets/sample_map/<world>/world_data.json (byte-identical on every run)
python -m tools.visual_assets_sample_map keytable          # the terrain name -> key table over the three worlds
python -m tools.visual_assets_sample_map render --all      # exact_x1/x2.png and alias_x1/x2.png per world, render_stats.json, and index.html (the page)
python -m tools.visual_assets_sample_map evidence          # the committed x1 crops below (docs/assets/sample_map/, at most 256 KiB in all)
python -m pytest tests/visual_assets/test_sample_map_data.py tests/visual_assets/test_sample_map_render.py -q
```

`render` exports the current release (rc-0011) once into `reports/visual_assets/sample_map/rc-0011-runtime/` with the store's own `export-runtime` and reads the PNGs with the store's decoder. Everything but the
crops in this folder goes to the gitignored `reports/visual_assets/sample_map/`. A full render takes about 20 s and 640 MB. Scale: 16 px per cell at x1 (x2 doubles it). Buildings are drawn from
their 24 x 24 icon scaled to one 16 x 16 cell by nearest neighbour; places are the `icon.plate.location` plate with their marker glyph; entities are counted in the data, not drawn.

## The border rule is a port, proven three ways

`frontend/src/visualAssets/terrainBorders.ts` (`borderOverlays`, `composeCell`, `rotate`), `pickDetail.ts` and the resolver order of `resolver.ts` are PORTED to Python; the TS is neither imported nor
edited. (1) The rule's own test vectors are ported one for one; (2) a drift test reads the TS text and asserts every ported constant equals it; (3) a differential test bundles the real TS rule with the
frontend's own esbuild and compares overlays on seeded random maps (skipped, with a reason, where node or esbuild is missing). Only terrains with a Live Map rank fringe, so the numbers of bordered cells on rc-0010 are 627, 433 and 138 (frontier, highland, dungeon) in both views, since the exact view now resolves the terrain names through the registry aliases (on rc-0009 the exact view had 264, none and none).

## The committed evidence (x1 crops, 237,953 B in all of the 262,144 B cap, evidence and not assets)

| file (`_exact_`; an `_alias_` crop only where it differs, none now) | world, cells (x0,y0)-(x1,y1) | shows |
|---|---|---|
| `frontier_town_*_x1.png` | `frontier_living_world`, (4,8)-(52,40) | Hometown: the town hall, shops, inn, blacksmith, healer hut and CITY plate scattered on one flat terrain: no town terrain, no structures |
| `frontier_camp_ruin_*_x1.png` | `frontier_living_world`, (108,26)-(148,52) | the goblin camp (CAMP place, berry thicket) and the haunted battlefield (RUIN place, `ruin` terrain) |
| `highland_pass_*_x1.png` | `highland_traverse`, (84,86)-(124,112) | the mountain pass: mountain and forest with fringes, an iron vein, a frost shard cluster and the highland buildings (`icon.node.*` and `icon.building.*` tiles) |
| `highland_river_*_x1.png` | `highland_traverse`, (124,26)-(172,58) | River Ford: `river` is one rectangle of one terrain name (no key) |
| `dungeon_ruin_*_x1.png` | `dungeon_crawl`, (60,80)-(98,112) | the ruin block (`ruin`, no key), its RUIN marker and the forest edge |

On rc-0011 the alias view equals the exact view, so no `_alias_` crop is committed. Three boxes were shrunk from the rc-0009 ones to stay under the cap now that the exact view draws terrain everywhere. Measured and unmeasured: the full-world sheets (59,603 to 231,054 B at x1) are not committed; the numbers of every full render are in the gap report. This is the picture of three worlds at one seed, not of
every world.
