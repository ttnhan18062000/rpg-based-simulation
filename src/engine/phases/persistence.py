from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.core.models.snapshot import Snapshot
from src.core.models.enums import AIState
from src.api.kafka_client import get_kafka_producer, KAFKA_TOPIC_EVENTS, KAFKA_TOPIC_SNAPSHOTS
from src.utils.metrics import SIM_KAFKA_PUBLISH_DURATION
from src.utils.serialization import SimulationSerializer

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

class PersistencePhase(EnginePhase):
    """Handle external publishing (Kafka/Redis) and final state synchronization."""
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Persistence",
            description="Publishing snapshots and syncing final AI states.",
            permissions={
                "world": PhaseAccess.READ,
                "tick_applied": PhaseAccess.READ,
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        tick = ctx.world.tick
        applied = ctx.tick_applied
        
        # Kafka Publishing (Analytics & Persistence)
        producer = get_kafka_producer()
        if not producer: return

        try:
            # Snapshot: Every 1000 ticks or on demand
            if tick % 1000 == 0:
                with SIM_KAFKA_PUBLISH_DURATION.labels(type="snapshot").time():
                    snap = Snapshot.from_world(ctx.world)
                    producer.produce(
                        KAFKA_TOPIC_SNAPSHOTS,
                        key="latest",
                        value=SimulationSerializer.dumps(snap)
                    )
                    producer.poll(0)

            # Events: Every tick with successful actions
            if applied:
                with SIM_KAFKA_PUBLISH_DURATION.labels(type="events").time():
                    # We wrap the payload in a dict; the serializer will handle recursively Pydantic models (proposals)
                    payload = {"tick": tick, "proposals": applied}
                    producer.produce(
                        KAFKA_TOPIC_EVENTS,
                        key=str(tick),
                        value=SimulationSerializer.dumps(payload)
                    )
                    producer.poll(0)
                    
        except Exception as e:
            logger.error("Tick %d: Failed to publish to Kafka: %s", tick, e)
