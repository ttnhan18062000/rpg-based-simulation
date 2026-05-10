from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import QuestUpdate

if TYPE_CHECKING:
    from src.core.updates import StateUpdate


class TrustBoundaryPhase:
    """
    Pipeline phase responsible for removing untrusted raw worker mutations.

    This phase must not perform gameplay logic.
    It only strips unauthorized mutation surfaces.
    """

    @staticmethod
    def strip(update: StateUpdate) -> StateUpdate:
        """
        Strip unauthorized raw worker effects.

        Allowed:
            - task intent
            - navigation intent
            - interaction progress
            - legal resource transfer intents except blocked reward kinds

        Stripped:
            - direct InventoryUpdate
            - direct RewardUpdate
            - unauthorized quest status_set
            - direct world mutations
            - unauthorized reward transfer kinds
        """
        sanitized_entity_updates = {}

        blocked_transfer_kinds = {
            "QUEST_REWARD",
            "REWARD",
            "KILL_REWARD",
            "TAX",
        }

        for entity_id, entity_update in update.entity_updates.items():
            clean_quest = entity_update.quest

            if clean_quest is not None:
                clean_quest = QuestUpdate(
                    quest_id=clean_quest.quest_id,
                    progress_delta=clean_quest.progress_delta,
                    status_set=None,
                    multi_updates=getattr(clean_quest, "multi_updates", []),
                )

            clean_resource_transfers = [
                transfer
                for transfer in entity_update.resource_transfers
                if transfer.transfer_kind not in blocked_transfer_kinds
            ]

            sanitized_entity_updates[entity_id] = replace(
                entity_update,

                # Direct economy/reward mutation is never trusted from raw workers.
                inventory=None,
                reward=None,

                # Direct readiness/biological mutation is also not trusted.
                readiness_delta=0.0,
                biological=None,

                # Preserve combat damage/effects, but strip attached rewards via
                # clean_resource_transfers above.
                combat=entity_update.combat,

                quest=clean_quest,
                resource_transfers=clean_resource_transfers,
            )

        return replace(
            update,
            entity_updates=sanitized_entity_updates,

            # Direct world-side effects are generated only by authoritative systems.
            node_updates={},
            building_updates={},
            chest_updates={},
            ground_items_remove=[],
            corpses_remove=[],
        )
