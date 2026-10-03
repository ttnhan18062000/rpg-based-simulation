# Investigation — TCK-20260619-E41D-DEFECTION-ESCORT

## Ticket
Epic 4.1D · Defection Mechanics + Escort Behavior

## Context Scan Results

### MCP search_docs
Query: "defection escort group party grievance dissolution"
- `docs/plans/long_term_development_roadmap.md` §Epic 4.1 confirms the defection (betrayal_desertion) and escort (PROTECT_TARGET route) design.
- `docs/audits/D01_rpg_feature_impact.md` §Full Party Adventure Loop — partial; dissolution events part of lifecycle.
- `docs/logic_checklist_exhaustive.md` §Group coordination — checks for party lifecycle events.
- `tickets/done/TCK-20260619-E41-PARTY-LOOP.md` — parent epic; confirms threshold ≥ 3 grievances, PROTECT_TARGET +3.0 urgency, OWN_SURVIVAL -1.0 penalty.

### Graphify
Key nodes in community 0:
- `GroupRecord` at `src/core/state.py:L510` — has `grievance_log: Tuple[str, ...]`, `escort_target_id: Optional[int]`, `dissolution_tick: Optional[int]` (all added in E41A). No new fields needed.
- `PartyLifecycleService` at `src/systems/social_systems/party_lifecycle.py` — currently has only `check_leadership()`. Need to add `check_defection()`.
- `AdventureRouteScorer.score()` at `src/domains/adventure/scoring.py` — has class-synergy block §8. Need to add escort scoring block §9.
- `RouteFamily` at `src/domains/adventure/schema.py:L16` — does NOT have `PROTECT_TARGET` or `OWN_SURVIVAL`. Both must be added.
- `SocialUpdate` at `src/core/updates.py:L275` — has `notoriety_delta: float`. The ticket says `reputation_delta={entity_id: -2.0}`. Closest match: `notoriety_delta += 2.0` (increases notoriety = negative reputation). No `reputation_delta` dict field exists; use `notoriety_delta`.
- `StateUpdate` at `src/core/updates.py:L833` — has `groups_add_or_update: List[GroupRecord]` for the updated GroupRecord (member removed).
- `LeadershipChangedEvent` at `src/observability/events.py:L276` — pattern reference for new `BetrayalDesertionEvent`.
- `GroupPhase.resolve()` at `src/engine/pipeline_phases/groups.py` — wires leadership election; will extend to wire defection check.

## Key Findings

### 1. reputation_delta clarification
The ticket says `SocialUpdate(reputation_delta={entity_id: -2.0})`. No such field exists on `SocialUpdate`. The closest matching field is `notoriety_delta: float = 0.0` (increases public notoriety/infamy) which is applied to the defecting entity's EntityUpdate. This is architecturally correct — defection raises notoriety.

### 2. GroupRecord mutation pattern
GroupRecord is frozen. The immutable replace pattern (`dataclasses.replace`) is used throughout (E41A, E41B). The defection removes one member from `group.member_ids` by returning a new GroupRecord with the member removed via `groups_add_or_update`. If the group drops to 0 or 1 members, `dissolution_tick` should be set.

### 3. RouteFamily additions
`PROTECT_TARGET` and `OWN_SURVIVAL` do not exist in `RouteFamily`. Both must be added to `src/domains/adventure/schema.py`.

### 4. Defection guard: only defect non-leader members
The ticket says "remove entity from group.member_ids". We must select which entity defects. The natural approach: the entity with the most grievances (or in a pure-service model, the caller passes the entity). Since `check_defection()` is called per-entity (like `check_leadership()` is called per-group), the group-phase loop should iterate over members and call `check_defection(group, member_entity, tick)`.

### 5. Dissolution threshold
If after defection `len(group.member_ids) <= 1`, set `dissolution_tick = tick` on the updated GroupRecord.

### 6. Integration with GroupPhase
`GroupPhase.resolve()` currently runs the leadership pass over all surviving groups. The defection pass runs after the leadership pass, similarly iterating all active groups, checking each member.

### 7. BetrayalDesertionEvent
A new `SimulationEvent` subclass following the `LeadershipChangedEvent` pattern:
- `event_type = "betrayal_desertion"`
- `event_category = "social"`
- `severity = "WARNING"`
- `source_system = "party_lifecycle_service"`
- `payload`: group_id, grievance_count, remaining_members

## Files to Change
1. `src/domains/adventure/schema.py` — add `PROTECT_TARGET`, `OWN_SURVIVAL` to `RouteFamily`
2. `src/observability/events.py` — add `BetrayalDesertionEvent`
3. `src/systems/social_systems/party_lifecycle.py` — add `check_defection()`
4. `src/domains/adventure/scoring.py` — add escort scoring block §9
5. `src/engine/pipeline_phases/groups.py` — wire defection pass after leadership pass
6. `tests/unit/social/test_party_lifecycle.py` — add 2 acceptance tests + edge cases
7. `docs/parity_ledger/social_narrative.yaml` — add SOC-230
8. `docs/simulation/domains/party_contract.md` — new doc (post-implementation, per ticket)
9. `docs/mechanics/04_strategic_cognition.md` — update route scoring terms

## Architecture Conformance
- All state changes via `dataclasses.replace` and typed updates (GroupRecord → `groups_add_or_update`, entity social → `EntityUpdate.social`)
- No direct writes to `AuthoritativeState`
- Deterministic: defection check is pure function (group, entity, tick) → (new_group | None, event | None, entity_update | None)
- BetrayalDesertionEvent follows existing SimulationEvent pattern
