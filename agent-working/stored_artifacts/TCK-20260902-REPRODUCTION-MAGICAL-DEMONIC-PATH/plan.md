---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH
artifact_type: plan
tags: [lifecycle, world]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH

## Summary

Add a fifth, additive, flag-gated spawn branch inside `CalamityService.process_world_dynamics`
(`src/world/calamity.py:22-59`) that spawns a parentless, full-ADULT magical/demonic entity
alongside the existing `world_boss` spawn, on the exact same `should_spawn`/`target_region`
evaluation already used by that boss branch — no new trigger vocabulary, no population-pressure
gate, no maturation clock. The approach mirrors `CampService.process_camps()`'s own "4.
Natural-Creature Reproduction" branch (`src/world/camp.py:85-104`, parity ledger `WORLD-120`) in
every respect except the two the ticket explicitly inverts: no `life_stage=LifeStage.CHILD` /
`age_ticks` maturation-clock trick (this path spawns directly at the `IdentityComponent.life_stage`
default of `ADULT`, `src/core/state.py:512`), and no population-pressure suppression gate (the
existing `world_boss` branch it sits beside has never had one, and the atlas explicitly pairs the
dormant population-pressure signal `WD-15` with the *human/humanoid* path `WD-16`, not with `WD-08`
— the calamity substrate this ticket reuses; `docs/brainstorm/rpg_feature_atlas.html` line 947).
A new `EntityGenerator.spawn_magical_demonic_entity()` method (additive sibling to `spawn_monster`,
never a modification of it) builds the entity with `kind="magical_demonic_entity"`,
`role=EntityRole.MONSTER`, `faction=Faction.MONSTER_HORDE` — the only content-catalog values that
exist for a calamity-spawned hostile entity today — and populates the parentless birth record via
the already-shipped `V2EntityBuilder.birth_record(parent_a_entity_id=None,
parent_b_entity_id=None, birth_tick=state.tick, birth_city_id=None)`. The flag
(`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`, default OFF) is checked in-service inside
`process_world_dynamics`, matching `CampService`'s idiom (`camp.py:28`, `flags = getattr(state,
"feature_flags", None) or {}`), because — like `CampService.process_camps` — `CalamityService.
process_world_dynamics` is itself called unconditionally from `world_dynamics.py:133` and the new
branch must reuse the *same* `target_region` the boss branch already selected, which is only
available inside the function body.

## Decisions (resolving the three open questions)

### Decision 1 — Population-pressure gate: does NOT apply to this path

**Evidence:**
- The existing `world_boss` branch this ticket sits beside (`calamity.py:39-58`) has zero
  reference to `compute_regional_scarcity()`, `migration_threshold`, or `population_cohorts` —
  it is purely `calamity_intensity`-driven. This is the direct sibling-branch precedent, and the
  ticket's own Scope text says to follow "its existing intensity/trigger pattern."
- `docs/brainstorm/rpg_feature_atlas.html` line 947 (idea 32 card): "32 splits three ways: natural
  births reuse `WD-14` almost directly, magical births reuse `WD-08`, and the human/humanoid
  marriage-gated path has no existing precedent at all — needs a new cadence-gated sub-phase
  (proposed `WD-16`), **paired with `WD-15`'s dormant population-pressure signal**." The
  population-pressure signal is explicitly paired with the new human/humanoid `WD-16` sub-phase,
  not with `WD-08` (confirmed as `CalamityService.process_world_dynamics()` verbatim at
  `docs/audits/D19_domain_phase_inventory.md:261`) — the exact function this ticket's magical path
  reuses.
- Conceptually, a calamity-driven spawn is a world-threat escalation event, not a settlement/camp
  demographic signal — the Migration Law (§5) is authored around `PopulationCohort`s that live on
  `RegionState`, seeded by settlement/camp demographics, not calamity intensity.

**Consequence:** Test Plan item 8 ("Population-pressure gate (conditional on Plan's resolution)")
is **not required**. No `compute_regional_scarcity()`/`migration_threshold` reference is added
anywhere in this ticket's code.

### Decision 2 — Trigger relationship and flag-gating location

**Trigger relationship:** ADDITIVE, inside the *same* `should_spawn`/`target_region` evaluation as
the existing `world_boss` spawn (`calamity.py:39-44`) — not a separate/parallel condition. The new
branch reuses the identical `CALAMITY_MIN_INTERVAL`/`CALAMITY_FORCE_INTERVAL`/`calamity_intensity >
0.3` filter and the already-selected `target_region`, and issues a *second*, independent
`generator.spawn_magical_demonic_entity(...)` call appended to `entities_add` alongside `boss`.
This matches the ticket's Scope text verbatim ("at or above its existing trigger threshold... same
intensity/trigger pattern") and avoids introducing any new authored magic number.

**Flag-gating location:** in-service, inside `CalamityService.process_world_dynamics`, matching
`CampService.process_camps`'s idiom (`camp.py:28`, `flags = getattr(state, "feature_flags", None)
or {}`, checked at `camp.py:86` wrapping only its new branch) — **not** the call-site idiom used by
`CreatureTerritoryService` (`world_dynamics.py:194-199`).

**Rationale:** `CalamityService.process_world_dynamics`, like `CampService.process_camps`, is
already called *unconditionally* from `world_dynamics.py` (line 133 for calamity, line 168 for
camps) with no existing call-site gate — this is structurally the same situation `CampService`
already solved. `CreatureTerritoryService`, by contrast, is a *new standalone call* added to
`world_dynamics.py` (lines 193-199) with no pre-existing unconditional call to nest inside, so a
call-site gate was the only option there. This ticket's new branch must reuse the boss branch's
already-computed `target_region` (to position the magical/demonic entity in the same
highest-intensity region), which is a local variable inside `process_world_dynamics` — only
reachable from an in-service check, not a call-site one. Following `CampService`'s idiom exactly
also keeps this ticket's own code shape identical to its structural sibling, `WORLD-120`.

### Decision 3 — Content-catalog `kind`/faction value

**`kind`:** no existing "demon"/"magical-being" `kind` string exists anywhere in `src/` (confirmed
via `grep -rn "demon\|Demon\|DEMON\|magical_being\|MAGICAL" src/ --include=*.py -i`; the only hits
are `SkillCategory.MAGICAL`/`SkillType.MAGICAL` — an unrelated skill-scaling category
[`src/core/skills.py:12`, `src/systems/lifecycle_systems/genetics.py:17`] — and a region content
tag `"magical"` on the `moon_cave` region definition [`src/core/registries.py:725`], neither of
which is an entity `kind`). Decision: new descriptive `kind="magical_demonic_entity"`, following
the same free-text descriptive-string convention already used by every other spawn method in
`generator.py` (`"world_boss"`, `"goblin_warrior"`/`"orc_warrior"`, `"goblin"` — none of these are
catalog-registered either; `kind` is a free descriptive field on `EntityState`, not a registry
lookup — confirmed by `V2EntityBuilder.kind()` at `src/core/builder.py:114`, a plain string setter).

**`faction`/`role`:** `Faction` is a closed `IntEnum` with exactly 4 members —
`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL` (`src/core/enums.py:24-28`), mirrored
verbatim by `FactionDefinition.valid_buckets` in the content-catalog schema
(`src/content/schema.py:172`: `{"HERO_GUILD", "MONSTER_HORDE", "TOWN_COUNCIL", "NEUTRAL"}`) — no
demonic/magical faction bucket exists, and adding a new enum member is a schema change out of this
ticket's scope. `EntityRole` is likewise a closed 6-member `IntEnum`
(`src/core/enums.py:6-12`: `HERO`/`SHOPKEEPER`/`MONSTER`/`CITIZEN`/`WORKER`/`GUARD`). Decision:
reuse `role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE` — the exact pair already used by
every other spawn method in `generator.py` that produces a hostile creature (`spawn_monster`
line 79, `spawn_natural_creature_offspring` line 113, `spawn_calamity` line 161, `spawn_goblin`
line 142) — a calamity-spawned magical/demonic being is squarely within that same existing
"hostile creature" bucket; no new value is invented.

## Steps

### Step 1 — Register the feature flag
**Files:** `src/domains/optimization/feature_flags.py`
**Change:** Append `"ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH": FeatureMode.OFF,` immediately after
the existing `"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": FeatureMode.OFF,` entry
(`feature_flags.py:146`), with a DEV-002-style comment block matching the sibling entry's wording
(new mechanic, no corpus-profile turn-on, no SHADOW-validation history) but naming this ticket
(`TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH`) and this file (`src/world/calamity.py`). This is
its own distinct flag — never an alias of or rename to
`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (per the sibling ticket's own Decision 3 convention:
"each is its own per-ticket flag").
**Do NOT touch:** `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, `ENABLE_CREATURE_TERRITORY_LIFECYCLE`,
or any other existing flag entry.
**Verify:** Test Plan item 5 (flag defaults OFF) —
`FeatureFlagManager().get_flag_mode('ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH') ==
FeatureMode.OFF`.

### Step 2 — Add `EntityGenerator.spawn_magical_demonic_entity()`
**Files:** `src/systems/world_systems/generator.py`
**Change:** Add a new method immediately after `spawn_natural_creature_offspring()` (after line
120), structurally modeled on it but with the CHILD/`age_ticks` maturation-clock lines removed per
Decision 3/Anti-Drift:
```python
def spawn_magical_demonic_entity(
    self, pos: tuple[float, float], state: AuthoritativeState | None = None,
    kind: str = "magical_demonic_entity", difficulty_tier: int = 4, birth_tick: int = 0,
) -> EntityState:
    """Spawn a parentless magical/demonic entity directly at ADULT life stage (no
    CHILD->ADULT maturation clock), with birth-record fields populated via the
    parentless V2EntityBuilder.birth_record() path (both parent ids None)."""
    entity_id = self.get_next_id()
    from src.world.spawn_config import DIFFICULTY_TIERS
    mults = DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])
    tick = state.tick if state else 0
    evolution_level = self.rng.get_int(Domain.SPAWN, tick, entity_id, mults.level_min, mults.level_max)
    base_hp = 50 * mults.hp
    base_atk = 10 * mults.atk
    base_def = 5 * mults.def_stat
    base_gold = 10 * mults.gold
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(entity_id)
        .kind(kind)
        .location(*pos)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE,
                  evolution_level=evolution_level)
        .navigation(home_position=pos, leash_radius=10.0)
        .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
        .inventory(gold=int(base_gold))
        .birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick, birth_city_id=None)
        .build())
```
Note: deliberately **no** `.lifecycle(age_ticks=...)` call and **no** `life_stage=LifeStage.CHILD`
kwarg to `.identity(...)` — `IdentityComponent.life_stage` defaults to `LifeStage.ADULT`
(`src/core/state.py:512`), satisfying AC2 by omission, not by a new mechanism. `difficulty_tier`
defaults to `4` to match the existing `world_boss` spawn's own `difficulty_tier=4`
(`calamity.py:51`) — same escalation tier, since both entities emerge from the same
high-intensity-region trigger.
**Do NOT touch:** `spawn_monster()` (line 59) — its signature has 7+ call sites across the
codebase (per investigation's Anti-Drift Hazards); do not modify it. Do NOT touch
`spawn_natural_creature_offspring()` (lines 85-120) or `spawn_goblin()`/`spawn_calamity()` — this
is a purely additive new method.
**Verify:** Test Plan items 1-3 (spawn produces an entity; `life_stage == LifeStage.ADULT` with no
CHILD kwarg or pre-seeded `age_ticks`; `parent_a_entity_id is None`, `parent_b_entity_id is None`,
`birth_tick` equals spawn tick, `birth_city_id is None`).

### Step 3 — Add the additive branch inside `CalamityService.process_world_dynamics`
**Files:** `src/world/calamity.py`
**Change:** Inside the existing `if should_spawn:` block (`calamity.py:39-58`), after the existing
`boss = generator.spawn_monster(...)` call and its `updates = updates.replace(...)` (lines 47-57),
add a new nested check reusing the *same* `target_region` already selected at line 44:
```python
flags = getattr(state, "feature_flags", None) or {}
if flags.get("ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH", "OFF") == "ON":
    magical_demonic_entity = generator.spawn_magical_demonic_entity(
        state=state,
        pos=target_region.center,
        birth_tick=state.tick,
    )
    updates = updates.replace(
        entities_add=updates.entities_add + [magical_demonic_entity],
    )
```
Place the `flags = getattr(...)` line once, near the top of the method (mirroring
`camp.py:28`'s placement at the top of `process_camps`), not repeated inline — per the sibling
ticket's Anti-Drift Note "flag is checked once, wrapping only the new block." The new block must
run only when `should_spawn` is true and `high_intensity_regions` is non-empty (i.e., nested inside
the existing `if high_intensity_regions:` body, after the boss spawn), so it shares the exact same
trigger evaluation and target region as the boss — per Decision 2.
**Do NOT touch:** the `should_spawn`/`high_intensity_regions`/`target_region` computation
(`calamity.py:34-44`), the existing `boss = generator.spawn_monster(...)` call or its
`updates.replace(...)` (lines 47-57), the Maturity Advancement block (lines 29-31),
`apply_calamity_consequences()` (lines 61-82), or `CalamityPressurePropagator.propagate_seasonal()`
(lines 85-146). Do NOT reference `compute_regional_scarcity()`/`migration_threshold`/
`population_cohorts` anywhere in this branch (Decision 1). Do NOT add a
`population_cohorts_set` entry to `updates` under any circumstance.
**Verify:** Test Plan item 1 (flag ON → magical/demonic entity spawns on trigger); Test Plan item 5
(flag OFF → `process_world_dynamics`'s output is byte-identical to today's, i.e. no
`magical_demonic_entity` kind in `entities_add`); Test Plan item 7 (existing
`test_calamity_raid_maturity_advancement`/`test_calamity_raid_spawning` pass unchanged — run these
two existing tests as-is after this step to confirm non-regression before proceeding).

### Step 4 — Add the new unit test file
**Files:** `tests/unit/world/test_calamity_magical_demonic_reproduction.py` (new)
**Change:** Following `tests/unit/world/test_calamity_raid.py`'s state-construction style
(`AuthoritativeState(tick=..., seed=42, ...)`, `CalamityService.process_world_dynamics(state,
generator)`), add tests covering:
- Test Plan item 1: flag ON, calamity trigger conditions met (`tick - last_calamity_tick >=
  CALAMITY_MIN_INTERVAL`, `tick % CALAMITY_FORCE_INTERVAL == 0`, a region with
  `calamity_intensity > 0.3`) → a `magical_demonic_entity`-kind entity appears in
  `entities_add`.
- Test Plan item 2: the spawned entity's `identity.life_stage == LifeStage.ADULT`; explicit
  assertion that the entity was NOT built with `life_stage=LifeStage.CHILD` and that
  `lifecycle.age_ticks` is not pre-seeded near the CHILD→ADULT boundary (i.e., `age_ticks == 0`,
  the `LifecycleComponent` default — not `2970` or similar).
- Test Plan item 3: `lifecycle.parent_a_entity_id is None`, `lifecycle.parent_b_entity_id is None`,
  `lifecycle.birth_tick == state.tick`, `lifecycle.birth_city_id is None`, and the entity's
  `navigation.position` falls inside the target region's bounds (mirroring the natural-creature
  path's own resolution of the same birth_city_id ambiguity, per investigation).
- Test Plan item 5: flag OFF (default) → `process_world_dynamics(state, generator)` produces no
  `magical_demonic_entity`-kind entity; only the existing `world_boss` appears in `entities_add`
  (byte-identical to pre-ticket behavior).
- Test Plan item 6: architecture guard — no `GeneticsSystem`/`GeneticProfile` import or reference
  anywhere in `spawn_magical_demonic_entity()` or the new branch in `calamity.py` (grep-based
  source-text assertion, matching the sibling tickets' precedent).
- Flag-name-uniqueness guard: `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` is registered as its own
  distinct key in `feature_flags.py`, not aliased to `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`.
- No-population-cohorts-write guard: `StateUpdate.world_updates` contains no
  `population_cohorts_set` entry from this branch.
**Do NOT touch:** `tests/unit/world/test_calamity_raid.py`,
`tests/unit/world/test_calamity_pressure_propagator.py`,
`tests/unit/world/test_natural_creature_reproduction.py`, or
`tests/unit/progression/test_lifecycle.py` — regression-only, read-only for this ticket.
**Verify:** `pytest tests/unit/world/test_calamity_magical_demonic_reproduction.py -v` — all new
tests pass; run alongside `tests/unit/world/test_calamity_raid.py` to confirm no interference.

### Step 5 — Add the authoritative-apply-path integration test
**Files:** `tests/integration/optimization/test_component_patch_apply_parity.py`
**Change:** Append one new test following the existing round-trip pattern in that file (and
mirroring `test_natural_creature_spawn_commits_through_authoritative_apply_path` from the sibling
ticket): construct a `StateUpdate` containing a `spawn_magical_demonic_entity()`-built entity,
round-trip it through `ApplyPath.apply_generation()`, and assert all birth-record fields
(`parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`) and `life_stage ==
ADULT` survive the authoritative apply path unchanged.
**Do NOT touch:** any other existing test in this file — append only.
**Verify:** Test Plan item 4 (AC4 — spawn commits through the authoritative apply path).

### Step 6 — Update the Mechanics Bible
**Files:** `docs/mechanics/05_world_evolution.md`
**Change:** Add a new `### Magical/Demonic Reproduction
(TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH)` subsection immediately after the existing
"Natural-Creature Reproduction" subsection (after line 302, before the `---` at line 304 and the
"## 7. Cultural Drift" heading), following that subsection's exact structure
(`docs/mechanics/05_world_evolution.md:268-302`): flag name/default, trigger (citing
`CALAMITY_MIN_INTERVAL`/`CALAMITY_FORCE_INTERVAL`/the `calamity_intensity > 0.3` filter as
existing named constants, reused verbatim — not new authored numbers), parentless birth-record
population via `V2EntityBuilder.birth_record()`, and — as its own explicit bullet, per AC6 — the
"no childhood" rule: the entity spawns directly at `LifeStage.ADULT` with no CHILD→ADULT transition
or maturation clock (contrasting explicitly with the Natural-Creature subsection's short-clock
trick immediately above it), and a bullet stating no population-pressure suppression gate applies
to this path (citing Decision 1's rationale: calamity-intensity-driven, not settlement-demographic).
**Do NOT touch:** the "Natural-Creature Reproduction" subsection (lines 268-302), "Creature
Territory Lifecycle" (lines 239-267), or the "Migration Law"/"Age Bracket Thresholds" content in
§5 (lines 207-232) — this ticket does not modify the Migration Law.
**Verify:** AC6 (docs updated) — manual review; no automated test, matches the sibling ticket's own
precedent (docs changes are not test-gated).

### Step 7 — Add the parity ledger entry
**Files:** `docs/parity_ledger/world_dynamics.yaml`
**Change:** Add a new entry with `id: WORLD-121` (next available after `WORLD-120`, the last entry
in the file at line 1697), via `tools/parity_ledger_writer.py` (per CLAUDE.md's Parity-updater full-
file-rewrite-risk guidance — the sanctioned writer only, never a raw Edit to this YAML). Follow
`WORLD-120`'s citation style exactly (`docs/parity_ledger/world_dynamics.yaml:1697-1725`): `text`
describing the flag/trigger/birth-record/no-childhood/no-population-gate behavior, `status:
verified`, `priority: P2` (matching `WORLD-120`'s priority — this is a new, not-yet-P0-critical
mechanic, same tier as its sibling), `v2_evidence` citing `src/world/calamity.py` (the new branch),
`src/systems/world_systems/generator.py` (`spawn_magical_demonic_entity()`), and
`src/domains/optimization/feature_flags.py` (`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` registered
default OFF), cross-referencing `SOC-259` (birth-record schema consumed, same as `WORLD-120`) and
this ticket ID. Do **not** cross-reference `WORLD-DEMO-001` (Migration Law) — Decision 1 resolved
the population-pressure gate as inapplicable, unlike `WORLD-120`'s conditional citation of it.
`test_path`: the new Step 4 test
(`tests/unit/world/test_calamity_magical_demonic_reproduction.py::<primary spawn test name>`).
**Do NOT touch:** `WORLD-023` through `WORLD-028` (the pre-existing `P0`/`test_path: null` entries
living in the same `process_world_dynamics` function) — do not add, remove, or modify their
`status`/`test_path`/anything else. This is a **pre-existing gap**, out of this ticket's scope; do
not worsen it (e.g. by editing those entries' `text` to describe the new branch) and do not
opportunistically "fix" it either (adding a `test_path` to `WORLD-023`-`WORLD-028` is explicitly
flagged in investigation.md as not an AC of this ticket — leave them untouched). Do not touch
`WORLD-120` or any other existing entry.
**Verify:** AC6 (parity ledger entry added) — `tools/parity_ledger_writer.py`'s own schema
validation passing is the mechanical check; no separate test.

## Scope Guards

- Do not touch `spawn_monster()`'s signature or body (`generator.py:59-83`) — 7+ call sites depend
  on it unchanged.
- Do not touch the existing `world_boss` spawn branch's trigger/selection logic
  (`calamity.py:33-58`'s `should_spawn`/`high_intensity_regions`/`target_region` computation) —
  only append after it, inside the same `if` blocks.
- Do not touch `apply_calamity_consequences()` or `CalamityPressurePropagator.propagate_seasonal()`
  (`calamity.py:61-146`) — unrelated methods in the same file.
- Do not pass `life_stage=LifeStage.CHILD` or pre-seed `age_ticks` anywhere in the new spawn method
  — this is the sibling ticket's maturation-clock trick, and is the opposite of this ticket's "no
  childhood" requirement.
- Do not add any `GeneticsSystem`/`GeneticProfile` reference — out of scope per the ticket.
- Do not write `population_cohorts_set` under any circumstance.
- Do not reference `compute_regional_scarcity()`/`migration_threshold`/`PopulationCohort` anywhere
  in this ticket's new code (Decision 1: population-pressure gate does not apply to this path).
- Do not add a new `Faction` or `EntityRole` enum member — reuse `MONSTER_HORDE`/`MONSTER`
  (Decision 3); adding a new enum value is a schema change out of scope.
- Do not modify `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, `ENABLE_CREATURE_TERRITORY_LIFECYCLE`,
  or any other existing feature flag entry.
- Do not touch `WORLD-023` through `WORLD-028` (pre-existing P0/`test_path: null` gap in the same
  function) — explicitly out of scope; do not worsen it, do not opportunistically fix it either.
- Do not touch `WORLD-120` or any parity ledger entry other than the new `WORLD-121`.
- Do not touch the "Natural-Creature Reproduction" or "Creature Territory Lifecycle" subsections in
  `docs/mechanics/05_world_evolution.md`, or the Migration Law / Age Bracket Thresholds content in
  §5.
- Do not touch `CreatureTerritoryService`, `RaidService`, `SpawnService`, `BossService`,
  `DemographicCycleService`, or any other system called from `world_dynamics.py`'s macro-dynamics
  block (`world_dynamics.py:127-199`) other than adding the new in-service flag check described in
  Step 3 — the call site itself (`world_dynamics.py:133`) is not touched by this ticket.
- The natural-creature and human/humanoid reproduction paths (separate sibling tickets) are not
  touched.

## Dependency Map

- Step 1 (flag registration) is independent — no dependency.
- Step 2 (`spawn_magical_demonic_entity()`) is independent of Step 1, but Step 3 depends on Step 2
  (the branch calls the new generator method).
- Step 3 depends on Steps 1 and 2 (needs the flag key and the generator method to exist).
- Step 4 (unit tests) depends on Steps 1-3 (exercises the flag, the generator method, and the new
  branch together).
- Step 5 (integration test) depends on Step 2 (needs `spawn_magical_demonic_entity()` to build a
  test entity) but not on Step 3 (it exercises the apply path directly, not through
  `process_world_dynamics`).
- Step 6 (docs) depends on Steps 1-3 being finalized (documents their exact shape) but has no code
  dependency — can be written in parallel with Step 4/5 once Steps 1-3 are settled.
- Step 7 (parity ledger) depends on Steps 1-4 (cites the flag, generator method, branch, and the
  Step 4 test's exact name as `test_path`) and should be done last.

Suggested execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 (matches the numbering above).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — calamity/pressure event at/above existing trigger threshold produces a new magical/demonic entity | Step 3 (branch), Step 2 (spawn method) | Test Plan item 1, new file `test_calamity_magical_demonic_reproduction.py` |
| AC2 — spawned directly at ADULT life stage, no CHILD→ADULT transition or maturation clock | Step 2 (omits `life_stage=CHILD`/`age_ticks`) | Test Plan item 2, same new file |
| AC3 — birth-record fields: `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, correct `birth_city_id`/region | Step 2 (`.birth_record(...)` call) | Test Plan item 3, same new file |
| AC4 — spawn committed through the authoritative apply path, not a direct mutation | Step 3 (`StateUpdate.entities_add`), Step 5 (apply-path round-trip) | Test Plan item 4, `test_component_patch_apply_parity.py` |
| AC5 — new unit test(s) following `test_calamity_raid.py`'s pattern | Step 4 | `test_calamity_magical_demonic_reproduction.py` |
| AC6 — `05_world_evolution.md` documents the path (incl. "no childhood"); `world_dynamics.yaml` entry cites it | Step 6, Step 7 | Manual doc review; `WORLD-121` entry with `test_path` set |

## Anti-Drift Notes

- **Copy-paste hazard from the sibling method**: `spawn_natural_creature_offspring()`
  (`generator.py:85-120`) is the closest structural template for Step 2, but its
  `life_stage=LifeStage.CHILD` (line 114) and `.lifecycle(age_ticks=short_clock_age)` (line 118)
  lines must be *deleted*, not copied — leaving `.identity(...)` without a `life_stage=` kwarg at
  all (defaults to `ADULT`) and dropping the `.lifecycle(...)` call entirely (folded into
  `.birth_record(...)`'s own internal `.lifecycle(...)` call). Copy-pasting the sibling method
  body without removing these two lines is a direct AC2 violation.
- **`should_spawn` sharing is intentional, not incidental**: the new branch must reuse the exact
  `target_region` local variable already computed for the boss spawn (`calamity.py:44`), not
  recompute its own region selection — recomputing independently would risk picking a different
  region on ties and silently diverge from "following its existing intensity/trigger pattern."
- **`CALAMITY_RANDOM_CHANCE` (`calamity.py:19`) stays untouched** — a pre-existing dead constant
  unrelated to this ticket's trigger reuse; do not wire it into the new branch under the
  assumption it's part of "the existing trigger pattern" — it is declared but never read anywhere
  in `process_world_dynamics` today.
- **`birth_city_id` stays `None`** — `LifecycleComponent.birth_city_id` is `Optional[int]` while
  `RegionState.id` is `str`; there is no numeric city id available from a calamity's origin
  region. AC3's "or the calamity's origin location if no city applies" is satisfied by the
  entity's spawned `position` (`target_region.center`) falling inside the target region's bounds,
  not a stored field — identical to the natural-creature path's own resolution of this same
  ambiguity (test asserts position-in-bounds, not a `birth_city_id` value).
- **Flag check placed once, in-service** — per `CampService`'s own Anti-Drift precedent, the
  `flags = getattr(state, "feature_flags", None) or {}` line goes once near the top of
  `process_world_dynamics`, and only the new branch is wrapped in the `if flags.get(...) ==
  "ON":` check — the Maturity Advancement block and the existing boss-spawn logic remain fully
  unconditional, exactly as today.
- **`WORLD-023`-`WORLD-028`'s `test_path: null` gap**: this ticket's new Step 4 test file lives in
  the same module (`calamity.py`) these P0 entries describe, but is written to verify only the new
  branch's own behavior (AC1-AC3) — it does not, and is not required to, backfill `test_path` for
  `WORLD-023`-`WORLD-028`. Resist the temptation to "helpfully" wire the new test into one of
  those entries' `test_path` fields; that would misrepresent what the new test actually covers
  (the magical/demonic branch, not maturity advancement or the boss's legendary-stats/equipment
  behavior those entries describe).

## Unresolved Questions

None — all three open questions from investigation.md are resolved above with citations (Decisions
1-3), and neither decision requires an architecture-review escalation: both follow direct,
evidence-grounded precedent already established by the sibling `WORLD-120` ticket and the existing
unguarded `world_boss` branch this ticket sits beside.
