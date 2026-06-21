# Plan — TCK-20260619-E41D-DEFECTION-ESCORT

## Overview
Implement defection mechanics (check_defection in PartyLifecycleService) and escort route-scoring in AdventureRouteScorer. Wire defection pass into GroupPhase. Add BetrayalDesertionEvent. Add PROTECT_TARGET + OWN_SURVIVAL RouteFamily members. Create party_contract.md doc.

## Steps

### Step 1 — src/domains/adventure/schema.py
Add two RouteFamily enum members:
```python
PROTECT_TARGET = "protect_target"
OWN_SURVIVAL = "own_survival"
```

### Step 2 — src/observability/events.py
Add `BetrayalDesertionEvent(SimulationEvent)` after `LeadershipChangedEvent`:
- event_type = "betrayal_desertion"
- event_category = "social"
- severity = "WARNING"
- source_system = "party_lifecycle_service"
- Fields: group_id, grievance_count (stored in payload)
- Factory classmethod `create(tick, group_id, entity_id, grievance_count, remaining_member_ids)`

### Step 3 — src/systems/social_systems/party_lifecycle.py
Add `check_defection(group, entity, tick)` static method to `PartyLifecycleService`:
```
Signature:
  check_defection(
      group: GroupRecord,
      entity: EntityState,
      tick: int,
  ) -> Tuple[Optional[GroupRecord], Optional[BetrayalDesertionEvent], Optional[EntityUpdate]]

Logic:
  1. If len(group.grievance_log) < 3: return (None, None, None)
  2. new_members = group.member_ids - {entity.id}
  3. dissolution = tick if len(new_members) <= 1 else group.dissolution_tick
  4. updated_group = replace(group, member_ids=new_members, dissolution_tick=dissolution, last_updated_tick=tick)
  5. event = BetrayalDesertionEvent.create(tick, group.id, entity.id, len(group.grievance_log), list(new_members))
  6. entity_update = EntityUpdate(entity_id=entity.id, social=SocialUpdate(notoriety_delta=2.0))
  7. return (updated_group, event, entity_update)
```

### Step 4 — src/domains/adventure/scoring.py
Add escort scoring block §9 after class-synergy block §8:
```python
# ── 9. Escort Scoring (SOC-230) ──────────────────────────────────────────
# Applied only when group has an escort_target_id and this entity is NOT the target.
if (
    group is not None
    and group.escort_target_id is not None
    and entity.id != group.escort_target_id
):
    if route.family == RouteFamily.PROTECT_TARGET:
        final_score = round(final_score + 3.0, 4)
    elif route.family == RouteFamily.OWN_SURVIVAL:
        final_score = round(max(0.0, final_score - 1.0), 4)
```

### Step 5 — src/engine/pipeline_phases/groups.py
Add defection pass after the leadership pass (after `GroupPhase.last_tick_events` append for leadership). Iterate all active groups, iterate each member, call `check_defection`. Collect updated groups, events, entity updates. Merge into the running update.

Also expose `last_tick_defection_events: List[BetrayalDesertionEvent] = []` for tests.

### Step 6 — Tests
Append tests to `tests/unit/social/test_party_lifecycle.py` (6 new tests per test plan).

### Step 7 — Parity Ledger
Add SOC-230 to `docs/parity_ledger/social_narrative.yaml`.

### Step 8 — Docs
Create `docs/simulation/domains/party_contract.md`.
Update `docs/mechanics/04_strategic_cognition.md` to mention PROTECT_TARGET and OWN_SURVIVAL route families.
Run `make knowledge-index-update`.

## Architecture Review Checklist
- [x] All durable state via typed records/updates (GroupRecord replace + EntityUpdate.social + groups_add_or_update)
- [x] Determinism: check_defection is a pure function with no side effects
- [x] GroupRecord lifecycle fields from E41A reused (grievance_log, escort_target_id, dissolution_tick) — no new fields added
- [x] BetrayalDesertionEvent follows SimulationEvent pattern (not invented schema)
- [x] RouteFamily additions are additive (no existing values changed)
- [x] notoriety_delta used for reputation penalty (no non-existent reputation_delta dict)
