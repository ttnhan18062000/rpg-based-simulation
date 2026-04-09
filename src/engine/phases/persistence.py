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

# Redis/MsgPack are optional infrastructure dependencies
try:
    import redis as syncredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

logger = logging.getLogger(__name__)

class PersistencePhase(EnginePhase):
    """Handle external publishing (Kafka/Redis) and final state synchronization."""

    def __init__(self) -> None:
        super().__init__()
        self._last_published_slim: dict[int, Any] = {}
    
    @property
    def contract(self) -> PhaseContract:
        from src.engine.phases.contract import PhaseContract, PhaseAccess
        return PhaseContract(
            name="Persistence",
            description="Publishing snapshots and syncing final AI states.",
            permissions={
                "world": PhaseAccess.READ,
                "config": PhaseAccess.READ,       # Needed for publish thresholds
                "tick_applied": PhaseAccess.READ,
                "tick_events": PhaseAccess.READ,  # Needed for stream telemetry
                "emit": PhaseAccess.READ
            }
        )

    def execute(self, ctx: EngineContext) -> None:
        tick = ctx.world.tick
        applied = ctx.tick_applied
        
        # 1. Redis Streaming (Canonical Map-Stream - Pillar 5)
        try:
            from src.api.redis_client import get_sync_redis
            from src.api.presenters.entity_presenter import EntityPresenter
            from src.api.presenters.world_presenter import WorldPresenter
            r = get_sync_redis()
            
            # Convert to Slim Schema (Filtered for performance/isolation)
            from src.core.models.snapshot import Snapshot
            snap = Snapshot.from_world(ctx.world)
            
            loot_duration = ctx.config.loot_duration if hasattr(ctx.config, "loot_duration") else 10.0
            new_slim = {}
            for eid, e in snap.entities.items():
                if not e.combat.alive: continue
                new_slim[eid] = EntityPresenter.to_slim_schema(e, loot_duration=loot_duration)

            # Compute Delta
            from src.api.schemas import EventSchema
            changed = []
            removed = []
            for eid, e in new_slim.items():
                old_e = self._last_published_slim.get(eid)
                if old_e is None or old_e != e:
                    changed.append(e.model_dump())
            for eid in self._last_published_slim:
                if eid not in new_slim:
                    removed.append(eid)

            serialized_events = [
                EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                            entity_ids=list(ev.entity_ids), metadata=ev.metadata).model_dump()
                for ev in ctx.tick_events
            ]

            # Compute Rich & Compact Payloads (Canonicalization - Pillar 5)
            rich_payload = WorldPresenter.to_compact_tick(snap, ctx.tick_events, mode="rich")
            compact_payload = WorldPresenter.to_compact_tick(snap, ctx.tick_events, mode="compact")

            # Publish to Redis Stream if non-empty or heartbeat
            import json
            from src.utils.serialization import SimulationJSONEncoder
            
            if changed or removed or serialized_events or tick % 20 == 0:
                delta = {
                    "tick": tick,
                    "changed": changed,
                    "removed": removed,
                    "events": serialized_events,
                }
                
                r.xadd("sim:stream", {
                    "payload": json.dumps(delta),
                    "rich": json.dumps(rich_payload, cls=SimulationJSONEncoder),
                    "compact": json.dumps(compact_payload, cls=SimulationJSONEncoder),
                })
            
            self._last_published_slim = new_slim
            
        except Exception as e:
            logger.error("Tick %d: Failed to publish to Redis stream: %s", tick, e)

        # 2. Kafka Publishing (Analytics & Persistence)
        try:
            from src.api.kafka_client import get_kafka_producer
            producer = get_kafka_producer()
        except Exception as e:
            logger.warning("Tick %d: Kafka producer unavailable, skipping persistence: %s", tick, e)
            producer = None
            
        if not producer:
            return

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
                    from src.actions.base import ActionBatch
                    batch = ActionBatch(tick=tick, proposals=applied)
                    producer.produce(
                        KAFKA_TOPIC_EVENTS,
                        key=str(tick),
                        value=SimulationSerializer.dumps(batch)
                    )
                    producer.poll(0)
                    
        except Exception as e:
            logger.error("Tick %d: Failed to publish to Kafka: %s", tick, e)
