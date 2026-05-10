from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import CombatUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class NearDeathHardeningPhase:
    """
    Applies authoritative near-death hardening after combat resolution.
    """

    @staticmethod
    def apply(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Apply near-death hardening after authoritative combat resolution.

        LAW:
            If an entity survives a hit with critically low remaining HP, it gains
            a small permanent max-HP increase in the same authoritative tick.

        Trigger:
            - entity has a CombatUpdate
            - combat update is not REJECTED
            - entity survives the hit
            - projected HP is > 0
            - projected HP is <= 10% of current max HP

        Effect:
            - CombatUpdate.max_hp_delta += 5

        Why this runs in the pipeline:
            This is not a worker reward. It is an authoritative consequence of
            surviving a near-death combat event.
        """
        refined_entity_updates = dict(update.entity_updates)

        for entity_id, entity_update in list(refined_entity_updates.items()):
            entity = state.entities.get(entity_id)

            if entity is None:
                continue

            combat_update = entity_update.combat

            if combat_update is None:
                continue

            if combat_update.outcome_kind == "REJECTED":
                continue

            current_hp = entity.combat.hp
            current_max_hp = entity.combat.max_hp

            projected_hp = current_hp + combat_update.hp_delta

            survived = (
                projected_hp > 0
                and combat_update.alive_set is not False
            )

            if not survived:
                continue

            near_death_threshold = max(1, int(current_max_hp * 0.10))

            if projected_hp > near_death_threshold:
                continue

            hardened_combat = combat_update.merge(
                CombatUpdate(
                    max_hp_delta=5,
                    trace={
                        "NEAR_DEATH_HARDENING": 5.0,
                        "NEAR_DEATH_PROJECTED_HP": float(projected_hp),
                        "NEAR_DEATH_THRESHOLD": float(near_death_threshold),
                    },
                )
            )

            refined_entity_updates[entity_id] = replace(
                entity_update,
                combat=hardened_combat,
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )
