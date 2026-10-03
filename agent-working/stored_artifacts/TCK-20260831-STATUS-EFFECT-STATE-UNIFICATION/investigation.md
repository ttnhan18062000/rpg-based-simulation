---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION
artifact_type: investigation
tags: [architecture]
---

# Investigation — TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

## Current Behavior

### WoundState / ScarState precedent (`src/core/state.py:90-113`)

```python
@dataclass(frozen=True, slots=True)
class WoundState:            # state.py:90-101
    id: str
    kind: str
    severity: float
    tick_inflicted: int
    atk_penalty: float = 0.0
    def_penalty: float = 0.0
    speed_penalty: float = 0.0
    max_hp_penalty: float = 0.0
    healed: bool = False
    scar_created: bool = False

@dataclass(frozen=True, slots=True)
class ScarState:              # state.py:104-113
    id: str
    wound_kind: str
    tick_created: int
    atk_penalty: float = 0.0
    def_penalty: float = 0.0
    speed_penalty: float = 0.0
```

Storage: not a dict, not a single value — both are stored as **lists** on `CombatComponent`
(`state.py:311-312`: `wounds: List[WoundState] = field(default_factory=list)`, `scars: List[ScarState]
= field(default_factory=list)`), frozen to `tuple` on `EntityState.to_readonly()` (`state.py:906-907`).
`CombatComponent.to_canonical_dict()` (`state.py:313-333`) includes `"wounds": [asdict(w) for w in
self.wounds]` and `"scars": [...]` so both feed the determinism hash.

Write path: a dedicated typed update record, `WoundUpdate` (`src/core/updates.py:610-624`):
```python
class WoundUpdate:
    wounds_add: List[WoundState] = field(default_factory=list)
    wounds_heal: List[str] = field(default_factory=list)   # wound IDs to heal
    scars_add: List[ScarState] = field(default_factory=list)
```
hung off `EntityUpdate.wound_update: Optional[WoundUpdate]` (`updates.py:657`), applied through a
dedicated `WoundPatch` (`src/engine/patches.py:623-648`) that is registered in
`extract_patches()` (`patches.py:742-743: if update.wound_update is not None: p = WoundPatch(...)`).
`WoundPatch.apply()` reads `changes.get("combat", entity.combat)`, extends `wounds`/`scars` lists,
marks healed wounds via `replace(w, healed=True)`, and writes back a new `CombatComponent` into
`changes["combat"]`. This is the exact shape (typed dataclass → typed Update record → dedicated
Patch class registered in `extract_patches`) `StatusEffectState` must follow per the ticket's Scope.

Note: `_apply_entity_update_to_dict` (`src/engine/apply.py:475-489`) also treats
`update.wound_update is not None` as a `stats_dirty` trigger that forces
`SkillScalingService.get_effective_stats(..., wounds=new_com.wounds, scars=new_com.scars, ...)` to
re-run — wounds/scars feed derived combat stats, not just gating. `StatusEffectState` for
frozen/stunned has no equivalent derived-stat consumer today (see below).

### `InteractionComponent` / `InteractionUpdate` (existing typed multi-tick channel state)

`InteractionComponent` (`state.py:391-407`) already exists and already tracks multi-tick channel
progress:
```python
class InteractionComponent:
    target_node_id: int | None = None
    progress: int = 0
    start_tick: int = 0
```
It has **no `kind` field**. Its typed update, `InteractionUpdate` (`updates.py:67-82`), also has no
`kind`: `target_node_id`, `progress_delta`, `reset`. Write path: `InteractionPatch`
(`patches.py:120-143`) — `reset=True` replaces the whole component with a fresh
`InteractionComponent()` (defaults), otherwise merges `target_node_id`/`progress`.

`interaction_kind`, by contrast, is stored as a **plain string key in `identity.properties: Dict[str,
Any]`** (`IdentityComponent.properties`, `state.py:491`), written via `EntityUpdate.property_updates:
Dict[str, Any]` (`updates.py:662`) and applied through `IdentityPatch.apply()`
(`patches.py:200-236`, specifically `props.update(self.property_updates)` at line 221) — a plain
dict merge with no typed shape, no validation of the value set, and (important) **no way to clear a
key** — `property_updates` only ever adds/overwrites, it never deletes.

Every one of the 7 `interaction_kind` producers/consumers reads `entity.interaction.target_node_id`
(the typed field) and `entity.identity.properties.get("interaction_kind")` (the untyped field) in
the *same* guard clause, and both are always set together at the same call site in the two
producers (`harvest.py:31-42`, `loot.py:38-46`). This is strong evidence `interaction_kind` belongs
as a `kind` field on `InteractionComponent`/`InteractionUpdate`, not folded into `StatusEffectState`
— see "interaction_kind's relationship to StatusEffectState" below.

### The 5 status-flag consumer files (`status_frozen` / `status_stunned`)

All 5 are pure boolean gates except one (`combat.py`, which also scales damage):

1. **`src/engine/legality.py`** — 4 call sites, all `if actor.identity.properties.get("status_frozen")
   or actor.identity.properties.get("status_stunned"): return False, ReasonCode.ATTACKER_STATUS_BLOCKED`
   (or `entity`/`attacker` depending on method):
   - `legality.py:132` — `LegalityServiceV2.verify_action_legality` (region-suppression guard)
   - `legality.py:166` — `LegalityServiceV2.verify_movement_legality` (movement legality, "0. Status
     Check")
   - `legality.py:218` — `LegalityServiceV2.verify_attack_legality` ("2. Readiness / Status Law")
   - `legality.py:319` — `LegalityServiceV2.verify_aoe_legality` ("1. Attacker Validity")
2. **`src/engine/combat.py:84`** — `CombatResolutionSystem.calculate_tactical_multipliers`:
   ```python
   if defender.identity.properties.get("status_frozen"):
       atk_mult *= 1.5
       trace["SHATTER"] = 1.5
   ```
   This is the **one non-boolean-gate use** — `status_frozen` on the *defender* multiplies attacker
   damage by 1.5x ("Shatter"), and the multiplier is recorded in the per-attack `trace` dict
   (`CombatUpdate.trace`). `status_stunned` is not read here at all (only `status_frozen`).
3. **`src/engine/pipeline_phases/actor_validity.py:59-65`** — `ActorValidityPhase.resolve` (Logic ID
   `TOWN-001`, compliance tag `AUTH-010`), reads all three status keys together:
   ```python
   is_stunned = entity.identity.properties.get("status_stunned", False)
   is_frozen = entity.identity.properties.get("status_frozen", False)
   is_sleeping = entity.identity.properties.get("status_sleeping", False)
   ```
   `status_sleeping` is **not in this ticket's scope** but is read in the exact same guard as
   `status_frozen`/`status_stunned` — see Anti-Drift Hazards.
4. **`src/systems/strategic_systems/work_queue.py:32`** — `WorkQueueBuilder.build`, skips an entity
   from the eligible-work-queue candidate list if frozen or stunned.
5. **`src/systems/strategic_systems/intelligence.py`** — 3 call sites, all `continue`/`return
   StrategicUpdate()` early-exit guards labeled "Legality Guard: Incapacitated entities skip
   strategic cycles": lines `848`, `918`, `1221`.

**Writers**: a repo-wide grep (`grep -rn "status_frozen\|status_stunned" .` across `src/`, `docs/`,
content packs) found **zero production writers**. The only places these keys are ever set are test
fixtures that construct `identity.properties={"status_frozen": True}` directly (`tests/unit/combat/
test_phase5_combat_legality.py:62`, `test_combat_legality_regression.py:51`,
`test_rpg_core_recovery.py:188`, `test_phase5_negative_cases.py:184/194/255`,
`test_tactical_hardening.py:30`, `tests/unit/strategic/test_status_hardening.py:22,45`,
`tests/unit/core/test_hardening_e5.py:65`). **This means in production today these flags are always
absent/false** — every one of the 5 consumer files' frozen/stunned branches is currently dead in
live simulation runs, only exercised via direct-construction test fixtures. This is a real fact for
Plan: the migration's write side has no existing production caller to port — Plan must decide
whether the new `StatusEffectState` write path is validated purely by porting the existing
direct-dict test fixtures to the new typed shape (minimum viable) or also wires a real production
producer (would be new functionality, arguably out of this ticket's stated scope, which is a
structural migration not a new-feature ticket).

### The 7 `interaction_kind` consumer files

Producers (2 — both also set `InteractionUpdate` in the same `EntityUpdate` construction):
- `src/actions/harvest.py:31-42` — `HarvestAction.start_harvest` sets
  `property_updates={"interaction_kind": "harvest", "harvest_duration": float(node.required_ticks)}`
  alongside `interaction=InteractionUpdate(target_node_id=..., progress_delta=0.0, reset=False)`.
  `harvest_duration` is a **second, adjacent untyped property key** set at the same call site —
  **not in this ticket's scope** (only `interaction_kind` is named); do not fold it in.
- `src/actions/loot.py:38-46` — `LootAction.start_loot` sets `property_updates={"interaction_kind":
  target_kind}` (`target_kind` is `"ground_item"` or `"corpse"`, passed in by the caller) alongside
  the same `InteractionUpdate` pattern.

Consumers (read `entity.identity.properties.get("interaction_kind")` guarded by
`entity.interaction.target_node_id is not None`):
- `src/systems/world_systems/harvesting.py:19` — `HarvestSystem.update`, gates on `== "harvest"`.
  Also reads the adjacent `harvest_duration` key at line 43 (`entity.identity.properties.get
  ("harvest_duration", 10.0)`) — out of scope, flagged for awareness only.
- `src/systems/economy_systems/chests.py:19` — `ChestSystem.update`, gates on `== "chest"`.
- `src/systems/economy_systems/loot.py:20-63` — `LootSystem.update`, gates on `in ["ground_item",
  "corpse"]`, branches on the value 3 more times (lines 20, 21, 28, 63).
- `src/systems/economy_systems/town_service.py:17-46` — `TownServiceSystem.update`, gates on `in
  ["inn", "tavern", "guild"]`, branches on the value for "inn" vs other kinds (line 46).
- `src/systems/social_systems/guilds.py:19` — `GuildIntelSystem.update`, gates on `== "guild"`.

**Distinct value set actually observed** (closed, enum-like, 7 values): `"harvest"`, `"ground_item"`,
`"corpse"`, `"chest"`, `"guild"`, `"inn"`, `"tavern"`.

**Gap found**: `"chest"`, `"guild"`, `"inn"`, `"tavern"` are read by consumers but **never produced
anywhere in `src/`** — only `"harvest"` (`actions/harvest.py`) and `"ground_item"`/`"corpse"`
(`actions/loot.py`) have real production writers. `tests/unit/world/test_chest_lifecycle.py:14` and
`tests/unit/world/test_guild_intel.py:12` construct `identity.properties={"interaction_kind":
"chest"}` / `"guild"` directly as fixtures — `ChestSystem`/`GuildIntelSystem`/`TownServiceSystem`'s
"inn"/"tavern"/"guild"/"chest" branches are exercised only by tests, never by a live production
action today. Not a defect this ticket needs to fix (out of scope — production wiring gap, not a
typed-state gap), but Plan should be aware the migration's "provably unchanged" bar for these 4
values can only be demonstrated via test-fixture parity, not an end-to-end production trace.

**Reset/staleness note**: because `interaction_kind` lives in `identity.properties` (merge-only, no
delete) while `target_node_id` lives in `InteractionComponent` (replaced wholesale on
`reset=True` → fresh `InteractionComponent()`), after an interaction reset `interaction_kind`
*stays* in the properties dict indefinitely — it is never cleared. This causes no visible bug today
only because every consumer's guard checks `entity.interaction.target_node_id is not None` *before*
reading `interaction_kind`, so the stale value is never actually branched on. If `interaction_kind`
moves onto `InteractionComponent` as a `kind` field, a `reset=True` naturally clears it for free
(since the whole component gets replaced with defaults) — an incidental correctness improvement, but
one that changes what "provably unchanged" needs to demonstrate (the old stale-but-unread state
vs. the new clean-on-reset state) — Plan should call this out explicitly rather than let it pass
silently.

### `InteractionSystem.enforce` (`src/engine/interaction.py`) — related but not a consumer

`src/engine/interaction.py` (195 lines, Compliance IDs `TOWN-005, TOWN-010, TOWN-020`) is a live,
wired production phase (`src/engine/pipeline.py:317`, phase `"interaction_enforcement"`) that also
operates on `InteractionUpdate`/`ResourceNodeUpdate`/`IdentityUpdate`. It does **not** reference
`identity.properties` or `interaction_kind` at all (grepped, zero hits) — confirmed **not** an 8th
consumer, the ticket's 7-file list is complete. It is however evidence that extending
`InteractionUpdate` with a `kind` field sits in the same phase family already handling
`InteractionUpdate` deltas, which is architecturally low-risk relative to the pipeline.

## Mechanics / Engine Constraints

- `docs/engine/authoritative_pipeline.md:67-72` — "Actor Validity" (Logic ID `TOWN-001`): "Law:
  Stunned or Frozen entities are blocked from submission." / "Law: Sleeping entities are blocked
  from submission." This is the doc backing `actor_validity.py`'s boolean gate — text is generic
  ("Stunned or Frozen"), not coupled to the `identity.properties` implementation detail, so a typed
  migration with unchanged behavior does not require a text change here (see "Docs Requiring
  Update").
- `docs/mechanics/02_combat_laws.md:37` — the tactical-modifier table: `| **Shatter** | x1.50 Atk |
  Target is currently in the Frozen state. |`. This is the doc backing `combat.py:84`'s SHATTER
  multiplier. Same as above — text names the "Frozen state" generically, not the property key, so no
  text change is required as long as the SHATTER multiplier's behavior (1.5x atk when defender is
  frozen) is preserved bit-for-bit by the migration.
- `docs/architecture/cognition_domain_ownership.md` — establishes ownership only for `CognitionModel`
  sub-components (`PerceptionModel`, `TemporalModel`, `CausalMemory`, `SpatialMemory`,
  `MotivationModel`, `CommitmentModel`, `RelationshipModel`, `RoleModelBundle`, `DerivedViews`,
  `DecisionTrace`) — see "Docs Requiring Update" for why `StatusEffectState`/`interaction_kind` do
  not belong in this table at all (they live on `EntityState` components, not `CognitionModel`).

## Docs Requiring Update

None of the docs examined require a text change to remain accurate, **provided** the migration
preserves current behavior exactly (which is the ticket's own AC #2 requirement). All are Format 2
(considered, excluded):

The `docs/engine/authoritative_pipeline.md` Actor Validity section (path:
`docs/engine/authoritative_pipeline.md`, lines 67-72) is not required to change: its "Stunned or
Frozen entities are blocked from submission" law is stated in terms of entity status, not the
`identity.properties` dict shape that currently backs it. Migrating the storage from an untyped dict
key to a typed `StatusEffectState` does not change this law's truth value, so the doc text stays
accurate.

The `docs/mechanics/02_combat_laws.md` Shatter row (path: `docs/mechanics/02_combat_laws.md`, line
37) is not required to change for the same reason: it documents the 1.5x Shatter multiplier as a
function of "the Frozen state," not the storage mechanism. As long as `combat.py:84`'s SHATTER
behavior is bit-identical after migration, this row remains accurate.

The `docs/architecture/cognition_domain_ownership.md` EmotionalModel gap (path:
`docs/architecture/cognition_domain_ownership.md`) — the ticket's own Assumptions/Open Questions and
AC #4 flag this speculatively. Investigation traced it concretely: `EmotionalModel` is a real
`CognitionModel` sub-component field (`src/core/cognition.py:168,197`) genuinely missing a row in
that table, but it is a **pre-existing, unrelated gap** — `EmotionUpdateService` is called only from
`src/engine/pipeline_phases/hardening.py:97` for the `"near_death"` event kind, has zero code overlap
with any of the 12 `StatusEffectState`/`interaction_kind` consumer files, and is explicitly listed
Out of Scope by this ticket's own text ("Re-wiring `EmotionUpdateService.update_on_event()` for
event_kinds beyond `'near_death'`... not part of this migration"). AC #4's own wording is
conditional ("ONLY IF this ticket's scope touches EmotionUpdateService migration") — this ticket's
actual scope does not touch it, so per AC #4's own condition the row addition is **not required**.
Recommend Plan state this explicitly as "condition not met" rather than silently drop it (mirrors
the `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` resolution pattern, even though
this bullet was never written in Format 1 to begin with since the condition was already
resolvable at investigation time).

`None.` would be inaccurate to write bare, since the EmotionalModel row is a real (if unrelated) gap
worth a future ticket — but no Format 1 bullet applies to *this* ticket's own required doc changes.

## Parity Ledger Overlap

- **`docs/parity_ledger/town_resource.yaml`**: `TOWN-009` ("Looting is a channeled state with
  progress, interruption, and completion semantics.", P0, `status: verified`) and `TOWN-010`
  ("Harvesting is a channeled state tied to nearby resource-node legality and harvest duration.", P0,
  `status: verified`) both cite `v2_evidence: src/engine/interaction.py (InteractionSystem.enforce
  ...)` and `test_path: tests_v2/parity/test_resource_interaction_parity.py`. **That test file does
  not exist** (`find . -iname test_resource_interaction_parity.py` → no results) — a pre-existing
  broken P0 test_path, not caused by this ticket. Flagging per investigation instructions; not this
  ticket's job to fix, but the migration must not further stale this evidence — if `interaction_kind`
  moves onto `InteractionComponent`, `v2_evidence` naming `src/engine/interaction.py` specifically
  (rather than the real `harvesting.py`/`loot.py`/etc. producers) stays equally (in)accurate either
  way, so no ledger update is strictly triggered by this migration, but Plan/parity-updater should
  be aware the existing evidence was already imprecise before this ticket touched anything.
  `TOWN-113`, `TOWN-116`, `TOWN-117`, `TOWN-118` (all P0, `status: verified`, channel-interruption
  semantics) have `test_path: null` — evidenced only via "exhaustive checklist audit," not a live
  test. None of these five entries need a `status`/`v2_evidence` change from this migration as long
  as channel behavior (progress accrual, reset-on-interrupt, completion threshold) is bit-identical
  after the `kind` field moves onto `InteractionComponent` — but the parity-updater phase should
  double check after implementation that no entry's `v2_evidence` file path became stale (e.g. if
  `IdentityPatch` is no longer touched for `interaction_kind` writes and `InteractionPatch` becomes
  the sole writer instead).
- **`docs/parity_ledger/combat_movement.yaml`**: no entry keyed specifically to `status_frozen`/
  `status_stunned`/`ATTACKER_STATUS_BLOCKED` was found by name (grepped `ATTACKER_STATUS_BLOCKED`,
  `status_frozen`, `status_stunned` across all `docs/parity_ledger/*.yaml` — zero hits). `COMB-122`
  ("`test_shatter_combo`: combo behavior", P0, `status: verified`, `test_path: null`) is the closest
  entry that plausibly covers the SHATTER multiplier at `combat.py:84`, though its evidence is the
  same "exhaustive checklist audit" placeholder, not a named test. No P0 entry currently names
  `status_frozen`/`status_stunned` by field, so there is no existing ledger entry whose `status` this
  migration is obligated to flip — but if Plan/parity-updater judges the migration meaningfully
  changes the *evidence* for the ATTACKER_STATUS_BLOCKED law (a new typed test replacing the old
  dict-literal tests), a fresh entry citing the new test file would strengthen, not weaken, ledger
  accuracy. Not flagging this as a required Format 1 doc bullet since no existing entry's `status`
  or `v2_evidence` becomes false through this migration — this is a discretionary strengthening
  opportunity, not a correctness requirement.

## Prior Work

- **`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`** (`stored_artifacts/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING/`)
  — this is *not* the ticket that created `WoundState`/`ScarState` (those already existed); it wired
  new *consumers* of wound/scar distress into tactical decision logic (cover-seeking/retreat gates,
  PROTECTOR guard branches). Confirms `WoundState`/`ScarState` is an actively-extended, stable
  pattern other tickets build on top of without needing to touch the typed record itself — good
  precedent that a `StatusEffectState` following the same shape will be similarly extensible.
- Registry scan (`docs/REGISTRY.yaml`, filtered on `related_code_areas` overlap with this ticket's
  12 consumer files) returned ~90 matches, almost all incidental touches to `src/core/state.py` /
  `src/engine/legality.py` / `src/systems/strategic_systems/intelligence.py` from unrelated feature
  work (faction/siege/quest/hunger/perf tickets) — none of them touch `status_frozen`/
  `status_stunned`/`interaction_kind` or propose a typed-state migration for either. No closer prior
  art than the `WoundState`/`ScarState` precedent itself was found.

## Risks and Open Questions

1. **Determinism-hash coverage** (open, needs Plan's explicit handling): `EntityState.to_canonical_dict()`
   (`state.py:739-801`) currently includes `"properties": dict(sorted(self.identity.properties.items()))`
   at line 796 as a single top-level key — this is what currently puts `status_frozen`,
   `status_stunned`, `interaction_kind`, and every other `identity.properties` key into the
   determinism/replay hash. If either field moves off `identity.properties` onto a new typed
   component, that component's own `to_canonical_dict()` must add an equivalent entry (mirroring how
   `combat.to_canonical_dict()` already includes `"wounds"`/`"scars"`, `interaction.to_canonical_dict()`
   already includes its 3 fields) — otherwise the migration silently drops that state from the
   canonical hash, which would be a determinism/replay regression even though runtime behavior
   ("provably unchanged" per AC #2) looks identical. This is not itself a design decision (Plan's
   job is field shape) but it is a concrete correctness requirement Plan must include as a step.
2. **No production writer for `status_frozen`/`status_stunned`** (see Current Behavior): the
   migration's "behavior provably unchanged" bar can only be proven via the existing test-fixture
   writers (13 sites across 8 test files) being ported to construct the new typed field instead of a
   dict literal — there is no live production code path to trace end-to-end. Open question for Plan:
   is porting test fixtures alone sufficient "provably unchanged" coverage, or does AC #2 imply new
   coverage is also needed? Recommend treating fixture-parity as sufficient (matches the ticket's own
   framing as a storage-shape migration, not new functionality) but this is Plan's call, not mine to
   assume.
3. **`status_sleeping` sits in the same untyped dict, same read site (`actor_validity.py:59-65`), but
   is explicitly out of this ticket's scope.** Plan needs to decide whether `actor_validity.py` ends
   up with a hybrid read (2 typed field reads + 1 remaining untyped dict read) as an accepted
   interim state, or whether that hybrid is itself confusing enough to warrant a follow-up ticket
   note. Not this ticket's job to migrate `status_sleeping` — flagging so it isn't accidentally
   swept in as scope creep, and so the resulting hybrid code isn't mistaken for an oversight.
4. **`StatusEffectState`'s proposed fields (`source`, `magnitude`, `expires_tick`) have zero current
   readers beyond a boolean truthy check.** Every one of the 5 status-flag consumer sites (including
   the SHATTER multiplier) only checks presence/truthiness — none reads a magnitude, none reads an
   expiry tick, none reads a source. Unlike `WoundState`/`ScarState` (whose richer fields — severity,
   penalties, tick_inflicted — are genuinely read by `SkillScalingService.get_effective_stats` and
   healing/scar-creation logic), `StatusEffectState`'s proposed enrichment fields would currently be
   write-only with no reader. This is not necessarily wrong (future-proofing the way `WoundState` was
   presumably built out ahead of some of its own consumers), but Plan should treat it as a conscious
   YAGNI trade-off to state explicitly, not an assumed win — especially since AC #2 requires
   "behavior provably unchanged," which a magnitude/expiry field with no reader trivially satisfies
   (it just sits unused) but doesn't itself justify.

## Anti-Drift Hazards

- Do not conflate `harvest_duration` (`harvest.py:39-40`, `harvesting.py:43`) with `interaction_kind`
  — they're set at the same call site and read in the same file, but only `interaction_kind` is in
  this ticket's scope. Leave `harvest_duration` in `identity.properties` untouched.
- Do not migrate `status_sleeping` (`actor_validity.py:59-61`) alongside `status_frozen`/
  `status_stunned` — it is read in the same guard but is not named in this ticket's scope.
- Do not touch `EmotionUpdateService`/`EmotionalModel`/`hardening.py:97` — confirmed zero code
  overlap with this ticket's actual consumer files; touching it would be unrelated scope creep despite
  the ticket's own doc-gap flag (see "Docs Requiring Update").
- Do not "fix" the 4 never-produced `interaction_kind` values (`"chest"`, `"guild"`, `"inn"`,
  `"tavern"`) by adding new production writers — that would be new functionality (wiring
  ChestSystem/GuildIntelSystem/TownServiceSystem to a real action), not a typed-state migration. The
  migration only needs to preserve the *existing* (test-fixture-only) behavior for those values.
  Wiring real producers is legitimate future work but a different ticket.
- Preserve the exact SHATTER semantics at `combat.py:84` — `status_frozen` (not `status_stunned`) on
  the **defender** (not attacker) multiplies **attacker** `atk_mult` by exactly `1.5` and records
  `trace["SHATTER"] = 1.5`. This is the one call site where getting attacker/defender or
  frozen/stunned swapped would silently change combat balance without any test necessarily catching
  it unless the shatter-specific test (`COMB-122`/`test_shatter_combo`, if it exists under that name)
  is in the regression run.
- If `interaction_kind` moves onto `InteractionComponent`/`InteractionUpdate`, remember `reset=True`
  already replaces the whole component (`InteractionPatch.apply`, `patches.py:135-136`) — this will
  newly *clear* `kind` on reset where the old dict-based `interaction_kind` never cleared. Confirm
  this doesn't change any consumer's observable behavior (it shouldn't, per the "Reset/staleness
  note" above, since all consumers gate on `target_node_id is not None` first) but call it out
  explicitly as an intentional, provably-inert side effect rather than an unnoticed change.
