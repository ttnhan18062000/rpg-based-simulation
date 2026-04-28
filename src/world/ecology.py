# src/world/ecology.py
from __future__ import annotations
from typing import TYPE_CHECKING, List
from src.core.updates import StateUpdate
from src.core.enums import Domain

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.generator import EntityGenerator

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
                if generator.rng.get_float(Domain.SPAWN, state.tick, r_id + "_seed") < 0.5:
                    # Determine node kind based on region
                    kind = "WOOD" if region.kind == "FOREST" else "STONE"
                    if region.kind == "MOUNTAIN": kind = "IRON"
                    
                    # Random position
                    rx = generator.rng.get_float(Domain.SPAWN, state.tick, r_id + "_node_x") * (xmax - xmin) + xmin
                    ry = generator.rng.get_float(Domain.SPAWN, state.tick, r_id + "_node_y") * (ymax - ymin) + ymin
                    
                    # Create ResourceNodeState (Need ResourceNodeState import or generator method)
                    # For now, let's just return a placeholder or assume we have a generator method
                    from src.core.state import ResourceNodeState
                    new_node = ResourceNodeState(
                        id=1000 + state.tick + int(rx), # Simplified ID generation
                        kind=kind,
                        position=(rx, ry),
                        yields_item=kind.lower() + "_ore" if kind != "WOOD" else "wood_log",
                        remaining_charges=5,
                        max_charges=5,
                        required_ticks=10
                    )
                    nodes_add.append(new_node)
                    
        return StateUpdate(nodes_add=nodes_add)
