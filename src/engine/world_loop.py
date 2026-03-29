"""WorldLoop — the authoritative 4-phase tick engine.

Phase cycle:
  1. Scheduling — identify ready entities, dispatch to workers
  2. Wait & Collect — drain the action queue
  3. Conflict Resolution & Application — validate + apply proposals
  4. Cleanup & Advancement — remove dead, territory effects, advance tick
"""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.gameplay.effects import EffectType, territory_debuff
from src.core.models.enums import AIState, ActionType, Domain
from src.core.entities.entity import Entity, Stats, Vector2, Inventory
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.models.snapshot import Snapshot
from src.engine.action_queue import ActionQueue
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.infrastructure.manager import SystemManager
from src.systems.infrastructure.base import SystemContext
from src.systems.gameplay.combat_system import CombatSystem
from src.systems.lifecycle.progression_system import ProgressionSystem
from src.systems.world.world_object_system import WorldObjectSystem
from src.systems.gameplay.quest_system import QuestSystem
from src.systems.calamity.calamity_system import CalamitySystem
from src.systems.world.environment_system import EnvironmentSystem
from src.systems.gameplay.economy_system import EconomySystem
from src.systems.gameplay.action_system import ActionSystem
from src.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src.systems.infrastructure.telemetry_system import TelemetrySystem
from src.systems.lifecycle.world_evolution_system import WorldEvolutionSystem
from src.systems.world.generator import EntityGenerator
from src.utils.metrics import SIM_TICK_DURATION

import pickle
from src.api.kafka_client import get_kafka_producer, KAFKA_TOPIC_EVENTS, KAFKA_TOPIC_SNAPSHOTS

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
    from src.platform.rng import DeterministicRNG
    from src.utils.replay import ReplayRecorder

logger = logging.getLogger(__name__)


class WorldLoop:
    """The heartbeat of the simulation.

    Single-threaded mutation of WorldState through a 4-phase cycle:
      1. Scheduling — identify ready entities, dispatch to workers
      2. Wait & Collect — drain the action queue
      3. Conflict Resolution & Application — validate + apply proposals
      4. Cleanup & Advancement — remove dead, territory effects, advance tick
    """

    __slots__ = (
        "_config",
        "_world",
        "_action_queue",
        "_worker_pool",
        "_conflict_resolver",
        "_generator",
        "_recorder",
        "_last_applied",
        "_tick_events",
        "_faction_reg",
        "_rng",
        "_system_manager",
        "_action_system",
        "_hero_lifecycle",
        "_logger",
        "_telemetry_bridge",
        "_history_system"
    )

    def __init__(
        self,
        config: SimulationConfig,
        world: WorldState,
        worker_pool: WorkerPool,
        conflict_resolver: ConflictResolver,
        generator: EntityGenerator,
        recorder: ReplayRecorder | None = None,
        faction_reg: FactionRegistry | None = None,
        rng: DeterministicRNG | None = None,
    ) -> None:
        self._config = config
        self._world = world
        self._action_queue = ActionQueue()
        self._worker_pool = worker_pool
        self._conflict_resolver = conflict_resolver
        self._generator = generator
        self._recorder = recorder
        self._last_applied: list[ActionProposal] = []
        self._tick_events: list = []
        self._faction_reg = faction_reg or FactionRegistry.default()
        self._rng = rng
        
        # Wrapped logger for automatic context (Phase L3 Logging)
        from src.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'tick': 0, 'component': 'world_loop'})
        
        # Initialize Systems (Phase 4)
        self._system_manager = SystemManager(config, rng or DeterministicRNG(0))
        self._system_manager.register(CombatSystem(config, self._rng), config.subsystem_rate_core)
        self._system_manager.register(ProgressionSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(WorldObjectSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(QuestSystem(config, self._rng), config.subsystem_rate_economy)
        self._system_manager.register(CalamitySystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(EnvironmentSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(EconomySystem(config, self._rng), config.subsystem_rate_economy)
        
        from src.systems.world.strategy_system import StrategySystem
        from src.systems.calamity.calamity_evolution import CalamityEvolutionSystem
        from src.systems.infrastructure.history_system import HistorySystem
        self._system_manager.register(StrategySystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(CalamityEvolutionSystem(config, self._rng), config.subsystem_rate_environment)
        self._history_system = HistorySystem(config, self._rng)
        self._system_manager.register(self._history_system, config.subsystem_rate_environment)
        
        # ActionSystem for post-resolution hooks
        self._action_system = ActionSystem(config, self._rng)
        
        # Dedicated Epic-17 Hero Mechanics
        self._hero_lifecycle = HeroLifecycleSystem(config, self._rng)
        self._system_manager.register(self._hero_lifecycle, config.subsystem_rate_core)
        
        # New decoupled systems (Phase 2)
        self._system_manager.register(WorldEvolutionSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(TelemetrySystem(config, self._rng), config.subsystem_rate_economy)
        
        from src.systems.infrastructure.event_system import EventBus, TelemetryBridge
        self._world.event_bus = EventBus()
        self._telemetry_bridge = TelemetryBridge(self._world, self._emit)
        self._telemetry_bridge.attach(self._world.event_bus)
        
        # Explicit initialization of all systems with context
        self._system_manager.init_all(world, generator, self._faction_reg, self._emit)
        self._action_system.on_init(SystemContext(config, world, self._rng, generator, self._faction_reg, self._emit))

    @property
    def world(self) -> WorldState:
        return self._world

    @property
    def last_applied(self) -> list[ActionProposal]:
        """Actions applied during the most recent tick."""
        return self._last_applied

    @property
    def tick_events(self) -> list:
        """Enriched events emitted during the most recent tick."""
        return self._tick_events

    def _emit(self, category: str, message: str,
              entity_ids: tuple[int, ...] = (), metadata: dict | None = None) -> None:
        from src.utils.event_log import SimEvent
        self._tick_events.append(SimEvent(
            tick=self._world.tick,
            category=category,
            message=message,
            entity_ids=entity_ids,
            metadata=metadata,
        ))

    def tick_once(self) -> bool:
        """Execute a single tick. Returns False if simulation should stop."""
        tick = self._world.tick
        alive_count = sum(1 for e in self._world.entities.values() if e.combat.alive and e.kind != "generator")

        if alive_count == 0 and tick > 0:
            self._logger.info("Tick %d: No entities alive — simulation ended.", tick, extra={'tick': tick})
            return False

        if tick >= self._config.max_ticks:
            self._logger.info("Tick %d: Max ticks reached.", tick, extra={'tick': tick})
            return False

        self._step()
        self._world.tick += 1
        return True

    def create_snapshot(self) -> Snapshot:
        """Create an immutable snapshot of the current world state."""
        return Snapshot.from_world(self._world)

    def run(self) -> None:
        """Execute the simulation until max_ticks or no entities remain."""
        self._logger.extra['tick'] = self._world.tick
        self._logger.info("=== Simulation started (seed=%d) ===", self._world.seed)

        self._world.tick = 0
        while self._world.tick < self._config.max_ticks:
            if not self.tick_once():
                break

            if self._world.tick % 50 == 0:
                alive_count = sum(1 for e in self._world.entities.values() if e.combat.alive and e.kind != "generator")
                self._logger.info(
                    "Tick %d: %d entities alive",
                    self._world.tick,
                    alive_count,
                    extra={'tick': self._world.tick}
                )

        self._logger.info("=== Simulation finished at tick %d ===", self._world.tick, extra={'tick': self._world.tick})
        if self._recorder:
            self._recorder.flush()

    def _step(self) -> None:
        """Execute one complete tick cycle (Phase 4 Orchestration)."""
        self._logger.extra['tick'] = self._world.tick
        self._tick_events = []
        tick = self._world.tick
        t0 = time.perf_counter()

        # --- Phase 1: Pre-Action Systems (Calamities, Environment, etc.) ---
        # Note: These run at various rates via the SystemManager
        with SIM_TICK_DURATION.labels(phase="subsystems").time():
            self._system_manager.tick(self._world, tick)

        # --- Phase 2: Action Generation & Resolution ---
        self._phase_generators()
        
        with SIM_TICK_DURATION.labels(phase="scheduling").time():
            ready_entities = self._phase_scheduling()

        applied: list[ActionProposal] = []
        if ready_entities:
            # Wait & Collect
            with SIM_TICK_DURATION.labels(phase="collect").time():
                snapshot = Snapshot.from_world(self._world)
                self._worker_pool.dispatch(ready_entities, snapshot, self._action_queue)
                proposals = self._action_queue.drain()

                # Chaos Resilience
                if len(proposals) < len(ready_entities):
                    acted_ids = {p.actor_id for p in proposals}
                    for entity in ready_entities:
                        if entity.id not in acted_ids:
                            from src.utils.metrics import SIM_INVALID_ACTIONS_TOTAL
                            SIM_INVALID_ACTIONS_TOTAL.labels(action_type="rest", reason="timeout").inc()
                            
                            proposals.append(ActionProposal(
                                actor_id=entity.id,
                                verb=ActionType.REST,
                                target=None,
                                reason="Chaos Drop / Worker Timeout",
                                new_ai_state=int(entity.mind.ai_state)
                            ))

            # Resolution & Application
            with SIM_TICK_DURATION.labels(phase="resolve").time():
                pre_positions = {e.id: (e.spatial.pos.x, e.spatial.pos.y) for e in self._world.entities.values()}
                applied = self._conflict_resolver.resolve(proposals, self._world)
                self._last_applied = applied
                self._update_ai_states(applied)

                # --- Phase 3: Post-Action Tactical Hooks ---
                ctx = SystemContext(self._config, self._world, self._rng, self._generator, self._faction_reg, self._emit)
                self._action_system.handle_tactical_maneuvers(ctx, applied, pre_positions)
                
                # Execute state mutations (items, loot, harvest) and visualization updates
                with SIM_TICK_DURATION.labels(phase="item_processing").time():
                    self._action_system.process_applied_actions(ctx, applied)

                # Emit standardized events
                _cat_map = {"REST": "rest", "MOVE": "movement", "USE_ITEM": "item", "LOOT": "loot", "HARVEST": "harvest"}
                for action in applied:
                    if action.verb.name in ("ATTACK", "USE_SKILL"):
                        continue
                    involved = [action.actor_id]
                    if isinstance(action.target, int): involved.append(action.target)
                    cat = _cat_map.get(action.verb.name, action.verb.name.lower())
                    self._emit(cat, f"Entity {action.actor_id}: {action.verb.name} → {action.reason}", entity_ids=tuple(involved))

        t4 = time.perf_counter()
        if ready_entities:
            SIM_TICK_DURATION.labels(phase="total_active").observe(t4 - t0)
        else:
            SIM_TICK_DURATION.labels(phase="total_idle").observe(t4 - t0)

        # --- Phase 5: Persistence & Streaming ---
        with SIM_TICK_DURATION.labels(phase="persistence").time():
            self._handle_kafka_publishing(tick, applied)
            self._handle_redis_publishing(tick, applied)

        # --- Phase 4: Cleanup & Advancement ---
        with SIM_TICK_DURATION.labels(phase="cleanup").time():
            self._phase_cleanup()

    def _handle_kafka_publishing(self, tick: int, applied: list[ActionProposal]) -> None:
        """Publish snapshots and events to Kafka for persistence and analytics."""
        from src.utils.metrics import SIM_KAFKA_PUBLISH_DURATION
        
        # publish immutable snapshot to Kafka every 1000 ticks for compaction
        if tick % 1000 == 0:
            producer = get_kafka_producer()
            if producer:
                try:
                    with SIM_KAFKA_PUBLISH_DURATION.labels(type="snapshot").time():
                        snap = Snapshot.from_world(self._world)
                        producer.produce(
                            KAFKA_TOPIC_SNAPSHOTS,
                            key="latest", # use static key for log compaction
                            value=pickle.dumps(snap)
                        )
                        producer.poll(0)
                except Exception as e:
                    logger.error("Failed to publish snapshot to Kafka: %s", e)
                    
        # publish deterministic tick events
        if applied:
            producer = get_kafka_producer()
            if producer:
                try:
                    with SIM_KAFKA_PUBLISH_DURATION.labels(type="events").time():
                        payload = {"tick": tick, "proposals": applied}
                        producer.produce(
                            KAFKA_TOPIC_EVENTS,
                            key=str(tick),
                            value=pickle.dumps(payload)
                        )
                        producer.poll(0)
                except Exception as e:
                    logger.error("Failed to publish events to Kafka: %s", e)

    def _handle_redis_publishing(self, tick: int, applied: list[ActionProposal]) -> None:
        """Hook for additional Redis-based persistence (managed primarily by EngineManager)."""
        # We can use this to track secondary Redis tasks if needed.
        # For now, it's a placeholder to satisfy the persistence phase call in _step.
        pass

    def _phase_generators(self) -> None:
        """Run generator entities (immediate, no worker dispatch)."""
        if self._generator.should_spawn(self._world):
            entity = self._generator.spawn(self._world)
            self._world.add_entity(entity)
            logger.info("Tick %d: Spawned %s #%d at %s", self._world.tick, entity.kind, entity.id, entity.spatial.pos)

    def _phase_scheduling(self) -> list:
        """Identify entities ready to act this tick."""
        current_time = float(self._world.tick)
        ready = [
            e
            for e in self._world.entities.values()
            if e.combat.alive and e.kind != "generator" and e.next_act_at <= current_time
        ]
        # Deterministic order: next_act_at, then entity ID
        ready.sort(key=lambda e: (e.next_act_at, e.id))
        return ready

    def _update_ai_states(self, applied: list[ActionProposal]) -> None:
        """Propagate new AI states from brain decisions after action resolution."""
        for proposal in applied:
            entity = self._world.entities.get(proposal.actor_id)
            if entity is None:
                continue
            if proposal.new_ai_state is not None:
                entity.mind.ai_state = AIState(proposal.new_ai_state)
            if proposal.reason:
                entity.mind.last_reason = proposal.reason

    def _phase_cleanup(self) -> None:
        """Remove dead entities, respawn heroes at town, drop loot, rebuild spatial index."""
        dead_ids = [eid for eid, e in self._world.entities.items() if not e.combat.alive]
        for eid in dead_ids:
            entity = self._world.entities.get(eid)
            if entity is None:
                continue

            if entity.identity.faction == Faction.HERO_GUILD and entity.home_pos is not None:
                ctx = SystemContext(self._config, self._world, self._rng, self._generator, self._faction_reg, self._emit)
                resolved = self._hero_lifecycle.process_hero_death(ctx, entity, self._world.tick)
                if resolved:
                    continue

            # Default logic for generic mobs / non-hero entities
            from src.utils.metrics import TOTAL_DEATHS
            TOTAL_DEATHS.inc()

            if entity.inventory:
                dropped = entity.inventory.get_all_item_ids()
                if dropped:
                    self._world.drop_items(entity.spatial.pos, dropped)
                    logger.info(
                        "Tick %d: Entity %d (%s) dropped %d items at %s",
                        self._world.tick, eid, entity.kind, len(dropped), entity.spatial.pos,
                    )

            removed = self._world.remove_entity(eid)
            if removed:
                logger.info("Tick %d: Entity %d (%s Lv%d) died.", self._world.tick, eid, removed.kind, removed.stats.progression.level)
                if hasattr(self._world, "event_bus") and self._world.event_bus:
                    from src.core.data.events import DeathEvent
                    self._world.event_bus.publish(DeathEvent(
                        entity_id=eid, killer_id=None,
                        x=removed.spatial.pos.x, y=removed.spatial.pos.y,
                        level_at_death=removed.stats.progression.level,
                        is_permadeath=True
                    ))

    def _check_endgame_conditions(self) -> bool:
        if self._world.world_age < 50000: return True
        func = sum(1 for b in self._world.buildings if b.is_functional and b.durability > b.max_durability * 0.8)
        if func == len(self._world.buildings): return False
        dest = sum(1 for b in self._world.buildings if not b.is_functional)
        if dest >= 3: return False
        return True

    def _apply_monument_buffs(self, hero) -> None:
        for m in self._world.monuments:
            if m.buff_type == "hp":
                hero.stats.combat.max_hp = int(hero.stats.combat.max_hp * 1.1)
                hero.stats.combat.hp = hero.stats.combat.max_hp
            elif m.buff_type == "atk":
                hero.stats.combat.atk = int(hero.stats.combat.atk * 1.1)
