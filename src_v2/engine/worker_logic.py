from __future__ import annotations

from src_v2.core.worker_protocol import WorkerPacket, WorkerResult
from src_v2.core.updates import EntityUpdate


def default_simulation_worker(packet: WorkerPacket) -> WorkerResult:
    """
    Law: Pure simulation logic. No whole-world access.
    M8 Logic path for concurrent entity processing.
    """
    # Simply reducing readiness as a placeholder for Milestone 8
    # In a full simulation, this would involve movement/combat logic 
    # using packet.subject and packet.neighbor_view.
    return WorkerResult(
        source_packet_id=packet.packet_id,
        entity_id=packet.subject.id,
        update=EntityUpdate(
            entity_id=packet.subject.id,
            readiness_delta=-100.0 # Standard action cost
        )
    )
