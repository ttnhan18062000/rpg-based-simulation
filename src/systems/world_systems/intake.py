from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import ConcernState

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class ConcernIntakeSystem:
    """
    Authoritative logic for filtering world events into local character concerns.
    Implements Phase 9: Concern Intake and Salience Filtering.
    """

    @staticmethod
    def evaluate_salience(
        entity: EntityState,
        neighbors: List[Tuple[int, EntityState]],
        state: AuthoritativeState
    ) -> List[ConcernState]:
        """
        Scan neighbors for high-salience events (Combat, Death, Plunder).
        VERIFIED v2: strategic_salience_filtering
        """
        concerns = []
        
        # 1. Nearby Combat Threat
        # If any hostile neighbor is currently attacking or has recently attacked
        for _, neighbor in neighbors:
            if neighbor.identity.faction != entity.identity.faction:
                if neighbor.combat.alive:
                    # Hostile is alive and nearby -> DANGER
                    dist = abs(neighbor.navigation.position[0] - entity.navigation.position[0]) + abs(neighbor.navigation.position[1] - entity.navigation.position[1])
                    if dist <= 3.0:
                        concerns.append(ConcernState(
                            id=f"danger_hostile_{neighbor.id}",
                            kind="danger",
                            source=str(neighbor.id),
                            urgency=0.8 if dist <= 1.5 else 0.5,
                            created_tick=state.tick
                        ))

            # 2. Witnessing Death (Grief/Trauma)
            if not neighbor.combat.alive and neighbor.identity.faction == entity.identity.faction:
                 # Ally just died or is lying dead nearby
                 concerns.append(ConcernState(
                     id=f"trauma_dead_ally_{neighbor.id}",
                     kind="trauma",
                     source=str(neighbor.id),
                     urgency=0.6,
                     created_tick=state.tick
                 ))

        # 3. Opportunity: Resource Nodes (Salience based on hunger/needs)
        # (This is often handled by goals, but can be a 'concern' if we are starving)
        if entity.biological.hunger > 60.0:
            for node_id, node in state.resource_nodes.items():
                dist = abs(node.position[0] - entity.navigation.position[0]) + abs(node.position[1] - entity.navigation.position[1])
                if dist <= 5.0 and node.remaining_charges > 0:
                     concerns.append(ConcernState(
                         id=f"opp_food_{node_id}",
                         kind="opportunity",
                         source=str(node_id),
                         urgency=entity.biological.hunger / 100.0,
                         created_tick=state.tick
                     ))

        return concerns
