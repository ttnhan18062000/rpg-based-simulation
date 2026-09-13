# Preliminary Visual-System Planning for RPG Content

Status: investigation snapshot  
Scope: structural planning between the content taxonomy and a future art specification  
Art direction status: **PRELIMINARY — no palette, resolution, style, or asset count is approved here**  
Companion: `docs/brainstorm/codex/taxonomy/content-taxonomy.md`

## Evidence and decision language

This document uses four evidence labels:

- **Repository fact** — directly supported by checked-out code, data, or implemented documentation.
- **Planning fact** — stated by an active or approved plan, but not necessarily implemented.
- **Brainstorm direction** — proposed in non-authoritative design material.
- **Analysis inference** — a recommendation or hypothesis derived from those sources.

Candidate counts and sizes are experiment ranges, not production commitments. “Visual identity” means an
independently recognizable representation, not necessarily one unique source image. A composed sprite can
provide a distinct visual identity while reusing a body, role cue, equipment layer, and overlay.

## 1. Executive Summary

**Repository fact.** The current player-facing map is a 2D canvas with a 16-pixel cell constant. It draws
terrain as flat rectangles, heroes as diamonds, other entities as circles, buildings as lettered squares,
resource nodes as inset squares, and ground loot as diamonds. It also draws HP bars, selection/hover rings,
combat-target lines, range/vision boundaries, fog, remembered-entity ghosts, and a minimap. No character,
item, building, or skill sprite is loaded. The only canvas `drawImage()` use is an off-screen minimap cache.
The repository has no production PNG/SVG asset set in `frontend/src` or `frontend/public`; Lucide supplies
React UI icons, while `src/rendering/` produces deterministic flat-color QA images.
The inspector and contextual panels already use text, badges, progress bars, color tables, and Lucide
symbols, but their optional `/api/v1/metadata/*` source is not implemented; they fall back to empty metadata.

**Analysis inference.** The likely art workload is therefore not environment illustration. It is a compact
information system with six major families: assembled entity sprites; inventory/equipment icons; skill,
class, and progression icons; world-object markers; condition/effect feedback; and reusable UI symbols.
The expensive families are entity archetypes, an eventual 20–40-skill roster, 50–80 possible items, and
unstable effect/Place systems. Quest blueprints, relation edges, generated people, cooldowns, numeric stats,
and world-event instances can become numerous but are visually cheap because they should reuse symbols,
existing subjects, text, and meters.

The highest risks are trying to distinguish too many concepts through hue, treating every content ID or
runtime instance as a unique asset, and freezing sprites before status, Place, equipment, and skill schemas
stabilize. The next step is a small set of native-scale experiments: silhouettes, grayscale item icons,
worst-case skill families, semantic-channel overload, compositional character reuse, and crowded combat
screens. Those experiments should precede a final art specification.

## 2. Visual Representation Boundary

### Unique visual identity

A unique visual identity is warranted when confusing an identity with its nearest neighbor would change a
player decision at the point where it is seen.

Likely candidates are:

- a combat-relevant entity archetype or assembled archetype look;
- an inventory item whose function, value, or equipment choice matters;
- an executable skill or planned executable skill;
- each class and breakthrough in build/progression UI;
- a reusable building or resource-node type on the map;
- a high-priority objective/interactable family;
- a faction emblem when affiliation is the subject of a decision.

“Unique” does not mean “painted from scratch.” `goblin_scout` and `goblin_archer` may be independently
recognizable compositions made from one goblin body family plus different role/equipment cues.

### Visual family identity

Visual families share a stable construction grammar. Strong candidates are:

- race/body-plan families, with archetype-specific role and equipment cues;
- humanoid melee, ranged, caster, worker, and leadership cues;
- weapon shapes, even though no authoritative `WeaponFamily` enum exists;
- material/node families such as ore, plant, organic trophy, crystal, and essence;
- physical, magical, elemental, passive, and utility skill grammars;
- service-bearing building families;
- wound/impairment, beneficial, harmful, and elemental effect families, pending gameplay design.

Family names in this document are visual hypotheses, not new gameplay enums.

### Semantic representation

The following should normally be encoded with reusable badges, borders, markers, meters, overlays, or
symbols rather than identity-specific art:

- item rarity and equipment slot;
- quest type, objective kind, completion, and target location;
- element or damage accent;
- cooldown, stamina cost, charges, durability, progress, and severity;
- selection, hover, visibility, memory, and target relationship;
- faction/diplomatic state where exact faction identity is already shown elsewhere;
- resource availability/depletion and building damage/availability;
- buff/debuff polarity and remaining duration once an effect model exists.

### No dedicated visual identity

These should use text, numbers, a meter, an existing subject representation, or no direct rendering:

- generated entity, wound, scar, contract, quest, event, stack, or relation IDs;
- numeric stats and derived multipliers;
- levels, XP/AP quantities, cooldown values, effect stacks, and duration values;
- 75 current faction-relation records and future pairwise race relations;
- recipe ingredient quantities and service parameters;
- quest-blueprint parameters and generated objective instances;
- profile IDs, module IDs, compatibility aliases, and simulation seeds.

## 3. Visual Identity Taxonomy

```text
Visual Content
├── World-space representation
│   ├── Terrain/tile families
│   ├── Entity compositions
│   │   ├── body/race or creature base
│   │   ├── role/combat-delivery cue
│   │   ├── equipped-item cue where readable
│   │   └── selection, faction, threat, health, state overlays
│   ├── Buildings and service locations
│   ├── Resource nodes and availability states
│   ├── Ground loot, chests, corpses, camps, and local scars
│   └── Objectives, hazards, and interactables
├── Inventory and equipment representation
│   ├── Weapons
│   ├── Armor and shields
│   ├── Trinkets
│   ├── Consumables
│   ├── Tools
│   └── Materials
├── Ability and progression representation
│   ├── Executable skills
│   ├── Profile-only/unresolved skill labels
│   ├── Classes
│   ├── Breakthroughs
│   └── Passive capability markers
├── Conditions and feedback
│   ├── Wounds
│   ├── Scars
│   ├── Passive effects
│   ├── Temporary beneficial/harmful effects
│   ├── Elemental states
│   └── action, impact, transition, and objective feedback
├── Semantic UI symbols
│   ├── quest and objective families
│   ├── slots, rarity, elements, and damage
│   ├── faction/diplomacy/relationship state
│   ├── routes, events, services, and availability
│   └── visibility, selection, warning, progress, and history
└── Text/numeric-only state
    ├── runtime IDs and provenance
    ├── quantities, durations, cooldowns, and stats
    ├── relation axes and generated records
    └── authoring/profile/module metadata
```

## 4. Visual Cardinality Table

Ranges below are capacity hypotheses, not asset orders. “Estimated Visual Identity Count” always means the
number of independently recognizable outcomes needed at that category level. Reusable body templates,
cues, overlays, and channels are described separately and must not be summed with that number. A composed
look can be one visual identity while reusing several source components.

| Content Category | Current Content Count | Expected Content Count | Estimated Visual Identity Count | Representation Type | Reuse Potential | Information Density | Confidence | Notes |
|---|---:|---:|---:|---|---|---|---|---|
| Entity archetypes | 29 | 40–60 | 29 now; capacity for 40–60 | World sprite composition | High | High | Medium | Each ID may need a recognizable assembled outcome in identity-sensitive views; shared body/role/gear components prevent 29 unique complete assets. Tactical map views may collapse noncritical neighbors with text fallback. |
| Race/species | 13 | 13–20 | 8–15 body/silhouette families | Sprite base/family | High | High | Medium | Eight body models already support reuse; not every race needs a wholly separate construction method. |
| Roles | 23 | 25–35 | 8–14 visible role cues | Equipment/pose/accessory cue | Very high | Medium | Low | Many roles matter in inspector text more than at map scale. |
| Classes | 4 engine definitions | 4–10 | 4 now; capacity for 10 | UI emblem + optional sprite cue | Medium | High | Medium | Engine: NOVICE, WARRIOR, MAGE, ROGUE. The current Class Hall instead hard-codes warrior/ranger/mage/rogue UI keys and depends on missing metadata routes; resolve this boundary before art. |
| Items, total | 36 | 36 floor; 50–80 expansion scenario | 25–50 icons | Inventory/equipment icons | Medium–high | High | Medium | Named functional items deserve distinction; common materials can share grammar. Subtype projections below are independent conditional scenarios and are not additive bounds inside the 50–80 total. |
| Weapons | 10 | 15–30 | 10 now; 15–30 if roster expands | Icon + optional equipped cue | Medium | High | High current | No formal weapon-family schema; use sword/staff/bow/axe/dagger only as experiment groupings. |
| Armor/shields | 2 | 8–20 conditional | 2–12 | Icon + optional body overlay | Medium | High | Low future | Five slots exist, but only torso/main-hand/off-hand are populated by catalog mappings. |
| Trinkets, consumables, tools | 2 + 2 + 2 | 4–12 / 8–20 / 4–12, independent conditional projections | 6–25 | Icons | Medium | Medium–high | Low future | The three subtype maxima are not a simultaneous item-roster commitment. Runtime kinds for tools/trinkets are not stable enough to lock their grammar. |
| Materials | 18 | 20–35 | 12–25 | Icon families | High | Medium | Medium | Ore/plant/organic/crystal/essence groupings can share construction without sharing exact identity. |
| Executable skills | 4 | 20–40 conditional | 4 current; capacity for 20–40 | Distinct ability icon | Medium | Very high | Low future | Only one of 16 profile labels exactly matches an executable definition. |
| Skill-profile labels | 16 | 20–40 | 16 test identities, not 16 production assets yet | Stress-test labels/text until resolved | High | Very high | High current / low authority | `firebolt` and `fireball` demonstrate an identity-resolution hazard. |
| Breakthroughs | 3 | 5–15 | 3 now; test capacity for 5–15 | Distinct progression icons | Medium | High | Medium current / low future | Iron Will, Fleet Foot, Titan Grip have distinct effects and IDs. The richer Class Hall breakthrough shape is not the same registry. |
| Wounds/scars/status-like state | 3 generated wound kinds; 0 unified definitions | Wounds 3–5; unified roster unknown | 1–3 current coarse identities; future unknown | Badge/overlay + UI detail | Very high | High | Low | Do not produce a finalized condition icon set before the schema converges. Reserved channels are a system concern, not additional identities. |
| Terrain | 10 catalog definitions; 23 frontend numeric colors | 10–20 | 10–20 tile identities | Tile/fill family | High | Medium | Medium | Backend string terrain and frontend numeric codes are a representation boundary; 23 current colors do not prove 23 catalog identities. |
| Biomes | 13 | 15–30 | 5–12 compositions | Terrain mix, accents, labels | Very high | Low–medium | Medium | A biome does not automatically need its own tile sheet. |
| Regions | 20 | 20–40, then migration | 0 dedicated art identities; 20 text/marker identities | Text + generic map marker | Very high | Low | Medium current / low future | Named region identity normally survives through label/location, not unique terrain art. Do not reuse the separate Place projection here. |
| Buildings | 9 catalog; fewer live frontend marker keys | 12–25 | 6–15 | World object + service symbol | Medium–high | High | Medium | Current markers are letters/colors; building and service identity should remain separable. |
| Services | 8 | 10–20 | 8–12 symbols | UI/map semantic icon | Very high | Medium | Medium | One service symbol can appear on several buildings. |
| Resource nodes | 12 catalog | 15–30 | 8–20 | World object family + state | High | High | Medium | Node and yielded material should be related but not visually identical. |
| Ground loot/chest/corpse/camp/local scar | 5 runtime schema families | Runtime-scaled | 5–10 reusable types | World object/marker | Very high | High | Medium | Instances reuse type art; quantities and provenance stay textual. |
| Quest blueprints | 40 | 50–80 | 6–10 quest-family symbols | Icon + text + marker | Very high | Medium | High | Never create one icon per blueprint by default; target-object symbols belong to their own content families. |
| Objective kinds | 14 | 15–25 | 8–16 shared glyphs | Semantic icon/marker | High | High | Medium | Exact glyph count should follow player-visible distinctions, not enum count. |
| Adventure route families | 16 | 16–25 | 4–10 symbols | Text + small icon/line style | Very high | Medium | Low | Many route choices may be best distinguished by labels and destination. |
| World-event categories | 28 | 35–50 | 8–14 family symbols | Event-log icon + severity treatment | Very high | Medium | Medium | Event identity comes from subject, verb, time, and place—not unique artwork. |
| Factions | 16 | 16–30 | 8–16 emblems initially; capacity for 30 | Emblem, banner, accent | Medium | Medium–high | Low | Whether every faction is player-facing at once is not yet established. |
| Relation/diplomatic records | 75 directed records; 6 diplomatic states | 75 current / 240 structural ceiling; sparse expected | 3–6 state glyphs | Text, line, badge | Very high | Low | High current / low expected | No edge-specific art. Direction and state are data. |
| Planned Places | 0 implemented; 7 proposed kinds | 20–50 authored/migrated plus runtime | 7–20 kind/selected-landmark identities | Marker/world-object family | High | High | Low | Footprint, scale, ownership, maturity, and transformation are unresolved. |

## 5. Visual Cost Drivers

Ranked from highest likely production/system risk:

1. **Skill distinguishability.** A possible 20–40 executable roster combines abstract verbs, delivery
   shapes, elements, targets, passive/active state, cooldown, and rank in tiny UI footprints.
2. **Entity composition.** Forty to sixty archetypes are manageable only if body plan, role, equipment,
   faction, tier, and temporary state do not multiply into unique complete sprites.
3. **Item/equipment breadth.** Similar swords, staves, crystals, and trinkets need useful distinctions in
   both inventory and possible world/equipped contexts.
4. **Condition/effect instability.** The schema is fragmented; producing icons now risks rework or a visual
   grammar that cannot support the eventual model.
5. **Semantic-channel competition.** Current color tables already encode terrain, entity kind, behavior,
   resources, buildings, rarity, class, damage, and UI state. More color meanings will collide.
6. **Place and world-object evolution.** Planned persistent Places may change ownership, kind, maturity,
   hazard, activity, and footprint without changing identity.
7. **Crowded one-cell readability.** HP, selection, faction, target, condition, objective, memory, and
   equipment cues cannot all be painted directly on one 16-pixel cell.

Visually cheap despite high data cardinality: generated people using archetype compositions; 40–80 quest
blueprints using type/target grammar; 75–240 relation edges using badges and text; histories, goals,
contracts, and events using subject icons and prose; numeric progression using meters and numbers.

## 6. Silhouette Requirements

| Category | Silhouette criticality | Identities/coexistence pressure | Similarity pressure | Silhouette may communicate | Do not force into silhouette |
|---|---|---|---|---|---|
| Player/focused unit | Critical | One focus among many nearby occupants | High in same-race crowds | player/focus and living unit | class rank, faction history, numeric build |
| Entity body/race family | High | Up to dozens of entities; 8 body models and 13 races currently | High among humanoids; lower across body plans | humanoid, quadruped, spider, large body, spirit, flying | every race ID if another cue suffices; cognition, drives, stats |
| Entity archetype/role | High only for immediate tactical roles | Several same-family actors may share nearby tiles | Very high for goblin/human variants | melee/front line, ranged, caster, worker/interactor, leader/boss | exact occupation, class, faction, every equipped item |
| Weapons/equipment | High for dominant weapon family; medium otherwise | One held cue per entity; many icons in inventory | High for swords/staves and small trinkets | melee/ranged/caster, shielded, tool-bearing | rarity, exact material, durability, numeric bonuses |
| Resource nodes | High | Several node types may occur in one region | High for veins/clusters and plants | harvestable object family and gross form | charges, exact yield quantity, rarity |
| Loot/chest/corpse | Critical at object-family level | Several object families may share a tile neighborhood | High because loot and hero currently share diamond geometry | dropped item stack, container, dead body | exact contents, provenance, generated ID |
| Interactable/objective | High at affordance level | Multiple candidates/markers can coexist | High when the objective is an existing building/node/entity | “can interact” and “current objective target” as external shapes | replace the subject's own identity; full quest type/parameters |
| Buildings/entrances | Medium–high | A town can show several service buildings | High for mine/dungeon/cave entrances | structure/entrance/service family where possible | ownership, HP, service availability, Place history |
| Conditions/effects | Low for base silhouette; high for a few urgent external overlays | Several can coexist on one entity | High under one-cell limits | incapacitated/critical only through an added marker or pose | wound type, stacks, duration, passive roster |

Mandatory cross-category tests remain: living versus corpse or remembered entity; ordinary versus
leader/boss; entity versus node, loot, building, hazard, and objective; and available versus depleted or
inactive interactable without hue alone.

**Repository fact.** The live canvas has partial primitive-category separation: ordinary entities are
circles; buildings and resources are square treatments. Hero and loot are both diamonds and are separated
by size, glow/context, ID/HP treatment, and draw behavior—not by silhouette alone. No objective diamond is
currently drawn. **Analysis inference.** Replacement art must improve this overlap rather than merely
preserve the primitive shapes; an external objective marker must not converge with either hero or loot.

## 7. Shape-Language Hypotheses

These are experiment hypotheses, not a style guide:

- **Body plan first:** use the outer mass to communicate humanoid, quadruped, many-legged, spectral,
  large-bodied, or flying before color and detail.
- **Combat delivery second:** held/extended horizontal or diagonal forms can suggest melee reach; a bow-like
  open arc can suggest ranged; a staff/focus/raised-hand mass can suggest casting.
- **Authority through mass placement:** leaders/bosses can test broader shoulders, taller headgear, larger
  upper mass, or a separate underlay—not simply brighter color.
- **Objects by interaction verb:** containers closed around a center, resources growing/projecting from the
  ground, entrances framing negative space, objectives using an external marker rather than changing the
  object itself.
- **Items by dominant contour:** weapon/tool category should read in monochrome before elemental, rarity,
  or material decoration is applied.
- **Abstract skills by action geometry:** strike, projectile, area, guard, movement, tracking, trade, and
  crafting can each test a recurring compositional grammar while retaining distinct central motifs.

| Repository semantic | Candidate shape-language responsibility to test |
|---|---|
| Offensive/strike/projectile | Direction, outward force, impact, or an open attack path |
| Defensive/guard/shield | Enclosure, interruption, bracing, or stable mass |
| Mobility/route/explore | Orientation, path, displacement, or an intentionally open destination |
| Support/trade/crafting | Connection, exchange, assembly, or subject-plus-tool relationship |
| Healing/restoration | Repair, replenishment, or protected recovery rather than generic “beneficial color” |
| Control/incapacitation | Blocked motion, interruption, containment, or broken continuity; capacity-only until statuses stabilize |
| Physical/magical/elemental | Weight/contact versus emanation/field versus a scoped modifier; exact grammar requires tests |
| Dangerous/friendly | Threat direction/instability versus nonthreatening stability; relationship must retain a non-shape label |
| Interactable | A clear affordance frame or approach point around the underlying subject |
| Resource | Grounded/growing/extractable mass tied to a node family, not a generic objective symbol |
| Objective | An external focus/destination structure that preserves the target's own identity |
| Environmental/background | Broad, low-frequency masses and texture, subordinate to occupants and interaction state |

Do not treat these groupings as new mechanics. Their purpose is to make families learnable and cheaper.

## 8. Visual Channels

Available channels include outer and internal shape, orientation, scale, value/contrast, hue/saturation,
frame, overlay, emblem, texture, motion/timing, screen-space effect, UI placement, line/arrow, meter, and
text. The working rule is one semantic dimension per primary channel within a view. A channel may be reused
in another view only when the meanings cannot collide there.

| Gameplay dimension | Candidate primary channel | Secondary channel | New base art? | Notes |
|---|---|---|---|---|
| Body/object family | Outer silhouette/mass | Internal shape | Yes, at family-template level | Humanoid, beast, building, node, loot, and corpse are the load-bearing split. |
| Exact entity archetype | Composed landmark/motif | Name on focus | Composed outcome, not unique complete source art | Reuse body, role, gear, and accent components. |
| Race/species | Body-plan silhouette where meaningful | Local body detail | Sometimes a family base | Do not force 13 unrelated silhouettes if body models legitimately overlap. |
| Role/combat delivery | Held/attached shape and orientation | Pose or inspector label | Usually an overlay/component | Bow, shield, staff, tool; exact occupation may stay textual. |
| Class | Emblem in class/build UI | Optional accessory cue | Icon yes; full sprite no | UI/engine roster mismatch must resolve first. |
| Boss/leader/tier | Scale/mass accent or underlay shape | Emblem | Overlay, not new base | Must not be brighter hue alone. |
| Item family | Dominant icon contour | UI placement/frame category | Yes, at item-family/icon level | Rarity and element must not change the base contour. |
| Exact item identity | Internal motif/material landmark | Name/tooltip | Usually distinct icon composition | Stack quantity, durability, and value do not create new base art. |
| Equipment slot | UI placement/slot silhouette | Corner badge | No | HEAD/TORSO/LEGS/MAIN_HAND/OFF_HAND are metadata. |
| Rarity | Border notches/weight | Scoped accent hue | No | Must pass grayscale; avoid changing item silhouette. |
| Exact skill identity | Central action motif | Name/tooltip | Yes, one composed icon per executable identity | Numeric rank/cooldown states reuse it. |
| Skill kind/category | Frame or small badge | UI grouping | No | ACTIVE/PASSIVE and PHYSICAL/MAGICAL/ELEMENTAL are grammar. |
| Target/delivery | Orientation/action geometry | Corner target badge | Usually no | Strike, projectile, area, self, ally, etc.; roster not fully stable. |
| Element/damage | Scoped accent hue | Glyph or texture shorthand | No by itself | Hue is scoped to skill/combat-detail views, not a global entity color. |
| Condition family | Status glyph in bounded row | Pattern/polarity placement | Icon composition after schema stabilizes | Only urgent incapacity gets a map overlay. |
| Condition severity/duration | Meter/fill and number | Value/contrast | No | Never create icons per stack, severity, or duration. |
| Quest type | Reusable verb icon | Text label | No blueprint-specific base | Keep blueprint/runtime namespaces separate. |
| Objective kind/target | External map marker + glyph | Target subject and text | No instance-specific base | Marker must not replace the target's object/entity art. |
| Faction | Emblem | Scoped accent in diplomacy/inspector | Emblem may be unique; sprite base no | Do not globally recolor whole units by faction without testing. |
| Diplomatic/relationship state | Line style or state badge | Text | No | Direction and score remain data; no edge-specific art. |
| Selection/focus | Ring/outline | Highest local contrast | No | This channel is reserved for selection, not faction or rarity. |
| Targetability/range | Tile-space overlay/boundary | Cursor/tooltip | No | Do not reuse the selection ring. |
| Visibility/memory | Opacity/value treatment under fog | Question glyph for remembered entities | No | Must remain different from death, depletion, and disabled state. |
| Availability/depletion | Texture/pattern or structural state | Desaturation and text | No | Opacity alone would collide with memory/fog. |
| Health/progress/cooldown | Meter/fill | Number/text | No | Current canvas/HUD already use bars; precision lives in text. |
| Recent event/urgency | Brief motion/timing or screen-space feedback | Static aftermath marker | No | Motion is never the only cue and needs a reduced-motion fallback. |

On the map, precedence should be tested as: fog/knowledge treatment below the subject; depletion pattern on
the object; objective marker outside the subject; condition glyph in a bounded status position; selection
ring outside all of those; target/range treatment in tile space. Faction belongs in an emblem/accent slot,
not any of those state channels. If the stack exceeds its tested capacity, lower-priority detail moves to
the inspector plus an overflow count.

## 9. Readability Hierarchy

At ordinary map scale the player should perceive, in order:

1. walkable world versus obstacles/hazardous terrain;
2. focused/player entity;
3. immediate threats and active combat relationships;
4. objective or required interactable;
5. nearby allies, neutral actors, and important world objects;
6. health/critical condition and availability;
7. archetype/role/faction detail;
8. decorative variation.

At minimap scale the hierarchy should collapse to terrain regions, player/focus, threats, destinations,
objectives, and viewport. Individual item, wound, class, skill, or role identity should not be expected to
survive the current two-pixels-per-tile minimap base.

In inventory/skill UI the order changes: category and exact identity first, availability/cooldown second,
cost/quantity/rarity third, descriptive/stat detail on focus. The HUD roadmap’s planning principle—rank
default information by volatility and attention-worthiness rather than alphabetical/static order—should
also govern which visual alarms receive prominence.

## 10. Character and Entity Sprite Structure

### Proposed composition model

```text
entity visual
  = body-plan/race base
  + role or combat-delivery cue
  + optional readable equipment cue
  + optional leader/tier cue
  + scoped faction accent or emblem
  + runtime overlays (selection, HP, target, condition, objective)
```

**Repository fact.** Archetypes already compose race, faction, role, stat, combat, cognition, drive,
inventory, skill profile, traits, and themes. Eight body-model profiles support 13 races. This data shape
supports visual composition, but it does not prove every field belongs in art.

Recommended boundaries:

- body/race controls the base silhouette only when readable and gameplay-relevant;
- role/combat profile controls the strongest occupational or threat cue;
- actual equipped main/off-hand items may replace generic held cues when legible;
- faction uses a small accent/emblem layer, not a full-body recolor by default;
- class can appear as an inspector/party emblem and perhaps one accessory cue, not a complete skin;
- traits, cognition, drives, and numeric stats remain non-visual unless a specific trait changes gameplay
  perception (for example flying, large body, undead, venomous, or fire-aligned);
- generated personhood/history belongs in name, portrait/detail treatment, scars, or selected significant
  tokens—not an automatically unique full sprite.

### One-cell constraints

The current 16-pixel cell is a real implementation fact, not a required sprite resolution. Candidate art
may overhang or use a larger cached source drawn into a cell, but tests must establish collision, crowding,
camera, selection, and fog behavior before this is allowed. A sprite that reads only when enlarged in an
asset viewer fails the gameplay requirement.

## 11. Item and Equipment Visual Structure

Use three layers conceptually:

1. **category/family contour** — sword-like weapon, staff/focus, bow, shield/armor, potion, ration, tool,
   trinket, ore, plant, organic trophy, crystal/essence;
2. **identity motif/material cue** — rust, silvering, ember, venom, frost, spirit, healing, ancient;
3. **semantic UI layer** — rarity border, slot badge, quantity/durability meter, equipped/locked state.

Current difficult groups include `rusted_sword` / `iron_sword` / `steel_sword` / `silvered_blade`,
`wooden_staff` / `apprentice_staff`, and `crystal_shard` / `frost_shard`. Material or rarity color alone is
insufficient because color also carries elemental and UI meanings. The identity cue should survive
grayscale where the choice matters.

Equipment slots are metadata: HEAD, TORSO, LEGS, MAIN_HAND, OFF_HAND. They need slot symbols or placement
silhouettes in equipment UI, not five variants of every item. Head and leg content does not currently exist;
do not freeze a paper-doll layout based only on the currently populated three mappings.

Generated stack quantity, durability, value, owner, and provenance should not produce new base icons.
Brainstormed significant items may later gain a history marker, nameplate, or small unique overlay; this is
not authority for unique art for every item instance.

## 12. Skill and Ability Icon Structure

Every executable skill should be distinguishable in the skill bar and selection UI, but distinctness can
be built from a grammar:

```text
delivery geometry (strike / projectile / area / guard / movement / utility)
+ central subject or verb motif
+ optional element/damage accent
+ target badge where needed
+ UI state (passive, cooldown, unavailable, mastery)
```

Active/passive and physical/magical/elemental are metadata layers, not substitutes for exact skill identity.
Cooldown, cost, power, rank, mastery, and times used should use state treatment and text/meters, never new
icons per numeric state.

**Repository fact.** Four executable definitions exist: `power_strike`, `HEAVY_STRIKE`, `fireball`, and
`swift_reflexes`; profile data names 16 labels, including `firebolt` but not `fireball`. **Analysis
inference.** The visual system should test all 16 labels as a semantic stress corpus while commissioning
only implemented/approved skill art. The naming/definition mismatch must be resolved before a production
roster is frozen.

Abstract utilities—`appraise`, `bargain`, `repair`, `forge_basic`, `track_beast`, and `track_scent`—are
more difficult than elemental attacks and should drive icon tests. Similar actions in the same family must
be tested side by side, not individually against unrelated icons.

## 13. Status and Effect Representation

There is not enough architectural stability for a final status taxonomy.

| Area | Current requirement | Likely future requirement | Capacity to reserve | Decision status |
|---|---|---|---|---|
| Wounds | Generated permanent `WoundState`; live creation yields CRUSH, SLASH, PIERCE with severity-scaled penalties | Diagnosis, tactical consequence, perhaps type distinction | One wound-family marker, severity channel, room for several type motifs | Type icon roster is premature; BURN appears only in a state comment. |
| Scars | `ScarState` schema and entity list exist; formation is not a stable common player-facing loop | Persistent history/body evidence if wiring lands | Persistent-history/scar slot in detail UI; optional subtle sprite cue | Do not assume one sprite alteration per generated scar. |
| Passive effects | `swift_reflexes` is a passive skill; traits/breakthroughs also alter capability | More passives and learned capabilities | Passive badge state in skill/build UI | Usually absent from map overlays unless tactically urgent. |
| Temporary effects | Timed `well_rested_until`; legacy API shape exposes `active_effects` with duration/multipliers | General buffs/debuffs with duration/stacks/source | Small status row, polarity, duration, source tooltip | No unified authoritative registry exists. |
| Frozen/stunned | Free-form identity properties gate action/combat/work in several engine paths | Typed impairing conditions | High-priority incapacitation overlay and grayscale-safe pattern | Storage and roster are unstable; representation may change. |
| Elemental states | Skills/items use element/damage metadata; no stable general elemental-condition roster | Burn/freeze/shock/etc. only if mechanics approve them | Element accent channel plus independent polarity/type cue | Do not infer a status from every element tag. |
| General conditions | None unified | Brainstorm material proposes typed wound/scar/status/buff/debuff records | Extensible icon grammar and overflow behavior | Explicitly blocked on gameplay/schema design. |

Map overlays should be reserved for conditions that change immediate actionability: incapacitation, severe
danger, targetability, or an objective-critical state. Lesser modifiers belong in the selected-entity HUD.
If multiple effects coexist, show a bounded priority subset plus an overflow count rather than covering the
one-cell sprite.

## 14. World Object and Objective Representation

| Family | Unique identity policy | Reusable representation | Runtime/temporary state |
|---|---|---|---|
| Resource nodes | Distinguish node/material families needed for harvesting choice | Plant, tree, vein/outcrop, nest, wisp, cluster bases + identity motif | available, depleted, remaining charges, harvest progress |
| Buildings | Distinguish service/location types encountered on map | Building/entrance template + service symbol; selected named landmarks may be unique | owner, HP/damaged, open/unavailable, selected |
| Chests | Reuse chest/container family; tier need not create complete art | container + tier/guard cue | closed/looted, guarded, selected |
| Camps | Reuse camp/hostile-site family unless a persistent named Place becomes important | footprint/marker + faction/threat cue | active/cleared, maturity, owner |
| Hazards/local scars | Use hazard/scar family and ground overlay | pattern + hazard-kind glyph | active, severity, known/unknown |
| Objectives | Represent objective verb and target, not every quest instance | objective glyph + marker/ring + subject representation | active/completed/failed/blocked, progress |
| Interactables | Reuse the underlying object plus interaction affordance | focus ring, cursor/marker, verb tooltip | available, reserved, out of range |
| Ground items | One loot-stack marker in world; exact item icons in loot panel | stack/diamond + count | quantity, visibility, ownership if later relevant |
| Corpses | Reuse body-plan corpse family or a clear corpse marker | body family + dead-state treatment | lootable/empty, known/unknown |
| Places | Seven proposed kind markers; unique treatment only for selected persistent landmarks | kind marker + footprint + name + owner/hazard state | maturity, active, occupied, transformed, contested |

**Analysis inference.** A Place that changes from CITY to RUIN should retain its name/identity and change
state/kind treatment; it should not silently become a new unrelated art identity. Multi-tile footprints and
point locations require different experiments, and the planned Place schema must land before either is
specified.

## 15. UI Semantic Iconography

| Vocabulary | Current bounded surface | Likely encoding | Rationale |
|---|---:|---|---|
| Quest blueprint type | 6 | Icon + text | Useful scan aid; exact quest remains title/target text. |
| Runtime quest kind | 6, non-identical vocabulary | Icon + text | Keep separate until mapping is explicit. |
| Objective kind | 14 | Marker + icon + text on focus | World direction needs a marker; exact verb may need text. |
| Skill kind/category | 2 kinds, 3 categories | Frame/badge, not identity icon | Exact skill icon remains primary. |
| Equipment slots | 5 | Slot silhouette/icon + tooltip | Stable bounded metadata. |
| Elements/damage tags | 11 taxonomy tags; narrower frontend skill union | Accent + glyph/pattern when decision-critical | Hue alone is unsafe and vocabularies differ. |
| Item rarity | 3 current values | Border/notch + optional color | Must remain readable without hue. |
| Relationship role | 3 current | Icon + text | Friend/rival/neutral is compact and player-facing. |
| Diplomatic state | 6 | Icon/line style + text | Avoid edge-specific art; direction/context remain textual. |
| Route family | 16 | Text first; 4–10 family glyphs only if tests help | Sixteen tiny unique route icons may not improve choice. |
| World-event category | 28 | 8–14 family icons + severity/state | Event subject and wording carry exact meaning. |
| Building service | 8 | Map/HUD symbol + text | Reusable across location types. |
| Faction identity | 16 | Emblem + text; accent in scoped views | Emblems may be valuable, but simultaneous visibility is unknown. |
| Behavior state | 17 frontend colors | Text/status glyph on focus; map encoding only for urgent states | Current palette already has red-state collisions; not every AI state needs a map icon. |

Do not create an icon merely because an enum exists. An icon earns a place when it speeds a repeated scan,
survives its display size, and is less ambiguous than text.

## 16. Visual Reuse Model

| Reuse level | Meaning | Major families |
|---|---|---|
| Level 1 — unique complete asset | Separately authored whole representation | Select landmark/hero/boss treatments only after evidence; perhaps important named items |
| Level 2 — shared family template | Stable template with family-specific construction | body plans, weapon contours, resource/node bases, building/service families |
| Level 3 — base + semantic overlay | Composition creates distinct assembled looks | most archetypes, equipped characters, Places, factions on units, item elemental/history cues |
| Level 4 — shared icon grammar | Distinct motifs under common syntax | skills, objectives, quests, effects, services, events |
| Level 5 — UI-only state | Badge, border, pattern, meter, ring, opacity | rarity, slot, cooldown, selection, visibility, depletion, diplomatic state |
| Level 6 — text/numeric only | No dedicated image | stats, IDs, quantities, duration, relation axes, recipe parameters, generated provenance |

These are reuse layers, not mutually exclusive maturity levels. One skill can combine a Level 2 family
template, Level 3 motif composition, Level 4 grammar, Level 5 cooldown treatment, and Level 6 numeric text.
Every later asset decision ledger should therefore record four orthogonal fields: source-art uniqueness,
composition/template, runtime overlays, and text fallback. The default source-art investment should be
Level 2–4. Level 1 requires a player-facing importance argument, not merely a unique content ID.
Runtime-generated identities remain Level 3–6 unless a significant-item/person/Place mechanic explicitly
promotes them. Maximum component and overlay counts are experiment outputs, not fixed here.

## 17. Worst-Case Visual Stress Test Set

This is the initial identity-by-view decision ledger at stress-group granularity; it deliberately does not
specify all current IDs. Before production, extend the same fields to every approved player-facing identity.
“Current gate” means current code/data supplies the semantic distinction. “Capacity only” means the entry
tests extensibility but cannot block a current-content art specification.

| Gate | Test identity/group and primary view | Player decision/distinction that must survive | Reuse/fallback | Nearest confusion |
|---|---|---|---|---|
| Current | Goblin Scout / Goblin Archer — combat map | scouting/close threat versus ranged threat | shared goblin base; role cue; name on focus | each other; Bandit Scout |
| Current | Apprentice Mage / Arcane Mage / Moon Cult Sorcerer — map/inspector | experience/faction/corruption where the game exposes it | human caster base; emblem/accent; text | each other; Town Healer |
| Current | Town Healer / Forest Druid — map/inspector | human civic healer versus elf/nature healer | healer cue over race bases; text | caster group above |
| Current | Spirit Guardian — map | selectable living entity versus effect/resource | spectral body base; entity ring/name | Spirit Wisp |
| Current | Dragon Cult Champion — combat map | leader/flying/fire threat priority | body/leader composition; inspector detail | ordinary caster; fire feedback |
| Current | Cave Spider / Lizardfolk Scout — map | many-legged beast versus upright amphibious scout | separate body families | resource nest; small beast |
| Current | Rusted / Iron / Steel / Silvered swords — inventory | equipment/value/anti-undead choice | sword template + identity motif; item name | adjacent swords |
| Current | Wooden Staff / Apprentice Staff — inventory | basic versus progression magic weapon | staff template + motif; item name | each other; Spirit Lantern |
| Current | Warding Charm / Frost Focus — inventory | holy defense versus icy magic focus | trinket grammar + motif; item name | crystal material; skill icon |
| Current | Crystal Shard / Frost Shard / Spirit Essence — inventory/loot | crafting-material selection without hue | material grammar + contour; item name | each other; node output |
| Current | Ember Axe / Venom Dagger — inventory | weapon category first, modifier second | weapon contour + modifier motif | fire skill; venom material |
| Current | Spirit Lantern — inventory/world interaction | tool/interactable function | tool contour + spirit motif; label | staff, potion, Spirit Wisp |
| Current | Power Strike / Heavy Strike — skill UI | choose between near-synonymous physical attacks | physical-action grammar; skill name | each other; profile Dirty Strike |
| Current | CRUSH / SLASH / PIERCE wounds — inspector | type only if counterplay differs; severity is independent | wound grammar; diagnosis text | one another; damage-type glyphs |
| Current | Frozen / stunned flags — map/inspector | why an actor cannot act, if recovery/counterplay differs | incapacity family + label | each other; fogged/inactive entity |
| Current | Spirit Wisp / ground loot — map | harvest node versus dropped item | object-family silhouette; hover label | Spirit Guardian/Essence |
| Current | Mine Entrance / Dungeon Entrance — map | service/resource site versus adventure hazard | entrance template + service/hazard cue; label | each other; Cave terrain |
| Current | Investigate / Explore — quest UI/map marker | evidence-seeking versus traversal/discovery | quest grammar + text/target | each other; tracking skills |
| Current | Moon Cult / Arcane Circle — diplomacy/inspector | exact affiliation independent of caster body | emblem + text | each other; Dragon Cult |
| Current | Active / depleted resource node — map | whether harvesting is possible | same node base + pattern/state label | obstacle; decorative terrain |
| Capacity only | Fireball / profile `firebolt` — skill UI | test whether projectile scale/delivery could distinguish two approved skills later | fire-skill grammar + label | each other |
| Capacity only | Appraise / Bargain — skill UI | information/value inspection versus negotiated exchange | merchant-utility grammar + verb motif | each other; generic coin |
| Capacity only | Hold Line / Shield Bash — skill UI | sustained defensive stance versus impact attack | shield grammar + action geometry | each other; Iron Shield item |
| Capacity only | Track Beast / Track Scent — skill UI | target category versus tracking method, only if mechanics retain both | tracking grammar + subject/method motif | each other; Explore objective |

## 18. Resolution Experiments

These candidates are selected because the current native cell is 16 pixels and the HUD uses compact icons;
they are not requirements.

| Visual family | Smallest plausible candidate to test | Larger fallback(s) to test | Information that must survive | Failure that justifies increase |
|---|---|---|---|---|
| Entity world sprites | 16×16 source/read at one cell | 24×24 or 32×32 source drawn with controlled overhang/scale | body plan, focus, threat delivery, alive/dead | nearest archetypes collapse or overlays cover silhouette |
| Equipped-item cue | 8–12 pixels within character footprint | separate 16×16 cached cue or omit at map scale | melee/ranged/caster or shield/tool role | exact contour flickers or reads as noise |
| Inventory/item icons | 16×16 | 24×24, then 32×32 for abstract trinkets/materials | category and nearest-neighbor identity | sword/material/trinket stress sets fail native-scale matching |
| Skill icons | 16×16 | 24×24; 32×32 for abstract utilities if UI permits | action identity, family, availability | worst-case skill row cannot be distinguished without labels |
| Class/breakthrough icons | 16×16 | 24×24 or 32×32 in detail view | class/effect motif | WARRIOR/MAGE/ROGUE or three breakthroughs blur together |
| Semantic badges | 8×8 or 12×12 | 16×16 | slot, polarity, target, quest/objective family | badge becomes punctuation-like or fails grayscale |
| Resource/world-object sprite | 16×16 | 24×24/32×32 or multi-tile marker where schema permits | object family and availability | nodes confuse with loot, entities, or terrain |
| Building/Place marker | 16×16 point marker | 24×24/32×32; footprint treatment after Place design | entrance/service/kind/objective | labels are always required for basic category recognition |
| Effect/status marker | 12×12 | 16×16/24×24 in status row | urgency, polarity, coarse family | multiple effects cannot coexist or hue becomes sole cue |
| Minimap symbols | 2–4 pixel primitives | 6–8 pixel icon at high minimap zoom | focus/threat/objective/destination only | symbol disappears or merges into terrain/viewport outline |

Acceptance question across all families: can the Section 17 stress set be identified at its actual gameplay
scale, in context, without zooming the source artwork?

## 19. Palette Requirements

### Semantic color dimensions already competing

The implementation or plans expose at least these color candidates: terrain, entity/archetype family,
behavior state, resource type, building/service type, HP severity, rarity, class, damage type, element,
faction, diplomacy/relationship, selection/interaction, objective urgency, visibility/fog, and UI chrome.
They cannot all receive globally unique hues.

Separate palette layers conceptually:

- **global palette:** overall luminance/contrast and shared neutrals;
- **semantic accents:** a deliberately limited set for danger, benefit, selection, objective, element, or
  faction inside a scoped view;
- **per-asset local colors:** body, material, terrain, and object colors that establish identity;
- **UI colors:** surfaces, text, borders, controls, warnings, and disabled state.

Mandatory non-color readability applies to player/focus, hostile/urgent state, selected/targeted,
available/depleted, rarity where it changes decisions, buff/debuff polarity, and skill/item identity. Use
shape, pattern, label, frame, or position as a secondary cue.

**Planning fact.** The palette investigation found roughly 200 raw hex usages across multiple tables,
four divergent building-color copies, and near-luminance collisions among COMBAT, ALERT, and GUARD_CAMP.
It proposes a fresh tested data-visualization palette rather than preserving current hex values. This
document agrees with the need for experiments but does not adopt a palette.

Proposed experiments: view high-priority sets in grayscale; simulate common color-vision deficiencies;
compare symbols against actual dark UI surfaces and every relevant terrain family; and test scoped use of
color so element accents in a skill panel cannot be mistaken for faction or rarity.

## 20. Animation Requirements

| Classification | Content | Preliminary requirement |
|---|---|---|
| No animation needed | terrain, most items, materials, equipment slots, class/faction emblems, quest/objective symbols, buildings at rest | Static representation is sufficient. |
| Optional idle animation | characters/creatures, selected important world objects | Test a 2–4-frame loop; static fallback must remain readable. |
| Gameplay feedback animation | hit, heal, block, skill activation, harvest completion, loot pickup, objective completion | Short event feedback; identity must not depend on the animation. |
| State transition animation | death/corpse, depleted/recovered node, building/Place damaged or transformed, effect applied/expired | Use only when the transition matters and state remains clear afterward. |
| Screen/UI effect | selection change, critical warning, panel/loading transition, cooldown completion | Bounded, optional, reduced-motion-safe. |

**Repository fact.** World entities snap on data updates because the canvas has no
`requestAnimationFrame` loop; UI has hover/color transitions and 200 ms HP-width transitions but no shared
motion tokens or `prefers-reduced-motion` rule. **Planning fact.** A frontend-tier idea proposes one shared
draw pipeline with optional cached sprites/effects and a later interpolation loop. These are dependencies,
not authorization to design animation frames here.

## 21. Native-Scale Validation Rules

### Mandatory tests

- recognizable at the exact native map/HUD/minimap scale where used;
- distinguishable from every named nearest neighbor in the current-gate stress set; capacity-only pairs are
  exploratory until their gameplay distinctions are approved;
- player/focus, threat, objective, and interactable hierarchy survives crowded nearby tiles;
- core identity and urgent state remain readable in grayscale;
- no required meaning depends exclusively on hue, motion, hover, or single-pixel decoration;
- selected, targeted, dead, remembered, depleted, disabled, and fogged states do not become interchangeable;
- labels are present wherever the symbol grammar is not independently reliable;
- multiple coexisting overlays follow a priority/overflow policy and do not obscure the base subject;
- zoom scaling uses nearest-neighbor/pixelated behavior only if the chosen experiment benefits from it;
- rendered state remains deterministic where used by the server QA renderer.

### Optional quality tests

- recognizable by silhouette alone after brief learning;
- readable under common color-vision simulations;
- aesthetically coherent when unrelated families share a screen;
- optional idle/effect animation does not cause flicker or attention competition;
- artwork remains pleasant at larger inspect/detail scale;
- family grammar lets a new identity be guessed before reading its label.

### Reference harness and evaluation protocol

“Native scale” must be a recorded test configuration, not a screenshot resized by eye. The first experiment
should create a disposable comparison harness—not a production renderer—with these recorded inputs:

- CSS display size and backing-buffer size, browser, device-pixel ratio, viewport, and sampling mode;
- current default map condition (16 CSS pixels per cell at zoom 1.0), the supported low-zoom boundary
  (0.5), and at least one enlarged inspection condition; these are test cases, not sprite specifications;
- exact inventory/skill/status display boxes used for each applicable candidate size from Section 18;
- representative light/dark and visually busy terrain backgrounds, fog/memory state, adjacent units, and
  all overlays enabled by the scenario;
- allowed sprite overhang and crop behavior, recorded for each candidate rather than silently changed;
- an unscaled capture of every test condition plus the source candidate and configuration manifest.

Use a labeled familiarization round followed by randomized unlabeled identification and in-context decision
rounds. Record a confusion matrix, identification time, confidence, text usage, and failures by background,
zoom, and color condition. A small pilot cohort (hypothesis: 3–5 independent reviewers) may calibrate task
difficulty, but it does not approve art. Before comparing final candidates, preregister per-task pass
thresholds based on decision criticality and use fresh reviewers; do not select thresholds after seeing
which candidate wins. A critical category error—player versus loot, threat versus neutral, objective versus
decoration, active versus depleted—should be treated more severely than a slower exact-name distinction in
an inspector where text is available.

Each experiment must output: harness manifest, comparison sheet, raw observations, confusion matrix,
decision with confidence, rejected alternatives, and unresolved follow-up. If no preregistered threshold
exists, the result is exploratory and cannot freeze a production rule.

## 22. Art-System Failure Risks

| Rank | Risk | Likelihood / Impact | Mitigation before production |
|---:|---|---|---|
| 1 | Hue carries too many meanings | High / High | Assign channels per view; require secondary cues and grayscale tests. |
| 2 | Every content/runtime ID receives unique art | High / High | Enforce reuse levels and identity boundary in Sections 2 and 16. |
| 3 | Skills are individually attractive but mutually indistinguishable | High / High | Test family rows and nearest neighbors, especially abstract utilities. |
| 4 | Character variants explode as race × role × class × faction × gear × state | High / High | Layered composition with bounded overlays; never pre-render the Cartesian product. |
| 5 | One-cell overlays cover sprites | High / High | Readability hierarchy, priority subset, overflow indicator, HUD drill-down. |
| 6 | Status taxonomy changes faster than icon production | High / Medium–high | Reserve a grammar and slots; freeze no roster until schema approval. |
| 7 | Item/material icons rely on color and blur together | Medium–high / High | Dominant contour and grayscale stress tests. |
| 8 | Runtime-generated identities are mistaken for authored asset demand | Medium / High | Keep instance provenance at reuse Levels 3–6. |
| 9 | Live client and server QA renderer develop contradictory semantics | Medium / High | Share semantic layer order/vocabulary contracts even if runtimes differ. |
| 10 | “Programmer art” results from inconsistent rules, not drawing quality | High / Medium | Define family templates, channel ownership, spacing, and validation before polish. |
| 11 | Animation/effects undermine performance or accessibility | Medium / Medium | Cached/bounded effects, evidence-gated tiers, reduced-motion fallback. |
| 12 | Planned Place/faction/history systems force expensive rework | Medium / Medium | Work on generic markers and composition now; postpone identity-specific production. |

## 23. Dependencies on Unfinished Gameplay Design

| Area | Current State | Why Visual Decision Should Wait | Safe Work That Can Be Done Now |
|---|---|---|---|
| Unified statuses/effects | Fragmented wounds, free-form frozen/stunned, timed rest marker, passive skill, legacy frontend effect records | No approved type roster, stacking, priority, polarity, or source model | Test generic condition rows, urgency overlays, severity/duration channels, and overflow. |
| Wound/scar lifecycle | Wounds are permanent; scar schema exists but formation/player loop is not stable | It is unclear which distinctions drive treatment or tactical choice | Test generic wound severity and optional type motifs; keep scars in detail/history. |
| Skill roster | 4 executable definitions versus 16 profile labels | Identity, naming, effects, and exact future count are unresolved | Use all labels as stress-test semantics; produce grammar prototypes only. |
| Equipment expansion | 5 slots, but catalog mappings populate three and only two armor items exist | Paper-doll and visible gear layers could encode a false roster | Test weapon/shield cues and flexible slot icons; leave head/leg layout provisional. |
| Item instances/significance | Base definitions exist; significant-item layer is brainstorm-only | Unknown which generated items gain persistent visual identity | Reserve history/name/unique marker without unique instance art. |
| Places | 7 proposed kinds; no implemented Place collection | Footprint, migration, runtime construction, transformation, ownership, and naming are unresolved | Test kind markers, point vs footprint legibility, owner/hazard overlays. |
| Classes | Four engine definitions; Class Hall hard-codes a different four-key set and its metadata endpoints are absent | The playable roster/UI contract must converge; class may be build UI identity, sprite cue, or both | Test the engine four only as provisional emblems and one optional accessory channel; do not commission against the divergent UI list. |
| Faction presentation | 16 authored factions, four legacy behavior buckets | Simultaneous visibility and emblem importance are unknown | Test a small worst-case emblem set and scoped faction accents in diplomacy UI. |
| Race/role expansion | 13 races, 23 roles, uneven archetype coverage | New archetypes may close gaps without adding new body families | Establish body-plan and role-cue templates; avoid full combination sheets. |
| Quest type mapping | Blueprint and runtime vocabularies each have six non-identical values | A single icon table could imply a mapping the game does not have | Keep namespaces separate; test verb/target grammar. |
| Objectives/routes/events | Bounded enums create generated instances | Not all enum values may appear in the same player-facing view | Group by scan task; prefer text until repeated icon value is demonstrated. |
| Place/region transformation | Regions are current; Place identity is planned | Whether art attaches to region, Place, footprint, or named landmark is unsettled | Preserve identity/state separation and generic transformation cues. |
| Rendering architecture | Reconnected canvas and separate server QA renderer exist; shared live core/tier model remains an idea | Asset loading, cached sprite composition, interpolation, and tier ownership are unapproved | Specify semantic outputs and layer order, not implementation or file formats. |
| Palette system | Current tables are fragmented; redesign is unscheduled | Exact hues must follow real context, collision, and accessibility tests | Define channel ownership and test sets; do not preserve or replace hex values here. |
| Motion system | Some transitions exist; no shared tokens/reduced-motion support | Timing and render loop are not calibrated | Classify animation need and require static/reduced-motion fallbacks. |

## 24. Proposed Art-System Experiments

Do not perform these as part of this document.

Run them in stages. Stage A defines the harness/protocol above. Stage B tests stable current families
(silhouette, resolution, composition, items, skills, and world-object confusion). Stage C integrates those
families in crowded combat, semantic-color, and minimap tests. Passing A–C is sufficient to draft a
**current-content** art specification. Stage D tests optional/future capacity—statuses, Places, expanded
factions/skills, and animation—only after the relevant schemas or gameplay decisions land. Stage D must not
indefinitely block the current-content specification.

| Order | Experiment | Question | Input/test set | Success criteria | Decision informed |
|---|---|---|---|---|---|
| A1 | Reference harness/protocol | Are later comparisons reproducible at actual scale? | Current map/HUD configurations plus Section 21 manifest fields | A second reviewer can reproduce captures and scoring from the manifest | All later experiment validity |
| B1 | Silhouette-only entities | Can body plan, focus, and threat delivery read without color/detail? | Current-gate Section 17 entity groups in a crowded grid | Meets preregistered family/threat thresholds at native scale | Base sprite families and minimum size |
| B2 | 16 vs 24 vs 32 comparison | What is the smallest viable source/display size? | Same difficult entity/item/skill set in the reference harness | Smallest passing candidate meets every mandatory task threshold | Candidate resolution ranges |
| B3 | Character composition reuse | Can shared bases still yield recognizable archetypes? | Goblin trio, human caster trio, healer pair, leader/boss | Neighbor identities remain below the preregistered confusion limit | Level 2/3 composition model |
| B4 | Grayscale item test | Are category and identity carried by contour/motif? | Sword set, staff pair, trinkets, shard set, Spirit Lantern | Meets category/exact-identity thresholds without hue or rarity color | Item grammar and icon size |
| B5 | Skill-family distinguishability | Do icons work as a set rather than alone? | Current strikes first; capacity-only merchant, shield, tracking, and fire pairs separately | Current set passes; future set produces nonbinding capacity findings | Skill grammar and resolution |
| B6 | World-object confusion | Do gameplay objects remain distinct from entities and terrain? | Spirit Wisp/Guardian/Essence, mine/dungeon, node/loot/corpse/chest | Critical object-family errors stay below their preregistered threshold | World-object grammar |
| C1 | Native crowded combat | Does the hierarchy survive realistic overlap and terrain? | player, allies, similar enemies, loot, node, objective, HP, target lines, fog | Focus/threat/objective decisions pass before exact-detail tasks | Draw order, overlay priority, sprite size |
| C2 | Semantic-color overload | How many meanings can coexist in one combat/HUD view? | faction + element + danger + selection + rarity mock states | Every high-priority meaning has a passing non-color cue and no channel collision | Channel allocation and palette scope |
| C3 | Minimap reduction | Which meanings survive at 2-pixel tile base and higher zoom? | player, threat, objective, destination, resource | Only intended high-level signals meet recognition thresholds | Minimap symbol budget |
| D1 | Status capacity/overflow | Can unstable future effects fit without covering a unit? | wound + incapacity + hypothetical buff/debuff + objective combinations | Priority state visible; overflow discoverable; base identity intact | Status row/map overlay extension contract |
| D2 | Place point-vs-footprint | Can one system support small sites and settlements? | seven proposed Place kinds using generic blocks, no final art | Marker/footprint and owner/hazard state remain legible | Future Place representation |
| D3 | Faction-emblem subset | Is an emblem system useful at current roster size? | Moon Cult, Arcane Circle, Dragon Cult, Forest Wardens, Town Council | Meets recognition threshold in diplomacy/list contexts without hue | Whether 16 full emblems are justified |
| D4 | Static vs 2–4-frame idle | Does minimal animation add life without obscuring state? | representative body families and reduced-motion/static fallback | Recognition does not regress and attention errors stay within threshold | Whether idle animation is worth production cost |

## 25. Preliminary Visual System Model

**PRELIMINARY — NOT A FINAL ART SPEC**

- **Likely asset families:** entity body/role compositions; item/equipment icons; skill/progression icons;
  terrain; building/resource/object families; status/effect grammar; quest/objective/service/faction symbols.
- **Likely reuse strategy:** family templates and base-plus-overlay composition for most world sprites;
  shared grammar for skills and semantics; UI-only state and text for generated/numeric content.
- **Likely semantic channels:** silhouette for body/object family; attached form for role/delivery; motif for
  exact icon identity; scoped accent for one semantic axis; frame/pattern/badge/meter/ring/line for state.
- **Highest-risk categories:** skills, compositional characters, similar items, unstable conditions, Places,
  and any view that combines faction, element, behavior, rarity, selection, and urgency through color.
- **Relatively cheap systems:** quest blueprints, relationship edges, objective/event instances, histories,
  numeric progression, cooldowns, quantities, and runtime IDs.
- **Likely animation scope:** static by default; optional 2–4-frame character idle; short gameplay feedback;
  bounded state transitions and reduced-motion-safe UI effects.
- **Blocked decisions:** final palette, source/display resolutions, art style, status roster, Place assets,
  expanded equipment paper doll, full skill roster, faction-emblem breadth, sprite-loading architecture,
  live render tier, and animation timing.
- **Next gate:** run Stages A–C in Section 24 with the current-gate Section 17 set at actual
  map/HUD/minimap scale, then write a current-content art specification. Add extension specifications from
  Stage D only as the corresponding gameplay schemas stabilize.

## Source Index

### Repository facts

- `docs/brainstorm/codex/taxonomy/content-taxonomy.md` — content identity, cardinality, implementation/planning boundaries.
- `frontend/src/components/GameCanvas.tsx` — canvas layers, zoom/pan, minimap, locations, current markers.
- `frontend/src/hooks/useCanvas.ts` — primitive drawing, selection, HP, combat lines, fog, memory, hover/click priority.
- `frontend/src/constants/colors.ts` — 16-pixel cell, terrain/entity/state/resource colors and legend.
- `frontend/src/types/api.ts` — live client entity, skill, effect, quest, building, node, chest, location, region shapes.
- `frontend/src/components/{InspectPanel,EntityList,EventLog,BuildingPanel,ClassHallPanel}.tsx` — current compact HUD representations.
- `src/rendering/{render,render_annotated,incremental,review_pipeline}.py` — deterministic QA rendering and layer contract.
- `docs/visual_quality/{scoring_contract,current_state}.md` — implemented QA-rendering scope and calibration limits.
- `data/content/entities/{entity_archetypes,skill_profiles}.yaml` — archetype composition and unresolved skill-label corpus.
- `data/content/world/{items,resources,buildings,terrain,biomes,runtime_regions}.yaml` — current world/item identities.
- `data/content/social/factions.yaml` — current faction identities.
- `src/core/{skills,classes,equipment,state}.py` and `src/core/models/{inventory,quests,social}.py` — executable skills, classes, slots, runtime objects, conditions, semantic enums.
- `src/engine/{combat,rpg_depth,legality}.py` — wound creation and free-form incapacitation checks.
- `src/domains/{adventure,world_emergence}/schema.py` — route and event vocabularies.
- `experiments/spatial_rendering/prototype/output/dungeon_crawl_annotated.png` — inspected QA-render example; flat categorical geometry, not player art.

### Planning facts

- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` and milestone epics M2–M6 — planned RPG core sequence.
- `docs/plans/hud_delivery_roadmap.md` — thin HUD foundation, vertical slice, evidence-driven extraction, volatility-first hierarchy.
- `docs/plans/live_map_scaling_roadmap.md` — reconnected map and evidence-gated performance/interest management.
- `docs/plans/idea_hud_color_asset_system.md` — palette inventory, collisions, accessibility, and unscheduled redesign idea.
- `docs/plans/idea_hud_motion_transition_system.md` — current motion inventory and reduced-motion gap.
- `docs/plans/idea_frontend_canvas_render_tiers.md` — unscheduled shared-pipeline sprite/effect tier concept.
- `docs/plans/world_rendering/idea_world_rendering_core.md`, `idea_world_render_validation.md`, and `docs/plans/world_rendering_core_epic.md` — historical plans and implemented QA-rendering lineage.

### Brainstorm directions

- `docs/brainstorm/rpg_expected_schemas.html` — proposed Place and unified modifier/status shapes; not implementation authority.
- `docs/brainstorm/codex/2026-08-27-core-rpg-new-idea-portfolio.md` — significant items, Households, commitments, testimony, failure.
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` — non-authorizing temporal modifier direction.
