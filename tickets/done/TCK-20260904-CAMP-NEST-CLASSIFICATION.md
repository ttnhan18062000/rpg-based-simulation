---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMP-NEST-CLASSIFICATION
phase: done
date: 2026-09-04
tags: [content, feature-flags]
---

# TCK-20260904-CAMP-NEST-CLASSIFICATION

## Title
Camp/Nest race classification rule and flag-gated Nest branch on CampService

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Consolidates M4 design ideas 44+45+46. Establishes a documented, race-data-verified City/Camp/Nest classification rule keyed off `natural_traits` in `data/content/living/races.yaml`, explicitly resolving the goblin `social_humanoid` contradiction and the 5 currently-unclassified races (wolf, undead, troll, dragonkin, spirit). Adds a flag-gated Nest branch to `CampService` (`src/world/camp.py`) that reuses `RAID_MATURITY_THRESHOLD`/`MATURITY_PER_TICK` timing but substitutes a spread outcome for the raid outcome, plus new typed Camp/Nest feature fields (totem, stockpile, palisade) on `CampState`/`CampUpdate`.

## Scope
- Document the City/Camp/Nest classification rule against real `natural_traits` data for all 13 races in `data/content/living/races.yaml` (human, wolf, goblin, spider, orc, elf, dwarf, undead, troll, lizardfolk, dragonkin, slime, spirit); the decision must be recorded in `plan.md`/`investigation.md`, not deferred.
- Explicitly resolve the goblin contradiction: goblin carries `social_humanoid` (shared with City-eligible human/elf/dwarf) alongside `opportunistic`/`small_body`, which is the trait set idea 44's card claims justifies Camp classification — state which trait(s) decide Camp-over-City for goblin specifically.
- Give an explicit disposition (Camp, Nest, or neither/out-of-scope-for-now) for each of: wolf (`quadruped, pack_hunter, territorial, carnivore`), undead (`undead` only), troll (`large_body, regenerating`), dragonkin (`flying, large_body, fire_aligned, magic_sensitive` — note dragonkin's trait profile is the closest match to idea 47's Lair concept, not Camp/Nest; state whether dragonkin is excluded from Camp/Nest classification entirely for that reason), spirit (`spiritual, magic_sensitive`).
- Add a new feature flag (registered in `src/domains/optimization/feature_flags.py`'s flag map, default OFF, following the `ENABLE_CREATURE_TERRITORY_LIFECYCLE`/`ENABLE_REPRODUCTION_*` naming and default-OFF precedent) gating a new Nest branch in `CampService`.
- Nest branch reuses `CampService.MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD` for timing but at threshold triggers a spread/population-growth outcome instead of the existing raid-spawn outcome in `CampService.process` (`src/world/camp.py`).
- Add typed fields for Camp/Nest features — totem, stockpile, palisade — to `CampState` (`src/core/state.py`) and `CampUpdate` (`src/core/updates.py`), not free-form dict/metadata storage; magnitudes may be provisional but must be explicitly documented as such.
- Extend `tests/unit/world/test_camp_lifecycle.py` and `tests/unit/world/test_natural_creature_reproduction.py` to cover the Nest branch (flag ON and flag OFF/no-op) and the new typed fields.

## Out of Scope
- CampState world-generation/WorldCompiler wiring, `WorldModuleSpec` changes, or seeding a live Camp/Nest at world-compile time — no AC in this ticket may assume a live seeded Camp exists at compile time; that is `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`.
- Any change to `src/world/creature_territory.py`'s `CreatureTerritoryService` — it is an intentionally separate, parallel per-entity territory mechanism per its own docstring; do not merge or extend it as part of Nest work.
- Dissolution/transformation of Camp/Nest content on any trigger — that mechanism family belongs to idea 48 (place-type transitions), which has no ticket yet.

## Acceptance Criteria
- [x] `plan.md`/`investigation.md` records an explicit classification decision for all 13 races in `races.yaml`, with the goblin `social_humanoid` contradiction named and resolved, and all 5 previously-unclassified races (wolf, undead, troll, dragonkin, spirit) given an explicit disposition (not left ambiguous or silently deferred).
- [x] A new flag (default OFF) gates a Nest branch in `CampService`; with the flag OFF, existing raid-branch behavior and all current tests in `test_camp_lifecycle.py` pass unchanged (regression).
- [x] With the flag ON, a Camp instance flagged as Nest-kind reaches `RAID_MATURITY_THRESHOLD` and produces a spread outcome (documented, tested) instead of a raid outcome, using the same `MATURITY_PER_TICK` accrual.
- [x] `CampState`/`CampUpdate` carry new typed fields for totem, stockpile, and palisade (not dict/metadata storage), each round-tripping through `to_canonical_dict()`/merge correctly and covered by a serialization test.
- [x] No `WorldModuleSpec`, `WorldCompiler`, or world-generation code is touched by this ticket.

## Related Tickets
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-109's camp_constructed divergence_note)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/world/camp.py
- src/core/state.py (CampState)
- src/core/updates.py (CampUpdate)
- data/content/living/races.yaml
- src/world/creature_territory.py (related-but-explicitly-separate, do not merge)
- src/domains/optimization/feature_flags.py
- tests/unit/world/test_camp_lifecycle.py
- tests/unit/world/test_natural_creature_reproduction.py

## Assumptions / Open Questions
- The classification decision (goblin resolution + 5-race dispositions) is a genuine judgment call this ticket must make explicitly, not defer — flagged directly by the epic doc's own Content note.
- Feature-flag name is not yet chosen; must be registered following existing naming/default-OFF conventions.
- Totem/stockpile/palisade magnitudes have no existing anchor in the codebase and must be documented as provisional/flagged, per the epic doc's Content & Balance Requirements note.
- docs/parity_ledger/world_dynamics.yaml's WORLD-109 divergence_note ("camp_constructed has no viable engine path... camps are pre-placed at world generation") pre-dates this work and should be revisited only if this ticket changes that fact — it currently does not, since CampState construction remains out of scope here.
- dragonkin's trait profile overlaps more with idea 47's Lair concept than Camp/Nest — this ticket must state explicitly whether dragonkin is excluded from Camp/Nest classification for that reason, to avoid conflicting with TCK-20260904-LAIR-ENTITY-ANCHOR.

## Implementation Notes
Implemented exactly per the APPROVED `plan.md`'s 7 ordered steps, no deviations:

1. Added `CampService.NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll", "slime"})` as a
   class constant on `CampService` (`src/world/camp.py`), immediately after `CAMP_SPAWN_INTERVAL`.
2. Registered `ENABLE_CAMP_NEST_SPREAD` (default `FeatureMode.OFF`) in
   `FeatureFlagManager.__init__`'s `_flags` dict (`src/domains/optimization/feature_flags.py`),
   between `ENABLE_REPRODUCTION_HUMANOID_PATH` and `ENABLE_INFORMATION_HUB_ACCUMULATION`, with the
   standard DEV-002 default-OFF comment convention.
3. Added `totem_tier: int = 0`, `stockpile: float = 0.0`, `palisade_integrity: float = 0.0` to
   `CampState` (`src/core/state.py`), after `last_raid_tick`, and wired all three into
   `to_canonical_dict()`'s manually maintained `res` dict.
4. Added `totem_tier_set: Optional[int] = None`, `stockpile_delta: float = 0.0`,
   `palisade_integrity_set: Optional[float] = None` to `CampUpdate` (`src/core/updates.py`), and
   extended `merge()` with the additive (`stockpile_delta`) / non-None-wins
   (`totem_tier_set`/`palisade_integrity_set`) pattern matching the existing fields.
5. Extended `apply_plan.py`'s camp-application block (the sole authoritative commit point for
   `CampUpdate` -> `CampState`) to read and apply the three new fields via the same
   `replace(camp, ...)` call already used for `maturity`/`active`/`last_raid_tick`.
6. Forked the existing raid-trigger gate in `CampService.process_camps()` (block 3) on
   `is_nest_spread = flags.get("ENABLE_CAMP_NEST_SPREAD", "OFF") == "ON" and camp.kind in
   CampService.NEST_RACE_KINDS`. When true, calls
   `generator.spawn_natural_creature_offspring(camp.position, state=state, kind=camp.kind,
   difficulty_tier=int(camp.maturity/20.0)+1, birth_tick=state.tick)` and applies the identical
   `maturity_delta=-20.0`/`last_raid_tick_set=state.tick` cost the raid branch uses. When false
   (flag OFF, or kind not in `NEST_RACE_KINDS`), the original `RaidService.check_for_raid()` path
   runs byte-for-byte unchanged (including its pre-existing `for mob in raid_update.entities_add:
   pass` no-op loop, preserved verbatim per the plan's Anti-Drift Notes). The pre-existing
   `camp_updates[c_id]` overwrite-not-merge behavior between block 1 (maturity evolution) and
   block 3 (raid/spread) was preserved unchanged in both branches, per the plan's explicit
   instruction not to fix or worsen it in this ticket.
7. Updated docs: added a new "### Camp/Nest Classification & Nest Spread" subsection to
   `docs/mechanics/05_world_evolution.md` §6, immediately after "### Natural-Creature
   Reproduction" and before "### Magical/Demonic Reproduction", carrying the full classification
   table, the goblin-resolution rationale, the spread-outcome mechanism, and the cost/cooldown
   reuse. Updated `docs/world/raid_boss_camp_contract.md`'s "Raid trigger" subsection with the new
   fork description (phrased as the correct relative `maturity_delta=-20.0`, explicitly not
   repeating the doc's pre-existing "resets to 50" imprecision for the new text), added a new
   "Camp/Nest classification" note, and added the Nest branch as a second documented precedent
   under "Extension rules" rule 1. Added a new parity-ledger entry `WORLD-124` to
   `docs/parity_ledger/world_dynamics.yaml` via `tools/parity_ledger_writer.py::write_entry`
   (schema-validating write path, rebuilt the derived SQLite index in-process on success) — no
   raw YAML edit was made.

All 7 core implementation steps landed exactly as specified, including the explicit Anti-Drift
Notes (no `CampState` construction, no independent Nest cooldown, no extension of block 2's
garrison-spawn binary, no routing through `FeatureFlagManager.is_enabled()`).

**One real, disclosed deviation from `plan.md`'s Scope Guards**: the Document-Update phase (an
independent doc-accuracy verification pass that runs after Implement) additionally touched two
files `plan.md` explicitly did NOT list in scope:
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — `plan.md`'s own Scope Guards said
  this doc is "scope-tracking, not updated by child-ticket implementation work." Document-Update
  nonetheless added a dated "Status update, 2026-09-04" annotation to Scope item 1, noting that the
  classification-rule/CampService-Nest half of that item has now shipped (while the CampState
  world-generation wiring half remains open, tracked by the sibling ticket
  `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`). This mirrors the doc's own pre-existing
  "Correction, 2026-09-02" annotation convention and keeps the epic doc from silently drifting
  stale about this ticket's real completion state (per CLAUDE.md's Traceability priority and the
  project's established pattern, seen repeatedly this session, of correcting roadmap-doc status
  the moment a scope item actually lands) — but it was not something the APPROVED plan called for,
  and done-checker's Verify pass correctly flagged it as an undocumented deviation. Kept (not
  reverted) because the annotation is factually accurate, low-risk (additive, dated, doesn't touch
  any other scope item), and consistent with how this same epic doc has already been updated by
  sibling M4 tickets outside their own plan's stated scope — but it is now explicitly recorded here
  rather than silently passed through, which is the actual gap Verify caught.
- `docs/core/update_intents.md` — Document-Update's broader staleness sweep (per its own Document
  Rule to check for other doc areas a change might make stale, not just the two docs the plan
  named) found the `camp_updates` row in the World-level intent taxonomy table was stale even
  before this ticket (it omitted the pre-existing `last_raid_tick_set` field) and would become more
  stale once the three new fields landed. Updated the row to list all current `CampUpdate` fields,
  correctly noting the three new ones as unpopulated scaffolding. This is a legitimate doc-accuracy
  fix, not out-of-scope production behavior, but was likewise not named in `plan.md` and is recorded
  here for the same reason.

## Test Summary
Added 10 new tests to `tests/unit/world/test_camp_lifecycle.py`, matching every test named in
`test_plan.md`'s "New Tests Required" section 1-9 plus the flag-registry test (test 10):
`test_nest_race_kinds_classification_matches_documented_table`,
`test_nest_flag_registered_in_feature_flag_manager_default_off`,
`test_camp_flag_off_nest_kind_camp_still_raids`, `test_camp_flag_on_camp_kind_still_raids`,
`test_camp_flag_on_nest_kind_spreads_instead_of_raiding`,
`test_nest_spread_reuses_same_500_tick_cooldown_as_raid`,
`test_nest_branch_does_not_construct_new_campstate`,
`test_campstate_totem_stockpile_palisade_round_trip_canonical_dict`,
`test_campupdate_totem_stockpile_palisade_merge_semantics`,
`test_campupdate_totem_stockpile_palisade_apply_via_apply_plan`. No new tests were added to
`test_natural_creature_reproduction.py` — its existing suite (including the architecture guards
`test_reproduction_paths_never_mutate_region_directly` and
`test_natural_creature_reproduction_does_not_reference_genetics`) already fully covers the
regression surface the plan asked it to protect, and re-ran green unmodified.

**Post-Test-phase coverage gap closed**: the Test phase's cross-cutting scoped run (877 passed, 0
failed) found that `test_campupdate_totem_stockpile_palisade_apply_via_apply_plan` in
`test_camp_lifecycle.py` — despite its name — actually applies the `CampUpdate` via
`src/engine/apply.py`'s `ApplyPath.apply_partial`, not `src/engine/apply_plan.py`'s
`ApplyPlanBuilder`. This meant the new `totem_tier`/`stockpile`/`palisade_integrity` lines added to
`apply_plan.py`'s Camps block (the parallel apply mechanism used by the plan/diff-based commit
path) were never exercised by any test. Added
`test_apply_plan_builder_camp_totem_stockpile_palisade` to
`tests/unit/domains/optimization/test_apply_plan_builder.py` (the file's confirmed owning location
for `ApplyPlanBuilder`-specific tests), mirroring the file's existing `build_plan(...)` call
pattern (`test_apply_plan_builder_grouping`/`test_apply_plan_builder_noop`) and the round-trip
test's `CampState`/`CampUpdate` construction. It runs a `camp_updates` entry with
`totem_tier_set=3, stockpile_delta=12.0, palisade_integrity_set=60.0` through
`ApplyPlanBuilder.build_plan` directly and asserts `plan.world_collection_changes["camps"]["camp_1"]`
reflects all three new field values. `pytest tests/unit/domains/optimization/test_apply_plan_builder.py -q`
— 3 passed (2 pre-existing + 1 new).

Ran (via `/home/u24desktop/Working/venv/bin/python3 -m pytest`, this machine's pydantic-enabled
venv — bare `python3` lacks `pydantic`):
- `tests/unit/world/` — **306 passed** (all 3 pre-existing `test_camp_lifecycle.py` tests
  byte-for-byte unchanged behavior, all pre-existing `test_natural_creature_reproduction.py`
  tests unchanged, plus the 10 new tests above).
- `tests/unit/content/test_catalog.py tests/unit/content/test_layered_catalog.py
  tests/unit/content/test_resolvers.py` — all passed (no `races.yaml`/resolver schema drift).
- `tests/integration/world/test_long_run_stability.py::test_long_run_stability` — **not
  exercised to completion**: this test is marked `@pytest.mark.extra_slow` and hit this sandbox's
  wall-clock resource-budget `TimeoutError` (`tests/conftest.py`'s `timeout_handler`) partway
  through its long simulated run, independent of this ticket's change. This is a pre-existing
  environment/resource-limit characteristic of the test (already `extra_slow`-marked and
  `skipif`'d on CI for a documented wall-clock-throttle nondeterminism reason), not a functional
  regression: the test runs with default (all-OFF) feature flags, so the Nest branch added by
  this ticket is never on the executed code path — only the pre-existing, byte-for-byte-preserved
  raid branch runs. Flagging explicitly per Definition-of-Done rather than silently treating it as
  passed.

## Files Changed
- `src/world/camp.py` — `NEST_RACE_KINDS` constant; Nest-spread fork inside the raid-trigger gate.
- `src/domains/optimization/feature_flags.py` — registered `ENABLE_CAMP_NEST_SPREAD` (default OFF).
- `src/core/state.py` — `CampState.totem_tier`/`stockpile`/`palisade_integrity` fields + `to_canonical_dict()` wiring.
- `src/core/updates.py` — `CampUpdate.totem_tier_set`/`stockpile_delta`/`palisade_integrity_set` fields + `merge()` wiring.
- `src/engine/apply_plan.py` — camp-application block extended to commit the three new `CampUpdate` fields.
- `tests/unit/world/test_camp_lifecycle.py` — 10 new tests (classification, flag registry, flag ON/OFF x Camp/Nest kind, cooldown reuse, no-new-CampState guard, typed-field round-trip/merge/apply-plan).
- `tests/unit/domains/optimization/test_apply_plan_builder.py` — added `test_apply_plan_builder_camp_totem_stockpile_palisade`, closing the coverage gap where `apply_plan.py`'s Camps block (new `totem_tier`/`stockpile`/`palisade_integrity` handling) was never exercised via `ApplyPlanBuilder` directly (the existing `test_camp_lifecycle.py` round-trip test only exercises the parallel `apply.py::ApplyPath.apply_partial` mechanism).
- `docs/mechanics/05_world_evolution.md` — new "Camp/Nest Classification & Nest Spread" §6 subsection.
- `docs/world/raid_boss_camp_contract.md` — "Raid trigger" subsection extended, new "Camp/Nest classification" note, "Extension rules" rule 1 updated with the Nest precedent.
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-124` entry (written via `tools/parity_ledger_writer.py::write_entry`, not a raw edit); Parity phase later appended the `ApplyPlanBuilder`-path test citation to this entry's `test_path`.
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — Document-Update phase added a dated status-update annotation to Scope item 1, noting the classification-rule/CampService-Nest half has shipped (world-gen half remains open, tracked by `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`). **Not in `plan.md`'s stated scope** — see the disclosed deviation note in Implementation Notes above.
- `docs/core/update_intents.md` — Document-Update phase updated the `camp_updates` intent-taxonomy row to list all current `CampUpdate` fields (including a pre-existing `last_raid_tick_set` omission and the three new fields from this ticket). **Not in `plan.md`'s stated scope** — see the disclosed deviation note in Implementation Notes above.
- `staging_artifacts/TCK-20260904-CAMP-NEST-CLASSIFICATION/plan.md`, `investigation.md`, `test_plan.md` — pre-existing from this ticket's Investigate/Plan phases (already reviewed and APPROVED by architecture-reviewer prior to this Implement run); no content changes made to them during Implement.

## Completion Summary
Implemented the City/Camp/Nest/Excluded race classification rule (documented, not a runtime
lookup) and its sole code projection, `CampService.NEST_RACE_KINDS`. Added the flag-gated
(`ENABLE_CAMP_NEST_SPREAD`, default OFF) Nest-spread fork inside `CampService`'s existing
raid-trigger gate: Nest-classified camps (wolf/spider/troll/slime) spawn a parentless same-kind
offspring instead of raiding, at the identical cost/cooldown the raid path already uses, while
Camp-classified camps (goblin/orc) are entirely unaffected by the flag. Added three new typed,
durable Camp/Nest feature fields (`totem_tier`, `stockpile`, `palisade_integrity`) to
`CampState`/`CampUpdate`, wired through serialization, merge, and the authoritative
`apply_plan.py` commit path as provisional scaffolding (no accrual/production logic added, per
scope). Updated the Mechanics Bible, the camp/raid/boss engine contract, and the parity ledger
(`WORLD-124`) to document the new behavior. All new and pre-existing tests in the scoped
`tests/unit/world/` and `tests/unit/content/` suites pass (306 + content tests green); the one
`extra_slow`-marked integration test could not be run to completion in this sandbox due to a
resource-budget timeout unrelated to this ticket's flag-gated change.
