from __future__ import annotations

from src_v2.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src_v2.engine.domain_logic import SimulationDomainLogic


def default_simulation_worker(packet: WorkerPacket) -> WorkerResult:
    """
    Law: Pure simulation logic. No whole-world access.
    M8 Logic path for concurrent entity processing.
    """
    if packet.work_kind == "ENTITY_MOVE":
        target = packet.payload.get("target_position", packet.subject.position)
        update = SimulationDomainLogic.execute_move(packet, packet.subject, target)
    elif packet.work_kind == "ENTITY_ACT":
        update = SimulationDomainLogic.execute_action(packet.subject, packet.payload, packet.tick)
    else:
        # Unknown work kind
        from src_v2.core.updates import EntityUpdate
        update = EntityUpdate(entity_id=packet.subject.id)

    return WorkerResult(
        source_packet_id=packet.packet_id,
        work_id=packet.work_id,
        entity_id=packet.subject.id,
        work_class=packet.work_class,
        update=update,
        status=ResultStatus.SUCCESS
    )
