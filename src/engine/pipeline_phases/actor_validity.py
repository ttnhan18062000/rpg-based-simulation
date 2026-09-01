# Compliance IDs: AUTH-010
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.enums import ReasonCode
from src.core.updates import (
    NavigationUpdate,
    InteractionUpdate,
    RejectionEvent,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class ActorValidityPhase:
    """
    Reject proposals from dead, inactive, frozen, or stunned actors.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Law 300.1: Actor Validity.

        Invalid actors may not submit any authoritative proposal.

        Invalid means:
            - combat.alive is False
            - lifecycle.active is False
            - a "stunned" StatusEffectState is present in combat.status_effects
            - a "frozen" StatusEffectState is present in combat.status_effects

        Important:
            Navigation intent is also a proposal. A dead actor may not submit
            NavigationUpdate(target_set=...), even if EntityUpdate.new_position is
            still None.

        Effects:
            - strip task
            - strip navigation target / direct movement
            - strip resource transfers
            - strip interaction progress
            - emit one GLOBAL_PROPOSAL RejectionEvent
        """
        refined_entity_updates = dict(update.entity_updates)
        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

        for entity_id, entity_update in sorted(update.entity_updates.items()):
            entity = state.entities.get(entity_id)

            if entity is None:
                continue

            is_stunned = any(s.kind == "stunned" for s in entity.combat.status_effects)
            is_frozen = any(s.kind == "frozen" for s in entity.combat.status_effects)
            is_sleeping = entity.identity.properties.get("status_sleeping", False)
            is_dead = not entity.combat.alive
            is_inactive = not entity.lifecycle.active

            if not (is_stunned or is_frozen or is_sleeping or is_dead or is_inactive):
                continue

            reason = ReasonCode.ATTACKER_STATUS_BLOCKED

            has_navigation_proposal = (
                entity_update.navigation is not None
                and (
                    entity_update.navigation.target_set is not None
                    or entity_update.navigation.path_set is not None
                    or entity_update.navigation.movement_mode_set is not None
                    or entity_update.navigation.clear_target
                    or entity_update.navigation.clear_path
                )
            )

            has_direct_movement = (
                entity_update.new_position is not None
                or entity_update.moved_this_tick
            )

            has_task = entity_update.task is not None
            has_resource_transfer = bool(entity_update.resource_transfers)
            has_interaction = entity_update.interaction is not None
            has_combat_proposal = (
                entity_update.combat is not None
                and (
                    entity_update.combat.hp_delta != 0.0
                    or entity_update.combat.alive_set is not None
                )
            )

            has_any_proposal = (
                has_navigation_proposal
                or has_direct_movement
                or has_task
                or has_resource_transfer
                or has_interaction
                or has_combat_proposal
            )

            if not has_any_proposal:
                continue

            current_navigation = entity_update.navigation or NavigationUpdate()

            clean_navigation = replace(
                current_navigation,
                target_set=None,
                path_set=None,
                movement_mode_set=None,
                clear_target=True,
                clear_path=True,
                failure_reason=reason,
            )

            clean_interaction = None
            if entity_update.interaction is not None:
                clean_interaction = InteractionUpdate(
                    reset=True,
                )

            refined_entity_updates[entity_id] = replace(
                entity_update,
                task=None,
                navigation=clean_navigation,
                new_position=None,
                moved_this_tick=False,
                resource_transfers=[],
                interaction=clean_interaction,
                combat=None,
                readiness_delta=0.0,
            )

            reason_key = reason.value if hasattr(reason, "value") else str(reason)
            new_rejections_delta[reason_key] = new_rejections_delta.get(reason_key, 0) + 1

            new_rejection_events.append(
                RejectionEvent(
                    tick=state.tick,
                    actor_id=entity_id,
                    action_kind="GLOBAL_PROPOSAL",
                    reason=reason,
                )
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events,
        )
