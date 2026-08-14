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

    ECOLOGY_INTERVAL = 200  # Ticks between ecology checks

    # Density-dependent regen (E21D, 2026-06-28):
    # At DENSITY_CAP or more alive entities in a region, regen is reduced to DENSITY_FLOOR.
    # Interpolates linearly between 1.0 (zero entities) and DENSITY_FLOOR (≥ DENSITY_CAP).
    DENSITY_CAP: int = 16    # entity count at which regen hits the floor
    DENSITY_FLOOR: float = 0.25  # minimum regen multiplier (25% at saturation)

    @staticmethod
    def _region_entity_counts(state: "AuthoritativeState") -> dict[str, int]:
        """Count alive entities per region (O(N) over entities, called once per cycle)."""
        from src.engine.legality import LegalityServiceV2
        counts: dict[str, int] = {}
        for entity in state.entities.values():
            if not (entity.combat.alive and entity.lifecycle.active):
                continue
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if region is not None:
                counts[region.id] = counts.get(region.id, 0) + 1
        return counts

    @staticmethod
    def _density_modifier(entity_count: int) -> float:
        """
        Linear density modifier: 1.0 at 0 entities, DENSITY_FLOOR at ≥ DENSITY_CAP.

        High-entity-density regions regenerate slower, creating scarcity pressure
        that drives migration and territorial conflict (E21D AC).
        """
        cap = ResourceEcologyService.DENSITY_CAP
        floor = ResourceEcologyService.DENSITY_FLOOR
        if entity_count <= 0:
            return 1.0
        if entity_count >= cap:
            return floor
        return round(1.0 - (entity_count / cap) * (1.0 - floor), 6)

    @staticmethod
    def process_ecology(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Periodically attempt to seed new resources in valid regions.
        """
        if state.tick % ResourceEcologyService.ECOLOGY_INTERVAL != 0:
            return StateUpdate()

        regen_node_updates: dict = {}
        regen_events: List[WorldEvent] = []

        # Build entity-count-per-region map for density-dependent regen (E21D).
        from src.engine.legality import LegalityServiceV2
        region_entity_counts = ResourceEcologyService._region_entity_counts(state)

        for node_id, node in state.resource_nodes.items():
            if node.regen_rate_per_tick <= 0:
                continue
            if node.remaining_charges >= node.max_charges:
                continue
            if node.cooldown_remaining > 0:
                continue
            was_depleted = (node.remaining_charges == 0)

            # Apply density modifier: nodes in crowded regions regen slower.
            region = LegalityServiceV2.get_region_for_position(node.position, state)
            entity_count = region_entity_counts.get(region.id, 0) if region else 0
            density_mod = ResourceEcologyService._density_modifier(entity_count)
            effective_regen = max(1, round(node.regen_rate_per_tick * density_mod))

            new_charges = min(node.max_charges, node.remaining_charges + effective_regen)
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
                    kind = "wood_node" if region.kind == "FOREST" else "stone_outcrop"
                    if region.kind == "MOUNTAIN": kind = "iron_vein"

                    # Random position
                    rx = generator.rng.get_float(Domain.SPAWN, state.tick, f"x_{r_id}") * (xmax - xmin) + xmin
                    ry = generator.rng.get_float(Domain.SPAWN, state.tick, f"y_{r_id}") * (ymax - ymin) + ymin

                    # Create ResourceNodeState using next_node_id
                    from src.core.state import ResourceNodeState
                    from src.core.registries import ResourceRegistry
                    node_id = state.next_node_id + len(nodes_add)
                    new_node = ResourceNodeState(
                        id=node_id,
                        kind=kind,
                        position=(rx, ry),
                        yields_item=ResourceRegistry.get(kind).yield_item,
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
