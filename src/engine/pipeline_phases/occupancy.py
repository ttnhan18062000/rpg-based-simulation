from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.updates import (
    EntityUpdate,
    NavigationUpdate,
    RejectionEvent,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class OccupancyPhase:
    """
    Resolves occupancy conflicts in final proposed positions.
    """

    @staticmethod
    def resolve(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        LAW:
            Final movement results must not place two active entities on the same
            tile, and must not allow movement into a tile occupied by a static
            non-moving entity.

        Why this exists:
            MovementSystem handles normal navigation-intent movement, but worker
            proposals or tests may directly provide EntityUpdate.new_position.
            The authoritative pipeline must still validate final positions before
            ApplyPath commits them.

        Determinism:
            If multiple entities claim the same destination tile, the lowest entity
            id wins. All other claimants are rejected with OCCUPANCY_CONFLICT.

        Static occupancy:
            If the destination is occupied by an entity that is not moving away in
            this same update, the move is rejected.
        """
        refined_entity_updates = dict(update.entity_updates)

        # Moving entities are entities that propose a concrete final position.
        moving_entity_ids = {
            entity_id
            for entity_id, entity_update in refined_entity_updates.items()
            if entity_update.new_position is not None
        }

        if not moving_entity_ids:
            return update

        # Current occupied tiles in authoritative state.
        current_occupied: dict[tuple[int, int], int] = {}

        for entity_id, entity in state.entities.items():
            if not entity.lifecycle.active:
                continue

            current_occupied[
                (
                    int(entity.navigation.position[0]),
                    int(entity.navigation.position[1]),
                )
            ] = entity_id

        # Destination claims from proposed movement results.
        claims_by_tile: dict[tuple[int, int], list[int]] = {}

        for entity_id, entity_update in refined_entity_updates.items():
            if entity_update.new_position is None:
                continue

            tile = (
                int(entity_update.new_position[0]),
                int(entity_update.new_position[1]),
            )

            claims_by_tile.setdefault(tile, []).append(entity_id)

        rejected_entity_ids: set[int] = set()

        for tile in sorted(claims_by_tile):
            contenders = sorted(claims_by_tile[tile])

            existing_occupant_id = current_occupied.get(tile)

            # If the tile is occupied by an entity that is not moving away, nobody
            # may move into that tile.
            if (
                existing_occupant_id is not None
                and existing_occupant_id not in moving_entity_ids
            ):
                rejected_entity_ids.update(contenders)
                continue

            # If multiple entities claim the same destination, lowest id wins.
            winner_id = contenders[0]
            for loser_id in contenders[1:]:
                rejected_entity_ids.add(loser_id)

        new_rejections_delta = dict(update.rejections_delta)
        new_rejection_events = list(update.rejection_events)

        for entity_id in sorted(rejected_entity_ids):
            entity_update = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )

            current_navigation_update = entity_update.navigation or NavigationUpdate()
            reason = "OCCUPANCY_CONFLICT"
            
            new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
            new_rejection_events.append(RejectionEvent(
                tick=state.tick,
                actor_id=entity_id,
                action_kind="MOVE",
                reason=reason
            ))

            refined_entity_updates[entity_id] = replace(
                entity_update,
                new_position=None,
                moved_this_tick=False,
                navigation=replace(
                    current_navigation_update,
                    failure_reason=reason,
                ),
            )

        return replace(
            update,
            entity_updates=refined_entity_updates,
            rejections_delta=new_rejections_delta,
            rejection_events=new_rejection_events
        )
