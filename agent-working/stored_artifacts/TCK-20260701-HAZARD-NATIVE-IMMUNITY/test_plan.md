---
status: active
artifact_type: test_plan
ticket_id: TCK-20260701-HAZARD-NATIVE-IMMUNITY
date: 2026-07-02
---

# Test Plan — TCK-20260701-HAZARD-NATIVE-IMMUNITY

> **Revision note (2026-07-02):** Supersedes the first-pass test plan (faction-bucket +
> region-type design), preserved at
> `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/test_plan.md` (marked superseded). This
> plan targets the corrected `hazard_kind`/`FactionDefinition.hazard_immunities` design.

## Regression Surface
Same call sites as the first pass (unchanged by the redesign):
- `src/engine/world_dynamics.py` `WorldDynamicsSystem.resolve_dynamics` (sole production call
  site).
- `tests/unit/world/test_regional_consequences.py::test_regional_hazard_drain`,
  `tests/unit/world/test_weather.py::test_hazard_drain_scaling`/`::test_miasma_effect`,
  `tests/integration/pipeline/test_recovery_gaps.py::test_regional_hazard_impact` — all build
  entities without a `"faction_id"` property matching any faction with authored
  `hazard_immunities`, and regions without an explicit `hazard_kind` (defaults to
  `"PHYSICAL"`, which no faction lists). Unaffected — re-verified against the new design's
  default-safety property, same conclusion as the first pass reached for its own defaults.
- `tests/unit/observability/test_event_extractor_world.py` — operates on pre-built
  `StateUpdate`/`hp_delta` fixtures downstream of `calculate_hazard_drain`; unaffected.
- `tests/unit/content_semantics/test_semantics.py::test_faction_semantics` — exercises
  `FactionSemanticsService` against the real catalog; must continue passing unchanged after
  `get_hazard_immunities` is added (new method, no changes to existing methods).
- `docs/parity_ledger/world_dynamics.yaml` `WORLD-029`/`WORLD-060` — evidence/test_path need
  updating to describe the corrected mechanism (not the reverted one).

## New Tests Required

### `src/content/schema.py` / catalog loading
1. `tests/unit/content/test_faction_schema.py` (or nearest existing schema test file) —
   `FactionDefinition(..., hazard_immunities=["NATURAL_TERRAIN"])` round-trips through Pydantic
   validation; defaults to `[]` when omitted (existing faction YAML entries without the field
   must still load without error — the whole catalog, `repo.load_all()`, must not break).

### `src/content_semantics/faction.py`
2. `tests/unit/content_semantics/test_semantics.py::test_get_hazard_immunities` (new test,
   same file/pattern as existing `test_faction_semantics`, real `CatalogRepository("data/content")`) —
   after Step 7 content authoring: `service.get_hazard_immunities("wild_beast_pack") ==
   frozenset({"NATURAL_TERRAIN"})`; `service.get_hazard_immunities("hero_guild")` (or whichever
   real hero-aligned faction id exists in the catalog) `== frozenset()`;
   `service.get_hazard_immunities("nonexistent_faction") == frozenset()` (missing-faction
   safety).

### `src/world/environment.py` — `calculate_hazard_drain`
Add to `tests/unit/world/test_regional_consequences.py` (mirrors existing
`make_hero`/builder-based idioms in that file):

3. `test_hazard_drain_faction_endures_matching_hazard_kind` — real catalog faction
   `wild_beast_pack` (via `.identity(properties={"faction_id": "wild_beast_pack"})`), region
   `hazard_kind="NATURAL_TERRAIN"`, `hazard_level=2.0` → assert drain `== 0`. Uses real content
   (post Step 7 authoring), not synthetic data, so this is also an end-to-end proof the content
   authoring actually took effect.
4. `test_hazard_drain_different_faction_same_hazard_kind_full_drain` — a hero-aligned faction id
   (no `hazard_immunities` entry) in the **same** `hazard_kind="NATURAL_TERRAIN"`,
   `hazard_level=2.0` region → assert drain `== 20` (unchanged base formula). Directly encodes
   "hostile/visiting entities are NOT exempt" — and proves endurance is faction-specific, not a
   blanket hazard-kind exemption for anyone standing in it.
5. `test_hazard_drain_shared_hazard_kind_hurts_mutually_hostile_factions_equally` — synthetic
   `hazard_kind="TOXIC_GAS"` region (no faction in the real catalog lists `"TOXIC_GAS"` in
   `hazard_immunities`), `hazard_level=1.0`; both `wild_beast_pack` and a hero-aligned faction
   entity → assert **both** take the identical, full, unchanged drain. This is the literal
   "hero and wolf fight in toxic gas, both endure it" scenario from the design discussion — the
   test that would have caught the first-pass design's core flaw (it could never have made this
   test pass, since wolves were unconditionally exempt in any `WILDERNESS` region).
6. `test_hazard_drain_synthetic_faction_endures_named_hazard_kind` — **not** real catalog
   content: use `configure_faction_semantics_service`/a test-local `CatalogRepository` (or
   monkeypatch `repo.factions`) to register a synthetic `"fiend_lords"` faction with
   `hazard_immunities=["CHAOS_CORRUPTION"]`, region `hazard_kind="CHAOS_CORRUPTION"` → assert
   drain `== 0` for the fiend entity, and `!= 0` for a `wild_beast_pack` entity in the same
   region (proves cross-faction independence: enduring one hazard kind doesn't imply enduring
   another). Use `reset_faction_semantics_service()` in teardown/fixture cleanup to avoid
   singleton leakage into other tests — this is exactly what
   `content_semantics/faction.py`'s existing `configure_faction_semantics_service`/
   `reset_faction_semantics_service` pair exists for.
7. `test_hazard_drain_zero_hazard_region_unaffected` — `hazard_level=0.0` regardless of
   `hazard_kind`/faction → assert drain `== 0` for both an enduring and a non-enduring faction
   (no double-counting/sign error in the new branch).
8. `test_hazard_drain_endurance_survives_miasma_and_calamity` — `hazard_kind="NATURAL_TERRAIN"`,
   `hazard_level=2.0`, `calamity_intensity=1.0`, `active_modifiers=["MIASMA"]`,
   `wild_beast_pack` entity → assert drain `== 0` (endurance applies before/regardless of
   modifiers — same unconditional-early-return design decision as the first pass, now keyed
   correctly).
9. `test_hazard_drain_default_hazard_kind_no_regression` — region built with no explicit
   `hazard_kind` (defaults `"PHYSICAL"`), any faction (including `wild_beast_pack`) → assert
   drain equals the unchanged base formula (proves the new default doesn't accidentally grant
   universal immunity).

## Scoped Pytest Commands
```
pytest tests/unit/world/test_regional_consequences.py -v
pytest tests/unit/world/test_weather.py -v
pytest tests/integration/pipeline/test_recovery_gaps.py -v
pytest tests/unit/observability/test_event_extractor_world.py -v
pytest tests/unit/content_semantics/test_semantics.py -v
pytest tests/simulation_quality/test_world_dynamics_scorer.py -v
```
(Added `tests/unit/content_semantics/test_semantics.py` to the scoped set relative to the
first pass, since the corrected design adds a method to `FactionSemanticsService`.) Do not run
the full suite; scoped to `world`/`environment`/`content_semantics`/`world_dynamics` domains.

## Anti-Drift Test Guards
- Every new test asserts an **exact integer drain value**, not truthiness (matches existing
  file convention).
- Test #4 (different faction, same hazard kind) and test #5 (shared hazard kind, mutually
  hostile) are **mandatory, not optional** — they are the literal regression guards for the two
  concrete scenarios the user gave when rejecting the first design. Do not ship without both
  passing.
- Test #5 must use two factions that are actually hostile to each other (verify via
  `FactionSemanticsService.is_hostile` in the test setup or an assertion) so the test can't be
  satisfied by two mutually-neutral factions by accident.
- Do not mock `RegionState`/`FactionDefinition` — construct real dataclass/Pydantic instances,
  matching existing file conventions. Only the synthetic fiend test (#6) uses catalog
  injection, and only via the already-existing `configure_faction_semantics_service`/
  `reset_faction_semantics_service` pair — not ad hoc monkeypatching.
- If race-level `hazard_immunities` is ever added to `RaceDefinition`, these tests must be
  revisited (flag left in code comment at the new branch in `calculate_hazard_drain`).
