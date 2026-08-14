---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY
artifact_type: investigation
tags: [simulation-quality, agency, adventure, corpus, calibration]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY

## Current Behavior

**Feature flag mechanism** (`src/domains/optimization/feature_flags.py:4-48`): `FeatureFlagManager`
holds a dict of 10 flags, all defaulting to `FeatureMode.OFF`, including
`ENABLE_ADVENTURE_ROUTING` (line 16). `is_enabled()` returns true for `ON`/`STRICT`.

**Profile-driven activation** (`tools/calibrate_simq.py:44-64` `_load_profile_feature_flags()`,
`:142-211` `_run_engine()`): reads `config/simulation_quality/profiles/<profile>.yaml`'s
`feature_flags:` block generically (`{str(k): str(v) for k, v in raw.get("feature_flags", {}).items()}`),
then at `_run_engine()` line 205-211 applies each recognized flag name (`_KNOWN_FLAGS` includes
`ENABLE_ADVENTURE_ROUTING`) as a `FeatureMode` override, profile value first, env var second. This
is fully generic — no scenario-name string matching. `tools/evaluate_simq.py` (current on-disk
state, post `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`) has **no** `ROUTING_KEYS` set and no
routing-specific branch in `_run_calibration()` (confirmed by reading the file: `_run_calibration()`
only does an `sys.argv` monkey-patch/restore around `cal_mod.main()`, ll. 65-79) — the hardcoded
special case cited in that ticket's Request Summary is genuinely gone.

**Gate in the pipeline**: `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py:51-162`)
is invoked from `src/engine/pipeline.py` wrapped in `run_phase("adventure_decision", ...,
"ENABLE_ADVENTURE_ROUTING")`, which short-circuits before `apply()` runs when the flag is OFF. When
ON, it evaluates each alive/active hero not under an unexpired strategic-project lock, generates
route candidates via `AdventureRouteGenerator.generate()` (opportunities from
`ResourceOpportunityProvider.get_opportunities()`), scores them via `AdventureDecisionService.decide()`,
and either commits a `StrategicUpdate` (route selected) or writes `last_defer_reason`/`last_defer_tick`
via `EntityUpdate.property_updates` (deferred, `RouteFamily.DEFER_WITH_REASON`).

**Found-state artifacts already on disk** (untracked, from the paused prior attempt):
- `config/simulation_quality/profiles/hero_guild_routing.yaml` — exactly `feature_flags:
  {ENABLE_ADVENTURE_ROUTING: "ON"}`, no other content. Uses the generalized mechanism correctly —
  identical shape to `simq_routing_test.yaml`'s own post-migration block.
- `data/worlds/hero_guild_routing/world.yaml` — `world_id: "hero_guild_routing"`, 5 modules
  (`frontier_village_core` order 0, `hero_adventurers` order 1, `mountain_pass` order 2,
  `ruins_mystery_quest` order 3, `goblin_camp_conflict` order 4), `generation_seed: 717`. Description
  text explicitly frames "dispatches adventuring parties across three competing destinations...
  choosing between routes rather than following one linear path. Adventuring and route-selection are
  the world's central framing" — genuinely route-selection-framed, not generic, and explicitly
  contrasts itself against `urban_political`'s and `dungeon_crawl`'s framings in-line.
- `data/worlds/hero_guild_routing/world_compile_report.json` — `entity_count: 31, region_count: 4,
  resource_node_count: 4, building_count: 5, quest_count: 10, distinct_populated_factions: 5,
  warnings: [], state_hash: abf2009e...`. Zero warnings confirmed by direct file read, not assumed.
- `data/worlds/world_index.json` — `hero_guild_routing` entry present and well-formed (`world_id`,
  `name`, `path: "hero_guild_routing/world.yaml"`, `schema_version`, `status: "COMPOSITION"`,
  timestamps), same shape as all 14 other registered worlds.

**Comparables** (read directly, not assumed from the ticket text):
- `urban_political` (`data/worlds/urban_political/world.yaml` + its `world_compile_report.json`):
  `entity_count: 30, region_count: 3`, description "Settlement-heavy world with faction relationships
  and trade pressure" — no adventuring/routing language.
- `dungeon_crawl`: `entity_count: 32, region_count: 4`, description "Quest-dense danger world...
  pure dungeon exploration with escalating bandit threat" — no adventuring/routing language either.
- `hero_guild_routing`: `31/4` — sits almost exactly between the two comparables on both axes, and
  is the only one of the three whose description text uses "adventuring"/"route-selection" language.

## Mechanics / Engine Constraints

- `docs/mechanics/adventure_routing_contract.md` — companion to `04_strategic_cognition.md`;
  defines the `RouteFamily` taxonomy and the `defer_with_reason` empty-candidate-set fallback as
  **intended** behavior when a hero has zero legal routes (not a bug). This directly bears on the
  Anti-Drift Hazards below: this world's regions must give every hero at least one legal route
  family across its full lifespan, or defer/stasis dynamics (see Parity Ledger Overlap) will
  recur in a new location.
- `docs/simulation/domains/adventure_contract.md` — `AdventureDecisionPhase` "opt-in by world
  archetype, not a global default" framing; this ticket's new archetype category ("routing-capable,
  real-scale") is consistent with that contract's intent — it does not change the contract, only
  adds a second world that opts in.
- Population-stability law (`docs/simulation_quality/eval_matrix_results.md`, "Newly-Anchored
  Worlds" section; enforced by `tests/unit/worldassembly/test_corpus_diversity.py::
  test_population_stability`): every calibration-corpus world must hold >=60% of its starting
  `entity_count` alive at every 50-tick checkpoint through 300 ticks, driven via bare
  `Kernel.tick_once()` with **no feature-flag overrides applied** (`flags={"no_frame_pacing": True}`
  only — no `extra_flags`/profile feature_flags plumbing exists in this test). See Risks below —
  this means the existing regression-guard mechanism tests `hero_guild_routing` with
  `ENABLE_ADVENTURE_ROUTING` at its **default OFF** state, not the ON state the world's own profile
  sets. This is a genuine architectural gap the planner must resolve, not an oversight to paper
  over.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml`:
  - `INFRA-237` (AgencyScorer contract coverage) — `status: verified`, `support_boundary`
    already populated by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` with an archetype-block note citing
    `ENABLE_ADVENTURE_ROUTING`. This ticket does not change `AgencyScorer` itself, so no edit to
    `INFRA-237`'s evidence/status is required — but its `support_boundary` note currently frames
    `simq_routing_test` as the *sole* routing-capable exception; that language should be extended
    (additively) to name `hero_guild_routing` as a second exception, per this ticket's own
    Acceptance Criteria ("without altering its existing '9 non-routing worlds stay C' language").
  - `SIMQ-CALIBRATED-001` — event-emission wiring for `route_selected`/`action_executed`, also has a
    `support_boundary` populated by the same prior ticket. Same additive-extension consideration.
- No entries exist in `docs/parity_ledger/strategic_cognition.yaml` for AGENCY/route_* events
  (confirmed via the prior ticket's own UQ-1 resolution — grep returned zero matches there; this was
  independently re-confirmed for this investigation).
- No P0 entries are directly implicated — `INFRA-237` and `SIMQ-CALIBRATED-001` are both P1.
- `docs/parity_ledger/town_resource.yaml` — `TOWN-188` (added by
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`) documents the global `hometown` resource-tag
  fix this world's `frontier_village_core` module automatically inherits (see Anti-Drift Hazards).
  No edit needed here — it is a global catalog fact this world benefits from, not a per-world entry.

## Prior Work

- `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` (done, `tickets/done/`) — built exactly the
  mechanism this ticket depends on. Its own Implementation Notes confirm: `ROUTING_KEYS` removed
  from `evaluate_simq.py`, `simq_routing_test.yaml` migrated onto `feature_flags:`, all 3
  `simq_routing_test` seeds re-verified byte/grade-identical post-migration, `make evaluate-full`
  and `make evaluate` both 0 regressions. **Confirmed DONE and its mechanism confirmed live-working**
  by direct code read (see Current Behavior) — not merely trusted from the ticket's own claim.
- `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (done) — the ruling this ticket must not reverse. Confirmed:
  documentation-only, added the "AGENCY — Cross-World Design Note" section to
  `eval_matrix_results.md`, populated `support_boundary` on `INFRA-237`/`SIMQ-CALIBRATED-001`. No
  code changes. The 9 non-routing worlds' AGENCY=C framing is untouched by anything on disk today.
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done) — **closest structural precedent**,
  same batch, same "author one new unit-tier world activating one previously-OFF flag, run
  population-stability + 3-seed calibration, add anchors, update docs" shape. Its Implementation
  Notes give the exact mechanical checklist this ticket should follow:
  1. Add world_id to `POPULATION_STABILITY_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py`
     (currently: `list(ANCHORED_WORLD_BANDS.keys()) + ["unit_faction_tension",
     "unit_information_source", "unit_selfmodel_pilot"]` — `hero_guild_routing` is not yet present).
  2. Add 3 seed entries (42/123/456) to `grade_anchors.json` and to `FAST_ANCHOR_KEYS` in
     `tests/simulation_quality/test_grade_regression.py` (confirmed: neither list currently mentions
     `hero_guild_routing`).
  3. Add a new `### hero_guild_routing` subsection to `eval_matrix_results.md` with the measured
     grade table.
  4. Add a row to `docs/simulation_quality/corpus_tier_taxonomy.md`'s Unit-tier table (currently
     lists exactly 3 unit-tier worlds: `unit_faction_tension`, `unit_information_source`,
     `unit_selfmodel_pilot` — confirmed via direct grep, `hero_guild_routing` absent).
  5. Extend `INFRA-237`/`SIMQ-CALIBRATED-001`'s `support_boundary` notes additively (mirroring how
     SELFMODEL-PILOT amended `INFRA-259`'s `text` field with one appended clause, no other field
     touched).
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` (done) — sibling unit-tier ticket,
  establishes the `unit_faction_tension`/`unit_information_source` precedent for isolation
  philosophy (single-mechanic worlds) that this ticket's Out-of-Scope section explicitly follows.
- `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` + `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`
  (both done) — **critical prior-work context, not just background**. These found and fixed a
  genuine content gap: `simq_routing_test`'s heroes spawn in `hometown`, and until this fix no
  resource node was tagged `hometown` in `source_region_tags`, so any hero with `sociability < 0.2`
  (the `FORM_PARTY` gate, `generator.py:124`) had zero legal routes for its entire life, driving a
  sustained `defer_with_reason` stasis streak that collapsed AGENCY to `F` (seed456, pre-fix). The
  fix was a **global** catalog change (`data/content/world/resources.yaml`: `wood_node` and
  `herb_patch` both gained `"hometown"` in `source_region_tags`) — confirmed still present on disk
  today (`grep -n hometown data/content/world/resources.yaml` returns both entries). Because
  `hero_guild_routing` also composes `frontier_village_core` (the module that places heroes in
  `hometown`), it inherits this fix automatically. This does **not** guarantee the same class of gap
  is absent in this world's *other* 4 modules (`hero_adventurers`, `mountain_pass`,
  `ruins_mystery_quest`, `goblin_camp_conflict`) — see Risks.
- The ticket references `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
  §2/§3 repeatedly. **This path does not exist on disk** — `staging_artifacts/` currently contains
  only a `.gitkeep` and `TCK-20260702-SIMQ-UPLIFT2-INFORMATION/`; no `EPIC-SCOPE-full-feature-world-coverage/`
  directory exists anywhere in `staging_artifacts/` or `stored_artifacts/`. This is flagged as a gap,
  not silently worked around: the investigation.md this and several sibling done tickets cite as
  their primary source evidence is not independently verifiable from the current repo state (it was
  presumably read and then never migrated to `stored_artifacts/`, or was cleaned up already). This
  does not block this ticket — the specific facts attributed to it (30/3 urban_political, 32/4
  dungeon_crawl, hero_guild faction precedent) were independently re-verified above by reading the
  actual world files directly — but the planner should not cite that path as if it is readable.

### Found-State Evaluation

**Does the existing draft world satisfy Scope items 1-3? Yes, on the evidence read directly:**

1. **Scope 1 (hard dependency landed)**: Confirmed — `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`
   is in `tickets/done/`, and its generalized mechanism is live and working (verified by reading
   `calibrate_simq.py`'s `_load_profile_feature_flags`/`_run_engine` and `evaluate_simq.py`'s current
   lack of any `ROUTING_KEYS`/routing special case).
2. **Scope 2 (scale + framing)**: Confirmed — 31 entities/4 regions sits between `urban_political`
   (30/3) and `dungeon_crawl` (32/4) almost exactly as the ticket predicted, and the world.yaml
   description text genuinely reads as adventuring/route-selection-framed (explicitly names three
   competing destinations and contrasts itself against the other two worlds' framings in its own
   prose) — this is not a generic description.
3. **Scope 3 (flag ON via generalized mechanism, by design from first compile)**: Confirmed —
   `hero_guild_routing.yaml`'s only content is `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}`, and
   the world was compiled (`world_compile_report.json` exists, 0 warnings) using that profile from
   the start, not toggled on after an initial OFF compile.

**Verdict: keep-as-is, not rework.** The draft world composition, profile, and registration are all
architecturally sound and match the ticket's own scale/framing targets closely enough that
re-authoring from scratch would not produce a materially different result. The one caveat is
process, not content: this was compiled without a prior plan.md or architecture-review pass, so it
should be treated as implementer output that still needs an `architecture-reviewer` verdict before
Scope items 4-7 are built on top of it (per the ticket's own Implementation Notes) — that is a
planner/reviewer decision, not something this investigation resolves unilaterally.

## Risks and Open Questions

- **OQ-1 (blocking, needs a planner/architecture decision): population-stability test flag
  mismatch.** `test_population_stability` (the mechanism Scope item 4 is expected to reuse, per the
  SELFMODEL-PILOT precedent) constructs its `Kernel` with `flags={"no_frame_pacing": True}` only —
  it does not read a world's profile `feature_flags:` block, so `hero_guild_routing` would be
  stability-tested with `ENABLE_ADVENTURE_ROUTING` at its default OFF state, not the ON state that is
  this world's entire reason for existing. Options for the planner to choose between (not decided
  here): (a) accept the mismatch — population collapse is a survival-mechanic concern that this
  ticket's own precedent (`unit_selfmodel_pilot`) also tested without its own flag active, since the
  200-500-tick 3-seed calibration matrix (Scope 5) already exercises the true ON-flag dynamics over
  a comparable tick range and would itself surface a collapse; or (b) generalize
  `test_population_stability` to read each world's own profile `feature_flags:` block (mirroring
  `calibrate_simq.py`'s own mechanism) before constructing the `Kernel`, which is more correct but is
  a test-harness change beyond a single-ticket world-authoring scope. Do not silently pick one without
  surfacing this to the plan.
- **OQ-2 (needs verification during Plan/Implement, not blocking scope): resource-tag coverage for
  the 3 new-to-this-world modules.** The `hometown`-gap precedent (see Prior Work) proves this class
  of bug is real and has happened before with the exact `frontier_village_core` module this world
  reuses. `mountain_pass`, `ruins_mystery_quest`, and `goblin_camp_conflict` are new combinations for
  a routing-active world — nobody has confirmed their region(s) have adequate `source_region_tags`
  coverage for whatever route families heroes are expected to pursue there. The compile report's 0
  warnings only proves structural validity (references resolve), not that every region offers a
  legal route. This should be explicitly checked (e.g. via `ResourceOpportunityProvider
  .get_opportunities()` inspection per-region, mirroring the HOMETOWN-RESOURCE-GAP ticket's own
  verification method) before or during the population-stability/calibration run, since a repeat of
  the stasis pattern in a different region would silently degrade the AGENCY grade this ticket exists
  to measure honestly.
- **OQ-3**: The `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` source
  document this ticket and several "Related Docs" references point to does not exist on disk (see
  Prior Work). If the planner or a future reader needs to re-verify a claim attributed to it beyond
  what this investigation already independently re-checked, that claim cannot currently be traced to
  source.
- Not a risk, but worth stating plainly: the process gap noted in the ticket's own Implementation
  Notes (world compiled before any `staging_artifacts/` existed) is confirmed real —
  `staging_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/` did not exist before this
  investigation created it just now.

## Anti-Drift Hazards

- **Do not let this ticket touch any of the 9 non-routing worlds' AGENCY grade.** The generalized
  `feature_flags:` mechanism is deliberately per-profile-file — a careless edit to a shared file
  (e.g. `default.yaml`) rather than `hero_guild_routing.yaml`'s own profile would leak the flag
  globally and violate the explicit Out-of-Scope / AC "None of the 9 existing non-routing worlds'
  AGENCY grades change" gate. `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/`
  should show only `simq_routing_test.yaml` and `hero_guild_routing.yaml` after this ticket, nothing
  else — mirror the exact grep the FLAG-GENERALIZE ticket ran as its own verification step.
- **Do not silently pick a `data/calibration/*` grade without noting the stasis-collapse precedent.**
  `simq_routing_test_seed456` collapsed to AGENCY=F/D before a content fix — an unlucky personality
  roll landing a hero with zero legal routes is a real, previously-observed failure mode for
  routing-active worlds, not a hypothetical. If any of `hero_guild_routing`'s 3 seeds shows an
  anomalously low AGENCY grade, the correct response (per precedent) is to investigate the specific
  entity/route-availability chain before accepting or "fixing" the grade, not to assume it is a
  scoring-formula issue.
- **Do not conflate this ticket's grade-anchor additions with a rewrite of the AGENCY Cross-World
  Design Note.** The note's existing "9 non-routing worlds stay C" and `simq_routing_test`
  calibration-harness framing must be preserved verbatim; this ticket only adds a new subsection/
  paragraph naming `hero_guild_routing` as a second, distinct routing-capable archetype (real-scale,
  not calibration-minimal) — additive, not a rewrite, mirroring exactly how
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` appended a bracketed status update to the
  same note rather than rewriting it.
- **Do not seed FACTION/INFORMATION/self-model content into this world** (explicit Out-of-Scope) even
  though the world's 5 populated factions and `hero_guild` faction reuse might tempt adding
  `faction_tension_overrides` or `information_source_profiles` blocks the way `urban_political` has —
  this world's isolation-tier philosophy (per `corpus_tier_taxonomy.md`'s Unit-tier definition)
  requires staying single-mechanic unless a specific archetype reason is found and justified in the
  plan.
- **Do not hand-wave the 200 vs 500 tick decision (UQ-1).** The ticket defaults to 500t matching
  `simq_routing_test`'s calibration length "since route/goal-selection dynamics may need more ticks
  than the 200-tick default to show signal" — but `unit_selfmodel_pilot`'s own precedent used 200-300
  ticks successfully for a different flag. This is a real design choice with a stated rationale, not
  a default to change without re-justifying.


---

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This doc's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
and/or its later rename, `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`, point
to a pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact drawn
from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` and/or `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.
