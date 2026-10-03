# Plan — TCK-20260619-E41C-REWARD-DIST

## Phase: Implement

### File 1 — NEW: `src/systems/social_systems/reward_distribution.py`

Pure computation module. No state mutation.

Functions:
1. `compute_fair_share(group, quest_reward, contribution_log) -> dict[int, int]`
   - proportion = contribution_log[mid] / total (or 1.0/N for equal split)
   - int() truncates; leader receives remainder
   - Conservation: sum == quest_reward always

2. `build_reward_transfer_intents(shares, source_id) -> list[EntityUpdate]`
   - Per member: `EntityUpdate(entity_id=mid, resource_transfers=[ResourceTransferIntent(source_kind="QUEST", gold_delta=share, transfer_kind="PARTY_REWARD_SHARE")])`
   - Returns list of EntityUpdate — caller merges into StateUpdate

### File 2 — MODIFY: `src/domains/adventure/scoring.py`

Add optional `group: Optional[GroupRecord] = None` parameter to `AdventureRouteScorer.score()`.

After step 7 (final_score calculation), apply synergy multipliers:
- If group is not None:
  - `roles_set = set(group.roles.values())`
  - WARRIOR+MAGE synergy: if "WARRIOR" in roles_set and "MAGE" in roles_set and route.family == RouteFamily.HUNT_WEAK_ENEMY: `final_score *= 1.15`
  - HERO synergy: if entity.identity.role == EntityRole.HERO and route.family == RouteFamily.QUEST_OPPORTUNITY: `final_score *= 1.10`
- Re-round after multipliers.

### File 3 — MODIFY: `tests/unit/social/test_party_lifecycle.py`

Append 6 new test functions as planned in test_plan.md.

## Architecture Review Checklist
- [x] No durable state mutated — all returns are new records / intent lists
- [x] Gold goes through ResourceTransferIntent (gold_delta) — conservation law respected
- [x] No raw domain models exposed from API
- [x] Deterministic — no RNG, pure math
- [x] TypedRecord pattern: EntityUpdate with ResourceTransferIntent
