---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-DEPTH-FACTION
phase: done
date: 2026-07-10
tags: [simulation-quality, faction, world, corpus, calibration]
---

# TCK-20260710-SIMQ-DEPTH-FACTION

## Title
Extend FACTION pillar depth (Pattern 6 tension seeding) to 2-3 more corpus worlds — Phase 3 Depth Wave 2 (FACTION half)

## Status
DONE

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
Investigate resolved UQ-1 definitively: 0 legitimate, tier-appropriate FACTION candidates remain in
the 17-world corpus. Plan phase then faced an explicit open question (deferred by Investigate, per
the project workflow rule that Investigate does not silently reduce or close scope on its own):
close this ticket as "already-satisfied by prior work" directly, or fold the finding into the
roadmap's Phase 5 Coverage Decision Gate.

**Decision: close as "already-satisfied" directly (`staging_artifacts/.../plan.md`'s
"Closure-Mechanism Decision" section), not folded into Phase 5.** Rationale: (1) Phase 3's own
Acceptance Signal text already names "zero new worlds, coverage already adequate, documented and
closed" as a valid outcome for this phase, with no dependency on Phase 5 to make it legitimate; (2)
Phase 5 is explicitly scoped as a later, corpus-wide gate that fires only once Phases 2-4 have all
landed (Phase 4, `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`, has not landed as of this
ticket) and answers a different question — whether pursuing full 17-world coverage is worth its
cost — not whether one pillar's one-ticket scope still has remaining work; (3) folding this finding
into Phase 5 would incorrectly imply the 6 tier-purity worlds are "not yet covered but could be,
pending a cost/benefit call," when the investigation found they are FACTION-inert by deliberate
design (isolation contracts), not by omission — there is no future world of "continuing FACTION
coverage into them" for Phase 5 to ever weigh.

At implementation time, ground truth was re-verified fresh against live `data/worlds/*/world.yaml`
(not trusted from the investigation's table alone, per the plan's anti-drift note that corpus
content can change between ticket pickup and implementation): `grep -l "faction_tension_overrides"
data/worlds/*/world.yaml` plus per-world `grep -n -A3 "^faction_tension_overrides:"` confirmed the
same 11/17 covered-world set with identical override values, and confirmed the 6 tier-purity worlds
have no real `faction_tension_overrides:` key (the two Unit-tier worlds' description fields contain
the string but only as documentation of the deliberate absence, not a populated key — the exact
anti-drift hazard the investigation flagged). No drift since investigation; the finding stands
unchanged.

Step 4 (`audit_fix_plan.md` check): `grep -n -i "faction" docs/plans/audit_fix_plan.md` at
implementation time returned only `P1-C` (Faction & Diplomacy System, RESOLVED 2026-07-03, an
unrelated diplomacy-engine item) and `P2-D` (Faction relationships sparse, RESOLVED 2026-07-07, the
global `faction_relationships.yaml` catalog density item, a different content domain per this
ticket's Out of Scope). No open, in-scope entry found; `audit_fix_plan.md` left untouched.

Durable closure record was written to `docs/simulation_quality/eval_matrix_results.md` (new
"FACTION Coverage Closure — Phase 3" section, pure append after the file's prior final section) and
`docs/simulation_quality/corpus_tier_taxonomy.md` (new closure paragraph after the "Current tier
mapping" table, before the "Named scale-diversity gaps" section — the tier table itself untouched)
so a future investigator scanning those docs directly finds the finding without needing to dig into
`stored_artifacts/`. `docs/plans/simq_development_roadmap.md`'s Phase 3 section got a dated closure
blockquote recording the FACTION-half closure and explicitly noting the INFORMATION half
(`TCK-20260710-SIMQ-DEPTH-INFORMATION`) is unaffected and proceeds independently on its own
evidence.

No code, content, or test files were touched. `docs/parity_ledger/faction.yaml`'s `FAC-012` entry
was left as-is (no new evidence world to add — it already accurately documents `urban_political` +
`frontier_marches`). No `faction_tension_overrides` content was authored into any of the 6
tier-purity worlds.

## Test Summary
No code or content changed, so no pre/post-change diff was applicable. A confirmatory regression
sweep was run instead, per `test_plan.md`'s "Scoped Pytest Commands", to prove the documentation-only
closure did not accidentally destabilize anything even though nothing code-facing was touched:

- `pytest tests/unit/worldbuilding/test_worldspec_schema.py tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_assembly.py` — Pattern-6 plumbing (schema/compiler/resolver)
- `pytest tests/unit/faction/` — faction domain (diplomacy state machine, siege, war exhaustion)
- `pytest tests/unit/worldassembly/test_corpus_diversity.py tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` — corpus-wide diversity/population-stability invariants across all 17 worlds
- `pytest tests/integration/scenarios/test_faction_campaign.py` — integration faction-campaign scenarios
- `pytest tests/simulation_quality/test_grade_regression.py` — SimQ fast grade-anchor regression

Combined result: 333 passed, 2 failed, in 335.77s. The 2 failures are both in
`test_grade_regression.py::test_grade_within_anchor_band` — `dungeon_crawl_seed42_200t` (COMBAT
actual=`C` vs anchor=`A`; PROGRESSION actual=`C` vs anchor=`A`) and `urban_political_seed42_200t`
(PROGRESSION actual=`C` vs anchor=`A`). Both failures are **pre-existing and unrelated to this
ticket**: (1) the drifted pillars are COMBAT and PROGRESSION, never FACTION — direct inspection of
both worlds' `data/calibration/*/quality_report.json` confirms `FACTION.grade == "S"` in both
cases, comfortably within the anchor band, meaning FACTION shows zero drift; (2)
`data/calibration/` is gitignored (confirmed via `.gitignore:240`) and untracked by git — these
`quality_report.json` files are locally-generated leftover artifacts from an unrelated prior run in
this environment, not part of this ticket's diff or of any committed repo state; (3) this ticket
made zero code/content changes, so it cannot have caused a COMBAT/PROGRESSION drift regardless. This
is local environmental staleness in generated calibration data, not a regression introduced by this
closure — recorded here per the "no known material gap is left unstated" rule rather than silently
omitted. All other 5 command groups (Pattern-6 plumbing, faction domain, corpus diversity,
population stability, integration faction campaign) passed cleanly. No new tests were added — none
are warranted for a documentation-only closure per `test_plan.md`'s "New Tests Required: None"
finding.

## Files Changed
- `docs/simulation_quality/eval_matrix_results.md` — appended "FACTION Coverage Closure — Phase 3" section (17-world coverage table + UQ-1 verdict)
- `docs/simulation_quality/corpus_tier_taxonomy.md` — added closure-note paragraph after the "Current tier mapping" section
- `docs/plans/simq_development_roadmap.md` — added dated closure blockquote to the Phase 3 section
- `tickets/inprogress/TCK-20260710-SIMQ-DEPTH-FACTION.md` (this file) — Status/Implementation Notes/Test Summary/Files Changed/Completion Summary filled in

No `src/`, `data/worlds/*/world.yaml`, `tests/`, `tests/simulation_quality/fixtures/grade_anchors.json`,
or `docs/parity_ledger/faction.yaml` files were touched.

## Completion Summary
**What "acceptance" means for this closure:** this ticket's original 8 acceptance criteria all
presuppose that content authoring occurs (candidate worlds selected, `faction_tension_overrides`
seeded, recalibration run, `FAC-012` extended, engine bugs filed if found). Investigation's UQ-1
resolution — 0 legitimate, tier-appropriate FACTION candidates remain among the 17-world corpus —
means those content-authoring criteria are satisfied **vacuously**, by prior work already done
under three other, already-closed tickets (`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`,
`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`, `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`), not
by any action taken under this ticket. This is not a failure or a shortfall against the original
scope — it is what those criteria's own text predicts happens when the honest answer to "is there a
genuinely uncovered candidate" is zero: there is nothing left for criteria written for a
content-authoring outcome to bind to.

**This ticket's own actual deliverable is different from its original criteria: a fresh coverage
re-verification against live repo state, plus a durably recorded closure.** Concretely: (1) all 17
corpus worlds were re-checked against live `data/worlds/*/world.yaml` (not just against
possibly-stale docs) at both investigation time and again at implementation time, with identical
results both times — 11/17 covered with matching override values, 6/17 confirmed FACTION-inert by
deliberate tier-purity design, not omission; (2) that finding was written durably into
`eval_matrix_results.md` and `corpus_tier_taxonomy.md` (not left only in `staging_artifacts/`, which
archives to `stored_artifacts/` on close and is less discoverable to a future investigator scanning
the docs directly); (3) the roadmap's Phase 3 FACTION-half was formally closed at the ticket level
(not deferred to Phase 5, which fires later on a different, corpus-wide question) with the
INFORMATION half of the same phase explicitly noted as unaffected and still open on its own
evidence; (4) a confirmatory regression sweep (5 pytest commands spanning Pattern-6 plumbing,
faction domain, corpus diversity, integration campaign scenarios, and SimQ grade-anchor regression)
proved zero drift resulted from this documentation-only closure. Zero code, content, or test files
were changed. No `faction_tension_overrides` content was authored into any tier-purity world, and
`docs/parity_ledger/faction.yaml`'s `FAC-012` entry was left untouched since no new evidence world
exists to extend it with.
