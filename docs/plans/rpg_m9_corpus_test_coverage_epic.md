---
status: active
layer: simulation
authority: P1
audience: agent
tags: [testing, simulation-quality, corpus]
---

# Epic Plan — RPG Design Roadmap, Milestone 9: World Corpus Test Coverage for New Features

**Tracking ticket:** `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (not yet created — scope-only, per
`docs/plans/rpg_design_roadmap.md`)
**Source:** Direct investigation of `docs/simulation_quality/corpus_tier_taxonomy.md`,
`config/simulation_quality/corpus_registry.yaml`'s `_worlds` key (21 real worlds),
`tests/simulation_quality/fixtures/grade_anchors.json` (84 committed run_keys),
`docs/simulation_quality/quality_scoring_contract.md` §5 (10 pillars, Scenario Registry SQ-01–24),
`docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry", all 32 stateful ideas), and
`docs/plans/rpg_m8_world_corpus_generation_epic.md`.
**Gate:** informs M1-M8 rather than blocking them — like M8, most findings are cheap reuse rather than
scope corrections; two findings (idea 66, ideas 53/55/58/62) are real gates for their own tickets, named
explicitly below and in the roadmap's Sequencing rules.

## Problem

M7 asks whether SimQ knows how to *grade* an event once it fires. M8 asks whether the world compiler can
*seed* an idea's content into a world at all. Neither asks the question in between: once an idea ships,
does a real SimQ corpus world actually exist to *exercise* it — end-to-end, in isolation, at scale, or as a
stable control — or does one need authoring? Without this, a shipped idea could be correctly coded,
correctly seedable, and correctly scorable by SimQ, and still never actually get graded in practice because
no world in the corpus ever triggers it.

This repo already has real, mature infrastructure for exactly this question —
`docs/simulation_quality/corpus_tier_taxonomy.md`'s four-tier framework (Unit/End-to-end/Stress/
Regression) plus a fifth, separate dimension (`tools/simq_long_run_observation.py`'s 5000-tick long-run
observation, for slow feedback loops no short calibration run would ever observe). This epic does not
invent a new testing framework — it classifies all 32 stateful/behavioral RPG ideas against the one that
already exists, the same way M8 classified them against the compiler's real insertion points.

## Scope (not yet broken into child tickets)

0. **Respect the corpus's own closed decision, don't appear to reopen it.** A real 2026-07-13 Coverage
   Decision Gate already ruled FACTION and INFORMATION coverage structurally saturated — no further
   candidate worlds, tier-authoring work closed against the existing table. Any new world this epic's
   findings call for is a *fresh* justification under this roadmap's own initiative, not a reopening of
   that gate. State this explicitly in any ticket that authors a new FACTION/INFORMATION-bearing world.

1. **Four ideas need a real Campaign run, not a corpus world — a distinct test-infrastructure category.**
   Ideas 53 (Inherited Reputation), 55 (Inherited Feuds), 58 (Dying Wish, in its full cross-generational
   form), and 62 (Generations Misremember) all require state to carry forward across multiple episodes
   (a birth, then reputation inheritance; a death, then feud transfer to an heir; Chronicle fidelity
   decaying across generations). No static compiled world can exercise any of them — they need
   `CampaignScorecardEvaluator`'s binary pass/fail evaluation, not SimQ's graduated 10-pillar model. Before
   any of these four ideas is ticketed, a real Campaign test plan (episode count, what triggers the
   inheritance/decay event, what the evaluator checks) needs deciding — this is a gate, not a nice-to-have.

2. **Idea 66 (Region/Place rebuild) has corpus-wide blast radius — the single largest testing-infrastructure
   risk in this epic.** It restructures `RegionState`/`RegionSpec` for every one of the corpus's 21 worlds
   simultaneously. `grade_anchors.json` enforces a tight regression tolerance (±1 letter-grade band and
   max(0.05, 0.20×score)) against all 84 committed run_keys — a structural compile-shape change at this
   scale will very likely trip that tolerance across many/most worlds even with zero real gameplay
   regression, purely from entity/region placement and content-distribution shifting under the hood.
   `corpus_tier_taxonomy.md`'s own Regression-tier policy already requires any deliberate content change to
   re-verify and re-commit anchors with attribution — idea 66 qualifies at a scale (21 worlds, 84 run_keys)
   no single prior ticket in the anchor history has touched at once. **Idea 66's own implementation ticket
   must budget a full `grade_anchors.json` recalibration pass as an explicit deliverable**, not something
   discovered mid-ticket when CI regression tests start failing corpus-wide.

3. **Several ideas already have a live SimQ scoring rule sitting idle — a narrower job than M7's general
   premise.** WORLD DYNAMICS' event table already scores `demographic_birth`/`demographic_mortality`
   (idea 32/43) and `region_transformed` (idea 48) with real +/- deltas and dormancy penalties already
   defined — these rules exist today with nothing to score, because the underlying mechanisms don't fire
   yet. For these three ideas specifically, the M7-adjacent work is "make the event actually fire," not
   "design a new scoring rule from scratch." (`camp_constructed`†, relevant to idea 45/66, is similarly
   already registered but the contract doc itself footnotes it as "not currently emittable" — a permanent
   dead event by design, not a gap, per this session's earlier finding.)

4. **Per-idea corpus-tier classification.** All 32 stateful ideas, tier + existing-world-or-new-authoring
   verdict + SimQ pillar:

   | Idea | Tier | Existing world / new need | SimQ pillar |
   |---|---|---|---|
   | 4 (Unified Modification) | **None needed** — regression tier already covers it | Any combat-enabled world; this is a storage refactor of already-exercised behavior | COMBAT (unaffected) |
   | 10 (Heir Assignment) | Unit | None exists; needs 4-6 entities, 1 region, a scripted/observed death | None yet, needs M7 |
   | 13 (Trade & Team-Up) | Unit | None exists; needs 2+ entities pre-seeded above the affection gate | None yet, needs M7 |
   | 14 (Species Classification) | End-to-end | Any race-diverse world (e.g. `frontier_living_world`) once the tier field exists | PROGRESSION |
   | 20 (Life Stages) | Unit + long-run observation | None exists; must use `simq_long_run_observation.py`, not a short calibration run — age transitions are too slow to observe otherwise | AGENCY&ACTION (needs M7 for event registration) |
   | 22 (Relationship Roles) | End-to-end (extend, don't author) | `highland_traverse` or `frontier_living_world` — both already SOCIAL-active | SOCIAL |
   | 30 (Possessions With History) | End-to-end (new) | None; genuinely depends on idea 13 shipping first (needs all 4 `acquired_method` paths) | NARRATIVE/ECONOMY, needs M7 |
   | 32 (Reproduction) | Stress or End-to-end | None until idea 43 seeds cohorts; then extend `frontier_living_world` | WORLD DYNAMICS — rule exists, idle |
   | 33 (Marriage) | Unit or extend an E2E world | `highland_traverse`/`frontier_living_world` (real SocialBond population) | SOCIAL, needs M7 for event |
   | 34 (Coming of Age) | Unit, shares idea 20's world | Same world as idea 20 — don't author twice | PROGRESSION, needs M7 |
   | 36/40 (Clan) | End-to-end | None built, but `crowded_frontier`/`frontier_marches` already contain unused `orc_clan_territory`-flavored content — likely zero new authoring once Clan ships | FACTION primary, SOCIAL secondary |
   | 37 (Race Relations) | Data-only, not tier-shaped | **Real gap: the corpus registry has no race-diversity dimension at all** — needs its own dedicated audit | None yet — new signal, not an existing SQ entry |
   | 39 (Affiliation Change) | End-to-end | `frontier_marches` (9 factions) once the trigger exists | FACTION |
   | 43 (population_cohorts seeding) | End-to-end | Any civilian_settlement world becomes valid the moment cohorts are non-empty — this is M8's compiler fix, not a corpus gap | WORLD DYNAMICS — rule exists, idle |
   | 44 (Settlement Capacity) | Stress | Confirmed zero new authoring — `hero_guild_routing` already composes City + hostile Camp content | WORLD DYNAMICS/ECONOMY |
   | 48 (Place-type transitions) | End-to-end + long-run | None; extend `lifecycle_full_coverage_world`'s existing 5000-tick precedent with a siege/destruction scenario | WORLD DYNAMICS — rule exists, idle |
   | 49 (Place-tied crafting materials) | End-to-end | Likely yes already — verify material/recipe coexistence in an existing resource world | ECONOMY |
   | 50 (Material-gated evolution) | Unit (new) | None; needs a small synthetic world, same shape as `unit_faction_tension` | PROGRESSION |
   | 51/52 (Country EXPAND + population-driven expansion) | End-to-end | `frontier_marches`, blocked on idea 43 regardless of tier | FACTION, WORLD DYNAMICS |
   | 53 (Inherited Reputation) | **Campaign-only** — see item 1 | none | Campaign evaluator, not SimQ pillars |
   | 54 (Guilt by Association) | End-to-end, gated on Clan | None; purpose-built world once Clan ships | FACTION/SOCIAL |
   | 55 (Inherited Feuds) | **Campaign-only** — see item 1 | none | Campaign evaluator |
   | 57 (Living Legend Feedback Loop) | Long-run observation | Any long-run world, run until fame accumulates | NARRATIVE primary, COGNITION secondary |
   | 58 (Dying Wish) | Long-run observation (simple form) / **Campaign-only (full cross-generational form)** — see item 1 | Any world with real deaths, run long enough | NARRATIVE-adjacent, needs M7 |
   | 60 (Reputations Are Local) | End-to-end | `frontier_extended`/`frontier_marches` (enough distinct locations); hard-blocked on the determinism-aware pass regardless of world choice | SOCIAL |
   | 62 (Generations Misremember) | **Campaign-only** — see item 1 | none | Campaign evaluator |
   | 63 (Belief/Religion) | Long-run observation, speculative | A world with real calamity/boss events; classification is genuinely underspecified, same caveat as its schema | None — idea itself too undefined to name one confidently |
   | 64 (The Empty Chair) | Unit (new) | None; needs a deliberately single-point-of-failure economic role, unlike every existing multi-entity-per-role world | ECONOMY |
   | 65 (Named Refugee Threads) | End-to-end/Stress, gated on 43+59 | `crowded_frontier`/`lifecycle_full_coverage_world` once dependencies land | WORLD DYNAMICS primary, SOCIAL secondary |
   | 66 (Region/Place rebuild) | Not a single tier — corpus-wide | See item 2 | WORLD DYNAMICS (foundational) |

5. **M8's "six real profiles" framing undercounted the available corpus.** `simq_scale_stress_seed42` and
   `lifecycle_full_coverage_world` are both real, recent (Aug 2026) Stress-tier worlds composing 8-12 modules
   each — richer test substrate than M8's own framing suggested. Whoever picks up items above referencing
   Stress-tier reuse should check these two directly, not just the three M8 originally named.

6. **Known scale ceiling, relevant if any future idea needs population beyond the current corpus max.**
   `WorldProceduralGenerator` — the only uncapped-population code path — is confirmed broken/unwired
   (`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`). The corpus's real current maximum is ~68 entities. Any
   idea whose test plan calls for a genuinely large population (none currently do, but idea 32/52's
   population-pressure mechanics could eventually motivate one) is blocked on that ticket, not just corpus
   authoring.

## Out of Scope

- Actually authoring any new corpus world, or writing any new SimQ signal rule — this epic identifies which
  ideas need one and what shape it should take; the authoring happens inside the relevant idea's own ticket
  or a dedicated corpus-authoring ticket, the same division M8 already established for compiler work.
- Designing the Campaign test plan for ideas 53/55/58/62 in full — item 1 names the gate; the actual
  episode-count/trigger/evaluator-check design is real scoping work for whichever ticket picks these up.
- Re-litigating the 2026-07-13 Coverage Decision Gate's FACTION/INFORMATION saturation finding — item 0
  respects it as closed.
- The race-diversity audit item 4's idea-37 row calls for — flagged as a real gap, not resolved here.

## Acceptance Signal

- All 32 stateful ideas have a named corpus-tier verdict (item 4's table), not left implicit.
- Ideas 53/55/58/62 have an explicit, written Campaign test plan before their tickets are scoped — not
  discovered as a blocker mid-implementation.
- Idea 66's ticket includes a budgeted `grade_anchors.json` recalibration pass as a stated deliverable.
- The idea-37 race-diversity gap is either resolved by a dedicated audit or explicitly deferred with a
  reason, not silently dropped.

## Open Questions

- Should the Campaign test plan for ideas 53/55/58/62 be one shared test (all four inheritance/decay
  mechanics exercised in one multi-episode run) or four separate ones? Leaning toward one shared run, since
  they share the same Reproduction/Campaign-boundary prerequisites, but not decided here.
- Idea 37's race-diversity audit: is this a small addition to the existing corpus registry's scale
  metrics, or does it need its own new registry dimension entirely? Not investigated in this epic's scope.

## References

- `docs/simulation_quality/corpus_tier_taxonomy.md` — the real tier framework this epic classifies against
- `config/simulation_quality/corpus_registry.yaml`, `tests/simulation_quality/fixtures/grade_anchors.json`
- `docs/simulation_quality/quality_scoring_contract.md` §5 — the 10 pillars, Scenario Registry
- `docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry") — per-idea proposed schemas
- `docs/plans/rpg_m7_simq_pillar_integration_epic.md`, `docs/plans/rpg_m8_world_corpus_generation_epic.md` —
  the two sibling epics this one sits between
- `docs/plans/rpg_design_roadmap.md`
