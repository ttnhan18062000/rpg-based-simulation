---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION
artifact_type: plan
tags: [faction, social]
---

# Implementation Plan — TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Summary

Wire `ClanState` into the authoritative mutation pipeline for the first time (mirroring
`FactionState`'s 6-touch-point pattern exactly), then build Clan joining (via a new
`ContractKind.CLAN` + `SocialAppraisalSystem._appraise_clan()` dispatch branch), leaving, and
margin-free succession-on-death as a fresh, standalone service — never reusing or coupling to
`PartyLifecycleService.check_leadership()` (Group's 0.2-margin election) or
`GroupSystem.update_groups()` (Group's unconditional dead-leader dissolution), per the ticket's
explicit "must be built fresh" framing. The durable-write mechanism for joining/leaving is a new
**two-phase pattern**: `CoreActions.execute_join_clan`/`execute_leave_clan` run through the
existing `ActionRouter`/`ActionRoutingPhase` machinery exactly like `execute_propose_marriage`
(legality, readiness, sliding-state, rejection-audit all reused for free) and call
`appraise_contract()` for joining — but because `ActionRouter.execute_action` is contractually
locked to `Dict[int, EntityUpdate]` (confirmed, `src/engine/domain/action_router.py:20-27`, and
the per-actor merge loop at `src/engine/pipeline_phases/actions.py:246-251` only folds
`EntityUpdate` fields), these handlers cannot themselves emit a registry-level `ClanUpdate`. So a
second, new pipeline phase (`ClanLifecyclePhase`, running immediately after the existing `groups`
phase, `src/engine/pipeline.py:391`) scans the already-annotated task outcomes
(`update.entity_updates[eid].task.payload_set` — annotated automatically by
`ActionRoutingPhase.route()` at `src/engine/pipeline_phases/actions.py:244`, the same mechanism
every other action already relies on) for `SUCCESS`-outcome `JOIN_CLAN`/`LEAVE_CLAN` tasks and
converts them into `ClanUpdate` membership deltas, and in the same phase runs the fresh
margin-free succession check and the dissolution check. The "zero assets" dissolution AC is
resolved by adding one new minimal `ClanState` field, `asset_ids: Tuple[int, ...] = ()` (Decision
below) — no asset-granting/consuming mechanic is built; the field is read-only in this ticket's
dissolution check and populated only via direct construction in tests.

## Decision — "Zero Assets" Dissolution AC (Investigation Risk #1)

**Chosen: Option (a) — add a new minimal `ClanState` field, `asset_ids: Tuple[int, ...] = ()`.**

Reasoning:
- The ticket's own Out-of-Scope guard reads: "Any new asset/institutional-footprint mechanic
  *beyond the minimum needed for the 'zero assets' dissolution AC* — if out of reach this ticket,
  defer explicitly." This authorizes exactly one minimal field; it does not forbid one. A single
  `Tuple[int, ...] = ()` field, following the *exact* existing pattern of
  `member_entity_ids`/`home_region_ids` on the same class (`src/core/state.py:683-684`), is
  unambiguously "in reach" — it is not a new mechanic, just a schema slot.
- Investigation's alternative sub-option (reusing `home_region_ids` as the footprint measure) was
  explicitly flagged as conflating "has territory" with "has assets" — rejected here for the same
  reason the investigation raised it as a concern, not a recommendation.
- Option (b) (scope AC #2 down to `member_entity_ids`-only) would require rewriting the ticket's
  own AC #2 text as a deviation. Since a compliant field is reachable at minimal diff, no deviation
  is needed — **AC #2's literal wording is implemented as written, no ticket-text revision
  required.**
- **Explicit scope boundary, restated so the implementer does not drift**: this ticket adds
  *only* the field and the dissolution-check read of it. No `ClanUpdate` mutator field
  (`asset_ids_add`/`asset_ids_remove`) is added — nothing in this ticket's scope grants or removes
  Clan assets, so a mutator would be dead API. Tests populate `asset_ids` via direct `ClanState(...)`
  construction (the same pattern already used throughout `test_faction_state.py` for setup). A
  future ticket owns whatever mechanic actually grants/spends Clan assets.

## Steps

### Step 1 — Extend `ClanState` schema with `asset_ids`
**Files:** `src/core/state.py`
**Change:** In the `ClanState` dataclass (`src/core/state.py:678-718`, confirmed by direct read —
8 fields today: `clan_id, name, member_entity_ids, home_region_ids, tension_level,
leader_entity_id, founded_tick, dissolved_tick`), add one new field immediately after
`home_region_ids` (line 684): `asset_ids: Tuple[int, ...] = ()`, docstring note: "IDs of
buildings/items/resources this Clan institutionally holds — the AC-mandated 'zero assets'
dissolution measure (idea 40/M4). No producer/consumer of this field exists yet; it is read-only
in this ticket's dissolution check and populated only by direct construction in tests until a
future ticket adds a real asset-granting mechanic." Add `"asset_ids": sorted(self.asset_ids)` to
`to_canonical_dict()` (mirrors `member_entity_ids`/`home_region_ids` at lines 697-698) and
`asset_ids=tuple(d.get("asset_ids", []))` to `from_dict()` (mirrors lines 712-713).
**Do NOT touch:** `FactionState` (lines 639-676) — it has no dissolution concept and none is added
here; do not add a matching field there.
**Verify:** `test_clan_state_serialization_round_trip` and
`test_clan_state_serialization_round_trip_defaults` (existing, must keep passing with the new
field defaulting to `()`); new `test_clan_state_asset_ids_round_trip` in
`tests/unit/domains/faction/test_clan_state.py`.

### Step 2 — Wire `ClanState` into `AuthoritativeState` (touch points 1–2 of the `FactionState` pattern)
**Files:** `src/core/state.py`
**Change:** Mirror `FactionState`'s wiring exactly (investigation confirmed 6 touch points total
via direct read of every cited line — this step covers the first 2):
1. Field declaration: add `clans: Dict[str, "ClanState"] = field(default_factory=dict)`
   immediately after the `factions: Dict[str, "FactionState"] = field(default_factory=dict)` line
   (confirmed `src/core/state.py:1232`), with a one-line comment `# Idea 40/M4: Durable clan-level
   state`, mirroring the `# Epic 5.3: Durable faction-level state (E53Aa)` comment style on the
   line above it.
2. `to_readonly()`: add `clans=ReadOnlyDict(self.clans),` immediately after
   `factions=ReadOnlyDict(self.factions),` (confirmed `src/core/state.py:1314`).
**Do NOT touch:** Any other field in the `replace(self, ...)` call at `to_readonly()`
(`src/core/state.py:1302-1324+`) — only add the one new line, do not reorder existing ones.
**Verify:** `test_authoritative_state_has_clans_field` (new, mirrors
`test_authoritative_state_has_factions_field` — `tests/unit/domains/faction/test_faction_state.py`
lines 43-58) — added in Step 6.

### Step 3 — `ClanUpdate` typed record + `StateUpdate.clan_updates` (touch points 3–5)
**Files:** `src/core/updates.py`
**Change:** Add a new frozen dataclass immediately after `FactionUpdate`
(`src/core/updates.py:920-941`, confirmed by direct read):
```python
@dataclass(frozen=True, slots=True)
class ClanUpdate:
    """Typed mutation record for a single clan's durable state (idea 40/M4)."""
    clan_id: str
    member_entity_ids_add: Tuple[int, ...] = ()
    member_entity_ids_remove: Tuple[int, ...] = ()
    leader_entity_id_set: Optional[int] = None
    dissolved_tick_set: Optional[int] = None

    def is_noop(self) -> bool:
        return (
            not self.member_entity_ids_add
            and not self.member_entity_ids_remove
            and self.leader_entity_id_set is None
            and self.dissolved_tick_set is None
        )
```
No `tension_delta`/`name_set`/`asset_ids_add` fields — nothing in this ticket's scope mutates
`tension_level` (idea 68 guard, see Anti-Drift Notes), `name`, or `asset_ids` (Decision above), so
no mutator field is added for them (avoids dead API).
Then, on `StateUpdate` (`src/core/updates.py:944-999`, confirmed field list read in full):
- Add `clan_updates: List[ClanUpdate] = field(default_factory=list)` immediately after
  `faction_updates: List[FactionUpdate] = field(default_factory=list)` (confirmed line 999).
- `is_noop()` (confirmed lines 1001-1028): add `and not self.clan_updates` immediately after
  `not self.faction_updates and` (confirmed line 1025).
- `merge_many()` (confirmed lines 1035-1160+): add accumulator seed
  `new_clan_updates = list(self.clan_updates)` immediately after
  `new_faction_updates = list(self.faction_updates)` (confirmed line 1082); add extend-skipping-noop
  `new_clan_updates.extend(cu for cu in other.clan_updates if not cu.is_noop())` immediately after
  the `new_faction_updates.extend(...)` block (confirmed lines 1151-1153); add
  `clan_updates=new_clan_updates,` to the final `replace(...)` call immediately after
  `faction_updates=new_faction_updates,` (confirmed line 1216).
**Do NOT touch:** Any other `StateUpdate` field or the dict-keyed merge branches (`entity_updates`,
`node_updates`, etc.) — `clan_updates` is a plain list extension exactly like `faction_updates`,
never a dict-keyed merge (multiple `ClanUpdate`s for the same `clan_id` in one tick are applied
sequentially by `apply.py`, not folded together — same as `faction_updates`).
**Verify:** `test_clan_update_is_noop`, `test_state_update_merge_clan_updates`,
`test_state_update_is_noop_with_clan_updates` (new — Step 6).

### Step 4 — `apply.py` merge block (touch point 6) + `ContractKind.CLAN` + `ReasonCode` additions
**Files:** `src/engine/apply.py`, `src/core/strategic.py`, `src/core/enums.py`
**Change:**
1. `src/engine/apply.py`: immediately after the Faction-merge block (confirmed
   `src/engine/apply.py:351-377`, ending with `new_factions[fu.faction_id] = replace(existing, ...)`),
   add a parallel Clan-merge block:
   ```python
   # Idea 40/M4: Apply clan updates to durable clans dict
   new_clans = dict(getattr(prior_state, "clans", {}))
   for cu in update.clan_updates:
       if cu.is_noop():
           continue
       existing = new_clans.get(cu.clan_id)
       if existing is None:
           existing = ClanState(clan_id=cu.clan_id)
       new_members = (set(existing.member_entity_ids) | set(cu.member_entity_ids_add)) - set(cu.member_entity_ids_remove)
       new_leader = cu.leader_entity_id_set if cu.leader_entity_id_set is not None else existing.leader_entity_id
       new_dissolved = cu.dissolved_tick_set if cu.dissolved_tick_set is not None else existing.dissolved_tick
       new_clans[cu.clan_id] = replace(existing,
           member_entity_ids=tuple(sorted(new_members)),
           leader_entity_id=new_leader,
           dissolved_tick=new_dissolved,
       )
   ```
   Then add `clans=new_clans,` to the `AuthoritativeState(...)` constructor call immediately after
   `factions=new_factions,` (confirmed `src/engine/apply.py:429`). Note: unlike `FactionUpdate`'s
   `tension_level`, `ClanUpdate` has no delta field requiring a `max(0.0, min(1.0, ...))` clamp
   (Anti-Drift: no tension mutation exists in this ticket at all — see Step 3).
2. `src/core/strategic.py`: add `CLAN = "CLAN"` to `ContractKind` (confirmed enum body
   `src/core/strategic.py:73-87`, currently ending `MARRIAGE = "MARRIAGE"` at line 87) — append as
   the new last member.
3. `src/core/enums.py`: add `CLAN_JOIN_ACCEPTED = "clan_join_accepted"` and
   `CLAN_JOIN_DECLINED = "clan_join_declined"` to `ReasonCode` immediately after
   `MARRIAGE_DECLINED = "marriage_declined"` (confirmed `src/core/enums.py:162-163`).
**Do NOT touch:** The Faction-merge block itself (`src/engine/apply.py:351-377`) — read it for the
pattern, do not reorder or modify its lines; the Clan block is a new, separate block placed after
it. Do not touch any other `ContractKind`/`ReasonCode` member.
**Verify:** `test_faction_update_apply_tension_delta` and the other 8
`test_faction_state.py` tests (regression — proves the adjacent Faction block wasn't disturbed);
new `test_clan_state_persists_across_ticks`, `test_clan_update_membership_add_remove` (Step 6).

### Step 5 — `SocialAppraisalSystem._appraise_clan()` dispatch branch
**Files:** `src/systems/social_systems/appraisal.py`
**Change:** Add a new dispatch branch in `appraise_contract()`'s `if`/`elif` chain (confirmed
`src/systems/social_systems/appraisal.py:57-87`) immediately after the `MARRIAGE` branch (confirmed
lines 84-85):
```python
elif contract.kind == ContractKind.CLAN:
    return SocialAppraisalSystem._appraise_clan(entity, contract, trust_score)
```
And a new method immediately after `_appraise_marriage` (confirmed lines 343-354):
```python
@staticmethod
def _appraise_clan(
    entity: EntityState,
    contract: ContractState,
    trust_score: float
) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
    """The shared prelude (trust<0.2, sentiment<-0.8, betrayal-history, appraisal.py:47-54)
    already expresses the entire trust gate this contract kind uses; reaching this method means
    the prelude already passed, so it always accepts. Mirrors _appraise_teach/_appraise_marriage's
    prelude-only shape (lines 333-354) exactly -- no utility/risk model or tension-level gate is
    added here; any ClanState.tension_level interaction beyond this shared prelude is idea 68
    (Inter-Clan Relations) scope, explicitly out of scope for this ticket."""
    return ContractStatus.ACCEPTED, ReasonCode.CLAN_JOIN_ACCEPTED, {}
```
The entity that appraises a Clan-join offer is the target Clan's `leader_entity_id` (the "target
appraises the source" direction confirmed via `execute_propose_marriage`,
`src/engine/domain/core_actions.py:437`) — this is decided and implemented in Step 6's
`execute_join_clan`, not in this file.
**Do NOT touch:** Lines 47-54 (the shared trust hard-cancel prelude) — confirmed unmodified by
direct read requirement (AC 3, explicit). Do NOT touch `_appraise_recruitment` or route `CLAN`
through it — `RECRUITMENT`'s utility/pay model is a different contract shape entirely (`terms` has
no `daily_pay`/`risk_level` for Clan joining).
**Verify:** `test_clan_join_routes_through_appraise_contract`,
`test_clan_join_shared_trust_prelude_still_cancels` (new, `tests/unit/social/test_clan_appraisal.py`
— Step 8); `test_appraisal_logic.py` (full file, regression — proves the prelude and other
`ContractKind` branches are untouched).

### Step 6 — Replace the stale `test_clan_state_does_not_touch_authoritative_state` + add wiring tests
**Files:** `tests/unit/domains/faction/test_clan_state.py`
**Change:** Delete `test_clan_state_does_not_touch_authoritative_state`
(`tests/unit/domains/faction/test_clan_state.py:70-75`, confirmed substring-check that will now be
false by construction) and replace it with a positive wiring assertion, mirroring
`test_faction_state.py::test_authoritative_state_has_factions_field` (lines 43-58):
```python
def test_clan_state_is_wired_into_authoritative_state():
    from src.core.state import AuthoritativeState, ClanState
    from src.core.updates import StateUpdate

    state = AuthoritativeState(tick=0, seed=0)
    assert hasattr(state, "clans")
    assert state.clans == {}
    field_names = {f.name for f in dataclasses.fields(AuthoritativeState)}
    assert "clans" in field_names

    update_field_names = {f.name for f in dataclasses.fields(StateUpdate)}
    assert "clan_updates" in update_field_names

    state2 = AuthoritativeState(tick=1, seed=0, clans={"x": ClanState(clan_id="x")})
    assert state2.clans["x"].clan_id == "x"
```
Also add, in the same file, mirroring `test_faction_state.py` 1:1 for the 6 touch points:
`test_authoritative_state_has_clans_field`, `test_clan_update_is_noop`,
`test_clan_update_membership_add_remove` (add-and-remove-in-one-update, mirrors
`test_faction_update_territory_add_remove`), `test_state_update_merge_clan_updates`,
`test_state_update_is_noop_with_clan_updates`, `test_clan_state_persists_across_ticks` (via
`ApplyPath.apply_generation`, mirrors `test_faction_state_factions_persist_across_ticks`), plus
Step 1's `test_clan_state_asset_ids_round_trip`. Also add `test_clan_state_is_frozen` coverage for
the new field (assign `AuthoritativeState.clans` directly → `FrozenInstanceError`) if not already
implied by the existing frozen test.
**Do NOT touch:** `test_clan_state_serialization_round_trip`,
`test_clan_state_serialization_round_trip_defaults`, `test_clan_state_is_frozen`,
`test_clan_state_canonical_dict_is_sorted_and_deterministic`,
`test_clan_state_does_not_share_faction_state_identity` — all five keep passing unmodified (only
extend defaults checks if the new `asset_ids` field needs an assertion added to the *existing*
round-trip tests rather than a new test — implementer's call, either is acceptable as long as no
existing assertion is weakened).
**Verify:** `pytest tests/unit/domains/faction/test_clan_state.py -x -v` — all pass, including the
new wiring tests. This step directly satisfies AC 6.

### Step 7 — `ClanLifecycleService` (pure logic: succession, dissolution, leave)
**Files:** `src/systems/social_systems/clan_lifecycle.py` (new), `src/observability/events.py`
**Change:** New module, pure static methods, no imports from `party_lifecycle.py` or `groups.py`
(Anti-Drift — built fresh, per ticket framing and investigation's confirmation that
`check_leadership()` operates on `GroupRecord`/`group.member_ids`, not `ClanState`):
```python
class ClanLifecycleService:
    @staticmethod
    def process_leave(clan_id: str, entity_id: int, tick: int) -> Tuple["ClanUpdate", "ClanMemberLeftEvent"]:
        """Unconditional -- no appraise_contract() gate (AC 4 does not require one; only
        joining, AC 3, requires appraisal). Returns the typed ClanUpdate removing entity_id
        from member_entity_ids and the Clan-specific event. Never mutates ClanState directly."""
        ...

    @staticmethod
    def process_succession(
        clan: "ClanState",
        members: List["EntityState"],
        current_update: Optional["StateUpdate"],
        tick: int,
    ) -> Tuple[Optional["ClanUpdate"], Optional["ClanSuccessionEvent"]]:
        """No 0.2-margin gate (contrast SOC-228, party_lifecycle.py:94) -- promotes immediately
        whenever the leader is dead/inactive/None and at least one scoreable member exists.
        Leader liveness uses the same same-tick-effective-state pattern as
        GroupSystem.update_groups()'s is_alive/is_active (groups.py:32-57) -- re-implemented
        locally here (reading current_update.entity_updates before falling back to member
        EntityState.combat.alive/lifecycle.active), NOT imported from groups.py, to avoid any
        accidental coupling between Group and Clan lifecycle code (Anti-Drift Hazard). Tiebreak:
        lowest entity id, mirroring party_lifecycle.py:88-91's tiebreak convention (the tiebreak
        rule is reused as a numeric convention, not as a function call/import). Returns
        (None, None) when the leader is alive/active, and (None, None) when the leader is
        dead/None but no scoreable members remain (defers to process_dissolution)."""
        ...

    @staticmethod
    def process_dissolution(clan: "ClanState", tick: int) -> Optional["ClanUpdate"]:
        """Sets dissolved_tick only when member_entity_ids AND asset_ids are BOTH empty
        (AC 2). Reads clan.member_entity_ids/asset_ids as given by the caller -- this ticket's
        ClanLifecyclePhase (Step 8) passes the start-of-tick state.clans snapshot, so a clan
        whose last member leaves this same tick dissolves on the FOLLOWING tick's pass, the
        same one-tick-lag design already used by FactionAwarenessService
        (src/engine/pipeline.py:233-234's own comment: 'one-tick lag is inherent (state
        frozen)') -- not a new pattern. Returns None if already dissolved or not eligible."""
        ...
```
In `src/observability/events.py`, add two new frozen `SimulationEvent` subclasses immediately
after `BetrayalDesertionEvent` (confirmed `src/observability/events.py:302-343+`), following its
exact shape (`event_category="social"`, custom `__init__` building a default `message`,
`source_system="clan_lifecycle_service"`):
- `ClanMemberLeftEvent(clan_id: str, entity_id: int, ...)` — `event_type="clan_member_left"`.
- `ClanSuccessionEvent(clan_id: str, old_leader_id: Optional[int], new_leader_id: int, ...)` —
  `event_type="clan_succession"`.
**Do NOT touch:** `PartyLifecycleService.check_leadership()`
(`src/systems/social_systems/party_lifecycle.py:43-119`) or `GroupSystem.update_groups()`
(`src/systems/world_systems/groups.py:19-108`) — confirmed untouched by this step; no shared
helper extraction between them and the new service (Anti-Drift Hazard, explicit).
**Verify:** `test_clan_succession_promotes_highest_sociability_on_leader_death`,
`test_clan_succession_lowest_id_tiebreak_on_equal_sociability`,
`test_clan_succession_no_promotion_when_leader_alive`,
`test_clan_succession_same_tick_death_effective_state`,
`test_clan_succession_no_surviving_members_defers_to_dissolution_check` (all in new
`tests/unit/domains/faction/test_clan_succession.py`); `test_clan_dissolves_when_members_and_assets_both_empty`,
`test_clan_does_not_dissolve_when_only_members_empty`,
`test_clan_does_not_dissolve_when_only_assets_empty` (same file); `test_clan_leave_removes_entity_via_clan_update`,
`test_clan_leave_emits_clan_specific_event`, `test_clan_leave_never_mutates_clan_state_directly`
(new `tests/unit/domains/faction/test_clan_lifecycle.py`).

### Step 8 — `CoreActions.execute_join_clan`/`execute_leave_clan` + action dispatch + `ClanLifecyclePhase`
**Files:** `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`,
`src/engine/pipeline_phases/clan_lifecycle.py` (new), `src/engine/pipeline.py`
**Change:**
1. **`core_actions.py`** — add `execute_join_clan` immediately after `execute_propose_marriage`
   (confirmed `src/engine/domain/core_actions.py:400-466`), following its structure closely but
   note the key divergence documented in this plan's Summary: `Dict[int, EntityUpdate]` cannot
   itself carry a `ClanUpdate`, so this handler's only job is the appraisal decision and legality
   signaling — the durable membership write happens in `ClanLifecyclePhase` (below), *not* here.
   ```python
   @staticmethod
   def execute_join_clan(entity, payload, current_tick, neighbor_view, context) -> Dict[int, EntityUpdate]:
       clan_id = payload.get("clan_id")
       clan = context.clans.get(clan_id) if context and hasattr(context, "clans") else None
       if not clan or clan.dissolved_tick is not None:
           return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND"))}
       if entity.id in clan.member_entity_ids:
           return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="ALREADY_MEMBER"))}
       leader = context.entities.get(clan.leader_entity_id) if clan.leader_entity_id is not None else None
       if leader is None:
           return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason=ReasonCode.TARGET_INVALID.value))}
       from src.systems.social_systems.appraisal import SocialAppraisalSystem
       from src.core.strategic import ContractState, ContractKind, ContractStatus
       temp_contract = ContractState(
           id=f"clan_join_{entity.id}_{clan_id}_{current_tick}", kind=ContractKind.CLAN,
           source_id=entity.id, target_id=leader.id, terms={"clan_id": clan_id},
           status=ContractStatus.OFFERED, created_tick=current_tick,
       )
       status, reason, _ = SocialAppraisalSystem.appraise_contract(leader, temp_contract, context)
       if status == ContractStatus.ACCEPTED:
           return {entity.id: EntityUpdate(entity_id=entity.id)}  # SUCCESS outcome auto-annotated by ActionRoutingPhase
       return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason=reason.value))}
   ```
   `"ALREADY_MEMBER"`/`"TARGET_NOT_FOUND"` follow the exact string-literal `failure_reason`
   convention already used at `core_actions.py:421` (`"TARGET_NOT_FOUND"`) — not new `ReasonCode`
   members, since `NavigationUpdate.failure_reason` is confirmed to accept bare strings there too.
   Add `execute_leave_clan` similarly (no appraisal call — AC 4 does not require one):
   ```python
   @staticmethod
   def execute_leave_clan(entity, payload, current_tick, neighbor_view, context) -> Dict[int, EntityUpdate]:
       clan_id = payload.get("clan_id")
       clan = context.clans.get(clan_id) if context and hasattr(context, "clans") else None
       if not clan or entity.id not in clan.member_entity_ids:
           return {entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="NOT_A_MEMBER"))}
       return {entity.id: EntityUpdate(entity_id=entity.id)}  # SUCCESS outcome auto-annotated
   ```
   Both rely on `ActionRoutingPhase.route()`'s existing outcome-annotation
   (`src/engine/pipeline_phases/actions.py:190-244`, confirmed by direct read: an `EntityUpdate`
   with no `navigation.failure_reason` and no `combat.outcome_kind=="REJECTED"` defaults to
   `outcome="SUCCESS"` at line 191, and `annotated_task` at line 244 folds the *original* action
   payload — including `clan_id` — plus `outcome` into `update.entity_updates[eid].task.payload_set`
   automatically). No manual `task=` field is set in either handler (confirmed unnecessary: any
   `task` field these handlers might return for the actor's own `eid` is overwritten anyway by
   `ActionRoutingPhase`'s `merged = replace(merged, task=annotated_task)` at line 250).
2. **`action_router.py`** — add two dispatch lines immediately after the `PROPOSE_MARRIAGE` branch
   (confirmed `src/engine/domain/action_router.py:61-62`):
   ```python
   if action == "JOIN_CLAN":
       return CoreActions.execute_join_clan(entity, payload, current_tick, neighbor_view, context)
   if action == "LEAVE_CLAN":
       return CoreActions.execute_leave_clan(entity, payload, current_tick, neighbor_view, context)
   ```
3. **New `src/engine/pipeline_phases/clan_lifecycle.py`** (`ClanLifecyclePhase`, thin wrapper
   mirroring `GroupPhase`'s structure — `src/engine/pipeline_phases/groups.py:1-40`), single method
   `resolve(state, update) -> StateUpdate`:
   - **Sub-step A (membership from action outcomes):** scan `update.entity_updates` for entities
     whose `task.payload_set` has `action in ("JOIN_CLAN", "LEAVE_CLAN")` and `outcome == "SUCCESS"`
     (this payload shape is guaranteed present after the `action_routing` phase, which runs at
     `src/engine/pipeline.py:286` — confirmed to run well before this new phase's insertion point
     at line 391+, so scanning here is safe). For each: build a `ClanUpdate(clan_id=payload["clan_id"],
     member_entity_ids_add=(eid,))` (JOIN) or `member_entity_ids_remove=(eid,)` (LEAVE, via
     `ClanLifecycleService.process_leave`, which also yields the `ClanMemberLeftEvent`).
   - **Sub-step B (succession + dissolution):** for each `clan_id, clan in state.clans.items()`,
     call `ClanLifecycleService.process_succession(clan, members, update, state.tick)` (members =
     `[state.entities[eid] for eid in clan.member_entity_ids if eid in state.entities]`) then
     `ClanLifecycleService.process_dissolution(clan, state.tick)`, appending any non-`None`
     `ClanUpdate`s.
   - Accumulate succession/leave events into a class-level buffer
     `ClanLifecyclePhase.last_tick_events: List[Union[ClanMemberLeftEvent, ClanSuccessionEvent]] = []`,
     cleared at the start of each `resolve()` call — mirroring `GroupPhase.last_tick_events`'s
     *structure* (`src/engine/pipeline_phases/groups.py:21-25,34-35`) for consistency with the
     existing precedent. Note for the implementer (do not "fix" this, out of scope): a repo-wide
     grep confirms `GroupPhase.last_tick_events`/`last_tick_defection_events` are written but never
     read anywhere else in `src/` — `kernel.py`'s actual event dispatch (`generated_events`,
     `src/engine/kernel.py:1000-1097`) does not consume them. This ticket does not need to close
     that gap; tests (Step 7) assert on `ClanLifecycleService.process_leave`/`process_succession`'s
     *direct return values*, exactly as `test_party_lifecycle.py` asserts on
     `PartyLifecycleService.check_leadership()`'s direct return (confirmed,
     `tests/unit/social/test_party_lifecycle.py:68-77`) — never through the kernel.
   - Return `update.merge(StateUpdate(clan_updates=all_new_clan_updates))`.
4. **`pipeline.py`** — add one new `run_phase` call immediately after the `groups` phase (confirmed
   `src/engine/pipeline.py:391`, before `active_contracts` at line 395):
   ```python
   update = run_phase("clan_lifecycle", update, lambda u: AuthoritativeApplyPipeline._resolve_clan_lifecycle(state, u))
   ```
   plus a matching `_resolve_clan_lifecycle` static method (mirrors `_resolve_groups`,
   `src/engine/pipeline.py:449-455`) that imports and calls `ClanLifecyclePhase.resolve(state, u)`.
   This placement is deliberate: `action_routing` (line 286, produces the SUCCESS/FAILURE task
   outcomes Sub-step A reads) and `lifecycle`/`combat_engagement` (lines 389/304, produce the
   same-tick `combat.alive_set=False` Sub-step B's succession check needs) both run earlier in the
   same tick — confirmed by reading the full `run_phase(...)` call sequence in `pipeline.py`.
**Do NOT touch:** `ActionRouter.execute_action`'s return-type contract (`Dict[int, EntityUpdate]`,
confirmed `action_router.py:20-27`) — do not widen it to `StateUpdate` for any action; that would
be a much larger, unbounded-blast-radius change affecting every existing action handler, not
scoped to this ticket. Do not touch `_resolve_groups`/`GroupPhase.resolve` itself.
**Verify:** `test_clan_join_never_silently_auto_composes` (architecture guard, new
`tests/unit/social/test_clan_appraisal.py`); `test_clan_leave_removes_entity_via_clan_update`
(Step 7); full `pytest tests/unit/social/ tests/unit/domains/faction/ -x -v` regression pass.

### Step 9 — `intentional_divergences.md` §2.48 DEFERRED → RATIFIED
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** In §2.48 (confirmed `docs/guidelines/intentional_divergences.md:1399-1426`): update the
`**Verification**:` field (currently pointing only at
`test_clan_state_does_not_touch_authoritative_state`, line 1416) to name the real landed test
paths — `tests/unit/domains/faction/test_clan_succession.py` (succession logic) and
`tests/unit/domains/faction/test_clan_state.py::test_clan_state_is_wired_into_authoritative_state`
(wiring) — and flip `**Status**: DEFERRED` (line 1426) to `**Status**: RATIFIED`.
**Do NOT touch:** Any other numbered entry in this file (e.g. §2.49 immediately below, confirmed
unrelated — `class_id_set`/progression).
**Verify:** Doc-diff review (not pytest-checkable); `done-checker`'s doc-coverage condition.

### Step 10 — New Mechanics Bible §9 "Clan Lifecycle Law"
**Files:** `docs/mechanics/04_strategic_cognition.md`
**Change:** Add a new numbered section 9 (file's current highest section is "8. Marriage Proposal
Law" — confirmed by investigation's direct read), reusing §8's exact subsection shape (Gate /
Direction / Durable record / Out of scope / Source). Content must state, precisely:
- **Gate**: shared trust hard-cancel prelude only (`appraisal.py:47-54`), same as Marriage/Teach —
  no additional utility/risk model for joining.
- **Direction**: target (the Clan's `leader_entity_id`) appraises the source (the joining entity),
  same direction as `execute_propose_marriage`.
- **Durable record**: joining/leaving write a `ClanUpdate` into `StateUpdate.clan_updates`
  (registry-keyed by `clan_id`, mirroring `FactionUpdate`), *not* an `EntityUpdate.strategic`
  record (contrast Marriage, which is per-entity).
- **Succession**: no 0.2 sociability-margin gate (explicitly contrasted with Group's
  `PartyLifecycleService.check_leadership()`/SOC-228) — promotion fires immediately on
  leader death/inactivity whenever at least one scoreable member remains; lowest-id tiebreak.
- **Dissolution**: `dissolved_tick` set only when `member_entity_ids` AND `asset_ids` are both
  empty simultaneously; one-tick lag (same class as `FactionAwarenessService`'s documented lag).
- **Out of scope**: idea 68 (Inter-Clan Relations / `tension_level` interactions), asset-granting
  mechanics, clan founding/creation.
- **Source**: cite `src/systems/social_systems/clan_lifecycle.py`,
  `src/engine/pipeline_phases/clan_lifecycle.py`, `src/engine/domain/core_actions.py`
  (`execute_join_clan`/`execute_leave_clan`), SOC-263.
**Do NOT touch:** §8 Marriage Proposal Law itself, or any other numbered section.
**Verify:** Doc-diff review; cross-checked against SOC-263 (Step 11) for wording parity.

### Step 11 — New parity ledger entry SOC-263
**Files:** `docs/parity_ledger/social_narrative.yaml`
**Change:** Append a new entry after the last existing entry in the file (confirmed highest
existing id is `SOC-262`, ending at `docs/parity_ledger/social_narrative.yaml:3900`), `id: SOC-263`,
following the `SOC-228`/`SOC-262` entries' prose style (verified-logic-ID + emitted-event +
affected-file summary):
```yaml
- id: SOC-263
  text: 'ClanState is wired into AuthoritativeState/StateUpdate/apply.py for the first time
    (idea 40/M4): joining routes through SocialAppraisalSystem.appraise_contract() via a new
    ContractKind.CLAN branch (target Clan leader appraises joining entity, shared trust prelude
    unmodified); leaving and succession write typed ClanUpdate records only, never direct
    ClanState mutation. Succession (ClanLifecycleService.process_succession) promotes the
    highest-sociability surviving member to leader_entity_id immediately on leader death/
    inactivity, with NO 0.2 sociability-margin gate -- an intentional divergence from Group''s
    PartyLifecycleService.check_leadership() (SOC-228), which this entry does not modify.
    Dissolution (process_dissolution) sets dissolved_tick only when member_entity_ids AND the
    new ClanState.asset_ids field are both empty simultaneously.'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/core/state.py (ClanState.asset_ids, AuthoritativeState.clans); src/core/updates.py
    (ClanUpdate, StateUpdate.clan_updates); src/engine/apply.py (clan-merge block); src/core/strategic.py
    (ContractKind.CLAN); src/systems/social_systems/appraisal.py (_appraise_clan); src/systems/social_systems/clan_lifecycle.py
    (ClanLifecycleService); src/engine/pipeline_phases/clan_lifecycle.py (ClanLifecyclePhase);
    src/engine/domain/core_actions.py (execute_join_clan/execute_leave_clan); src/observability/events.py
    (ClanMemberLeftEvent, ClanSuccessionEvent). (TCK-20260903-CLAN-LIFECYCLE-SUCCESSION)
  proof_type: parity
  test_path: 'pytest tests/unit/domains/faction/test_clan_state.py tests/unit/domains/faction/test_clan_succession.py
    tests/unit/domains/faction/test_clan_lifecycle.py tests/unit/social/test_clan_appraisal.py -x -v'
  divergence_note: 'Succession has no 0.2 sociability-margin gate (contrast SOC-228, Group''s
    check_leadership()); Group''s unconditional dead-leader dissolution (SOC-176/SOC-189) is
    unmodified and does not apply to Clan.'
  support_boundary: null
```
**Do NOT touch:** `SOC-228`, `SOC-230`, `SOC-256`, `SOC-262` — byte-identical, confirmed by
investigation's direct read; this is a brand-new entry, never an edit to an existing one.
**Verify:** `docs/parity_ledger/schema.json` validation (id pattern `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`,
`status: verified` requires non-null `v2_evidence`+`test_path` — both present above); the
`test_path` command must actually pass before this entry is added at `status: verified`.

## Scope Guards

- Do **not** modify `PartyLifecycleService.check_leadership()` (`party_lifecycle.py:43-119`) or add
  any `clan: bool` flag / shared-helper coupling to it. Group's SOC-228 margin gate stays verbatim.
- Do **not** modify `GroupSystem.update_groups()`'s dead-leader dissolution branch
  (`groups.py:93-108`, SOC-176/SOC-189). Group's unconditional dissolution stays verbatim.
- Do **not** touch the shared trust hard-cancel prelude (`appraisal.py:47-54`).
- Do **not** add any inter-clan diplomacy/alliance/war-adjacent field or logic
  (`ClanState.tension_level` stays unread/unwritten by this ticket — idea 68 is fully out of
  scope).
- Do **not** add a `ClanUpdate` mutator for `asset_ids` (`asset_ids_add`/`asset_ids_remove`) — no
  asset-granting mechanic exists in this ticket's scope; only the field + dissolution-read exist.
- Do **not** add Clan founding/creation logic — clans are pre-existing (schema ticket delivered
  the shape; tests construct `ClanState` directly for fixtures, same as `FactionState` tests do).
- Do **not** widen `ActionRouter.execute_action`'s `Dict[int, EntityUpdate]` return contract to
  `StateUpdate` for any action, Clan-related or otherwise.
- Do **not** conflate this ticket's Clan leadership succession with
  `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s personal inheritance/heir assignment — unrelated durable
  state, keep all new doc/comment language unambiguous about which "succession" is meant.
- Do **not** edit `SOC-228`, `SOC-230`, `SOC-256`, or `SOC-262` in the parity ledger — SOC-263 is a
  new, separate entry.
- Do **not** attempt to fix `GroupPhase.last_tick_events`'s apparent disconnection from
  `kernel.py`'s real event dispatch — pre-existing, out of scope; mirror its *structure* for
  `ClanLifecyclePhase` without trying to repair the gap.

## Dependency Map

- Step 1 (schema field) has no dependents that block it — it's a pure schema addition.
- Step 2 (AuthoritativeState wiring) depends on Step 1 (needs `ClanState` in its final shape).
- Step 3 (StateUpdate/ClanUpdate) is independent of Steps 1–2; can be done in parallel.
- Step 4 (apply.py + ContractKind + ReasonCode) depends on Steps 1–3 (needs `ClanState`,
  `ClanUpdate`, `StateUpdate.clan_updates` to all exist).
- Step 5 (`_appraise_clan`) depends on Step 4 (`ContractKind.CLAN`, `ReasonCode.CLAN_JOIN_ACCEPTED`).
- Step 6 (test replacement) depends on Steps 2–3 (the fields it asserts on must exist).
- Step 7 (`ClanLifecycleService` + events) depends on Step 1 (`asset_ids`), Step 3 (`ClanUpdate`).
- Step 8 (action handlers + phase wiring) depends on Steps 4–5 (`ContractKind.CLAN`,
  `_appraise_clan`) and Step 7 (`ClanLifecycleService`, event classes).
- Steps 9–11 (docs/parity) depend on Steps 1–8 being implemented and their tests passing (the
  `test_path`/`Verification` fields must name real, passing tests).
- Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 (matches the
  numbering above; each step is independently verifiable before the next begins).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1 — dead/inactive leader → highest-sociability promotion, no 0.2 margin gate | Step 7 (`ClanLifecycleService.process_succession`), Step 8 (phase wiring/placement) | `test_clan_succession_promotes_highest_sociability_on_leader_death`, `test_clan_succession_lowest_id_tiebreak_on_equal_sociability`, `test_clan_succession_no_promotion_when_leader_alive`, `test_clan_succession_same_tick_death_effective_state`, `test_clan_succession_no_surviving_members_defers_to_dissolution_check` |
| AC 2 — dissolved_tick set only when member_entity_ids AND asset measure both empty | Step 1 (`asset_ids` field), Step 7 (`process_dissolution`) | `test_clan_dissolves_when_members_and_assets_both_empty`, `test_clan_does_not_dissolve_when_only_members_empty`, `test_clan_does_not_dissolve_when_only_assets_empty` |
| AC 3 — joining routes through `appraise_contract()`, prelude unmodified | Step 5 (`_appraise_clan` dispatch), Step 8 (`execute_join_clan`) | `test_clan_join_routes_through_appraise_contract`, `test_clan_join_shared_trust_prelude_still_cancels`, `test_clan_join_never_silently_auto_composes` |
| AC 4 — leaving removes member via typed `ClanUpdate`, emits Clan-specific event | Step 7 (`process_leave`, event classes), Step 8 (`execute_leave_clan`, phase Sub-step A) | `test_clan_leave_removes_entity_via_clan_update`, `test_clan_leave_emits_clan_specific_event`, `test_clan_leave_never_mutates_clan_state_directly` |
| AC 5 — `intentional_divergences.md` §2.48 Verification updated + Status RATIFIED | Step 9 | Doc-diff review; `done-checker` doc-coverage condition |
| AC 6 — `test_clan_state_does_not_touch_authoritative_state` replaced | Step 6 | `pytest tests/unit/domains/faction/test_clan_state.py -x -v` |
| AC 7 — new dedicated parity ledger entry, distinct from SOC-166/228/230/256 | Step 11 | `docs/parity_ledger/schema.json` validation; SOC-263's own `test_path` |

## Anti-Drift Notes

- **SOC-228 stays Group-only, verbatim.** Any temptation to add a `clan_mode` parameter to
  `PartyLifecycleService.check_leadership()` "to reuse the tiebreak logic" must be resisted — the
  tiebreak *convention* (lowest id) is reused as a numeric rule, never as a function call/import.
  `ClanLifecycleService` must have zero import dependency on `party_lifecycle.py` or `groups.py`
  (verify via `test_clan_lifecycle_service_does_not_import_group_lifecycle`, an architecture-guard
  test suggested by test_plan.md's Anti-Drift Test Guards section).
- **`asset_ids` is read-only in this ticket.** No `ClanUpdate` field, no service, no action writes
  it. If review or a future agent is tempted to "complete the feature" by adding an asset-granting
  mechanic in this same ticket, that is out of scope — flag it as a follow-up ticket idea instead.
- **The one-tick dissolution lag is intentional, not a bug** — `process_dissolution` reads the
  start-of-tick `state.clans` snapshot, so a clan whose last member leaves this tick dissolves next
  tick. This mirrors `FactionAwarenessService`'s already-documented one-tick lag
  (`pipeline.py:233-234`'s own comment) — do not "fix" it by threading `update.clan_updates`
  same-tick folding into the dissolution check; that adds real complexity for a lag class this
  codebase already accepts elsewhere.
- **`ClanLifecyclePhase.last_tick_events` mirrors a structurally pre-existing gap
  (`GroupPhase.last_tick_events`/`last_tick_defection_events` are confirmed never read by
  `kernel.py`'s real event dispatch).** Do not spend implementation effort trying to wire Clan
  events into `kernel.py`'s `generated_events`/`_event_listeners` — that would be scope creep onto
  a pre-existing, unrelated gap. Tests assert on service-function return values directly.
- **`Dict[int, EntityUpdate]` is a hard contract boundary** for every `ActionRouter`/`CoreActions`
  handler, confirmed by direct read of `action_router.py:20-27` and the per-actor merge loop at
  `actions.py:246-251`. `execute_join_clan`/`execute_leave_clan` must never attempt to smuggle a
  `ClanUpdate`/`StateUpdate` through this return type — the split between "action handler decides
  ACCEPTED/CANCELLED" and "`ClanLifecyclePhase` commits the registry write" is the whole point of
  this design, not an accident to "simplify away."
- **Do not conflate "succession" with `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s heir/inheritance
  system** — different durable state (`ClanState.leader_entity_id` vs. that ticket's heir field),
  unrelated mechanics. Keep §9's Mechanics Bible language and SOC-263's text unambiguous.
- **`tension_level` stays fully unwired by this ticket** — it exists on `ClanState` today (from the
  schema ticket) but nothing in Steps 1–11 reads or writes it. A new test
  (`test_clan_state_no_new_idea68_fields`, suggested by test_plan.md) should assert the `ClanState`/
  `ClanUpdate` field sets are exactly what this plan specifies, no more — guards against silent
  idea-68 scope creep in a later drive-by edit.

## Deviations (recorded during Implement)

- **Step 10 — Mechanics Bible section number: §9 → §10.** This plan's Step 10 assumed the file's
  current highest section was "8. Marriage Proposal Law" (true when the plan was written). By the
  time Implement ran, a different, unrelated ticket had already landed a real "## 9. Coming of Age
  Archetype-Choice Roll (idea 34, STRAT-267)" section in
  `docs/mechanics/04_strategic_cognition.md`, so `## 9.` was no longer free. The new Clan Lifecycle
  Law section was added as **`## 10.`** instead, immediately after §9, with the exact same
  subsection shape (Gate/Direction/Durable record/Succession/Dissolution/Out of scope/Source) §8
  specifies. No other part of Step 10's content requirements changed. SOC-263's parity ledger text
  (Step 11) and `tickets/inprogress/TCK-20260903-CLAN-LIFECYCLE-SUCCESSION.md`'s Implementation
  Notes both reference "§10", not "§9", for consistency.
