from __future__ import annotations

from dataclasses import replace
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.engine.domain_logic import SimulationDomainLogic


def default_simulation_worker(packet: WorkerPacket) -> List[WorkerResult]:
    """
    Law: Pure simulation logic. No whole-world access.
    M8 Logic path for concurrent entity processing.
    """
    if packet.work_kind == "ENTITY_MOVE":
        target = packet.payload.get("target_position", packet.subject.navigation.position)
        updates = SimulationDomainLogic.execute_move(packet, packet.subject, target)
    elif packet.work_kind == "ENTITY_ACT":
        updates = SimulationDomainLogic.execute_action(packet.subject, packet.payload, packet.tick, packet.neighbor_view, context=packet)
        if packet.subject.id in updates:
            from src.core.updates import TaskUpdate
            updates[packet.subject.id] = replace(updates[packet.subject.id], 
                task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=packet.payload)
            )
    elif packet.work_kind == "ENTITY_BRAIN":
        # Pass packet as 'state' context (WorkerPacket provides entities/terrain/etc via accessors)
        updates = SimulationDomainLogic.execute_brain(packet, packet.subject)
    else:
        # Unknown work kind
        from src.core.updates import EntityUpdate
        updates = {packet.subject.id: EntityUpdate(entity_id=packet.subject.id)}

    results = []
    for eid, upd in updates.items():
        # Option A Enforcement: A worker result MUST only update its assigned subject
        # System updates (eid=0) are allowed if they are non-entity specific (e.g. debt)
        if eid != packet.subject.id and eid != 0:
            continue

        results.append(WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=eid,
            work_class=packet.work_class,
            update=upd,
            status=ResultStatus.SUCCESS
        ))
    return results
