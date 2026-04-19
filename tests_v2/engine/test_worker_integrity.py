import pytest
from src_v2.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src_v2.core.protocol_validator import ProtocolValidator, ProtocolViolationError
from src_v2.core.updates import EntityUpdate
from src_v2.core.state import EntityState

@pytest.fixture
def sample_packet():
    subject = EntityState(id=1, kind="ACTOR", position=(0.0, 0.0))
    return WorkerPacket(
        packet_id="100:0",
        tick=100,
        world_time=1000,
        seed=42,
        subject=subject,
        neighbor_view=[],
        work_kind="TEST",
        payload={}
    )

def test_protocol_duplicate_packet_rejection(sample_packet):
    """M8 Law: Duplicate packet IDs in a batch must be rejected."""
    packets = [sample_packet, sample_packet]
    with pytest.raises(ProtocolViolationError, match="Duplicate packet ID"):
        ProtocolValidator.validate_packet_batch(packets)

def test_protocol_option_a_pre_dispatch_rejection(sample_packet):
    """M8 Law: Multiple work items for the same entity in one tick is forbidden (Option A)."""
    p2 = WorkerPacket(
        packet_id="100:1",
        tick=100,
        world_time=1000,
        seed=43,
        subject=sample_packet.subject, # Same entity
        neighbor_view=[],
        work_kind="TEST",
        payload={}
    )
    with pytest.raises(ProtocolViolationError, match="Multiple work items for entity"):
        ProtocolValidator.validate_packet_batch([sample_packet, p2])

def test_protocol_canonical_context_rejection(sample_packet):
    """M8 Law: Neighbor view must be sorted by ID."""
    p2 = WorkerPacket(
        packet_id="100:1",
        tick=100,
        world_time=1000,
        seed=43,
        subject=EntityState(id=2, kind="X", position=(1.0, 1.0)),
        neighbor_view=[(10, None), (5, None)], # Unsorted
        work_kind="TEST",
        payload={}
    )
    with pytest.raises(ProtocolViolationError, match="Neighbor view not sorted"):
        ProtocolValidator.validate_packet_batch([p2])

def test_protocol_result_traceability_rejection(sample_packet):
    """M8 Law: Results must link back to a valid source packet."""
    result = WorkerResult(
        source_packet_id="UNKNOWN",
        entity_id=1,
        update=EntityUpdate(entity_id=1)
    )
    source_packets = {"100:0": sample_packet}
    with pytest.raises(ProtocolViolationError, match="Orphan result"):
        ProtocolValidator.validate_result_batch([result], source_packets)

def test_protocol_result_id_mismatch_rejection(sample_packet):
    """M8 Law: Result entity ID must match the packet's subject ID."""
    result = WorkerResult(
        source_packet_id="100:0",
        entity_id=999, # Mismatch
        update=EntityUpdate(entity_id=999)
    )
    source_packets = {"100:0": sample_packet}
    with pytest.raises(ProtocolViolationError, match="Result entity mismatch"):
        ProtocolValidator.validate_result_batch([result], source_packets)

def test_protocol_duplicate_result_rejection(sample_packet):
    """M8 Law: Duplicate authoritative results for same entity must be rejected."""
    res1 = WorkerResult(source_packet_id="100:0", entity_id=1, update=EntityUpdate(1))
    # Note: Validator doesn't know about packet IDs for results directly, 
    # but it checks entity_id uniqueness in one batch.
    with pytest.raises(ProtocolViolationError, match="Duplicate authoritative result"):
        ProtocolValidator.validate_result_batch([res1, res1], {"100:0": sample_packet})
