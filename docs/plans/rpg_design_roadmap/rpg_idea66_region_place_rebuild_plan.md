---
status: active
layer: world
authority: P1
audience: agent
tags: [content, architecture]
---

# Plan — Idea 66: Region Contains Multiple Places (Region/Place Foundational Rebuild)

**Status:** promoted to `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD` (2026-09-02) as a scope-only
epic. This document is the pre-ticket scoping layer for idea 66, originally promoted out of
`rpg_m8_world_corpus_generation_epic.md`'s item 9 into its own document because M8's own scope
explicitly says idea 66 "owns the world-schema migration and corpus-wide grade-anchor impact directly,
rather than deferring that cost to this epic." Child tickets (schema migration, `WorldCompiler` wiring,
two-stage pilot/recalibration — separable units of work, per the epic's own Scope section) are cut when
the epic is picked up for action; this doc remains the scoping source for that pass, the same role M2's
own epic doc played before its 15-ticket batch was created.

**Source:** `docs/brainstorm/rpg_feature_atlas.html` idea 66; `docs/brainstorm/rpg_expected_schemas.html`
§"Region & Place" (`schema-66`, the most detailed schema section in that document);
`docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` item 9;
`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2.

**Gate (plan-owner decision, 2026-08-29 — promoted, narrow gate):** blocks only work whose authoritative
state depends on Place identity or containment — M2's idea 35 (City ownership) and idea 48 (place-type
transitions), and M4's place-shaped branch (ideas 44-47, 61). It is not a whole-milestone gate: M2's ideas
36, 37, and 43 (population seeding) are explicitly unblocked by it, and M4's material/expansion (49-52) and
institution (40, 41, 64) branches apply the gate only where a specific outcome authoritatively uses Place
identity/containment, at that ticket's own scope.

## Problem

Confirmed directly against real code: `RegionSpec.bounds` (`src/worldbuilding/schema.py`) is a single
rectangular box, and real world-module content (`data/content/world_modules/*.yaml`) contributes flat
sibling regions — `hometown`, `old_mine`, `goblin_camp`, `haunted_battlefield` — with zero containment
between them. A City isn't a place inside a Region today; a City *is* one Region, specifically whichever
region box `worldbuilding/compiler.py` tagged `kind=="TOWN"`. This idea doesn't extend that model, it
replaces it — `Place` becomes the atomic point-of-interest object, positioned within a Region's (larger)
bounds. A Region can hold as many Places as its geography implies: one City, a City plus two Ruins and a
Camp, or none at all (empty wilderness).

This one rebuild directly subsumes four things already separately proposed or found broken elsewhere in
this roadmap: idea 45 (Camp) and idea 46 (Nest) become `CAMP`/`NEST`-kind Places instead of a bespoke
`CampState` reused by analogy; idea 47 (Lair) becomes a `LAIR`-kind Place anchored to its occupant, reusing
today's real `boss_region_id` precedent; and the previously-unscoped Ruins/Mines/Battlefields gap (real in
content today, e.g. `haunted_battlefield`/`old_mine`, currently flattened into ordinary Region tags with no
idea assigned to fixing it) becomes `RUIN`/`DUNGEON`-kind Places instead of a permanent gap. It also
directly informs idea 35's sovereignty wiring: sovereignty most naturally belongs at the Region (territory)
level, with Places inheriting it by default and only overriding when a specific Place is independently
contested — a Lair sitting inside otherwise-hostile territory, for instance.

## Target Shape

Full field-level schema already worked out in `docs/brainstorm/rpg_expected_schemas.html#schema-66` — not
duplicated in full here, only the shape summary needed to scope tickets:

**`RegionState` (revised)** — becomes a territory container. Adds `places: List[str]` (ordered `place_id`
references); `bounds` semantics extend from "one settlement's footprint" to "a contiguous area that may
hold several Places"; `owner_faction_id` becomes territory-level sovereignty, overridable per-Place;
`tags` extends to describe the territory as a whole (biome/ecology), not a single settlement. All other
existing fields (`trauma_score`, `hazard_level`/`hazard_kind`, `population_cohorts`) are reused unchanged.

**`PlaceState` (new)** — `place_id`, `region_id` (parent reference), `kind: PlaceKind` (`CITY | CAMP | NEST
| LAIR | RUIN | DUNGEON | LANDMARK`), `position` (point within the region's bounds), `footprint` (optional
sub-bounds, multi-tile CITY-kind only), `owner_faction_id` (optional sovereignty override),
`scale` (optional, CITY-kind only — settlement size as a scalar; replaces the idea of a separate "Town"
kind sitting below City by scale), `maturity` (optional, CAMP/NEST-kind, reused from `CampState.maturity`),
`occupant_entity_id` (optional, LAIR-kind, reused from today's `boss_region_id` pattern),
`hazard_level` (optional, RUIN/DUNGEON-kind local override — moves from a Region-level tag to a real
field), `building_ids`/`entity_ids` (CITY-kind, today's `town_tiles`/`town_entities` equivalent, re-scoped
to the Place instead of the whole Region).

**Added 2026-09-02 (direction-alignment audit extension):** `prior_kind: Optional[PlaceKind]` and
`transformed_tick: Optional[int]` — a single-hop transformation trail (what this Place used to be, and
when), not a full history log. Serves Principle 5 ("places remember what happened to them") — a City
destroyed into a Ruin should carry legible trace of what it used to be, not just its current kind. See
`docs/brainstorm/rpg_expected_schemas.html#schema-66` for the field-table entry.

**Settlement-size note:** there is no separate "Town" kind below City in this shape — settlement size
(hamlet through metropolis) is the `scale` scalar on a single `CITY`-kind Place, not a taxonomy split. The
non-`CITY` kinds are explicitly the non-civilization side of the map: where monsters, ancient remnants, and
natural spawns live, not where settled population lives.

## Scope (not yet broken into child tickets)

1. **Schema migration.** Add `PlaceState`/`PlaceKind` per the shape above; extend `RegionState` with
   `places: List[str]`. Resolve the open membership-index question below *before* ticketing this, not
   during implementation.
2. **Open design decision to resolve first:** does Place membership work as `RegionState.places: List[str]`
   only, or does each entity/building also need a direct `place_id` field for fast lookup without a
   Region-side scan? The Durable State Rule (project `CLAUDE.md`) argues for a registry index either way.
   `Group`/`Party` already faced this exact tradeoff for a structurally similar problem (see the parallel
   open question on `ClanState` membership in `rpg_expected_schemas.html`'s Clan schema) — check how that
   resolved before deciding here rather than re-deriving it from scratch.
3. **`WorldCompiler` wiring.** `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) is confirmed the
   sole production site that constructs a populated `AuthoritativeState` from content (per M8's own
   investigation) — this is the actual insertion point, not a new parallel pipeline.
4. **Two-stage pilot, not a single 21-world cutover** (per M9's investigation, item 2):
   - **Stage A** (smallest correctness check): `unit_information_source` — 16 entities, 1 region
     (`frontier_village_core` + `hero_adventurers`). One region becomes one `Region` containing exactly one
     `Place(kind=CITY)`; nothing else should change, and the diff is trivially hand-verifiable.
   - **Stage B** (first real mixed-content check): `hero_guild_routing` — 4 regions (City + `goblin_camp`
     wilderness + `ruins_mystery_quest` + `mountain_pass`) — proves the migration handles non-uniform region
     kinds before rolling out to the remaining 19 worlds.
   - No true parallel-run is feasible — `WorldCompiler.compile()` is a single synchronous pass with no
     existing hook for running two schema versions side-by-side. The practical equivalent is sequential: old
     schema's `state_hash` + grades are already recorded as the baseline for all 21 worlds today; compile
     under the new schema and diff against that recorded baseline. A staged hard cutover (Stage A → Stage B
     → remaining 19), not a live comparison.
5. **Recalibration procedure, using infrastructure that already exists.** Every
   `world_compile_report.json` already carries a `state_hash` field. Recompile each world under the new
   schema and diff `state_hash` against the committed one first — an unchanged hash proves a lossless
   migration for that world with no SimQ grade run needed at all. Only for worlds whose hash *does* change
   does a full `grade_anchors.json` re-run and manual grade-shift triage apply (real vs. compile-shape
   noise). `grade_anchors.json`'s tolerance (±1 letter-grade band, `max(0.05, 0.20×score)`) across all 84
   committed `run_keys` will very likely trip on a structural compile-shape change at this scale even with
   zero real gameplay regression — budget this as a genuine per-world triage pass across all 21 worlds/84
   run_keys, not a single batch diff.
6. **Downstream unblocking.** Once this lands, ideas 35, 45, 46, 47, and 48 become buildable against a real
   `Place` model instead of a flat one — each keeps its own ticket (see Out of Scope), but this rebuild is
   the shared prerequisite all of them cite.

## Out of Scope

- Actually implementing ideas 35 (City ownership), 45 (Camp), 46 (Nest), 47 (Lair), 48 (place-type
  transitions), or 61 — each keeps its own ticket once this rebuild lands and unblocks it. This plan only
  builds the `Place` model itself and migrates existing content onto it.
- A `Country`-tier entity — a separate M8 finding (this engine's sovereignty model is region-level and
  faction-based only; "Country" throughout the roadmap's ideas 35/51 really means `FactionState` with
  territory), not part of this rebuild.
- Authoring new content inside the new Place kinds (e.g. idea 37's race-relations matrix, idea 45's Camp
  texture) — this plan seeds the schema and migrates existing content 1:1, it does not add new gameplay
  content.
- Idea 48's place-type transition *mechanic* itself (reusing `TransformationService`'s existing threshold
  table, per the M2 epic doc's own finding) — only `Place.kind` becoming a real, migrated field is in scope
  here; the runtime mutation rule belongs to idea 48's own ticket.

## Acceptance Signal

- The membership-index open question (List-only vs. `place_id` back-reference) is decided and recorded here
  before any child ticket starts, not discovered mid-implementation.
- Stage A (`unit_information_source`) compiles with a byte-identical `state_hash` to its committed baseline,
  or any hash change is explained and accepted before Stage B begins.
- Stage B (`hero_guild_routing`) compiles correctly with all 4 non-uniform region kinds represented as the
  expected `Place.kind` values, verified by direct inspection, before the remaining 19 worlds are attempted.
- All 21 worlds have gone through the `state_hash`-first recalibration procedure; every world whose hash
  changed has a recorded triage note (real regression vs. compile-shape noise) in this rebuild's own ticket,
  not deferred to a future audit.
- M2's idea 35/48 tickets and M4's idea 44-47/61 tickets are unblocked and can cite this plan's landed state
  as their prerequisite.

## References

- `docs/brainstorm/rpg_feature_atlas.html` — idea 66's full card (target shape, subsumption, sequencing)
- `docs/brainstorm/rpg_expected_schemas.html#schema-66` — full field-level `RegionState`/`PlaceState` schema
  and the membership-index open question
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — Idea 66 promotion, gate boundary, Sequencing rules
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` — item 9 (sequencing recommendation,
  ownership note), item 2 (Camp's insertion point, superseded by this rebuild if it lands first)
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — item 2 (two-stage pilot, recalibration
  procedure, corpus-wide risk)
- `docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md`,
  `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — the tickets this rebuild unblocks
