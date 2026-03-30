from __future__ import annotations
import logging
import pickle
from typing import TYPE_CHECKING
from src.engine.phases.base import EnginePhase
from src.core.models.snapshot import Snapshot
from src.core.models.enums import AIState
from src.api.kafka_client import get_kafka_producer, KAFKA_TOPIC_EVENTS, KAFKA_TOPIC_SNAPSHOTS
from src.utils.metrics import SIM_KAFKA_PUBLISH_DURATION

if TYPE_CHECKING:
    from src.engine.phases.context import EngineContext

logger = logging.getLogger(__name__)

class PersistencePhase(EnginePhase):
    """Handle external publishing (Kafka/Redis) and final state synchronization."""
    
    def execute(self, ctx: EngineContext) -> None:
        tick = ctx.world.tick
        applied = ctx.tick_applied
        
        # 1. Propagate AI State changes from decisions
        for proposal in applied:
            entity = ctx.world.entities.get(proposal.actor_id)
            if entity is None: continue
            if proposal.new_ai_state is not None:
                entity.mind.decision.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.mind.decision.last_reason = proposal.reason

        # 2. Kafka Publishing (Analytics & Persistence)
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
                        value=pickle.dumps(snap)
                    )
                    producer.poll(0)

            # Events: Every tick with successful actions
            if applied:
                with SIM_KAFKA_PUBLISH_DURATION.labels(type="events").time():
                    payload = {"tick": tick, "proposals": applied}
                    producer.produce(
                        KAFKA_TOPIC_EVENTS,
                        key=str(tick),
                        value=pickle.dumps(payload)
                    )
                    producer.poll(0)
                    
        except Exception as e:
            logger.error("Tick %d: Failed to publish to Kafka: %s", tick, e)
