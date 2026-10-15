---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation: map markers, key design note (points 1-7) and budget evidence

Gate: asset-planner reads this before ANY registry edit. No registry file, bound, store code, `src/` or `frontend/` file was changed by this ticket's work so far. Measurements: `docs/assets/budgets.md` section "Registry re-measurement for the map-markers batch (2026-10-13)". Scratch script: a temp-dir generator run against the real `load_registry`; the committed registry was not touched.

## 0. Findings that need the owner or the planner first

1. **Option (b) for resource nodes does not work as the ticket words it, and cannot be done without a client contract change.** `frontend/src/visualAssets/pickDetail.ts` picks a declared value as `values[fnv1a32(key|x|y|seed) % values.length]`: it is a pure function of the CELL, not of the node's kind. An axis with one value per node kind would draw a random kind's art on every node. To select by kind the client needs a different selection rule (a pick contract version 2, `PICK_CONTRACT_VERSION`) or an axis whose value is chosen by the caller. That is a store/client contract change: **STOP, owner question, not part of this batch.** (a) and (c) need no code change.
2. **No store-code change is needed for (a) or (c), for any family prefix I propose.** The real `load_registry` (default namespace, no fixture flag) loaded a scratch registry holding `icon.building.*`, `icon.marker.*`, `icon.node.*` and `icon.unit.*` keys: only the `icon` family rules apply (`registry.py:30-52`: a non-decorative icon needs `label_key == "label." + key` and a `label`).
3. **No bound is exceeded.** Every shape sits at about 9 to 10 % of `MAX_REGISTRY_BYTES`, loads in about 0.1 s against the 2 s line, uses under 10 % of `MAX_VISUAL_KEYS` and under 1 % of `MAX_ALIASES` (table below).
4. **A key is about 543 B, not 450 B** (the real shape with `label_key`, `label` and a structured fallback: 30 new keys and 5 aliases added 16,288 B). The 450 B in budgets.md was the older shape. Still far from the bound.

## 1. Names (key = family prefix + lowercase of the kind name as the presenter emits it)

Sources, read only. Place kinds: `src/core/state.py:344-352` (`PlaceKind`: CITY, CAMP, NEST, LAIR, RUIN, DUNGEON, LANDMARK; the data uses upper case). Building kinds: `src/api/presenters/state_presenter.py:261` (`"building_type": b.kind`; the values are authored in `world.resolved.yaml` `buildings:`). Resource-node kinds: `state_presenter.py:270` (`"resource_type": n.kind`). Entity kind: `state_presenter.py:69` and `:173` (`"kind": entity.kind`).

Counts over ALL 24 worlds under `data/worlds/*/resolved/world.resolved.yaml` (a grep of the authored data, not a compile; the sample map counts only 3 worlds):

| family | kinds (count of occurrences over all worlds) | exact key today | proposed key |
|---|---|---|---|
| building | shop 24, inn 24, healer_hut 21, blacksmith 20, town_hall 19, mine_entrance 7, watchtower 4 | `icon.building.inn`, `icon.building.blacksmith` | NEW `icon.building.healer_hut`, `town_hall`, `mine_entrance`, `watchtower` (4); `shop` -> alias to `icon.building.store` |
| place | CITY 20, CAMP 11, NEST 10, RUIN 9, LAIR 2 (DUNGEON, LANDMARK not in authored data, `PlaceKind` has them) | none exact (existing `icon.marker.*`: enemy_camp, ruins, dungeon_entrance, shrine, boss_arena, resource_grove) | NEW `icon.marker.nest`; CITY: owner's choice; aliases below |
| resource node | cover_patch_high 122, wood_node 38, herb_patch 35, berry_thicket 25, iron_vein 22, healing_flower_patch 11, crystal_outcrop 9, cover_patch_medium 8, spirit_wisp 7, silver_vein 7, cover_patch_low 6, frost_shard_cluster 4, moon_resin_tree 2 | none (`icon.marker.resource_grove` exists, nothing maps to it) | 13 kinds; see section 4 |
| entity | the samples hold 10 kinds (alpha, blacksmith, guard, leader, merchant, predator_hunter, raider, scout, sentinel, worker); the planner's count is 11 | `icon.class.*` holds warrior, ranger, mage, rogue only (24x24 panel class icons: a different thing from a kind) | see section 5 |

(The list is every `resource_type:` occurrence in the resolved worlds: 13 distinct kinds, three of them `cover_patch_*` per #543.)

Key names follow the V2 names (#523), lower case, snake case: `icon.<family>.<kind>`.

## 2. Families and sizes

- Place glyph: 16x16, live 12x12, drawn over the shared location plate (`icon_style_guide.md` sizes table; the existing six `icon.marker.*` keys). Fits an existing family.
- Building: 24x24 panel icon (live 20x20), the existing `icon.building.*` family. On a 16 px map cell a 24x24 icon is drawn scaled down or only on the panel; today the client draws a lettered square per building on the cell (`useCanvas.ts:157-175`, `bLabels[b.building_type]`). **Decision for the owner/planner: do buildings need a 16x16 map glyph?** The style guide sizes call the 24x24 a panel icon; a map cell is 16 px. If the map must show the art, a building needs a second 16x16 key (a `icon.marker.<building>`-style key) or the client scales 24 -> 16 (not a whole-number scale, which D20 forbids: "Map zoom: whole-number scales only"). I recommend: draw the 4 missing building icons at 24x24 like the 5 existing ones (panel use) and raise the map-glyph question to the owner as a separate, later choice, not in this batch.
- Resource node: today an inset square of the `RESOURCE_COLORS` fill (`useCanvas.ts:179-190`). A node is a map object on a 16 px cell: a 16x16 glyph with a 12x12 live area, **no plate** (it is not a location). It fits the `icon` family; a new key prefix `icon.node.*` keeps it apart from `icon.marker.*` (locations over a plate). No schema field and no store code is needed for a prefix.
- Entity: today a coloured circle per entity (`useCanvas.ts:255-300`, `ctx.arc`). 16x16 glyph, live 12x12, no plate, prefix `icon.unit.*`. (`icon.class.*` stays the panel class icons.)

## 3. Aliases (registry-only, Known gap: no runtime consumer; each is the owner's choice)

| alias | target | status |
|---|---|---|
| `icon.building.shop` | `icon.building.store` | the sample-map proposal (#519); owner's choice (a coin purse reads as a shop; alternative: a new key) |
| `icon.marker.camp` | `icon.marker.enemy_camp` | owner's choice (a camp may not be hostile) |
| `icon.marker.ruin` | `icon.marker.ruins` | near-certain: same name, singular |
| `icon.marker.dungeon` | `icon.marker.dungeon_entrance` | rpg's suggestion with a question mark |
| `icon.marker.lair` | `icon.marker.boss_arena` | rpg's suggestion with a question mark; a lair is not a boss arena |
| CITY | `icon.plate.location` alone, or a new `icon.marker.city` glyph | owner's choice (20 occurrences, the most common place) |

Aliases used: 5 to 6 of `MAX_ALIASES` 1024. A key that is an alias is not drawn by the live client (it does not resolve aliases, #523).

## 4. Resource nodes: the owner's options (13 kinds over all worlds)

| option | keys | bytes added (measured, real loader) | tiles | notes |
|---|---|---|---|---|
| (a) one key per kind | 13 `icon.node.<kind>` | registry 47,231 B with the 11 role keys (below) | 13 | recognisable per kind; the three `cover_patch_*` kinds (#543) can share one key via aliases, giving 11 keys and 11 tiles |
| (b) one key with a detail axis, one value per kind | 1 key + a 13-value axis | not measured (not buildable) | 13 | **not possible with `pickDetail` (finding 1)**: the pick is per cell. Needs a pick-contract change: STOP |
| (c) grouped by material | 5 `icon.node.{plant,ore,crystal,spirit,cover}` + 13 aliases | registry 42,493 B with the 11 role keys (4,738 B less than (a)), plus 13 alias lines (about 60 B each, not measured) | 5 | loses the kind (iron vs silver, herb vs berry, wood); the kind would be a hover text only |

## 5. Entities: the owner's options (child 3, after rpg's answer on #548)

| option | keys | bytes added | tiles | needs from rpg |
|---|---|---|---|---|
| role markers | 11 `icon.unit.<kind>` | registry 47,231 B (with option (a) nodes) | 11 | nothing new, but they follow V2 names that M1 may rename (#523, #548) |
| property markers (diet, size) | about 5 | registry 44,087 B (with option (a) nodes; 3,144 B less than roles) | 5 | the entity's diet and size as presented fields: the presenter has no `diet` or `size` field today (`state_presenter.py`, a search for both finds none) |

## 6. `safety_class` and `fallback` (per `fallback_safety.md`)

Every new key: `safety_class: identifying` (the image says what the object is); fallback structured `glyph_and_text`, equal to what the client draws today, so a missing art loses nothing: buildings: the lettered square plus the building name as text (`useCanvas.ts:163-175`); resource nodes: the inset square in `RESOURCE_COLORS[kind]` plus the node name as hover text (`useCanvas.ts:179-190`, `constants/colors.ts:122`); entities: the coloured circle plus the kind as text (`useCanvas.ts:255-300`, `ctx.arc`); places: the emoji label plus the location name as hover text (`GameCanvas.tsx:77-84`). None is `critical`: no marker alone carries a fact whose loss misleads play. The exact fallback glyph texts for each kind are fixed in child 2's key edit, not here.

## 7. Existing tests that pin counts and will go red when the registry gains keys (known red until rc-0011, as in the terrain batch)

- `tests/visual_assets/store/unit/test_registry.py:294` (`len(keys) == 65`) and the registry-content pins in the same file.
- `tests/visual_assets/test_key_usage.py:109,125` (`registry_keys == 65`).
- Every test that exports or compares the CURRENT release candidate by its registry hash: `test_release_byte_reproducibility.py` (`RELEASE_ID = "rc-0010"`), `store/unit/test_atlas.py:191` (87 entries), `test_sample_map_render.py`, `test_rc_0010_extends_rc_0009.py` (it reads rc-0010 and rc-0009), and the `adopted_facts.py` pins (`TERRAIN_VARIANT_AXES`, `RC_0010_*`). They fail with `registry_mismatch` on an export of rc-0010 once the registry gains keys (a registry edit makes every older candidate unexportable, `store_contract.md` Known gaps).
- The proof record (`registry hash` pins): refresh after the guarded change.
Exact list is confirmed by running `tests/visual_assets` after the key edit, as in `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES` (16 red then); expect the same families.

## 8. Questions for the owner, taken from this note

1. Resource nodes: (a) 13 keys, (a') 11 keys with the 3 cover_patch kinds sharing one, or (c) 5 grouped keys. (b) is not available without a client contract change; ask only if the owner wants it.
2. Buildings: are the 4 missing icons 24x24 panel icons only, or does the map need a 16x16 glyph per building?
3. Aliases: `shop`, `camp`, `lair`, `dungeon` (rpg's ?), and CITY: alias, new glyph or plate alone.
4. Entities (later): roles (11) or properties (about 5), after #548.
