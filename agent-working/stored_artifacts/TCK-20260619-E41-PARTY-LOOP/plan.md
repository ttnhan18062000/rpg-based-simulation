# Plan — TCK-20260619-E41-PARTY-LOOP

## Approach

Extend `GroupRecord` with lifecycle fields. Add `FairShareProtocol` as a pure function. Add class synergy to route scoring. Wire defection and escort mechanics.

## Sequence

**E41A → E41B → E41C → E41D** (strictly sequential; each depends on prior)

---

## E41A · GroupRecord Lifecycle Extension

**File**: `src/core/state.py:L507`

Add optional fields to `GroupRecord` (frozen=True, slots=True means new fields need defaults):

```python
formation_tick: int = 0
escort_target_id: Optional[int] = None       # entity_id of ESCORT_TARGET, if any
grievance_log: Tuple[str, ...] = ()          # immutable event summary strings
reward_pool: int = 0                         # accumulated gold pending distribution
last_leadership_check_tick: int = 0
dissolution_tick: Optional[int] = None       # set when group dissolves
```

Update `to_canonical_dict()` to include new fields.

---

## E41B · Sustained Lifecycle + Leadership Election

**File**: `src/systems/social_systems/` — new `party_lifecycle.py`

```python
class PartyLifecycleService:
    LEADERSHIP_CHECK_INTERVAL = 100  # ticks

    @staticmethod
    def check_leadership(group: GroupRecord, members: list[EntityState], tick: int) -> Optional[GroupUpdate]:
        """Elect new leader if current leader's sociability < max member sociability by 0.2."""
        if tick - group.last_leadership_check_tick < PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL:
            return None
        sociabilities = {e.id: e.personality.sociability for e in members if e.id in group.member_ids}
        current = sociabilities.get(group.leader_id, 0.0)
        best_id = max(sociabilities, key=sociabilities.get)
        if sociabilities[best_id] - current >= 0.2:
            return GroupUpdate(group_id=group.id, new_leader_id=best_id, leadership_changed=True)
        return None

    @staticmethod
    def check_defection(group: GroupRecord, entity: EntityState, tick: int) -> Optional[SocialUpdate]:
        """If grievance score > threshold, entity defects; emit betrayal_desertion event."""
        ...
```

Wire into the social/group phase of the 6-phase kernel loop.

---

## E41C · FairShareProtocol + Class Synergy

**File**: `src/systems/social_systems/reward_distribution.py` (new)

```python
def compute_fair_share(group: GroupRecord, quest_reward: int, contribution_log: dict[int, float]) -> dict[int, int]:
    """
    Distribute quest_reward proportional to each member's contribution_score.
    Falls back to equal split if no contributions recorded.
    """
    total = sum(contribution_log.values()) or len(group.member_ids)
    shares = {}
    remaining = quest_reward
    for member_id in sorted(group.member_ids):
        raw = (contribution_log.get(member_id, 1.0) / total) * quest_reward
        shares[member_id] = int(raw)
        remaining -= int(raw)
    # give remainder to leader
    shares[group.leader_id] = shares.get(group.leader_id, 0) + remaining
    return shares
```

**Class synergy** in `src/domains/adventure/scoring.py`:
- WARRIOR + MAGE in same party: `combat_route_score *= 1.15`
- Two WARRIORs: no bonus
- HERO + any: `quest_route_score *= 1.10`

---

## E41D · Defection + Escort Behavior

**Defection**: in `PartyLifecycleService.check_defection()`:
- Threshold: grievance_score > 3.0 (same scale as nemesis promotion)
- On defection: remove from group.member_ids, emit `betrayal_desertion` SimulationEvent
- Reputation penalty: `SocialUpdate(reputation_delta={entity_id: -2.0})`

**Escort behavior** in `src/domains/adventure/scoring.py`:
- If entity is in a group where `group.escort_target_id` is set and this entity is NOT the target:
  - PROTECT_TARGET route scores +3.0 urgency bonus
  - OWN_SURVIVAL routes score -1.0 urgency penalty
- Add `PROTECT_TARGET` to `RouteFamily` enum if not present

After E41D: create `docs/simulation/domains/party_contract.md`. Run `make knowledge-index-update`.
