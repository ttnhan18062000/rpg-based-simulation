---
status: active
layer: world
authority: P1
audience: agent
tags: [content, architecture]
---

# Epic Plan — RPG Design Roadmap, Milestone 8: World Corpus, Generation & Modules

**Status, re-verified 2026-09-06:** this epic has no buildable deliverable of its own (see its own
Out of Scope below) — it's an "informs" analysis whose findings feed M2-M4's real tickets. Of its 9
scope items, all are now resolved: items 1 and 7 (idea 43 seeding, idea 32 capacity-gating) were found
stale on re-check — both are real, live, and tested, corrected below with real citations; item 3
(idea 44's `settlement_capacity`) landed in a different technical shape than originally scoped, also
corrected below; items 2, 4, 5, 6, 8, 9 were already accurate. No tracking ticket is needed to "close"
this epic — its findings have all been consumed by the milestones that needed them.

**Tracking ticket:** `TCK-20260823-EPIC-RPG-M8-WORLD-CORPUS` (never created — not needed; this epic's
own scope is analysis/findings only, with no independent implementation to track, per
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

1. **Idea 43's insertion point — confirmed clean, low-risk. Landed, 2026-09-06 (re-verified):**
   `TCK-20260831-POPULATION-COHORT-SEEDING` (`tickets/done/`, DONE) implemented exactly this — real
   `_seed_population_cohorts()` function, called at compile time from `WorldCompiler.compile()` step 2
   (`src/worldbuilding/compiler.py:190,354`). Every compiled world now gets real, populated
   `RegionState.population_cohorts` at compile time — confirmed directly in source, not merely
   inferred from the ticket being closed (grepping the static `data/worlds/*/world.yaml` spec files
   for `population_cohorts` finds nothing, since it's a compile-time-derived runtime field, not
   declarative spec content — check the compiler's own seeding function, not the raw world files, to
   verify this).
2. **Idea 45's insertion point — closed, as-built, by idea 66 plus `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`.**
   This item originally read: "`CampState` is never constructed anywhere in production code,
   `WorldModuleSpec` has no `camp_recipes` field, and the compiler has no camp step at all — needs a new
   schema field plus a new compiler step." That framing is now stale and superseded, exactly as the
   original note below predicted. Idea 66's `Place` hierarchy already gave `WorldCompiler.compile()` a
   generic insertion point for `kind=CAMP`/`kind=NEST` `PlaceState` construction (both Direct and
   Composition content paths); `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` closed the remaining gap with only a
   narrow addition — a single optional `creature_kind: Optional[str]` field on `PlaceRecipeSpec`/`PlaceSpec`
   (CAMP/NEST-scoped, `None` by default) plus an additive branch inside the *existing* Place-construction
   loop that builds a companion `CampState`, keyed by the same `place_id`, when that field is set. No new
   `WorldModuleSpec` field and no new compiler step were needed. The bridge is opt-in and inert for all
   content on disk today (including `hero_guild_routing`'s `goblin_camp_place`) — migrating real content to
   set `creature_kind` remains a separate, future, deliberately-deferred step (see that ticket's
   Gameplay-Activation Risk Decision).
3. **Idea 14/44's `settlement_capacity` — resolved differently than originally scoped, 2026-09-06
   (re-verified).** No literal `settlement_capacity` field was ever added to `data/content/living/
   races.yaml` (confirmed — still zero hits repo-wide for that exact field name). Instead,
   `TCK-20260904-CAMP-NEST-CLASSIFICATION` (`tickets/done/`, DONE) consolidated ideas 44+45+46 and
   delivered the underlying City/Camp/Nest/Excluded classification as a documented, race-data-verified
   rule with its sole code projection `CampService.NEST_RACE_KINDS` (`src/world/camp.py`) — a derived
   classification, not a stored per-race field. M2's idea-14 ticket correctly did NOT add this field
   (it was explicitly scoped out there, per `rpg_m2_foundational_systems_epic.md`); the concept landed
   in M4 instead, in a different technical shape than this item originally anticipated.
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
7. **Idea 32 (reproduction pressure-gating near capacity) — both blockers cleared, 2026-09-06
   (re-verified against real code, not assumed from M3 having shipped).** This item's original framing
   ("no reproduction/capacity-gating mechanism exists in code at all") is now stale and was itself
   found via an incomplete search (grepping for the literal word "capacity" — the real mechanism uses
   "scarcity"/"migration_threshold" terminology instead, which a narrower search missed). The real,
   current state: both the natural-creature path (`src/world/camp.py:127-130`) and the humanoid path
   (`src/world/reproduction_humanoid.py:67-72`) gate reproduction on
   `compute_regional_scarcity(region) > migration_threshold` (default 0.7) — reproduction is skipped
   when a region is too scarce/crowded, landed as part of M3's Reproduction epic. The magical-demonic
   path (`src/world/calamity.py:60-66`) *intentionally* excludes this gate, with a real documented
   rationale ("a calamity-driven spawn is a world-threat escalation event, not a settlement/camp
   demographic signal") — a deliberate, symmetric design choice, not an oversight or gap. All three
   paths have real test coverage (`tests/unit/world/test_reproduction_humanoid_cadence.py`,
   `test_natural_creature_reproduction.py`, `test_calamity_magical_demonic_reproduction.py`). Combined
   with item 1's confirmation that `population_cohorts` is genuinely seeded at compile time, idea 32
   can now actually be corpus-tested against real compiled worlds — no further building needed before
   that testing could start.
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
   prevent. **High-level plan written up separately, 2026-09-02:**
   [`docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`](rpg_idea66_region_place_rebuild_plan.md)
   — full field-level schema, the two-stage pilot, and the `state_hash` recalibration procedure, ready for
   ticketing; this item stays as the sequencing note, that document is the scoping source.

## Out of Scope

- Building any of the schema/compiler-step gaps named above — this epic identifies where they belong,
  the actual building happens inside the relevant idea's own M2/M4 ticket.
- Re-auditing world-module deployment status unless this epic starts significantly later than M1-M3 (the
  "all 20 used" finding could drift; it was already found to have drifted once before, in the direction of
  getting fixed, by `TCK-20260630-WORLD-DEPLOY-MODULES`).
- Building a `Country`-tier entity — item 6 is a finding to route to ideas 35/51's own scope discussion,
  not a deliverable of this epic.

## Acceptance Signal

- **Satisfied, 2026-09-06 (re-verified against real code, not assumed from tickets being closed):**
  idea 43's compile-time seeding (item 1) and idea 32's capacity-gating (item 7) are both real, live,
  and tested — see those items' own corrected text above. Idea 45/44's insertion points landed via
  `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` and `TCK-20260904-CAMP-NEST-CLASSIFICATION` respectively, in a
  different technical shape than originally scoped (a documented classification rule, not a new
  schema field, for idea 44) but functionally equivalent to what this epic asked for.
- No new corpus-profile authoring work is scheduled for idea 44's testing needs in `crowded_frontier`,
  `hero_guild_routing`, or `resource_dense_basin` — confirmed unnecessary, don't duplicate it.
- Idea 32's corpus-testing work can now actually proceed (both its blockers cleared) — this epic itself
  builds nothing, so a real corpus-testing pass for idea 32 (if wanted) would be its own future ticket,
  not automatically implied by this acceptance signal being satisfied.

## References

- `docs/world/compiler_contract.md`, `docs/world/generator_contract.md`
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/mechanics/regional_sovereignty.md`
- `tickets/done/TCK-20260630-WORLD-DEPLOY-MODULES.md`
- `docs/brainstorm/rpg_feature_atlas.html` — ideas 14, 32, 39, 43, 44, 45, 48, 51
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Idea 66 promotion, temporal axis
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` — Idea 66 schema-migration
  ownership clarification, 2026-08-29
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` — idea 66's own dedicated
  high-level plan, 2026-09-02
