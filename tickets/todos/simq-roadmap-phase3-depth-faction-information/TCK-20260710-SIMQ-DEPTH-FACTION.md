---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-FACTION
phase: open
date: 2026-07-10
tags: [simulation-quality, faction, world, corpus, calibration]
---

# TCK-20260710-SIMQ-DEPTH-FACTION

## Title
Extend FACTION pillar depth (Pattern 6 tension seeding) to 2-3 more corpus worlds — Phase 3 Depth Wave 2 (FACTION half)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is the FACTION half of `docs/plans/simq_development_roadmap.md` Phase 3 ("Depth Wave 2:
FACTION + INFORMATION"). The roadmap's stated premise is that FACTION tension seeding is proven
in one world (`urban_political`, via `TCK-20260702-SIMQ-UPLIFT2-FACTION`) and that the remaining
work is per-world content authoring using the already-reusable Pattern-6 compiler plumbing
(`FactionSpec.initial_tension_level` + `WorldCompositionSpec`/`NormalizedWorldComposition
.faction_tension_overrides`, documented in `docs/guidelines/design_patterns.md` Pattern 6).

**This premise is stale as of this ticket's filing — see Conflict Report / Assumptions below.**
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (done, 2026-07-04/07) already authored bespoke
`faction_tension_overrides` into 8 more worlds, and `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`
authored a 9th (`frontier_marches`) from inception. Combined with `urban_political` and the
unit-tier `unit_faction_tension`, **11 of the 17 corpus worlds already have FACTION tension
content authored and calibrated** (grades verified S/A per
`docs/simulation_quality/eval_matrix_results.md`'s "FACTION/INFORMATION Content Expansion"
section). This ticket's Investigate phase must re-establish, against current repo state (not
against the roadmap doc's 2026-07-10 snapshot), which worlds remain genuine, archetype-appropriate
FACTION candidates before any content authoring begins — see Assumptions/Open Questions UQ-1.

The compiler-level fix itself (Pattern 6) is confirmed still reusable as-is with zero engine
changes required: `FactionSpec.initial_tension_level` (`src/worldbuilding/schema.py:52-55`) and
`WorldCompositionSpec.faction_tension_overrides` / mirrored `NormalizedWorldComposition
.faction_tension_overrides` (`src/worldassembly/schema.py:40-43,168-171`) are already in place and
already used by 11 worlds — this ticket's remaining work, if UQ-1 resolves favorably, is
per-world content authoring (`faction_tension_overrides` entries judged against each candidate
world's actually-populated factions, per the archetype-matching discipline
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` established) plus recalibration and a
corpus-wide regression sweep — not new schema/compiler/resolver work.

## Scope
1. **Investigate phase (required first step, before any content authoring):** re-verify current
   FACTION coverage across all 17 corpus worlds against `docs/simulation_quality
   /corpus_tier_taxonomy.md`'s "Current tier mapping" table and `eval_matrix_results.md` (both may
   themselves be slightly stale by the time this ticket is picked up — verify against
   `data/worlds/*/world.yaml` directly). Identify the actual remaining candidate set.
2. Select 2-3 archetype-appropriate candidate worlds from whatever remains after step 1, with
   plausible multi-faction, conflict-adjacent archetypes — real archetype analysis against each
   candidate's actually-populated factions (per the `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`
   precedent's per-world judgment-call discipline: do not copy `urban_political`'s exact
   faction/value pairs into a world where those factions aren't populated).
3. For each selected world: seed `faction_tension_overrides` via the existing Pattern-6 schema/
   compiler/resolver plumbing (confirmed reusable, no new engine work expected — if Investigate
   finds otherwise, pause for a plan revision rather than push through, per the roadmap's explicit
   instruction).
4. Recalibrate each selected world (3-seed matrix, following the corpus's existing calibration
   pattern) and add/update grade-anchor entries in `tests/simulation_quality/fixtures
   /grade_anchors.json` + `FAST_ANCHOR_KEYS`.
5. Run a corpus-wide regression sweep (`make evaluate` / `make evaluate-full` as appropriate —
   FACTION content-only changes have historically stayed FACTION/INFORMATION/COGNITION-scoped per
   `eval_matrix_results.md`, but sweep the full corpus anyway per the roadmap's explicit
   instruction, since Pattern-6 activation history shows adjacent pillars can shift as a side
   effect).
6. Update `docs/simulation_quality/eval_matrix_results.md` and `corpus_tier_taxonomy.md` with the
   new worlds' grade tables/tier notes.
7. Extend `docs/parity_ledger/faction.yaml`'s `FAC-012` entry's `v2_evidence`/`test_path` with the
   newly selected worlds (mirroring how `FAC-012` already documents `frontier_marches` as a second
   data point beyond `urban_political`) rather than creating a new parity entry, unless Investigate
   finds a reason a new entry is warranted.
8. Track any newly-discovered engine bug as its own ticket rather than folding it into this
   ticket's scope (per the roadmap's explicit instruction, mirroring the INFORMATION-side
   precedent where 3 causally-linked kernel bugs surfaced during `urban_political` activation).

## Out of Scope
- The INFORMATION half of this Phase 3 wave — filed as a sibling ticket in this same
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/` folder; can run independently
  (different content domain) but both cite `docs/plans/simq_development_roadmap.md` Phase 3.
- Any new schema/compiler/resolver engine work — Pattern 6 plumbing is confirmed reusable as-is;
  if Investigate finds it insufficient, that is new information requiring a plan revision, not
  in-scope engineering to push through under this ticket's original estimate.
- Adding FACTION content to `crowded_frontier` or `resource_dense_basin` (Stress tier) unless
  Investigate explicitly justifies overriding their documented "tier-purity default" (deliberately
  FACTION=C, per `corpus_tier_taxonomy.md`, to isolate scale/composition as the sole variable) —
  default assumption is these stay out of scope.
- Adding FACTION content to `simq_routing_test` (purpose-built AGENCY calibration fixture, not a
  shipped-gameplay archetype) or `hero_guild_routing`/`unit_information_source`/
  `unit_selfmodel_pilot` (Unit tier, each isolates a different single mechanic by design).
- Expanding `data/content/social/faction_relationships.yaml`'s global relationship density
  (already done corpus-wide by `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`, 34→75 entries,
  51.5% populated-pair coverage) — this ticket is per-world `initial_tension_level`/
  `faction_tension_overrides` seeding only, not the global relationship catalog.
- Changing FACTION scoring weights/thresholds.
- Diplomatic event gameplay beyond tension seeding (alliances, war declarations, siege mechanics).
- Authoring any further unit-tier isolation world (that pattern is already covered by
  `unit_faction_tension`).

## Acceptance Criteria
- [ ] Investigate phase produces a re-verified candidate list (against current `data/worlds/`
      state, not the roadmap doc snapshot) of 2-3 archetype-appropriate worlds genuinely lacking
      FACTION tension content, with the stale-premise gap (11/17 worlds already covered) explicitly
      reconciled before any content authoring begins
- [ ] Each selected world has >=2 non-zero `faction_tension_overrides` entries on catalog-registered
      factions actually populated in that world, archetype-justified (not copy-pasted from another
      world's values)
- [ ] Each selected world compiles with 0 warnings (`world_compile_report.json`) and holds >=60%
      population-alive floor through at least 200-300 ticks at seed 42
- [ ] Each selected world's FACTION grade moves measurably off `C` (calibration_hits > 0 for
      `diplomatic_transition` or `faction_tension_delta`) across a 3-seed calibration matrix, with
      grade-anchor entries added to `grade_anchors.json`/`FAST_ANCHOR_KEYS`
- [ ] `make evaluate` (full corpus sweep, not just `--dry-run`) exits 0 with 0 regressions
- [ ] `docs/parity_ledger/faction.yaml` `FAC-012` extended (or a justified new entry added) with
      `v2_evidence` covering the newly selected worlds
- [ ] `eval_matrix_results.md` and `corpus_tier_taxonomy.md` updated with the new worlds' grade
      tables/tier notes
- [ ] Any newly-discovered engine bug is filed as its own ticket, not silently folded into this
      one's scope

## Related Tickets
- `docs/plans/simq_development_roadmap.md` Phase 3 — parent roadmap phase (both FACTION and
  INFORMATION halves)
- **Sibling ticket (INFORMATION half of this same Phase 3 wave)** — filed in parallel in this same
  `tickets/todos/simq-roadmap-phase3-depth-faction-information/` folder; different content domain,
  can run independently, but both should be picked up together per the roadmap's Phase 3 framing
- `TCK-20260702-SIMQ-UPLIFT2-FACTION` (done) — original Pattern-6 compiler fix + `urban_political`
  seeding; this ticket extends the same plumbing to more worlds
- `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC` (done) — documented Pattern 6 in
  `docs/guidelines/design_patterns.md`
- `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (done) — **already extended FACTION content to
  8 more worlds**; this is the stale-premise conflict this ticket's Investigate phase must
  reconcile first (see Request Summary / Assumptions UQ-1)
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` (done) — authored `frontier_marches` with
  `faction_tension_overrides` from inception (9th world with FACTION content)
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done) — authored `unit_faction_tension`
  (unit-tier FACTION isolation world); explicitly out of scope to duplicate here
- `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS` (done) — expanded the *global*
  `faction_relationships.yaml` catalog (34→75 entries); a different, already-closed content
  domain from this ticket's *per-world* `faction_tension_overrides` seeding
- `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (done) — defines the tier taxonomy this ticket's
  candidate-world selection must respect (do not seed FACTION into Stress/Unit tier worlds without
  explicit justification)
- `docs/plans/simq_development_roadmap.md` Phase 2 (SOCIAL, filed as
  `tickets/todos/simq-roadmap-phase2-depth-social/`) — precedent wave this Phase 3 wave's shape
  follows; its actual cost should sanity-check this ticket's effort budget once it closes

## Related Docs
- `docs/plans/simq_development_roadmap.md` — Phase 3 section (source of this ticket)
- `docs/guidelines/design_patterns.md` — Pattern 6 ("Compile-Time Pillar Activation Pattern")
- `docs/simulation_quality/quality_scoring_contract.md` §5 — FACTION pillar definition (Faction &
  Military: diplomacy, military conflict, territory)
- `docs/simulation_quality/corpus_tier_taxonomy.md` — tier definitions and current per-world
  tier/content mapping; authoritative source for which worlds already have FACTION content
- `docs/simulation_quality/eval_matrix_results.md` — "FACTION/INFORMATION Content Expansion"
  section (8-world grade tables) and "Stress-Tier Worlds" / "Unit-Tier Isolation Worlds" sections
- `docs/guides/feature_flags.md` — FACTION tension seeding itself is not flag-gated (unlike
  `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION`), but candidate worlds' other active
  flags should be checked for cross-pillar interaction risk
- `docs/parity_ledger/faction.yaml` — `FAC-012` (compile-time tension seeding, already covers
  `urban_political` + `frontier_marches`), `FAC-001` (cross-referenced), `FACTION-TENSION-001`
  (a distinct, already-verified runtime mechanism — `FactionAwarenessService
  .compute_tension_updates()` reacting to `RESOURCE_DEPLETED` events — not touched by this ticket)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — original Pattern-6 fix plan/investigation
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/` — per-world archetype-matching
  judgment-call precedent for the 8 worlds already covered
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/` — `frontier_marches` authored-from-
  inception precedent
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — compile/verify/anchor workflow
  reference

## Related Code Areas
- `src/worldbuilding/schema.py:49-55` — `FactionSpec.initial_tension_level` (confirmed in place,
  bounded `[0.0, 1.0]`, reusable as-is)
- `src/worldassembly/schema.py:40-43,168-171` — `WorldCompositionSpec.faction_tension_overrides` /
  `NormalizedWorldComposition.faction_tension_overrides` (confirmed mirrored, reusable as-is)
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()` (constructs `FactionState` per
  `FactionSpec`, seeded from `initial_tension_level`)
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver.assemble()` (applies
  `faction_tension_overrides` post module-merge)
- `data/worlds/*/world.yaml` — the 6 remaining un-authored candidates' composition files (exact
  set to be re-confirmed by Investigate — likely subset of `hero_guild_routing`, `crowded_frontier`,
  `resource_dense_basin`, `simq_routing_test`, `unit_information_source`, `unit_selfmodel_pilot`,
  pending tier-purity justification per Out of Scope)
- `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`)
- `docs/parity_ledger/faction.yaml` — `FAC-012` entry to extend

## Assumptions / Open Questions
- **UQ-1 (high severity — may invalidate this ticket's scope as written):** The roadmap's premise
  ("FACTION is currently active in only `urban_political`") is factually stale as of this ticket's
  filing (2026-07-10): 11 of 17 corpus worlds already have `faction_tension_overrides` authored
  and calibrated (`urban_political`, the 8 `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` worlds,
  `frontier_marches`, `unit_faction_tension`). Of the remaining 6 worlds, `crowded_frontier` and
  `resource_dense_basin` (Stress tier) and `simq_routing_test`/`hero_guild_routing`/
  `unit_information_source`/`unit_selfmodel_pilot` (Unit/Regression-baseline tier) each have a
  documented tier-purity reason to stay FACTION-inert. **If Investigate confirms no remaining
  world is a legitimate, tier-appropriate FACTION candidate, this ticket cannot proceed as scoped
  and must return to Scope for a revision** (e.g. re-scope as a stress/unit-tier tier-purity
  exception with explicit justification, or close as already-satisfied by prior work, or fold into
  the roadmap's Phase 5 Coverage Decision Gate instead). This is not a reason to skip filing the
  ticket now (per the orchestrating instruction this is pre-filed for later pickup), but Investigate
  must resolve it before any content authoring step runs.
- UQ-2: If UQ-1 resolves with fewer than 2 legitimate candidates, should this ticket's target count
  drop below the roadmap's "2-3 worlds" framing, or should it request a tier-purity exception for
  one of the Stress-tier worlds? Left to Investigate/Plan — default assumption if unresolved is to
  proceed with however many legitimate candidates exist (even if only 1) rather than force an
  inappropriate tier-purity exception.
- UQ-3: `docs/simulation_quality/corpus_tier_taxonomy.md` is dated "as of 2026-07-07" and
  `eval_matrix_results.md` may have further updates since — Investigate must verify both against
  live `data/worlds/*/world.yaml` content, not trust either doc as current without a spot-check.
- `layer: world` was chosen over `layer: simulation` to match this ticket's actual mechanism (per-
  world content authoring in `data/worlds/`), mirroring `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-
  EXPANSION`'s and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s own `layer: world` choice,
  rather than `TCK-20260702-SIMQ-UPLIFT2-FACTION`'s `layer: simulation` (which did engine-level
  schema/compiler/resolver work, not applicable here since that plumbing is already built).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
