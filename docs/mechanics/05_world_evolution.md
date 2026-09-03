---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-09-04
---

# Chapter 5: World Evolution

This chapter describes the "Macro Laws" that govern the state of the world environment, regional safety, and the passage of time.

---

## 1. The Passage of Time
The simulation operates on a fixed-rate tick system. Every action and biological process is synced to this clock.

| Unit | Tick Count | Real-Time Approx (Simulated) |
| :--- | :--- | :--- |
| **1 Tick** | 1 | ~36 Seconds |
| **1 Hour** | 100 | 1 Hour |
| **1 Day** | 2400 | 24 Hours |

---

## 2. Regional Trauma & Hazards
Regions are not static. They react to the violence and activity within their borders through the **Trauma Score**.

### The Trauma Cycle
1.  **Event**: Every entity death in a region adds **+1.0** to the regional `Trauma Score`
    (`src/engine/world_dynamics.py:54-55`, confirmed 2026-09-02).
2.  **Threshold**: If `Trauma Score > 50.0`, the region enters an unstable state.

**Flagged, not yet resolved, 2026-09-02:** `src/engine/apply_plan.py:218` applies a separate `+2.0` trauma
increment in a context this section's death-only narrative doesn't cover. Not confirmed wrong — just
undocumented; needs its own follow-up check before this cycle description can be called complete.
3.  **Hazard Scaling**: Unstable regions gain **+0.01** `Hazard Level` per world cycle.

> For how per-entity Hazard Level drain is actually resolved against an entity standing in
> the region (including faction-based endurance to a region's hazard kind), see
> [§3 Regional Sovereignty — Hazard Impacts](#hazard-impacts) below.

---

## 3. Regional Sovereignty
Regions can be claimed and controlled by specific factions based on their active **Influence**.

### Influence Shifts

**Corrected, 2026-09-02** (Bible-chapter check following the Social/Economic axis investigations): this
section previously stated ±1.0 per death and ±100.0 ownership thresholds. Both were wrong, verified directly
against `src/world/influence.py` — not a rounding difference, a 5x/2x discrepancy in a chapter re-verified
as recently as 2026-09-01. This specific number was already independently confirmed correct elsewhere this
session (the M2 epic doc's own idea-35 depth-audit), but that finding was never folded back into this
chapter until now.

Every death in a region shifts the balance of power by `DEATH_INFLUENCE_SHIFT = 5.0`
(`src/world/influence.py:28`):
*   **Monster Death**: Increases Hero Influence by **+5.0**.
*   **Hero Death**: Decreases Hero Influence by **-5.0** (shifts towards Monster Horde).

### Ownership Thresholds
Conquest and liberation trigger at `CONQUEST_THRESHOLD = -50.0` / `LIBERATION_THRESHOLD = 50.0`
(`influence.py:29-30`), not ±100.0:
*   **Hero Controlled (Liberation)**: Influence ≥ **+50.0**.
*   **Monster Controlled (Conquest)**: Influence ≤ **-50.0**.
*   ±100.0 is only the influence value's clamp bound (`max(-100.0, min(100.0, ...))`,
    `influence.py:59`), not itself a trigger — it caps how far influence can drift past the real
    ±50.0 thresholds, it does not define a second, stricter ownership tier.

**Impact of Ownership**: Faction-owned regions may provide safe zones for allies, trigger reinforcement spawns, or apply special economic modifiers to local trade.

### Hazard Impacts
As `Hazard Level` (0.0 to 1.0) increases, entities within the region suffer:
*   **Passive HP Drain**: Health is lost every tick based on the hazard's intensity.
*   **Environmental Fatigue**: Sleep Debt increases by **+1.0** (extra exhaustion) due to extreme conditions.
*   **Suppression**: If a region is "Suppressed," entities lose **-5.0 Readiness** per tick, significantly slowing down their action frequency.

#### Native Endurance to a Region's Hazard Kind
Every region carries a `hazard_kind` tag (e.g. `"PHYSICAL"` — the default, `"NATURAL_TERRAIN"`,
`"TOXIC_GAS"`, `"UNDEAD_CORRUPTION"`, `"ARCANE_CORRUPTION"`) describing *what kind* of hazard its
passive drain represents. Separately, a faction's catalog definition may declare
`hazard_immunities` — the set of `hazard_kind` values its members endure without harm (e.g.
`wild_beast_pack` and `goblin_warband` both declare `hazard_immunities: ["NATURAL_TERRAIN"]`,
since wolves and goblins are native to their own forest habitats; `undead_remnants` declares
`hazard_immunities: ["UNDEAD_CORRUPTION"]`, since undead endure the corruption of their own
battlefield for a distinct in-fiction reason from ordinary wilderness endurance). `"TOXIC_GAS"`
remains synthetic/test-only (used only in unit tests, `tests/unit/world/test_regional_consequences.py`);
`"UNDEAD_CORRUPTION"` is an authored production value as of
TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (`data/content/world_modules/undead_battlefield.yaml`).
`"ARCANE_CORRUPTION"` is an authored production value as of
TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
(`data/content/world_modules/moon_cult_ruins.yaml`'s `moon_cave` region, matched by
`arcane_circle`'s `hazard_immunities`).

When computing Passive HP Drain for an entity, `EnvironmentService.calculate_hazard_drain`
resolves the entity's catalog faction id and checks it against the region's `hazard_kind`:
if the entity's faction endures that hazard kind, drain is **zero**; otherwise the drain
formula above applies unchanged. This endurance check is **unconditional** — it applies before
and independent of `calamity_intensity` scaling or the `MIASMA` modifier, and it does not
consult hostility relationships between factions.

This means endurance is strictly a property a faction declares for itself, never an inference
from being hostile (or not) to another faction. A hazard kind that no faction present has
declared endurance for hurts **every** faction standing in it equally — for example, if a hero
party and a wolf pack fight each other inside a `"TOXIC_GAS"` region, both sides take full,
unmitigated drain, because neither faction lists `"TOXIC_GAS"` in its `hazard_immunities`. A
faction being bucketed as hostile-to-heroes (e.g. `legacy_engine_bucket: "MONSTER_HORDE"`)
confers no hazard endurance by itself.

`RegionState.hazard_kind` defaults to `"PHYSICAL"` and `FactionDefinition.hazard_immunities`
defaults to an empty list, so this mechanism is fully opt-in per content: existing regions and
factions with neither field authored behave exactly as before (full, unmitigated drain for
every entity). Content must explicitly author both a region's `hazard_kind` and a faction's
matching `hazard_immunities` entry for the exemption to take effect.

> **Compiled-instance staleness note**: `data/worlds/sandbox_world/`'s compiled/resolved
> artifacts are generated ahead-of-time from the source catalog and do not pick up this
> mechanism's effect until they are recompiled — that recompile is the responsibility of
> `TCK-20260701-SANDBOX-MONSTER-BALANCE`, not this chapter's authoring change.
>
> `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` extended this mechanism corpus-wide: 7 modules
> (`orc_clan_territory`, `bandit_road_trade_pressure`, `old_mine_resource_loop`,
> `forest_warden_grove`, `undead_battlefield`, `nomadic_herd`, `sunken_swamp_border`) gained
> `hazard_kind` + matching native-faction `hazard_immunities`, and the 8 worlds whose compiled
> state predated these fixes (`simq_routing_test`, `dungeon_crawl`, `generated_frontier_3_42`,
> `frontier_extended`, `frontier_living_world`, `swamp_border_world`, `highland_traverse`,
> `wilderness_survival`) were recompiled to pick them up.

---

## 3. Ecology & Replenishment
The world automatically replenishes consumed resources and removes "Simulation Trash" (decay).

### Respawn Laws
*   **Resource Nodes**: Once depleted (0 charges), nodes enter a cooldown. They respawn after **100 ticks** by default.
*   **Monsters**: Replenished periodically based on the region's `Influence` and `Trauma`. High Hero influence reduces monster spawn rates.
*   **Chests**: Once looted, chests enter a long cooldown before they can be searched again.

### Decay Laws
*   **Corpses**: Entities that are killed remain in the world as `Corpse` objects for a fixed duration (`decay_tick`) before being permanently removed.
*   **Ground Items**: Items dropped on the floor also decay over time to prevent simulation clutter.

### Derived Scarcity Ratio (Consumer-Facing)
Resource nodes do not carry a separate durable "scarcity" field -- consumers derive one at read
time from `ResourceNodeState.remaining_charges / max_charges`, scoped to nodes tagged into a
region via `ResourceRegistry` definitions' `source_region_tags`. Two consumers use this ratio
today:
*   **`ResourceOpportunityProvider`** (`src/world/providers/resources.py`) uses the raw ratio
    directly as a *reward multiplier* -- opportunities on a near-depleted node are worth less
    (`reward *= 0.5 + 0.5 * depletion_mult`).
*   **`QuestGenerator`** (`src/quests/generator.py`) uses the *inverse* of the region-averaged
    ratio, `scarcity = 1.0 - avg(remaining/max)`, as a *quest-selection weight* -- a region with
    heavily depleted nodes favors `GATHER`-kind quest templates. This is a distinct derived
    signal from the trauma/hazard signals in §2 above, aggregated the same way (read-time, from
    durable per-node fields, never itself persisted).

---

## 4. Regional Transformation
Regions can physically transform their "Kind" over long periods.
*   **Stability**: High stability regions resist change. Low stability (caused by high trauma) allows for transformations.
*   **Shifting**: A `PLAIN` region might shift to a `FOREST` or `SWAMP` depending on the environmental "Pressure" and duration of trauma.

---

## 5. Demographic Cohort Cycle

Each region tracks an abstract population divided into three age brackets: `young`, `adult`, and `elder`. The demographic cycle runs every **200 ticks** (`DemographicCycleService.COHORT_INTERVAL`).

### Birth/Death Law
```
net_change = int(cohort.count * birth_rate) - int(cohort.count * mortality_rate)
new_count  = max(0, cohort.count + net_change)
```
Default rates: `birth_rate = 0.02`, `mortality_rate = 0.01` → net +1% per 200 ticks.

### Succession — Default Heir Assignment (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT)

`LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`). When an active
entity dies (`OLD_AGE` or `COMBAT`) with `heir_entity_id is None`, a default heir is selected from
the deceased's `SocialComponent.bonds` before the same-tick heirloom-transfer step runs.

**Candidate filter:** every `target_id` in `deceased.social.bonds` where `target_id != deceased.id`,
`state.entities.get(target_id)` exists, AND `target.lifecycle.active is True`. This filter is
strictly stricter than the pre-existing manual-heir-transfer path's liveness check (existence only,
not `.active`) — the manual path is unchanged by this mechanic.

**Score:**

score = 0.6 × familiarity + 0.4 × ((sentiment + 1.0) / 2.0)

- `familiarity` (native range 0.0–1.0) is weighted 0.6 — the primary signal, since how much the
  deceased actually knew/interacted with a candidate is the more direct proxy for "who they would
  leave things to" than bare positive regard.
- `sentiment` (native range −1.0–1.0) is normalized to 0.0–1.0 before weighting at 0.4 — a
  secondary signal. Negative-sentiment bonds are not excluded, only down-weighted: a hostile bond
  contributes 0.0 to this term rather than disqualifying the candidate outright.
- Combined score range: 0.0–1.0.

**Tie-break (explicit total order, no hash/dict-iteration-order dependence):** candidates are
ordered by `(-score, -last_interaction_tick, target_id)` — highest score wins; ties broken by most
recent `last_interaction_tick` (higher tick = more recent, since it is an absolute tick number, not
a delta); remaining ties broken by lowest `target_id`.

**No-candidate case:** if the candidate set is empty (zero bonds, or every bonded target is dead or
missing), no heir is assigned and no exception is raised — inventory/heirlooms remain untransferred,
identical to today's `heir_entity_id is None` behavior.

**Selection result flow:** the selected id is recorded via `LifecycleUpdate.heir_entity_id_set` on
the dying entity's own `EntityUpdate` (never a direct field mutation), applied authoritatively by
`LifecyclePatch.apply()` (`src/engine/patches.py:84`). The same selected id is used locally within
the same `resolve_lifecycle` call to drive the same-tick heirloom-transfer `ResourceTransferIntent`,
matching the pre-existing manual-heir-set + same-tick-transfer behavior.

This is unrelated to §7.2's `TRUST_BONUS_WEIGHT`/`score_trust_bonds()` in
`docs/mechanics/04_strategic_cognition.md` — that mechanic computes a trust-bonus overlay for
`PartyCompositionScorer`/`AdventureRouteGenerator` FORM_PARTY generation confidence, a
cognition-layer use case with a different base score and a different chapter; no constant or
function is shared between the two.

**Source:** `src/systems/lifecycle_systems/lifecycle.py` (`LifecycleSystem._select_default_heir`,
`LifecycleSystem.resolve_lifecycle`) (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT, 2026-08-26)

### Personal Dependents (Non-Parental) (TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS)

`LifecycleComponent.dependent_entity_ids: list[int]` (`src/core/state.py`) records the ids of
entities this entity is personally responsible for — a general, plural concept distinct from
`heir_entity_id` above (single-valued, death-only "who inherits") and distinct from the
child→parent-direction `parent_a_entity_id`/`parent_b_entity_id` fields (which record whose child
this entity is, the opposite direction).

**Write path (mirrors `heir_entity_id`'s own precedent exactly):** the field is written only via
`LifecycleUpdate.dependent_entity_ids_add: list[int]` on an entity's own `EntityUpdate` — never a
direct field mutation — merged additively across same-tick writers by `LifecycleUpdate.merge()`,
and applied authoritatively by `LifecyclePatch.apply()` (`src/engine/patches.py`), which extends
the existing list and assigns the result the same way `heirlooms` is assigned (as a `tuple`,
matching that field's own pre-existing list-typed-but-tuple-assigned pattern).

**Construction (tests/demo only):** `V2EntityBuilder.lifecycle(dependent_entity_ids=[...])`
(`src/core/builder.py`) or `V2EntityBuilder.replace_lifecycle(LifecycleComponent(
dependent_entity_ids=[...]))`. No production system establishes this relationship automatically as
of this ticket.

**Scoring effect:** see `docs/mechanics/04_strategic_cognition.md` §6.13 (Personal Dependents Route
Bias, SOC-262) for the `AdventureRouteScorer.score()` bias this field drives.

**Deferred follow-up — not implemented by this mechanic:** birth-triggered parental dependent
auto-registration (a newborn automatically becoming a parent's dependent via
`parent_a_entity_id`/`parent_b_entity_id`) is explicitly **not** built here. It is deferred to
`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`, pending that epic's birth-record schema maturing further.

**Source:** `src/core/state.py` (`LifecycleComponent.dependent_entity_ids`), `src/core/updates.py`
(`LifecycleUpdate.dependent_entity_ids_add`), `src/engine/patches.py` (`LifecyclePatch.apply()`),
`src/core/builder.py` (`V2EntityBuilder.lifecycle()`) (TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS,
2026-09-02)

### Migration Law
When `scarcity(region) > cohort.migration_threshold` (default 0.7), **30%** of that cohort (min 1) emigrates to the lowest-scarcity adjacent region. Adjacency requires a shared boundary edge with non-degenerate overlap on the other axis.

### Age Bracket Thresholds (Entity-Level)
| `age_ticks` range | Bracket | Modifier |
|---|---|---|
| < 3000 | young | none |
| 3000–6999 | adult | none |
| ≥ 7000 | elder | STR/AGI −30%, VIT/END −50%, WIS/CHA +30% |

### Population Density Demand Signal (E52D)
High-population regions amplify resource demand pressure in `RegionalPressureModel`:

```
population_density = total_cohort_count / max(1, region_area)
demand_multiplier  = 1.0 + (population_density * 0.5)
resource_pressure_intensity = min(1.0, base_intensity * demand_multiplier)
```

This closes the demographic feedback loop: population growth → density increase → resource pressure increase → scarcity increase → migration or constraint.

**Source:** `src/domains/demographics/cohort.py`, `src/domains/world_emergence/models.py`
**Contract:** `docs/world/demographics_contract.md`

### Individual-Birth Population-Pressure Nudge (idea 38, TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE)

`DemographicCycleService.process_demographics()`'s own aggregate birth/death cycle above runs only
every `COHORT_INTERVAL` (200) ticks. Between cycles, individual births produced by the Reproduction
epic's per-entity paths (§6) did not move the aggregate `population_cohorts` count at all — a region
flagged low-population by the pressure gate could stay flagged indefinitely regardless of real
per-entity births. This nudge closes that gap with a deliberately **coarse, additive-only** fix, per
the idea-38 atlas card's revision-25 decision: on a successful individual birth, the birth region's
`population_cohorts["young"].count` is incremented by exactly `+1` — **never a full resync/recount**
against actual named entities. The aggregate cohort stays a background abstraction, not a real
census; the named-entity layer and the aggregate cohort layer remain intentionally decoupled.

**Mechanism:** a new, genuinely additive field on the typed `WorldUpdate`,
`population_young_births_delta: int = 0`, distinct from `population_cohorts_set` (the existing
whole-dict-replace field used by the 200-tick cycle and by migration). `WorldUpdate.merge()` sums
`population_young_births_delta` across every `WorldUpdate` merged in a call — so two births landing
on the same region in the same tick correctly accumulate to `+2`, not a last-write-wins clobber. The
authoritative apply path (`src/engine/apply_plan.py`) resolves `population_cohorts_set` first (the
whole-dict base, whichever of a same-tick `DemographicCycleService` rebuild or the prior region
state it is), then layers the nudge's delta on top of the `young` bracket — so a same-tick collision
between the aggregate cycle's own rebuild and a reproduction path's nudge can never clobber either
signal. If the region has no `young` bracket seeded yet (a region can legitimately have
`population_cohorts == {}` — zero declared population seeds nothing, per
`TCK-20260831-POPULATION-COHORT-SEEDING`), a fresh `PopulationCohort(bracket="young",
count=<delta>)` is materialized with dataclass defaults (`birth_rate=0.02`, `mortality_rate=0.01`,
`migration_threshold=0.7`) rather than the birth's signal being silently dropped — mirroring
`src/worldbuilding/compiler.py`'s own `_seed_population_cohorts()`, whose docstring states seeded
cohorts likewise "leave birth_rate/mortality_rate at their PopulationCohort dataclass defaults."

**Participating paths:** the Natural-Creature and Humanoid reproduction paths (§6) each set the
nudge inside their own already-flag-gated branch, on every successful birth. The Magical/Demonic
path is deliberately **excluded** — see its own subsection in §6 for the confirmed rationale
(`WORLD-121`: a calamity-driven spawn is a world-threat escalation event, not a settlement/camp
demographic signal, and this path already never *reads* the population-pressure signal either).

**Source:** `src/core/updates.py` (`WorldUpdate.population_young_births_delta`),
`src/engine/apply_plan.py`, `src/world/camp.py`, `src/world/reproduction_humanoid.py`

---

## 6. Calamities & World Threats
When the global `Maturity` and regional `Trauma` scores are sufficiently high, the simulation triggers "Macro Events."
*   **Boss Spawns**: Unique, high-threat entities appear in traumatized regions.
*   **Raids**: Faction-based attacks on town centers or resource hubs.
*   **Threat Evolution**: Monsters in high-hazard regions evolve to higher `Evolution Levels`, becoming deadlier and granting better rewards.

### Creature Territory Lifecycle (TCK-20260831-CREATURE-TERRITORY-LIFECYCLE)

Behind `ENABLE_CREATURE_TERRITORY_LIFECYCLE` (default OFF), `CreatureTerritoryService`
(`src/world/creature_territory.py`) gives monster-kind entities anchored by proximity to an
existing camp (same 10x10 box check `CampService` uses to count nearby monsters) a per-entity
`territory_maturity` value that grows every world-dynamics tick.

**Per-tick delta formula:**

```
base_rate = TERRITORY_MATURITY_RATES.get(entity.kind, DEFAULT_TERRITORY_MATURITY_RATE)
trauma_multiplier = 1.5 if region.trauma_score > 50.0 else 1.0
delta = base_rate * trauma_multiplier
```

The `trauma_score > 50.0 -> x1.5` rule is not a new threshold -- it is the same regional
instability threshold defined in §2 above, reused verbatim from `CampService`'s own camp-maturity
multiplier (`src/world/camp.py`).

**Threshold-crossing spawn:** when an entity's maturity would cross
`TERRITORY_MATURITY_THRESHOLD` (100.0) on a given tick, `CreatureTerritoryService` spawns a new
territory-occupant monster of the same kind at the entity's position and resets that entity's
`territory_maturity` to 0.0 (not merely capped) for that tick. This does not use the entity-level
`LifeStage`/`age_ticks` vocabulary from §5 above -- per-species territory pacing is a distinct,
per-entity mechanic with its own typed field (`IdentityComponent.territory_maturity`).

Per-species base rates are authored, inspectable content in `TERRITORY_MATURITY_RATES`
(`src/world/creature_territory.py`), not derived from any existing table.

### Natural-Creature Reproduction (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH)

Behind `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (default OFF), `CampService.process_camps()`
(`src/world/camp.py`) gains a fourth, additive branch that spawns a parentless same-kind offspring
for a camp that has reached raid maturity, on the camp's own spawn cadence — no new maturity field,
no new spawn-trigger vocabulary.

**Trigger:** `camp.maturity >= RAID_MATURITY_THRESHOLD` (80.0) and `state.tick %
CAMP_SPAWN_INTERVAL == 0` (30) — both existing named constants already used by the garrison-spawn
and raid-trigger blocks in the same function, not new authored numbers.

**Parentless birth record:** the offspring is built via `EntityGenerator.spawn_natural_creature_offspring()`,
which calls `V2EntityBuilder.birth_record(parent_a_entity_id=None, parent_b_entity_id=None,
birth_tick=state.tick, birth_city_id=None)` — no tracked parent pair, and consequently no
`SocialBond` seeding (both parent ids `None`).

**Short CHILD→ADULT maturation clock:** the offspring is built with `life_stage=LifeStage.CHILD`
and `age_ticks = 3000 - CAMP_SPAWN_INTERVAL` (2970) pre-seeded, rather than `age_ticks=0`. The
existing, role-agnostic per-tick `age_ticks += 1` increment and `LifecycleSystem`'s forward-only
`life_stage_set` transition then carry the entity to `ADULT` after exactly one more
`CAMP_SPAWN_INTERVAL` (30 ticks) — the entity's own next spawn-cadence cycle. This explicitly does
**not** touch `LifeStageService.get_stage_for_age()`'s global 3000/7000-tick thresholds documented
in §5's "Age Bracket Thresholds" table above — those remain shared, unmodified, and apply exactly
as before to every entity in the simulation.

**Population-pressure suppression gate:** reuses §5's Migration Law verbatim — spawn is suppressed
when `compute_regional_scarcity(region.id, state)` exceeds the camp's region's `young`-bracket
`migration_threshold` (default 0.7). Because camps sit in wilderness/monster territory that is not
guaranteed to have `population_cohorts` seeded, this gate mirrors the Migration Law's own existing
skip-when-empty convention (`_check_migration`/`DemographicCycleService.process_demographics`, both
skip evaluation entirely when `region.population_cohorts` is empty): a camp in a region with no
cohort data, or no region at all, is treated as eligible (not suppressed) rather than assumed worst
case. On a successful birth, this path also nudges the birth region's `young`-bracket count by `+1`
via `WorldUpdate.population_young_births_delta` — see "Individual-Birth Population-Pressure Nudge"
below (`TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`).

### Camp/Nest Classification & Nest Spread (TCK-20260904-CAMP-NEST-CLASSIFICATION)

Behind `ENABLE_CAMP_NEST_SPREAD` (default OFF), `CampService.process_camps()` (`src/world/camp.py`)
gains a fork *inside* the existing raid-trigger gate (the same `camp.maturity >=
RAID_MATURITY_THRESHOLD` (80.0) and `state.tick - camp.last_raid_tick >= 500`-tick cooldown check
that gates the raid outcome): for camps classified as Nest kind, the raid outcome is replaced with
a spread/population-growth outcome. No new maturity field, no new spawn-trigger vocabulary, and no
independent cooldown — a Nest-classified camp cannot both raid and spread on the same qualifying
tick.

**Classification rule.** All 13 `races.yaml` races resolve to one of City / Camp / Nest / Excluded,
keyed off `natural_traits`, `drive_profile`, and `cognition_profile`:

| Race | Classification | Deciding rule |
|---|---|---|
| human, elf, dwarf, lizardfolk | City | `humanoid` + `tool_user` in `natural_traits`, `drive_profile != "opportunistic_raider"` |
| goblin, orc | Camp | `humanoid` + `tool_user` in `natural_traits`, `drive_profile == "opportunistic_raider"` |
| wolf, spider, troll, slime | Nest | `tool_user` absent from `natural_traits`, `cognition_profile == "instinctive_animal"`, `drive_profile == "territorial_predator"` |
| undead, spirit | Excluded (neither) | No City/Camp/Nest trait pair fits; population growth has no reproduction-concept fit for either race (reanimation / incorporeal guardian, not birth) — a real, named gap, no owning ticket |
| dragonkin | Excluded (Lair-adjacent) | Fails both City/Camp and Nest; its high-intelligence, solitary, place-anchored profile matches idea 47's Lair concept instead, owned by `TCK-20260904-LAIR-ENTITY-ANCHOR` |

Goblin's `social_humanoid` trait (shared with City-eligible human/elf) does **not** decide Camp-vs-
City — it is present on both City and Camp races. The real discriminator is `drive_profile ==
"opportunistic_raider"`, shared exclusively by goblin and orc among all 13 races, and already
independently corroborated by the pre-existing garrison-spawn block's `"goblin_warrior" if
camp.kind == "goblin" else "orc_warrior"` fallback (`src/world/camp.py`), which has always treated
orc as the code's de facto second Camp race.

The only code projection of this table is `CampService.NEST_RACE_KINDS = frozenset({"wolf",
"spider", "troll", "slime"})` — City and Excluded races are not represented in code because no
production path constructs a `CampState` for them (`CampState` construction remains out of scope
of this ticket; see WORLD-109 below).

**Spread outcome:** for a Nest-classified camp (`camp.kind in CampService.NEST_RACE_KINDS`) at
raid maturity, past the cooldown, with the flag ON, `CampService.process_camps()` spawns one
parentless same-kind offspring via `EntityGenerator.spawn_natural_creature_offspring(kind=camp.kind,
...)` — the same parentless-birth mechanism the Natural-Creature Reproduction path above uses —
instead of calling `RaidService.check_for_raid()`. The offspring is keyed directly off `camp.kind`
(no `goblin_warrior`/`orc_warrior`-style archetype remapping), and no new `CampState` is
constructed anywhere in this branch.

**Cost:** identical to the raid outcome it replaces — `maturity_delta=-20.0` (a relative delta, not
an absolute reset) and `last_raid_tick_set=state.tick`, reusing the same 500-tick cooldown. A
Camp-classified camp (goblin, orc) is unaffected by this flag: it always takes the raid outcome,
even with `ENABLE_CAMP_NEST_SPREAD` ON.

**New typed Camp/Nest feature fields.** `CampState`/`CampUpdate` (`src/core/state.py`,
`src/core/updates.py`) gain three typed fields — `totem_tier: int`, `stockpile: float`,
`palisade_integrity: float` — round-tripping through `to_canonical_dict()` and `CampUpdate.merge()`
and committed via `apply_plan.py`'s authoritative camp-application block, the same commit point the
existing `maturity`/`active`/`last_raid_tick` fields already go through. **These magnitudes are
provisional scaffolding only** — no production code path in this ticket populates them with a
non-default value or defines accrual/effect logic (e.g. what a totem buffs, how stockpile
accumulates); that is left to a follow-on ticket.

### Magical/Demonic Reproduction (TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH)

Behind `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` (default OFF), `CalamityService.process_world_dynamics()`
(`src/world/calamity.py`) gains a third, additive branch that spawns a parentless magical/demonic
entity in the same high-intensity region as — and on the exact same trigger evaluation as — the
existing world-boss spawn. No new maturity field, no new spawn-trigger vocabulary.

**Trigger:** identical to the existing world-boss spawn's own trigger — `state.tick -
state.last_calamity_tick >= CALAMITY_MIN_INTERVAL` (2000), `state.tick % CALAMITY_FORCE_INTERVAL ==
0` (5000), and the region filter `calamity_intensity > 0.3` — all existing named constants already
used by the boss-spawn block in the same function, not new authored numbers. The magical/demonic
entity spawns at the same `target_region.center` already selected for the boss, not a separately
computed region.

**Parentless birth record:** the entity is built via `EntityGenerator.spawn_magical_demonic_entity()`,
which calls `V2EntityBuilder.birth_record(parent_a_entity_id=None, parent_b_entity_id=None,
birth_tick=state.tick, birth_city_id=None)` — no tracked parent pair, and consequently no
`SocialBond` seeding (both parent ids `None`), identical to the Natural-Creature path above.

**No childhood:** unlike the Natural-Creature path immediately above, this entity spawns directly
at `LifeStage.ADULT` with `age_ticks=0` — no `life_stage=LifeStage.CHILD` kwarg and no pre-seeded
`age_ticks` are ever passed to the builder. `IdentityComponent.life_stage` already defaults to
`ADULT`, so this is satisfied by omission of the sibling path's maturation-clock trick, not by a
new mechanism. There is no CHILD→ADULT transition and no maturation clock for this path at all —
this is an explicit, resolved design decision (magical/demonic beings do not have a childhood), not
an open question.

**No population-pressure suppression gate:** unlike the Natural-Creature path, this branch does
**not** read `compute_regional_scarcity()`/`migration_threshold`/`PopulationCohort` at all, and does
not participate in §5's Migration Law in any way. A calamity-driven spawn is a world-threat
escalation event, not a settlement/camp demographic signal — the existing world-boss branch this
path sits beside has never had a population-pressure gate either. **This path is also deliberately
excluded from the individual-birth population-pressure nudge** (see "Individual-Birth
Population-Pressure Nudge" below) — `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`
evaluated this exclusion explicitly (confirmed, not an oversight): since this path never *reads*
the population-pressure signal either, symmetry with its own rationale above argues it should not
*write* to that signal. This path writes neither `population_cohorts_set` nor
`population_young_births_delta` under any circumstance.

### Humanoid Reproduction (TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE)

Behind `ENABLE_REPRODUCTION_HUMANOID_PATH` (default OFF), `WorldDynamicsSystem.resolve_dynamics()`
(`src/engine/world_dynamics.py`) gains a new "3.10 Humanoid Reproduction" step, nested inside the
existing `cadence.world_dynamics`-gated block on its own independent cadence — the same
nested-cadence pattern step "3.4 Boss Spawning" already established for `cadence.boss_spawn` in the
same function. Unlike the Natural-Creature and Magical/Demonic paths above, which spawn a
parentless entity from a per-camp/per-calamity anchor, this path operates on **existing entity
pairs** and is the one path in the epic that gets a genuinely new `SystemCadence` field rather than
reusing `cadence.world_dynamics` plus an inner constant.

**Cadence:** a new `SystemCadence.reproduction_humanoid` field (200 ticks, `src/engine/cadence.py`)
— a multiple of the outer `cadence.world_dynamics` gate (50) so the nested check aligns cleanly
with one out of every four `world_dynamics` passes. `should_run(state.tick, None,
cadence.reproduction_humanoid)` is checked independently of, and nested inside, the outer
`cadence.world_dynamics` check, exactly as `cadence.boss_spawn` already does for step 3.4.

**Eligibility (`HumanoidReproductionService.process_reproduction()`, `src/world/reproduction_humanoid.py`):**
one O(n) pass over `state.entities` filtered to `identity.life_stage == LifeStage.ADULT`,
`combat.alive`, and `lifecycle.active` (the same three-flag liveness convention already used
elsewhere in this file), sorted by entity id for deterministic iteration. For each unpaired
candidate, the existing indexed `SpatialQueryService.nearby_entities()` grid lookup (not a naive
all-pairs scan) finds the lowest-id unpaired candidate within `HUMANOID_PAIRING_RADIUS` (10.0 units
— the same 10-unit `nearby_entities()` radius convention already used for `_threat_resolved()`'s
interaction-radius check in `src/systems/strategic_systems/intelligence.py` and
`RoleModelSelectionPhase.RADIUS` in `src/strategy/role_model_phase.py`) whose
`EntityState.kind` matches ("same-race" — no separate `race` field exists on `IdentityComponent`)
and whose `reproduction_cooldowns` entry for the other party (if any) has already expired.

**Population-pressure suppression gate:** reuses §5's Migration Law verbatim, identically to the
Natural-Creature path above — a pairing is skipped when `compute_regional_scarcity(region.id,
state)` exceeds the birth region's `young`-bracket `migration_threshold` (default 0.7), and a
region with no `population_cohorts` seeded, or no region at all, is treated as eligible (not
suppressed), mirroring the Migration Law's own skip-when-empty convention.

**Tracked-parent birth record, not parentless:** the offspring is built via
`EntityGenerator.spawn_humanoid_offspring()`, which calls `V2EntityBuilder.birth_record()` with
real `parent_a_entity_id`/`parent_b_entity_id`, `birth_tick`, and each parent's own
`lifecycle.genetic_profile` — resolved to a concrete `GeneticProfile` via
`GeneticsSystem.generate_profile_from_seed(parent_id)` when a first-generation parent has none of
its own yet (no live spawn path today populates a parent's own `genetic_profile`), since
`birth_record()`'s internal `combine_profiles()` call only fires when at least one supplied parent
profile is non-`None` — passing both through as `None` would silently skip genetics combination for
every first-generation pairing. `parent_a_role`/`parent_b_role` are threaded through from each
parent's live `identity.role`, driving `combine_profiles()`'s existing combat-lean bias (both
`EntityRole.HERO` → combat-lean). The offspring spawns at `life_stage=LifeStage.CHILD`,
`age_ticks=0` — a real newborn, not the Natural-Creature sibling's fast-forwarded maturation-clock
trick, since this path has no analogous "must appear battle-ready soon" requirement.

**Cooldown and bond writes:** on a successful pairing, both parents receive a per-key
`LifecycleUpdate.reproduction_cooldowns_add` upsert (`REPRODUCTION_COOLDOWN_TICKS` = 400, 2x the
cadence interval, so a repeat check on the same pair stays blocked through the very next cadence
firing after the birth), and the already-shipped `build_parent_bond_updates_for_birth()` seeds each
parent's reciprocal `SocialBond` toward the child at `familiarity=0.8`/`sentiment=0.8`, applied
through the normal authoritative apply path — never a direct mutation.

**Not marriage-gated:** per the 2026-08-29 build-order decoupling of Marriage (idea 33) from
Reproduction (idea 32), this eligibility path never reads or checks any marriage-contract state
(`ContractKind.MARRIAGE`/`MarriageState`) — verified by an architecture-guard test
(`tests/unit/world/test_reproduction_humanoid_cadence.py`).

**Closes the population-pressure feedback loop:** on a successful pairing, this path also nudges
the birth region's `young`-bracket count by `+1` via `WorldUpdate.population_young_births_delta` —
see "Individual-Birth Population-Pressure Nudge" below
(`TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`).

---

## 7. Cultural Drift (E62)

Over long campaigns, regional cultures develop distinct values driven by their accumulated
narrative history. Culture drift is a **long-horizon** mechanism — it operates at episode
boundaries, not per tick.

### Axis Definitions

| Axis | Derivation source | Motivation effect |
|---|---|---|
| `fatalism` | `calamity` events + entity_death with cause="calamity" | +caution, −pride |
| `hero_veneration` | entity_death where entity_role="HERO" | +loyalty, +pride |
| `resource_scarcity_memory` | `INFLATION_SPIRAL` events | +survival |
| `faction_conflict_exposure` | `war_declared`, `territory_transferred`, `faction_destroyed` | +caution, −loyalty |

All axes are floats in [0.0, 1.0]. Normalisation: `axis = min(1.0, raw_sum / 3.0)`.
Three high-significance events saturate an axis.

### Derivation Trigger

`CultureDriftExporter.export()` is called from `CampaignOrchestrator._advance_state()`
at every episode boundary, after the narrative ledger has been updated for that episode.
It calls `ChronicleGrouper().group(narrative_ledger)` to group all accumulated entries,
then `CultureDeriver.derive(hierarchy)` to produce `Dict[str, CultureState]`.

### Persistence

`CultureState` per region is stored as `CultureCarryForward` in
`CampaignState.region_cultures: Dict[str, CultureCarryForward]`. Regions without events
in a given episode keep their prior culture snapshot unchanged until the next derivation.

### Motivation Overlay

`CulturalBiasApplicator.compute_culture_delta(culture, tags) -> float` returns an
additive delta layered onto `MotivationBiasService.compute_bias_multiplier()` result.

- Axes below `CULTURE_ACTIVATION_THRESHOLD = 0.3` produce no effect.
- Final delta is bounded: `max(-0.5, min(1.0, delta))`.
- The overlay is **transient** — it never modifies the entity's durable `MotivationModel`.

### Acceptance Signal

> In a 5-episode campaign, the `caution` tag motivation delta for a region with 3 calamity
> events exceeds that of a region with 3 hero deaths by at least 0.1.

**Sources:** `src/domains/culture/`
**Contract:** `docs/world/culture_drift_contract.md`
**Parity:** WORLD-CULT-001, WORLD-CULT-002, WORLD-CULT-003
