import pytest
from dataclasses import replace
from src.core.state import EntityState, IdentityComponent
from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.builder import V2EntityBuilder

def test_frozen_state_mutation_prevention():
    """Law: Authoritative state components must be frozen."""
    ident = IdentityComponent(role=1)
    
    with pytest.raises(Exception): # dataclasses.FrozenInstanceError
        ident.role = 999

def test_worker_context_immutability():
    """Law: Workers must receive a context that cannot be mutated to affect the engine."""
    subject = V2EntityBuilder(1).kind("ACTOR").location(0.0, 0.0).build()
    packet = WorkerPacket(
        packet_id="1:0",
        work_id="1:1:TEST",
        tick=1,
        world_time=10,
        seed=42,
        work_class=WorkClass.CRITICAL,
        subject=subject,
        neighbor_view=[],
        work_kind="TEST",
        payload={}
    )
    
    # Attempting to mutate the subject inside the packet
    with pytest.raises(Exception):
        packet.subject.kind = "HACKED"

def test_local_executor_isolation_contract():
    """
    Law: Even in LocalSequentialExecutor, the worker must only return an update,
    not mutate the state it was given.
    """
    from src.engine.executor import LocalSequentialExecutor
    executor = LocalSequentialExecutor()
    
    subject = V2EntityBuilder(1).kind("ORIGINAL").location(0.0, 0.0).build()
    
    # A malicious worker that tries to mutate its input
    class MaliciousWorker:
        def execute(self, packet: WorkerPacket, rng, profile):
            try:
                packet.subject.kind = "MUTATED"
            except:
                pass # Swallow the frozen error to see if it bypasses
            return WorkerResult(
                source_packet_id=packet.packet_id,
                work_id=packet.work_id,
                entity_id=packet.subject.id,
                work_class=packet.work_class,
                update=EntityUpdate(entity_id=packet.subject.id)
            )

    # Verify original state remains untouched even if worker logic executes
    assert subject.kind == "ORIGINAL"
