"""EngineManager — singleton wrapper that runs the WorldLoop on a background thread.

The API reads from an atomically-swapped immutable Snapshot; the WorldLoop
mutates WorldState exclusively on its own thread (Single-Writer preserved).
"""

from __future__ import annotations

import logging
import threading
import time
import typing
import uuid
from typing import TYPE_CHECKING

from src_legacy.ai.brain import AIBrain
from src_legacy.core.gameplay.buildings import Building
from src_legacy.core.models.enums import AIState, Domain, EnemyTier, EntityRole, Material
from src_legacy.core.gameplay.faction import Faction, FactionRegistry
from src_legacy.core.world.grid import Grid
from src_legacy.core.entities.entity import Entity, Vector2
from src_legacy.core.world.regions import Region, Location
from src_legacy.core.world.resource_nodes import ResourceNode
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.world_state import WorldState
from src_legacy.actions.base import ActionBatch
from src_legacy.engine.conflict_resolver import ConflictResolver
from src_legacy.engine.worker_pool import WorkerPool
from src_legacy.engine.world_loop import WorldLoop
from src_legacy.systems.world.generator import EntityGenerator
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.utils.event_log import EventLog, SimEvent
from src_legacy.core.world.world_generator import WorldGenerator

if TYPE_CHECKING:
    from src_legacy.config import SimulationConfig

logger = logging.getLogger(__name__)


class EngineManager:
    """Manages the simulation lifecycle on a background thread.

    Provides thread-safe access to:
      - latest snapshot (atomic reference swap)
      - event log (lock-guarded ring buffer)
      - control commands (start / pause / resume / step / reset)
    """

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self.config = config
        self._tick_rate: float = 0.05  # seconds between ticks (20 tps default)

        # Simulation components (built in _build)
        self._rng: DeterministicRNG | None = None
        self._loop: WorldLoop | None = None
        self._worker_pool: WorkerPool | None = None
        
        self._tick_payloads: dict[str, Any] = {}
        self._payload_lock = threading.Lock()
        
        # AOA Phase 6: Unified Transport State (Infrastructure Hardening)
        self._last_published_slim: dict[int, Any] = {}

        # Thread-safe shared state
        self._snapshot_lock = threading.Lock()
        self._latest_snapshot: Snapshot | None = None
        self._event_log = EventLog()

        # Counters
        self._total_spawned: int = 0
        self._total_deaths: int = 0

        # Control
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._step_requested = threading.Event()
        self._stop_requested = threading.Event()
        
        # Caching (Infrastructure Hardening)
        self._static_data_cache: typing.Any | None = None
        self._static_data_lock = threading.Lock()

        self._build()
        
        # Wrapped logger (Phase L3 Logging)
        from src_legacy.utils.logging import RobustLoggerAdapter
        self._logger = RobustLoggerAdapter(logger, {'component': 'engine_manager', 'tick': -1})

    # -- public properties --

    @property
    def running(self) -> bool:
        return self._running.is_set()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    @property
    def tick_rate(self) -> float:
        return self._tick_rate

    @tick_rate.setter
    def tick_rate(self, value: float) -> None:
        self._tick_rate = max(0.01, min(value, 2.0))

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    @property
    def total_spawned(self) -> int:
        return self._total_spawned

    @property
    def total_deaths(self) -> int:
        return self._total_deaths

    # -- listeners --

    def add_tick_listener(self, cb: typing.Callable[[Snapshot, list[SimEvent]], None]) -> None:
        with self._listeners_lock:
            if cb not in self._listeners:
                self._listeners.append(cb)

    def remove_tick_listener(self, cb: typing.Callable[[Snapshot, list[SimEvent]], None]) -> None:
        with self._listeners_lock:
            if cb in self._listeners:
                self._listeners.remove(cb)

    # -- snapshot access --

    def get_snapshot(self) -> Snapshot | None:
        with self._snapshot_lock:
            return self._latest_snapshot

    def get_grid(self) -> Grid | None:
        """Return the grid from the latest snapshot (static data)."""
        snap = self.get_snapshot()
        return snap.grid if snap else None

    @property
    def world(self) -> WorldState:
        """AOA Shim: Direct access to the loop's world (for integration tests)."""
        if self._loop is None:
            raise RuntimeError("EngineManager world accessed before build")
        return self._loop.world

    def get_static_data(self) -> typing.Any | None:
        """Return cached static world data or generate it if missing."""
        snap = self.get_snapshot()
        if snap is None:
            return None
            
        with self._static_data_lock:
            if self._static_data_cache is None:
                from src_legacy.api.presenters.world_presenter import WorldPresenter
                self._static_data_cache = WorldPresenter.to_static_data_response(snap)
            return self._static_data_cache

    def clear_static_cache(self) -> None:
        """Invalidate the static data cache."""
        with self._static_data_lock:
            self._static_data_cache = None

    def get_tick_payload(self, mode: str) -> typing.Any | None:
        """Return the pre-computed payload for the latest tick in the given mode."""
        with self._payload_lock:
            return self._tick_payloads.get(mode)

    # -- lifecycle --

    def start(self) -> None:
        if self._running.is_set():
            return
        self._stop_requested.clear()
        self._paused.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, name="engine-loop", daemon=True)
        self._thread.start()
        # Start resource metrics collector
        try:
            from src_legacy.utils.resource_collector import start_resource_collector
            start_resource_collector()
        except Exception:
            self._logger.debug("Resource collector not started", exc_info=True)
        self._logger.info("EngineManager started (tick_rate=%.3fs)", self._tick_rate)

    def pause(self) -> None:
        self._paused.set()
        logger.info("EngineManager paused at tick %d", self._current_tick())

    def resume(self) -> None:
        self._paused.clear()
        logger.info("EngineManager resumed at tick %d", self._current_tick())

    def step(self) -> None:
        """Execute exactly one tick (must be paused)."""
        if not self._paused.is_set():
            self.pause()
        self._step_requested.set()

    def stop(self) -> None:
        self._stop_requested.set()
        self._paused.clear()
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        if self._worker_pool:
            self._worker_pool.shutdown()
        self._logger.info("EngineManager stopped.")

    def reset(self) -> None:
        """Stop, rebuild, and leave in paused state ready to start."""
        self.stop()
        self._event_log.clear()
        self._total_spawned = 0
        self._total_deaths = 0
        self.clear_static_cache()
        self._build()
        # Take initial snapshot
        if self._loop:
            snap = self._loop.create_snapshot()
            with self._snapshot_lock:
                self._latest_snapshot = snap
        logger.info("EngineManager reset.")

    # -- internals --

    def _build(self) -> None:
        """Construct all simulation components from config."""
        cfg = self._config
        self._rng = DeterministicRNG(cfg.world_seed)
        self.clear_static_cache()
        
        # --- KAFKA RECOVERY ---
        world = self._try_recover_world(cfg)
        if world is not None:
            generator = EntityGenerator(cfg, self._rng)
            self._finalize_build(world, cfg, generator)
            return
            
        # --- GENERATE NEW WORLD (epic-05 EngineManager decomposition) ---
        generator_service = WorldGenerator(cfg, self._rng)
        world, generator = generator_service.generate()
        self._total_spawned = generator_service.total_spawned
        self._finalize_build(world, cfg, generator)

    def _finalize_build(self, world: WorldState, cfg: SimulationConfig, generator: EntityGenerator) -> None:
        """Finalize engine setup: create loop, brain, worker pool, and initial snapshot."""
        faction_reg = FactionRegistry.default()
        brain = AIBrain(cfg, self._rng, faction_reg)
        assert self._rng is not None
        self._worker_pool = WorkerPool(cfg, brain, self._rng)
        conflict_resolver = ConflictResolver(cfg, self._rng)

        self._loop = WorldLoop(
            config=cfg, world=world, worker_pool=self._worker_pool,
            conflict_resolver=conflict_resolver, generator=generator,
            faction_reg=faction_reg, rng=self._rng,
        )

        # Initial snapshot
        snap = self._loop.create_snapshot()
        with self._snapshot_lock:
            self._latest_snapshot = snap

    def _try_recover_world(self, cfg: SimulationConfig) -> WorldState | None:
        """Attempt to recover the simulation state from Kafka."""
        from src_legacy.api.kafka_client import create_kafka_consumer, KAFKA_TOPIC_SNAPSHOTS, KAFKA_TOPIC_EVENTS, HAS_KAFKA
        from src_legacy.utils.serialization import SimulationSerializer
        from src_legacy.core.models.snapshot import Snapshot
        
        if not HAS_KAFKA:
            return None
            
        from confluent_kafka import TopicPartition, OFFSET_BEGINNING
        
        # Unique consumer group for startup so it doesn't mess with other readers
        consumer = create_kafka_consumer(f"sim_startup_{uuid.uuid4().hex}")
        if not consumer:
            return None
            
        try:
            # 1. Recover latest Compacted Snapshot
            consumer.assign([TopicPartition(KAFKA_TOPIC_SNAPSHOTS, 0)])
            consumer.seek(TopicPartition(KAFKA_TOPIC_SNAPSHOTS, 0, OFFSET_BEGINNING))
            
            latest_snap = None
            timeout_strikes = 0
            # Read until we hit EOF for the partition
            while timeout_strikes < 3:
                msg = consumer.poll(1.0)
                if msg is None:
                    timeout_strikes += 1
                    continue
                timeout_strikes = 0  # Reset on successful poll (AOA stabilization)
                
                if msg.error():
                    break
                    
                try:
                    obj = SimulationSerializer.loads(msg.value(), Snapshot)
                    if obj and hasattr(obj, "tick"):
                        # Keep the latest one we find (compacted topics)
                        latest_snap = obj
                except Exception as e:
                    logger.debug("Failed to deserialize snapshot: %s", e)
                    
            if not latest_snap:
                logger.debug("Kafka Setup: No snapshot found on sim.snapshots")
                return None
                
            logger.info("Kafka Setup: Recovered snapshot at tick %d", latest_snap.tick)
            
            spatial = SpatialHash(cfg.spatial_cell_size)
            world = WorldState.from_snapshot(latest_snap, spatial)
            
            # 2. Replay subsequent Events
            consumer.assign([TopicPartition(KAFKA_TOPIC_EVENTS, 0)])
            logger.critical("="*80)
            logger.critical("SIMULATION_REPLAYER_ACTIVE tick=%d", world.tick)
            logger.critical("="*80)
            
            recovery_rng = DeterministicRNG(cfg.world_seed)
            resolver = ConflictResolver(cfg, recovery_rng)
            replayed_ticks = 0
            timeout_strikes = 0
            
            while timeout_strikes < 3:
                msg = consumer.poll(0.5)
                if msg is None:
                    timeout_strikes += 1
                    continue
                timeout_strikes = 0
                
                if msg.error():
                    break
                    
                try:
                    batch = SimulationSerializer.loads(msg.value(), ActionBatch)
                    if batch and batch.tick > world.tick:
                        applied = resolver.resolve(batch.proposals, world)
                        
                        # Unified Phase: Apply deferred side-effects (LOOT, HARVEST, Skill damage)
                        from src_legacy.systems.gameplay.action_system import ActionSystem
                        ActionSystem.apply_action_state_transitions(world, cfg, applied, recovery_rng)
                        
                        world.tick = batch.tick
                        replayed_ticks += 1

                except Exception as e:
                    logger.warning("Failed to deserialize event: %s", e)
                    
            if replayed_ticks > 0:
                logger.info("Kafka Setup: Replayed %d ticks of events. Current synchronized tick: %d", 
                            replayed_ticks, world.tick)
                            
            return world
            
        except Exception as e:
            # Downgrade to debug if it's a state error (e.g. empty topics during E2E start)
            if "Erroneous state" in str(e) or "_STATE" in str(e):
                logger.debug("Kafka recovery skipped (topic likely empty): %s", e)
            else:
                logger.error("Failed to recover world from Kafka: %s", e)
            return None
        finally:
            consumer.close()

    def _run_loop(self) -> None:
        """Background thread main loop."""
        logger.info("Engine thread started.")
        assert self._loop is not None

        while not self._stop_requested.is_set():
            # Handle pause
            if self._paused.is_set() and not self._step_requested.is_set():
                time.sleep(0.01)
                continue

            single_step = self._step_requested.is_set()
            if single_step:
                self._step_requested.clear()

            # Execute one tick
            _tick_start = time.perf_counter()
            alive_before = set(self._loop.world.entities.keys())
            can_continue = self._loop.tick_once()

            if not can_continue:
                self._apply_tick_outputs()
                logger.info("Simulation ended at tick %d.", self._loop.world.tick)
                break

            # Track spawns / deaths
            alive_after = set(self._loop.world.entities.keys())
            new_ids = alive_after - alive_before
            dead_ids = alive_before - alive_after
            self._total_spawned += len(new_ids)
            self._total_deaths += len(dead_ids)

            from src_legacy.utils.metrics import (
                ACTIVE_ENTITIES, TOTAL_SPAWNS, TOTAL_DEATHS,
                SIM_CURRENT_TICK, SIM_TICKS_PER_SECOND,
            )

            current_tick = self._loop.world.tick
            ACTIVE_ENTITIES.set(len(alive_after))
            SIM_CURRENT_TICK.set(current_tick)
            if new_ids:
                TOTAL_SPAWNS.inc(len(new_ids))
            if dead_ids:
                TOTAL_DEATHS.inc(len(dead_ids))

            # Throughput
            tick_elapsed = time.perf_counter() - _tick_start
            if tick_elapsed > 0:
                SIM_TICKS_PER_SECOND.set(1.0 / tick_elapsed)

            self._apply_tick_outputs()

            # Rate limiting
            if not single_step:
                time.sleep(self._tick_rate)

        self._running.clear()
        logger.info("Engine thread exited.")

    def _apply_tick_outputs(self) -> None:
        """Atomic snapshot swap for API consumers (AOA Pillar 1)."""
        assert self._loop is not None
        
        snap = self._loop.create_snapshot()
        events = list(self._loop.tick_events)
        
        with self._snapshot_lock:
            self._latest_snapshot = snap
        if events:
            self._event_log.append_many(events)
        
        # Note: Canonical persistence (Kafka/Redis) is now handled 
        # inside the engine cycle (PersistencePhase).

    def _current_tick(self) -> int:
        if self._loop:
            return self._loop.world.tick
        return 0
