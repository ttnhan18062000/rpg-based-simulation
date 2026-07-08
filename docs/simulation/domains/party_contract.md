---
status: active
layer: simulation
authority: P1
audience: agent
---

# Party Contract — Epic 4.1 Full Party Adventure Loop

**Authority:** P1  
**Layer:** social  
**Tickets:** TCK-20260619-E41A-GROUP-LIFECYCLE, TCK-20260619-E41B-LEADERSHIP, TCK-20260619-E41C-REWARD-DIST, TCK-20260619-E41D-DEFECTION-ESCORT  
**Parity IDs:** SOC-227, SOC-228, SOC-229, SOC-230

---

## Overview

This document describes the full party lifecycle for multi-entity groups in the V2 simulation. A party is represented by a `GroupRecord` (authoritative durable state in `src/core/state.py`). All lifecycle changes are expressed as typed records and updates — no direct state mutation.

---

## 1. GroupRecord Lifecycle Fields

Added in TCK-20260619-E41A-GROUP-LIFECYCLE (SOC-227):

| Field | Type | Purpose |
|---|---|---|
| `formation_tick` | `int` | Tick at which the group was formed |
| `escort_target_id` | `Optional[int]` | Entity ID of the member being escorted (if any) |
| `grievance_log` | `Tuple[str, ...]` | Ordered log of unresolved grievance reason strings |
| `reward_pool` | `int` | Accumulated gold awaiting FairShareProtocol distribution |
| `last_leadership_check_tick` | `int` | Last tick on which a leadership election was evaluated |
| `dissolution_tick` | `Optional[int]` | Tick at which the group dissolved (None if still active) |

All fields have safe immutable defaults for backward compatibility. `to_canonical_dict()` serializes them flat.

---

## 2. Leadership Election

Implemented in `PartyLifecycleService.check_leadership()` (SOC-228).

- **Interval:** Every `LEADERSHIP_CHECK_INTERVAL` (100) ticks.
- **Criterion:** Highest-sociability member (OCEAN trait at `entity.identity.personality.sociability`) beats current leader by ≥ 0.2 → elected.
- **Tiebreaker:** Lowest entity id.
- **Output:** Updated `GroupRecord` (immutable replace) + optional `LeadershipChangedEvent` (category=social, event_type=leadership_changed).
- **Wired in:** `GroupPhase.resolve()` leadership pass (after GroupSystem).

---

## 3. Reward Distribution

Implemented in `src/systems/social_systems/reward_distribution.py` (SOC-229).

- **`compute_fair_share(group, quest_reward, contribution_log)`** — Distributes `quest_reward` gold proportionally to `contribution_log` weights. Equal split fallback (weight=1.0 per member) if log is empty. Leader absorbs rounding remainder. Conservation law: `sum(shares.values()) == quest_reward` always.
- **`build_reward_transfer_intents(shares, source_id)`** — Wraps each share in a `ResourceTransferIntent(source_kind="QUEST", transfer_kind="PARTY_REWARD_SHARE")`. Gold is NEVER mutated directly.

### Class Synergy (SOC-229)

In `AdventureRouteScorer.score()` (block §8), when a group context is present:

| Condition | Route | Effect |
|---|---|---|
| WARRIOR + MAGE both in `group.roles` | `HUNT_WEAK_ENEMY` | final_score × 1.15 |
| Entity is `EntityRole.HERO` | `QUEST_OPPORTUNITY` | final_score × 1.10 |

---

## 4. Defection Mechanics

Implemented in `PartyLifecycleService.check_defection()` (SOC-230).

- **Threshold:** `len(group.grievance_log) >= DEFECTION_GRIEVANCE_THRESHOLD` (3 unresolved grievances).
- **On defection:**
  1. Entity removed from `group.member_ids` via `dataclasses.replace` → `GroupRecord` returned.
  2. `BetrayalDesertionEvent` emitted (event_type=`betrayal_desertion`, category=social, severity=WARNING).
  3. `EntityUpdate(social=SocialUpdate(notoriety_delta=2.0))` applied to defecting entity.
  4. If `len(new_members) <= 1` → `dissolution_tick = tick` set on updated group.
- **Rate:** At most one defection per group per tick (GroupPhase picks first eligible member).
- **Wired in:** `GroupPhase.resolve()` defection pass (after leadership pass).

---

## 5. Escort Behavior

Implemented in `AdventureRouteScorer.score()` (block §9, SOC-230).

Triggered when: `group.escort_target_id is not None` AND `entity.id != group.escort_target_id`.

| Route family | Adjustment |
|---|---|
| `PROTECT_TARGET` | `+3.0` (urgency bonus — protecting the target is the priority) |
| `OWN_SURVIVAL` | `-1.0` (floored to 0.0 — deprioritise self-preservation when escorting) |

The escort target itself is exempt from these adjustments.

### RouteFamily additions

`src/domains/adventure/schema.py RouteFamily`:
- `PROTECT_TARGET = "protect_target"` — route representing guarding/protecting the escort target.
- `OWN_SURVIVAL = "own_survival"` — route representing self-preservation actions.

---

## 6. Authoritative Pipeline Integration

`GroupPhase.resolve()` in `src/engine/pipeline_phases/groups.py` runs three sequential passes:

1. **GroupSystem pass** — Handles position sliding, formation, and existing group mutations.
2. **Leadership election pass (E41B)** — Evaluates sociability-based election for all active groups.
3. **Defection pass (E41D)** — Evaluates grievance threshold for all active groups; fires at most one defection per group per tick.

All outputs accumulate into `StateUpdate` via `groups_add_or_update`, `groups_remove`, and `entity_updates` — never via direct `AuthoritativeState` mutation.

---

## 7. Event Inventory

| Event class | event_type | Trigger |
|---|---|---|
| `LeadershipChangedEvent` | `leadership_changed` | Leadership election fires |
| `BetrayalDesertionEvent` | `betrayal_desertion` | Grievance threshold reached |

Both extend `SimulationEvent` (Pydantic BaseModel). Both are accessible from `GroupPhase.last_tick_events` and `GroupPhase.last_tick_defection_events` respectively for test inspection.

---

## 8. Tests

```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
```

Key acceptance tests:
- `test_leadership_election_picks_highest_sociability` (SOC-228)
- `test_fair_share_protocol_distributes_by_contribution` (SOC-229)
- `test_class_synergy_bonus_applied_to_combat_routes` (SOC-229)
- `test_betrayal_desertion_fires_on_high_grievance` (SOC-230)
- `test_escort_target_route_scores_above_survival` (SOC-230)
