---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMP-NEST-CLASSIFICATION
artifact_type: plan
tags: [content, feature-flags]
---

# Implementation Plan — TCK-20260904-CAMP-NEST-CLASSIFICATION

## Summary

This plan implements a flag-gated Nest branch inside `CampService.process_camps`'s existing
raid-trigger gate (`src/world/camp.py:66-84`), keyed off a new `CampService.NEST_RACE_KINDS`
frozenset (`{"wolf", "spider", "troll", "slime"}`) checked against `CampState.kind`. The
City/Camp/Nest/Excluded classification for all 13 `races.yaml` races is a documentation-and-code
pair, not a single runtime lookup table: the *only* classification fact `CampService` needs at
runtime is "is this camp's kind Nest-eligible," because `CampState` instances are only ever
constructed with Camp-track `kind` values (`goblin`, `orc` today) or the new Nest-track kinds
(`wolf`, `spider`, `troll`, `slime`) — City races never populate `CampState.kind`, so a
City/Camp/neither discriminator has no runtime consumer in this ticket's scope and would be
unused dead code. The full 13-race table (already resolved in `investigation.md`, reproduced
below) is recorded as documentation in `docs/mechanics/05_world_evolution.md` and
`docs/world/raid_boss_camp_contract.md`; `NEST_RACE_KINDS` is its only code projection, and a new
test (`test_nest_race_kinds_classification_matches_documented_table`) is the parity guard between
the two. The Nest branch reuses `RAID_MATURITY_THRESHOLD`/`MATURITY_PER_TICK`/the existing
500-tick `last_raid_tick` cooldown unchanged, and produces its spread outcome by calling
`EntityGenerator.spawn_natural_creature_offspring` (the existing block-4 precedent,
`src/systems/world_systems/generator.py:86-121`) with `kind=camp.kind` directly — confirmed safe
because `.kind(kind)` (`generator.py:112`) is a free-form label with no registry validation, and
`camp.kind` values for Nest camps (`"wolf"`, `"spider"`, etc.) are already valid monster-kind
strings used elsewhere (`src/world/spawn_config.py:33` lists `"wolf"` in the FOREST spawn table).
No new `CampState` is constructed anywhere. Three new typed fields (`totem_tier`, `stockpile`,
`palisade_integrity`) are added to `CampState`/`CampUpdate` and wired through all three points a
durable field must touch to actually persist: the dataclass, `to_canonical_dict()`, `merge()`,
and — the step most likely to be silently skipped — `apply_plan.py`'s camp-application block
(`src/engine/apply_plan.py:275-286`), the sole authoritative commit point for `CampUpdate` fields.

## Classification Rule (record of decision — code projection is `NEST_RACE_KINDS` only)

| Race | Classification | Deciding rule |
|---|---|---|
| human, elf, dwarf, lizardfolk | City | `humanoid` + `tool_user` in `natural_traits`, AND `drive_profile != "opportunistic_raider"` |
| goblin, orc | Camp | `humanoid` + `tool_user` in `natural_traits`, AND `drive_profile == "opportunistic_raider"` |
| wolf, spider, troll, slime | Nest | `tool_user` absent from `natural_traits`, `cognition_profile == "instinctive_animal"`, `drive_profile == "territorial_predator"` |
| undead | Excluded (neither) | No `humanoid`/`tool_user` pair, no `instinctive_animal`/`territorial_predator` pair; population growth has no reproduction-concept fit (reanimation, not birth) — real, named gap, no owning ticket |
| spirit | Excluded (neither) | Same structural failure as undead; incorporeal (`spirit_body`), anchored-guardian archetype, not a raiding/breeding population — no owning ticket |
| dragonkin | Excluded (Lair-adjacent) | Fails both City/Camp (`natural_traits` omit `humanoid`/`tool_user`) and Nest (`cognition_profile` is `arcane_scholar`, not `instinctive_animal`); its profile matches idea 47's Lair concept, owned by `TCK-20260904-LAIR-ENTITY-ANCHOR` — excluded here to avoid double-scoping |

**Goblin contradiction, resolved**: goblin carries `social_humanoid` (shared with City races
human/elf) which the naive "camp races lack social_humanoid" heuristic wrongly treats as
discriminating. It is not: `social_humanoid` is present on City races *and* goblin, and absent
from orc (already the code's de facto second Camp race via the pre-existing
`"goblin_warrior" if camp.kind == "goblin" else "orc_warrior"` fallback at `camp.py:60`) — so
`social_humanoid` cannot be the decider. The actual discriminator is `drive_profile ==
"opportunistic_raider"`, which goblin and orc share exclusively among all 13 races and which
`natural_traits` alone does not expose (`races.yaml`, verified in `investigation.md`'s table).

**Code projection**: `NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll", "slime"})` on
`CampService`. City and Excluded races are not represented in code because nothing in this
ticket's scope constructs a `CampState` for them (`CampState` construction stays out of scope
per the ticket and WORLD-109's still-true divergence note).

## Steps

### Step 1 — Add `NEST_RACE_KINDS` classification constant to `CampService`

**Files:** `src/world/camp.py`

**Change:** Add a class-level constant immediately after the existing timing constants
(`src/world/camp.py:17-19`, i.e. after `CAMP_SPAWN_INTERVAL = 30`):
```python
NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll", "slime"})
```
This is the sole runtime representation of the Nest branch of the classification rule above. No
other code change in this step — this step only introduces the constant so Step 6 can consume it
and so the classification-parity test can be written and pass independently of the branching
logic.

**Do NOT touch:** Block 2 (garrison spawn, `camp.py:46-63`) — its `"goblin_warrior"/"orc_warrior"`
binary is not extended to Nest kinds in this step or any later step (see Anti-Drift Notes). Do not
add a City-side or Excluded-side constant — no code path in this ticket's scope consumes one.

**Verify:** `test_nest_race_kinds_classification_matches_documented_table` (new,
`tests/unit/world/test_camp_lifecycle.py`) — asserts `CampService.NEST_RACE_KINDS ==
frozenset({"wolf", "spider", "troll", "slime"})` exactly, no more, no fewer.

---

### Step 2 — Register `ENABLE_CAMP_NEST_SPREAD` feature flag

**Files:** `src/domains/optimization/feature_flags.py`

**Change:** `FeatureFlagManager.__init__`'s `_flags` dict (confirmed at
`src/domains/optimization/feature_flags.py:10-176`, terminating just before
`get_flag_mode`'s `return self._flags.get(flag, FeatureMode.OFF)` at line 187) is the canonical
flag registry. Add a new entry after the existing `"ENABLE_REPRODUCTION_HUMANOID_PATH":
FeatureMode.OFF` entry (line 164) and before `"ENABLE_INFORMATION_HUB_ACCUMULATION"` (line 176),
following the exact comment convention every recent sibling entry uses (cites this ticket ID,
states DEV-002 default-OFF policy, notes no corpus profile/SHADOW-validation history exists yet):
```python
# TCK-20260904-CAMP-NEST-CLASSIFICATION: gates the Nest spread-outcome branch in
# CampService.process_camps (default OFF per DEV-002; no corpus profile turns this on and
# no SHADOW-validation history exists).
"ENABLE_CAMP_NEST_SPREAD": FeatureMode.OFF,
```
This registration exists for discoverability/`serialize()`/`get_all_flags()` only — the actual
runtime gate check in `camp.py` (Step 6) does **not** call `FeatureFlagManager.is_enabled()`;
it reads `state.feature_flags` directly as a string dict, matching the one existing precedent in
`camp.py` itself (block 4, line 87: `flags.get("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "OFF")
== "ON"`). Using `FeatureFlagManager.is_enabled()` in `camp.py` would introduce a second,
inconsistent flag-reading convention inside the same function and is explicitly rejected.

**Other writers to this shared registry**: `FeatureFlagManager._flags` is a static dict populated
once in `__init__` and otherwise only read (`get_flag_mode`, `get_all_flags`, `serialize`) —
no other code path in the repo writes to it at runtime; this is an append-only dict literal, so
there is no ordering/race concern with concurrent writers, only the ordinary "don't collide with
another ticket's flag name" concern, which the search below rules out.

**Do NOT touch:** Any other entry in `_flags`. Do not route `camp.py`'s gate check through
`is_enabled()`.

**Verify:** `test_nest_flag_registered_in_feature_flag_manager_default_off` (new,
`tests/unit/world/test_camp_lifecycle.py`, per test_plan.md's fallback — no dedicated
feature-flag-registry test module was found under `tests/unit/domains/optimization/` for this
kind of check, so it stays in the world test module to keep the scoped pytest command in
test_plan.md accurate) — asserts `"ENABLE_CAMP_NEST_SPREAD"` appears in
`FeatureFlagManager().get_all_flags()` and `get_flag_mode("ENABLE_CAMP_NEST_SPREAD") ==
FeatureMode.OFF`.

---

### Step 3 — Add typed totem/stockpile/palisade fields to `CampState`

**Files:** `src/core/state.py`

**Change:** `CampState` (`src/core/state.py:1232-1261`, confirmed frozen/slotted dataclass with
exactly `id, kind, position, maturity, active, faction, last_raid_tick` plus the two cache
fields) gets three new fields added after `last_raid_tick: int = 0` (line 1241) and before the
cache fields:
```python
totem_tier: int = 0              # 0 = no totem; provisional numeric strength scale, unanchored
stockpile: float = 0.0           # accumulated resource stockpile; provisional magnitude, unanchored
palisade_integrity: float = 0.0  # 0 = no palisade; provisional defensive scale, unanchored
```
`to_canonical_dict()` (`src/core/state.py:1248-1261`) must add all three to its manually
maintained `res` dict (confirmed: this dict is hand-written, not derived from `dataclasses.fields`,
so a field added to the dataclass and omitted here silently drops from canonical hashing/replay —
this is the exact failure mode `investigation.md` flags as the highest-probability silent gap):
```python
"totem_tier": self.totem_tier,
"stockpile": self.stockpile,
"palisade_integrity": self.palisade_integrity,
```
Per the ticket's explicit note and `investigation.md`'s full-codebase confirmation (no
`totem`/`stockpile`/`palisade` string exists anywhere in `src/world/`, `src/core/state.py`, or
`src/core/updates.py` prior to this ticket), these defaults/magnitudes are provisional and must
be flagged as such in a code comment (above) and in the docs update (Step 8) — not presented as
tuned/balanced values.

**Other writers to `CampState`**: `CampState` instances are only ever constructed in test code
today (`tests/unit/world/test_camp_lifecycle.py`, `test_natural_creature_reproduction.py`) —
confirmed via `investigation.md`'s citation of `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own
finding ("no production code currently constructs `CampState()`"). The only place an *existing*
`CampState` is mutated is `apply_plan.py`'s `replace(camp, ...)` call (Step 5) — no other writer
exists to race with.

**Do NOT touch:** `position`, `active`, `faction`, or any other existing field's type or default.
Do not remove or rename the `_canonical_cache`/`_readonly_cache` machinery.

**Verify:** `test_campstate_totem_stockpile_palisade_round_trip_canonical_dict` (new,
`tests/unit/world/test_camp_lifecycle.py`) — constructs a `CampState` with non-default values for
all three new fields and asserts `to_canonical_dict()` includes all three keys with correct
values.

---

### Step 4 — Add matching delta/set fields to `CampUpdate` and extend `merge()`

**Files:** `src/core/updates.py`

**Change:** `CampUpdate` (`src/core/updates.py:890-905`, confirmed frozen/slotted dataclass with
`id, maturity_delta, active_set, last_raid_tick_set` and a `merge()` that sums
`maturity_delta` and prefers non-`None` `_set` fields from the incoming update) gets three new
fields added after `last_raid_tick_set: Optional[int] = None` (line 896), following the file's
existing `_delta`/`_set` naming convention exactly:
```python
totem_tier_set: Optional[int] = None
stockpile_delta: float = 0.0
palisade_integrity_set: Optional[float] = None
```
`merge()` (lines 898-905) is extended to match the existing additive/non-None-wins pattern
exactly:
```python
def merge(self, other: CampUpdate) -> CampUpdate:
    if self.id != other.id:
        raise ValueError("Cannot merge CampUpdates for different camps")
    return replace(self,
        maturity_delta=self.maturity_delta + other.maturity_delta,
        active_set=other.active_set if other.active_set is not None else self.active_set,
        last_raid_tick_set=other.last_raid_tick_set if other.last_raid_tick_set is not None else self.last_raid_tick_set,
        stockpile_delta=self.stockpile_delta + other.stockpile_delta,
        totem_tier_set=other.totem_tier_set if other.totem_tier_set is not None else self.totem_tier_set,
        palisade_integrity_set=other.palisade_integrity_set if other.palisade_integrity_set is not None else self.palisade_integrity_set,
    )
```

**Other writers to `CampUpdate.merge()`**: `merge()` is called wherever two `CampUpdate`s for the
same camp id need combining. `camp.py`'s `process_camps` currently only ever assigns
`camp_updates[c_id] = CampUpdate(...)` once per camp per call (blocks 1 and 3 both write to the
same dict key without merging — block 3's raid-trigger assignment at line 80 *overwrites* block
1's maturity-evolution assignment at line 44 rather than merging with it; this is pre-existing
behavior, confirmed by reading `camp.py:36-84`, and out of scope to change here). The Nest branch
(Step 6) must follow the exact same pre-existing overwrite pattern for consistency — it replaces
block 3's assignment on the Nest-kind path, it does not call `.merge()` against block 1's update.
No other current call site merges `CampUpdate`s for the same camp within a single `process_camps`
invocation, so there is no double-counting risk introduced by adding `stockpile_delta` as
additive.

**Do NOT touch:** `id`, `maturity_delta`, `active_set`, `last_raid_tick_set`, or their existing
merge semantics.

**Verify:** `test_campupdate_totem_stockpile_palisade_merge_semantics` (new,
`tests/unit/world/test_camp_lifecycle.py`) — asserts `stockpile_delta` sums across two merged
updates and `totem_tier_set`/`palisade_integrity_set` follow non-None-wins from the incoming
update.

---

### Step 5 — Wire new `CampUpdate` fields through `apply_plan.py`'s authoritative commit point

**Files:** `src/engine/apply_plan.py`

**Change:** The camp-application block (`src/engine/apply_plan.py:275-286`, confirmed as the
single place `CampUpdate` fields are consumed to produce the next `CampState`) currently reads
`maturity_delta`, `active_set`, `last_raid_tick_set` explicitly and calls `replace(camp,
maturity=new_mat, active=new_act, last_raid_tick=new_raid)` (line 285). Extend it to also read
and apply the three new fields, following the identical per-field pattern already used for
`active_set`/`last_raid_tick_set`:
```python
new_totem = c_upd.totem_tier_set if c_upd.totem_tier_set is not None else camp.totem_tier
new_stockpile = camp.stockpile + c_upd.stockpile_delta
new_palisade = c_upd.palisade_integrity_set if c_upd.palisade_integrity_set is not None else camp.palisade_integrity
new_camps[c_id] = replace(camp, maturity=new_mat, active=new_act, last_raid_tick=new_raid,
                           totem_tier=new_totem, stockpile=new_stockpile,
                           palisade_integrity=new_palisade)
```
This is explicitly called out because, per `investigation.md`, omitting this step is the single
most likely silent-gap failure mode for the ticket: new `CampUpdate` fields would be accepted by
the dataclass and `merge()` but never actually committed to `AuthoritativeState.camps`, and no
test outside this exact code path would catch it (the round-trip and merge tests in Steps 3/4
only exercise the dataclasses directly, not the apply pipeline).

**Other writers to `new_camps`/`AuthoritativeState.camps`**: this loop (`apply_plan.py:276-285`)
is confirmed as the only writer inside `apply_plan.py`'s camp handling; `src/engine/apply.py:222,415`
only wires `plan.world_collection_changes["camps"]` through unchanged with no camp-specific field
logic (confirmed by investigation.md). No other module writes to `state.camps` outside this
function and `AuthoritativeState`'s own initial construction — there is no concurrent-writer
ordering concern for this step.

**Do NOT touch:** The `new_mat`/`new_act`/`new_raid` lines or the `"camps" in cols` gating logic
around this block. Do not change how `new_camps` is initialized (line 276).

**Verify:** `test_campupdate_totem_stockpile_palisade_apply_via_apply_plan` (new,
`tests/unit/world/test_camp_lifecycle.py`) — builds a `StateUpdate` carrying a `CampUpdate` with
non-default deltas/sets for all three new fields, runs it through `ApplyPath.apply_partial(state,
update)` (mirroring the existing pattern at `tests/unit/world/test_natural_creature_reproduction.py:199,225`),
and asserts `next_state.camps[...]` reflects all three new field values correctly.

---

### Step 6 — Implement the Nest branch fork inside the existing raid-trigger gate

**Files:** `src/world/camp.py`

**Change:** Inside block 3, "Raid Trigger" (`camp.py:65-84`), fork on flag + `NEST_RACE_KINDS`
membership *inside* the existing `camp.maturity >= RAID_MATURITY_THRESHOLD` /
`state.tick - camp.last_raid_tick >= 500` gate (both conditions unchanged — this is the same gate
`test_camp_raid_trigger` already exercises), rather than adding a fifth independent block:
```python
# 3. Raid Trigger (or Nest Spread, for Nest-classified camps with the flag ON)
if camp.maturity >= CampService.RAID_MATURITY_THRESHOLD:
    if state.tick - camp.last_raid_tick >= 500:  # 5 days
        is_nest_spread = (
            flags.get("ENABLE_CAMP_NEST_SPREAD", "OFF") == "ON"
            and camp.kind in CampService.NEST_RACE_KINDS
        )
        if is_nest_spread:
            offspring = generator.spawn_natural_creature_offspring(
                camp.position,
                state=state,
                kind=camp.kind,
                difficulty_tier=int(camp.maturity / 20.0) + 1,
                birth_tick=state.tick,
            )
            entities_add.append(offspring)
            camp_updates[c_id] = CampUpdate(
                id=c_id,
                maturity_delta=-20.0,  # same cost as raiding, per ticket's "reuses timing" requirement
                last_raid_tick_set=state.tick,
            )
        else:
            # existing, byte-for-byte unchanged raid outcome
            from src.world.raid import RaidService
            raid_update = RaidService.check_for_raid(state, generator)
            for mob in raid_update.entities_add:
                pass
            camp_updates[c_id] = CampUpdate(
                id=c_id,
                maturity_delta=-20.0,
                last_raid_tick_set=state.tick,
            )
```
Decision on the spread-outcome mechanism (the investigation's flagged open question, resolved
here per its own stated recommendation): spawn one parentless same-kind offspring near the camp
via `EntityGenerator.spawn_natural_creature_offspring`, keyed off `camp.kind` directly (no
`goblin_warrior`/`orc_warrior`-style archetype mapping needed — `NEST_RACE_KINDS` members are
already plain monster-kind strings; confirmed `.kind(kind)` at `generator.py:112` is a free-form
label with no registry validation, and `"wolf"` is already used as a monster kind elsewhere,
`src/world/spawn_config.py:33`). This is the only existing precedent in `process_camps` for a
parentless population-growth spawn (block 4), it does not construct a new `CampState` (satisfying
the Out-of-Scope constraint and keeping WORLD-109's divergence note true), and it applies the same
`maturity_delta=-20.0`/`last_raid_tick_set=state.tick` cost/cooldown-reset the raid path uses, per
the ticket's explicit "reuses timing" requirement.

**Other writers to `camp_updates[c_id]` within this call**: as noted in Step 4, block 1
(`camp.py:44`) writes `camp_updates[c_id]` first for maturity evolution, and this block
overwrites it (pre-existing behavior, unchanged by this ticket) — the Nest branch's assignment
follows the identical overwrite shape the existing raid branch already uses at line 80, so no new
double-write pattern is introduced. Block 4 (Natural-Creature Reproduction, lines 87-116) does not
touch `camp_updates` at all (it only touches `entities_add`/`world_updates`), so there is no
interaction between the Nest branch and block 4 through `camp_updates`.

**Do NOT touch:** Block 2 (garrison spawn, lines 46-63) — do not extend its
`"goblin_warrior"/"orc_warrior"` binary to Nest kinds; block 4 (lines 87-116) — its own
independent flag gate and region-mutation discipline must be undisturbed; the raid-outcome
branch's logic beyond wrapping it in the new `else`. Do not give the Nest branch an independent
cooldown or threshold.

**Verify:**
- `test_camp_flag_off_nest_kind_camp_still_raids` (new) — `kind="wolf"` camp, flag OFF → raid
  outcome (regression, proves flag-off no-op even for Nest kinds).
- `test_camp_flag_on_camp_kind_still_raids` (new) — `kind="goblin"` camp, flag ON → raid outcome
  (proves the fork keys on classification, not flag alone).
- `test_camp_flag_on_nest_kind_spreads_instead_of_raiding` (new) — `kind="wolf"` camp, flag ON →
  spread outcome (offspring in `entities_add`, no `RaidService` call), same cost fields applied.
  This is the ticket's core new-behavior AC.
- `test_nest_spread_reuses_same_500_tick_cooldown_as_raid` (new) — Nest-kind camp under the
  500-tick cooldown, flag ON, maturity above threshold → no spread outcome (proves shared
  cooldown, not an independent one).
- `test_nest_branch_does_not_construct_new_campstate` (new) — `inspect.getsource(CampService.process_camps)`
  never contains `"CampState("`, mirroring the existing
  `test_natural_creature_reproduction_does_not_reference_genetics` pattern.
- `test_camp_raid_trigger`, `test_camp_maturity_and_spawn`, `test_camp_clearing_reward`
  (existing, `test_camp_lifecycle.py`) — must pass byte-for-byte unchanged.
- `test_reproduction_paths_never_mutate_region_directly` (existing,
  `test_natural_creature_reproduction.py`) — must still pass; the Nest branch adds no
  region-touching mutation, so its source-scan list needs no extension.
- `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`-style guard: since
  the Nest branch spawns via the same `spawn_natural_creature_offspring` call, confirm (as part of
  writing `test_camp_flag_on_nest_kind_spreads_instead_of_raiding`, or a small addition to it) that
  the spawned offspring's `lifecycle.genetic_profile is None`, consistent with the existing
  parentless-spawn family.

---

### Step 7 — Update docs

**Files:** `docs/mechanics/05_world_evolution.md`, `docs/world/raid_boss_camp_contract.md`,
`docs/parity_ledger/world_dynamics.yaml`

**Change:**
- `docs/mechanics/05_world_evolution.md` §6 "Calamities & World Threats": add a new `###`-level
  subsection immediately after the existing "### Natural-Creature Reproduction" subsection,
  following that subsection's exact prose/structure shape (trigger condition, flag name,
  spread-outcome mechanism). Include the classification table from this plan's "Classification
  Rule" section (or a pointer to `investigation.md`/this plan for the full table plus the
  goblin-resolution and 5-race-disposition rationale).
- `docs/world/raid_boss_camp_contract.md`: update the "Raid trigger" subsection to describe the
  new fork (Camp-classified → raid outcome unchanged; Nest-classified + flag ON → spread outcome),
  add a "Camp/Nest classification" note (or pointer), and add the Nest branch as a second
  documented precedent under "Extension rules" (currently rule 1 only). **Precision requirement**:
  describe the cost as the same relative `maturity_delta=-20.0` the raid path already uses — do
  not describe it as "resets to 50" or any absolute value. The existing raid-trigger prose in this
  same doc already contains a pre-existing "resets to 50" vs. actual `-20.0`-relative-delta drift
  (confirmed in `investigation.md`, not this ticket's bug to fix); the new Nest text must not
  repeat that imprecision even though it is describing the identical numeric delta.
- `docs/parity_ledger/world_dynamics.yaml`: add a new entry with the next sequential `WORLD-1xx`
  id (following `WORLD-118`/`WORLD-119`'s numbering, lines 1629-1728), describing the Nest
  spread-outcome behavior, its flag gate (`ENABLE_CAMP_NEST_SPREAD`, default OFF), and
  `v2_evidence`/`test_path` pointing at `tests/unit/world/test_camp_lifecycle.py`'s new Nest
  tests — mirroring `WORLD-119`'s shape exactly. Use `tools/parity_ledger_writer.py` for this
  edit, not a raw YAML edit (per project convention — large full-file YAML rewrites via raw
  Edit risk corruption; the writer script is schema-validating).

**Do NOT touch:** `docs/parity_ledger/world_dynamics.yaml`'s WORLD-109 entry (still true, no
change needed — see investigation.md), `docs/mechanics/content_usage_matrix.md`'s `living/races`
row (no schema change to `races.yaml` occurred), or
`docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` (scope-tracking doc, not updated by
child-ticket implementation work).

**Verify:** No automated test; confirmed by re-reading the added sections against the "Docs
Requiring Update" list in `investigation.md` before closing the ticket, and by
`make knowledge-index-update` per the project's After-Work checklist since `docs/` files changed.

## Scope Guards

- No change to `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, or any
  `WorldModuleSpec` — no CampState/Nest is seeded at world-compile time by this ticket.
- No change to `src/world/creature_territory.py`'s `CreatureTerritoryService` — confirmed
  structurally independent (per-entity `IdentityComponent.territory_maturity`, not
  `CampState.maturity`); do not merge, extend, or reference it from the Nest branch.
- No dissolution/transformation mechanic for Camp/Nest content on any trigger — that belongs to
  idea 48, no ticket yet.
- No extension of block 2's garrison-spawn `"goblin_warrior"/"orc_warrior"` binary to
  wolf/spider/troll/slime kinds, unless a later Verify-phase finding shows the spread outcome is
  unobservable without it — if that happens, it must be raised explicitly, not silently added.
- No new `CampState` construction anywhere in `process_camps` (guarded by
  `test_nest_branch_does_not_construct_new_campstate`).
- No routing of the new flag through `FeatureFlagManager.is_enabled()` inside `camp.py`.
- No change to `docs/parity_ledger/world_dynamics.yaml`'s WORLD-109 entry, WORLD-030/031 entries,
  `docs/mechanics/content_usage_matrix.md`, or `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`.
- No City-side or Excluded-side classification constant in code — only `NEST_RACE_KINDS` is
  implemented, per the Summary's reasoning.

## Dependency Map

- Step 1 (constant) — independent.
- Step 2 (flag registration) — independent.
- Step 3 (`CampState` fields) — independent.
- Step 4 (`CampUpdate` fields) — independent of Steps 1-3, but its merge test benefits from Step 3
  existing first only in the sense that both dataclasses' fields are easier to reason about
  together; no actual code dependency.
- Step 5 (`apply_plan.py` wiring) — depends on Step 3 (needs `CampState.totem_tier` etc. to exist
  for `replace(...)` to accept them) and Step 4 (needs `CampUpdate`'s new `_set`/`_delta` fields to
  read from). Must land after both.
- Step 6 (Nest branch fork) — depends on Step 1 (`NEST_RACE_KINDS`) and Step 2 (flag name/default
  must exist for the gate check to reference, though the raw string key works even before Step 2
  lands — Step 2 is required for the AC's registry requirement, not for Step 6's code to run).
- Step 7 (docs) — should land last, once the final flag name, field names, and branch behavior
  from Steps 1-6 are settled, so the docs describe the actual shipped shape.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Classification decision recorded for all 13 races, goblin contradiction resolved, 5 unclassified races given explicit disposition | This plan's "Classification Rule" section + `investigation.md` (Step 1 for the code projection) | `test_nest_race_kinds_classification_matches_documented_table` |
| New flag (default OFF) gates Nest branch; flag OFF → existing raid-branch tests pass unchanged | Step 2 (registration), Step 6 (gate check) | `test_camp_raid_trigger`, `test_camp_maturity_and_spawn`, `test_camp_clearing_reward` (existing, unchanged), `test_camp_flag_off_nest_kind_camp_still_raids` |
| Flag ON + Nest-kind camp at `RAID_MATURITY_THRESHOLD` → spread outcome using same `MATURITY_PER_TICK` accrual | Step 6 | `test_camp_flag_on_nest_kind_spreads_instead_of_raiding`, `test_nest_spread_reuses_same_500_tick_cooldown_as_raid`, `test_camp_flag_on_camp_kind_still_raids` |
| `CampState`/`CampUpdate` carry typed totem/stockpile/palisade fields, round-trip via `to_canonical_dict()`/merge, covered by serialization test | Steps 3, 4, 5 | `test_campstate_totem_stockpile_palisade_round_trip_canonical_dict`, `test_campupdate_totem_stockpile_palisade_merge_semantics`, `test_campupdate_totem_stockpile_palisade_apply_via_apply_plan` |
| No `WorldModuleSpec`/`WorldCompiler`/world-generation code touched | Scope Guards (no step touches these files) | `test_nest_branch_does_not_construct_new_campstate`; manual diff review at Verify phase confirms no `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/` files changed |

## Anti-Drift Notes

- The existing raid branch's `for mob in raid_update.entities_add: pass` no-op loop
  (`camp.py:74-78`) is pre-existing dead code, not something this ticket introduces or should
  "clean up" — preserve it byte-for-byte in the `else` branch so `test_camp_raid_trigger`'s
  behavior stays identical; do not refactor it as a drive-by change.
- `camp_updates[c_id]` is overwritten (not merged) between block 1 and block 3 today — this is
  pre-existing behavior (confirmed by reading the source, not assumed), and the Nest branch must
  preserve this exact overwrite semantics rather than introducing a `.merge()` call, to avoid
  silently changing block 1's maturity-evolution delta's fate on a raid/spread tick.
  Investigating whether this overwrite is itself a latent bug is out of scope for this ticket.
- `docs/world/raid_boss_camp_contract.md`'s pre-existing "resets to 50" imprecision (vs. the
  actual `-20.0` relative delta) is not this ticket's bug to fix, but the new Nest-branch prose
  added to that same file must describe the cost correctly as a relative delta, not repeat the
  ambiguity in new text.
- Totem/stockpile/palisade numeric defaults (`0`, `0.0`, `0.0`) and any accrual logic are
  explicitly not implemented as "tuned" values by this ticket — the ticket only requires the
  typed fields to exist and round-trip; no accrual/production logic for totem/stockpile/palisade
  is in scope (the ticket's Scope section does not request one, and inventing one would be scope
  creep). If Implement finds a reason accrual logic is needed to make a field "used," flag it
  explicitly rather than adding it silently.
- A camp with `ENABLE_CREATURE_TERRITORY_LIFECYCLE` also ON alongside a Nest-classified camp with
  `ENABLE_CAMP_NEST_SPREAD` ON is a real, uncoordinated-but-non-conflicting combinatorial case
  (confirmed structurally independent mechanisms in `investigation.md`) — no code change needed
  for this ticket, just worth the implementer knowing it is not a bug if both fire near the same
  camp.

## Unresolved Questions

None. All items the investigation flagged as open (spread-outcome mechanism, Nest-vs-Camp keying
field, flag name/convention) are resolved explicitly above.
