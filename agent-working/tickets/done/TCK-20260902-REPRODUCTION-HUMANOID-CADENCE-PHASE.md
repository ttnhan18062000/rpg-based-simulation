---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
phase: done
date: 2026-09-02
tags: [lifecycle, engine]
---

# TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE

## Title
Human/humanoid reproduction cadence sub-phase — new WD-16 cycle, per-parent cooldown, NOT marriage-gated

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket 5 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION). This is the human/humanoid reproduction trigger path: a new cadence sub-phase (proposed WD-16) registered in `src/engine/cadence.py`'s `SystemCadence`, that periodically checks eligible ADULT, alive, same-location, same-race entity pairs with clear per-parent cooldowns and produces a birth. IMPORTANT — per an explicit 2026-08-31 plan-owner decision, this path does NOT require an active marriage contract as a precondition. The idea-32 atlas card's "gated on marriage" language is stale relative to the 2026-08-29 build-order decoupling of Marriage (idea 33) from Reproduction (idea 32); do not implement a marriage-contract check anywhere in this ticket, and flag the stale atlas card text for a doc correction. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA and TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE landing first (this path calls into the genetics inheritance step for the new entity's GeneticProfile).

## Scope
- Register a new cadence entry (proposed WD-16) in `src/engine/cadence.py`'s `SystemCadence`/`should_run()`, following the existing cadence-registration pattern used by other periodic system phases.
- On each cadence firing, evaluate eligible ADULT, alive, same-location, same-race entity pairs (cross-race pairing explicitly excluded per resolved design decision — same-race only).
- Eligibility requires: both entities ADULT life stage, alive, co-located, same race, and both individual per-parent cooldowns (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) clear.
- No marriage-contract check anywhere in this eligibility logic.
- On a successful pairing, produce a new entity via the existing builder path (`src/core/builder.py`, extended by TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA), recording `parent_a_id`, `parent_b_id`, `birth_tick`, `birth_city_id`, and calling into TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE's inheritance step for the new entity's `GeneticProfile`.
- Set both parents' per-parent cooldown fields on a successful birth.
- Seed a `SocialBond` between each parent and the child (reuses the seeding path from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA).
- Eligibility for the pairing is also suppressed when `compute_regional_scarcity()` for the birth region exceeds the region's cohort `migration_threshold` (0.7 default) — same population-pressure gate reused by the natural-creature path.
- Explicitly document (in Implementation Notes / a mechanics-doc note), not silently ignore, that individual births from this path do not yet feed back into the aggregate `population_cohorts` signal — that is closed by the final epic child ticket, TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE.

## Out of Scope
- Marriage as a precondition — explicitly excluded per the 2026-08-31 decision described above.
- The natural-creature and magical/demonic paths (separate tickets).
- The genetics inheritance formula itself — implemented in TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE, this ticket only calls into it.
- Closing the population-pressure feedback loop (nudging `population_cohorts` on birth) — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, the final child ticket.
- Correcting the stale "gated on marriage" text in `docs/brainstorm/rpg_feature_atlas.html`'s idea-32 card — note it as a disclosed gap for a small follow-up doc fix rather than editing the brainstorm doc as part of this ticket, unless Plan decides it's trivial enough to bundle in.

## Acceptance Criteria
- [x] A new WD-16-style cadence entry fires periodically per `SystemCadence`'s existing registration pattern.
- [x] Calling the reproduction check for two ADULT, alive, same-location, same-race entities with both per-parent cooldowns clear produces a new entity via the builder path, with `parent_a_id`, `parent_b_id`, `birth_tick`, `birth_city_id` correctly recorded and a `GeneticProfile` attached via TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE's inheritance step.
- [x] No marriage-contract state is read or checked anywhere in this eligibility path — verifiable by grep showing no `ContractKind.MARRIAGE`/`MarriageState` reference in the new code.
- [x] A `SocialBond` is seeded between each parent and the child at high familiarity/sentiment.
- [x] Both parents' per-parent cooldown fields are set on a successful birth, and a repeat check on the same pair before cooldown clears does not produce a second birth (test proves this).
- [x] Eligibility is suppressed when `compute_regional_scarcity()` exceeds the region's `migration_threshold` — test proves both allowed and suppressed cases.
- [x] `docs/mechanics/05_world_evolution.md` documents this cadence sub-phase, explicitly noting individual births do not yet feed the aggregate `population_cohorts` signal (until the closure ticket lands); a `docs/parity_ledger/world_dynamics.yaml` entry cites it.
- [x] A note is filed (ticket body or a small follow-up ticket, per Plan's judgment) flagging `docs/brainstorm/rpg_feature_atlas.html`'s idea-32 "gated on marriage" text as stale relative to the 2026-08-29 decoupling decision.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE (hard dependency — must land first, this ticket calls into its inheritance step)
- TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE (downstream sibling — depends on this ticket landing)
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT (related but explicitly NOT a dependency — Marriage and Reproduction are decoupled)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md (2026-08-29 build-order decoupling decision)
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card — "gated on marriage" text is stale, flag for correction)
- docs/mechanics/05_world_evolution.md
- docs/engine/kernel.md (cadence/phase registration pattern)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/cadence.py
- src/domains/demographics/cohort.py
- src/core/builder.py
- src/core/updates.py

## Assumptions / Open Questions
- Exact cadence interval for WD-16 (analogous to `DemographicCycleService`'s 200-tick `COHORT_INTERVAL`) is a Plan-phase decision.
- Whether the marriage-gate stale doc text gets its own tiny follow-up ticket or is corrected inline here is left to Plan's judgment based on how large the doc-fix ends up being.

## Implementation Notes

Implemented all 9 plan steps in order:

1. Added `reproduction_humanoid: int = Field(200, ge=1)` to `SystemCadence`'s
   World/Environmental block (`src/engine/cadence.py`).
2. Registered `ENABLE_REPRODUCTION_HUMANOID_PATH` (default `FeatureMode.OFF`) in
   `FeatureFlagManager` (`src/domains/optimization/feature_flags.py`), immediately after the
   `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` entry, with a DEV-002-style rationale comment.
3. Added `EntityGenerator.spawn_humanoid_offspring()` (`src/systems/world_systems/generator.py`),
   modeled on `spawn_natural_creature_offspring()` but calling `V2EntityBuilder.birth_record()`
   with real `parent_a_id`/`parent_b_id`/genetics/roles, `life_stage=LifeStage.CHILD`,
   `age_ticks=0` (no maturation-clock shortcut). Offspring role/faction default to
   `EntityRole.CITIZEN`/`Faction.TOWN_COUNCIL` (see plan.md Deviations — not specified by the
   ticket/plan, chosen to match `worldbuilding/compiler.py`'s own generic-humanoid default).
4. Added new `HumanoidReproductionService` (`src/world/reproduction_humanoid.py`): one O(n)
   candidate pass (ADULT/alive/active, sorted by id) + indexed
   `SpatialQueryService.nearby_entities()` pairing (10-unit radius,
   `HUMANOID_PAIRING_RADIUS`), scarcity gate reuse (`compute_regional_scarcity()`/
   `migration_threshold`, skip-when-empty convention), per-parent
   `reproduction_cooldowns_add` upserts (400-tick `REPRODUCTION_COOLDOWN_TICKS`), and
   `build_parent_bond_updates_for_birth()` for the reciprocal parent `SocialBond`s. **Deviation**
   (see plan.md Deviations for full detail): resolves each parent's `GeneticProfile` via
   `GeneticsSystem.generate_profile_from_seed(parent.id)` when the parent has none of its own,
   before calling `spawn_humanoid_offspring()` — `birth_record()`'s internal
   `combine_profiles()` call only fires when at least one supplied parent profile is non-`None`,
   so passing `None`/`None` through (as the plan's literal wording suggested) would have silently
   skipped genetics combination for every first-generation pairing. Caught by
   `test_eligible_adult_alive_same_location_same_race_pair_produces_birth`.
5. Wired a new "3.10 Humanoid Reproduction" step into
   `WorldDynamicsSystem.resolve_dynamics()` (`src/engine/world_dynamics.py`), immediately after
   step 3.9, combining the flag-gate pattern (3.9) with the nested-cadence pattern (3.4/
   `boss_spawn`) — `cadence.reproduction_humanoid` checked nested inside the outer
   `cadence.world_dynamics` gate.
6. Added architecture-guard tests (no-marriage-contract via `inspect.getsource()` +
   substring-absence check; no-`population_cohorts`-write) in new
   `tests/unit/world/test_reproduction_humanoid_cadence.py`.
7. Added the remaining 10 tests to the same file: cadence firing, eligible-pair birth, bond
   seeding, cooldown-blocks-repeat, scarcity allowed/suppressed, ineligible-pairs negatives
   (kind/location/alive/life_stage), flag-off guard, genetics real-parent-role-data guard
   (combat-lean via both-HERO parents), and the integration apply-path test. **Deviation**: test
   fixtures construct `EntityGenerator` via a local `_generator_for(state)` helper that mirrors
   `src/engine/pipeline.py`'s own `generator._last_id = state.next_entity_id - 1` setup — a raw
   `EntityGenerator(seed=42)` against hand-built test entities with hardcoded ids 1/2 would
   otherwise reuse those same ids for the spawned child, since `EntityGenerator.get_next_id()`
   counts from 1 independently of what ids already exist in `state.entities`. This is a
   test-construction correction, not a production-code change.
8. Added a new "Humanoid Reproduction" subsection to `docs/mechanics/05_world_evolution.md`
   (parallel to the Natural-Creature/Magical-Demonic subsections), and a new `WORLD-122` entry
   to `docs/parity_ledger/world_dynamics.yaml` via `tools/parity_ledger_writer.write_entry()`
   (schema-validated write path) plus a visible `python3 tools/parity_index.py build` rebuild.
   Re-verified `next_available_id("world_dynamics.yaml")` returned `WORLD-122` at
   implementation time (matching the plan's prediction) before writing.
9. Bundled the trivial stale-text fix at `docs/brainstorm/rpg_feature_atlas.html`'s
   "Phase placement mapping" table (idea-32 row): removed "marriage-gated" phrasing, added a
   2026-08-29 decoupling note, and clarified `WD-16` is a design-doc-only step label (never a
   code identifier — the shipped field is `SystemCadence.reproduction_humanoid`).

**Additional fix required by Step 8's own consequence**: adding `WORLD-122` to the ledger moved
the real shard's next-available id forward, which drifted a pre-existing hardcoded assertion in
`tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
(previously asserted `WORLD-122`, now correctly `WORLD-123`) — updated in this same ticket per
the documented "own legitimate change caused this baseline to drift" pattern, not filed as a
separate follow-up.

Ran `graphify update .` (AST-only, code graph unchanged topologically) and
`make knowledge-index-update` (3 changed doc files re-embedded) after the doc edits, and
`make docs-registry` to confirm `docs/REGISTRY.yaml` regenerates cleanly against the new
mechanics subsection.

## Test Summary

New file `tests/unit/world/test_reproduction_humanoid_cadence.py` — 12 tests, all passing:
cadence-fires pattern, eligible-pair birth (parent ids/birth_tick/birth_city_id/GeneticProfile),
no-marriage-contract architecture guard, no-`population_cohorts`-write guard, `SocialBond`
seeding (child side + parent side), cooldown-set + repeat-blocks-second-birth, scarcity
suppressed/allowed (both cases), four ineligible-pair negatives (kind/location/alive/life_stage),
flag-off regression guard, genetics real-parent-role combat-lean guard, and an integration test
proving the 3.10 call site commits through `ApplyPath.apply_generation()`.

Regression suites run clean after the change:
`pytest tests/unit/world/ tests/unit/progression/test_lifecycle.py
tests/unit/progression/test_genetics.py
tests/integration/optimization/test_component_patch_apply_parity.py` → 338 passed;
`pytest tests/unit/world/test_world_dynamics.py tests/unit/world/test_spawn_cadence.py
tests/unit/core/test_system_cadence.py tests/integration/pipeline/test_strategic_cadence.py
tests/unit/observability/test_event_shapers_world_dynamics.py
tests/unit/observability/test_event_extractor_world_dynamics.py` → 71 passed;
`pytest tests/unit/config/test_phase10_feature_flags.py
tests/integration/test_scenario_feature_flag_defaults.py
tests/integration/test_world_profile_feature_flag_guardrail.py` → 119 passed;
`pytest tests/tools/test_parity_index_baseline.py tests/tools/test_parity_ledger_writer.py
tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_index.py
tests/tools/test_parity_updater_static.py tests/tools/test_parity_ledger_scan.py` → 100 passed
(after the baseline-drift fix noted above).

**Follow-up pass (2026-09-02):** test-scoper's Test phase found a real coverage gap against
`test_plan.md` items 4 and 10 — two integration-level tests explicitly designated for
`tests/integration/optimization/test_component_patch_apply_parity.py` had never actually been
added there; only the unit-level equivalents in
`tests/unit/world/test_reproduction_humanoid_cadence.py` existed, and those don't exercise the
real authoritative apply path against real parent entities. Added the two missing tests to
`tests/integration/optimization/test_component_patch_apply_parity.py`:

- `test_parent_bond_updates_for_birth_apply_through_authoritative_path` (test_plan.md item 4's
  parent-side round-trip) — drives `build_parent_bond_updates_for_birth()` for two real parent
  `EntityState`s through `ApplyPath.apply_generation()` and asserts both land at
  `familiarity=0.8`/`sentiment=0.8`/`last_interaction_tick=birth_tick` in `entity.social.bonds`.
- `test_humanoid_reproduction_commits_through_authoritative_apply_path` (test_plan.md item 10) —
  drives the full `HumanoidReproductionService.process_reproduction()` output (child
  `entities_add` plus both parents' `entity_updates`) through `ApplyPath.apply_generation()` in a
  single tick and asserts the child's parent ids/birth_tick/life_stage, both parents'
  `reproduction_cooldowns[partner_id]` expiry, and both parents' reciprocal `SocialBond`s.

Both parent entities in the new integration test use ids 101/102 (not 1/2) to avoid a pre-existing,
out-of-scope `EntityGenerator` id-collision quirk: `EntityGenerator._last_id` always starts at 0
regardless of the entities already present in `state`, so a fresh `EntityGenerator(seed=42)` against
a `state` seeded with low entity ids can mint a colliding new id. This is not specific to the
humanoid-reproduction path (every sibling `EntityGenerator.spawn_*` test sidesteps it the same way,
by starting from an empty `entities={}`) and was left unfixed as out of scope for this ticket.

`pytest tests/integration/optimization/test_component_patch_apply_parity.py` (via
`/home/u24desktop/Working/venv/bin/python3 -m pytest`) → 9 passed, 0 failed (the file's 7
pre-existing tests plus the 2 new ones).

## Files Changed

- `src/engine/cadence.py` — new `reproduction_humanoid` `SystemCadence` field.
- `src/domains/optimization/feature_flags.py` — new `ENABLE_REPRODUCTION_HUMANOID_PATH` flag
  (default OFF).
- `src/systems/world_systems/generator.py` — new `EntityGenerator.spawn_humanoid_offspring()`.
- `src/world/reproduction_humanoid.py` (new) — `HumanoidReproductionService`.
- `src/engine/world_dynamics.py` — new "3.10 Humanoid Reproduction" step in
  `resolve_dynamics()`.
- `tests/unit/world/test_reproduction_humanoid_cadence.py` (new) — 12 tests.
- `tests/integration/optimization/test_component_patch_apply_parity.py` — added
  `test_parent_bond_updates_for_birth_apply_through_authoritative_path` and
  `test_humanoid_reproduction_commits_through_authoritative_apply_path` (follow-up pass,
  test_plan.md items 4/10, closing a coverage gap test-scoper flagged in Test phase).
- `tests/tools/test_parity_updater_static.py` — hardcoded next-id baseline updated
  `WORLD-122` → `WORLD-123` (legitimate drift caused by this ticket's own `WORLD-122` write).
- `docs/mechanics/05_world_evolution.md` — new "Humanoid Reproduction" subsection.
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-122` entry.
- `docs/brainstorm/rpg_feature_atlas.html` — stale "marriage-gated" phrasing corrected at the
  idea-32 "Phase placement mapping" row.
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`) to pick up the mechanics doc edit.
- `staging_artifacts/TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE/plan.md` — added a
  "Deviations" section documenting the genetics-resolution fix, offspring role/faction choice,
  `difficulty_tier` addition, `birth_city_id`-always-`None` rationale, and the parity-baseline
  update.
- `tickets/inprogress/TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE.md` — this file
  (Implementation Notes / Test Summary / Files Changed / Completion Summary / AC checkboxes /
  Status).

## Completion Summary

Implemented the human/humanoid reproduction cadence sub-phase end to end, behind
`ENABLE_REPRODUCTION_HUMANOID_PATH` (default OFF): a new `SystemCadence.reproduction_humanoid`
field (200 ticks) drives a new "3.10 Humanoid Reproduction" step in
`WorldDynamicsSystem.resolve_dynamics()`, which calls the new `HumanoidReproductionService` to
pair existing ADULT/alive/same-kind entities within a 10-unit indexed-radius lookup, spawn a real
tracked-parent newborn via `EntityGenerator.spawn_humanoid_offspring()` (real parent ids, genetics
via `GeneticsSystem`, role-driven combat-lean bias), set both parents' 400-tick reproduction
cooldowns, and seed reciprocal parent/child `SocialBond`s — all with no marriage-contract
precondition anywhere (grep- and test-verified) and no write to `population_cohorts`. All 8
acceptance criteria are satisfied and test-verified; the mechanics doc and parity ledger were
updated in the same session, and both remaining instances of stale "marriage-gated" atlas text
(the Phase Placement Mapping table row and the idea-32 card body) were corrected as a bundled
trivial fix per the ticket's own out-of-scope carve-out.

**Known, disclosed, out-of-scope gap:** while writing the new integration test
(`test_humanoid_reproduction_commits_through_authoritative_apply_path`), a pre-existing quirk was
found in `EntityGenerator._last_id` — it always starts at 0 regardless of `state`'s existing
entities, so low pre-existing entity ids (e.g. 1/2) can collide with a freshly-generated spawn id
and silently overwrite an entity in `entities_add`. Worked around in the test using ids 101/102,
matching every sibling spawn test's own existing pattern; `generator.py`'s id-assignment logic
itself was not touched, since this predates this ticket and affects every `EntityGenerator.spawn_*`
call site repo-wide, not just this one — a real but separate fix, not filed as its own ticket here
since it never manifests in live gameplay (only in tests seeding low, deterministic ids).
