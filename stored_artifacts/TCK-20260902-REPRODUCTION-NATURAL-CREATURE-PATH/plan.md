---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
artifact_type: plan
tags: [lifecycle, world]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH

## Summary

Add a flag-gated, additive fourth branch to `CampService.process_camps()` (`src/world/camp.py`)
that spawns a parentless same-kind offspring once a camp's maturity reaches the existing
`RAID_MATURITY_THRESHOLD` (80.0), on the existing `CAMP_SPAWN_INTERVAL` (30-tick) cadence, gated
by a population-pressure eligibility check reusing `compute_regional_scarcity()` verbatim. The
offspring is built via a new `EntityGenerator.spawn_natural_creature_offspring()` method that
calls the already-shipped `V2EntityBuilder.birth_record(parent_a_entity_id=None,
parent_b_entity_id=None, ...)` and seeds `age_ticks` just below the global 3000-tick CHILD→ADULT
boundary so the entity ages into ADULT after one spawn-interval's worth of ticks, using only the
existing global aging pipeline — no new field, no new maturation subsystem, no change to
`LifeStageService`. The whole new branch ships behind a brand-new `FeatureMode` flag,
`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, default OFF, following the exact DEV-002
default-OFF/in-service-flag-check pattern already used for `ENABLE_CREATURE_TERRITORY_LIFECYCLE`
and `ENABLE_GUILD_QUEST_GENERATION`. Nothing about the existing garrison-spawn (section 2) or
raid-trigger (section 3) blocks in `process_camps()` changes.

## Three Design Decisions (resolved, not deferred)

### Decision 1 — Short maturation clock: pre-seeded `age_ticks`, no new field

`LifeStageService.get_stage_for_age()` (`src/ai/life_stage.py:41-56`) uses fixed global thresholds
(`age_ticks < 3000 -> CHILD`, `< 7000 -> ADULT`) with **no per-species override anywhere in the
codebase** — confirmed by direct read; the function's own docstring (life_stage.py:44-51) states
the 3000/7000 literals are intentionally duplicated from `get_age_bracket()`
(`src/domains/demographics/cohort.py`) and must not diverge. Modifying these thresholds would
change every entity in the simulation (heroes, villagers, monsters alike) — explicitly an
anti-drift hazard.

**Decision:** spawn the offspring with `age_ticks = 3000 - CampService.CAMP_SPAWN_INTERVAL` (i.e.
`2970`), not `age_ticks=0`. The existing unconditional per-tick `age_ticks += 1` increment
(`src/engine/apply.py:84-110`, applies to every `lifecycle.active` entity regardless of role) and
`LifecycleSystem.resolve_lifecycle()`'s forward-only `life_stage_set` transition
(`src/systems/lifecycle_systems/lifecycle.py:53-70`, also role-agnostic) then carry the entity to
ADULT after exactly `CAMP_SPAWN_INTERVAL` (30) ticks — one spawn-cadence cycle — with **zero new
fields, zero new machinery, zero touches to `LifeStageService`**. The "clock length" is derived
from an existing named constant (`CAMP_SPAWN_INTERVAL`), not an arbitrary new number, directly
satisfying the ticket AC's "verifiable against `CampService`'s existing maturity/spawn constants."
This is investigation's own Option (a); Options (b) (skip CHILD entirely) and (c) (new
species-scoped field) are rejected — (b) fails the AC's literal "short CHILD→ADULT maturation
clock" text, (c) is unnecessary new-field scope creep.

### Decision 2 — Population-pressure gate on cohort-less (wilderness) regions: explicit skip branch

Read directly: `compute_regional_scarcity(region_id, state)` (`src/domains/demographics/cohort.py:153-180`)
returns `1.0` (maximum scarcity) both when `state.regions.get(region_id)` is `None`
(cohort.py:163-165) and when the region has zero resource nodes within its bounds
(cohort.py:178-179, `count == 0`). This is a real, non-raising "safe default" — but it is **not**
semantically "no pressure": comparing it against the `0.7` default `migration_threshold` would mean
a camp sitting in a wilderness region with no resource nodes tracked (the norm — camps are
wilderness/monster territory per the ticket's own scope) is suppressed **forever**, defeating the
feature entirely.

The existing Migration Law itself already has a documented convention for exactly this situation:
both call sites that read `region.population_cohorts` skip evaluation entirely when it is empty
(`_check_migration`, cohort.py:242-243: `if not region.population_cohorts: return {}, []`; and
`DemographicCycleService.process_demographics`, cohort.py:358-359: `if not region.population_cohorts:
continue`) — i.e. "no cohort data" reads as "no pressure signal to evaluate," not "assume worst
case."

**Decision:** mirror that convention explicitly.
- If `LegalityServiceV2.get_region_for_position(camp.position, state)` (already called at
  camp.py:37-38 for the trauma-multiplier check, reused not re-computed) returns `None`, treat the
  camp as eligible (no data → don't suppress) — this also matches camp.py's own existing handling
  of a `None` region for the trauma multiplier (`if region and region.trauma_score > 50.0`,
  camp.py:39), which already treats a missing region as "skip the modifier," not an error.
- If `region.population_cohorts` (`Dict[str, PopulationCohort]`, per-bracket, cohort.py:35-43) is
  empty, treat the camp as eligible — mirrors the two existing skip-when-empty call sites above.
- Only when `region.population_cohorts` is non-empty: read `migration_threshold` from the `"young"`
  bracket if present (spawn/birth semantically maps to the "young" bracket used elsewhere for
  age-0 population, cohort.py:28), else fall back to the `PopulationCohort` dataclass default
  `0.7` (cohort.py:43 — a fallback for an unusual populated-but-no-"young"-bracket region, not a
  hardcode bypassing an authored value per the anti-drift hazard). Compare against
  `compute_regional_scarcity(region.id, state)` (called fresh, not reused, since it must reflect
  the current tick's resource-node state) — suppress spawn when `scarcity > threshold`.

This ticket only **reads** `compute_regional_scarcity()`/`population_cohorts`/`migration_threshold`;
it never constructs a `WorldUpdate` with `population_cohorts_set` (that write path stays
exclusively `DemographicCycleService.process_demographics()`, cohort.py:337-370, and
`_check_migration`, cohort.py:223-321 — see Step 3's writer enumeration below).

### Decision 3 — Ship behind a new flag, `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, default OFF

`docs/brainstorm/rpg_feature_atlas.html`'s Implementation Patterns table (line 854) classifies
**idea 32 (Reproduction)** under "Content and logic both, flag-gated," explicitly naming
Reproduction as one of "several of these... entire new subsystems, not incremental changes,
belong behind a flag through at least one full staged rollout." `src/domains/optimization/feature_flags.py`
confirms the live convention: every brand-new-mechanic entry added since DEV-002 defaults `OFF`
with a comment citing "no corpus profile turns this on and no SHADOW-validation history exists"
(e.g. `ENABLE_CREATURE_TERRITORY_LIFECYCLE`, feature_flags.py:116-120; `ENABLE_HABIT_BIAS_ACTION_STYLE`,
:121-127; `ENABLE_ITEM_INSTANCE_HISTORY`, :128-134; `ENABLE_ROLE_MODEL_IMITATION`, :135-140) — and
critically, **each is its own per-ticket flag**, never a shared flag reused wholesale across
sibling tickets, even when siblings share a parent idea/epic.

**Decision:** introduce `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, default `FeatureMode.OFF`, as
this ticket's own flag — following the established per-mechanic (not per-idea) granularity, so a
regression found in this path's staged rollout doesn't force the magical/demonic or
human/humanoid paths off too, and vice versa (each path is architecturally distinct: different
spawn triggers, different component writes, different risk profiles). Sibling tickets
(`TCK-20260902-REPRODUCTION-...-PATH`, once filed) should follow the **same naming convention** —
`ENABLE_REPRODUCTION_<PATH>` — for their own independent flags, not literally reuse this flag
name. Checked inside `process_camps()` via `flags = getattr(state, "feature_flags", None) or {}`
then `flags.get("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "OFF") == "ON"` — this exact
in-service-check idiom (as opposed to gating at the `world_dynamics.py` call site) is itself an
established precedent, not novel: `GuildNeedScorer` (`src/ai/goals/scorers.py:253`) uses the
identical `flags = getattr(state, "feature_flags", None) or {}` pattern to gate logic from inside
a service rather than at its caller. `AuthoritativeState.feature_flags: Dict[str, Any]` (confirmed
at `src/core/state.py:1220`) is the field read.

## Steps

### Step 1 — Register the new feature flag

**Files:** `src/domains/optimization/feature_flags.py`

**Change:** Add `"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": FeatureMode.OFF,` to
`FeatureFlagManager.__init__`'s `self._flags` dict (alongside the other DEV-002-policy entries,
e.g. after `ENABLE_ROLE_MODEL_IMITATION` at feature_flags.py:140), with a comment matching the
established style: cites this ticket ID, states it is a brand-new gameplay mechanic (new spawn
branch inside `CampService.process_camps()`), and that DEV-002's default-OFF policy applies (no
corpus profile turns this on, no SHADOW-validation history exists yet). No other flags in this
file are touched.

**Do NOT touch:** any other flag's default value or comment; do not reorder existing entries.

**Verify:** `python3 -c "from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode; m = FeatureFlagManager(); assert m.get_flag_mode('ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH') == FeatureMode.OFF"` (sanity check, not a formal pytest — covered implicitly by Step 5's new tests constructing `state.feature_flags` overrides).

### Step 2 — Add `EntityGenerator.spawn_natural_creature_offspring()`

**Files:** `src/systems/world_systems/generator.py`

**Change:** Add a new method (do not modify `spawn_monster()`, which has 7 other call sites —
`src/world/camp.py:55`, `src/world/spawn.py:113`, `src/world/creature_territory.py:60`,
`src/certification/scenarios.py:81`, `src/world/boss.py:110`, `src/world/calamity.py:47`,
`src/world/raid.py:54`, plus `tests/integration/world/test_phase9_stability.py:28` — confirmed via
grep, changing its signature or defaults risks all of them):

```python
def spawn_natural_creature_offspring(
    self, pos: tuple[float, float], state: AuthoritativeState | None = None,
    kind: str = "monster", difficulty_tier: int = 1, birth_tick: int = 0,
) -> EntityState:
    """Spawn a parentless same-kind offspring already aged near the CHILD->ADULT
    boundary (see plan.md Decision 1) with birth-record fields populated via the
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
    from src.core.state import LifeStage
    from src.world.camp import CampService
    short_clock_age = 3000 - CampService.CAMP_SPAWN_INTERVAL
    return (V2EntityBuilder(entity_id)
        .kind(kind)
        .location(*pos)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE,
                   evolution_level=evolution_level, life_stage=LifeStage.CHILD)
        .navigation(home_position=pos, leash_radius=10.0)
        .combat(hp=int(base_hp), max_hp=int(base_hp), atk=int(base_atk), def_stat=int(base_def), readiness=100.0)
        .inventory(gold=int(base_gold))
        .lifecycle(age_ticks=short_clock_age)
        .birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick, birth_city_id=None)
        .build())
```

Mirrors `spawn_monster()`'s existing structure verbatim (generator.py:59-83) for stat/level
scaling — the only differences are `identity(..., life_stage=LifeStage.CHILD)` (builder.py:183,205
confirms `.identity()` already accepts this kwarg), `.lifecycle(age_ticks=...)` (builder.py:579
confirms `.lifecycle()` already accepts `age_ticks`), and `.birth_record(...)` (builder.py:619-651,
the exact API `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` shipped — confirmed by direct read,
parent ids `None` produces no `SocialBond` seeding per builder.py:640-650's `if bonds:` guard).
`birth_city_id` stays `None`: `LifecycleComponent.birth_city_id` is typed `Optional[int]`
(`src/core/state.py:165`) while `RegionState.id` is `str` (`state.py:257`) — there is no numeric
city id for a wilderness camp's region, so `None` is correct, not a gap (matches the parent ids'
own `None` for the same "not applicable" reason). The AC's "correct... region" is satisfied by the
spawned entity's `position` falling inside the camp's region bounds (same position-based
verification style `test_camp_maturity_and_spawn` already uses for `goblin.position == (50, 50)`),
not a stored field.

**Do NOT touch:** `spawn_monster()`, `spawn_hero()`, `spawn_goblin()`, or any other existing
`EntityGenerator` method's signature or body.

**Verify:** `test_natural_creature_offspring_has_no_tracked_parents`,
`test_natural_creature_offspring_short_maturation_clock` (Step 5).

### Step 3 — Wire the flag-gated spawn branch into `CampService.process_camps()`

**Files:** `src/world/camp.py`

**Change:** Inside the existing per-camp `for c_id, camp in state.camps.items()` loop
(camp.py:30-83), after the existing "3. Raid Trigger" block (camp.py:63-83) and before the
function's final `return`, add a new "4. Natural-Creature Reproduction" block, gated as follows.
Read `flags = getattr(state, "feature_flags", None) or {}` once, before the loop starts (mirrors
the exact idiom at `src/ai/goals/scorers.py:253` and `src/engine/world_dynamics.py:193`). Inside
the loop, for each active camp:

```python
if flags.get("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "OFF") == "ON":
    if (camp.maturity >= CampService.RAID_MATURITY_THRESHOLD
            and state.tick % CampService.CAMP_SPAWN_INTERVAL == 0):
        eligible = True
        if region is not None and region.population_cohorts:
            young = region.population_cohorts.get("young")
            threshold = young.migration_threshold if young is not None else 0.7
            from src.domains.demographics.cohort import compute_regional_scarcity
            scarcity = compute_regional_scarcity(region.id, state)
            eligible = scarcity <= threshold
        if eligible:
            offspring = generator.spawn_natural_creature_offspring(
                camp.position, state=state,
                kind="goblin_warrior" if camp.kind == "goblin" else "orc_warrior",
                difficulty_tier=int(camp.maturity / 20.0) + 1,
                birth_tick=state.tick,
            )
            entities_add.append(offspring)
```

`region` here is the same variable already computed once per camp at camp.py:38
(`region = LegalityServiceV2.get_region_for_position(camp.position, state)`) for the trauma
multiplier — reused, not recomputed, matching the "no additional wiring change" advantage noted in
investigation.md. The trigger reuses `RAID_MATURITY_THRESHOLD` (80.0) and `CAMP_SPAWN_INTERVAL`
(30) verbatim — both already-existing named constants, no new authored magic number — per Decision
1's own AC-alignment reasoning; the `kind=` mapping is copied verbatim from the existing garrison
spawn at camp.py:58 for consistency ("same-kind entity").

`entities_add` in this function is folded straight into `update.replace(entities_add=... +
camp_state_update.entities_add)` at `world_dynamics.py:177`, unconditionally, exactly like the
existing garrison-spawn/raid entities — **no `world_dynamics.py` change is needed** for this new
entity to reach the authoritative apply path.

**Other writers to `state.camps`/`process_camps()`'s own output (`StateUpdate.camp_updates`,
`entities_add`) that this step must not collide with:** none inside this function are touched —
the existing "1. Maturity Evolution" (camp.py:30-42), "2. Camp-based Spawning" (camp.py:44-61),
and "3. Raid Trigger" (camp.py:63-83) blocks are left byte-for-byte unmodified; the new block is
purely additive after them. `CampService.resolve_camp_clearing()` (camp.py:86-108) is a separate
entry point (invoked on explicit camp-clearing, not per-tick) and is untouched. No other service in
the codebase writes to `CampState` or calls `process_camps()`.

**Other writers to `region.population_cohorts` this step's eligibility check reads (read-only,
never write) that could interact:** `DemographicCycleService.process_demographics()`
(cohort.py:337-370, runs every `COHORT_INTERVAL=200` ticks, writes `population_cohorts_set` via
`WorldUpdate`) and `_check_migration()` (cohort.py:223-321, called from the same demographic cycle,
also writes `population_cohorts_set`) both execute in the same `resolve_dynamics()` tick
(`world_dynamics.py`, "3.7 Demographic Birth/Death Cycle") as `CampService.process_camps()`
("3.6 Process Camps," called one step earlier at world_dynamics.py:167-168, before "3.7" at
world_dynamics.py:171). Because `process_camps()` runs first in that ordering and reads
`state.regions[...].population_cohorts` from the **pre-tick** `AuthoritativeState` (not the
in-flight `StateUpdate` being built by 3.7), this step's scarcity read always sees the prior tick's
committed cohort counts — consistent with how every other reader in `resolve_dynamics()` (e.g. the
trauma-multiplier check) reads pre-tick state, and never a source of a race since `StateUpdate`s
from different phases are only reconciled at authoritative apply time, not read back mid-tick by
sibling phases. This step never constructs a `population_cohorts_set` itself, so it cannot
collide with either writer's own write.

**Do NOT touch:** the garrison-spawn block (camp.py:44-61), the raid-trigger block (camp.py:63-83),
`resolve_camp_clearing()` (camp.py:86-108), or `RaidService` (`src/world/raid.py`).

**Verify:** `test_camp_maturity_threshold_spawns_natural_creature_offspring`,
`test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`,
`test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold`,
`test_camp_maturity_and_spawn`/`test_camp_raid_trigger` (existing, must keep passing byte-for-byte
— flag defaults OFF so this step must not change their outcome at all).

### Step 4 — Add architecture-guard tests

**Files:** `tests/unit/world/test_natural_creature_reproduction.py` (new file, following
`test_camp_lifecycle.py`'s fixture style — direct `AuthoritativeState`/`RegionState`/`CampState`
construction, `EntityGenerator(seed=42)`, calling `CampService.process_camps(state, generator)`
directly, passing `feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"}` on the
`AuthoritativeState` construction per `state.py:1220`'s `Dict[str, Any]` typing, string values
matching `FeatureFlagManager.serialize()`'s `Dict[str, str]` output shape)

**Change:** Add all 7 tests from `test_plan.md`'s "New Tests Required" section:
1. `test_camp_maturity_threshold_spawns_natural_creature_offspring`
2. `test_natural_creature_offspring_has_no_tracked_parents`
3. `test_natural_creature_offspring_short_maturation_clock` — exercises the real transition path:
   construct state at `age_ticks=2970`, run `LecycleSystem`/apply through 30 more ticks (or
   directly call `LifeStageService.get_stage_for_age(3000)` after simulating the increment) to
   confirm `LifeStage.ADULT` is reached, and confirm it is *not* reached at `age_ticks=2999`.
4. `test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold` —
   region with seeded `population_cohorts={"young": PopulationCohort(bracket="young", migration_threshold=0.7)}`
   and resource nodes constructed so `compute_regional_scarcity()` > 0.7.
5. `test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold` — same
   region/cohort shape, resource nodes constructed so scarcity <= 0.7. Also add a third case (not
   separately named in test_plan.md but required by Decision 2 above): a camp in a region with
   **no** `population_cohorts` seeded at all — assert spawn proceeds (not suppressed), proving the
   explicit skip branch.
6. `test_natural_creature_reproduction_does_not_write_population_cohorts` — asserts
   `StateUpdate.world_updates` contains no `population_cohorts_set` entry.
7. `test_natural_creature_reproduction_does_not_reference_genetics` — asserts no
   `GeneticsSystem`/`GeneticProfile` import/call in the new code path (behavioral-form guard,
   matching the birth-record-schema ticket's no-marriage-precondition guard precedent).

Also add the integration round-trip test to
`tests/integration/optimization/test_component_patch_apply_parity.py`:
8. `test_natural_creature_spawn_commits_through_authoritative_apply_path` — full
   `ApplyPath.apply_generation()` round-trip of the new entity, confirming birth-record fields
   survive (mirrors that file's existing round-trip pattern and the birth-record schema ticket's
   own `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`).

**Do NOT touch:** any existing test in `test_camp_lifecycle.py`, `test_creature_territory_lifecycle.py`,
`test_demographics.py`, `test_lifecycle.py`, `test_spawn_cadence.py`, or the existing tests already
in `test_component_patch_apply_parity.py`.

**Verify:** all 8 new tests pass; the full regression surface from `test_plan.md`'s Scoped Pytest
Commands passes unchanged.

### Step 5 — Update `docs/mechanics/05_world_evolution.md`

**Files:** `docs/mechanics/05_world_evolution.md`

**Change:** Add a new subsection under `## 6. Calamities & World Threats`, immediately after the
existing `### Creature Territory Lifecycle (TCK-20260831-CREATURE-TERRITORY-LIFECYCLE)` subsection
(currently ending at line 266, before the `---` at line 268), titled `### Natural-Creature
Reproduction (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH)`. Document: the flag
(`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, default OFF), the trigger (`maturity >=
RAID_MATURITY_THRESHOLD` and `tick % CAMP_SPAWN_INTERVAL == 0`, reusing existing constants — cite
Decision 1's reasoning), the parentless birth-record population (`parent_a_entity_id=None`,
`parent_b_entity_id=None`, `birth_city_id=None`), the short maturation clock mechanism
(`age_ticks=3000-CAMP_SPAWN_INTERVAL` pre-seed, reusing the existing global `LifeStageService`
thresholds unchanged — explicitly note this does NOT touch the §5 "Age Bracket Thresholds"
table), and the population-pressure suppression gate (cite the §5 "Migration Law" it reuses
verbatim, and the explicit no-cohort-data skip branch from Decision 2).

**Do NOT touch:** the existing `### Creature Territory Lifecycle` subsection's content, `## 5.
Demographic Cohort Cycle`'s existing text (Migration Law, Age Bracket Thresholds tables), or any
other section.

**Verify:** manual doc read-through; no automated test (docs are prose, per repo convention).

### Step 6 — Add `docs/parity_ledger/world_dynamics.yaml` entry `WORLD-120`

**Files:** `docs/parity_ledger/world_dynamics.yaml`

**Change:** Append a new entry with `id: WORLD-120` (confirmed next available — highest existing
`WORLD-1xx` id is `WORLD-119` at world_dynamics.yaml:1650; `WORLD-DEMO-*` is a separate namespace
already at `WORLD-DEMO-006`), `status: verified`, `priority: P2`, `text` describing the
parentless-spawn/short-clock/scarcity-gate behavior, `v2_evidence` citing `src/world/camp.py`
(new branch), `src/systems/world_systems/generator.py` (`spawn_natural_creature_offspring`),
`src/domains/optimization/feature_flags.py:<new line>` (flag registration, DEV-002 default-OFF),
and cross-referencing `WORLD-DEMO-001` (the scarcity/migration-threshold law reused, not
reimplemented) and `SOC-259` (the birth-record schema this ticket consumes) — matching the
`WORLD-119` entry's citation style. `test_path` pointing at the new
`tests/unit/world/test_natural_creature_reproduction.py` tests plus the new integration round-trip
test. Use `python3 tools/parity_ledger_writer.py` (the sanctioned schema-validating writer) rather
than a raw YAML edit, per the project's parity-ledger-safety convention.

**Do NOT touch:** `WORLD-118`, `WORLD-119`, `WORLD-DEMO-001`, `WORLD-DEMO-006`, or `SOC-259` —
cross-referenced only, not modified.

**Verify:** parity ledger schema validation (`tools/parity_ledger_writer.py`'s own validation, or
`docs/parity_ledger/schema.json`); `test_path` tests from Step 4 pass.

## Scope Guards

- Do not modify `LifeStageService.get_stage_for_age()`'s global 3000/7000-tick thresholds.
- Do not modify `CreatureTerritoryService` (`src/world/creature_territory.py`), its
  `territory_maturity` field, or its `WORLD-118`/`WORLD-119` parity entries.
- Do not modify the raid-trigger block (`camp.py:63-83`) or `RaidService`
  (`src/world/raid.py`).
- Do not modify `spawn_monster()`, `spawn_hero()`, `spawn_goblin()`, or any other existing
  `EntityGenerator` method.
- Do not add any `GeneticsSystem`/`GeneticProfile` import or dependency — out of scope per the
  ticket; enforced by `test_natural_creature_reproduction_does_not_reference_genetics`.
- Do not write `population_cohorts_set` anywhere in this ticket's new code — the population-pressure
  feedback-loop closure is `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`'s scope, not
  this ticket's; enforced by `test_natural_creature_reproduction_does_not_write_population_cohorts`.
- Do not hardcode `0.7` when a real per-region `PopulationCohort.migration_threshold` exists —
  only use the `0.7` dataclass default as the documented fallback (Decision 2).
- Do not add any new content-catalog entries (new creature `kind` strings, new item recipes, etc.)
  — this ticket reuses the existing `"goblin_warrior"`/`"orc_warrior"` kind strings verbatim.
- Do not change `world_dynamics.py`'s "3.6 Process Camps" call site or its `update.replace(...)`
  wiring at world_dynamics.py:177 — the new entity flows through automatically.
- Do not touch any other `FeatureMode` flag's default value in `feature_flags.py`.

## Dependency Map

- Step 1 (flag registration) — independent, no dependencies.
- Step 2 (`spawn_natural_creature_offspring()`) — independent of Step 1; does not itself read the
  flag.
- Step 3 (camp.py wiring) — depends on Step 1 (needs the flag name to check) and Step 2 (needs the
  generator method to call).
- Step 4 (tests) — depends on Steps 1-3 (exercises the full wired path).
- Step 5 (mechanics doc) — depends on Step 3 (must describe the actual shipped behavior, not a
  planned one).
- Step 6 (parity ledger) — depends on Step 3 and Step 4 (`v2_evidence`/`test_path` must cite real,
  passing code/tests).

Steps 1 and 2 may be implemented in either order or in parallel; all subsequent steps are strictly
sequential.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Camp at/above maturity threshold produces new same-kind entity with short CHILD→ADULT clock | Steps 2, 3 | `test_camp_maturity_threshold_spawns_natural_creature_offspring`, `test_natural_creature_offspring_short_maturation_clock` |
| Birth-record fields populated: `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, correct `birth_city_id`/region | Step 2 | `test_natural_creature_offspring_has_no_tracked_parents` |
| Spawn eligibility suppressed when scarcity exceeds `migration_threshold`; both allowed and suppressed cases tested | Step 3 (eligibility gate) | `test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`, `test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold` |
| Spawn committed via authoritative apply path (`EntityUpdate`/`StateUpdate`), not direct mutation | Steps 2, 3 (existing `entities_add`/`StateUpdate` pattern, no new wiring) | `test_natural_creature_spawn_commits_through_authoritative_apply_path` |
| New unit test(s) following `test_camp_lifecycle.py` pattern | Step 4 | all 8 new tests |
| `05_world_evolution.md` documents this path; `world_dynamics.yaml` entry cites it | Steps 5, 6 | manual doc read-through; parity schema validation |

## Anti-Drift Notes

- **4th silent-drop-point precedent** (`ApplyPath._fast_replace_identity`,
  `src/engine/apply.py`): this ticket adds **no new field** to any component — `spawn_natural_creature_offspring()`
  is a fresh `EntityState` construction appended to `entities_add`, never a mutation-via-fast-path
  of an existing entity. The bug class from `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE` should not
  recur here, but if implementation discovers any need to write an `EntityUpdate` against an
  *already-existing* entity's `LifecycleComponent`/`IdentityComponent`, re-check all four silent-drop
  points (`is_noop()`, `merge()`, `Patch.apply()`'s `replace()` kwargs, and any `_fast_replace_*`
  helper) before assuming the birth-record schema ticket's wiring alone covers it.
- **Trauma-multiplier `region` reuse**: the eligibility gate in Step 3 deliberately reuses the
  `region` variable already computed once per camp at camp.py:38, rather than calling
  `LegalityServiceV2.get_region_for_position()` a second time — avoid introducing a duplicate,
  possibly-divergent lookup.
- **`compute_regional_scarcity()` must be called fresh** (not cached/reused from the trauma check),
  since it depends on `state.resource_nodes`, an entirely different piece of state from
  `region.trauma_score`.
- **Flag-check placement**: the flag is checked once per camp, inside the loop, wrapping only the
  new block — do not hoist it above the entire `process_camps()` function in a way that would also
  gate the existing garrison-spawn or raid-trigger blocks (those must remain unconditional, exactly
  as they are today).
- **Genetics boundary**: investigation confirmed no `GeneticsSystem`/`GeneticProfile` reference in
  `src/core/builder.py`'s birth-record path, `src/world/camp.py`, or
  `src/domains/demographics/cohort.py` — this plan introduces none either. Do not add any.

## Deviations

None. All 6 steps were implemented exactly as specified, including the exact code shapes given in
Steps 2 and 3. Test file expanded from the plan's minimum (7 unit tests) to 9 — the extra
no-population-cohorts-eligible case was already called out explicitly in Step 4's own text as
required-but-not-separately-named, and a flag-off regression guard was added for completeness;
neither changes any Step's scope or the Scope Guards.
