# src/world/ecology.py
from __future__ import annotations
from typing import TYPE_CHECKING, List
from src.core.updates import StateUpdate, ResourceNodeUpdate
from src.core.enums import Domain
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator

class ResourceEcologyService:
    """
    Handles regional resource replenishment (Nodes, Chests).
    """
    
    ECOLOGY_INTERVAL = 200 # Ticks between ecology checks
    
    @staticmethod
    def process_ecology(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Periodically attempt to seed new resources in valid regions.
        """
        if state.tick % ResourceEcologyService.ECOLOGY_INTERVAL != 0:
            return StateUpdate()

        regen_node_updates: dict = {}
        regen_events: List[WorldEvent] = []

        for node_id, node in state.resource_nodes.items():
            if node.regen_rate_per_tick <= 0:
                continue
            if node.remaining_charges >= node.max_charges:
                continue
            if node.cooldown_remaining > 0:
                continue
            was_depleted = (node.remaining_charges == 0)
            new_charges = min(node.max_charges, node.remaining_charges + node.regen_rate_per_tick)
            delta = new_charges - node.remaining_charges
            if delta <= 0:
                continue
            regen_node_updates[node_id] = ResourceNodeUpdate(node_id=node_id, charges_delta=delta)
            if was_depleted:
                regen_events.append(WorldEvent(
                    category=WorldEventCategory.RESOURCE_RECOVERED,
                    tick=state.tick,
                    region_id=None,
                    subject=str(node_id),
                    severity=1.0,
                ))

        nodes_add = []

        # 1. Count nodes per region
        region_node_count = {r_id: 0 for r_id in state.regions}
        for node in state.resource_nodes.values():
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(node.position, state)
            if region and region.id in region_node_count:
                region_node_count[region.id] += 1
                
        # 2. Check density and seed
        for r_id, region in state.regions.items():
            # Target nodes based on stability and hazard
            # High hazard -> more rare resources, High stability -> more common resources
            xmin, ymin, xmax, ymax = region.bounds
            area = (xmax - xmin) * (ymax - ymin)
            
            # Base target: 1 node per 200x200 area
            target_count = int((area / 40000.0) * (1.0 + region.stability))
            target_count = max(1, target_count)
            
            current_count = region_node_count[r_id]
            if current_count < target_count:
                # Seed chance (50% per interval if under target)
                if generator.rng.get_float(Domain.SPAWN, state.tick, f"seed_{r_id}") < 0.5:
                    # Determine node kind based on region
                    kind = "WOOD" if region.kind == "FOREST" else "STONE"
                    if region.kind == "MOUNTAIN": kind = "IRON"
                    
                    # Random position
                    rx = generator.rng.get_float(Domain.SPAWN, state.tick, f"x_{r_id}") * (xmax - xmin) + xmin
                    ry = generator.rng.get_float(Domain.SPAWN, state.tick, f"y_{r_id}") * (ymax - ymin) + ymin
                    
                    # Create ResourceNodeState using next_node_id
                    from src.core.state import ResourceNodeState
                    node_id = state.next_node_id + len(nodes_add)
                    new_node = ResourceNodeState(
                        id=node_id,
                        kind=kind,
                        position=(rx, ry),
                        yields_item=kind.lower() + "_ore" if kind != "WOOD" else "wood_log",
                        remaining_charges=5,
                        max_charges=5,
                        required_ticks=10,
                        regen_rate_per_tick=1,
                    )
                    nodes_add.append(new_node)
                    
        return StateUpdate(
            nodes_add=nodes_add,
            next_node_id_set=state.next_node_id + len(nodes_add) if nodes_add else None,
            node_updates=regen_node_updates,
            world_events_add=regen_events,
        )
