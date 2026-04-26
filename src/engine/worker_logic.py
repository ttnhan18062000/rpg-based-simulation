from __future__ import annotations

from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.engine.domain_logic import SimulationDomainLogic


def default_simulation_worker(packet: WorkerPacket) -> List[WorkerResult]:
    """
    Law: Pure simulation logic. No whole-world access.
    M8 Logic path for concurrent entity processing.
    """
    if packet.work_kind == "ENTITY_MOVE":
        target = packet.payload.get("target_position", packet.subject.position)
        updates = SimulationDomainLogic.execute_move(packet, packet.subject, target)
    elif packet.work_kind == "ENTITY_ACT":
        updates = SimulationDomainLogic.execute_action(packet.subject, packet.payload, packet.tick, packet.neighbor_view, context=packet)
    elif packet.work_kind == "ENTITY_BRAIN":
        # Pass packet as 'state' context (WorkerPacket provides entities/terrain/etc via accessors)
        updates = SimulationDomainLogic.execute_brain(packet, packet.subject)
    else:
        # Unknown work kind
        from src.core.updates import EntityUpdate
        updates = {packet.subject.id: EntityUpdate(entity_id=packet.subject.id)}

    results = []
    for eid, upd in updates.items():
        results.append(WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=eid,
            work_class=packet.work_class,
            update=upd,
            status=ResultStatus.SUCCESS
        ))
    return results
