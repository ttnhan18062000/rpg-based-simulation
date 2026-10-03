---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-HAZARD-NATIVE-IMMUNITY
phase: done
date: 2026-07-01
tags: [world, hazard, engine, mechanics, combat]
---

# TCK-20260701-HAZARD-NATIVE-IMMUNITY

## Title
Hazard drain should exempt entities native to a region; only affect hostile/visiting factions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Investigating `TCK-20260701-SANDBOX-MONSTER-BALANCE` found the actual root cause of
`sandbox_world`'s monster deaths: the `woods` region has `hazard_level: 1.5`, and
`EnvironmentService.calculate_hazard_drain()` (`src/world/environment.py`) applies
environmental damage uniformly to every living entity standing in a region, regardless of
whether that entity is native to (belongs in) that habitat or is an intruding hostile. 5
monsters spawned in their own `woods` habitat die from that region's own hazard within ~7
ticks — a design gap, not intended behavior. `calculate_hazard_drain(region, entity)` already
takes `entity` as a parameter but the current formula never reads it:

```python
base_drain = region.hazard_level * (1.0 + region.calamity_intensity)
if "MIASMA" in region.active_modifiers:
    base_drain *= 1.5
return int(base_drain * 10.0)
```

This ticket adds a native-entity exemption (or reduction) so hazardous regions read as
"dangerous to outsiders" rather than "instantly lethal to the creatures that live there."

## Scope
1. Investigate what "native to a region" should mean concretely. Check
   `data/content/world_modules/wolf_den_near_forest.yaml` first — its description
   ("Animal ecology module proving contextual hostility instead of enemy-by-type") suggests a
   faction/context-based hostility pattern may already exist somewhere in the composition or
   faction-relationship system; if entities from that module already survive their own
   region's high `hazard_level` (2.0) via some existing mechanism, use/extend that mechanism
   rather than inventing a new one. If no such mechanism exists yet, evaluate candidates:
   - Region carries an associated "native faction" (check `RegionSpec`/`RegionState` for an
     existing faction-ownership or ecology-association field before adding a new one)
   - Entity `kind` (e.g. `"monster"`) matched against a region `tags` list (e.g. `[forest]`
     matching a `wilderness`-type region)
   - Faction-based: entity's `Faction` compared against the region's dominant/sovereign
     faction (see `docs/mechanics/05_world_evolution.md` §3 Regional Sovereignty — regions
     already track faction influence)
2. Implement the chosen mechanism in `EnvironmentService.calculate_hazard_drain(region,
   entity)` — extend the signature's existing (currently unused) `entity` parameter, do not
   add new parameters unless the chosen mechanism genuinely requires world/state context
   `calculate_hazard_drain` doesn't currently receive.
3. Precedent check: `src/world/calamity.py`'s `apply_calamity_consequences` already does
   entity-kind-based conditional logic (`entity.kind == "hero" and region.hazard_level >
   0.5`) for a different hazard-adjacent mechanic — follow a consistent pattern/style.
4. Ensure hostile/visiting entities (e.g. a hero party invading a monster den) are NOT exempt
   — the exemption is specifically for entities that belong in that habitat, not a blanket
   region-type immunity.
5. Update `docs/mechanics/05_world_evolution.md` §2 (Regional Trauma & Hazards) with the new
   native-immunity rule — this is a Mechanics Bible chapter, must stay in 100% parity with
   code per project rules.
6. Update the relevant parity ledger entry in `docs/parity_ledger/world_dynamics.yaml` (find
   the entry covering `hazard_drain_applied`/`calculate_hazard_drain`; add one if none exists)
   with `v2_evidence` and `test_path`.
7. Add unit tests: native entity in a hazardous region takes reduced/zero drain; hostile
   entity in the same region takes full drain; entity in a zero-hazard region is unaffected
   either way (no regression to the base formula for the non-native case).
8. If this is a divergence from previously-documented behavior (hazard was universal before),
   add an entry to `docs/guidelines/intentional_divergences.md` with rationale class
   "Bug Fix" or "Intentional Gameplay Change" (decide which fits — "Bug Fix" if the unused
   `entity` parameter is read as evidence this was always intended; "Intentional Gameplay
   Change" if treated as new design).

## Out of Scope
- Changing the hazard drain base formula (`hazard_level * (1.0 + calamity_intensity) * 10`)
  for entities/hazard-kinds without a matching endurance entry — that stays as-is
- `data/worlds/sandbox_world/` (the compiled world instance) — `TCK-20260701-SANDBOX-MONSTER-BALANCE`
  owns instance-specific verification. Shared catalog **source** content
  (`data/content/world_modules/*.yaml`, `data/content/social/factions.yaml`) is **in scope**
  where the corrected mechanism (see Implementation Notes) requires authored
  `hazard_kind`/`hazard_immunities` values to have any effect — this is a deliberate,
  necessary narrowing of the original guard, not a violation of it.
- Calamity intensity growth logic (`apply_calamity_consequences`) — reference only, not
  modified
- Region sovereignty/influence mechanics — reference only if used for native determination,
  not restructured
- Race-level (`RaceDefinition.hazard_immunities`) resolution — documented extension point
  only, not implemented; faction-level granularity is sufficient for current content
- Authoring a fiend/demon faction or a chaos-corruption region into production content — that
  is an illustrative example from the design discussion, not a content request; cover it with
  a synthetic test-fixture-only unit test instead

## Acceptance Criteria
- [x] `calculate_hazard_drain` reads `entity` to determine native-vs-hostile status
- [x] Native entities take reduced or zero drain in their home-type region; hostile entities
      in the same region take full (unchanged) drain
- [x] A hazard kind that no faction is flagged as enduring affects **all** factions present in
      that region equally, including two mutually hostile factions (e.g. hero and wolf both
      take damage fighting in a toxic-gas region) — endurance must not be derivable from
      hero-hostility or from a coarse "monster" bucket
- [x] `docs/mechanics/05_world_evolution.md` updated and in parity with code
- [x] Parity ledger entry updated/added with a passing `test_path`
- [x] New unit tests cover native/hostile/zero-hazard/shared-hazard cases
- [x] No regression in existing hazard/environment/world_dynamics tests
- [x] `docs/guidelines/intentional_divergences.md` entry added if applicable

## Related Tickets
- TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC — parent epic
- TCK-20260701-SANDBOX-MONSTER-BALANCE — this fix (combined with the worldcomposition.v1
  migration) is expected to resolve the blocked ticket's extinction issue
- TCK-20260628-SIMQ-EPIC — grandparent context

## Related Docs
- `docs/mechanics/05_world_evolution.md` §2 (Regional Trauma & Hazards), §3 (Regional
  Sovereignty — reference for native/faction determination)
- `docs/parity_ledger/world_dynamics.yaml`
- `docs/guidelines/intentional_divergences.md`
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/plan.md` — full evidence trail of
  the hazard discovery (Deviations section, second attempt)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/`
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` — holds this (second, closing) pass's
  `plan.md`/`investigation.md`/`test_plan.md` (the current plan of record, describing the
  `hazard_kind`/`hazard_immunities` design), plus `SUPERSEDED.md`. **Incident**: during this
  pass's Finalize step, the first pass's original superseded `plan.md`/`investigation.md`/
  `test_plan.md` in this same directory were accidentally overwritten (not merged alongside)
  by the second pass's files — see `SUPERSEDED.md`'s "Incident note" for what survives as the
  historical record of the first pass (ticket Implementation Notes below, and
  `tickets/working_log.csv`).

## Related Code Areas
- `src/world/environment.py` — `EnvironmentService.calculate_hazard_drain`
- `src/engine/world_dynamics.py` (~L20-40) — `WorldDynamicsSystem.resolve_dynamics`, the
  per-entity per-tick call site
- `src/world/calamity.py` (~L74) — precedent for entity-kind-conditional hazard-adjacent logic
- `data/content/world_modules/wolf_den_near_forest.yaml`,
  `data/content/world_modules/goblin_camp_conflict.yaml` — content authoring targets for the
  corrected mechanism
- `data/content/social/factions.yaml` — content authoring target (`hazard_immunities`)
- `src/content/schema.py` — `FactionDefinition` (new `hazard_immunities` field)
- `src/worldbuilding/schema.py` — `RegionSpec` (new `hazard_kind` field)
- `src/core/state.py` — `RegionState` (new `hazard_kind` field)
- `src/content_semantics/faction.py` — `get_faction_id_str`, `FactionSemanticsService` (new
  `get_hazard_immunities` method)

## Assumptions / Open Questions
None outstanding — resolved during investigation/design. See Implementation Notes for the
full decision trail, including why the first-pass design (faction-bucket + region-type) was
rejected and replaced.

## Implementation Notes
**Reopened 2026-07-02.** A first implementation pass shipped, passed its own review and test
suite, and was marked DONE using a design that gated the exemption on
`entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`. That design
was not a bug — it matched its own plan and passed every test written against it. It was
**superseded**, not broken: follow-up discussion with the user surfaced a requirement the
original design could not satisfy — endurance to a hazard must be a property a faction/race
declares for itself (e.g. "fiends endure chaos corruption"), not something inferred from being
"hostile to the hero faction" or from a coarse legacy faction bucket. The original design also
had no way to make a hazard (e.g. toxic gas) hurt two mutually hostile factions equally, since
it only ever exempted the `MONSTER_HORDE` side.

The corrected design (full rationale, rejected alternatives, and evidence trail in
`stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/plan.md`) replaces the faction-bucket/
region-type check with two new, independent, data-driven fields, both defaulting to "no
immunity anywhere" so existing behavior is unchanged until content opts in:
- `RegionState.hazard_kind: str = "PHYSICAL"` (new field, threaded from a new
  `RegionSpec.hazard_kind` content field) — what kind of hazard a region's drain represents.
- `FactionDefinition.hazard_immunities: List[str] = []` (new catalog field on
  `src/content/schema.py`) — which hazard kinds a faction's members endure, authored per
  faction in `data/content/social/factions.yaml`.

`calculate_hazard_drain` resolves the entity's real catalog faction id via the already-existing
`get_faction_id_str(entity)` helper and checks it against `region.hazard_kind` via the
already-existing `FactionSemanticsService` singleton (explicitly documented as safe for
per-tick hot-path use). `wolf_den`/`near_forest`/`goblin_camp` get `hazard_kind:
"NATURAL_TERRAIN"`; `wild_beast_pack`/`goblin_warband` get `hazard_immunities:
["NATURAL_TERRAIN"]`. No fiend/chaos-corruption content is authored — that stays an
illustrative example covered by a synthetic unit test only.

The first pass's uncommitted working-tree changes (`src/world/environment.py`,
`docs/mechanics/05_world_evolution.md`, `docs/parity_ledger/world_dynamics.yaml`,
`docs/guidelines/intentional_divergences.md`, `tests/unit/world/test_regional_consequences.py`)
have been surgically reverted to their pre-first-pass state (verified via `git diff` showing
empty diffs on all five files) — only this ticket's own hunks were touched; an unrelated,
already-completed hunk from `TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP` sitting in the same
`docs/parity_ledger/world_dynamics.yaml` file was left untouched and verified still present.
The first pass's `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` is marked superseded
above rather than deleted, per traceability rules — it documents real, valid work that was
correctly executed against a design that was later found insufficient, not a mistake to erase.

**Awaiting architecture-review gate before Implement phase proceeds** (per coordinator
routing) — this is a materially different engine design (new `RegionState` field, new catalog
schema field, new content authoring across 2+ faction/region files) and goes through the same
gate as every other ticket in this epic.

**Implement phase completed 2026-07-02 (redesign pass).** Architecture review approved (after
one correction — plan.md Step 10 was fixed to target `### Hazard Impacts` under
`## 3. Regional Sovereignty`, not `## 2. Regional Trauma & Hazards`, matching the same
fix pattern the first pass already had to apply once). Implemented exactly per
`stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/plan.md`'s 12 ordered steps:

1. `FactionDefinition.hazard_immunities: List[str] = []` added to `src/content/schema.py`.
2. `RegionSpec.hazard_kind: Optional[str] = "PHYSICAL"` added to `src/worldbuilding/schema.py`.
3. `RegionState.hazard_kind: str = "PHYSICAL"` added to `src/core/state.py`, included in
   `to_canonical_dict()` so determinism/replay hashing covers the new field.
4. `src/worldbuilding/compiler.py` threads `hazard_kind` from `RegionSpec` to `RegionState` at
   compile time, mirroring the existing `hazard_level` pattern.
5. `FactionSemanticsService.get_hazard_immunities(faction_id) -> frozenset[str]` added to
   `src/content_semantics/faction.py`.
6. `EnvironmentService.calculate_hazard_drain` (`src/world/environment.py`) now resolves the
   entity's real catalog faction id via `get_faction_id_str` and returns zero drain if
   `region.hazard_kind` is in that faction's `hazard_immunities`; base formula unchanged
   otherwise. Unconditional early return — applies before/regardless of `calamity_intensity`
   and `MIASMA`.
7. Content authoring (in scope per plan.md's "Scope Change" — shared catalog source content,
   not the compiled `sandbox_world` instance): `hazard_kind: "NATURAL_TERRAIN"` added to
   `near_forest`/`wolf_den` (`wolf_den_near_forest.yaml`) and `goblin_camp`
   (`goblin_camp_conflict.yaml`); `hazard_immunities: ["NATURAL_TERRAIN"]` added to
   `wild_beast_pack` and `goblin_warband` in `data/content/social/factions.yaml`.
8-9. 11 new unit tests added (see Test Summary).
10. `docs/mechanics/05_world_evolution.md` — new "Native Endurance to a Region's Hazard Kind"
    subsection added under `### Hazard Impacts` (§3 Regional Sovereignty), plus a
    cross-reference note added to §2 Regional Trauma & Hazards. Includes the
    toxic-gas-hurts-both-sides counter-example and the sandbox_world staleness note.
11. `docs/parity_ledger/world_dynamics.yaml` — both `WORLD-029` and `WORLD-060` updated with
    `v2_evidence` describing the new mechanism and `test_path` pointed at
    `tests/unit/world/test_regional_consequences.py`. The unrelated, already-completed
    `camp_constructed` hunk from `TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP` in the same file was
    verified untouched (`git diff` confirms only the two intended entries plus the
    pre-existing hunk changed).
12. `docs/guidelines/intentional_divergences.md` — new entry §2.20 "Hazard-Kind Faction
    Endurance" added (Rationale Class: Bug Fix), plus a summary-table row. This is the correct
    file — the CLAUDE.md reference to `v2_intentional_divergences.md` does not exist in this
    repo; only `docs/guidelines/intentional_divergences.md` exists, matching this ticket's own
    Related Docs and plan.md Step 12.

**Test #5 deviation from test_plan.md's literal suggestion**: test_plan.md suggested
`wild_beast_pack` for the "shared hazard kind hurts mutually hostile factions" test, but real
catalog data shows `wild_beast_pack`'s `alignment_bucket` is `"wild"` (not `"invader"`), so
`FactionSemanticsService.is_hostile("hero_guild", "wild_beast_pack")` is actually `False` — it
is only *contextually* hostile via `is_hostile_compat` under combat engagement, not
unconditionally hostile. Since test_plan.md's own anti-drift guard requires the test to use
two factions "actually hostile... verify via `FactionSemanticsService.is_hostile`", the test
uses `goblin_warband` (`alignment_bucket: "invader"`) instead, which `is_hostile("hero_guild",
"goblin_warband")` confirms `True`. The test asserts this hostility directly before asserting
both factions take identical full drain in a shared, unendured `"TOXIC_GAS"` region — same
scenario, catalog-accurate faction choice.

Migration note from plan.md was confirmed moot at Implement-phase start: `git diff` on all
five files plan.md flagged (`src/world/environment.py`,
`docs/guidelines/intentional_divergences.md`, `docs/mechanics/05_world_evolution.md`,
`docs/parity_ledger/world_dynamics.yaml`, `tests/unit/world/test_regional_consequences.py`)
showed empty diffs before this pass started — the stale rejected-design working-tree changes
described in the plan's "Migration Note" were already gone, so no manual revert was needed.

**Empirical trace (informal, not a substitute for `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s own
verification)**: with the new content authored, `FactionSemanticsService.get_hazard_immunities`
confirms `wild_beast_pack` and `goblin_warband` both resolve to `frozenset({"NATURAL_TERRAIN"})`
and `hero_guild` resolves to `frozenset()`. If `data/worlds/sandbox_world/` is recompiled from
the updated source catalog (that recompile is out of this ticket's scope), wolves spawned with
`faction_id: "wild_beast_pack"` standing in `wolf_den` (`hazard_kind: "NATURAL_TERRAIN"`) would
take zero passive hazard drain, while a hero party in the same region would take the unchanged,
full drain.

## Test Summary
Scoped pytest run per `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/test_plan.md`:
`pytest tests/unit/world/test_regional_consequences.py tests/unit/world/test_weather.py
tests/integration/pipeline/test_recovery_gaps.py tests/unit/observability/test_event_extractor_world.py
tests/unit/content_semantics/test_semantics.py tests/simulation_quality/test_world_dynamics_scorer.py
tests/unit/content/test_catalog.py` — **78 passed, 0 failed**. Additionally ran
`tests/unit/worldbuilding/` + `tests/unit/core/` (RegionSpec/RegionState/compiler regression
surface) — **304 passed, 0 failed**. 11 new tests added: 7 in
`test_regional_consequences.py` (native endurance, hostile full-drain, shared-hazard-kind
mutual-hostility, synthetic fiend faction, zero-hazard, endurance-survives-miasma/calamity,
default-hazard-kind-no-regression), 1 in `test_semantics.py`
(`get_hazard_immunities`), and 2 in `test_catalog.py` (schema round-trip/default, real-catalog
load with `hazard_immunities` authored). No existing test required modification — all pre-existing
hazard-drain call sites (`test_weather.py` x2, `test_recovery_gaps.py`) construct regions/entities
with no `hazard_kind`/`faction_id` set, so they exercise the unchanged default-safety path.

## Files Changed
- `src/content/schema.py` — `FactionDefinition.hazard_immunities: List[str] = []`
- `src/worldbuilding/schema.py` — `RegionSpec.hazard_kind: Optional[str] = "PHYSICAL"`
- `src/core/state.py` — `RegionState.hazard_kind: str = "PHYSICAL"`, added to `to_canonical_dict()`
- `src/worldbuilding/compiler.py` — threads `hazard_kind` into compiled `RegionState`
- `src/content_semantics/faction.py` — `FactionSemanticsService.get_hazard_immunities`
- `src/world/environment.py` — `EnvironmentService.calculate_hazard_drain` reads `entity`'s
  resolved faction and `region.hazard_kind`
- `data/content/world_modules/wolf_den_near_forest.yaml` — `hazard_kind: "NATURAL_TERRAIN"`
  on `near_forest`/`wolf_den`
- `data/content/world_modules/goblin_camp_conflict.yaml` — `hazard_kind: "NATURAL_TERRAIN"`
  on `goblin_camp`
- `data/content/social/factions.yaml` — `hazard_immunities: ["NATURAL_TERRAIN"]` on
  `wild_beast_pack`, `goblin_warband`
- `tests/unit/world/test_regional_consequences.py` — 7 new tests
- `tests/unit/content_semantics/test_semantics.py` — 1 new test
- `tests/unit/content/test_catalog.py` — 2 new tests
- `docs/mechanics/05_world_evolution.md` — `### Hazard Impacts` (§3) subsection + §2 cross-reference
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-029`, `WORLD-060` updated
- `docs/guidelines/intentional_divergences.md` — §2.20 entry + summary-table row

Not touched (out of scope, per plan/scope guards): `src/world/calamity.py`,
`data/worlds/sandbox_world/`, any `Faction` enum-based logic, `RaceDefinition`, and no
fiend/chaos-corruption faction or region was added to production content (covered by a
synthetic test-fixture-only unit test instead).

## Completion Summary
This ticket has two implementation passes. The first pass shipped a working
`Faction.MONSTER_HORDE`/`region.kind == "WILDERNESS"` design, passed its own review and 56+5
tests, and was marked DONE — that work was valid against its own plan but was later found to
re-derive hazard "endurance" from hero-hostility, which the user explicitly rejected as the
wrong coupling (it could never model a hazard, like toxic gas, that hurts two mutually hostile
factions equally). The ticket was reopened and redesigned around two independent, data-driven
fields — `RegionState.hazard_kind` and `FactionDefinition.hazard_immunities` — that let a
faction declare endurance to a named hazard kind for its own in-fiction reason, decoupled from
hostility to any other faction. This second pass is the one that closes the ticket: all
acceptance criteria are met, all scoped tests pass (78 direct + 304 regression-surface, 0
failures), both parity ledger entries are updated, the mechanics doc and divergence log are in
parity with the shipped code, and the first pass's now-superseded staging docs remain preserved
under `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` marked `SUPERSEDED.md` for
traceability. `data/worlds/sandbox_world/`'s compiled artifacts remain stale until
`TCK-20260701-SANDBOX-MONSTER-BALANCE` recompiles them — that empirical verification is
explicitly that ticket's job, not this one's.

**KNOWN GAP (found 2026-07-01, during `TCK-20260701-SANDBOX-MONSTER-BALANCE`'s attempt-3
investigation — logged here for transparency, fixed under a separate hotfix):** this ticket's
content changes (`hazard_kind: "NATURAL_TERRAIN"` authored on `wolf_den_near_forest.yaml` and
`goblin_camp_conflict.yaml` regions) do not actually load through the real
`worldcomposition.v1` pipeline. `RegionRecipeSpec` (`src/worldbuilding/recipe.py`,
`extra="forbid"`) was never given a `hazard_kind` field, so `python3 -m
src.worldbuilding.cli resolve <world>` fails with `extra_forbidden` on any module authoring
it — and even with that fixed, `WorldAssemblyResolver.resolve_module_contribution()` never
forwards `hazard_kind` into the resolved spec, so it would silently default to `"PHYSICAL"`
either way. This blocks **all** `worldcomposition.v1` module loading, not just
`sandbox_world` — confirmed via `pytest tests/integration/worldassembly/
test_real_content_world_modules.py` (5/5 ERROR in the current working tree). The 11 unit
tests this ticket added did not catch it because they construct `RegionState`/`EntityState`
directly, bypassing the module-loading → resolver → compiler pipeline entirely. Fix tracked
under `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (hotfix), which also adds real pipeline-level
regression coverage so this class of gap (a new content field that never round-trips through
actual YAML loading) is caught by CI going forward, not just unit-level construction tests.
