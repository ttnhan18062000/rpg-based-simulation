---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE
artifact_type: investigation
tags: [lifecycle, strategy]
---

# Investigation — TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Current Behavior

**`LifecycleSystem.resolve_lifecycle()`** (`src/systems/lifecycle_systems/lifecycle.py:37-164`), the
trigger site this ticket must hook into:
- Iterates every active entity (`state.entities.items()`, line 47) and computes
  `target_stage = LifeStageService.get_stage_for_age(entity.lifecycle.age_ticks)` (line 57).
- `if LifeStageService.is_forward_transition(entity.identity.life_stage, target_stage)` (line 58):
  builds/reuses `ent_upd = ent_upd or EntityUpdate(entity_id=e_id)`, then
  `ent_upd = replace(ent_upd, identity=replace(existing_identity, life_stage_set=target_stage))`
  (lines 59-61). This is the exact line pair a Coming-of-Age write must sit next to.
- Immediately after (lines 63-68), an `if target_stage == LifeStage.ELDER:` branch calls
  `compute_elder_attribute_update(...)` and merges it into `ent_upd` via `ent_upd.merge(elder_update)`
  — this is the direct structural precedent for a sibling `if target_stage == LifeStage.ADULT and
  entity.identity.life_stage == LifeStage.CHILD:` branch computing the archetype-choice roll and
  merging its own `IdentityUpdate(role_set=...)` the same way. Note the ELDER branch guards on
  `target_stage` alone (relies on `is_forward_transition` already having gated CHILD/ADULT-origin
  cases out); the new branch must additionally check the *origin* stage was CHILD (not e.g. an ELDER
  entity somehow re-classified downward, which `is_forward_transition` already forbids, but the
  explicit origin check makes the "fires exactly once, only at CHILD→ADULT" AC self-evident at the
  call site rather than relying on transitively-true invariants).
- `refined_entity_updates[e_id] = ent_upd` (line 70) is the sole place per-entity updates are
  committed into the returned `StateUpdate.entity_updates` dict — same target for the new write.
- Death/succession handling (lines 72-162) is unrelated and must not be touched.

**`LifeStageService`** (`src/ai/life_stage.py`):
- `get_stage_for_age(age_ticks)` (lines 42-56): pure boundary function, CHILD `< 3000`, ADULT
  `< 7000`, else ELDER. Numeric literals are intentionally duplicated from
  `get_age_bracket()` (`src/domains/demographics/cohort.py`, WORLD-DEMO-003) — do not import.
- `is_forward_transition(current, target)` (lines 58-66): ordinal comparison, monotonic forward-only.
  Every world-generated ADULT entity starts at `age_ticks=0` with `life_stage=ADULT` already
  (construction default, not a "just born" fact) — confirmed at `IdentityComponent.life_stage:
  LifeStage = LifeStage.ADULT` default (`src/core/state.py:517`). Only entities explicitly
  constructed with `life_stage=LifeStage.CHILD` can ever pass through the CHILD→ADULT branch.

**`OccupationChangeGoalScorer.score()`** (`src/ai/goals/occupation_change_scorer.py:32-100`) — the
convergence-risk precedent this ticket must NOT copy:
- Line 33: hard-gates on `entity.identity.role == EntityRole.CITIZEN` only.
- Lines 46-52: single pass tallying live headcount per role (`SHOPKEEPER`, `WORKER`, `GUARD`,
  `_CANDIDATE_ROLES` at line 14) within the entity's own region.
- Lines 57-66: `for role in _CANDIDATE_ROLES: ... if counts[role] < target_count and skill_ok: dest_role
  = role; break` — **fixed iteration order, first-fit, zero randomness, zero weighting**. Any
  region with an open SHOPKEEPER slot and a skill-qualified entity will *always* pick SHOPKEEPER
  before ever considering WORKER/GUARD, for every entity satisfying the same gate in the same
  region on the same tick — this is the exact zero-variance collapse the metamorphic AC exists to
  prevent, and confirms empirically why a fixed-priority-first-fit design is structurally unsound
  for this ticket's requirement.
- `target_count = max(MIN_OCCUPATION_SLOTS, int((area / 10000.0) * BASE_OCCUPATION_DENSITY[role]))`
  (lines 59-62) is the regional-need/target-count signal this ticket may read (not modify) for its
  own regional-need weight term, per the ticket's Out of Scope bullet.

**`src/world/occupation_config.py`**: `BASE_OCCUPATION_DENSITY = {SHOPKEEPER: 0.5, WORKER: 1.0,
GUARD: 0.5}`, `MIN_OCCUPATION_SLOTS = 1`. Pure config, no logic — safe, read-only reuse target.

**`PersonalityService.get_goal_modifiers()`** (`src/ai/personality.py:9-41`) — the closest existing
numeric-weighting precedent, but it modifies goal *utility* (an additive `1.0 + modifier` scale
consumed elsewhere by goal scoring), not occupation *selection*. It has no notion of combining
multiple weighted signals into a discrete categorical choice among N options — this ticket's
selection mechanism (softmax / weighted-random draw over `{SHOPKEEPER, WORKER, GUARD}`) has no
direct precedent anywhere in `src/ai/` or `src/ai/goals/`; confirmed by grep across both directories
for `random`/`softmax`/`weighted` — no hits outside RNG-domain plumbing (`src/core/rng.py`) and
world-generation spawn variance (`EntityGenerator`, unrelated domain).

**`src/core/state.py`**:
- `LifeStage(str, Enum)` (lines 438-442): `CHILD`, `ADULT`, `ELDER`.
- `IdentityComponent` (lines 499-521): `role: int = 0` (`EntityRole.HERO`), `life_stage: LifeStage =
  LifeStage.ADULT` (line 517).
- `LifecycleComponent` (lines 153-192, now spans through the birth-record fields landed by
  `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`): `age_ticks`, `max_age_ticks`, `is_permadeath`,
  `death_tick`, `death_reason`, `generation`, `heir_entity_id`, `heirlooms`,
  `parent_a_entity_id: Optional[int] = None`, `parent_b_entity_id: Optional[int] = None`,
  `dependent_entity_ids`, **`birth_tick: int = 0`** (line 166), `birth_city_id: Optional[int] = None`,
  `reproduction_cooldowns: Dict[int, int] = {}`, `active: bool = True`.

**`src/core/updates.py`**: `IdentityUpdate` (lines 224-252+) has `role_set: Optional[int] = None`
(line 226) and `life_stage_set: Optional[LifeStage] = None` (line 231) — both already exist as
first-class fields, both merged via `merge()` (lines 254+) with `other` taking precedence. No schema
change is needed on `IdentityUpdate` for this ticket; a single `IdentityUpdate(role_set=archetype)`
merged onto the same `ent_upd` that already carries `life_stage_set=target_stage` satisfies AC 1's
"exactly one `IdentityUpdate`... assigning an occupation" requirement (the merge collapses both
field-sets into one `IdentityUpdate` object on `ent_upd.identity`, which is what actually gets
written by the apply path — there is no risk of "two" `IdentityUpdate`s existing simultaneously on
one `EntityUpdate` since `EntityUpdate.identity` is a single `Optional[IdentityUpdate]` slot).

## Reproduction Epic Status (materially changed since ticket text was written)

The ticket's Request Summary and AC 4 describe the no-birth-record exclusion as "BLOCKED until the
epic's schema child ticket lands." That is now stale in a stronger way than the ticket text
anticipated: **the entire Reproduction epic is DONE**, not just the schema child ticket —
`tickets/done/` contains `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`,
`TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH`, `TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH`,
`TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE`, `TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE`,
and `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`, all under
`tickets/done/m3-reproduction-epic/`. Three live (feature-flagged) reproduction paths exist in
`src/` today:
- `src/world/camp.py:85-114` — Natural-Creature path (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`),
  calls `EntityGenerator.spawn_natural_creature_offspring(..., birth_tick=state.tick)`
  (`src/systems/world_systems/generator.py:84-118`): builds `life_stage=LifeStage.CHILD`,
  `age_ticks = 3000 - CampService.CAMP_SPAWN_INTERVAL` (a "fast-forwarded maturation clock" landing
  just below the CHILD→ADULT boundary), parentless (`parent_a_entity_id=None,
  parent_b_entity_id=None` via `.birth_record(...)`).
- `src/world/calamity.py:67-75` — Magical/Demonic path (`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`),
  calls `spawn_magical_demonic_entity(..., birth_tick=state.tick)`
  (`generator.py:122-153`): built directly at ADULT life stage (no CHILD→ADULT maturation clock at
  all) — **this path can never reach the Coming-of-Age trigger site**, parentless.
- `src/world/reproduction_humanoid.py` — Humanoid path (`ENABLE_REPRODUCTION_HUMANOID_PATH`), calls
  `spawn_humanoid_offspring(..., parent_a_id, parent_b_id, birth_tick, ...)`
  (`generator.py:157-193`): `life_stage=LifeStage.CHILD`, `age_ticks=0` (no fast-forward — "unlike
  `spawn_natural_creature_offspring()`'s fast-forwarded maturation clock, this path has no analogous
  'must appear battle-ready soon' requirement", per the docstring), **real, non-`None`
  `parent_a_entity_id`/`parent_b_entity_id`**.

Grepping the entire non-test `src/` tree for `life_stage=LifeStage.CHILD` confirms these are the
**only two call sites in the codebase** that ever construct a CHILD-life-stage entity
(`generator.py:115` and `generator.py:185`). Both call sites unconditionally chain into
`.birth_record(...)` immediately afterward. **There is currently no code path anywhere that
constructs a CHILD-life-stage entity without also populating a birth record** — the population the
AC 4 exclusion is meant to guard against (a CHILD who was never "born," e.g. a hand-placed
world-genesis construction default) does not exist in the live codebase today.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md`** does not yet cover life-stage transitions or
  occupation assignment at all (grepped the file for "life_stage"/"Coming of Age"/"archetype" — no
  hits). The closest structural precedent for where a new subsection belongs is **§8 "Marriage
  Proposal Law (idea 33, SOC-261)"** (lines 959-1017, the final section, ending the file at line
  1017) — a new **§9 "Coming of Age Archetype-Choice Roll (idea 34)"** should follow it, matching
  that section's format (Gate / Direction / Durable record / Out of scope / Source).
- **`docs/core/state.md`'s Frozen Lifecycle Law** (cited by the birth-record-schema investigation
  and by `docs/core/entities.md`): all `EntityState` mutation must flow through the frozen
  snapshot → deliberation → refinement → authoritative-transition sequence. The Coming-of-Age write
  must be expressed purely as an `IdentityUpdate.role_set` merged onto the same `EntityUpdate`
  `resolve_lifecycle()` already builds for `life_stage_set` — never a direct `replace(entity.identity,
  ...)`.
- **Determinism** (`docs/engine/kernel.md`'s 7-phase loop; CLAUDE.md "Do not break determinism"):
  since this ticket introduces the first genuinely stochastic/weighted selection in `src/ai/`
  (`OccupationChangeGoalScorer` and `PersonalityService` are both deterministic given their inputs),
  any random draw MUST go through the seeded, tick/entity-keyed RNG service (`src/core/rng.py`'s
  `Domain`-keyed `get_int`/`get_float` style calls, the same pattern
  `EntityGenerator.spawn_natural_creature_offspring()` already uses for `evolution_level` via
  `self.rng.get_int(Domain.SPAWN, tick, entity_id, ...)`) — never Python's unseeded `random` module.
  This is the single highest-risk determinism hazard in this ticket and must be flagged to the
  planner explicitly: a softmax-then-argmax (fully deterministic given weights) sidesteps this
  entirely, while a weighted-random draw does not.
- **`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md:48-52`** is the authoritative
  design-intent source: "Fires alongside M1's idea 20 (Life Stages) and needs idea 32's birth record
  to exist first... the personality/occupation/regional-need archetype-choice weighting has no
  existing numeric precedent — a free judgment call. Guard the known convergence-risk bug class...
  with a metamorphic rule: increasing the regional-need weight should push the distribution, not
  collapse its variance to zero." This is the direct source of AC 2/3's exact wording — confirms the
  ticket did not invent the metamorphic requirement independently.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: needs a new §9 "Coming of Age Archetype-Choice Roll
  (idea 34)" documenting the weighting mechanism (personality/parental-occupation/regional-need
  terms, whichever selection function the Plan phase picks) and the convergence-risk metamorphic
  guard, following §8's Gate/Direction/Durable-record/Out-of-scope/Source format — required
  verbatim by AC 6.
- `docs/parity_ledger/strategic_cognition.yaml`: needs a new entry. Current max ID in this file is
  `STRAT-266` (the Marriage durable-record entry) — the next available ID is `STRAT-267`. (The
  investigation brief's mention of "STRAT-266, STRAT-267" as existing precedent entries is
  imprecise: only STRAT-266 exists today; STRAT-267 is the ID this ticket's own new entry should
  claim, not a pre-existing entry to read.) Priority should be `P1` at minimum (not `P0` — nothing
  in this ticket's scope is a hard-conservation/determinism-critical law the way `P0` entries like
  STRAT-266 are, though the planner may judge otherwise once the RNG-vs-softmax decision is made).

The `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` roadmap doc (path:
`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`) is not required to change for this
ticket: it is a planning/roadmap document that already correctly describes idea 34's requirements
in the build-order text quoted above; this ticket fulfills that plan rather than revising it, and
no other M3 roadmap content needs correction as a result of this ticket's own scope.

The `docs/brainstorm/rpg_feature_atlas.html` idea 34 card (path:
`docs/brainstorm/rpg_feature_atlas.html`) is not required to change: per the project's own
"Sync capabilities page with atlas" convention this only applies when an atlas edit has
gameplay-visible impact requiring a companion update — this ticket implements what the existing
idea 34 card already describes rather than changing the card's own content. If the Plan phase's
final weighting-formula choice diverges materially from the card's description, the implementer
should re-check this exclusion at that time.

## Parity Ledger Overlap

- No existing `docs/parity_ledger/*.yaml` entry documents CHILD→ADULT occupation/archetype
  assignment (grepped `strategic_cognition.yaml`, `social_narrative.yaml`, `progression.yaml` for
  "archetype"/"coming.of.age"/"CHILD.*ADULT" — no hits). This ticket requires a **new** entry, not a
  status change to an existing one.
- `STRAT-266` (`docs/parity_ledger/strategic_cognition.yaml:3920-3945`, `status: verified`,
  `priority: P0`) — the Marriage durable-record entry — is the most recent addition to this file and
  the format template for the new entry, but has no functional overlap with this ticket's scope
  (Marriage vs. Coming of Age are explicitly independent per the M3 roadmap's idea 33/34 split).
- `SOC-259` (`docs/parity_ledger/social_narrative.yaml`, from
  `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`) documents the birth-record schema fields this
  ticket reads (`birth_tick`, `parent_a_entity_id`, `parent_b_entity_id`) but does not need a status
  change — this ticket only reads those fields, it does not modify their write path.
- No `P0` entry is directly touched by this ticket's own Related Code Areas (the ELDER-branch
  precedent in `resolve_lifecycle()` and `compute_elder_attribute_update` are read as a structural
  pattern, not modified) — so there is no pre-existing `P0` `test_path` gate this ticket must keep
  green beyond ordinary regression coverage.

## Prior Work

- `TCK-20260824-LIFE-STAGE-TRANSITIONS` (DONE) — landed the exact CHILD→ADULT/ADULT→ELDER trigger
  site and `LifeStageService`; its own investigation.md documents the "ADULT-by-default construction
  bookkeeping" design decision this ticket's origin-stage check must respect.
- `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (DONE) — landed `OccupationChangeGoalScorer`, the
  convergence-risk precedent this ticket must explicitly diverge from (see Current Behavior above).
- `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` and its five sibling Reproduction-epic tickets
  (all DONE, see "Reproduction Epic Status" above) — provide the birth-record fields this ticket's
  AC 4 exclusion reads, and the two live CHILD-spawning code paths analyzed above.
- `TCK-20260831-ROLE-MODEL-IMITATION` (`docs/mechanics/04_strategic_cognition.md` §4 "Role-Model
  Watching & Imitation Fidelity") — a different mechanism (adult-to-adult behavioral imitation, not
  occupation assignment) but worth the planner's awareness as an adjacent "parental influence on
  entity behavior" precedent that already exists in this same doc chapter; not scope-overlapping.
- No prior ticket has ever implemented a weighted/stochastic categorical selection over `EntityRole`
  candidates — confirmed by the `PersonalityService`/`OccupationChangeGoalScorer` review above. This
  is a genuinely novel mechanism in this codebase, not a variant of an existing one.

## Risks and Open Questions

- **DEFINITIVE FINDING on the birth-record sentinel question (the ticket's explicit re-examine
  ask):** `birth_tick == 0` alone is **not** a safe, unambiguous "no birth record" signal in
  general — it is architecturally possible for a *genuine*, tracked-parent Humanoid-path birth to
  carry `birth_tick == 0`. Evidence: `HumanoidReproductionService.process_reproduction()`
  (`src/world/reproduction_humanoid.py`) is gated only by
  `should_run(state.tick, None, cadence.reproduction_humanoid)` (`src/engine/cadence.py:39-53`,
  `reproduction_humanoid: int = Field(200, ge=1)`), and `should_run(0, None, 200)` evaluates
  `0 % 200 == 0 → True` — **no explicit `tick > 0` guard exists on this path**, unlike the other two
  reproduction paths (see below). Reproduction cooldowns default to an empty dict
  (`LifecycleComponent.reproduction_cooldowns: Dict[int, int] = {}`), so the cooldown check
  (`a.lifecycle.reproduction_cooldowns.get(b_id, 0) > state.tick`) is trivially `0 > 0 == False` at
  genesis and blocks nothing. If two same-`kind` ADULT/alive/active entities exist within
  `HUMANOID_PAIRING_RADIUS = 10.0` of each other at world genesis (plausible — not a contrived edge
  case — for any town/settlement seeded with multiple CITIZENs in proximity) and regional scarcity
  is below threshold, a real child with **non-`None` `parent_a_entity_id`/`parent_b_entity_id`** and
  `birth_tick == 0` is produced. By contrast, the other two paths are provably excluded from tick 0:
  the Natural-Creature path requires `camp.maturity >= RAID_MATURITY_THRESHOLD (80.0)`, and
  `CampState.maturity` defaults to `0.0` with no world-genesis construction site found anywhere in
  `src/` (grepped `CampState(` — no direct instantiation outside the frozen-dataclass definition and
  type-only references), so it cannot reach 80.0 at tick 0; the Magical/Demonic path's
  `should_spawn` requires `state.tick % CALAMITY_FORCE_INTERVAL == 0 and state.tick > 0` (explicit
  guard, `src/world/calamity.py:35`) **and** `state.tick - state.last_calamity_tick >=
  CALAMITY_MIN_INTERVAL (2000)`, both independently false at tick 0.
  **Resolution recommended to the Plan phase:** a safe, currently-testable exclusion check is the
  **compound** condition `lifecycle.birth_tick == 0 AND lifecycle.parent_a_entity_id is None AND
  lifecycle.parent_b_entity_id is None` (all three at their construction defaults simultaneously) —
  this correctly recognizes a tick-0 Humanoid birth as "has a birth record" (its parent ids are
  non-`None`), and is proven safe against the other two paths by the accumulation-gate evidence
  above (neither can produce a parentless, `birth_tick == 0` entity in practice). It is *not*
  provably safe against a hypothetical future reproduction path with neither an accumulation gate
  nor tracked parent ids — flag this as a forward-compatibility caveat in the new doc section, not
  as a currently-live gap.
  **Practically, however**: since every CHILD-life-stage entity in the current codebase already goes
  through `.birth_record(...)` (see "Reproduction Epic Status" above — no other CHILD-construction
  path exists), this exclusion currently has **zero real population to act on** — it cannot actually
  exclude anything today. The ticket's own AC 4 ("track as BLOCKED... do not silently omit") is
  satisfiable either by implementing the compound check above (forward-looking correctness, costs
  nothing since no current entity would be wrongly excluded) or by explicitly stubbing it with a
  comment citing this investigation's finding that no current population requires it — the Plan
  phase should pick one and document the choice; do not silently pick the simpler
  `birth_tick == 0`-only check without the compound guard, since that check alone IS provably unsafe
  per the evidence above.
- **RNG determinism for the weighted selection is unresolved and high-risk** — see Mechanics/Engine
  Constraints above. The Plan phase must pick a concrete mechanism (softmax+argmax deterministic
  given weights, vs. a seeded weighted-random draw via `src/core/rng.py`) before implementation; do
  not default to Python's `random` module.
- **The exact weighting formula (softmax vs. weighted-random, and the personality/parental/regional
  coefficient shapes) has zero precedent** — explicitly flagged as an open Plan-phase design decision
  by the ticket itself; this investigation confirms no hidden precedent was missed.
- **Parental occupation signal availability**: for the Natural-Creature and Magical/Demonic paths
  (parentless), there is no parental occupation to weight by at all — the Plan phase must define a
  fallback (e.g. neutral/zero parental term) for parentless CHILD entities rather than assuming
  `parent_a_entity_id`/`parent_b_entity_id` are always resolvable to a live entity with a `role`.
  Even for the Humanoid path, a parent may have died or deactivated (`lifecycle.active == False`)
  by the time the child reaches adulthood ~3000-7000 ticks later — `state.entities.get(parent_id)`
  can legitimately return `None` or an inactive entity; the scorer must handle this without raising.

## Anti-Drift Hazards

- **Do not modify `OccupationChangeGoalScorer`'s own selection logic, `_CANDIDATE_ROLES` tuple, or
  `BASE_OCCUPATION_DENSITY`/`MIN_OCCUPATION_SLOTS`** — explicit Out of Scope. Read-only reuse of the
  regional target-count formula is fine; changing the scorer's own fixed-priority behavior is not.
- **Do not implement the weighted selection as a `GoalScorer`/`GoalKind`** — Coming of Age is a
  direct, deterministic-trigger write inside `LifecycleSystem.resolve_lifecycle()` at the same
  phase/tick as the `life_stage_set` write, not a goal-hierarchy candidate evaluated in
  `StrategicIntelligenceSystem.evaluate_strategic_intent()`. Introducing a new `GoalKind` would be
  scope creep into the goal-hierarchy system this ticket does not touch.
- **Do not let the roll fire more than once per entity** — since `resolve_lifecycle()` runs every
  tick for every active entity, the origin-stage check (`entity.identity.life_stage ==
  LifeStage.CHILD`, read from the *pre-tick* frozen state, not from `ent_upd`) is what guarantees
  "exactly once": once the durable `life_stage_set` write lands and the entity's *next* frozen
  snapshot shows `life_stage == ADULT`, the same branch's origin check will no longer match. Do not
  gate on `target_stage == ADULT` alone (that would also match every future tick after the
  transition already happened, since `get_stage_for_age` is a pure re-derivation, not a one-shot
  event) — `is_forward_transition` already prevents a same-tick re-fire, but an implementer must not
  accidentally weaken or bypass that check while adding the new branch.
- **Do not use Python's unseeded `random` module** — see Mechanics/Engine Constraints above; this is
  the single most likely determinism regression this ticket could introduce.
- **Do not implement the no-birth-record exclusion as `birth_tick == 0` alone** — proven unsafe
  above; use the compound check or an explicitly-documented stub, not the single-field shortcut.
- **Do not widen scope into the long-run corpus population-pressure convergence property (idea 38)**
  — explicit Out of Scope; the metamorphic test here is a bounded single-tick synthetic batch only.
- **`test_life_stage_transition_is_monotonic_forward_only`** (`tests/unit/progression/
  test_lifecycle.py:339-372`) currently only asserts `entity_updates[2].identity.life_stage_set`;
  after this ticket, the same `child_at_3000` fixture will *also* trigger a Coming-of-Age roll and
  populate `role_set` — the test will still pass unmodified (it does not assert `role_set is None`),
  but the implementer/test-writer should be aware this existing test's fixture now exercises the new
  code path incidentally, and a new dedicated test should assert the `role_set` behavior explicitly
  rather than relying on this test's silence about it.
