from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import EntityUpdate, QuestOpportunityRewardIntent
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import RewardUpdate
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

_log = logging.getLogger(__name__)


class QuestOpportunityRewardSystem:
    """
    Converts QuestOpportunityRewardIntent records into authoritative
    ResourceTransferIntent entries (gold + XP) and emits a QUEST_COMPLETED
    WorldEvent.  Runs inside QuestRewardPhase before ResourceTransactionPhase.
    """

    @staticmethod
    def _emit_terminal_removals(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Remove QuestOpportunity entries whose reward transaction was already
        accepted in a prior tick (transaction_id present in
        state.processed_transaction_ids).
        """
        removals = []
        for q_id in sorted(state.quest_registry):
            txn_id = f"quest:{q_id}:reward"
            if txn_id in state.processed_transaction_ids:
                removals.append(q_id)

        if not removals:
            return update

        return replace(
            update,
            quest_registry_remove=list(update.quest_registry_remove) + removals,
        )

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Process QuestOpportunityRewardIntents: emit ResourceTransferIntents for
        gold/XP delivery and WorldEvent(QUEST_COMPLETED).  Quest entries whose
        reward transaction already succeeded are removed from the registry.

        Decision logic only — no durable state is mutated here.
        """
        update = QuestOpportunityRewardSystem._emit_terminal_removals(state, update)

        for intent in sorted(
            update.quest_opportunity_reward_intents,
            key=lambda i: (i.quest_id, i.entity_id),
        ):
            quest_opp = state.quest_registry.get(intent.quest_id)
            if quest_opp is None:
                continue  # already removed — idempotency guard

            entity = state.entities.get(intent.entity_id)
            if entity is None:
                continue

            reward_spec = quest_opp.reward_spec
            gold = int(reward_spec.get("gold", 0))
            xp = int(reward_spec.get("xp", 0))

            faction_rep = reward_spec.get("faction_rep", 0.0)
            if faction_rep:
                _log.debug(
                    "quest_opportunity_reward: faction_rep=%s skipped for quest=%s (Phase 5)",
                    faction_rep,
                    intent.quest_id,
                )

            if gold > 0 or xp > 0:
                reward_intent = ResourceTransferIntent(
                    source_id=intent.quest_id,
                    source_kind="QUEST",
                    gold_delta=gold,
                    reward_upd=RewardUpdate(xp_gain=xp),
                    transfer_kind="QUEST_REWARD",
                    transaction_id=f"quest:{intent.quest_id}:reward",
                    group_id=f"quest:{intent.quest_id}:reward",
                    is_group_required=True,
                )
                ent_upd = update.entity_updates.get(
                    intent.entity_id,
                    EntityUpdate(entity_id=intent.entity_id),
                )
                ent_upd = replace(
                    ent_upd,
                    resource_transfers=list(ent_upd.resource_transfers) + [reward_intent],
                )
                update = replace(
                    update,
                    entity_updates={**update.entity_updates, intent.entity_id: ent_upd},
                )

            event = WorldEvent(
                category=WorldEventCategory.QUEST_COMPLETED,
                tick=state.tick,
                subject=intent.quest_id,
                payload={
                    "gold": float(gold),
                    "xp": float(xp),
                    "entity_id": float(intent.entity_id),
                },
            )
            update = replace(
                update,
                world_events_add=list(update.world_events_add) + [event],
            )

            # When there is nothing to transact, remove immediately.
            # When gold/xp > 0, removal is deferred to _emit_terminal_removals
            # on the next tick once the transaction is recorded in
            # state.processed_transaction_ids.
            if gold == 0 and xp == 0:
                update = replace(
                    update,
                    quest_registry_remove=list(update.quest_registry_remove) + [intent.quest_id],
                )

        return update
