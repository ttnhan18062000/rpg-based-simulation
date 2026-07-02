# Compliance IDs: SOC-229
"""
src/systems/social_systems/reward_distribution.py
──────────────────────────────────────────────────────────────────────────────
FairShareProtocol — proportional quest reward distribution for party groups.

Ticket: TCK-20260619-E41C-REWARD-DIST
Logic ID: SOC-229

Distribution rule:
  If contribution_log is provided (non-empty), each member receives a share
  proportional to their recorded contribution weight.  If no contributions are
  recorded, an equal split is used (weight 1.0 per member).

  Rounding: int() truncation is applied per member.  The leader absorbs the
  remainder so that sum(shares.values()) == quest_reward always (conservation).

Conservation law:
  Gold moves to members via ResourceTransferIntent.  Direct mutation of entity
  gold is never performed here.  Callers are responsible for merging the
  returned EntityUpdate list into a StateUpdate and routing it through the
  authoritative ResourceTransactionPhase.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from src.core.state import GroupRecord
    from src.core.updates import EntityUpdate


def compute_fair_share(
    group: "GroupRecord",
    quest_reward: int,
    contribution_log: Dict[int, float],
) -> Dict[int, int]:
    """
    Compute per-member gold shares proportional to contribution weights.

    Args:
        group:            The active GroupRecord whose members receive shares.
        quest_reward:     Total gold to distribute (must be >= 0).
        contribution_log: Mapping of entity_id → float weight.  May be empty.
                          Members absent from the log receive weight 1.0 (equal
                          split fallback applies when the log is fully empty).

    Returns:
        Dict mapping each member_id → integer gold share.
        Invariant: sum(result.values()) == quest_reward.
    """
    if quest_reward <= 0:
        return {mid: 0 for mid in group.member_ids}

    member_ids = sorted(group.member_ids)  # deterministic iteration order

    # Build effective weights: use contribution_log value or 1.0 fallback.
    # "Equal split" fires only when the entire log is empty (total==0 after
    # summing real contributions). Individual absent members still get weight 1.0
    # so partial logs work correctly.
    weights: Dict[int, float] = {
        mid: contribution_log.get(mid, 1.0) for mid in member_ids
    }
    total_weight = sum(weights.values())

    if total_weight == 0:
        # Degenerate case: all weights zero — revert to equal split.
        total_weight = float(len(member_ids))
        weights = {mid: 1.0 for mid in member_ids}

    # Compute truncated shares.
    shares: Dict[int, int] = {
        mid: int((weights[mid] / total_weight) * quest_reward)
        for mid in member_ids
    }

    # Conservation: leader absorbs rounding remainder (may be 0 or positive).
    remainder = quest_reward - sum(shares.values())
    shares[group.leader_id] = shares.get(group.leader_id, 0) + remainder

    return shares


def build_reward_transfer_intents(
    shares: Dict[int, int],
    source_id: str,
) -> List["EntityUpdate"]:
    """
    Wrap each member's gold share in a ResourceTransferIntent.

    The returned EntityUpdate objects must be merged into the StateUpdate by
    the caller — this function performs no state mutation.

    Args:
        shares:    Output of compute_fair_share().
        source_id: Identifier for the originating quest / event (used as
                   source_id on the intent and as part of the transaction_id).

    Returns:
        List of EntityUpdate, one per member with gold_delta > 0.
    """
    from src.core.updates import EntityUpdate
    from src.core.update_models.resources import ResourceTransferIntent

    result: List[EntityUpdate] = []
    for member_id in sorted(shares):
        gold = shares[member_id]
        if gold <= 0:
            continue

        intent = ResourceTransferIntent(
            source_id=source_id,
            source_kind="QUEST",
            gold_delta=gold,
            transfer_kind="PARTY_REWARD_SHARE",
            transaction_id=f"party_reward:{source_id}:{member_id}",
            group_id=f"party_reward:{source_id}",
            is_group_required=False,  # per-member splits are independent
        )
        result.append(
            EntityUpdate(
                entity_id=member_id,
                resource_transfers=[intent],
            )
        )

    return result
