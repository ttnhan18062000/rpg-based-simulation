---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
artifact_type: investigation
tags: [lifecycle, world]
---

# Investigation — TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH

## Current Behavior

**`CampService.process_camps()`** (`src/world/camp.py:21-84`) — runs unconditionally every tick from
`WorldDynamicsSystem.resolve_dynamics()` (`src/engine/world_dynamics.py:166-168`, not behind any
`FeatureMode` flag, unlike the sibling `CreatureTerritoryService`). Per active camp:
- `MATURITY_PER_TICK = 0.05` (camp.py:17), x1.5 if `region.trauma_score > 50.0` (camp.py:39-40) —
  the exact multiplier reused by `CreatureTerritoryService` (see below).
- Every `CAMP_SPAWN_INTERVAL = 30` ticks (camp.py:19,45), if nearby monster count (10x10 proximity
  box around `camp.position`, filtered on `EntityRole.MONSTER` + `combat.alive`) is below
  `cap = max(2, int(camp.maturity / 10.0))`, spawns one monster via
  `generator.spawn_monster(camp.position, state=state, kind=..., difficulty_tier=...)`
  (camp.py:53-61).
- At `RAID_MATURITY_THRESHOLD = 80.0` (camp.py:18,64), with `state.tick - camp.last_raid_tick >=
  500`, triggers a raid and applies `maturity_delta=-20.0` (camp.py:78-82).
- `entities_add` from spawned monsters is folded straight into
  `update.replace(entities_add=... + camp_state_update.entities_add)` at
  `world_dynamics.py:177` — a new spawn added inside `process_camps()` requires **no additional
  wiring change** to flow through to the authoritative apply path, unlike a new sibling service
  (see `CreatureTerritoryService`'s `is_noop()`-gated `.merge()` pattern at
  `world_dynamics.py:193-199`, needed only for a *separate* call site).

**`EntityGenerator.spawn_monster()`** (`src/systems/world_systems/generator.py:59-83`) builds a
fully-formed, already-frozen `EntityState` via `V2EntityBuilder` chaining `.kind()`, `.location()`,
`.identity(role=MONSTER, faction=MONSTER_HORDE, evolution_level=...)`, `.navigation()`, `.combat()`,
`.inventory()`. It never calls `.lifecycle(...)`, `.birth_record(...)`, or passes `life_stage=` —
every camp-spawned monster today gets `LifecycleComponent` defaults (`age_ticks=0`,
`max_age_ticks=10000`, `parent_a_entity_id=None`, `birth_tick=0`, ...) and `IdentityComponent`'s
default `life_stage=LifeStage.ADULT` (`src/core/state.py:512`). There is currently no
generator/builder call path that spawns a monster already in `LifeStage.CHILD`, and `spawn_monster()`
has no keyword for birth-record fields or `life_stage`.

**`DemographicCycleService`/`compute_regional_scarcity()`** (`src/domains/demographics/cohort.py`):
- `compute_regional_scarcity(region_id, state)` (cohort.py:153-180) — pure function, returns `1.0 -
  mean(remaining/max_charges)` across resource nodes whose position falls inside the region's
  bounds; returns `1.0` if the region has no nodes or doesn't exist. Takes only `region_id`/`state`,
  no per-cohort argument.
- `migration_threshold` (cohort.py:35-43) is a field on `PopulationCohort`, **per bracket, per
  region** (`young`/`adult`/`elder` each carry their own instance), defaulting to `0.7`. It is not a
  single per-region scalar — `region.population_cohorts` is a `Dict[str, PopulationCohort]` keyed
  by bracket. `_check_migration()` (cohort.py:223-321) reads `cohort.migration_threshold` per
  bracket when deciding emigration, comparing against the single region-wide `scarcity` value.
- Camps are not guaranteed to sit in a region that has `population_cohorts` seeded at all (camps
  are typically wilderness/monster territory, not settled population centers) — this ticket's
  eligibility gate must decide what to compare against when `region.population_cohorts` is empty
  (see Risks and Open Questions).

**`src/core/builder.py`** — `V2EntityBuilder.lifecycle()` (builder.py:575-617) and
`.birth_record()` (builder.py:619-651) are exactly as `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`
shipped them (confirmed by direct read, matches its plan.md verbatim): `.birth_record(parent_a_entity_id=None,
parent_b_entity_id=None, birth_tick=0, birth_city_id=None, seed_familiarity=0.8, seed_sentiment=0.8)`
populates `LifecycleComponent.parent_a_entity_id`/`parent_b_entity_id`/`birth_tick`/`birth_city_id`
via `.lifecycle(...)` and seeds no `SocialBond`s when both parent ids are `None` (the `bonds` dict
stays empty, `.social(bonds=...)` is skipped entirely — builder.py:640-650). This is exactly the
parentless-spawn shape this ticket needs: call `.birth_record(birth_tick=state.tick,
birth_city_id=...)` with parent ids left at their `None` defaults.
`.identity(life_stage=Optional[LifeStage])` (builder.py:165-215) already accepts a `life_stage`
kwarg, usable to seed a new entity directly into `LifeStage.CHILD`.

**Aging / life-stage transition mechanism (critical constraint for the "short maturation clock" AC)**:
- `src/engine/apply.py:84-110` — every tick, for every entity with `lifecycle.active` (or when
  `is_life_due`), `age_ticks` is incremented by exactly 1. This is **unconditional on role/kind** —
  monsters age exactly like heroes/villagers.
- `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py:53-70`) calls
  `LifeStageService.get_stage_for_age(entity.lifecycle.age_ticks)` for **every** active entity
  (again, no role/kind filter) and applies a forward-only `life_stage_set` transition.
  `LifeStageService.get_stage_for_age()` (`src/ai/life_stage.py:41-56`) uses fixed, global
  thresholds: `age_ticks < 3000 -> CHILD`, `< 7000 -> ADULT`, else `ELDER`. These thresholds are
  **not parameterized by species/kind** anywhere in the codebase — they are the same 3000/7000
  ticks used for hero/villager entities, intentionally duplicated (not imported) from
  `get_age_bracket()` in `cohort.py` per `TCK-20260824-LIFE-STAGE-TRANSITIONS`'s Design Decision 1.
- **Consequence**: there is no existing per-species/short-clock mechanism. A natural-creature
  entity built with `life_stage=CHILD` and `age_ticks=0` would take the same 3000 ticks to reach
  ADULT as a human — not "short." The only reuse-only path to a genuinely short clock is
  pre-seeding `age_ticks` close to (but below) the 3000-tick boundary at spawn time (e.g.
  `age_ticks=3000-N` for a small `N`), so the existing global aging/transition machinery carries
  the new entity to ADULT after only `N` ticks without touching `LifeStageService`'s global
  thresholds. This is a design decision, not something the codebase already answers — see Risks and
  Open Questions.

**`src/world/creature_territory.py`** (`CreatureTerritoryService`, closest sibling precedent,
`TCK-20260831-CREATURE-TERRITORY-LIFECYCLE`) — a **parallel, not shared**, service mirroring
`CampService`'s trauma-multiplier shape for a per-entity `IdentityComponent.territory_maturity`
field. Confirms the project's established pattern of "mirror the shape, do not refactor the
original" for this exact kind of reuse. Also the source of a critical prior-bug lesson: its
Test-phase fix discovered a **4th silent-drop point** — `ApplyPath._fast_replace_identity`
(`src/engine/apply.py`) hand-builds a component via `object.__new__` + per-field
`object.__setattr__`, bypassing `dataclasses.replace()`, and had to be patched separately from the
three standard wiring points (`*Update.is_noop()`, `*Update.merge()`, `*Patch.apply()`'s `replace()`
kwargs) after a new field was added to `IdentityComponent`. `LifecycleComponent`'s birth-record
fields were added by the just-landed schema ticket and (per its own Implementation Notes) wired
through the three standard points and verified via a full `apply_generation()` round-trip test —
but this ticket does not add any *new* field, so the 4th silent-drop-point risk does not apply here
directly; it is cited only as an anti-drift precedent (see below) in case the "short clock" design
choice at Plan time ends up requiring a new field.

## Mechanics / Engine Constraints

- **`docs/mechanics/05_world_evolution.md` §2** (Regional Trauma & Hazards) — the `trauma_score >
  50.0 -> x1.5` maturity-multiplier law this ticket's spawn trigger reuses via `CampService`.
- **`docs/mechanics/05_world_evolution.md` §5** (Demographic Cohort Cycle) — "Migration Law": `When
  scarcity(region) > cohort.migration_threshold (default 0.7)`. This is the exact law the ticket's
  eligibility-suppression gate reuses (`compute_regional_scarcity()` + `migration_threshold`), but
  the doc's own wording ("cohort.migration_threshold") confirms this is a per-cohort field, not a
  region-wide scalar — reinforcing the open question above about which cohort/bracket a
  camp-anchored, non-population-cohort-tracked spawn should compare against.
- **`docs/mechanics/05_world_evolution.md` §5** "Age Bracket Thresholds (Entity-Level)" — documents
  the exact 3000/7000 `age_ticks` boundaries `LifeStageService` implements; any new spawn path must
  respect these as given, not invent a parallel/conflicting threshold system for the same
  `life_stage`/`age_ticks` vocabulary (the `CreatureTerritoryService` precedent explicitly chose a
  *separate* vocabulary — `territory_maturity`, not `life_stage`/`age_ticks` — specifically to avoid
  this collision; see §6 subsection: "This does not use the entity-level LifeStage/age_ticks
  vocabulary from §5 above").
- **CLAUDE.md Durable State Rule / Authoritative Mutation Pipeline Contract** — the spawn must be
  committed via `entities_add` in a typed `StateUpdate` (as `CampService`/`CreatureTerritoryService`
  already do), and the camp-maturity accrual/spawn decision must be pure decision logic reading
  `AuthoritativeState`, never a direct mutation.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: AC explicitly requires this ("`docs/mechanics/05_world_evolution.md` documents this reproduction path"). Add a new subsection alongside §6's existing "Creature Territory Lifecycle" subsection documenting the natural-creature reproduction trigger, its maturity/spawn constants, the parentless birth-record population, and the scarcity-based suppression gate.
- `docs/parity_ledger/world_dynamics.yaml`: AC explicitly requires a new entry citing this path (next available id in the `WORLD-1xx` series is `WORLD-120`, confirmed — current max is `WORLD-119`; `WORLD-DEMO-*` is a separate id namespace already at `WORLD-DEMO-006`).

The `docs/world/raid_boss_camp_contract.md` doc (path: `docs/world/raid_boss_camp_contract.md`,
under `docs/`) is not added here as a required-bullet target because it was not listed in the
ticket's own "Related Docs," but flag it for Plan's attention: it directly documents `camp.py`'s
"Monster spawning" behavior with specific numeric formulas (`monster_cap = max(2,
int(camp.maturity/10))`, "Spawn runs every 50 ticks" — note this figure is already stale relative
to the actual `CAMP_SPAWN_INTERVAL = 30` in code, a pre-existing drift unrelated to this ticket). If
the natural-creature spawn branch is implemented as a new code path inside `CampService` alongside
the existing garrison-spawn logic, a reader of this contract doc would reasonably expect the new
behavior to appear there too — Plan should decide whether to fold a short note in or leave it to a
future doc-hygiene pass, since it is not one of this ticket's AC-mandated docs.

The `docs/world/demographics_contract.md` doc (cited as source/contract for §5's demographic
material) was not read in full during this investigation and is not added as a required bullet — it
documents the cohort/migration model this ticket only *reads from* (`compute_regional_scarcity`,
`migration_threshold`) without changing that model's own behavior (population-pressure feedback
closure is explicitly out of scope, deferred to
`TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`), so no change to that contract is expected.

## Parity Ledger Overlap

- `WORLD-118` (`status: verified`, `priority: P2`) — `CreatureTerritoryService.process_territories()`'s
  trauma-multiplier maturity accrual. Same multiplier shape this ticket reuses via `CampService`
  directly (not via `CreatureTerritoryService`); no change needed to this entry.
- `WORLD-119` (`status: verified`, `priority: P2`) — `CreatureTerritoryService`'s threshold-crossing
  same-kind spawn + exact-reset-to-zero. Closest structural precedent for "spawn on maturity
  crossing," but a different maturity field (`IdentityComponent.territory_maturity`, not
  `CampState.maturity`) and a different trigger owner (per-entity, not per-camp). No change needed.
- `WORLD-DEMO-001` (`status: verified`, `priority: P1`) — the exact migration-pressure/scarcity law
  (`compute_regional_scarcity`, `migration_threshold` default 0.7) this ticket's eligibility gate
  reuses. Not modified by this ticket (no P0 entries touched, so no `test_path` re-verification is
  mandatory), but this ticket's new parity entry should cross-reference `WORLD-DEMO-001` in its
  `v2_evidence`/text since it reuses that exact law rather than reimplementing scarcity.
- `SOC-259` (`docs/parity_ledger/social_narrative.yaml`, `status: verified`, `priority: P2`) — the
  just-shipped birth-record schema entry (`LifecycleComponent`/`LifecycleUpdate`/`LifecyclePatch`/
  `V2EntityBuilder.birth_record`). This ticket's new entities call into that shipped surface;
  no change to `SOC-259` itself is needed since the schema is being consumed, not altered.
- No `P0` entries are touched by this ticket's scope (`WORLD-DEMO-001`, `WORLD-118`, `WORLD-119` are
  all `P1`/`P2`), so no pre-existing `test_path` requires re-verification as a hard gate — but
  `compute_regional_scarcity()`/`migration_threshold` regression tests (`tests/unit/world/
  test_demographics.py`) should still be run since this ticket is a new consumer of that function.

## Prior Work

- `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` (done) — hard dependency, already landed. Shipped
  exactly the API this ticket must call: `V2EntityBuilder.birth_record(parent_a_entity_id=None,
  parent_b_entity_id=None, birth_tick=int, birth_city_id=Optional[int])`. Confirmed via direct read
  of `src/core/builder.py` that the shipped signature matches the plan verbatim, and that leaving
  both parent ids `None` produces no `SocialBond` seeding (safe no-op path for this ticket's
  parentless case).
- `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE` (done) — closest sibling precedent for "reuse
  CampService's trauma-multiplier maturity shape for a same-kind threshold-crossing spawn." Key
  transferable lessons: (1) mirror the shape as a parallel implementation, don't refactor the
  original service; (2) independently verify no hidden live consumer of the field/state being
  extended before extending it; (3) the `ApplyPath._fast_replace_identity` 4th-silent-drop-point bug
  — a real, previously-hit failure mode when a component gains a new field and the fast-path
  reconstruction helper in `src/engine/apply.py` isn't updated to carry it through. This ticket adds
  **no new field** (it only calls the already-wired birth-record fields and, if the "short
  maturation clock" is implemented via pre-seeded `age_ticks`, uses only pre-existing fields), so
  this specific bug class should not recur here — but Plan/Implement should re-verify this
  assumption explicitly if the maturation-clock design ends up requiring any new durable field.
- `docs/parity_ledger/world_dynamics.yaml:WORLD-DEMO-001` / `tests/unit/world/test_demographics.py`
  — existing, passing regression coverage for the scarcity/migration-threshold law this ticket's
  eligibility gate reuses verbatim.

## Risks and Open Questions

1. **"Short CHILD->ADULT maturation clock" has no existing implementation path.** `LifeStageService`'s
   3000/7000-tick thresholds are global and unparameterized by species/kind (see Current Behavior).
   The only way to achieve a genuinely *short* clock while fully reusing the existing
   age_ticks-driven transition machinery is to pre-seed the new entity's `age_ticks` near (just
   below) the 3000 boundary at spawn time, rather than starting at 0. This is a real design decision
   for Plan, not something already answered by the codebase — flag rather than assume. Alternatives
   Plan should weigh: (a) pre-seeded `age_ticks` (zero new fields, fully reuses existing global
   aging/transition path, but the "clock length" is implicit/derived rather than an authored
   constant); (b) skip `LifeStage.CHILD` entirely and spawn straight into `ADULT` like every existing
   camp/territory spawn does today (simplest, but arguably fails the AC's literal "with a short
   CHILD->ADULT maturation clock" requirement); (c) a genuinely new species-scoped maturation field/
   mechanism (most work, introduces a new durable field with the associated silent-drop-point risk
   noted above).
2. **Which `migration_threshold` to compare against when a camp's region has no seeded
   `population_cohorts`.** `migration_threshold` lives per-bracket on `PopulationCohort`
   (`young`/`adult`/`elder`), not as a single region-wide scalar; camps are not guaranteed to sit in
   a region with any cohorts seeded (they're wilderness/monster territory). The ticket's own AC text
   parenthetically says "(0.7 default)," suggesting the literal default constant may be an acceptable
   fallback when no cohort exists, but Plan must decide explicitly (e.g., read
   `region.population_cohorts[<some bracket>].migration_threshold` if present, else fall back to the
   `PopulationCohort` dataclass default of `0.7`) rather than leaving this implicit.
3. **Whether to ship behind a `FeatureMode` flag.** The sibling `CreatureTerritoryService` ticket's
   own Scope explicitly required "Ships behind a FeatureMode flag, default OFF"; this ticket's Scope
   has no equivalent line, and the service it's extending (`CampService.process_camps()`) itself runs
   unconditionally with no flag today. Plan should make an explicit call rather than defaulting
   either way silently, since this changes camp-anchored world population growth behavior in every
   existing/future scenario the moment it lands if unflagged.
4. **Whether the new spawn logic lives inside `CampService.process_camps()` itself or as a new
   sibling method/service.** Implementing inside `process_camps()` gets automatic `entities_add`
   wiring for free (`world_dynamics.py:177` already folds `camp_state_update.entities_add`) with no
   `world_dynamics.py` changes needed; a new sibling service would need its own `is_noop()`-gated
   `.merge()` call site (matching `CreatureTerritoryService`'s pattern at `world_dynamics.py:193-199`).
   This is a real implementation choice with different wiring-change surface area — Plan's call.
5. **Genetics-involvement boundary** — ticket's own "Assumptions/Open Questions" flags this as
   likely "no" but unconfirmed. Investigation confirms: `GeneticsSystem`/`GeneticProfile` were not
   found referenced anywhere in `src/core/builder.py`'s birth-record path, `src/world/camp.py`, or
   `src/domains/demographics/cohort.py` — no code-level entanglement exists today, consistent with
   "no genetics wiring needed," but this investigation did not read the `GeneticsSystem`/
   `GeneticProfile` module itself (out of this ticket's Related Code Areas) to positively confirm the
   boundary; Plan should treat this as reasonably likely but not code-verified.

## Anti-Drift Hazards

- **Do not modify `LifeStageService.get_stage_for_age()`'s global 3000/7000 thresholds** to create a
  "short" clock for natural creatures — that function is shared by every entity in the simulation
  (heroes, villagers, monsters alike) and any change ripples into human/villager aging.
- **Do not modify `CreatureTerritoryService`** — it is a separate, already-shipped mechanic
  (`territory_maturity`, threshold=100.0) with its own parity entries (`WORLD-118`/`WORLD-119`) and
  its own `FeatureMode` flag; this ticket's spawn trigger is anchored to `CampState.maturity`
  (`RAID_MATURITY_THRESHOLD`-style camp constants per the ticket's own Scope), a structurally
  different maturity signal, not a re-use of `territory_maturity`.
- **Do not touch `RaidService`'s raid-trigger branch** inside `CampService.process_camps()`
  (`camp.py:63-83`) — this ticket's spawn hook is additive alongside the existing "2. Camp-based
  Spawning" block, not a modification of "3. Raid Trigger."
- **Do not add a `GeneticsSystem`/`GeneticProfile` dependency** — explicitly out of scope per the
  ticket; the parentless path calls `.birth_record()` with both parent ids `None`, which produces no
  bonds and requires no genetics inputs.
- **Do not implement the population-pressure feedback loop** (nudging `population_cohorts` on a
  successful birth) — explicitly deferred to `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`;
  this ticket only *reads* `compute_regional_scarcity()`/`migration_threshold` as a gate, it must not
  write back to `population_cohorts`.
- **Do not silently drop the new spawn's birth-record fields on a fast-path apply.** Per the
  `CreatureTerritoryService` precedent's 4th-silent-drop-point bug in `ApplyPath._fast_replace_identity`:
  a newly-spawned entity built via `V2EntityBuilder` and appended to `entities_add` is a fresh
  construction (not a mutation-via-fast-path), so this specific bug class shouldn't apply directly —
  but if the maturation-clock design ends up needing an `EntityUpdate` write to an *already-existing*
  entity's `LifecycleComponent`/`IdentityComponent` at any point, re-check all silent-drop points
  (`is_noop()`, `merge()`, `Patch.apply()`'s `replace()` kwargs, and any `_fast_replace_*` helper in
  `src/engine/apply.py`) rather than assuming the birth-record schema ticket's wiring alone covers it.
- **Do not hardcode `0.7`** as the migration threshold instead of reading `PopulationCohort.migration_threshold`
  when a real cohort exists for the camp's region — the ticket text's "(0.7 default)" describes the
  dataclass default, not a license to bypass an authored per-region override.
