---
status: active
layer: world
authority: P1
audience: agent
tags: [content, architecture]
---

# Epic Plan — RPG Design Roadmap, Milestone 8: World Corpus, Generation & Modules

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M8-WORLD-CORPUS` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** Direct investigation of `src/worldbuilding/compiler.py`, `src/worldmodules/`,
`data/content/world_modules/*.yaml` (20 files), `data/worlds/*/world.yaml` (21 compiled worlds),
`docs/world/compiler_contract.md`, `docs/world/generator_contract.md`,
`docs/simulation_quality/corpus_tier_taxonomy.md`.
**Gate:** informs M1-M6 rather than blocking them — this epic answers "can the mechanism actually be
instantiated into a real world" for the ideas that need it, which matters most once each idea's own
milestone is ready to ship, not before.

## Problem

**2026-08-29 review note:** Idea 66 is promoted (plan-owner decision, see the parent roadmap and item 9
below) — its own implementation ticket owns the world-schema migration and corpus-wide grade-anchor impact
directly, rather than deferring that cost to this epic as a later audit finding. If the temporal-axis
proposal's calendar/lifecycle work (see the parent roadmap's "Temporal axis") reaches ticket scope, this
epic's job extends to confirming that calendar, lifecycle, routine, and seasonal configuration can actually
enter compiled worlds — the same question this epic already asks of every other idea's content.

Every prior milestone in this roadmap answered "is the mechanism correct" and "what data does it need."
Neither answers a third question: **does the engine's real world-generation/compilation pipeline actually
have a place for this content to enter a running world, and do the existing test corpora actually exercise
it once built?** `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:177-641`) is confirmed the sole
production site that constructs a populated `AuthoritativeState` from content — every content-seeding idea
in this roadmap lives or dies on whether that function has (or gets) a real insertion point.

## Scope (not yet broken into child tickets)

1. **Idea 43's insertion point — confirmed clean, low-risk.** `WorldCompiler.compile()` step 2 already
   loops over `spec.regions`; `RegionState.population_cohorts` just needs to be set inside that existing
   loop. No new architecture required — reuse the M2 ticket, don't scope this separately.
2. **Idea 45's insertion point — confirmed deeper than the atlas originally scoped.** `CampState` is never
   constructed anywhere in production code, `WorldModuleSpec` has no `camp_recipes` field, and the compiler
   has no camp step at all. This ticket needs a new schema field plus a new compiler step, not a data-seed
   call into an existing pattern — re-scope idea 45's own M4 ticket estimate accordingly. **Superseded by
   scope item 9 below if idea 66 lands first**: a real `Place` hierarchy would give Camp a proper insertion
   point instead of a bespoke schema field.
3. **Idea 14/44's `settlement_capacity` — confirmed not-yet-built at the schema level**, not merely
   unwired. Doesn't exist anywhere in `src/` or `docs/` except this atlas's own prose. M2's ticket for idea
   14 needs to include the actual schema addition, not assume one exists to extend.
4. **World-module deployment — confirmed a non-issue, re-verify only if this epic starts much later.** All
   20 authored world modules are live in at least one of the 21 real compiled worlds today (re-checked
   directly against `TCK-20260630-WORLD-DEPLOY-MODULES`'s original "7 of 20 unused" finding, which was
   fixed by that same ticket and has stayed fixed). No reuse-the-unused-module opportunity exists for any
   of M1-M6's content — this dimension is closed, not a gap to plan around.
5. **Corpus-profile gap analysis, per idea.** Three of the six real profiles (`crowded_frontier`,
   `hero_guild_routing`, `resource_dense_basin`) already have City-type settlement content
   (`frontier_village_core`) coexisting with hostile camp-flavored population content
   (`goblin_camp_conflict`, `orc_clan_territory`, `bandit_road_trade_pressure`) in the same compiled world —
   once idea 44/45's mechanism exists, testing the settlement-capacity split needs **zero new corpus
   authoring** for those three profiles. `dungeon_crawl` and `wilderness_survival` deliberately have no
   City-type content (by taxonomy design) and aren't candidates for this test regardless.
6. **Ideas 39/51 (contested border between two political entities) — confirmed not achievable by any
   profile, and not a corpus-authoring gap.** No `Country`-tier entity exists anywhere in `src/`; this
   engine's sovereignty model is region-level and faction-based only
   (`docs/mechanics/regional_sovereignty.md`). "Country" throughout this roadmap's ideas 35/51 is really
   `FactionState` with territory — there is no separate concept to build a corpus scenario against beyond
   what Faction already provides. Worth a terminology clarification on ideas 35/51 themselves (not done in
   this epic) if this reads as confusing to a future implementer.
7. **Idea 32 (reproduction pressure-gating near capacity) — confirmed not achievable by any profile, for
   two independent reasons.** `population_cohorts` is unseeded in every world in the corpus (same root
   cause as item 1), and no reproduction/capacity-gating mechanism exists in code at all — only
   scarcity-triggered emigration exists today, a different mechanic. Fixing corpus content alone would not
   exercise anything; both the cohort model (idea 43) and the capacity concept (idea 32 itself) need
   building first. Sequence this epic's work on idea 32 strictly after M3 ships, not before.
8. **Reusable groundwork already found**: a real, freeform location-tag vocabulary already exists across
   the 20 modules (`ruins`, `cave`, `mine`/`underground`, den-flavored regions, `settlement`) via
   `RegionRecipeSpec.tags`, used today only for quest-routing. Idea 48 (place-type transitions) can reuse
   this existing tag vocabulary as a starting point rather than inventing a new one, even though no
   place-type-transition mechanism sits on top of it yet.
9. **Idea 66 — Region Contains Multiple Places, a foundational rebuild — should be sequenced first in this
   epic, not last despite its list position.** Confirmed directly: `RegionSpec.bounds` is a single
   rectangular box and real world-modules contribute flat sibling regions (`hometown`, `old_mine`,
   `goblin_camp`) with zero containment between them — a City isn't a place inside a Region today, it IS a
   Region. This idea replaces that with `Place` as the atomic point-of-interest object (kinds: `CITY`,
   `CAMP`, `NEST`, `LAIR`, `RUIN`, `DUNGEON`) positioned within a Region's larger bounds. It directly
   subsumes items 2 (Camp's schema gap) and 6 above (the location-tag vocabulary becomes real `Place.kind`
   values instead of freeform tags), and gives idea 47 (Lair) and the previously-unscoped Ruins/Mines gap a
   proper home instead of each inventing its own bespoke shape. **Recommendation: scope and land idea 66
   before ticketing idea 45 (Camp) or idea 47 (Lair) in M4** — building those on today's flat model first
   means redoing both once (or if) this rebuild lands, and this epic's own item 2 already found Camp's
   current insertion point deeper than originally scoped, which is exactly the kind of rework idea 66 would
   prevent.

## Out of Scope

- Building any of the schema/compiler-step gaps named above — this epic identifies where they belong,
  the actual building happens inside the relevant idea's own M2/M4 ticket.
- Re-auditing world-module deployment status unless this epic starts significantly later than M1-M3 (the
  "all 20 used" finding could drift; it was already found to have drifted once before, in the direction of
  getting fixed, by `TCK-20260630-WORLD-DEPLOY-MODULES`).
- Building a `Country`-tier entity — item 6 is a finding to route to ideas 35/51's own scope discussion,
  not a deliverable of this epic.

## Acceptance Signal

- Ideas 45 and 14's M4/M2 tickets reflect the corrected, deeper scope (new schema field + compiler step)
  before implementation starts on either, not discovered mid-ticket.
- No new corpus-profile authoring work is scheduled for idea 44's testing needs in `crowded_frontier`,
  `hero_guild_routing`, or `resource_dense_basin` — confirmed unnecessary, don't duplicate it.
- Idea 32's corpus-testing work is explicitly sequenced after both idea 43 (M2) and idea 32 (M3) itself
  ship, not attempted earlier against an empty cohort model.

## References

- `docs/world/compiler_contract.md`, `docs/world/generator_contract.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/mechanics/regional_sovereignty.md`
- `tickets/done/TCK-20260630-WORLD-DEPLOY-MODULES.md`
- `docs/brainstorm/rpg_feature_atlas.html` — ideas 14, 32, 39, 43, 44, 45, 48, 51
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Idea 66 promotion, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — Idea 66 schema-migration
  ownership clarification, 2026-08-29
