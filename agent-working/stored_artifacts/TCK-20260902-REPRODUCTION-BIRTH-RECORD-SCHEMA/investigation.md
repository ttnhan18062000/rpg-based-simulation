---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
artifact_type: investigation
tags: [lifecycle, core]
---

# Investigation — TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA

## Current Behavior

**`LifecycleComponent`** (`src/core/state.py:151-180`, `@dataclass(frozen=True, slots=True)`):
current fields are `age_ticks`, `max_age_ticks`, `is_permadeath`, `death_tick`, `death_reason`,
`generation`, `heir_entity_id: Optional[int]`, `heirlooms: list[str]`, `active: bool`, plus a
`_canonical_cache`. `to_canonical_dict()` (lines 165-180) enumerates every field explicitly and
caches the result on `object.__setattr__`. **No parent identity, birth tick, birth location, or
reproduction-cooldown field exists anywhere on this component** — confirmed by reading the full
class body. This matches the ticket's premise exactly.

**`LifecycleUpdate`** (`src/core/updates.py:434-462`): typed mutation record with `age_delta`,
`generation_delta`, `is_permadeath_set`, `death_tick_set`, `death_reason_set`,
`heir_entity_id_set: Optional[int]`, `heirlooms_add: list[str]`. `is_noop()` (445-449) and
`merge()` (451-462) both enumerate every field individually — any new field added to the
dataclass must also be added to both of these methods or it will silently fail to merge/noop-check.
No parent/birth/cooldown fields exist here either.

**Apply path — `LifecyclePatch`** (`src/engine/patches.py:55-88`): the sole authoritative
consumer of `LifecycleUpdate`. `apply()` (69-88) reads `changes.get("lifecycle", entity.lifecycle)`,
applies each field with `set`-wins-over-baseline semantics (`u_life.heir_entity_id_set if ... is not
None else new_lifecycle.heir_entity_id`, line 84), and writes the new `LifecycleComponent` back into
`changes["lifecycle"]` only if it differs from the entity's current one (line 87). This is invoked
from `AuthoritativeApplyPipeline`/`ApplyPath` (`src/engine/apply_plan.py:279`,
`is_life_due = should_run(tick, None, cadence.lifecycle)`; `src/engine/apply_plan.py:725-726`,
`if update.lifecycle is not None or update.active is not None: p = LifecyclePatch(...)`) — this is
the only place that may durably write `LifecycleComponent` fields. Any new schema field must follow
this exact `*_set`/patch/apply chain; there is no other write path.

**`CampUpdate.last_raid_tick_set`** (`src/core/updates.py:860-875`) — the ticket's cited cooldown
precedent: `CampUpdate` is keyed by `id: str` (one Camp), with `last_raid_tick_set: Optional[int]`
applied wholesale (`new_raid = c_upd.last_raid_tick_set if c_upd.last_raid_tick_set is not None else
camp.last_raid_tick`, `src/engine/apply_plan.py:272`). This is a **single-value "last-write-wins"
set field**, not a per-key dict — it is NOT structurally a per-parent (multi-key) cooldown pattern.
The closer structural precedents inside `updates.py` for a per-key dict update are
`WorldUpdate.population_cohorts_set: Optional[Dict[str, Any]]` (wholesale dict replace, line 810)
and `BuildingUpdate.price_modifiers_set: Optional[Dict[str, float]]` (wholesale dict replace, line
770) — both replace the entire dict on `set`, mirroring how `RelationshipService.process_update`
(`src/systems/social_systems/relationships.py:52-62`) merges `SocialComponent.bonds: Dict[int,
SocialBond]` per-key instead (copy-dict, mutate one key, replace). A per-parent reproduction
cooldown (`Dict[int, int]`, parent_entity_id -> cooldown-expiry-tick) most closely matches the
per-key-dict-merge shape used for `bonds`/`trust_history`/etc, not the single-scalar `CampUpdate`
shape the ticket names as precedent — flagged under Risks/Open Questions below since the ticket's
own Assumptions section already marks this as an open Plan-phase decision.

**`EntityUpdate`** (`src/core/updates.py:648-744`): `lifecycle: Optional[LifecycleUpdate]` is
already a first-class field (line 670), merged via `self.lifecycle.merge(other.lifecycle)`
(line 731) and no-op-checked via `self.lifecycle.is_noop()` (line 696). No changes needed to
`EntityUpdate` itself — new fields live inside `LifecycleUpdate`.

**Entity creation / mid-tick spawn path — `StateUpdate.entities_add: List[EntityState]`**
(`src/core/updates.py:921`, merged at lines 1030/1099/1154): the authoritative mechanism for
introducing a brand-new entity mid-simulation (not just at world-assembly time). Confirmed live and
already used by `src/world/spawn.py:process_spawns` (`SpawnService`, lines 22-120): builds fully
constructed `EntityState` objects via `generator.spawn_monster`/`spawn_goblin` (which use
`V2EntityBuilder` internally), appends them to a plain list, and returns
`StateUpdate(entities_add=entities_add, next_entity_id_set=generator._last_id + 1 if entities_add
else None)`. `src/engine/apply.py:267-272` consumes `update.entities_add` by inserting each
`EntityState` directly into `new_entities[ent.id] = ent`. This is the exact shape a future
reproduction-trigger ticket will use to commit a newly-built child entity — this schema/builder
ticket must produce an `EntityState` (via the new builder path) that is compatible with being placed
directly into `entities_add`, plus separate `EntityUpdate`s for the two parents (cooldown +
`SocialUpdate.bond_updates`) in the same `StateUpdate`. `AuthoritativeState.next_entity_id`
(`src/core/state.py:1268`, self-healing guard at 1241-1242) is the existing monotonic-ID contract
this must respect — no new ID-allocation mechanism is needed or in scope.

**`V2EntityBuilder`** (`src/core/builder.py:79-160+`): `.lifecycle(...)` (lines 574-606) currently
accepts `active`, `age_ticks`, `max_age_ticks`, `is_permadeath`, `death_tick`, `death_reason`,
`generation`, `heir_entity_id`, `heirlooms` — builds a dict of only non-`None` overrides via
`_component()` (lines 55-64, which additionally filters to only fields present on the target
dataclass, so passing an as-yet-nonexistent kwarg is silently dropped rather than erroring). New
schema fields need a symmetrical extension of this method's signature (`parent_a_entity_id`,
`parent_b_entity_id`, `birth_tick`, `birth_city_id`, and the new cooldown field). `.social(...)`
(lines 496-544) already accepts `bonds: Optional[Dict[int, SocialBond]]` and applies it wholesale via
`_copy_dict` — sufficient, unmodified, for seeding the new child's own `bonds` entries toward its
two parents at construction time. `.build()` (133-160+) assembles the final frozen `EntityState`
from whatever `self._lifecycle`/`self._social` currently hold — no changes needed there.

**`SocialBond` seeding precedent — `src/systems/social_systems/relationships.py:51-62`**
(`RelationshipService.process_update`): `bond = new_bonds.get(tid, SocialBond(target_id=tid));
new_bonds[tid] = replace(bond, familiarity=..., sentiment=..., last_interaction_tick=...,
role=...)`, driven by `SocialUpdate.bond_updates: List[BondUpdate]` (a `BondUpdate` has
`target_id`, `familiarity_delta`, `sentiment_delta`, `last_interaction_tick_set`, `role_set` —
confirmed by the field names consumed here; the class itself lives in `src/core/updates.py` next to
`SocialUpdate`). **This is the authoritative path for the two already-existing PARENTS to receive a
new bond toward the child** (their `EntityUpdate.social.bond_updates` must include a `BondUpdate`
targeting the new child's id, applied through the normal `EntityUpdate`/apply-path machinery — the
same "typed EntityUpdate, never direct state mutation" law AC 2 states explicitly). For the
newly-constructed CHILD entity itself, seeding its own `bonds` toward each parent happens at
construction time via `V2EntityBuilder.social(bonds={...})` directly (no update/patch needed — the
entity doesn't exist yet to be "updated"). `SocialBond` (`src/core/models/social.py:13-20`):
`target_id: int`, `familiarity: float` (0.0-1.0), `sentiment: float` (-1.0 to 1.0),
`last_interaction_tick: int`, `role: RelationshipRole` (defaults `NEUTRAL`). No kinship-specific
field exists on `SocialBond` — "high familiarity/sentiment" per AC 4 must be expressed purely via
the existing `familiarity`/`sentiment` floats (no new field on `SocialBond`/`SocialComponent` is in
scope; the ticket's Related Code Areas do not list `src/core/models/social.py` for modification).

**`docs/core/entities.md:52`** — the existing Lifecycle component-table row already lists
`age_ticks, max_age_ticks, is_permadeath, death_tick, death_reason, generation, heir_entity_id,
heirlooms, active` and must be extended with the new field names.

## Mechanics / Engine Constraints

- **`docs/core/state.md`'s "Frozen Lifecycle" Law** (cited by `docs/core/entities.md:32` and
  `:145`): all `EntityState` mutation must flow through the frozen snapshot -> deliberation ->
  refinement -> authoritative-transition sequence (`AuthoritativeState.apply()`). New birth-record
  fields must be written only via `LifecycleUpdate.*_set` through `LifecyclePatch.apply` — never a
  direct `replace(entity.lifecycle, ...)` outside that path. This is identical to the constraint the
  `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` investigation already established for `heir_entity_id`, and
  this ticket's own AC 2 states it explicitly.
- **`docs/engine/authoritative_mutation_pipeline_contract.md`** (general Proposal -> Refine -> Apply
  shape, phase-ordering law): the new-entity-creation path (`StateUpdate.entities_add`) and the
  parent-side `EntityUpdate` (cooldown + bond) both already fit this contract's existing vocabulary
  without requiring the contract document itself to change (same reasoning the prior heir-assignment
  investigation reached for this same doc — it does not enumerate individual component/system
  internals).
- **Determinism** (`docs/engine/kernel.md`'s 7-phase deterministic loop; project Hard Rule "Do not
  break determinism"): this ticket does not add RNG or nondeterministic ordering itself (it is pure
  schema + builder plumbing, no trigger logic), but the per-parent cooldown field's dict-key
  iteration order must not leak into any future canonicalization/serialization in a
  non-deterministic way — `to_canonical_dict()` must sort dict keys the same way
  `LocalScarState.to_canonical_dict()` (`state.py:208`, `dict(sorted(...))`) and
  `LifecycleComponent.to_canonical_dict()`'s own `heirlooms` field
  (`sorted(list(self.heirlooms))`, line 176) already do for existing collection fields.
- **No marriage precondition** (explicit ticket constraint, 2026-08-29 build-order decision): no
  code path touched by this ticket (`LifecycleComponent`, `LifecycleUpdate`, `LifecyclePatch`,
  `V2EntityBuilder.lifecycle()`, `RelationshipService`) references any marriage/contract state today
  — confirmed by grepping `src/core/strategic.py`'s `ContractState`/`ContractStatus` and
  `src/systems/social_systems/relationships.py` for "marriage": no hits. There is nothing to
  decouple; the constraint is preserved by omission — this investigation's own new-field proposal
  introduces no marriage read/write, and the planner/implementer must keep it that way.

## Docs Requiring Update

- `docs/core/entities.md`: line 52's Lifecycle component-table row must list the new fields
  (`parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, and the new cooldown
  field name) alongside the existing `heir_entity_id`/`heirlooms` entries, matching this doc's
  existing per-component "Key Fields" table format.
- `docs/mechanics/01_entity_anatomy.md`: this chapter documents `EntityState`'s component model
  (its own Lifecycle-adjacent content is the elder-bracket attribute-bonus rule at lines 121-126,
  citing `lifecycle.age_ticks`/`LifecycleSystem.resolve_lifecycle()`) but currently has no
  birth-record/parentage content at all (confirmed by grepping the file for "parent|birth|heir" —
  only the existing elder-bracket paragraph and unrelated substring hits). A new short subsection
  (or an extension of the existing Lifecycle row/description) documenting what the new fields mean
  and that they are populated only at entity-construction time (never mutated afterward except the
  cooldown field, which the reproduction-trigger tickets will update) must be added.
- `docs/parity_ledger/social_narrative.yaml`: no existing entry documents per-entity birth/parentage
  metadata or a reproduction-specific bond-seeding rule (grepped all `SOC-\d+` entries for
  "parent|birth_tick|reproduction" — no hits; current max ID is `SOC-258`, so the next available ID
  is `SOC-259`). This is the correct file (not `world_dynamics.yaml`) because the new fields live on
  the per-entity `LifecycleComponent`/`SocialComponent`, matching where `SOC-245`
  (`TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s default-heir entry) already lives — that ticket
  established the precedent that individual-entity Lifecycle/kinship mechanics belong in
  `social_narrative.yaml`, not `world_dynamics.yaml`. A new `P2`-or-higher entry must record: the new
  schema fields, that they are written only through the typed update/apply path, the
  `SocialBond`-seeding rule, and a `test_path` pointing at this ticket's new serialization/builder
  tests.

The `docs/parity_ledger/world_dynamics.yaml` entries `WORLD-DEMO-005` and `WORLD-DEMO-006` (path:
`docs/parity_ledger/world_dynamics.yaml`, listed in the ticket's own Related Docs) are not required
to change for this ticket: both describe the *regional, aggregate* `PopulationCohort`/demographic
mechanics (`RegionalPressureModel` demand multiplier and `WorldCompiler.compile()`'s cohort seeding
at world-assembly time) — a completely different data model (`RegionState.population_cohorts: Dict[
str, PopulationCohort]`) from this ticket's *per-entity* `LifecycleComponent` birth-record fields.
Neither entry's `text` mentions individual entity parentage, and neither `v2_evidence` path
(`src/domains/demographics/cohort.py`, `src/domains/world_emergence/models.py`,
`WorldCompiler.compile()`) is touched by this ticket's Related Code Areas. They were listed in the
ticket as candidates to check for overlap, not as docs this ticket must edit — confirmed excluded.

The `docs/mechanics/05_world_evolution.md` "Birth/Death Law" subsection (§5, lines 149-158,
path: `docs/mechanics/05_world_evolution.md`) is also not required to change: it documents the
*regional cohort* birth/death rate formula (`net_change = int(cohort.count * birth_rate) -
int(cohort.count * mortality_rate)`), an aggregate demographic-cycle mechanic wholly distinct from
this ticket's individual-entity birth-record schema — this ticket does not touch
`DemographicCycleService` or `PopulationCohort` at all (both explicitly Out of Scope via the sibling
POPULATION-PRESSURE-CLOSURE child ticket). Naming collision with "birth" is coincidental; the two
concepts do not overlap in code or in the Mechanics Bible's existing chapter boundaries.

`CLAUDE.md` (path: `CLAUDE.md`, listed in the ticket's Related Docs) is not a `docs/` path and is not
itself modified by any implementation ticket — it was listed only as the source of the Durable State
Rule / Authoritative Mutation Pipeline Contract constraint this investigation already cites above.

## Parity Ledger Overlap

- No existing parity ledger entry (checked `social_narrative.yaml`, `world_dynamics.yaml`,
  `strategic_cognition.yaml`, `infrastructure.yaml` — the four files that reference
  `heir_entity_id`/`LifecycleComponent`/`heirloom` anywhere) documents per-entity birth/parentage
  metadata. Closest existing entry: `SOC-245` (`TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s default-heir
  selection rule, `social_narrative.yaml`) — same component (`LifecycleComponent`), same apply path
  (`LifecyclePatch`), but a functionally distinct mechanic (succession-on-death vs.
  birth-record-at-creation). No overlap requiring a status change to `SOC-245` itself.
- No `P0` parity entries are touched by this ticket's Related Code Areas, so there is no pre-existing
  `test_path` gate that must already pass before this work lands. A new entry (see "Docs Requiring
  Update") must be added with its own passing `test_path` per the standard "new entry, own test"
  rule — it is new, not modifying an existing `P0`.

## Prior Work

- `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` (`tickets/done/`, `stored_artifacts/`) — the closest
  precedent: a `LifecycleComponent`/`LifecycleUpdate`/`LifecyclePatch` field write path
  (`heir_entity_id_set`), landed the `social_narrative.yaml` `SOC-245` entry and a
  `05_world_evolution.md` subsection. Its investigation.md is the template this investigation
  followed for describing the frozen-state/apply-path constraint and for the "Docs Requiring Update"
  file-selection reasoning (why `social_narrative.yaml` over `world_dynamics.yaml`). Its plan.md
  and implementation were not re-read in full (out of scope for a schema-only ticket) beyond
  confirming the write-path shape, which is unchanged in current `src/`.
- `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR` (`tickets/done/`) — a bug-fix ticket
  touching `LifecycleComponent.heirlooms`'s tuple/list handling; relevant only as a reminder that
  `heirlooms` is stored as a `tuple` after `LifecyclePatch.apply` (line 85:
  `heirlooms=tuple(new_heirlooms)`) despite the dataclass default being `list[str]` — a
  type-looseness precedent to be aware of but not something this ticket needs to fix or touch.
- `TCK-20260831-POPULATION-COHORT-SEEDING` (DONE, hard dependency per ticket's Related Tickets) —
  the ticket that fixed `PopulationCohort.to_canonical_dict()` canonical-dict round-trip coverage
  referenced by this ticket's own AC 5 as the test-pattern template. Confirmed satisfied; no
  remaining gap blocks this ticket.
- `TCK-20260831-SPECIES-INTELLIGENCE-TIER` (DONE, hard dependency) — not directly touched by this
  ticket's Related Code Areas; listed only as a satisfied prerequisite per the ticket body.
- `src/world/spawn.py` (`SpawnService.process_spawns`) — not a "ticket" but the clearest existing
  runtime precedent for the `entities_add` + `next_entity_id_set` mid-tick entity-creation pattern
  this schema must be compatible with (see Current Behavior above). No prior ticket/artifact
  specifically documents this pattern in prose; it was read directly from source.

## Risks and Open Questions

- **Per-parent cooldown field shape is a genuine open Plan-phase decision, not resolved here** — the
  ticket's own Assumptions/Open Questions section flags this, and this investigation's Current
  Behavior section above shows the two candidate precedents (`CampUpdate.last_raid_tick_set`,
  single-scalar last-write-wins vs. `WorldUpdate.population_cohorts_set`/`BuildingUpdate.
  price_modifiers_set`, wholesale-dict-replace vs. the `bonds`/`trust_history` per-key-merge
  pattern) are structurally different from each other. A per-parent cooldown needs a `Dict[int, int]`
  (parent_entity_id -> cooldown-expiry-tick) on `LifecycleComponent`, and the corresponding
  `LifecycleUpdate` field must decide between: (a) wholesale dict replace on `set` (simplest, matches
  `population_cohorts_set`/`price_modifiers_set`, but a caller must always pass the *complete* dict,
  including both parents' unrelated pre-existing cooldowns, or risk clobbering the other parent's
  entry), or (b) a per-key add/delta shape (matches `bonds`, safer for concurrent-tick correctness
  but more code). Not assumed here — flagged for the Plan phase per the project's Uncertainty Rule.
- **Whether `birth_city_id` should validate against a real region/building registry** is unresolved.
  The ticket only asks for an `Optional[int]` field; nothing in Related Code Areas suggests adding
  referential-integrity validation (e.g. against `AuthoritativeState.regions`/`buildings`), and doing
  so would be scope creep into world-registry validation logic this ticket does not own. Flagging so
  the implementer does not silently add validation beyond a bare typed field.
- **`SocialBond.familiarity`/`sentiment` numeric targets for "high" are undefined** — AC 4 says "high
  familiarity/sentiment" without a number. No existing constant in `src/core/models/social.py` or
  `src/systems/social_systems/relationships.py` defines a "high" threshold (bonds are built purely
  from accumulated deltas elsewhere; this is the first *seeded-at-construction* bond in the
  codebase). The Plan phase must pick and document explicit values (e.g. following the same
  documentation-format precedent `SOC-245`/`04_strategic_cognition.md` §7.2 used for a different
  named-constant formula) rather than leaving them as inline magic numbers.
- **Whether the new child's `bonds` dict should seed a bond FROM parent as well** (i.e., does the
  parent's own `EntityUpdate.social.bond_updates` entry get created in the same
  builder-wiring path this ticket owns, or is that left for a later reproduction-trigger ticket to
  wire, since the ticket is explicit that "it only builds the schema and the builder-level wiring
  those paths will call into")? The ticket's Scope bullet 4 says "Seed a SocialBond between each
  parent and the new child entity ... following the seeding precedent in
  relationships.py:55" — read together with the ticket's explicit exclusion of trigger logic, the
  most consistent reading is: this ticket provides a *reusable helper/method* (on the builder or a
  small builder-adjacent function) that a caller supplies with parent EntityUpdates and a child-build
  call, but does **not** itself decide when reproduction happens. This is a shape question for the
  Plan phase, not an ambiguity in the underlying data model.

## Anti-Drift Hazards

- **Do not add a marriage-contract read or precondition anywhere in this schema, the builder path,
  or the apply path** — explicit ticket constraint (Out of Scope, 2026-08-29 decision). No existing
  code in the touched files references marriage today; keep it that way. This includes not gating
  `SocialBond` seeding on any `ContractState`/`ContractStatus` value.
  `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` describes both ideas 32 (Reproduction)
  and 33 (Marriage) but only idea 32 is in scope here.
- **Do not implement any of the three reproduction trigger paths** (natural-creature,
  magical/demonic, human/humanoid) or genetics inheritance wiring — both explicitly Out of Scope,
  reserved for sibling child tickets. This ticket must stop at schema + builder construction + typed
  apply-path wiring; no code should decide *when* a birth happens.
- **Do not touch `EntityUpdate.merge()`'s existing per-field enumeration incorrectly** — every new
  `LifecycleUpdate` field must be added to both `LifecycleUpdate.is_noop()` and
  `LifecycleUpdate.merge()` (both hand-enumerate fields; a forgotten field silently fails to merge
  across multiple same-tick writers, exactly the class of bug the existing `heir_entity_id_set`
  pattern already avoids correctly).
- **Do not put the `SocialBond` "high familiarity/sentiment" seeding logic inside
  `RelationshipService.process_update`** — that method processes deltas against an *existing*
  `SocialComponent`; the new child's own bonds are seeded once, at construction, via
  `V2EntityBuilder.social(bonds=...)`, not through the delta-merge apply path. Conflating the two
  would misrepresent the "typed EntityUpdate applied via authoritative apply path" AC (AC 2) — the
  child's own initial bonds are legitimately builder-time construction (the entity doesn't exist yet
  to have an update applied to it), while the *parents'* reciprocal bonds toward the child (if in
  scope per the Risks/Open Questions item above) genuinely must go through `SocialUpdate.bond_updates`
  since the parents already exist as durable entities.
- **Do not silently coerce `heirlooms`'s existing `list`/`tuple` looseness onto the new fields** —
  keep new list-shaped fields (if any) consistent with whichever shape the Plan phase picks, and do
  not reuse `heirlooms`' known type-inconsistency (see
  `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR` above) as a model to copy.
- **Keep `to_canonical_dict()` sorted/deterministic for any new dict-shaped field** (the cooldown
  field) — follow the `dict(sorted(...))` pattern already used elsewhere in `state.py`, not raw
  `dict(self.field)`, to avoid a hidden non-determinism source in canonical hashing.
