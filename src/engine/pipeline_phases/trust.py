# Compliance IDs: TOWN-150, TOWN-151, TOWN-152, TOWN-153, TOWN-154
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import (
    NavigationUpdate,
    QuestUpdate,
    RejectionEvent,
)

if TYPE_CHECKING:
    from src.core.updates import StateUpdate


class TrustBoundaryPhase:
    """
    Pipeline phase responsible for removing untrusted raw worker mutations.

    This phase is the first security/authority gate in the authoritative
    pipeline. It runs before actor-validity, contracts, actions, movement,
    resources, occupancy, lifecycle, and group resolution.

    Important law:
        Worker output is only a proposal.

    Therefore raw workers are allowed to propose semantic intent, such as:
        - task intent
        - navigation intent
        - interaction progress
        - non-authoritative resource transfer intent

    But workers are not allowed to directly mutate authoritative world state,
    such as:
        - inventory
        - rewards
        - combat state
        - biological state
        - readiness
        - final position
        - node/building/chest/ground/corpse world state

    This phase must not perform gameplay resolution. It only strips unsafe
    mutation surfaces and records rejection/audit information when a worker
    attempted a forbidden direct mutation.
    """

    UNTRUSTED_DIRECT_MOVEMENT_REASON = "UNTRUSTED_DIRECT_MOVEMENT"

    @staticmethod
    def strip(update: StateUpdate) -> StateUpdate:
        """
        Strip unauthorized raw worker effects.

        Allowed from raw workers:
            - EntityUpdate.task
            - EntityUpdate.navigation as intent
            - EntityUpdate.interaction as progress proposal
            - ResourceTransferIntent, except blocked reward/tax kinds
            - QuestUpdate.progress_delta, but not direct status_set

        Stripped from raw workers:
            - direct InventoryUpdate
            - direct RewardUpdate
            - direct CombatUpdate
            - direct BiologicalUpdate
            - direct readiness mutation
            - direct final position mutation
            - direct world object mutation
            - unauthorized quest status_set
            - unauthorized reward/tax transfer kinds

        Direct movement handling:
            Raw workers may not directly set EntityUpdate.new_position or
            EntityUpdate.moved_this_tick. Those fields represent authoritative
            movement execution results, not worker intent.

            If a worker submits direct movement, this phase:
                - clears new_position
                - resets moved_this_tick to False
                - adds NavigationUpdate.failure_reason =
                  "UNTRUSTED_DIRECT_MOVEMENT"
                - increments rejections_delta
                - adds a RejectionEvent

            Occupancy conflict is intentionally NOT emitted here. Occupancy
            conflict belongs to OccupancyPhase and applies only after an
            authoritative phase has produced final movement results.
        """
        sanitized_entity_updates = {}

        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

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

                    # Quest status is authoritative. Workers may report
                    # progress but may not directly mark a quest completed,
                    # failed, or rewarded.
                    status_set=None,

                    # Preserve batched progress updates if the current model
                    # supports them.
                    multi_updates=getattr(clean_quest, "multi_updates", []),
                )

            clean_resource_transfers = [
                transfer
                for transfer in entity_update.resource_transfers
                if transfer.transfer_kind not in blocked_transfer_kinds
            ]

            # Direct final movement is not a semantic intent. It is an
            # authoritative execution result. Therefore the trust boundary
            # must reject it before movement/occupancy phases.
            had_direct_movement = (
                entity_update.new_position is not None
                or entity_update.moved_this_tick is True
            )

            clean_navigation = entity_update.navigation

            if had_direct_movement:
                reason = TrustBoundaryPhase.UNTRUSTED_DIRECT_MOVEMENT_REASON

                new_rejections_delta[reason] = (
                    new_rejections_delta.get(reason, 0) + 1
                )

                # TrustBoundaryPhase does not receive AuthoritativeState, so it
                # cannot know the real current tick. Use -1 as a sentinel
                # meaning "rejected at stateless trust boundary". Downstream
                # replay/state still receives the authoritative refined update.
                new_rejection_events.append(
                    RejectionEvent(
                        tick=-1,
                        actor_id=entity_id,
                        action_kind="GLOBAL_PROPOSAL",
                        reason=reason,
                    )
                )

                current_navigation = clean_navigation or NavigationUpdate()
                clean_navigation = replace(
                    current_navigation,
                    failure_reason=reason,
                )

            sanitized_entity_updates[entity_id] = replace(
                entity_update,

                # Direct economy/reward mutation is never trusted from raw
                # workers. These must be produced by resource/town/combat
                # systems and resolved through authoritative phases.
                inventory=None,
                reward=None,

                # Direct readiness/biological/combat mutation is not trusted.
                # Combat/action effects must come from action routing/domain
                # execution, not worker-provided mutation.
                readiness_delta=0.0,
                biological=None,
                combat=None,

                # Direct final position mutation is not trusted. Workers may
                # submit NavigationUpdate intent, but not the final position.
                new_position=None,
                moved_this_tick=False,

                # Preserve semantic intent/navigation, with rejection reason
                # attached if direct movement was attempted.
                navigation=clean_navigation,

                # Preserve safe quest progress, but strip direct status changes.
                quest=clean_quest,

                # Preserve safe resource transfer intents, but strip direct
                # reward/tax kinds.
                resource_transfers=clean_resource_transfers,
            )

        return replace(
            update,
            entity_updates=sanitized_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events,

            # Direct world-side effects are generated only by authoritative
            # systems. Raw workers must not directly mutate these collections.
            node_updates={},
            building_updates={},
            chest_updates={},
            ground_items_remove=[],
            corpses_remove=[],
        )