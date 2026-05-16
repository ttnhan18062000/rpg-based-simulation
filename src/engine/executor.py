# Compliance IDs: INFRA-071, INFRA-072, INFRA-073, INFRA-074, INFRA-075, INFRA-076, INFRA-077, SUB-003, SUB-004, SUB-280, SUB-281, SUB-282, SUB-283, SUB-284, SUB-285, SUB-286, SUB-287, SUB-288
# src/engine/executor.py
from __future__ import annotations
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, List, Dict, Any, Protocol, Callable

from src.core.worker_protocol import WorkerResult, ResultStatus, WorkerPacket
from src.core.work import WorkClass

if TYPE_CHECKING:
    from src.core.work import WorkItem
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.engine.worker_manager import WorkerManager

def _readonly_mapping(value):
    """
    Create a shallow read-only mapping.

    This prevents:
        state.entities[1] = ...
        state.regions["x"] = ...
        state.buildings[1] = ...

    It does not make the dataclass objects inside the mapping deeply immutable.
    """
    if isinstance(value, MappingProxyType):
        return value
    return MappingProxyType(dict(value))


def _readonly_state_view(state: AuthoritativeState) -> AuthoritativeState:
    """
    Create a read-only execution view for worker/domain logic.

    Purpose:
        Domain logic may inspect authoritative state, but must not mutate
        authoritative containers directly.

    Fraud this catches:
        - brain/action/move logic mutates state.entities directly
        - local sequential execution bypasses isolation protection
        - comments claim readonly behavior but runtime state is still mutable
    """
    return replace(
        state,
        entities=_readonly_mapping(state.entities),
        resource_nodes=_readonly_mapping(state.resource_nodes),
        buildings=_readonly_mapping(state.buildings),
        regions=_readonly_mapping(state.regions),
        terrain=_readonly_mapping(state.terrain),
        building_tiles=_readonly_mapping(state.building_tiles),
        global_resources=_readonly_mapping(state.global_resources),
        blocked_tiles=frozenset(state.blocked_tiles),
        town_tiles=frozenset(state.town_tiles),
    )


class IWorkExecutor(Protocol):
    """
    Law: Execution strategy interface.
    Separates 'how work is executed' from 'what logic is executed'.
    """
    def execute(
        self, 
        work_items: List[WorkItem], 
        state: AuthoritativeState, 
        rng: DeterministicRNG,
        profile: RuntimeProfile
    ) -> List[WorkerResult]:
        ...

    def set_concurrency_limit(self, limit: float) -> None:
        ...

class LocalSequentialExecutor:
    """
    Milestone A Law: The deterministic, single-process execution baseline.
    Bypasses all concurrency plumbing and packets for absolute semantic truth.
    """

    def execute(
        self,
        work_items: List[WorkItem],
        state: AuthoritativeState,
        rng: DeterministicRNG,
        profile: RuntimeProfile,
    ) -> List[WorkerResult]:
        from src.engine.domain_logic import SimulationDomainLogic
        from src.core.updates import TaskUpdate, EntityUpdate, EMPTY_ENTITY_UPDATE
        from src.core.concurrency_law import ConcurrencyLaw

        # Critical isolation boundary:
        # All domain logic must receive this readonly state view, not the
        # mutable authoritative state object owned by the kernel/apply path.
        readonly_state = state.readonly_view()

        results: List[WorkerResult] = []

        for i, item in enumerate(work_items):
            # 1. ENTITY CRITICAL WORK: ENTITY_MOVE / ENTITY_ACT / ENTITY_BRAIN
            if (
                item.work_kind in ("ENTITY_MOVE", "ENTITY_ACT", "ENTITY_BRAIN")
                and isinstance(item.owner_id, int)
            ):
                subject = readonly_state.entities.get(item.owner_id)
                if not subject:
                    continue

                frozen_subject = subject

                if item.work_kind == "ENTITY_MOVE":
                    target = item.payload.get(
                        "target_position",
                        frozen_subject.navigation.position,
                    )
                    from src.core.updates import NavigationUpdate
                    updates = {
                        frozen_subject.id: EntityUpdate(
                            entity_id=frozen_subject.id,
                            navigation=NavigationUpdate(target_set=target)
                        )
                    }

                elif item.work_kind == "ENTITY_ACT":
                    updates = SimulationDomainLogic.execute_action(
                        frozen_subject,
                        item.payload,
                        readonly_state.tick,
                        context=readonly_state,
                    )

                    if frozen_subject.id in updates:
                        updates[frozen_subject.id] = replace(
                            updates[frozen_subject.id],
                            task=TaskUpdate(
                                work_kind_set="ENTITY_ACT",
                                payload_set=item.payload,
                            ),
                        )

                elif item.work_kind == "ENTITY_BRAIN":
                    updates = SimulationDomainLogic.execute_brain(
                        readonly_state,
                        frozen_subject,
                    )

                else:
                    # Logic ID: CORE-PERF-018
                    updates = {frozen_subject.id: EMPTY_ENTITY_UPDATE}

                for eid, upd in updates.items():
                    # Option A Enforcement:
                    # Sequential entity work may only emit an update for itself
                    # or system entity 0.
                    if eid != frozen_subject.id and eid != 0:
                        continue

                    results.append(
                        WorkerResult(
                            source_packet_id=f"local:{readonly_state.tick}:{i}",
                            work_id=f"{readonly_state.tick}:{item.owner_id}:{item.work_kind}",
                            entity_id=eid,
                            work_class=item.work_class,
                            update=upd,
                            status=ResultStatus.SUCCESS,
                            class_priority=ConcurrencyLaw.get_class_priority(
                                item.work_class
                            ),
                            local_priority=item.priority,
                        )
                    )

            # 2. SYSTEM DEFERRED WORK
            elif item.work_kind == "DRAIN_DEBT" and isinstance(item.owner_id, str):
                from src.engine.domain_logic import SimulationDomainLogic
                from src.core.updates import EntityUpdate
                from src.core.concurrency_law import ConcurrencyLaw

                drain = SimulationDomainLogic.drain_debt(item.owner_id, profile)

                results.append(
                    WorkerResult(
                        source_packet_id=f"local:{readonly_state.tick}:{i}",
                        work_id=item.work_id,
                        entity_id=0,
                        work_class=item.work_class,
                        update=EntityUpdate(entity_id=0),
                        work_debt_update=drain,
                        subsystem_id=item.owner_id,
                        class_priority=ConcurrencyLaw.get_class_priority(
                            item.work_class
                        ),
                        local_priority=item.priority,
                    )
                )

        return results

    def set_concurrency_limit(self, limit: float) -> None:
        """Local executor is always sequential."""
        pass

class ConcurrentExecutionAdapter:
    """
    The concurrent execution strategy.
    Adapts WorkItems into WorkerPackets and dispatches them to a WorkerManager.
    """
    def __init__(self, worker_manager: WorkerManager, concurrency_limit: float = 1.0):
        self._worker_manager = worker_manager
        self._concurrency_limit = concurrency_limit

    def set_concurrency_limit(self, limit: float) -> None:
        """Update the active concurrency throttle for the next batch."""
        self._concurrency_limit = limit

    def execute(
        self, 
        work_items: List[WorkItem], 
        state: AuthoritativeState, 
        rng: DeterministicRNG,
        profile: RuntimeProfile
    ) -> List[WorkerResult]:
        from src.engine.worker_logic import default_simulation_worker
        from src.core.protocol_validator import ProtocolValidator
        from src.core.concurrency_law import ConcurrencyLaw
        from src.core.updates import EntityUpdate, EMPTY_ENTITY_UPDATE
        from src.core.immutability import deep_freeze
        from dataclasses import replace

        packets: List[WorkerPacket] = []
        source_meta: Dict[str, Tuple[WorkItem, WorkerPacket]] = {}
        final_results: List[WorkerResult] = []

        # Logic ID: CORE-PERF-020 (Persistent deep_freeze caching)
        if not hasattr(self, "_freeze_cache"):
            self._freeze_cache = {}

        def get_frozen(obj, key):
            obj_id = id(obj)
            cached_id, cached_obj = self._freeze_cache.get(key, (None, None))
            if cached_id == obj_id:
                return cached_obj
            frozen = deep_freeze(obj)
            self._freeze_cache[key] = (obj_id, frozen)
            return frozen

        frozen_regions = get_frozen(state.regions, "regions")
        frozen_resource_nodes = get_frozen(state.resource_nodes, "nodes")
        frozen_buildings = get_frozen(state.buildings, "buildings")
        frozen_groups = get_frozen(state.groups, "groups")
        frozen_corpses = get_frozen(state.corpses, "corpses")
        frozen_ground_items = get_frozen(state.ground_items, "ground_items")
        frozen_terrain = get_frozen(state.terrain, "terrain")
        
        from src.engine.domain.view import DomainView
        from src.engine.spatial_query import SpatialQueryService
        frozen_grid = DomainView._get_cached_spatial_grid(state)
        frozen_occ_map = SpatialQueryService.get_occupancy_map(state)
        
        # CORE-PERF-021: Reuse region list cache
        frozen_regions_list = getattr(state, "_region_list_cache", None)
        if frozen_regions_list is None:
             DomainView.get_region_for_position(state, (0,0)) # Build cache
             frozen_regions_list = getattr(state, "_region_list_cache")
             
        frozen_building_map = SpatialQueryService._get_building_map(state)
        frozen_regions_bounds = SpatialQueryService._get_regions_global_bounds(state)
        frozen_region_index = SpatialQueryService._get_region_index(state)
        frozen_building_region_map = SpatialQueryService._get_building_region_map(state)
        frozen_node_map = SpatialQueryService._get_node_map(state)
        frozen_corpse_map = SpatialQueryService._get_corpse_map(state)
        frozen_ground_item_map = SpatialQueryService._get_ground_item_map(state)

        for i, item in enumerate(work_items):
            if item.work_kind in ("ENTITY_MOVE", "ENTITY_ACT", "ENTITY_BRAIN") and isinstance(item.owner_id, int):
                subject = state.entities.get(item.owner_id)
                if subject:
                    # Optimization: state is already a readonly_view, so entities are already frozen
                    subject_snapshot = subject
                    
                    from src.core.enums import Domain
                    packet_id = f"{state.tick}:{i}"
                    packet_seed = rng.get_int(Domain.DEFAULT, state.tick, item.owner_id, 0, 1000000)
                    packet = WorkerPacket(
                        packet_id=packet_id,
                        work_id=f"{state.tick}:{item.owner_id}:{item.work_kind}",
                        tick=state.tick,
                        world_time=state.world_time,
                        seed=packet_seed,
                        work_class=item.work_class,
                        subject=subject_snapshot,
                        neighbor_view=[], # Computed lazily by worker
                        work_kind=item.work_kind,
                        payload=item.payload,
                        class_priority=ConcurrencyLaw.get_class_priority(item.work_class),
                        local_priority=item.priority,
                        regions=frozen_regions,
                        resource_nodes=frozen_resource_nodes,
                        buildings=frozen_buildings,
                        groups=frozen_groups,
                        corpses=frozen_corpses,
                        ground_items=frozen_ground_items,
                        town_center=state.town_center,
                        terrain=frozen_terrain,
                        all_entities=state.entities, # Full state (efficient in Mega-Chunks)
                        spatial_grid=frozen_grid,
                        occupancy_map=frozen_occ_map,
                        region_list=frozen_regions_list,
                        building_map=frozen_building_map,
                        _region_index_cache=frozen_region_index,
                        _regions_global_bounds=frozen_regions_bounds,
                        _building_region_map_cache=frozen_building_region_map,
                        _node_map_cache=frozen_node_map,
                        _corpse_map_cache=frozen_corpse_map,
                        _ground_item_map_cache=frozen_ground_item_map
                    )
                    packets.append(packet)
                    source_meta[packet_id] = (item, packet)

            # 2. SYSTEM DEFERRED WORK (Milestone C: De-simulation)
            elif item.work_kind == "DRAIN_DEBT" and isinstance(item.owner_id, str):
                from src.engine.domain_logic import SimulationDomainLogic
                from src.core.concurrency_law import ConcurrencyLaw
                from src.core.updates import EntityUpdate
                
                drain = SimulationDomainLogic.drain_debt(item.owner_id, profile)
                final_results.append(WorkerResult(
                    source_packet_id=f"local:{state.tick}:{i}",
                    work_id=item.work_id,
                    entity_id=0,
                    work_class=item.work_class,
                    update=EntityUpdate(entity_id=0),
                    work_debt_update=drain,
                    subsystem_id=item.owner_id,
                    class_priority=ConcurrencyLaw.get_class_priority(item.work_class),
                    local_priority=item.priority
                ))

        ProtocolValidator.validate_packet_batch(packets)
        
        # M10 Law: Persist source packets for kernel-level validation
        self._source_packets = {p.packet_id: p for p in packets}
        
        raw_results = self._worker_manager.execute_batch(
            packets, 
            default_simulation_worker,
            concurrency_limit=self._concurrency_limit
        )

        # Optimization: Map work_id to priority in O(1)
        priority_map = {item.work_id: item.priority for item in work_items}

        for res in raw_results:
            source_packet = self._source_packets.get(res.source_packet_id)
            if source_packet:
                item_priority = priority_map.get(source_packet.work_id, 0)

                final_results.append(WorkerResult(
                    source_packet_id=res.source_packet_id,
                    work_id=source_packet.work_id,
                    entity_id=res.entity_id,
                    work_class=source_packet.work_class,
                    update=res.update,
                    status=res.status,
                    class_priority=ConcurrencyLaw.get_class_priority(source_packet.work_class),
                    local_priority=item_priority,
                    compute_time_ns=res.compute_time_ns
                ))
        
        ProtocolValidator.validate_result_batch(final_results, self._source_packets)
        return final_results
