---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
artifact_type: investigation
tags: [lifecycle]
---

# Investigation — TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE

## Current Behavior

**`src/systems/lifecycle_systems/genetics.py`** (full file read, 132 lines):
- `SkillType` (`:14-19`) — `PHYSICAL`/`MAGICAL`/`ELEMENTAL`/`HYBRID` enum, unrelated to inheritance (LEG-RPG-145, skill scaling only).
- `GeneticProfile` (`:22-33`) — frozen, `slots=True` dataclass, six fields: `strength_mult`, `agility_mult`,
  `intelligence_mult`, `wisdom_mult`, `constitution_mult`, `charisma_mult`, each `float = 1.0` (neutral
  default).
- `GeneticsSystem.apply_genetic_profile(base_stats, profile)` (`:53-75`) — static method, takes a
  `Dict[str, int]` of base stats and a `GeneticProfile`, returns `Dict[str, float]` effective stats via
  `base_value * mult` per attribute. The `profile` is a **transient parameter** — never read from or written
  to any durable entity field.
- `GeneticsSystem.generate_profile_from_seed(seed: int) -> GeneticProfile` (`:77-97`) — static method,
  MD5-hashes the seed string, extracts 6 two-byte hex offsets, maps each to `0.8 + (val/255.0)*0.5` (range
  0.8–1.3), rounds to 3 decimals. Deterministic: identical seed → identical profile (verified by
  `test_deterministic_profile_from_seed`).
- `SkillScalingSystem.compute_skill_power()` (`:105-131`) — unrelated skill-power formula consumer, not in
  this ticket's scope.

**`src/systems/genetics.py`** — pure 2-line re-export shim (`from src.systems.lifecycle_systems.genetics
import GeneticsSystem, SkillScalingSystem, GeneticProfile, SkillDefinition, SkillType`).

**Confirmed zero real callers** (`graphify query "GeneticsSystem GeneticProfile inheritance"`, cross-checked
by direct grep): the only nodes that reference `GeneticsSystem`/`GeneticProfile` outside their own defining
module are `tests/unit/progression/test_genetics.py` (11 tests, all exercising the two static methods
directly) and the shim. No non-test, non-shim call site exists anywhere in `src/`.

**No durable storage exists for a `GeneticProfile` anywhere on `EntityState`.** Grepped
`src/core/state.py`, `src/core/updates.py`, `src/engine/patches.py` for `genetic`/`GeneticProfile` — zero
hits. `EntityState`'s components (`IdentityComponent`, `AttributeComponent`, `LifecycleComponent`, etc.,
`src/core/state.py:462-760`) have no field of type `GeneticProfile` or equivalent multiplier bundle.
`EntityUpdate` (`src/core/updates.py:661-696`) likewise has no `genetic_profile`/`genetics` field. This means
`apply_genetic_profile()` is only ever callable with a profile the caller holds in a local variable — there
is no way today for a spawned entity to "own" a `GeneticProfile` across ticks. See Risks below — this is a
gap this ticket must close, not a pre-existing pattern it can just plug into.

**`V2EntityBuilder.birth_record()`** (`src/core/builder.py:619-...`, shipped by
TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) — the real, live, non-test caller pattern this ticket should
follow. Signature: `birth_record(*, parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=0,
birth_city_id=None, seed_familiarity=0.8, seed_sentiment=0.8)`. Internally calls `self.lifecycle(...)` to
populate the five `LifecycleComponent` birth fields, then seeds child-side `SocialBond`s toward each
non-`None` parent via `.social(bonds=...)`. Already has one real cross-module caller today:
`EntityGenerator.spawn_natural_creature_offspring()` (`src/systems/world_systems/generator.py:85-...`),
which calls it with both parent ids `None` (parentless path — no genetics involvement, confirmed by that
ticket's own Completion Summary).

**Occupation/role field — no literal "Adventurer" value exists anywhere.** `IdentityComponent.role`
(`src/core/state.py:496`) is an `int` typed against `EntityRole` (`src/core/enums.py:6-12`):
`HERO=0, SHOPKEEPER=1, MONSTER=2, CITIZEN=3, WORKER=4, GUARD=5`. There is no `ADVENTURER` member.
`EntityGenerator.spawn_hero()` (`src/systems/world_systems/generator.py:34-57`) sets
`identity.role=EntityRole.HERO` and `kind("hero")` — `HERO` is the closest legacy analog to "Adventurer."
Separately, `RoleSemanticsService` (`src/content_semantics/role.py:8-77`) provides catalog-driven
`get_role_family(role_id)` / `is_combatant(role_id)` / `is_civilian(role_id)`, reading a `role_id` string
against `CatalogRepository` (content data, not live entity state) with a legacy fallback: `is_combatant`
returns `True` for `role_family in ("combatant", "adventurer", "recon", "attacker", ...)` **or** legacy
`EntityRole in (HERO, MONSTER, GUARD)`; `is_civilian` returns `True` for `role_family in ("civilian",
"service", "trade")` **or** legacy `EntityRole in (CITIZEN, SHOPKEEPER)`. `"adventurer"` literally appears
here as one `role_family` string value, but this service operates on a content-catalog `role_id`, not
directly on a live `EntityState` — how (or whether) a live entity's catalog `role_id` is resolvable from
just its `identity.role` int is not established anywhere in the read code. This is a genuine open question,
not a settled precedent — see Risks below.

## Mechanics / Engine Constraints

- **`docs/simulation/lifecycle_systems_contract.md` § Genetics** (Compliance IDs LEG-RPG-144, LEG-RPG-145):
  states all multipliers "range 0.8–1.3" (a hard law), that assignment happens only "at spawn" via
  `generate_profile_from_seed()`, and that "Genetic profiles are **permanent** — they do not change during
  simulation (no evolution or mutation during a run)." A parent-combination path is a **second
  construction-time assignment mechanism** (for bred entities, alongside the existing seed-based mechanism
  for spawned entities) — it does not violate the permanence law as long as the combined profile is set once
  at entity-construction time and never mutated afterward, mirroring the birth-record fields' own
  construction-time-only law (01_entity_anatomy.md §5).
- **Extension rule #2** in the same contract doc: "To add a new genetic trait: extend `GeneticProfile`...
  Multiplier range must stay 0.8–1.3 unless the trait is intentionally extreme (document in
  intentional_divergences.md)." Any new combination formula must keep each resulting per-attribute
  multiplier inside 0.8–1.3, or the divergence must be recorded in
  `docs/guidelines/intentional_divergences.md`.
- **`docs/mechanics/01_entity_anatomy.md` §5, "Birth Record (Reproduction Schema)"** — establishes that birth
  fields are "populated only at entity-construction time, via `V2EntityBuilder.birth_record()` — never
  mutated afterward." A genetics field, if added, should follow the identical law.
- **CLAUDE.md Durable State Rule**: "If something survives beyond the current tick or current function call,
  it must have a typed model, a stable location in entity/world/registry state, a defined lifecycle,
  inspection/debug visibility, and tests." A produced entity's combined `GeneticProfile` clearly survives
  beyond construction (it should affect the entity for its whole life per the permanence law) — today there
  is no stable location for it at all (see Current Behavior). This is the central architectural gap this
  ticket must resolve.
- **Authoritative Mutation Pipeline Contract** — durable changes only via typed `EntityUpdate`/`StateUpdate`
  through the authoritative apply path (`src/engine/patches.py`/`src/engine/apply_plan.py`), never a direct
  mutation. Ticket AC4 already states this; it requires a new `ComponentPatch`-style write path (or
  extending an existing one, e.g. `LifecyclePatch`) once the storage field's location is decided.

## Docs Requiring Update

- `docs/mechanics/01_entity_anatomy.md`: ticket AC explicitly requires this ("documents the inheritance
  mechanism"); add a new subsection near the existing §5 "Birth Record (Reproduction Schema)" documenting
  the combination formula, the 0.8–1.3 range law, and the occupation-bias direction rule, mirroring how
  TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA added its own birth-record subsection there.
- `docs/simulation/lifecycle_systems_contract.md`: the current "Genetics — `genetics.py`" section states
  assignment happens only "at spawn" via `generate_profile_from_seed()` and frames `GeneticsSystem` as
  having exactly one assignment mechanism — this becomes stale/incomplete the moment a second
  (parent-combination) assignment mechanism exists in the same module. Must add a subsection for the new
  combination method, parallel to the existing "Assignment at spawn" subsection, and note it as this
  module's first real live caller.
- `docs/parity_ledger/social_narrative.yaml`: new entry required — no existing entry documents an
  inheritance/combination mechanism (LEG-RPG-144's existing coverage, `PROG-028` in `progression.yaml`,
  only covers `test_genetic_seed_init` — a different behavior). Recommend adding to
  `social_narrative.yaml` rather than `progression.yaml`, for consistency with this same Reproduction
  epic's sibling entries (`SOC-259` birth-record schema, `WORLD-120` natural-creature path) rather than
  mixing into the unrelated evolution/training-focused entries already in `progression.yaml`. Final file
  choice is a Plan-phase call, but the entry itself is required either way.
- `docs/core/entities.md`: **only if** the implementer's Plan-phase storage decision adds the new
  `GeneticProfile`-carrying field to a component whose field table is already documented in this file (e.g.
  `LifecycleComponent`, whose row `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` already updated for its
  own new fields, or `IdentityComponent`) — then that row's Key Fields cell and line-range citation must be
  updated to match, exactly as the birth-record-schema ticket did for its own five new fields. If the
  condition is not met (e.g. the storage location is decided to be pass-through/non-durable, or a wholly new
  component not yet in this doc's table), resolve this bullet per the Format 1 conditional-bullet convention
  rather than deleting it silently.

## Parity Ledger Overlap

- **`PROG-028`** (`docs/parity_ledger/progression.yaml:281-301`) — `text: "test_genetic_seed_init: Genetic
  seed init."`, `status: verified`, `priority: P0`, **`test_path: null`**. This is the only existing ledger
  entry that cites LEG-RPG-144 (Innate Talents/Genetics) coverage, and it is a **P0 entry with a missing
  test_path**, which CLAUDE.md's Authoritative Mechanics Rule states P0 entries require. This gap predates
  this ticket and is not caused by it, but this ticket's work directly touches the same compliance ID —
  flagging for optional cleanup, not treating as mandatory in-scope (the ticket's own Related Code Areas do
  not list `progression.yaml`).
- **`SOC-259`** (`docs/parity_ledger/social_narrative.yaml`, `status: verified`) — the birth-record schema
  entry this ticket's new field/write-path extends; the new inheritance entry should cross-reference it.
- **`WORLD-120`** (`docs/parity_ledger/world_dynamics.yaml`, `status: verified`) — natural-creature
  reproduction path; explicitly confirms `parent_a_entity_id`/`parent_b_entity_id` stay `None` and no
  genetics involvement for that path — consistent with, and a useful cross-check for, this ticket's
  human/humanoid-only scope.
- No existing entry anywhere documents a genetic-inheritance/combination mechanism — a new entry is
  required (see Docs Requiring Update above); this is a new P2-appropriate entry (matches ticket Priority),
  not a P0 requiring `test_path` at creation, but should include one anyway per the new-test convention this
  epic's sibling tickets have all followed.

## Prior Work

- **TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA** (done) — shipped the exact pattern this ticket should
  follow: new typed fields on `LifecycleComponent`/`LifecycleUpdate`, a `LifecyclePatch.apply()` extension as
  the sole authoritative write path, and a new `V2EntityBuilder.birth_record()` convenience method. Notably,
  that ticket's own "Related Code Areas" list also started narrow (`src/core/state.py`, `src/core/updates.py`,
  `src/core/builder.py`, `src/engine/patches.py`, `src/engine/apply_plan.py`,
  `src/systems/social_systems/relationships.py` — it *did* list `state.py` and `patches.py` up front, unlike
  this ticket) and its plan.md enumerated every other writer of the touched component to rule out collision
  risk (Step 1's "Other writers" analysis) — that same enumeration discipline should be repeated here once
  the storage field's home is chosen.
- **TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH** (done) — registered a feature flag
  (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, default OFF) in `src/domains/optimization/feature_flags.py`
  because it wired a **real, live, every-tick-executed branch** into `CampService.process_camps()`. This
  ticket's situation differs: per the epic's stated build order, no live reproduction trigger exists yet
  (TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE, which would call into this ticket's function during an
  actual tick, has not been implemented). A feature flag gating code that no live tick-processing path
  invokes yet provides no protective/rollback value the way the natural-creature flag did. Recommend: this
  ticket does **not** need its own feature flag; the flag (if any) belongs to whichever ticket wires a live
  trigger. Flag this reading for Plan-phase confirmation rather than assuming it silently.
- `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md:37` explicitly states: "Birth cooldowns and
  the genetic-inheritance multiplier range have no comparable existing anchor" — confirming the ticket's own
  Assumptions note that the occupation-bias weighting formula must be designed fresh, not copied from
  elsewhere.
- `src/ai/goals/occupation_change_scorer.py` / `docs/mechanics/04_strategic_cognition.md` Tier 4 —
  precedent for role-based branching keyed off `EntityRole` (`SHOPKEEPER`/`WORKER`/`GUARD` vs `CITIZEN`), a
  useful structural pattern (not a numeric one) for how this ticket might read "occupation" off
  `IdentityComponent.role` if Plan decides that is the source field.

## Risks and Open Questions

1. **Blocking — no durable storage field exists for `GeneticProfile` on any entity today.** AC4 ("resulting
   profile is written via a typed `EntityUpdate` through the authoritative apply path") cannot be satisfied
   without adding a new field to `EntityState` (directly, or via an existing component) and a matching
   `EntityUpdate` field plus apply-path write logic — this necessarily touches `src/core/state.py` and
   `src/engine/patches.py`, neither of which is listed in this ticket's "Related Code Areas" (only
   `src/core/updates.py` is listed alongside the genetics files). The sibling BIRTH-RECORD-SCHEMA ticket's
   own scope needed the same four files together. Plan must not treat `state.py`/`patches.py` as out of
   bounds just because the ticket text omitted them — confirm this reading explicitly before Plan, don't
   silently assume a workaround (e.g. stuffing it into `IdentityComponent.properties`, which the Durable
   State Rule and this investigation's Anti-Drift Hazards both forbid).
2. **Blocking — "Adventurer-occupation" has no literal enum value anywhere.** `EntityRole` has no
   `ADVENTURER` member; the two real candidates are (a) `IdentityComponent.role == EntityRole.HERO` (set by
   `spawn_hero()`), or (b) `RoleSemanticsService.is_combatant(role_id)`/`get_role_family(role_id)`, which
   does include `"adventurer"` as a `role_family` string but operates on a content-catalog `role_id`, not
   directly on live `EntityState`. No code path in the read files establishes how a live human/humanoid
   entity's catalog `role_id` would be resolved for this comparison. Do not assume `EntityRole.HERO` is
   definitively "Adventurer" without an explicit Plan-phase decision — this determines the entire
   occupation-bias branch's input.
3. **AC1's "real, live caller" is satisfiable without a live simulation trigger existing yet.** The most
   direct reading: wire the new combination function into `V2EntityBuilder.birth_record()` via new optional
   parameters (a real, non-test, non-shim call site, already proven pattern from the natural-creature path's
   own `.birth_record()` call), exercised directly by this ticket's own new unit/integration tests — not
   requiring `HUMANOID-CADENCE-PHASE` to exist. Confirm this reading at Plan rather than assuming a different
   call site is required.
4. **No downstream consumer of a stored `GeneticProfile` exists.** `SkillScalingService.get_effective_stats()`
   (`src/engine/rpg_depth.py`, per `01_entity_anatomy.md`'s Wound Penalty section) does not reference
   genetics at all today. Even once this ticket stores a combined `GeneticProfile` on a bred entity, nothing
   in the production effective-stats pipeline reads it back — that wiring is out of scope for both this
   ticket and its declared successor (`HUMANOID-CADENCE-PHASE` only covers the trigger/cadence, not
   stat-consumption). Confirm this "standalone, testable, non-consumed-yet" framing is acceptable and not
   silently expected to visibly affect combat output in this ticket.
5. `PROG-028` (P0, `test_path: null`) is a pre-existing gap on the same compliance ID (LEG-RPG-144) this
   ticket's new caller exercises — optional cleanup opportunity, not mandatory scope.
6. The exact per-attribute combination/weighting formula (how two 0.8–1.3 parent multipliers + an
   occupation-bias direction produce a new 0.8–1.3 child multiplier) has zero numeric precedent anywhere in
   the codebase (confirmed by the epic doc's own note) — must be designed fresh at Plan, not assumed here.

## Anti-Drift Hazards

- Do not implement the human/humanoid reproduction trigger/cadence logic itself (cooldown checks, entity
  pairing) — explicitly out of scope, belongs to `TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE`.
- Do not add genetics involvement to the natural-creature or magical/demonic paths — both are confirmed
  genetics-free by their own shipped tickets (`NATURAL-CREATURE-PATH`'s Completion Summary: "natural
  creatures do not use `GeneticsSystem`/`GeneticProfile`"; `parent_a/b_entity_id` always `None` there).
- Do not store the combined `GeneticProfile` (or its component multiplier values) inside
  `IdentityComponent.properties: Dict[str, Any]` — this is exactly the free-form metadata escape hatch
  CLAUDE.md's Durable State Rule forbids ("do not store durable meaning in... free-form metadata").
- Do not add any marriage-contract precondition anywhere — same 2026-08-29 decoupling decision the sibling
  Reproduction-epic tickets already guard with dedicated tests.
- Do not touch `SkillScalingSystem`/`compute_skill_power()` in the same file — unrelated (LEG-RPG-145, skill
  power formulas), not in this ticket's scope.
- Do not remove, rename, or change the behavior of `GeneticsSystem.generate_profile_from_seed()` — it is the
  existing, independently-tested, spawn-time assignment mechanism (still used implicitly by the lifecycle
  contract doc's "Assignment at spawn" law) and must coexist unchanged alongside the new combination method.
- Any new per-attribute combined multiplier must stay within 0.8–1.3 (the lifecycle contract's Extension
  rule #2) unless explicitly recorded as an intentional divergence — do not let the occupation-bias weighting
  push values outside this range "for flavor."
- Do not conflate this ticket's produced entity (human/humanoid, from `HUMANOID-CADENCE-PHASE`, not yet
  built) with any other spawn path — this inheritance function must be standalone and callable in isolation
  by tests, not accidentally wired into `spawn_natural_creature_offspring()` or
  `spawn_magical_demonic_entity()`.
