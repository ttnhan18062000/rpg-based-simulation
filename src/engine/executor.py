# src/engine/executor.py
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, List, Dict, Any, Protocol, Callable

from src.core.worker_protocol import WorkerResult, ResultStatus, WorkerPacket
from src.core.work import WorkClass

if TYPE_CHECKING:
    from src.core.work import WorkItem
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.engine.worker_manager import WorkerManager

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
        profile: RuntimeProfile
    ) -> List[WorkerResult]:
        from src.engine.domain_logic import SimulationDomainLogic
        from src.core.updates import EntityUpdate

        results: List[WorkerResult] = []
        for i, item in enumerate(work_items):
            # 1. ENTITY CRITICAL WORK (ENTITY_MOVE/ACT/BRAIN)
            if item.work_kind in ("ENTITY_MOVE", "ENTITY_ACT", "ENTITY_BRAIN") and isinstance(item.owner_id, int):
                subject = state.entities.get(item.owner_id)
                if not subject:
                    continue
                
                # M8 Law: Even in sequential baseline, logic must only receive frozen snapshots
                from src.core.immutability import deep_freeze
                frozen_subject = deep_freeze(subject)
                # Note: We don't deep_freeze the entire state here for performance, 
                # but we pass the frozen_subject which is the primary mutation target.
                # The state dictionaries are already MappingProxyType if we use AuthoritativeState correctly.
                
                # Execute Domain Logic Directly
                if item.work_kind == "ENTITY_MOVE":
                    target = item.payload.get("target_position", frozen_subject.position)
                    updates = SimulationDomainLogic.execute_move(state, frozen_subject, target)
                elif item.work_kind == "ENTITY_ACT":
                    from src.core.updates import TaskUpdate
                    updates = SimulationDomainLogic.execute_action(frozen_subject, item.payload, state.tick, context=state)
                    if frozen_subject.id in updates:
                        updates[frozen_subject.id] = replace(updates[frozen_subject.id], task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=item.payload))
                elif item.work_kind == "ENTITY_BRAIN":
                    updates = SimulationDomainLogic.execute_brain(state, frozen_subject)
                else:
                    from src.core.updates import EntityUpdate
                    updates = {frozen_subject.id: EntityUpdate(entity_id=frozen_subject.id)}
                for eid, upd in updates.items():
                    results.append(WorkerResult(
                        source_packet_id=f"local:{state.tick}:{i}",
                        work_id=f"{state.tick}:{item.owner_id}:{item.work_kind}",
                        entity_id=eid,
                        work_class=item.work_class,
                        update=upd,
                        status=ResultStatus.SUCCESS
                    ))
            
            # 2. SYSTEM DEFERRED WORK (Milestone C: De-simulation)
            elif item.work_kind == "DRAIN_DEBT" and isinstance(item.owner_id, str):
                from src.engine.domain_logic import SimulationDomainLogic
                from src.core.concurrency_law import ConcurrencyLaw
                from src.core.updates import EntityUpdate
                
                drain = SimulationDomainLogic.drain_debt(item.owner_id, profile)
                results.append(WorkerResult(
                    source_packet_id=f"local:{state.tick}:{i}",
                    work_id=item.work_id,
                    entity_id=0, # System target
                    work_class=item.work_class,
                    update=EntityUpdate(entity_id=0),
                    work_debt_update=drain,
                    subsystem_id=item.owner_id,
                    class_priority=ConcurrencyLaw.get_class_priority(item.work_class),
                    local_priority=item.priority
                ))
        return results

    def set_concurrency_limit(self, limit: float) -> None:
        """Local executor is always sequential (limit=0 effectively)."""
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
        from src.core.updates import EntityUpdate
        from src.core.immutability import deep_freeze
        from dataclasses import replace

        packets: List[WorkerPacket] = []
        source_meta: Dict[str, Tuple[WorkItem, WorkerPacket]] = {}
        final_results: List[WorkerResult] = []

        for i, item in enumerate(work_items):
            if item.work_kind in ("ENTITY_MOVE", "ENTITY_ACT", "ENTITY_BRAIN") and isinstance(item.owner_id, int):
                subject = state.entities.get(item.owner_id)
                if subject:
                    # M7/A Law: Deeply frozen snapshot context
                    subject_snapshot = deep_freeze(subject)
                    
                    from src.engine.domain_logic import SimulationDomainLogic
                    neighbor_view = SimulationDomainLogic.get_neighbor_view(state, subject_snapshot, radius=10.0) # Default test radius
                    frozen_neighbor_view = [tuple([eid, deep_freeze(ent)]) for eid, ent in neighbor_view]
                    
                    from src.core.enums import Domain
                    packet_id = f"{state.tick}:{i}"
                    # Phase 2 Law: Use stateless get_int for order-independent seed derivation
                    packet_seed = rng.get_int(Domain.DEFAULT, state.tick, item.owner_id, 0, 1000000)
                    packet = WorkerPacket(
                        packet_id=packet_id,
                        work_id=f"{state.tick}:{item.owner_id}:{item.work_kind}",
                        tick=state.tick,
                        world_time=state.world_time,
                        seed=packet_seed,
                        work_class=item.work_class,
                        subject=subject_snapshot,
                        neighbor_view=frozen_neighbor_view,
                        work_kind=item.work_kind,
                        payload=item.payload,
                        regions=deep_freeze(state.regions),
                        resource_nodes=deep_freeze(state.resource_nodes),
                        buildings=deep_freeze(state.buildings),
                        groups=deep_freeze(state.groups),
                        town_center=state.town_center,
                        terrain=deep_freeze(state.terrain)
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

        for res in raw_results:
            source_packet = self._source_packets.get(res.source_packet_id)
            if source_packet:
                # Find the corresponding work item for priority injection
                # (In a cleaner version, we'd map this better, but this works for Sprint 1)
                item_priority = 0
                for item in work_items:
                    if f"{state.tick}:{item.owner_id}:{item.work_kind}" == source_packet.work_id:
                        item_priority = item.priority
                        break

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
