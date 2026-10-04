from __future__ import annotations
from typing import List, Set, Dict
from src.core.worker_protocol import WorkerPacket, WorkerResult

class ProtocolViolationError(Exception):
    """Raised when the bounded-concurrency contract is violated."""
    pass

class ProtocolValidator:
    """
    Law: One place to enforce Option A and protocol identity.
    M8 Law: Enforce one-result-per-entity-per-tick and explicit identity matching.
    """
    
    @staticmethod
    def validate_packet_batch(packets: List[WorkerPacket]) -> None:
        """Verify a batch of packets for identity uniqueness and canonical context."""
        seen_ids: Set[str] = set()
        seen_entities: Set[int] = set()
        
        for packet in packets:
            # 1. Identity Uniqueness
            if packet.packet_id in seen_ids:
                raise ProtocolViolationError(f"Duplicate packet ID: {packet.packet_id}")
            seen_ids.add(packet.packet_id)
            
            # 2. Option A Pre-dispatch check (One work item per entity per tick)
            # In a richer world, this might be per (entity, domain), but for M8 it is per entity.
            if packet.subject.id in seen_entities:
                raise ProtocolViolationError(f"Multiple work items for entity {packet.subject.id}")
            seen_entities.add(packet.subject.id)
            
            # 3. Canonical Context Check
            last_id = -1
            for neighbor_id, _ in packet.neighbor_view:
                if neighbor_id <= last_id:
                    raise ProtocolViolationError(f"Neighbor view not sorted in packet {packet.packet_id}")
                last_id = neighbor_id

    @staticmethod
    def validate_result_batch(
        results: List[WorkerResult], 
        source_packets: Dict[str, WorkerPacket]
    ) -> None:
        """Verify results against their source packets and enforce Option A."""
        seen_entities: Set[int] = set()
        seen_debt_subsystems: Set[str] = set()

        for result in results:
            ProtocolValidator._check_source_traceability(result, source_packets)
            ProtocolValidator._check_one_result_per_entity(result, seen_entities)
            ProtocolValidator._check_one_debt_update_per_subsystem(result, seen_debt_subsystems)
            # A FAILURE status is acceptable by contract: delta enforcement happens at apply,
            # the validator checks protocol shape only.

    @staticmethod
    def _check_source_traceability(result: WorkerResult, source_packets: Dict[str, WorkerPacket]) -> None:
        """Match a result to its source packet (optional for local-only baseline runs)."""
        if result.source_packet_id in source_packets:
            packet = source_packets[result.source_packet_id]

            # Identity Matching
            if result.entity_id != packet.subject.id:
                raise ProtocolViolationError(
                    f"Result entity mismatch: expected {packet.subject.id}, got {result.entity_id}"
                )

            if result.work_id != packet.work_id:
                raise ProtocolViolationError(
                    f"Result work_id mismatch: expected {packet.work_id}, got {result.work_id}"
                )
        elif not result.source_packet_id.startswith("local:"):
            # If not local, must have a source packet
            raise ProtocolViolationError(f"Orphan result: source packet {result.source_packet_id} not found")

    @staticmethod
    def _check_one_result_per_entity(result: WorkerResult, seen_entities: Set[int]) -> None:
        """Option A enforcement (post-execution): one result per non-zero entity, a subsystem for system results."""
        if result.entity_id != 0:
            if result.entity_id in seen_entities:
                raise ProtocolViolationError(f"Duplicate authoritative result for entity {result.entity_id}")
            seen_entities.add(result.entity_id)
        elif not result.subsystem_id:
            # System results (entity_id=0) must specify a subsystem_id to avoid collision
            raise ProtocolViolationError("System result missing subsystem_id")

    @staticmethod
    def _check_one_debt_update_per_subsystem(result: WorkerResult, seen_debt_subsystems: Set[str]) -> None:
        """Allow at most one debt-update system result per subsystem per batch (PERF-M1-T04).

        System results tie on the whole sort key and the kernel merges their debt updates
        last-writer-wins per subsystem, so two for one subsystem would make the committed state
        depend on arrival order.
        """
        if result.work_debt_update is None or not result.subsystem_id:
            return
        if result.subsystem_id in seen_debt_subsystems:
            raise ProtocolViolationError(f"Duplicate system result for subsystem {result.subsystem_id}")
        seen_debt_subsystems.add(result.subsystem_id)
