---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMP-NEST-CLASSIFICATION
artifact_type: test_plan
tags: [content, feature-flags]
---

# Test Plan — TCK-20260904-CAMP-NEST-CLASSIFICATION

## Regression Surface

**Unit — `tests/unit/world/`:**
- `tests/unit/world/test_camp_lifecycle.py` — all 3 existing tests
  (`test_camp_maturity_and_spawn`, `test_camp_clearing_reward`, `test_camp_raid_trigger`) must pass
  byte-for-byte unchanged. `test_camp_raid_trigger` in particular exercises the exact block (lines
  66-84 in `camp.py`) the new Nest fork is inserted into — it is the single most important
  regression test for this ticket, since it directly asserts the pre-existing raid outcome
  (`maturity_delta == -20.0`, `last_raid_tick_set == 500`) for a `kind="goblin"` camp, which must
  stay the Camp path unconditionally (goblin classifies as Camp, and even with the new flag ON,
  goblin's `kind` is not in `NEST_RACE_KINDS`).
- `tests/unit/world/test_natural_creature_reproduction.py` — all existing tests, especially
  `test_flag_off_by_default_does_not_spawn_natural_creature_offspring` and
  `test_reproduction_paths_never_mutate_region_directly` (architecture guard) — the new Nest branch
  sits in the same function and must not perturb block 4's independent flag gate or its own
  region-mutation discipline.
- `tests/unit/world/test_world_dynamics.py` — covers `WorldDynamicsSystem.resolve_dynamics()`,
  which calls `CampService.process_camps()` on cadence; confirm the Nest branch doesn't change
  cadence-triggering behavior for non-Nest camps.

**Integration:**
- `tests/integration/world/test_long_run_stability.py` — per
  `docs/world/raid_boss_camp_contract.md`'s own "Regression tests" section, this covers maturity
  growth, monster cap, and raid trigger threshold/outcome over a long run; must remain green with
  the flag at its default OFF.

**Content:**
- `tests/unit/content/test_catalog.py`, `tests/unit/content/test_layered_catalog.py`,
  `tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver` — this ticket reads
  `races.yaml` but does not modify its schema or the resolvers that consume it; these confirm that
  fact holds (no accidental schema drift).

## New Tests Required

1. **`test_nest_race_kinds_classification_matches_documented_table`**
   - Category: unit (data/logic parity guard)
   - Verifies: the module-level classification constant (e.g. `CampService.NEST_RACE_KINDS`)
     contains exactly `{"wolf", "spider", "troll", "slime"}` and no others — a direct guard against
     silent drift between the investigation's documented table and the implemented constant.
   - Location: `tests/unit/world/test_camp_lifecycle.py` (or a new
     `tests/unit/world/test_camp_nest_classification.py` if the implementer prefers a dedicated
     file for the classification-table tests as a group — reasonable either way).

2. **`test_camp_flag_off_nest_kind_camp_still_raids`**
   - Category: unit (regression / flag-off no-op)
   - Verifies: a camp with `kind="wolf"` (a Nest-eligible race) at raid maturity, with the new flag
     left at its default OFF, still produces the **existing raid outcome** (`maturity_delta ==
     -20.0`, `last_raid_tick_set` set, no offspring in `entities_add`) — proves flag-off is a true
     no-op even for a Nest-kind camp, not just for goblin.
   - Location: `tests/unit/world/test_camp_lifecycle.py`.

3. **`test_camp_flag_on_camp_kind_still_raids`**
   - Category: unit (regression / correct branch selection)
   - Verifies: with the new flag ON, a `kind="goblin"` (Camp-classified) camp at raid maturity still
     takes the raid outcome, not the spread outcome — proves the fork keys correctly off
     classification, not just the flag.
   - Location: `tests/unit/world/test_camp_lifecycle.py`.

4. **`test_camp_flag_on_nest_kind_spreads_instead_of_raiding`**
   - Category: unit (new behavior, core AC)
   - Verifies: with the new flag ON, a `kind="wolf"` (or another `NEST_RACE_KINDS` member) camp at
     `maturity >= RAID_MATURITY_THRESHOLD` and past the 500-tick cooldown produces the spread
     outcome (whatever Plan/Implement finalize it as — e.g. parentless offspring in
     `entities_add`) instead of a `RaidService`-shaped raid, while still applying the same
     `maturity_delta`/`last_raid_tick_set` cost fields.
   - Location: `tests/unit/world/test_camp_lifecycle.py` (new test, mirroring
     `test_camp_raid_trigger`'s shape) or a new dedicated Nest test file.

5. **`test_nest_spread_reuses_same_500_tick_cooldown_as_raid`**
   - Category: unit (anti-drift / timing-reuse guard)
   - Verifies: a Nest-kind camp below the 500-tick cooldown since `last_raid_tick`, even at
     `maturity >= RAID_MATURITY_THRESHOLD` with the flag ON, does **not** trigger a spread outcome
     — proves the Nest branch reuses the same cooldown gate, not an independent one.
   - Location: `tests/unit/world/test_camp_lifecycle.py`.

6. **`test_campstate_totem_stockpile_palisade_round_trip_canonical_dict`**
   - Category: unit (serialization / architecture guard)
   - Verifies: constructing a `CampState` with non-default `totem_tier`, `stockpile`,
     `palisade_integrity` values produces a `to_canonical_dict()` output that includes all three new
     keys with the correct values — direct regression guard against the documented "manually
     maintained dict, easy to silently miss a field" risk in `to_canonical_dict()`.
   - Location: `tests/unit/world/test_camp_lifecycle.py` or `tests/unit/core/test_state.py` if a
     dedicated state-serialization test module already exists for other typed state classes
     (confirm the existing pattern before choosing).

7. **`test_campupdate_totem_stockpile_palisade_merge_semantics`**
   - Category: unit (merge-logic guard)
   - Verifies: `CampUpdate.merge()` sums `stockpile_delta` across two updates (additive, matching
     `maturity_delta`'s convention) and prefers the non-`None` `totem_tier_set`/
     `palisade_integrity_set` from the incoming update (matching `active_set`/
     `last_raid_tick_set`'s convention) — mirrors the existing implicit contract already exercised
     by `maturity_delta`/`active_set` in the current file, now extended to the 3 new fields.
   - Location: `tests/unit/world/test_camp_lifecycle.py` or alongside other `CampUpdate` tests if a
     dedicated updates-merge test module exists.

8. **`test_campupdate_totem_stockpile_palisade_apply_via_apply_plan`**
   - Category: integration (architecture guard — authoritative-apply-path law)
   - Verifies: a `StateUpdate` carrying a `CampUpdate` with new-field deltas/sets, run through
     `ApplyPath.apply_partial()` (mirroring `test_natural_creature_reproduction.py`'s own
     `ApplyPath.apply_partial` usage pattern), produces a `next_state.camps[...]` with the new
     fields correctly committed — directly targets the single most likely silent-gap failure mode
     identified in investigation.md (new `CampUpdate` fields accepted but never actually applied in
     `apply_plan.py`'s camp block).
   - Location: `tests/unit/world/test_camp_lifecycle.py`.

9. **`test_nest_branch_does_not_construct_new_campstate`**
   - Category: architecture guard (behavioral-form, mirrors
     `test_natural_creature_reproduction_does_not_reference_genetics`'s `inspect.getsource` pattern)
   - Verifies: `inspect.getsource(CampService.process_camps)` never contains `CampState(` — direct
     guard against the Out-of-Scope violation risk flagged in investigation.md (no dynamic camp
     construction; WORLD-109 divergence note must stay true).
   - Location: `tests/unit/world/test_camp_lifecycle.py`.

10. **`test_nest_flag_registered_in_feature_flag_manager_default_off`**
    - Category: unit (registry consistency guard)
    - Verifies: the new flag name appears in `FeatureFlagManager().get_all_flags()` and
      `get_flag_mode(<name>)` returns `FeatureMode.OFF` by default — direct AC coverage for "flag
      registered in feature_flags.py's flag map, default OFF."
    - Location: a feature-flags test module if one exists for other recent flags (check
      `tests/unit/domains/optimization/` or similar before adding to `test_camp_lifecycle.py`), or
      `tests/unit/world/test_camp_lifecycle.py` if no dedicated flag-registry test module exists.

## Scoped Pytest Commands

```
pytest tests/unit/world/ -v
pytest tests/integration/world/test_long_run_stability.py -v
pytest tests/unit/content/test_catalog.py tests/unit/content/test_layered_catalog.py tests/unit/content/test_resolvers.py -v
```

Never `pytest tests/` — scope stays within `tests/unit/world/`, the one integration file
`docs/world/raid_boss_camp_contract.md` itself names as regression coverage for `camp.py`, and the
content/catalog tests confirming no `races.yaml`/resolver drift. If a dedicated feature-flags test
module is found during implementation, add it to the scoped command explicitly.

## Anti-Drift Test Guards

- `test_camp_flag_off_nest_kind_camp_still_raids` and `test_camp_flag_on_camp_kind_still_raids`
  (above) together prove the fork is keyed on **both** flag state and classification, not either
  alone — this is the single most important pair of guards against a broken conditional silently
  making the Nest branch fire for the wrong camps or never fire at all.
- `test_reproduction_paths_never_mutate_region_directly` (existing, `test_natural_creature_
  reproduction.py`) already covers `CampService.process_camps` as a whole for the durable-state law
  (`object.__setattr__`/`replace(region`-style direct mutation forbidden) — if the Nest branch adds
  any new region-touching logic (e.g. a spread-triggered population signal analogous to block 4's
  `population_young_births_delta` nudge), this existing guard's source-scan list should be extended
  to keep covering it, not left to silently age out.
- `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile` (existing) is a
  precedent worth mirroring if the Nest spread outcome also spawns offspring via
  `spawn_natural_creature_offspring` — confirm the Nest-spawned entities also have
  `lifecycle.genetic_profile is None`, consistent with the existing parentless-spawn family.
- `test_campstate_totem_stockpile_palisade_round_trip_canonical_dict` guards specifically against
  the documented "manually maintained `to_canonical_dict()` dict, not auto-derived" risk — this
  class of bug (field added to dataclass, forgotten in the serialization dict) has no compiler/type
  -checker protection in this codebase's pattern, so the test is the only real guard.
- `test_nest_branch_does_not_construct_new_campstate` guards the Out-of-Scope boundary with the
  next ticket (`TCK-20260904-CAMPSTATE-PLACE-BRIDGE`), which is explicitly responsible for
  eventually wiring real `CampState` construction — this ticket must not preempt that by
  accident.
