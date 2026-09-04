---
status: active
layer: simulation
authority: P1
audience: agent
tags: [testing, simulation-quality, corpus]
---

# Epic Plan — RPG Design Roadmap, Milestone 9: World Corpus Test Coverage for New Features

**Tracking ticket:** `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`)
**Source:** Direct investigation of `docs/simulation_quality/corpus_tier_taxonomy.md`,
`config/simulation_quality/corpus_registry.yaml`'s `_worlds` key (21 real worlds), `data/worlds/*/world.yaml`
and `data/worlds/*/world_compile_report.json`, `data/content/world_modules/*.yaml` (20 real modules),
`tests/simulation_quality/fixtures/grade_anchors.json` (84 committed run_keys),
`docs/simulation_quality/quality_scoring_contract.md` §5 (10 pillars, Scenario Registry SQ-01–24),
`src/domains/demographics/cohort.py` (real age-bracket thresholds), `tests/integration/scenarios/
test_campaign_runtime.py` and `CampaignScorecardEvaluator` (real Campaign test infrastructure),
`docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry", all 32 stateful ideas), and
`docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md`.
**Gate:** informs M1-M8 rather than blocking them — like M8, most findings are cheap reuse rather than
scope corrections; two findings (idea 66, ideas 53/55/58/62) are real gates for their own tickets, named
explicitly below and in the roadmap's Sequencing rules.

## Problem

**2026-08-29 review note:** this epic's own finding under item 4 (Ideas 20/34) — the long-run tool's default
5000-tick run can't even reach the real 7000-tick elder threshold — is the same class of gap the
temporal-axis proposal names in its own §9.7 (existing 5,000-tick runs can't observe elder thresholds, let
alone a 72,000-tick season or 288,000-tick year, once fantasy-year-scaled aging lands). If that proposal's
calendar work reaches ticket scope, this epic's scenario horizons should extend to daily/seasonal/annual/
lifespan/multi-generation coverage rather than relying on one fixed tick count — see the parent roadmap's
"Temporal axis" section. Not resolved here; flagged as a forward-looking extension of this epic's existing
mandate.

M7 asks whether SimQ knows how to *grade* an event once it fires. M8 asks whether the world compiler can
*seed* an idea's content into a world at all. Neither asks the question in between: once an idea ships,
does a real SimQ corpus world actually exist to *exercise* it — end-to-end, in isolation, at scale, or as a
stable control — or does one need authoring? Without this, a shipped idea could be correctly coded,
correctly seedable, and correctly scorable by SimQ, and still never actually get graded in practice because
no world in the corpus ever triggers it.

This repo already has real, mature infrastructure for exactly this question —
`docs/simulation_quality/corpus_tier_taxonomy.md`'s four-tier framework (Unit/End-to-end/Stress/
Regression) plus a fifth, separate dimension (`tools/simq_long_run_observation.py`'s long-run observation,
for slow feedback loops no short calibration run would ever observe) — plus, for four ideas, real Campaign
test infrastructure (`CampaignOrchestrator`/`CampaignScorecardEvaluator`) distinct from both. This epic does
not invent a new testing framework — it classifies all 32 stateful/behavioral RPG ideas against the ones
that already exist, and (per a direct follow-up request) specifies each one concretely: real world names,
real module compositions, real entity/region counts, real trigger sequences, and real assertable checks —
not tier labels with a one-line gesture.

## Scope (not yet broken into child tickets)

0. **Respect the corpus's own closed decision, don't appear to reopen it.** A real 2026-07-13 Coverage
   Decision Gate already ruled FACTION and INFORMATION coverage structurally saturated — no further
   candidate worlds, tier-authoring work closed against the existing table. Any new world this epic's
   findings call for is a *fresh* justification under this roadmap's own initiative, not a reopening of
   that gate. State this explicitly in any ticket that authors a new FACTION/INFORMATION-bearing world.

1. **Four ideas need a real Campaign run, not a corpus world — with a real, previously-undiscovered
   evaluator gap.** Ideas 53 (Inherited Reputation), 55 (Inherited Feuds), 58 (Dying Wish, full
   cross-generational form), and 62 (Generations Misremember) all require state to carry forward across
   multiple episodes. Real Campaign test infrastructure already exists
   (`tests/integration/scenarios/test_campaign_runtime.py`'s `SimulationScenarioDefinition`, run via
   `CampaignOrchestrator`; a real 3-episode precedent already exists,
   `test_hero_pursues_craft_upgrade_across_three_episodes`). `EntityCarryForward.reputation` already maps
   directly to `entity.social.public_reputation` and already carries forward every episode.
   `NEMESIS_EPISODE_COUNT = 2` (`grief_urgency.py`) — a nemesis relation needs conflict repeated across 2+
   episodes before it registers. **But `CampaignScorecardEvaluator.evaluate()` checks exactly 7 fixed
   pass/fail fields today** (`self_model_usage`, `route_decision_quality`, `combat_learning`,
   `information_learning`, `reward_conversion`, `cooperation_usage`, `world_feedback_usage`) — **none of
   which touch reputation, nemesis, or Chronicle fidelity.** Testing these four ideas needs new scorecard
   fields added to the evaluator itself, not just new episodes run through the existing one.

   **Concrete shared test plan, base world `frontier_living_world`** (`hero_guild_perspective`,
   `tick_limit: 400`/episode):
   - *Episode 1:* seed a Hero (`entity_id=1`) with `public_reputation=1.6` and `heir_entity_id` pointing to a
     second Hero-role entity in the same faction (idea 10). Trigger a betrayal event against a
     `goblin_camp_conflict` antagonist to start nemesis accrual (1 of 2 episodes needed).
   - *Episode 2:* repeat the same antagonist conflict (`NEMESIS_EPISODE_COUNT=2` now satisfied,
     `NemesisRelationImporter` fires). Entity 1 dies mid-episode via a scripted lethal hit. Assert: heir
     inherits inventory (idea 10); `inherited_reputation_seed` on the heir ≈ 1.6 × idea 53's decay-seed
     fraction (not yet specified anywhere — flag as an open numeric decision for idea 53's own ticket);
     nemesis relation transfers to the heir at reduced weight (idea 55).
   - *Episode 3:* if idea 58 is wired into the same run, assert the heir's `dying_wish_intention` is
     non-null and targets the episode-2 nemesis.
   - *Episode 4:* compile Chronicle across episodes 1-3; assert `ChronicleRecord.fidelity` for the death
     event is below 1.0 (idea 62), and the heir's inherited reputation has decayed further toward neutral
     per idea 53's `reputation_decay_rate`.
   - *Evaluator change needed:* add `reputation_inheritance_check` and `nemesis_transfer_check` fields to
     `CampaignScorecard`; fail if a death with a live heir occurs and `inherited_reputation_seed` is unset.

2. **Idea 66 (Region/Place rebuild) — corpus-wide migration, not a single test world.** It restructures
   `RegionState`/`RegionSpec` for every one of the corpus's 21 worlds simultaneously.
   `grade_anchors.json`'s tolerance (±1 letter-grade band, `max(0.05, 0.20×score)`) across all 84 committed
   run_keys will very likely trip on a structural compile-shape change at this scale even with zero real
   gameplay regression.

   - **Two-stage pilot, not one.** *Stage A* (smallest correctness check): `unit_information_source` — 16
     entities, 1 region (`frontier_village_core` + `hero_adventurers`). One region becomes one `Region`
     containing exactly one `Place(kind=CITY)`; nothing else should change, and the diff is trivially
     hand-verifiable. *Stage B* (first real mixed-content check): `hero_guild_routing` — 4 regions
     (City + `goblin_camp` wilderness + `ruins_mystery_quest` + `mountain_pass`), already proves the
     migration handles non-uniform region kinds before rolling out to the remaining 19 worlds.
   - **Real recalibration procedure, using infrastructure that already exists.** Every
     `world_compile_report.json` already carries a `state_hash` field. Recompile each world under the new
     schema and diff `state_hash` against the committed one first — an unchanged hash proves a lossless
     migration for that world with no SimQ grade run needed at all. Only for worlds whose hash *does* change
     does a full `grade_anchors.json` re-run and manual grade-shift triage apply (real vs. compile-shape
     noise). Budget this as a genuine per-world triage pass across 21 worlds/84 run_keys, not a single batch
     diff.
   - **No true parallel-run is feasible.** `WorldCompiler.compile()` is a single synchronous pass with no
     existing hook for running two schema versions side-by-side. The practical equivalent is sequential: old
     schema's `state_hash` + grades are already recorded as the baseline for all 21 worlds today; compile
     under the new schema and diff against that recorded baseline. A staged hard cutover (Stage A → Stage B
     → remaining 19), not a live comparison.

3. **Several ideas already have a live SimQ scoring rule sitting idle.** WORLD DYNAMICS' event table already
   scores `demographic_birth`/`demographic_mortality` (idea 32, gated on idea 43) and `region_transformed`
   (idea 48) with real deltas and dormancy penalties defined — these rules exist today with nothing to
   score. For these, the work is "make the event fire," not "design a new rule." **The full expected-event
   registry — real event names, payloads, triggers, and pillar/scenario mapping for all 32 ideas — now lives
   in `docs/brainstorm/rpg_expected_schemas.html`'s "Expected Events" section, not duplicated here.** That
   section also answers whether any idea needs a genuinely new SimQ pillar (checked directly: no — 5 new
   scenario entries within existing pillars are needed, SQ-25 through SQ-29, but no 11th pillar), and found
   one standalone gap independent of this epic's own ideas: no `entity_evolved` event exists today even for
   the already-shipped XP-only evolution path.

4. **Per-idea corpus-tier classification and concrete world spec.**

   **Idea 4 (Unified Modification) — no new world.** A storage-shape refactor of already-exercised behavior.
   Assertion: after the refactor, the 2 real Regression-tier worlds (`urban_political`, `simq_routing_test`,
   both 30 entities/3 regions) keep their committed COMBAT-pillar scores within `grade_anchors.json`'s
   existing tolerance. Pure regression check.

   **Ideas 10 (Heir Assignment) + 13 (Trade & Team-Up) — one shared new Unit-tier world.** Compose
   `frontier_village_core` (1 region "hometown": village_worker×8, frontier_guard×3, traveling_merchant×1,
   village_blacksmith×1) + `hero_adventurers` (3 Hero-role entities, `hero_guild` faction) = 16 entities, 1
   region, 3 factions — matches `unit_selfmodel_pilot`'s real recipe exactly. For idea 10: pre-seed one
   Hero's `SocialBond.sentiment` toward `village_blacksmith` above the (not-yet-decided — flag as open)
   heir-eligibility threshold, trigger a *scripted* lethal hit (natural old-age death at `age_ticks ≥
   10,000` exceeds even the long-run tool's range, so scripting is the practical path), assert
   `heir_entity_id` equals the highest-sentiment civilian and inventory transfers. For idea 13: gate 2 of the
   3 Heroes' mutual sentiment above the affection threshold, leave the 3rd as a negative control; assert
   `ResourceTransferIntent(source_kind=ENTITY)` succeeds only for the gated pair, and `TeamUpInvite` reaches
   `ACCEPTED` only between them.

   **Ideas 20 (Life Stages) + 34 (Coming of Age) — same 16-entity world, long-run tooling, real timing
   bug found.** Confirmed real thresholds directly (`src/domains/demographics/cohort.py:50-88`):
   `get_age_bracket()` defines young (age_ticks<3000), adult (<7000), elder (≥7000);
   `compute_elder_attribute_update()` applies STR/AGI×0.7, VIT/END×0.5, WIS/CHA×1.3 at the elder boundary.
   **`tools/simq_long_run_observation.py` defaults to `--ticks 5000` — below the 7000-tick elder
   threshold, so its default run would never observe an ADULT→ELDER transition at all.** Any ticket testing
   idea 20 must use `--ticks 8000` minimum or the test silently proves nothing. Initialize 1-2 entities'
   `age_ticks` near 0 (instead of default-adult) so both the CHILD→ADULT and the real 7000-tick elder
   boundary are observable in one run. Assert `identity.life_stage` flips at the new CHILD→ADULT threshold,
   elder deltas apply at 7000, and idea 34's `archetype_locked` flips false→true specifically at
   CHILD→ADULT. **Open question surfaced, not previously flagged: `get_age_bracket()`'s young/adult/elder
   string system and `IdentityComponent.life_stage: LifeStage` (CHILD/ADULT/ELDER enum) may be two
   overlapping age-tier systems — reconcile before idea 20 is ticketed, not just tested.**

   **Idea 22 (Relationship Roles) — zero new world, add one assertion.** `highland_traverse` (18 entities, 5
   regions) or `frontier_living_world` (49 entities, 8 regions, 6 factions) — both already SOCIAL-active. No
   new authoring; add one assertion to either world's existing 200-tick calibration run: after a
   repeated-grudge sequence matching the real `nemesis_ids` promotion pattern (grudge ≥ 3.0), assert
   `SocialBond.role` lands on the matching classification via a **direct end-of-run field read** — a 4th
   struct field won't move `grade_anchors.json`'s pillar-score tolerance on its own, so this must be a field
   check, not a score-drift check.

   **Idea 30 (Possessions With History) — extend `frontier_living_world`, blocked on idea 13.** Already has
   LOOT (`goblin_camp_conflict`/`undead_battlefield`) and CRAFTED (`old_mine_resource_loop`) paths; GIFT
   needs idea 13. Track one named `ItemInstance` (e.g. a weapon looted from `undead_battlefield`) through
   LOOT→CRAFTED(upgrade)→GIFT(idea 13)→INHERITED(idea 10, if the holder dies later in the same run) across
   one long-run session; assert `owner_history` accumulates all 4 `acquired_method` values in order.

   **Idea 14 (Species Classification) — zero new world.** `frontier_living_world` already spans the race
   diversity needed (human/elf/dwarf townsfolk, goblins, wolves, undead) to exercise both `tool_user`-tagged
   and non-`tool_user` races. Assert every entity's `intelligence_tier` matches its race's `natural_traits`
   (`tool_user` → `high`), and low-tier entities (wolves) are excluded from coming-of-age/Progression-Planner
   eligibility.

   **Idea 32 (Reproduction) + 43 (population_cohorts seeding) — zero new world, blocked in sequence.**
   *Correction: idea 43 has no standalone schema of its own — it's a field inside ideas 32's and 66's
   schemas, "populate an existing field," not a separate design.* `frontier_living_world`'s
   `world_compile_report.json` today has no cohort key at all (confirmed field list:
   `world_id/seed/entity_count/region_count/resource_node_count/building_count/quest_count/
   distinct_populated_factions/warnings/compile_duration_ms/state_hash`). Once seeded, run past the existing
   200-tick calibration window and assert `demographic_birth` fires at least once, `population_pressure_gate`
   reads `migration_threshold=0.7` correctly, and `genetic_inheritance_weight` (0.8–1.3) is applied to at
   least one child vs. parent average.

   **Idea 33 (Marriage) — zero new world.** `highland_traverse`: add `MarriageState(status=PROPOSED)` between
   the two highest-`SocialBond.sentiment` entities (reusing `RelationshipService`'s real per-pair data);
   assert transition to `ACCEPTED` at `familiarity ≥ 0.6` and `married_tick` gets set; assert exactly 1
   `MarriageState` record after a 200-tick run.

   **Ideas 36/40 (Clan) — zero new world.** `frontier_marches` (9 factions): retarget the existing, real,
   currently-unused `orc_clan_territory`-flavored module content into a real `ClanState` with
   `member_entity_ids` = all orc-faction entities in that module, `home_region_ids` = the 2 regions it
   spans. Assert `len(member_entity_ids) ≥ 3` and a defection event (Group's real precedent) removes exactly
   one member.

   **Idea 37 (Species Relations) — confirmed real gap, no world can be specified yet.** The corpus registry has
   no race-diversity dimension at all; a test world can't be designed without the dedicated audit item 4's
   own row already calls for.

   **Idea 39 (Affiliation Change) — zero new world.** `frontier_marches`: pick one entity from the smallest
   of the 9 factions, trigger `IdentityUpdate(faction_set=<a neighboring faction>)`, assert `identity.faction`
   changes and — per the idea's own explicit design — `SocialBond` entries with old-faction members do NOT
   auto-degrade without a separate event.

   **Idea 44 (Settlement Capacity) — zero new world, tier corrected to Unit.** `hero_guild_routing` (31
   entities, 4 regions, tier `unit` — corrects this epic's earlier Stress-tier label) composes
   `frontier_village_core` (City: town_hall/shop/blacksmith/inn/healer_hut) alongside `goblin_camp_conflict`.
   **Real caveat: the `goblin_camp` region itself is `type: wilderness, tags: [forest], hazard_level: 3.0` —
   camp-themed in name only, not a real `CampState` instance** (its `goblin_camp_place` content sets no
   `creature_kind`, the opt-in field `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` added — so `WorldCompiler.compile()`
   constructs no companion `CampState` for it, even though the compiler CAN now do so in general for content
   that opts in). This world tests the City-vs-hostile-population settlement-capacity split idea 44 needs,
   but does NOT exercise real `CampState`/idea-66-`Place(kind=CAMP)` machinery — that needs `goblin_camp_place`
   migrated to declare `creature_kind` first (deliberately deferred by the bridge ticket). Assert
   `settlement_capacity` resolves `FULL_SETTLEMENT` for the `frontier_village_core` region and
   `NONE`/`CAMP_ONLY` for `goblin_camp`.

   **Idea 45/46/47 (Camp/Nest/Lair) — subsumed under idea 66's Place model**, no separate world spec; see
   idea 66 above and idea 44's caveat.

   **Idea 48 (Place-Type Transitions) — extend `lifecycle_full_coverage_world`.** 41 entities, 8 regions,
   tier `stress`, 7 distinct factions — the richest faction-tension surface in the corpus. Author a
   `faction_tension_overrides` entry driving sustained conflict against the `frontier_village_core` region;
   this world's only committed run_key is 200t, so a siege reaching completion needs a separate, longer
   manual run via the long-run tooling, outside `grade_anchors.json`. Assert `Place.kind` flips CITY→RUIN and
   `region_transformed` fires (the already-idle WORLD DYNAMICS rule). **Real risk to carry into the
   assertion design:** this world's own prior investigation already found sustained COMBAT pressure starves
   SOCIAL/GUILD goal-selection for the whole run — a siege scenario compounds that. Tolerate SOCIAL/GUILD
   dropping in this specific test; don't treat it as a false regression.

   **Idea 49 (Place-Tied Crafting Materials) — zero new authoring, confirmed concretely.**
   `mountain_pass.yaml` (already in `hero_guild_routing`'s module list) defines real place-tied resources
   (`iron_vein: 4`, `frost_shard_cluster: 2`). Assert a recipe gated on `frost_shard` only completes when the
   crafting entity is at/near `mountain_pass_zone`. (`moon_resin_tree` exists in `moon_cult_ruins.yaml`, not
   currently composed into any registry world — adding it to a world's module list is a one-line config
   change, not new content authoring, if that specific material is wanted.)

   **Idea 50 (Material-Gated Evolution) — new Unit-tier world needed.** Matching `unit_faction_tension`'s
   real shape (18 entities, 3 regions, 5 factions): compose `frontier_village_core` + `mountain_pass` (for
   `frost_shard_cluster`) only. Seed one entity at XP just below a threshold (10/25/50) carrying
   `frost_shard`, run to the threshold tick, assert `alt_outcome_kind` fires instead of the default XP-only
   path; run a sibling entity without the material in the same world for direct comparison.

   **Ideas 51/52 (Country EXPAND + population-driven expansion) — zero new world, blocked on idea 43.**
   `frontier_marches`: once unblocked, assert `EXPAND_TERRITORY` fires for the faction with the highest
   `population_cohorts` scarcity signal, targeting an adjacent unclaimed region.

   **Idea 54 (Guilt by Association) — new world needed, gated on Clan.** 2 Clans of 4 members each; one
   member of Clan A commits a witnessed betrayal; assert a stranger's trust delta toward an *unmet* Clan A
   member is measurably lower than baseline.

   **Idea 57 (Living Legend Feedback Loop) — extend `lifecycle_full_coverage_world`'s existing 5000-tick
   run.** Seed one entity's `heroism_score` above the fame threshold early; assert a Townsperson entity's
   Motivation & Doctrine route bias measurably shifts toward adventuring after the fame-perception event, via
   the real Perception budget (10 signals) as the propagation mechanism.

   **Idea 60 (Reputations Are Local) — zero new world, hard-blocked regardless.** `frontier_extended`
   (largest, most regions): once the per-region shape exists, read the same entity's `public_reputation`
   from 3 different regions, assert 3 distinct values rather than one global float. Blocked on the
   determinism-aware pass no matter which world is used.

   **Idea 63 (Belief/Religion) — not concretely specifiable.** The schema itself is flagged underspecified;
   no real anchor exists yet to build a scenario against. `lifecycle_full_coverage_world`'s real
   calamity/boss events are the plausible substrate once the idea is grounded further, not a confirmed spec.

   **Idea 64 (The Empty Chair) — new Unit-tier world needed.** 1 region, exactly 1 SHOPKEEPER-role entity —
   no existing world has this; all have redundant role coverage. Kill it mid-run; assert
   `EconomicVacancyEvent` fires and either an apprentice auto-promotes or a market-price distortion is
   observable within N ticks.

   **Idea 65 (Named Refugee Threads) — zero new world, blocked on 43+59.** `crowded_frontier` (6 factions, 4
   regions): trigger a hostile-pressure event in one region, assert a civilian's `identity.home_region_id`
   is set to the fled-from region and `displaced_tick` is recorded.

5. **M8's "six real profiles" framing undercounted the available corpus.** `simq_scale_stress_seed42` and
   `lifecycle_full_coverage_world` are both real, recent (Aug 2026) Stress-tier worlds composing 8-12 modules
   each. Anywhere above referencing Stress-tier reuse should check these two directly.

6. **Known scale ceiling.** `WorldProceduralGenerator` — the only uncapped-population code path — is
   confirmed broken/unwired (`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`). Real current corpus max is
   ~68 entities. Any idea whose test plan eventually calls for genuinely large population (none do today,
   but ideas 32/52's pressure mechanics could motivate one) is blocked on that ticket, not just authoring.

## Out of Scope

- Actually authoring any new corpus world, or writing any new SimQ signal rule, or adding the new
  `CampaignScorecardEvaluator` fields — this epic specifies what's needed; the building happens inside the
  relevant idea's own ticket or a dedicated corpus-authoring ticket, the same division M8 established for
  compiler work.
- Deciding idea 53's exact `reputation_decay_rate`/seed-fraction numeric values — flagged as open, resolved
  in that idea's own ticket.
- Re-litigating the 2026-07-13 Coverage Decision Gate's FACTION/INFORMATION saturation finding.
- The race-diversity audit item 4's idea-37 row calls for — flagged as a real gap, not resolved here.
- Reconciling the `get_age_bracket()`/`LifeStage` possible-duplicate age-tier systems flagged under idea
  20 — a real finding, not this epic's to resolve.

## Acceptance Signal

- All 32 stateful ideas have a named corpus-tier verdict and a concrete world spec (item 4), not a tier
  label alone.
- Ideas 53/55/58/62 have the shared 4-episode Campaign test plan and the `CampaignScorecardEvaluator` field
  additions named as explicit prerequisites before any of the four is ticketed.
- Idea 66's ticket includes the 2-stage pilot (Stage A/B) and the `state_hash`-first recalibration procedure
  as stated deliverables, not discovered mid-implementation.
- The idea-37 race-diversity gap and the idea-20 age-tier-duplication question are either resolved or
  explicitly deferred with a reason, not silently dropped.

## Open Questions

- Is the Campaign test plan for ideas 53/55/58/62 one shared 4-episode run (as specified above) or four
  separate ones? This epic specifies one shared run since they share the same Reproduction/episode-boundary
  prerequisites — worth confirming before ticketing.
- Idea 37's race-diversity audit: a small addition to the existing corpus registry's scale metrics, or a
  wholly new registry dimension? Not investigated in this epic's scope.
- `get_age_bracket()`'s string-based age tiers vs. `LifeStage`'s enum — one system or two, and if two,
  which one idea 20's trigger should actually write to? Not resolved here.

## References

- `docs/brainstorm/rpg_expected_schemas.html`'s "Expected Events" section — the full event-type/payload/
  trigger/pillar registry for all 32 ideas, referenced but not duplicated in item 3 above
- `docs/simulation_quality/corpus_tier_taxonomy.md` — the real tier framework this epic classifies against
- `config/simulation_quality/corpus_registry.yaml`, `tests/simulation_quality/fixtures/grade_anchors.json`,
  `data/worlds/*/world_compile_report.json` (real `state_hash` field used in idea 66's recalibration plan)
- `docs/simulation_quality/quality_scoring_contract.md` §5 — the 10 pillars, Scenario Registry
- `tests/integration/scenarios/test_campaign_runtime.py`, `CampaignScorecardEvaluator` — real Campaign test
  infrastructure used in item 1's shared test plan
- `src/domains/demographics/cohort.py` — real age-bracket thresholds used in idea 20/34's spec
- `docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry") — per-idea proposed schemas
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`, `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` —
  the two sibling epics this one sits between
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, temporal axis
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` — §9.7 test-horizon conflict,
  echoing this epic's own 5000-tick/elder-threshold finding
