import pytest
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.core.protocol_validator import ProtocolValidator, ProtocolViolationError
from src.core.updates import EntityUpdate
from src.core.state import EntityState
from src.core.builder import V2EntityBuilder

@pytest.fixture
def sample_packet():
    subject = (V2EntityBuilder(1)
               .kind("ACTOR")
               .location(0.0, 0.0)
               .build())
    from src.core.work import WorkClass
    return WorkerPacket(
        packet_id="100:0",
        work_id="100:1:TEST",
        tick=100,
        world_time=1000,
        seed=42,
        work_class=WorkClass.CRITICAL,
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
    from src.core.work import WorkClass
    p2 = WorkerPacket(
        packet_id="100:1",
        work_id="100:1:TEST_DUPE",
        tick=100,
        world_time=1000,
        seed=43,
        work_class=WorkClass.CRITICAL,
        subject=sample_packet.subject, # Same entity
        neighbor_view=[],
        work_kind="TEST",
        payload={}
    )
    with pytest.raises(ProtocolViolationError, match="Multiple work items for entity"):
        ProtocolValidator.validate_packet_batch([sample_packet, p2])

def test_protocol_canonical_context_rejection(sample_packet):
    """M8 Law: Neighbor view must be sorted by ID."""
    from src.core.work import WorkClass
    p2 = WorkerPacket(
        packet_id="100:1",
        work_id="100:2:TEST",
        tick=100,
        world_time=1000,
        seed=43,
        work_class=WorkClass.CRITICAL,
        subject=(V2EntityBuilder(2)
                 .kind("X")
                 .location(1.0, 1.0)
                 .build()),
        neighbor_view=[(10, None), (5, None)], # Unsorted
        work_kind="TEST",
        payload={}
    )
    with pytest.raises(ProtocolViolationError, match="Neighbor view not sorted"):
        ProtocolValidator.validate_packet_batch([p2])

def test_protocol_result_traceability_rejection(sample_packet):
    """M8 Law: Results must link back to a valid source packet."""
    from src.core.work import WorkClass
    result = WorkerResult(
        source_packet_id="UNKNOWN",
        work_id="UNKNOWN",
        entity_id=1,
        work_class=WorkClass.CRITICAL,
        update=EntityUpdate(entity_id=1)
    )
    source_packets = {"100:0": sample_packet}
    with pytest.raises(ProtocolViolationError, match="Orphan result"):
        ProtocolValidator.validate_result_batch([result], source_packets)

def test_protocol_result_id_mismatch_rejection(sample_packet):
    """M8 Law: Result entity ID must match the packet's subject ID."""
    from src.core.work import WorkClass
    result = WorkerResult(
        source_packet_id="100:0",
        work_id=sample_packet.work_id,
        entity_id=999, # Mismatch
        work_class=sample_packet.work_class,
        update=EntityUpdate(entity_id=999)
    )
    source_packets = {"100:0": sample_packet}
    with pytest.raises(ProtocolViolationError, match="Result entity mismatch"):
        ProtocolValidator.validate_result_batch([result], source_packets)

def test_protocol_duplicate_result_rejection(sample_packet):
    """M8 Law: Duplicate authoritative results for same entity must be rejected."""
    from src.core.work import WorkClass
    res1 = WorkerResult(
        source_packet_id="100:0", 
        work_id=sample_packet.work_id,
        entity_id=1, 
        work_class=sample_packet.work_class,
        update=EntityUpdate(1)
    )
    # Note: Validator doesn't know about packet IDs for results directly, 
    # but it checks entity_id uniqueness in one batch.
    with pytest.raises(ProtocolViolationError, match="Duplicate authoritative result"):
        ProtocolValidator.validate_result_batch([res1, res1], {"100:0": sample_packet})
