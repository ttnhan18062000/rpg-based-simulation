from __future__ import annotations

import logging
import time
import random
from typing import TYPE_CHECKING, Callable

from src.actions.base import ActionProposal
from src.core.models.enums import AIState, ActionType, Domain
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.gameplay.faction import Faction, FactionRegistry
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
from src.systems.lifecycle.world_evolution_system import WorldEvolutionSystem
from src.systems.infrastructure.telemetry_system import TelemetrySystem
from src.systems.world.generator import EntityGenerator
from src.systems.social.knowledge_propagation_system import KnowledgePropagationSystem
from src.platform.rng import DeterministicRNG
from src.utils.metrics import SIM_TICK_DURATION

# Engine Phases (Decomposition Step 7)
from src.engine.phases.context import EngineContext
from src.engine.phases.presystems import PreSystemsPhase
from src.engine.phases.scheduling import SchedulingPhase
from src.engine.phases.collection import CollectionPhase
from src.engine.phases.resolution import ResolutionPhase
from src.engine.phases.cleanup import CleanupPhase
from src.engine.phases.finalization import FinalizationPhase
from src.engine.phases.persistence import PersistencePhase

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.world_state import WorldState
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
        "_history_system",
        "_social_registry",
        "_phases"
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
        social_registry: SocialRegistry | None = None,
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
        
        from src.core.models.social import SocialRegistry
        self._social_registry = social_registry or SocialRegistry()
        self._world.social_registry = self._social_registry
        
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
        from src.systems.social.knowledge_propagation_system import KnowledgePropagationSystem
        from src.systems.social.group_system import GroupSystem
        from src.systems.infrastructure.history_system import HistorySystem
        self._system_manager.register(StrategySystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(KnowledgePropagationSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(GroupSystem(config, self._rng), config.subsystem_rate_core)
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
        self._system_manager.register(KnowledgePropagationSystem(config, self._rng), config.subsystem_rate_environment)
        
        from src.systems.world.regional_consequence_system import RegionalConsequenceSystem
        from src.systems.world.strategy_world_integration_system import StrategicWorldIntegrationSystem
        self._system_manager.register(RegionalConsequenceSystem(config, self._rng), config.subsystem_rate_environment)
        self._system_manager.register(StrategicWorldIntegrationSystem(config, self._rng), config.subsystem_rate_environment)
        
        from src.systems.infrastructure.event_system import EventBus, TelemetryBridge
        self._world.event_bus = EventBus()
        self._telemetry_bridge = TelemetryBridge(self._world, self._emit)
        self._telemetry_bridge.attach(self._world.event_bus)
        
        # Orchestration Phases (Prioritized order as per TCK-20260330)
        self._phases = [
            PreSystemsPhase(),
            SchedulingPhase(),
            CollectionPhase(),
            ResolutionPhase(),
            CleanupPhase(),
            FinalizationPhase(),
            PersistencePhase()
        ]
        
        # Initialize Systems
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
        """Execute one complete tick cycle using decomposed Phases (AOA Orchestration)."""
        self._logger.extra['tick'] = self._world.tick
        self._tick_events = []
        
        # Initialize Tick Context
        ctx = EngineContext(
            config=self._config,
            world=self._world,
            action_queue=self._action_queue,
            worker_pool=self._worker_pool,
            conflict_resolver=self._conflict_resolver,
            generator=self._generator,
            rng=self._rng,
            faction_reg=self._faction_reg,
            system_manager=self._system_manager,
            action_system=self._action_system,
            hero_lifecycle=self._hero_lifecycle,
            emit=self._emit, social_registry=self._social_registry, tick_events=self._tick_events,
            tick_start_time=time.perf_counter()
        )

        # Run Phase Sequence
        from src.engine.phase_guard import PhaseGuard
        for phase in self._phases:
            try:
                with PhaseGuard(ctx, phase.contract) as guarded_ctx:
                    phase.execute(guarded_ctx)
            except Exception as e:
                self._logger.error("Phase %s failed: %s", phase.contract.name, e, exc_info=True)
                # If a phase fails, we might want to halt the tick or continue depending on config
                if not self._config.ignore_phase_errors:
                    raise
            
            # Post-Phase Infrastructure Sync (Pillar 1 Stabilization)
            if ctx.tick_new_entities:
                for entity in ctx.tick_new_entities:
                    self._world.add_entity(entity)
                # Clear the queue to prevent double-application in later phases (context is shared)
                ctx.tick_new_entities = []

        # Sync results for legacy API/Recorder
        self._last_applied = ctx.tick_applied


    def _check_level_ups(self) -> None:
        """DEPRECATED: Level-up logic moved to ProgressionSystem."""
        # This is a shim for legacy tests that mock this method.
        pass

    def _phase_cleanup(self) -> None:
        """AOA Shim: Manually triggers the CleanupPhase for integration tests."""
        from src.engine.phases.cleanup import CleanupPhase
        from src.engine.phases.context import EngineContext
        
        ctx = EngineContext(
            config=self._config,
            world=self._world,
            action_queue=self._action_queue,
            worker_pool=self._worker_pool,
            conflict_resolver=self._conflict_resolver,
            generator=self._generator,
            rng=self._rng,
            faction_reg=self._faction_reg,
            system_manager=self._system_manager,
            action_system=self._action_system,
            hero_lifecycle=self._hero_lifecycle,
            emit=self._emit, social_registry=self._social_registry, tick_events=self._tick_events,
            tick_start_time=time.perf_counter()
        )
        CleanupPhase().execute(ctx)

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
                hero.combat.max_hp = int(hero.combat.max_hp * 1.1)
                hero.combat.hp = hero.combat.max_hp
            elif m.buff_type == "atk":
                # AOA Stabilization: Use atk_base as atk is a read-only property
                hero.combat.atk_base = int(hero.combat.atk_base * 1.1)
