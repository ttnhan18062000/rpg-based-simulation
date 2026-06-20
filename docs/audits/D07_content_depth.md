---
status: active
layer: simulation
authority: P1
audience: agent
tags: [audit, content-depth, variety, quests, factions, world-modules, archetypes, catalog]
---

# D07 — Content Depth & Variety

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | A — Simulation Quality |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 3 / 5 |
| **Priority** | 7 |
| **Method** | count |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Is there enough authored content to populate interesting
simulation runs across multiple sessions, scenarios, and entity types?

**Related dimensions:** D01 (RPG Feature Impact) — quests and faction relationships are
Tier-1 RPG systems flagged as partial/missing there; D16 (Authoring DX) — adding content
is workable (DX gap 7/15 for modules); D03 (Behavioral Emergence) — content depth directly
limits how varied emergent entity behavior can appear across runs.

---

## Count Method

All catalog entries in `data/content/` are enumerated by file. Content is grouped into
four layers. Each gap finding is scored by Content Gap Risk — how urgently thin content
in this category limits simulation quality.

### Content Gap Risk Scoring

3 dimensions, each 1–5. Maximum: 15. Higher = more urgent to fill.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Scenario Impact** | Thin content barely noticeable in a run | Limits variety across multiple sessions | Prevents an entire class of simulation scenario |
| **Entry Count** | 15+ entries — workable variety | 6–14 entries — some repetition | ≤ 5 entries — too thin to produce variety |
| **RPG Essential** | Supporting / optional content type | Active gameplay category | Core RPG mechanic per D01 Tier 1 or 2 |

---

## Catalog Snapshot

**Total catalog entries:** 430 across 35 YAML files in `data/content/`

_(Excludes procedurally generated compositions in `data/content/world_compositions/generated/`)_

### Layer 1 — Foundation (stable)

| Category | Count | Notes |
|---|---|---|
| Traits | 25 | Rich; entity personality foundation |
| Themes | 24 | Rich; world flavor taxonomy |
| Roles | 23 | Good variety |
| Materials | 17 | Workable |
| Attributes | 15 | Sufficient (fixed set by mechanics) |
| Relationship axes | 12 | Sufficient |
| Elements | 11 | Sufficient |

Foundation layer is well-populated and stable. No gaps here.

### Layer 2 — Entity

| Category | Count | Notes |
|---|---|---|
| Stat profiles | 23 | Good variety |
| Entity archetypes | 21 | Workable but skewed (see below) |
| Populations | 14 | Workable |
| Races | 13 | Sufficient |
| Combat profiles | 10 | Workable |
| Skill profiles | 10 | Workable |
| Inventory profiles | 10 | Workable |
| Body models | 8 | Thin; limits biological variety |
| Cognition profiles | 7 | Thin; limits AI behavioral variety |
| Drive profiles | 7 | Thin; limits motivational variety |
| Need profiles | 6 | Thin |
| Sense profiles | 6 | Thin |

### Layer 3 — World

| Category | Count | Notes |
|---|---|---|
| Items | 34 | Good for current scale |
| Runtime regions | 15 | Sufficient |
| Biomes | 13 | Good |
| Resources | 11 | Workable |
| Buildings | 9 | Workable |
| Ecologies | 9 | Workable |
| Terrain | 9 | Sufficient |
| Services | 8 | Workable |
| Recipes (crafting) | 8 | Thin — limits crafting system value |

### Layer 4 — Social & Scenario

| Category | Count | Notes |
|---|---|---|
| Factions | 16 | Good |
| Faction relationships | 14 | ⚠️ Thin relative to 16 factions |
| Perspectives | 6 | Thin — limits scenario setup variety |
| Simulation scenarios | 8 | ⚠️ Thin; mostly one world |
| World compositions | 5 | Thin |
| Quest definitions | 34 | ✅ Resolved — TCK-20260619-E13A-QUEST-DEFS |

### Module Layer

| Category | Count | Notes |
|---|---|---|
| World modules | 19 | ✅ All 7 type slots populated (TCK-20260619-E13B) |
| World compositions | 5 (+4 generated) | Thin for a simulation platform |

**Module type distribution:**

| Type | Count |
|---|---|
| conflict | 6 |
| ecology | 3 |
| danger_zone | 2 |
| settlement | 2 |
| economy | 1 |
| **terrain** | **2** ✅ |
| **population** | **2** ✅ |

---

## Key Findings

### F1 — Quest definitions critically thin (4 across 14 modules) — Gap Risk: 15 / 15 — **RESOLVED**

**Resolution:** TCK-20260619-E13A-QUEST-DEFS added 30 quest definitions across 10 modules (2026-06-20).
Total quest definitions: **34** across **13 of 15** world modules.

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 5 | Quests are the primary entity mission structure; 4 definitions means most entities have no quest-driven motivation |
| Entry Count | 5 | 4 entries — only 3 of 14 world modules define any quests |
| RPG Essential | 5 | Quests are the Tier-1 RPG system D01 rated highest (22/25) after Resource Ecology; without quests entities have goals only from strategic scoring, not narrative missions |
| **Total** | **15** | |

~~Only `forest_deep_ecology` (1), `old_mine_resource_loop` (1), and `ruins_mystery_quest` (2)
define quest content. The other 11 modules — including all 6 conflict modules — have no
quest definitions. Conflict without a quest objective produces pure combat loops with no
narrative structure.~~

**Post-resolution:** 13 of 15 modules now define quest content. All 6 conflict modules have
3 quests each. Settlement and ecology modules have 3 quests each. `hero_adventurers` and
`sunken_swamp_border` are the only modules still without quest definitions (E13B scope).

**Note:** D01 flagged "Quest & Objective Depth" as a Tier-1 gap (score 18/25). This count
confirms the underlying cause has been addressed.

---

### F2 — No terrain or population world module types — Gap Risk: 10 / 15 — **RESOLVED**

**Resolution:** TCK-20260619-E13B-MODULE-TYPES added 2 terrain modules (mountain_pass, river_crossing)
and 2 population modules (nomadic_herd, settled_quarter) on 2026-06-20.
Module type distribution now: terrain=2, population=2 (from 0/0).

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 4 | A world composed only of conflict/ecology/settlement modules lacks traversable terrain and distinct population distributions |
| Entry Count | 5 | 0 terrain modules, 0 population modules — type slots completely empty |
| RPG Essential | 1 | These module types are useful but not individually critical; their absence is felt collectively |
| **Total** | **10** | |

~~6 of 7 registered module types have at least one entry. `terrain` and `population` have zero.
This limits world variety: current compositions are conflict + ecology + settlement only.
A dungeon, mountain pass, or nomadic population module would each require a new type.~~

**Post-resolution:** All 7 registered module types have at least one entry. mountain_pass and
river_crossing cover altitude/traversal terrain. nomadic_herd covers migratory beast populations.
settled_quarter covers dense service-hub populations with crafting access.

---

### F3 — Crafting recipes thin (8 entries) — Gap Risk: 10 / 15

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 3 | Crafting system is live (D09 confirmed) but 8 recipes limits economic loop variety |
| Entry Count | 4 | 8 recipes for 34 items and 11 resources — most item types have no recipe |
| RPG Essential | 3 | Crafting is a Tier-2 RPG mechanic; thin recipes mean the economy loop has little to converge on |
| **Total** | **10** | |

34 items exist in the catalog but only 8 crafting recipes. Most items have no production
path — they can only be acquired via loot or trade, not crafted. This limits the economic
loop: entities cannot pursue "gather resources → craft gear → upgrade" progression chains.

---

### F4 — Entity archetype distribution skewed — Gap Risk: 9 / 15

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 3 | 4 scout archetypes and only 1 each of most other roles means encounters repeat quickly |
| Entry Count | 3 | 21 entries is workable but 4/21 are the same role (scout) |
| RPG Essential | 3 | Archetype variety determines how distinct faction and biome encounters feel |
| **Total** | **9** | |

21 entity archetypes exist, but the distribution is unbalanced: 4 scouts, 2 raiders,
2 leaders, then 1 each for 13 other roles. In practice a settlement encounter pulls from
mostly scout-type entities. No dedicated mage/caster role has more than 1 entry.

---

### F5 — Simulation scenarios thin and frontier-concentrated — **RESOLVED: 14 total, all 3 target compositions covered** — Gap Risk: 9 / 15

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 4 | 6 of 8 scenarios use `frontier_living_world`; the simulation is effectively a single world with 6 starting conditions |
| Entry Count | 3 | 8 scenarios is low for a "simulation platform" pitch |
| RPG Essential | 2 | Scenarios are configuration, not narrative content; but they define the entry points |
| **Total** | **9** | |

**RESOLVED (TCK-20260619-E13D-SCENARIOS, 2026-06-20):** 6 new scenarios authored across
`dungeon_crawl` (2), `urban_political` (2), and `wilderness_survival` (2). Total: 14 scenarios
across 4 world compositions. All three previously zero-scenario compositions now have ≥2 scenarios.

~~8 scenarios exist in one file. 6 reference `frontier_living_world`, 2 reference
`frontier_extended`. No scenarios exist for `dungeon_crawl`, `urban_political`, or
`wilderness_survival` — three of the five named world compositions have zero scenarios.~~

---

### F6 — Faction relationships incomplete for faction count — Gap Risk: 8 / 15

| Dimension | Score | Reason |
|---|---|---|
| Scenario Impact | 3 | 16 factions but only 14 explicit relationships means many faction pairs interact with default/null stance |
| Entry Count | 3 | 14 relationships for 16 factions (120 directed pairs possible) — very sparse |
| RPG Essential | 2 | Faction AI uses relationships for alliance/hostility; missing relationships produce neutral default behavior |
| **Total** | **8** | |

14 faction relationships are defined for 16 factions. 120 directed faction pairs are
theoretically possible; only 14 are explicitly modeled. Factions without relationships
default to neutral posture, reducing faction conflict variety.

---

### Gap Risk Summary

| Finding | Description | Gap Risk |
|---|---|---|
| F1 | Quest definitions critically thin (4 total) — **RESOLVED: 34 total** | **15 / 15** |
| F2 | No terrain or population module types — **RESOLVED: terrain=2, population=2** | **10 / 15** |
| F3 | Crafting recipes thin (8 for 34 items) — **RESOLVED: 25 recipes, full chain** | **10 / 15** |
| F4 | Entity archetype distribution skewed | **9 / 15** |
| F5 | Scenarios frontier-concentrated — **RESOLVED: 14 scenarios, all compositions covered** | **9 / 15** |
| F6 | Faction relationships sparse (14 for 16 factions) | **8 / 15** |

---

## Content Strengths

These content categories are well-populated relative to current simulation scale:

| Category | Count | Assessment |
|---|---|---|
| Traits | 25 | Rich personality foundation |
| Items | 34 | Adequate for current economy scope |
| Factions | 16 | Good faction variety |
| Entity archetypes | 21 | Workable; needs distribution fix more than count increase |
| Biomes | 13 | Good territorial variety |
| Foundation layer | 90+ | Mature and stable |

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| **P0** | Author 15–20 quest definitions distributed across conflict and settlement modules | F1 — direct prerequisite for narrative simulation runs |
| **P1** | Add 2–3 terrain world modules (mountain pass, dungeon entrance, river crossing) | F2 |
| **P1** | Add scenarios for `dungeon_crawl`, `urban_political`, `wilderness_survival` | F5 |
| **P1** | Expand crafting recipes: at minimum 1 recipe per item tier (target 20+ recipes) | F3 |
| P2 | Add 6–8 more entity archetypes weighted toward underrepresented roles (mage, healer, leader variants) | F4 |
| P2 | Define faction relationships for at least 50% of cross-faction pairs (30+ entries) | F6 |
| P2 | Add 1–2 population world modules (nomadic tribe, merchant caravan) | F2 |

---

## Related Dimensions

- **D01 (RPG Feature Impact)** — Quest Depth scored 18/25 (Tier 1 partial); F1 resolved by TCK-20260619-E13A-QUEST-DEFS (34 quest definitions now in catalog). Resource Ecology Regeneration (top D01 gap, 22/25) also has no authored content — no resource regeneration cycle modules.
- **D16 (Authoring DX)** — Adding new modules is workable (DX gap 7/15); the bottleneck is not the authoring tooling but the time investment to write quest-rich modules.
- **D03 (Behavioral Emergence Quality)** — Content depth directly caps behavioral variety. With only 4 quests, entities cannot exhibit quest-driven narrative arcs. This dimension cannot be fully audited until F1 is addressed.
