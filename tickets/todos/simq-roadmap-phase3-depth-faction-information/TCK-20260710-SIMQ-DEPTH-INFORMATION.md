---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-INFORMATION
phase: open
date: 2026-07-10
tags: [simulation-quality, information, world, corpus, calibration]
---

# TCK-20260710-SIMQ-DEPTH-INFORMATION

## Title
Extend INFORMATION pillar depth (Pattern 6 `information_source_profiles` + `pending_information_responses` seeding) to 2-3 more corpus worlds — Phase 3 Depth Wave 2 (INFORMATION half)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is the INFORMATION half of `docs/plans/simq_development_roadmap.md` Phase 3 ("Depth Wave 2:
FACTION + INFORMATION"). The roadmap frames INFORMATION's history as harder than a compiler-plumbing
fix: `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` shipped the `information_source_profiles` schema/
compiler/resolver scaffolding (same Pattern-6 shape as FACTION), but investigation found the
scaffolding alone was insufficient — `InformationBeliefPhase.apply()`'s trigger branches were
unreachable. The follow-up, `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`, then found and fixed 3
causally-linked bugs to reach Branch A: `SelfModelUpdatePhase.apply()` hardcoding `events=[]`, a
missing `pipeline.py` merge wrapper for `InformationBeliefPhase.apply(...)`, and a kernel
tick-alignment bug affecting 3 unrelated event types corpus-wide
(`Kernel._phase_advancement()` comparing Resolution-phase-stamped properties against the wrong
tick). Getting INFORMATION into one world (`urban_political`) took 2 tickets and non-trivial engine
debugging, not just content authoring — the roadmap explicitly budgets Phase 3 as **L**, not **M**,
on this history.

**This ticket's Investigate-phase mandate (per the orchestrating instruction) was to check whether
the roadmap's premise about corpus coverage is stale for INFORMATION the same way it was found to be
stale for FACTION (`TCK-20260710-SIMQ-DEPTH-FACTION`, filed as this ticket's sibling in the same
folder, found 11 of 17 worlds already have FACTION content authored, not just `urban_political`).
That check was done directly against `data/worlds/*/world.yaml`,
`config/simulation_quality/profiles/*.yaml`, `docs/simulation_quality/eval_matrix_results.md`, and
`docs/parity_ledger/infrastructure.yaml::INFRA-256/257`. Verdict: yes — INFORMATION's premise is
stale too, and the resulting gap is arguably tighter than FACTION's. See Assumptions/Open Questions
UQ-1 for the full evidence and why this may leave zero legitimate remaining candidates, not just a
smaller pool.**

`information_source_profiles` + `pending_information_responses` + `ENABLE_BELIEF_ASSIMILATION: "ON"`
are already seeded, calibrated, and grade-anchored (INFORMATION `C→B`) in **9 of 17** corpus worlds:
`urban_political` (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION` /
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`), `sandbox_world`, `highland_traverse`,
`swamp_border_world`, `frontier_living_world`, `frontier_extended`, `generated_frontier_3_42` (all 6
via `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`), `frontier_marches` (authored-from-inception via
`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`), and `unit_information_source` (unit-tier isolation world
via `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`). This is documented in
`docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257` and
`docs/simulation_quality/eval_matrix_results.md`'s "FACTION/INFORMATION Content Expansion" and
"Stress-Tier Worlds"/"Unit-Tier Isolation Worlds" sections. The Pattern-6 compiler-level plumbing
(`PendingInformationResponseSpec`, `InformationSourceProfileSpec`,
`WorldCompiler.compile()`/`WorldAssemblyResolver.assemble()` seeding) and the
`InformationBeliefPhase`/kernel tick-alignment fixes are confirmed reusable as-is — zero new engine
work is expected for this ticket, mirroring the FACTION sibling's conclusion.

## Scope
1. **Investigate phase (required first step, before any content authoring):** re-verify current
   INFORMATION coverage across all 17 corpus worlds against `docs/simulation_quality
   /corpus_tier_taxonomy.md`'s "Current tier mapping" table, `eval_matrix_results.md`, and
   `docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257` (all may be slightly stale by
   pickup time) — verify directly against `data/worlds/*/world.yaml` and
   `config/simulation_quality/profiles/*.yaml` for `information_source_profiles`/
   `pending_information_responses`/`ENABLE_BELIEF_ASSIMILATION`. **Given this ticket's own scoping
   evidence (UQ-1) already suggests every one of the 8 remaining worlds has a documented,
   pre-existing reason to stay INFORMATION-inert, Investigate's real job is confirming or refuting
   that "zero legitimate candidates" conclusion, not assuming 2-3 candidates exist by default.**
2. If Investigate finds legitimate candidates: select up to 2-3 archetype-appropriate worlds with
   plausible information-asymmetry/intrigue archetypes (settlement-adjacent module present, not
   already tier-protected against INFORMATION) from whatever remains. If Investigate finds a
   settlement-adjacent module exists in a nominally tier-protected world (Stress/Unit/Regression)
   and believes an exception is justified, that requires explicit justification against
   `corpus_tier_taxonomy.md`'s classification criteria before proceeding — do not silently override
   tier-purity defaults.
3. For each selected world: seed `information_source_profiles` (candidate source(s), archetype-fit
   `knowledge_scopes` matching `InformationQueryRouter.matches_scope()`'s recognized vocabulary —
   `common_resource_sources`, `recipe_requirements`, `regional_danger`) via the existing Pattern-6
   compiler/resolver plumbing, seed `pending_information_responses` (the Branch A mechanism
   `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` used to reach `belief_assimilated`) targeting a
   real compiled population id in that world (not a copy-pasted `pop_0` placeholder — confirm via
   `entity.properties["population_id"]`), and set `ENABLE_BELIEF_ASSIMILATION: "ON"` in that world's
   calibration profile YAML.
4. Recalibrate each selected world (3-seed matrix, following the corpus's existing calibration
   pattern) and add/update grade-anchor entries in `tests/simulation_quality/fixtures
   /grade_anchors.json` + `FAST_ANCHOR_KEYS`.
5. Run a corpus-wide regression sweep (`make evaluate` / `make evaluate-full` as appropriate —
   INFORMATION content-only changes have historically also moved COGNITION as a side effect, per
   `belief_updated` being scored by both `InformationScorer` and `CognitionScorer` — document any
   such co-movement honestly rather than treating it as unexpected).
6. Update `docs/simulation_quality/eval_matrix_results.md` and `corpus_tier_taxonomy.md` with the
   new worlds' grade tables/tier notes.
7. Extend `docs/parity_ledger/infrastructure.yaml`'s `INFRA-256`/`INFRA-257` entries' `v2_evidence`
   with the newly selected worlds (mirroring how those entries already extend to the 6
   `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` worlds + `frontier_marches`), rather than
   creating new parity entries, unless Investigate finds a reason a new entry is warranted.
8. Track any newly-discovered engine bug as its own ticket rather than folding it into this ticket's
   scope — budget real risk for this given the documented precedent (`urban_political`'s activation
   alone surfaced 3 causally-linked kernel/cognition-pipeline bugs); a new world's specific
   population/module configuration could plausibly surface a 4th.

## Out of Scope
- The FACTION half of this Phase 3 wave — filed as a sibling ticket
  (`TCK-20260710-SIMQ-DEPTH-FACTION`) in this same
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/` folder; can run independently
  (different content domain, different pillar) but both cite
  `docs/plans/simq_development_roadmap.md` Phase 3.
- Any new schema/compiler/resolver engine work — Pattern 6 plumbing
  (`InformationSourceProfileSpec`/`PendingInformationResponseSpec`) and the
  `InformationBeliefPhase`/kernel tick-alignment fixes are confirmed reusable as-is; if Investigate
  finds them insufficient for a new world's specific configuration, that is new information
  requiring a plan revision (and likely its own bug ticket per Scope item 8), not in-scope
  engineering to push through under this ticket's original estimate.
- Wiring Branch B (`self_model.knowledge.unknowns` / `SelfModelUpdatePhase` /
  `ENABLE_SELF_MODEL_COGNITION`) into any shipped calibration profile — Branch B's mechanism is
  code-correct and test-proven per `docs/parity_ledger/infrastructure.yaml::INFRA-259`/`INFRA-260`,
  but remains deliberately OFF in every shipped world/profile outside `unit_selfmodel_pilot`. This
  ticket only extends Branch A (`pending_information_responses`) to more worlds.
- The paid-information marketplace path (`InformationNeedDetector`/`state.information_providers`/
  `PaidInformationTransactionSystem`) — a separate, still-orphaned mechanism from
  `information_source_profiles`; do not conflate the two per the idea doc's own Anti-Drift Hazards.
- Adding INFORMATION content to `dungeon_crawl` or `wilderness_survival` — both have a documented,
  structural "INFORMATION skip" (no settlement-adjacent module in their composition), not a
  tier-purity choice; overriding this would require new content authoring beyond this ticket's
  "seed onto an existing settlement module" scope.
- Adding INFORMATION content to `crowded_frontier` or `resource_dense_basin` (Stress tier) unless
  Investigate explicitly justifies overriding their documented tier-purity default (deliberately
  INFORMATION=C, mirroring their FACTION=C default, to isolate scale/composition as the sole
  variable) — default assumption is these stay out of scope.
- Adding INFORMATION content to `simq_routing_test` (purpose-built AGENCY calibration fixture, not a
  shipped-gameplay archetype), `hero_guild_routing` (Unit tier, isolates AGENCY/route-selection
  only), `unit_faction_tension` (Unit tier, isolates FACTION only), or `unit_selfmodel_pilot` (Unit
  tier, isolates COGNITION's self-model half only) — each is a deliberate single-mechanic isolation
  world by design; adding INFORMATION would break the isolation these tickets established
  (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`, `-UNIT-WORLD-AGENCY`,
  `-UNIT-WORLD-SELFMODEL-PILOT`).
- Changing INFORMATION scoring weights/thresholds (`docs/simulation_quality
  /quality_scoring_contract.md` §"INFORMATION & BELIEF" signal table).
- A full information marketplace or NPC query-response loop beyond the single-fire compile-time
  seed pattern already established.

## Acceptance Criteria
- [ ] Investigate phase produces a re-verified candidate list (against current `data/worlds/` state,
      not the roadmap doc snapshot) of legitimate, archetype-appropriate worlds genuinely lacking
      INFORMATION content, with the stale-premise gap (9/17 worlds already covered, all 8 remaining
      already documented as tier-protected or structurally unfit per UQ-1) explicitly reconciled
      before any content authoring begins — including the possibility that the honest answer is
      zero, in which case this ticket must return to Scope for a revision rather than force content
      into an inappropriate world
- [ ] IF legitimate candidates exist: each selected world has >=1 `information_source_profiles`
      entry with router-recognized `knowledge_scopes` and >=1 `pending_information_responses` entry
      targeting a real compiled population id, archetype-justified (not copy-pasted from another
      world's values)
- [ ] IF legitimate candidates exist: each selected world compiles with 0 warnings
      (`world_compile_report.json`) and holds >=60% population-alive floor through at least 200-300
      ticks at seed 42
- [ ] IF legitimate candidates exist: each selected world's INFORMATION grade moves measurably off
      `C` (calibration_hits > 0 for `belief_assimilated`) across a 3-seed calibration matrix, with
      grade-anchor entries added to `grade_anchors.json`/`FAST_ANCHOR_KEYS`
- [ ] `make evaluate` (full corpus sweep, not just `--dry-run`) exits 0 with 0 regressions
- [ ] `docs/parity_ledger/infrastructure.yaml` `INFRA-256`/`INFRA-257` extended (or a justified new
      entry added) with `v2_evidence` covering any newly selected worlds
- [ ] `eval_matrix_results.md` and `corpus_tier_taxonomy.md` updated with any new worlds' grade
      tables/tier notes
- [ ] Any newly-discovered engine bug is filed as its own ticket, not silently folded into this
      one's scope
- [ ] IF Investigate confirms zero legitimate candidates: the ticket is closed or re-scoped with that
      finding documented (not silently abandoned), per the same discipline the FACTION sibling
      ticket's UQ-1 establishes

## Related Tickets
- `docs/plans/simq_development_roadmap.md` Phase 3 — parent roadmap phase (both FACTION and
  INFORMATION halves)
- `TCK-20260710-SIMQ-DEPTH-FACTION` — sibling ticket (FACTION half of this same Phase 3 wave),
  filed in parallel in this same
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/` folder; different content domain
  and different pillar, can run independently, but both should be picked up together per the
  roadmap's Phase 3 framing. Its own Investigate phase reached the same structural conclusion this
  ticket's scoping evidence points toward: the roadmap's "single-world" premise is stale and the
  remaining un-covered worlds are, world-for-world, largely the same set (tier-protected
  Stress/Unit/Regression worlds), just mirrored across the two pillars (a FACTION-isolation unit
  world is an INFORMATION candidate-blocker and vice versa).
- `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` (done) — shipped `information_source_profiles` Pattern-6
  scaffolding + `urban_political` seeding; found the trigger-path gap and deferred it
- `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` (done) — shipped `pending_information_responses`
  Branch-A plumbing + the 3-bug kernel/cognition-pipeline fix chain that made INFORMATION genuinely
  reachable for `urban_political`; this ticket extends the same plumbing to more worlds, not the
  bug-fix chain itself (that work is done and reusable)
- `TCK-20260702-SIMQ-UPLIFT2-FACTION` (done) — sibling Pattern-6 fix for FACTION; established the
  schema/compiler/resolver template both INFORMATION tickets above followed
- `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC` (done) — documented Pattern 6 in
  `docs/guidelines/design_patterns.md`
- `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (done) — already extended INFORMATION content to
  6 more worlds (`sandbox_world`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
  `frontier_extended`, `generated_frontier_3_42`) alongside FACTION; this is the stale-premise
  conflict this ticket's Investigate phase must reconcile first (see Request Summary / Assumptions
  UQ-1)
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` (done) — authored `frontier_marches` with
  `information_source_profiles`/`pending_information_responses` from inception (8th world with
  INFORMATION content); also authored `crowded_frontier`/`resource_dense_basin` with a documented
  INFORMATION=C tier-purity default
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done) — authored `unit_information_source`
  (unit-tier INFORMATION isolation world, 9th world with INFORMATION content) and
  `unit_faction_tension` (unit-tier FACTION isolation world, explicitly INFORMATION-inert by design
  — out of scope to duplicate here)
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` (done) — authored `hero_guild_routing`, isolates
  AGENCY/route-selection only; explicitly INFORMATION-inert by design
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done) — authored `unit_selfmodel_pilot`,
  isolates COGNITION's self-model half only; explicitly INFORMATION-inert by design
- `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (done) — defines the tier taxonomy this ticket's
  candidate-world selection must respect (do not seed INFORMATION into Stress/Unit tier worlds
  without explicit justification)
- `docs/plans/simq_development_roadmap.md` Phase 2 (SOCIAL, filed as
  `tickets/todos/simq-roadmap-phase2-depth-social/`) — precedent wave this Phase 3 wave's shape
  follows; its actual cost should sanity-check this ticket's effort budget once it closes

## Related Docs
- `docs/plans/simq_development_roadmap.md` — Phase 3 section (source of this ticket)
- `docs/guidelines/design_patterns.md` — Pattern 6 ("Compile-Time Pillar Activation Pattern")
- `docs/plans/idea_information_belief_trigger_wiring.md` — the original idea doc behind
  `pending_information_responses`/Branch A; its Anti-Drift Hazards section is directly applicable
  here: (1) do not conflate `state.information_providers`
  (`InformationProviderState`/`PaidInformationTransactionSystem`) with
  `state.information_source_profiles`/`InformationBeliefPhase` — two separate registries feeding
  two separate, independently-gated systems; seeding one does not seed the other; (2) any change
  to shared cognition-pipeline code (e.g. `SelfModelUpdatePhase.apply()`) must be regression-tested
  against every calibration world, not just the one being extended; (3) do not widen scope into a
  full belief-assimilation response cycle or information marketplace.
- `docs/simulation_quality/quality_scoring_contract.md` §"INFORMATION & BELIEF" — pillar definition,
  event types (`belief_assimilated`, `lead_certainty_updated`, `paid_information_transaction`, etc.),
  signal table, and the `belief_active`/COGNITION cross-scoring note (SQ-15) — relevant because
  `belief_updated` is dual-scored by both `InformationScorer` and `CognitionScorer`, so any new
  world's INFORMATION move is expected to co-move COGNITION, per the `TCK-20260703-SIMQ-INFORMATION-
  BELIEF-TRIGGER`/`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` precedent
- `docs/simulation_quality/corpus_tier_taxonomy.md` — tier definitions and current per-world
  tier/content mapping; authoritative source for which worlds already have INFORMATION content and
  why the remaining worlds are tier-protected or structurally unfit
- `docs/simulation_quality/eval_matrix_results.md` — "FACTION/INFORMATION Content Expansion" section
  (6-world grade tables for the INFORMATION-fit subset), "Stress-Tier Worlds" (`frontier_marches`
  INFORMATION table; `crowded_frontier`/`resource_dense_basin` isolation confirmation), "Unit-Tier
  Isolation Worlds" (`unit_information_source` INFORMATION=B table;
  `unit_faction_tension`/`unit_selfmodel_pilot`/`hero_guild_routing` INFORMATION=C isolation
  confirmation)
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-256` (`information_source_profiles` compile-time
  plumbing, already covers `urban_political` + 6 `CORPUS-E2E-CONTENT-EXPANSION` worlds +
  `frontier_marches`), `INFRA-257` (`pending_information_responses` Branch-A plumbing, same
  world coverage), `INFRA-258` (kernel tick-alignment fix — `belief_assimilated`/`belief_updated`/
  `calamity_spawned`/`GovernorModeChanged`), `INFRA-259`/`INFRA-260` (Branch B code-correctness,
  not shipped in any calibration profile — not this ticket's concern)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/` — original Pattern-6 scaffolding
  plan/investigation, including the corrected `knowledge_scopes` vocabulary discovery
- `stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/` — Branch-A plumbing plan/
  investigation, the kernel tick-alignment bug investigation
  (`tick_alignment_bug_investigation.md`), and the exact bug-fix methodology (3 one-line
  `prior_state.tick` comparisons) to reuse if a 4th causally-linked bug surfaces in a new world's
  configuration
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/` — per-world archetype-matching
  judgment-call precedent for the 6 INFORMATION-fit worlds already covered (including the 2
  documented "INFORMATION skip" judgment calls for `dungeon_crawl`/`wilderness_survival`)
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/` — `frontier_marches`
  authored-from-inception precedent + the `crowded_frontier`/`resource_dense_basin` tier-purity
  default rationale

## Related Code Areas
- `src/domains/information/phase.py:27-110` — `InformationBeliefPhase.apply()`; confirmed Branch A
  (lines 45-81, the `pending_responses`/`resp_by_actor` path) is generically reachable for any
  world that seeds a matching `pending_information_responses` entry — the branch logic itself has
  no `urban_political`-specific special-casing, it iterates `state.entities.values()` and matches
  on `actor.id`, so reachability depends only on the compile-time seed being present and targeting
  a real compiled `actor_id`, exactly as `INFRA-257` documents for the 6 already-extended worlds
- `src/domains/information/schema.py:24-54` — `InformationSourceProfile`, `InformationSourceKind`
  enum (GUIDE, GUILD, BLACKSMITH, TRAVELER), `InformationQuery`
- `src/domains/information/router.py:22` — `InformationQueryRouter`; `matches_scope()`'s hard-coded
  recognized `knowledge_scopes` vocabulary (`common_resource_sources`, `recipe_requirements`,
  `regional_danger`) — any new world's profile content must use these literal strings, not invented
  ones
- `src/domains/information/normalizer.py`, `src/domains/information/assimilation.py` — Branch A's
  already-tested normalize/assimilate logic, reused unmodified by this ticket
- `src/cognition/self_model_phase.py:27-56` — `SelfModelUpdatePhase.apply()`; the `events=[]`
  hardcoding is already fixed per `INFRA-259`, not touched by this ticket (Branch A doesn't route
  through this phase)
- `src/engine/pipeline.py:152` — `ENABLE_BELIEF_ASSIMILATION` gate for `InformationBeliefPhase`;
  the merge-wrapper fix from `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` is already shipped
- `src/observability/event_extractor.py:286` — `belief_assimilated`/`belief_updated` `==
  prior_state.tick` comparison (kernel tick-alignment fix, already shipped, `INFRA-258`)
- `src/worldbuilding/schema.py` — `InformationSourceProfileSpec`, `PendingInformationResponseSpec`,
  `WorldSpec.information_source_profiles`/`.pending_information_responses` (confirmed in place,
  reusable as-is)
- `src/worldassembly/schema.py` — `WorldCompositionSpec`/`NormalizedWorldComposition` mirrors of the
  same fields (confirmed mirrored, reusable as-is)
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()` (constructs `InformationSourceProfile`
  list + resolves `target_population_id` -> compiled `actor_id` for
  `pending_information_responses`)
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver.assemble()` (passthrough, no
  merge/override logic — no catalog exists for this content, unlike factions)
- `data/worlds/*/world.yaml` — the 8 remaining un-authored candidates' composition files (exact set
  to be re-confirmed by Investigate — `dungeon_crawl`, `wilderness_survival` [documented structural
  skip], `crowded_frontier`, `resource_dense_basin` [Stress tier-purity], `simq_routing_test`
  [Regression/baseline], `hero_guild_routing`, `unit_faction_tension`, `unit_selfmodel_pilot` [Unit
  tier, each isolating a different single mechanic])
- `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`)
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-256`/`INFRA-257` entries to extend

## Assumptions / Open Questions
- **UQ-1 (high severity — likely invalidates this ticket's scope as written, more so than the
  FACTION sibling's equivalent finding):** The roadmap's Phase 3 framing treats INFORMATION as
  activated in one world (`urban_political`) with 2-3 more worlds as the remaining work. This is
  stale as of this ticket's filing (2026-07-10): **9 of 17 corpus worlds already have
  `information_source_profiles`/`pending_information_responses` authored, calibrated, and
  grade-anchored** (`urban_political`, the 6 `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`
  worlds, `frontier_marches`, `unit_information_source` — confirmed directly against
  `data/worlds/*/world.yaml`, `config/simulation_quality/profiles/*.yaml`, and
  `docs/parity_ledger/infrastructure.yaml::INFRA-256`/`INFRA-257`, not just the roadmap doc).
  **Of the remaining 8 worlds, every one already has a documented, pre-existing reason to stay
  INFORMATION-inert, per docs already in the repo (not a new judgment call this ticket would need
  to make):** `dungeon_crawl`/`wilderness_survival` have a documented **structural** INFORMATION
  skip (no settlement-adjacent module — `eval_matrix_results.md`'s own per-world write-ups call
  this out explicitly, distinct from a tier-purity choice); `crowded_frontier`/`resource_dense_basin`
  (Stress tier) have a documented INFORMATION=C tier-purity default (isolate scale/composition as
  the sole variable); `simq_routing_test` (Regression/baseline) is a "do not touch" purpose-built
  AGENCY fixture; `hero_guild_routing`/`unit_faction_tension`/`unit_selfmodel_pilot` (Unit tier)
  each isolate one different, non-INFORMATION mechanic by design. **This means the honest reading of
  current repo state is that zero worlds are currently undisputed, archetype-appropriate INFORMATION
  candidates** — tighter than the FACTION sibling ticket's finding (which left open the possibility
  Investigate might still find something). **If Investigate confirms this, this ticket cannot
  proceed as scoped and must return to Scope for a revision** (e.g., close as already-satisfied by
  prior work with 9/17 coverage documented as the intentional staged-depth bar, request a
  deliberate tier-taxonomy exception for one Stress-tier world with explicit justification, or fold
  into the roadmap's Phase 5 Coverage Decision Gate instead). This is not a reason to skip filing
  the ticket now (per the orchestrating instruction this is pre-filed for later pickup), but
  Investigate must resolve it — with a fresh, live re-check of `data/worlds/` and the taxonomy
  doc's currency, not by trusting this ticket's own snapshot — before any content-authoring step
  runs.
- UQ-2: If UQ-1 resolves with zero legitimate candidates, should this ticket close as
  already-satisfied (9/17 is the honest staged-depth bar), or should it be re-scoped to formally
  propose a tier-taxonomy exception (e.g., justify overriding one Stress-tier world's INFORMATION=C
  default)? Left to Investigate/Plan — default assumption if unresolved is to close/re-scope rather
  than force an inappropriate exception, mirroring the FACTION sibling's UQ-2 default.
- UQ-3: `docs/simulation_quality/corpus_tier_taxonomy.md` is dated "as of 2026-07-07" and
  `eval_matrix_results.md`/`docs/parity_ledger/infrastructure.yaml` may have further updates since
  this ticket's filing (2026-07-10) — Investigate must verify all three against live
  `data/worlds/*/world.yaml` content, not trust any of them as current without a spot-check.
- UQ-4: If UQ-1 unexpectedly resolves favorably (Investigate finds a genuine settlement-adjacent
  module in a nominally-protected world that was missed by this ticket's scoping pass, or the
  taxonomy itself has moved since 2026-07-07), budget real risk for a 4th causally-linked
  engine/cognition-pipeline bug surfacing in that world's specific configuration, per the documented
  precedent (`urban_political`'s activation alone surfaced 3). Track any such finding as its own
  ticket per Scope item 8/Out of Scope, not folded into this one.
- `layer: world` was chosen over `layer: simulation` to match this ticket's actual mechanism
  (per-world content authoring in `data/worlds/`), mirroring the FACTION sibling ticket's and
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s own `layer: world` choice, rather than
  `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`'s/`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`'s
  `layer: simulation` (which did engine-level schema/compiler/resolver/kernel work, not applicable
  here since that plumbing and the bug-fix chain are already built and shipped).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
