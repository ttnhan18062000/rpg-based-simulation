# Investigation — TCK-20260619-E41C-REWARD-DIST

## Topic
FairShareProtocol + Class Synergy Bonuses for multi-entity party reward distribution.

## Findings

### 1. GroupRecord.reward_pool exists (E41A)
`src/core/state.py` — `GroupRecord` has `reward_pool: int = 0` added in TCK-20260619-E41A.
`roles: Dict[int, str]` maps entity_id → role string (e.g. "LEADER", "WARRIOR", "MAGE", "VANGUARD").

### 2. Authoritative transfer path
`src/core/update_models/resources.py` — `ResourceTransferIntent(source_kind, gold_delta, transfer_kind)`.
EntityUpdate carries `resource_transfers: List[ResourceTransferIntent]`.
Quest reward system (`src/engine/pipeline_phases/quest_opportunity_rewards.py`) is the canonical pattern:
- Creates a `ResourceTransferIntent(source_kind="QUEST", gold_delta=gold, transfer_kind="QUEST_REWARD")`.
- Appends to the per-entity `EntityUpdate.resource_transfers`.
- Returns via `StateUpdate` — never writes directly to `AuthoritativeState`.

### 3. EntityRole values
`src/core/enums.py`:
- `HERO = 0`, `SHOPKEEPER = 1`, `MONSTER = 2`, `CITIZEN = 3`, `WORKER = 4`, `GUARD = 5`
- No WARRIOR/MAGE at entity level. These are **combat.tactical_role** strings (set in builder).
- GroupRecord.roles maps `entity_id → tactical_role string` ("WARRIOR", "MAGE", "VANGUARD", "LEADER").

### 4. Synergy detection
The scoring.py `score()` method takes `entity: EntityState` (single entity, not group).
Synergy requires group context. The ticket says: detect via `GroupRecord.roles`.
The scorer must accept an optional `group: GroupRecord` parameter to apply synergy multipliers.
- WARRIOR + MAGE together in group.roles.values(): `score *= 1.15` for HUNT_WEAK_ENEMY/combat routes.
- Any member with EntityRole.HERO (entity.identity.role): `score *= 1.10` for QUEST_OPPORTUNITY routes.
  - But since scorer runs per-entity, we check entity's own role + group context.
  - More precisely: if group has a HERO (any EntityRole.HERO member), QUEST routes score ×1.10.
  - Ticket says "HERO + any" → if entity itself is HERO, quest_route_score *= 1.10.

### 5. RouteFamily mapping for synergy
- Combat synergy (WARRIOR+MAGE): apply to `HUNT_WEAK_ENEMY` family (closest to "combat routes").
  The ticket says "combat_route_score" — the `HUNT_WEAK_ENEMY` RouteFamily is the combat route.
- Quest synergy (HERO+any): apply to `QUEST_OPPORTUNITY` family — already handled in scoring.py §QUEST_OPPORTUNITY.
  The synergy adds a 1.10 multiplier on top of the existing benefit calculation.

### 6. Test file location
`tests/unit/social/test_party_lifecycle.py` — existing file for E41B tests. New tests append here per ticket.

### 7. Conservation law compliance
`compute_fair_share()` must be mathematically conservative:
- All rounding remainders go to the leader (per ticket spec).
- Each share maps to one `ResourceTransferIntent(gold_delta=share)` per member.
- Source kind: "QUEST" / transfer_kind: "PARTY_REWARD_SHARE" — consistent with quest reward pattern.

### 8. No existing reward distribution system
`src/systems/social_systems/` contains: appraisal, contracts, group_service, guilds, memory, party, party_lifecycle, relationships, reputation. No `reward_distribution.py` — must be created fresh.

## Architecture Conclusion
- `compute_fair_share()` is pure computation (no state reads, no side effects) — returns `dict[int, int]`.
- `build_reward_transfer_intents()` wraps each share in a `ResourceTransferIntent` and returns per-entity `EntityUpdate` list — also pure.
- Synergy in `AdventureRouteScorer.score()` as optional `group` param — applied after base score, before final rounding.
- No durable state is mutated anywhere in these new functions.
