---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: investigation
tags: [epic-scoping, simulation-quality, world-content, feature-flags, pre-ticket]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-TIERS-EPIC

Pre-ticket epic-scoping pass (produced before the epic ticket ID existed, under the working name
`EPIC-SCOPE-full-feature-world-coverage`; this file/folder was renamed to the real ticket ID once
the epic and its 10 child tickets were created). No code changed by this investigation itself.
Produced in response to a product-philosophy statement that overrides the prior narrower "activate
one pillar in one world" approach: world data should eventually exercise every feature the engine
supports, across worlds of deliberately varied scale/composition, so SimQ scoring can surface
what's weak — not just what's already strong.

**Resulting tickets:** `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` (this ticket) + 10 child tickets under
`tickets/todos/simq-corpus-tiers/` (see that folder's `SEQUENCE.md`).

PHASE_TS: 2026-07-04T12:03:56Z

## Context search performed (per CLAUDE.md hard rule)

1. `mcp__knowledge-search__search_docs` (query: compile-time pillar activation / feature flag /
   world content seeding / FACTION / INFORMATION / hazard_kind) — surfaced
   `docs/simulation_quality/eval_matrix_results.md`, `TCK-20260702-SIMQ-EVAL-MATRIX`,
   `TCK-20260629-SIMQ-EMIT-WORLD`, `TCK-20260702-SIMQ-UPLIFT2-FACTION`,
   `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`, `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC` (Pattern 6
   authoring ticket) as the primary prior-work trail.
2. `graphify query "world content seeding feature flag activation per-world FACTION INFORMATION
   AGENCY"` — 2786-node BFS traversal rooted at `Faction`/the FACTION ticket's tension-transition
   test and `test_real_world_modules_load_from_data_content()`; confirmed the schema/state
   backbone (`WorldSpec`, `WorldCompositionSpec`, `NormalizedWorldComposition`,
   `WorldAssemblyResolver`, `FactionState`, `SelfModelBundle`) as the structural surface this epic
   would touch — no additional undiscovered edge contradicted the doc trail.

Both tools confirmed the same picture the ticket bodies later gave in full detail; raw grep/Read
was used only as follow-up per the Hard Rules.

---

## 1. Inventory of compile-time-gated / feature-flag-gated mechanics

All four fields below share the exact same architecture (Pattern 6,
`docs/guidelines/design_patterns.md`): a `WorldSpec`/`WorldCompositionSpec`/
`NormalizedWorldComposition` field with `default_factory=list`/`dict`, resolved by
`WorldAssemblyResolver.assemble()`, constructed into a real domain object by
`WorldCompiler.compile()`, and passed into the single `AuthoritativeState(...)` constructor call.
Confirmed via direct read of `src/worldbuilding/schema.py` (`WorldSpec`, lines 215-237) and
`src/worldassembly/schema.py` (`WorldCompositionSpec` lines 21-61, `NormalizedWorldComposition`
lines 151-189) that **these four are the complete set** — no other field on either class follows
this shape undiscovered. (`hazard_kind`/`hazard_level` on `RegionSpec` is a required-with-default
region field already populated in every world post the P2-B/hazard-kind staleness fix
(`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`) — it is not a coverage gap of this class.)

| Mechanic | Pillar(s) | Field / Flag | Defined at | Worlds w/ REAL content | Worlds w/ inert default |
|---|---|---|---|---|---|
| Faction tension seeding | FACTION | `faction_tension_overrides: Dict[str,float]` (composition-level override-merge, applied after catalog+module merge) | `src/worldassembly/schema.py:40` (`WorldCompositionSpec`) / `:168` (`NormalizedWorldComposition`); underlying `FactionSpec.initial_tension_level` at `src/worldbuilding/schema.py:52` | **urban_political only** — 2 of 16 catalog factions overridden (`bandit_company: 0.5`, `town_council: 0.5`) | dungeon_crawl, frontier_extended, frontier_living_world, generated_frontier_3_42, highland_traverse, sandbox_world, simq_routing_test, swamp_border_world, wilderness_survival — all 16 factions at `initial_tension_level: 0.0` (confirmed by grep across all `resolved/world.resolved.yaml`) |
| Information source profiles | INFORMATION | `information_source_profiles: List[InformationSourceProfileSpec]` | `src/worldbuilding/schema.py:226`; mirrored `src/worldassembly/schema.py:44`/`:172` | **urban_political only** — 1 source (`town_notice_board`, guide) | all other 9 worlds — empty list |
| Pending information responses | INFORMATION | `pending_information_responses: List[PendingInformationResponseSpec]` | `src/worldbuilding/schema.py:227`; mirrored `:48`/`:176` | **urban_political only** — 1 entry (`pop_0`, `bandit_road_danger`, `KNOWN_FACT`) | all other 9 worlds — empty list |
| Self-model / Branch B seed events | Cognition-adjacent (self-model `unknowns`; feeds `InformationBeliefPhase` Branch B, INFORMATION-adjacent) | `pending_self_model_information_events: List[PendingSelfModelInformationEventSpec]` | `src/worldbuilding/schema.py:228`; mirrored `:54`/`:182` | **urban_political only** — 1 entry (`pop_1`, `unknown`, `material.moon_resin.source`) | all other 9 worlds — empty list. **Also**: even in urban_political this is proven reachable only via test-scoped `ENABLE_SELF_MODEL_COGNITION=ON` override — the field being populated is necessary but not sufficient (see §3) |
| Adventure routing / AGENCY | AGENCY | `ENABLE_ADVENTURE_ROUTING` (`FeatureMode`, default `OFF`) | `src/domains/optimization/feature_flags.py:16`; gate applied in `src/engine/pipeline.py` (`run_phase("adventure_decision", ..., "ENABLE_ADVENTURE_ROUTING")`), short-circuits `AdventureDecisionPhase.apply()` | **simq_routing_test only** — and NOT via world content or a per-world profile flag: `tools/evaluate_simq.py` (lines ~35-86) hardcodes the 3 `simq_routing_test_seed*` scenario names and injects the env var `ENABLE_ADVENTURE_ROUTING=ON` around only those runs, then restores the prior value | all 9 other worlds, all seeds, all tick counts — ruled **archetype-correct, not a gap** by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` |
| Belief assimilation trigger | INFORMATION | `ENABLE_BELIEF_ASSIMILATION` (`FeatureMode`, default `OFF`) | `src/domains/optimization/feature_flags.py:18` | **urban_political only** — but via a *different, already-generalizable* mechanism: `config/simulation_quality/profiles/urban_political.yaml` has a `feature_flags:` block setting `ENABLE_BELIEF_ASSIMILATION: "ON"` (and `ENABLE_SOCIAL_COOPERATION: "ON"`). This is a **per-world profile YAML**, not a harness special-case — any world can flip this flag today with zero code changes | all other worlds — flag absent from their profile YAML (`default.yaml`, `dungeon_crawl.yaml`, `simq_routing_test.yaml` carry no `feature_flags:` key) → defaults OFF |
| `RolloutProfileManager` CLASS_B/CLASS_C matrices | AGENCY + INFORMATION + self-model (combined) | `CLASS_B`/`CLASS_C` `RolloutProfile.enabled_phases` (both include `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` + `ENABLE_BELIEF_ASSIMILATION` simultaneously) | `src/domains/optimization/rollout_profiles.py:56-86` | **none** — confirmed still true: `grep -rn "RolloutProfileManager"` outside its own module hits only its own test files (`tests/unit/config/test_phase10_rollout_profiles.py`, `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`). No `src/` call site, no `config/`, no `data/worlds/` entry references it. **"Committed but unwired into any live default" is still accurate** as of 2026-07-04. This is also the exact flag combination (`ENABLE_SELF_MODEL_COGNITION` + `ENABLE_BELIEF_ASSIMILATION` ON together) that the Branch B ticket found causes `InformationBeliefPhase.apply()` to clobber `self_model`'s same-tick write if the merge fix weren't already in place — i.e. CLASS_B/CLASS_C would have exercised the exact bug Branch B fixed, had they ever been wired live |
| Faction relationships catalog density | FACTION (cross-faction encounter variety) | `data/content/social/faction_relationships.yaml` (global catalog, not per-world) | `data/content/social/faction_relationships.yaml` | Global catalog: **34 relationship entries** covering **20 of 120 possible undirected faction pairs (16.7%)** across 15 of 16 factions (`neutral` has zero). This is P2-D in `docs/plans/audit_fix_plan.md` — currently `UNVERIFIED`/stale (last said "14 defined"); actual count is now 34/20-pairs, still well under the ticket's own 50%-coverage target | N/A — global, not per-world |

**Key architectural asymmetry surfaced (relevant to §3):** FACTION/INFORMATION/self-model seeding
and `ENABLE_BELIEF_ASSIMILATION` all go through **generalizable, already-existing mechanisms**
(world.yaml content fields, or a per-world `config/simulation_quality/profiles/<world>.yaml`
`feature_flags:` block). `ENABLE_ADVENTURE_ROUTING`, by contrast, is currently activated **only**
via a harness-level hardcoded scenario-name special case in `tools/evaluate_simq.py` — there is no
per-world profile-YAML path wired for it today, even though the mechanism that would carry it
(the same `feature_flags:` block already used for `ENABLE_BELIEF_ASSIMILATION`) already exists and
works. Turning AGENCY on broadly is therefore not blocked by a missing mechanism — the mechanism is
one line away from being reusable — it is blocked by the DA ruling being a deliberate scope
decision, not a technical gap.

---

## 2. World / scenario scale diversity

All 10 worlds under `data/worlds/` (excludes `world_index.json`, which is an index file, not a
world). Counts from `world_compile_report.json` (entity/region/resource/building/quest counts) and
`resolved/world.resolved.yaml` (module composition, populated-faction count). "Factions in
catalog" is a **global constant (16) for every world** — `AuthoritativeState.factions` is always
built from the full catalog regardless of content, so it is not a real per-world scale axis today.
The meaningful per-world FACTION-scale axis is **distinct factions actually assigned to a
population** (2-9), shown separately.

| World | Entities | Regions | Resource nodes | Buildings | Quests (defs) | Distinct populated factions | Module composition |
|---|---|---|---|---|---|---|---|
| wilderness_survival | 11 | 4 | 4 | 1 | 7 | 2 (undead_remnants, wild_beast_pack) | none (catalog/pack/module_refs, no shared modules) |
| sandbox_world | 18 | 3 | 5 | 5 | 6 | 3 (merchant_league, town_council, wild_beast_pack) | frontier_village_core, wolf_den_near_forest |
| highland_traverse | 18 | 5 | 3 | 5 | 6 | 3 (merchant_league, town_council, wild_beast_pack) | mountain_pass, river_crossing, nomadic_herd, settled_quarter |
| urban_political | 30 | 3 | 3 | 7 | 9 | 4 (bandit_company, hero_guild, merchant_league, town_council) | none (module_refs) — the only world with FACTION/INFORMATION/self-model content |
| dungeon_crawl | 32 | 4 | 3 | 1 | 9 | 4 (bandit_company, goblin_warband, undead_remnants, wild_beast_pack) | none (module_refs) |
| swamp_border_world | 26 | 4 | 7 | 5 | 6 | 4 (merchant_league, swamp_tribe, town_council, wild_beast_pack) | frontier_village_core, wolf_den_near_forest, sunken_swamp_border |
| simq_routing_test | 30 | 3 | 5 | 6 | 7 | 5 (goblin_warband, hero_guild, merchant_league, town_council, wild_beast_pack) | none (module_refs) — the only routing-ON world, purpose-built test world |
| frontier_living_world | 46 | 7 | 9 | 6 | 16 | 6 (+merchant_league, +undead_remnants, +goblin_warband, ...) | frontier_village_core, wolf_den_near_forest, goblin_camp_conflict, old_mine_resource_loop, bandit_road_trade_pressure, undead_battlefield |
| generated_frontier_3_42 | 44 | 6 | 9 | 6 | 16 | 7 (+arcane_circle, +orc_clan) | none (catalog/pack/module_refs — procedurally generated) |
| frontier_extended | 56 | 10 | 13 | 6 | 22 | 9 (+forest_wardens, +spirit_court) | frontier_village_core, wolf_den_near_forest, goblin_camp_conflict, old_mine_resource_loop, bandit_road_trade_pressure, undead_battlefield, orc_clan_territory, forest_warden_grove |

**Combinations NOT currently represented:**

- **Large faction count + small entity/region footprint.** No world combines a high distinct-faction
  count (6-9) with a small map — the 6-9-faction worlds (frontier_living_world,
  generated_frontier_3_42, frontier_extended) are also the largest by entity/region/resource count.
  The low-faction worlds (wilderness_survival, sandbox_world, highland_traverse: 2-3 factions) are
  also the smallest. Faction density and world size currently move together; nothing tests
  "many factions crammed into a tight map" or the inverse ("one dominant faction across a huge
  map").
- **High resource-node density with a small map.** frontier_extended has both the most regions (10)
  and the most resource nodes (13) — density (nodes/region ≈ 1.3) is not meaningfully different
  from smaller worlds (sandbox_world: 5/3 ≈ 1.7; swamp_border_world: 7/4 = 1.75). No world
  stress-tests a small number of regions saturated with resource nodes, or the inverse (a sprawling
  map with sparse resources).
- **FACTION/INFORMATION/self-model content combined with a large-scale world.** The only world
  with any of the four Pattern-6 fields populated (urban_political) is mid-scale (30 entities, 3
  regions) — there is no data point for how FACTION tension propagation, belief assimilation, or
  self-model assimilation behaves at frontier_extended's scale (56 entities, 10 regions) or at
  wilderness_survival's scale (11 entities, near-zero settlement structure).
- **A routing-capable (AGENCY-active) world that is also a "real" gameplay archetype.**
  `simq_routing_test` is explicitly authored as a minimal calibration/test world ("Minimal world
  for SimQ 10-pillar calibration... ENABLE_ADVENTURE_ROUTING must be ON"), not a world meant to
  represent a shipped gameplay archetype. There is no data point for what AGENCY activation looks
  like inside e.g. a settlement-heavy or wilderness-survival archetype at that archetype's native
  scale.
- **Quest density vs. entity count as an independent axis.** Quest-def count scales almost linearly
  with entity count across the corpus (e.g. dungeon_crawl 32 entities/9 quests,
  frontier_extended 56/22) — no world deliberately decouples these (e.g. few entities but many
  quest defs, testing whether quest activation saturates at low population).

**Conclusion:** "different worlds use different scale" is **partially true today** (an 11-entity to
56-entity range, a 1-region-density to 10-region range exist), but the variation is **incidental**
(a byproduct of which modules were composed for other reasons), not **deliberate** along the axes
the user named (faction density independent of size, resource density independent of map size,
feature-content richness independent of scale). New authoring would be needed to make scale
diversity intentional rather than coincidental.

---

## 3. Blast radius / risk per feature

### FACTION tension seeding in more worlds
**Pure content, additive, no code risk — confirmed by Pattern 6's own documented fix shape.**
`faction_tension_overrides` is a per-composition override-merge validated against
already-catalog-registered faction IDs (`ValueError` on typo, not a silent no-op — per the design
pattern doc). Seeding it in more worlds requires zero schema/compiler/resolver changes (that
plumbing is already generic per Pattern 6) — only new `world.yaml` key-value entries plus a
recompile (`python -m src.worldbuilding.cli resolve <world>`) and a recalibration run to confirm
the new grade. No engine code path changes. The only per-world judgment call is *which* factions
get non-zero tension (an authoring decision, not an architecture one).

### INFORMATION source profiles in more worlds
**Same low-risk profile as FACTION** — `information_source_profiles`/`pending_information_responses`
are direct composition-scoped passthroughs (no global catalog exists for this content, so there is
no override-merge-against-catalog complexity as there is for FACTION). Also pure content.

`ENABLE_BELIEF_ASSIMILATION` **does not need new world-scoping mechanism** — it already IS
world-scoped, via `config/simulation_quality/profiles/<world>.yaml`'s `feature_flags:` block
(confirmed: only `urban_political.yaml` has one, setting this flag `ON`; `default.yaml`,
`dungeon_crawl.yaml`, `simq_routing_test.yaml` have none, defaulting OFF). Turning it on for
another world is a one-line YAML addition, not a new mechanism — no code risk. The judgment call is
purely which worlds' `information_source_profiles` content makes belief assimilation meaningful to
observe (seeding profiles without turning the flag on produces zero signal; turning the flag on
without profiles produces zero signal from the other direction — the two must be seeded together).

### Branch B (self-model) activation in a REAL shipped world
This is qualitatively different risk from the two above — characterizing the tradeoff, not
deciding it:

- **What "proven but not shipped" means precisely** (per
  `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/plan.md` and the ticket's own Honesty Note):
  the full seed → assimilate → materialize → route chain is proven correct only through
  `tests/integration/domains/test_fused_loop.py::test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`,
  a hand-built state test with `ENABLE_SELF_MODEL_COGNITION` scoped ON *for that test only*. In the
  real compiled `urban_political` world with shipped default flags, `ENABLE_SELF_MODEL_COGNITION`
  is OFF, so `self_model.knowledge.unknowns` is never populated end-to-end in any shipped run today
  — the pending field exists in `urban_political/world.yaml` but is inert without the flag.
- **Why turning it on for real might behave differently than the test scenario:**
  1. **Entity-count/tick-count scale**: the proof is a single-entity, few-tick hand-built state
     test. No calibration run has exercised Branch B across a full population (11-56 entities
     depending on world) over 200-1000 ticks — cumulative assimilation behavior
     (`old_bundle` carrying real history tick-over-tick, per the `SelfModelPatch` fix's own
     description of "genuinely cumulative across ticks") is unverified at any realistic scale.
  2. **Interaction with `ENABLE_BELIEF_ASSIMILATION`**: the ticket's own Finding 4 is that
     `InformationBeliefPhase` + `SelfModelUpdatePhase` clobbered each other when both flags were on
     simultaneously — a bug that existed silently because *no calibration profile had ever run both
     together* until this ticket's own investigation. That class of interaction bug (two
     independently-reasonable-looking flags combining destructively) is exactly the risk the SimQ
     philosophy is meant to surface — but it also means turning Branch B on in a *real* profile is
     the first time this flag combination would run under full calibration load, not just a unit
     test.
  3. **`AdventureRouteGenerator`/`scoring.py` interaction** (Branch B's own blast-radius sweep,
     Finding: "8 intended positive fix effects... The only consumers with any live conditional
     behavior change require both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` ON
     simultaneously"): if a future ticket ever combines Branch B activation with AGENCY activation
     (as `RolloutProfileManager`'s CLASS_B/CLASS_C already model on paper), that's a third
     never-live-tested flag combination.
  4. Canonical-hash participation: `self_model` already participates in the canonical hash
     (confirmed, `SUB-374`), so turning the flag on changes committed hash baselines for whichever
     world it's turned on in — not a correctness risk, but a determinism/baseline-churn
     consideration worth flagging for whoever schedules the recalibration.
- This is a **higher-trust-required activation** than FACTION/INFORMATION source-profile seeding:
  the mechanism is code-proven correct in isolation, but has zero live-load evidence, and its own
  investigation trail is the reason the interaction-bug risk is documented at all (it was found by
  looking, not by running).

### `ENABLE_ADVENTURE_ROUTING` / AGENCY broadly
Tradeoff, not a recommendation:

- **Reversing the DA ruling** (flipping the flag ON in an existing archetype-appropriate world, e.g.
  urban_political or dungeon_crawl) would directly contradict
  `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s explicit finding that `AdventureDecisionPhase` is
  "opt-in by world archetype, not a global default" and that AGENCY=C in those worlds is
  "archetype-correct... requires no remediation." Reversing it requires: (a) updating the DA
  ticket's own documented decision and its anti-drift note ("if any calibration world enables
  `ENABLE_ADVENTURE_ROUTING`, AGENCY will activate and grade anchors must be updated"), (b)
  recalibrating grade anchors for that world, (c) accepting that the world's archetype identity
  (e.g. "Dungeon Crawl... pure dungeon exploration," "Urban Political... settlement-heavy... trade
  pressure" — neither description mentions adventuring/routing) may not conceptually fit
  hero-routing behavior, since neither has a `hero_guild`-adjacent population framed around route
  selection the way `simq_routing_test` explicitly does ("hero adventurers (agency, progression)").
  urban_political *does* already have a `hero_guild` faction population (4 entities use it per the
  populated-faction table above) — so it is not architecturally foreign there, only outside the
  DA ruling's current scope.
- **Middle ground** (author 1-2 NEW worlds with routing ON by design from inception, rather than
  flipping existing worlds): this does not touch the DA ruling at all — it adds a new archetype
  category (a "routing-capable, real-scale" world) alongside "routing-inactive" and
  "routing-test-only" (`simq_routing_test`). This is lower-risk in the sense that it creates new
  data rather than reinterpreting existing archetype-correctness, but it does NOT resolve the
  underlying tension the user's philosophy raises: the *existing* 9 non-routing worlds would still
  report AGENCY=C forever, which is the "if a feature is not implemented well, we still use it in
  the world data, observe the result" principle being deliberately not applied to AGENCY unless a
  new world is built specifically to carry it.
- **Mechanism cost is asymmetric to the other three pillars covered above**: unlike
  FACTION/INFORMATION, there is no existing per-world profile-YAML wiring for
  `ENABLE_ADVENTURE_ROUTING` today — activating it for any world other than via
  `tools/evaluate_simq.py`'s hardcoded `simq_routing_test_*` scenario-name special case would
  require either extending that hardcoded list (cheap, but perpetuates a special-case pattern) or
  generalizing it into the same `feature_flags:` block mechanism `ENABLE_BELIEF_ASSIMILATION`
  already uses (architecturally trivial — the mechanism already exists and works for a sibling
  flag — but is itself a small scope decision, not just content authoring).
- **Not decided here**: whether the answer is "flip existing worlds" (DA reversal), "author new
  worlds" (middle ground), or "leave AGENCY=C everywhere except test/new worlds" (status quo) is
  exactly the kind of user-facing tradeoff this investigation defers, per instructions.

### P2-D (faction relationships sparse) — fold-in candidate
Directly on-philosophy: 20/120 undirected faction pairs (16.7%) is a **global content-density gap**,
not a per-world one — every world draws from the same underactivated relationship catalog. Fixing
it once (author toward the ticket's own 50%+ target) benefits every world simultaneously and is
pure content (same risk class as FACTION tension seeding). Strong candidate to fold into this
epic's content-authoring scope rather than remaining a standalone P2-D ticket, since both are
"the global faction-content layer is thin" findings.

---

## 4. Other open questions requiring a human decision before ticket creation

1. **Should "distinct populated factions per world" become an explicit, tracked scale axis** (like
   entity/region/resource counts already are in `world_compile_report.json`), given that raw
   `factions_resolved` count is a constant 16 and therefore not a meaningful signal on its own?
   Currently nothing computes or reports the 2-9 range found in this investigation.
2. **Should FACTION/INFORMATION/self-model content be authored per-world individually (bespoke
   values matched to each world's archetype), or via a shared authoring template/generator** applied
   across all 9 currently-inert worlds? The former respects each world's distinct
   description/archetype (e.g. wilderness_survival's "no settlement" framing may make
   `information_source_profiles` like `town_notice_board` archetypally wrong there); the latter is
   faster but risks the same "generic content stamped everywhere" outcome the SimQ Uplift batches
   were originally trying to avoid by scoping to `urban_political` specifically.
3. **Does turning on `ENABLE_SELF_MODEL_COGNITION` in a real world require its own DA-style
   architecture ruling** (mirroring the AGENCY-DA precedent), given it is a currently-OFF-everywhere
   flag whose only live-fire evidence is a single cross-tick unit test, before any ticket seeds it
   into a shipped calibration profile? This investigation surfaces the risk (§3) but does not
   resolve whether that risk threshold requires a dedicated pre-approval step.
4. **Scale-diversity authoring order**: should new/expanded worlds be built to fill the identified
   scale gaps (§2's "NOT currently represented" list) before or independently of the
   feature-activation content pass? They are separable work (one is "make existing worlds richer,"
   the other is "add new worlds at unrepresented scale points") but the user's framing ("different
   worlds using different scenarios and scale") implies both should land together conceptually.
5. **P2-E** (`docs/plans/audit_fix_plan.md`: "Feature-gated phases have no per-scenario default
   test") is directly relevant risk-mitigation for this whole epic — if content/flags are about to
   be seeded much more broadly across many worlds, a test asserting each scenario's expected flag
   state would catch silent misconfiguration. Worth folding in as a guardrail ticket alongside
   P2-D, not treated as unrelated.
