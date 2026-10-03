---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-INFORMATION
artifact_type: investigation
tags: [simulation-quality, information, world, corpus, calibration]
---

# Investigation — TCK-20260710-SIMQ-DEPTH-INFORMATION

## Current Behavior

**Pattern-6 compiler/resolver plumbing (confirmed reusable as-is, zero engine changes needed):**

- `src/domains/information/schema.py:16-59` — `InformationSourceKind` enum (`guide`, `guild`,
  `blacksmith`, `traveler`); `InformationSourceProfile` (frozen dataclass: `source_id`,
  `source_kind`, `knowledge_scopes: Tuple[str,...]`, `accuracy`, `freshness`, `bias`, `cost_gold`,
  `max_answers_per_query`); `InformationSourceCandidate`; `InformationQuery`. Confirmed present and
  unchanged since `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`.
- `src/domains/information/router.py:22-105` — `InformationQueryRouter.route()`. `matches_scope()`
  (lines 46-53) is the hard-coded, load-bearing vocabulary any new world's `knowledge_scopes` must
  use verbatim: `"common_resource_sources"` → `material_source` queries, `"recipe_requirements"` →
  `recipe_definition`, `"regional_danger"` → `danger_rating`. `source_kind == "traveler"` bypasses
  the scope check entirely (line 57). Confirmed matches the ticket's Related Code Areas claim.
- `src/domains/information/phase.py:27-110` — `InformationBeliefPhase.apply()`. Branch A (lines
  45-81, the `pending_responses`/`resp_by_actor` path) iterates `state.entities.values()` and
  matches on `actor.id` — confirmed generic, no `urban_political`-specific special-casing. Branch B
  (lines 83-105, the `self_model.knowledge.unknowns` routing path) is separate and out of this
  ticket's scope per the ticket's own Out of Scope section. Reachability of Branch A depends only on
  (a) a compile-time `pending_information_responses` entry targeting a real compiled `actor_id`, and
  (b) `ENABLE_BELIEF_ASSIMILATION: "ON"` in the resolved calibration profile (confirmed by
  `frontier_marches`'s documented near-miss in `eval_matrix_results.md:1400-1409` — compile-time
  content alone with no matching profile YAML left Branch A unreached until the profile was added).
- `src/worldbuilding/schema.py`, `src/worldassembly/schema.py`, `src/worldbuilding/compiler.py`,
  `src/worldassembly/resolver.py` — confirmed present, unmodified since `INFRA-256`/`INFRA-257`
  shipped. `WorldAssemblyResolver.assemble()` is a passthrough for this content (no catalog/merge
  logic, unlike factions) — read but not modified as part of this investigation.

This mechanism is exercised by 9 of the corpus's 17 worlds today (see coverage table below), proven
at small scale (`unit_information_source`, 16 entities/1 region) and large scale (`frontier_marches`,
62 entities/9 regions, authored-from-inception).

## Mechanics / Engine Constraints

- `docs/simulation_quality/quality_scoring_contract.md` §"INFORMATION & BELIEF" — pillar definition,
  event types (`belief_assimilated`, `belief_updated`, `lead_certainty_updated`,
  `paid_information_transaction`), and SQ-15 (the `belief_updated` dual-scoring note: scored by both
  `InformationScorer` and `CognitionScorer`, so any new world's INFORMATION move is expected to
  co-move COGNITION). This was empirically confirmed in the 6-world `E2E-CONTENT-EXPANSION` table
  (`eval_matrix_results.md:686-825`, e.g. `sandbox_world`'s `C → B (dual-emission)` COGNITION note).
- `docs/simulation/domains/information_contract.md` §"Knowledge Assimilation Constraints" — an
  entity only assimilates facts from sources whose trust ≥ its assimilation threshold; contradicted
  facts are marked, not assimilated. Constrains any new world's `accuracy`/`bias` seed values if a
  candidate were to exist (moot given the UQ-1 finding below).
- `docs/guidelines/design_patterns.md` Pattern 6 ("Compile-Time Pillar Activation Pattern") — the
  general shape both FACTION and INFORMATION plumbing follow: a durable-state field permanently
  empty for every compiled world until `WorldCompiler.compile()` is taught to construct it. Already
  closed for INFORMATION (`INFRA-256`/`INFRA-257`).
- `docs/parity_ledger/infrastructure.yaml::INFRA-258` — kernel tick-alignment fix
  (`src/observability/event_extractor.py:286`), already shipped, required for `belief_assimilated`/
  `belief_updated` calibration hits to be observable through the real live loop at all. Not touched
  by this ticket.

## Parity Ledger Overlap

- **INFRA-256** (`information_source_profiles` compile-time plumbing) — status `verified`, priority
  P1. `v2_evidence` currently cites `urban_political` + the 6 `CORPUS-E2E-CONTENT-EXPANSION` worlds +
  `frontier_marches` = 8 worlds by name in its text body (the 9th, `unit_information_source`, is
  covered under the sibling `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` ticket but is not
  yet named in `INFRA-256`'s own text — a documentation gap, not a functional one; flagged in Risks
  below). No content-authoring extension needed for this ticket (zero candidates, see UQ-1
  resolution) — the only Plan-phase parity action is a documentation-completeness check/possible
  additive clause naming `unit_information_source`, mirroring `INFRA-256`'s existing pattern of
  additive-only extension clauses (frontier_marches's own clause is additive, does not reword prior
  text).
- **INFRA-257** (`pending_information_responses` Branch-A compile-time plumbing) — status `verified`,
  P1, same world-coverage set and same minor documentation-completeness note as INFRA-256.
- **INFRA-258** (kernel tick-alignment fix) — status `verified` (not re-checked line-by-line in this
  investigation; out of scope, already shipped and load-bearing for all 9 covered worlds' measured
  results).
- **INFRA-259/INFRA-260** (Branch B code-correctness) — explicitly out of scope per the ticket; not
  touched.
- No P0 entries are implicated. Both INFRA-256 and INFRA-257 are P1.

## Prior Work

- `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` (done) — shipped the Pattern-6 schema/compiler/resolver
  scaffolding + `urban_political` seeding; found Branch A unreachable and deferred the fix.
- `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` (done) — the 3-bug fix chain
  (`SelfModelUpdatePhase.apply()` `events=[]` hardcoding, missing `pipeline.py:152` merge wrapper,
  kernel tick-alignment) that made Branch A genuinely reachable for `urban_political`.
- `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (done) — extended INFORMATION to 6 more worlds
  (`sandbox_world`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
  `frontier_extended`, `generated_frontier_3_42`); documented the `dungeon_crawl`/
  `wilderness_survival` "INFORMATION skip" judgment calls (no settlement/service module in either
  composition — confirmed independently below, not just trusted from the doc).
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` (done) — authored `frontier_marches` with INFORMATION
  content from inception (needed its own new profile YAML to actually reach Branch A — a concrete
  precedent for "compile-time content alone is insufficient without the matching profile flag," a
  risk noted in this ticket's own Out of Scope/UQ-4); documented `crowded_frontier`/
  `resource_dense_basin`'s deliberate INFORMATION=C tier-purity default.
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done) — authored `unit_information_source`
  (INFORMATION isolation world) and `unit_faction_tension` (explicitly INFORMATION-inert by design).
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` (done) — authored `hero_guild_routing`; despite
  composing `frontier_village_core` (a settlement-bearing module, the same one `urban_political`/
  `sandbox_world`/etc. use), it is a deliberate AGENCY/route-selection isolation world — INFORMATION
  stays C "isolation-tier default" (`eval_matrix_results.md:1223`).
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done) — authored `unit_selfmodel_pilot`;
  isolates COGNITION's self-model half via `ENABLE_SELF_MODEL_COGNITION`, deliberately leaves
  `ENABLE_BELIEF_ASSIMILATION` absent — INFORMATION stays C "as predicted before the run"
  (`eval_matrix_results.md:1192`).
- `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (done) — defines the tier taxonomy this investigation
  cross-checked live worlds against.
- **`TCK-20260710-SIMQ-DEPTH-FACTION` (done, this ticket's sibling, closed before this
  investigation ran)** — same methodology, same corpus, mirrored conclusion. Its
  `stored_artifacts/TCK-20260710-SIMQ-DEPTH-FACTION/investigation.md` and `plan.md` directly informed
  this investigation's structure: (1) live-grep every `data/worlds/*/world.yaml` rather than trust
  docs, (2) build a per-world coverage table citing exact grep/read evidence, not doc citations, (3)
  when the answer is "zero candidates," close via a documented "already-satisfied by prior work"
  decision rather than escalate to the roadmap's Phase 5 Coverage Decision Gate (its own
  `plan.md`'s "Closure-Mechanism Decision" section gives the load-bearing reasoning for why Phase 5
  is a corpus-wide, later-phase decision checkpoint, not a per-ticket closure mechanism — directly
  reusable for this ticket, since it is not FACTION-specific reasoning). The FACTION ticket closed at
  11/17 covered, 6/17 tier-protected, zero legitimate candidates, and updated
  `eval_matrix_results.md` with a "FACTION Coverage Closure — Phase 3" table
  (`eval_matrix_results.md:1994-2023`) plus a correction note in
  `docs/plans/simq_development_roadmap.md`'s Phase 3 section (lines 286-307) that already states, in
  advance, the INFORMATION-half prediction this investigation confirms: "9 of 17 corpus worlds
  already have `information_source_profiles` content... All 8 remaining worlds have a pre-existing,
  already-documented reason to stay inert... the honest current reading is **zero** undisputed
  candidates."

## Corpus-Wide INFORMATION Coverage Re-Verification

Live-verified 2026-07-12 directly against `data/worlds/*/world.yaml` (`grep -c
"information_source_profiles\|pending_information_responses"`, then hand-read every hit to exclude
prose-description false positives) and `config/simulation_quality/profiles/*.yaml`
(`ENABLE_BELIEF_ASSIMILATION`). All 17 corpus worlds enumerated (`ls data/worlds/` minus
`world_index.json`).

| # | World | Tier | INFORMATION content? | Live evidence | Reason if not covered |
|---|---|---|---|---|---|
| 1 | `urban_political` | Regression/baseline (already E2E by criterion) | **Covered** | `information_source_profiles` (1 entry) + `pending_information_responses` (1 entry) in `world.yaml`; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `urban_political.yaml` | — |
| 2 | `sandbox_world` | End-to-end | **Covered** | 1+1 entries (`town_notice_board`/`hometown_danger`); `ENABLE_BELIEF_ASSIMILATION: "ON"` in `sandbox_world.yaml` | — |
| 3 | `highland_traverse` | End-to-end | **Covered** | 1+1 entries (`route_waystation_guide`); `ENABLE_BELIEF_ASSIMILATION: "ON"` in `highland_traverse.yaml` | — |
| 4 | `swamp_border_world` | End-to-end | **Covered** | 1+1 entries; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `swamp_border_world.yaml` | — |
| 5 | `frontier_living_world` | End-to-end | **Covered** | 1+1 entries; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `frontier_living_world.yaml` | — |
| 6 | `frontier_extended` | End-to-end | **Covered** | 1+1 entries; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `frontier_extended.yaml` | — |
| 7 | `generated_frontier_3_42` | End-to-end (generated) | **Covered** (documentation-only evidence — not in `grade_anchors.json`/`FAST_ANCHOR_KEYS`, per its own explicit scope decision, `INFRA-256` text) | 1+1 entries; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `generated_frontier_3_42.yaml` | — |
| 8 | `frontier_marches` | Stress (gap 3, authored-from-inception) | **Covered** | 1+1 entries; `ENABLE_BELIEF_ASSIMILATION: "ON"` in `frontier_marches.yaml` (required a dedicated profile file — `_resolve_profile()` would otherwise fall back to `default`, leaving Branch A unreached despite correct compile-time content) | — |
| 9 | `unit_information_source` | Unit (isolates INFORMATION itself) | **Covered** | 2+2 entries (`town_notice_board`, `hometown_danger` → `pop_0`); `ENABLE_BELIEF_ASSIMILATION: "ON"` in `unit_information_source.yaml` | — |
| 10 | `dungeon_crawl` | End-to-end | Not covered | `world.yaml` composes `ruins_mystery_quest` (danger_zone), `goblin_camp_conflict` (conflict), `old_mine_resource_loop` (economy), `scalable_bandit_camp` (conflict, has `population_recipes` but no settlement module type) — no `module_type: settlement` present anywhere in the composition | **Structural skip** — no settlement/service module; `eval_matrix_results.md:651-659` documents "forcing a notice-board archetype here would be dishonest" |
| 11 | `wilderness_survival` | End-to-end | Not covered | `world.yaml` composes `forest_deep_ecology`/`wolf_den_near_forest` (ecology), `undead_battlefield` (danger_zone), `survivor_camp_shelter` (`module_type: settlement`, but `provides: [shelter, survival]` only — no `population_recipes` key anywhere in the module file, confirmed by direct read) | **Structural skip** — `survivor_camp_shelter`'s `module_type` label is "settlement" but it spawns no population (only a `healer_hut` building), so there is no compiled `actor_id`/`population_id` a `pending_information_responses` entry could target; `eval_matrix_results.md:703-711` independently confirms "no settlement-adjacent module... spawns no settlement population of its own" |
| 12 | `crowded_frontier` | Stress (gap 1: many-factions/small-map) | Not covered | `world.yaml` composes `frontier_village_core` (settlement, population-bearing) + `hero_adventurers` + 3 conflict modules — a settlement module IS present but no `information_source_profiles`/`pending_information_responses` key exists | **Deliberate tier-purity default** — isolates scale/faction-density as the sole variable; `INFORMATION=C` stable all 3 seeds (`eval_matrix_results.md:1305`, "tier-purity default") |
| 13 | `resource_dense_basin` | Stress (gap 2: resource-saturated/small-map) | Not covered | `world.yaml` composes `frontier_village_core` (settlement) + `old_mine_resource_loop` + `orc_clan_territory` — settlement module present, no INFORMATION key | **Deliberate tier-purity default**; `INFORMATION=C` stable all 3 seeds (`eval_matrix_results.md:1357`) |
| 14 | `simq_routing_test` | Regression/baseline | Not covered | `world.yaml` composes `frontier_village_core` (settlement) + others; own description text mentions "information" only in prose ("a frontier village (economy, social, information, faction)"), no `information_source_profiles:`/`pending_information_responses:` key | Purpose-built minimal AGENCY/10-pillar calibration fixture predating the Pattern-6 uplift, "do not touch" baseline; `INFORMATION=C`, 0 events, all 3 seeds (`eval_matrix_results.md`, `simq_routing_test` 500t table) |
| 15 | `hero_guild_routing` | Unit (isolates AGENCY/routing only) | Not covered | `world.yaml` composes `frontier_village_core` (settlement) + `hero_adventurers` + `mountain_pass` + `ruins_mystery_quest` + `goblin_camp_conflict` — settlement module present, no INFORMATION key | **Deliberate isolation** — "isolation-tier default," `INFORMATION=C` stable all 3 seeds at 500t (`eval_matrix_results.md:1223`) |
| 16 | `unit_faction_tension` | Unit (isolates FACTION itself) | Not covered | `world.yaml` composes `frontier_village_core` + `wolf_den_near_forest`; description text explicitly states "`information_source_profiles`, `pending_information_responses`... stay empty/default" — confirmed no real content, only the description sentence itself matched the grep | **Deliberate single-mechanic isolation** (FACTION); `INFORMATION=C`, "isolation confirmed... 0 events, as designed" (`eval_matrix_results.md:1114`) |
| 17 | `unit_selfmodel_pilot` | Unit (isolates COGNITION self-model only) | Not covered | `world.yaml` composes `frontier_village_core` + `hero_adventurers`; description explicitly states "No `information_source_profiles` or `pending_information_responses` content is seeded in this world" — confirmed, only the description sentence matched the grep; `unit_selfmodel_pilot.yaml` profile has `ENABLE_SELF_MODEL_COGNITION: "ON"` but no `ENABLE_BELIEF_ASSIMILATION` key at all | **Deliberate single-mechanic isolation** (COGNITION self-model); `INFORMATION=C`, "isolation confirmed, as predicted before the run" (`eval_matrix_results.md:1192`) |

**Cross-check:** `grep -rn "ENABLE_BELIEF_ASSIMILATION" config/simulation_quality/profiles/*.yaml`
returns exactly 9 hits, one per profile file, matching rows 1-9 above exactly (no world has the flag
without matching `world.yaml` content, and no world with content lacks the flag). This is a stronger
verification than grep-count alone: two independent signals (compile-time content presence, runtime
flag presence) agree on the same 9-world set.

**On the two "hits" that initially looked like false positives (rows 16, 17):** `unit_faction_tension`
and `unit_selfmodel_pilot` each produced 1 grep hit for both `information_source_profiles` and
`pending_information_responses`, but direct inspection (`grep -n -A3`) showed the hit is inside the
`description:` prose field, not a real YAML key — both worlds' authors wrote sentences explicitly
stating these fields are empty, as a self-documenting design note. This is exactly the kind of
grep-vs-reality gap UQ-3 asked this investigation to guard against; resolved by reading actual
content, not trusting hit-counts.

## UQ-1 Resolution

**Definitive answer: zero genuinely uncovered, tier-appropriate INFORMATION candidates remain in the
corpus, as of live 2026-07-12 verification.**

9 of 17 corpus worlds have real, calibrated, grade-anchored `information_source_profiles` +
`pending_information_responses` content with `ENABLE_BELIEF_ASSIMILATION: "ON"` (independently
confirmed via two agreeing signals — compile-time content and runtime flag — not just doc citation).
Of the remaining 8:

- **2 are structurally incapable** (`dungeon_crawl`, `wilderness_survival`) — neither has a
  population-bearing settlement module. `wilderness_survival`'s `survivor_camp_shelter` module
  carries a `module_type: settlement` label but has no `population_recipes` at all, confirmed by
  direct read of `data/content/world_modules/survivor_camp_shelter.yaml` — it cannot host a
  `target_population_id` for any `pending_information_responses` entry to resolve against. This is a
  hard structural blocker, not a labeling nuance: even if content were authored, `WorldCompiler`
  would have no compiled `actor_id` to target.
- **2 have a genuine settlement module present but a documented, deliberate Stress-tier-purity
  default** (`crowded_frontier`, `resource_dense_basin`, both compose `frontier_village_core`) —
  each world's entire purpose is isolating scale/composition as the sole variable; adding
  INFORMATION content would confound that isolation, and both are independently confirmed
  `INFORMATION=C` stable across all 3 seeds in already-shipped calibration data.
- **1 is a "do not touch" Regression/baseline calibration fixture** (`simq_routing_test`) predating
  the Pattern-6 uplift.
- **3 are Unit-tier single-mechanic isolation worlds by explicit design**
  (`hero_guild_routing` isolates AGENCY/routing; `unit_faction_tension` isolates FACTION;
  `unit_selfmodel_pilot` isolates COGNITION's self-model half), two of which
  (`hero_guild_routing`, `unit_faction_tension`) also compose `frontier_village_core` and could
  technically host INFORMATION content, but doing so would break the single-variable isolation
  contract each was authored to establish — the same reasoning the FACTION sibling ticket applied
  to the mirror-image case (worlds that compose a settlement module but stay FACTION-inert by
  design).

This exactly matches the ticket's own pre-filed UQ-1 claim, word-for-word on the world list and the
per-world reasoning categories, and mirrors the FACTION sibling ticket's closure shape (11/17 covered
there vs. 9/17 here, 6/17 tier-protected there vs. 8/17 here — INFORMATION's gap is indeed tighter,
as the ticket predicted, because INFORMATION additionally requires a *population-bearing* settlement
module, a strictly narrower structural requirement than FACTION's "any faction-populating module").

**Recommendation for Plan phase: close as "already-satisfied by prior work," not fold into Phase 5.**
The FACTION sibling's `plan.md` "Closure-Mechanism Decision" reasoning applies without modification —
the roadmap's own Phase 3 correction note (`docs/plans/simq_development_roadmap.md:286-307`) already
predicted and pre-authorized exactly this outcome ("'zero new worlds, coverage already adequate,
documented and closed' is also a valid acceptance outcome"), and Phase 5 is explicitly a later,
corpus-wide, multi-phase decision gate, not a per-ticket closure mechanism.

## Risks and Open Questions

- **UQ-2 resolution:** close as already-satisfied (9/17 is the honest staged-depth bar), not
  re-scoped to a tier-taxonomy exception. No world's tier-purity/isolation rationale is weak enough
  to justify overriding it — every one of the 8 non-candidates has independently-confirmed,
  already-shipped `INFORMATION=C` calibration data backing its documented reason, not just a
  narrative claim.
- **UQ-3 resolution:** `corpus_tier_taxonomy.md` (dated 2026-07-06) and `eval_matrix_results.md` are
  both slightly stale relative to this investigation's 2026-07-12 live check, but the staleness is
  benign — both already correctly describe the current world set (no world was added, removed, or
  reclassified between 2026-07-06 and 2026-07-12 that affects INFORMATION). `eval_matrix_results.md`
  gained a "FACTION Coverage Closure — Phase 3" section on 2026-07-10 (FACTION sibling) but has no
  equivalent "INFORMATION Coverage Closure" section yet — this is the one concrete doc gap Plan
  should close, mirroring the FACTION table format exactly.
- **Minor parity-ledger documentation gap (not a functional gap):** `INFRA-256`/`INFRA-257`'s prose
  text names `urban_political` + the 6 `E2E-CONTENT-EXPANSION` worlds + `frontier_marches` (8 worlds)
  but does not explicitly name `unit_information_source` (the 9th) in either entry's `text` body,
  even though `unit_information_source` clearly satisfies both entries' `support_boundary`. This is a
  documentation-completeness gap left over from `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`,
  not something this ticket introduced — flagged for Plan to decide whether an additive clause is
  warranted (low priority, does not block closure).
- No open question blocks the Plan-phase closure decision — UQ-1/UQ-2/UQ-3/UQ-4 are all resolved by
  this investigation. UQ-4 (risk of a 4th causally-linked engine bug) is moot since no content
  authoring will occur.

## Anti-Drift Hazards

- **Do not conflate `state.information_providers`/`InformationNeedDetector`/
  `PaidInformationTransactionSystem` with `state.information_source_profiles`/
  `InformationBeliefPhase`.** Two separate registries feeding two separate, independently-gated
  systems, per `docs/plans/idea_information_belief_trigger_wiring.md`'s own Anti-Drift Hazards
  section. Not touched by this investigation; flagged here only because a future re-read of "is
  INFORMATION covered" must not accidentally credit the paid-information marketplace path as
  coverage — it remains orphaned corpus-wide.
- **Do not read a settlement module's presence as sufficient evidence for an INFORMATION candidate.**
  `crowded_frontier`, `resource_dense_basin`, `hero_guild_routing`, and `unit_faction_tension` all
  compose `frontier_village_core` (a population-bearing settlement module) yet are correctly
  INFORMATION-inert by design — module presence is necessary but not sufficient; the tier/isolation
  contract governs, not raw module composition.
- **Do not read `module_type: settlement` as sufficient evidence of population-bearing capability.**
  `survivor_camp_shelter` carries that label but has zero `population_recipes` — the correct test is
  presence of `population_recipes` in the composed modules, not the `module_type` string.
- **If this ticket is ever revisited under different premises** (e.g., a future world composition
  changes, or the roadmap's Phase 5 gate authorizes overriding a tier-purity default), re-run the
  live grep sweep against `data/worlds/*/world.yaml` and `config/simulation_quality/profiles/*.yaml`
  fresh — do not trust this investigation's table beyond its stated as-of date (2026-07-12), per the
  same discipline this investigation applied to the roadmap doc/taxonomy doc's own staleness.
