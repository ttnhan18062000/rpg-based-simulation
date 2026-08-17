from __future__ import annotations
import logging
import threading
import time
from typing import Optional, Any, Dict, List, Callable
import copy

from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile
from src.systems.world_systems.generator import EntityGenerator
from src.api.read_model_cache import ReadModelCache

logger = logging.getLogger(__name__)

class V2EngineManager:
    """
    V2 drop-in replacement for legacy EngineManager.
    Wraps the V2 Kernel and manages the background execution loop.
    """
    def __init__(self, profile: RuntimeProfile, seed: int = 42, entities_count: int = 10):
        self._profile = profile
        self._seed = seed
        self._entities_count = entities_count
        
        self._kernel: Optional[Kernel] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._stop_requested = threading.Event()
        self._step_requested = threading.Event()
        
        self._tick_rate = 0.05  # 20 TPS default
        
        self._latest_state: Optional[AuthoritativeState] = None
        self._latest_snapshot: Dict[str, Any] = {}
        self._read_cache = ReadModelCache()
        self._state_lock = threading.Lock()
        
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._event_listeners = []
        self._listeners_lock = threading.Lock()
        
        # Observability Metrics Initialization
        from collections import deque
        from prometheus_client import CollectorRegistry
        from src.observability.prometheus_collector import PrometheusMetricsCollector
        
        self._tick_times = deque(maxlen=100)
        self._latest_metrics_snapshot: Dict[str, Any] = {}
        self._metrics_registry = CollectorRegistry()
        self._metrics_collector = PrometheusMetricsCollector(self)
        self._metrics_registry.register(self._metrics_collector)
        self._errors_total = 0
        self._started_at: Optional[float] = None
        
        self._build()

    @property
    def metrics_registry(self) -> Any:
        return self._metrics_registry

    def get_tps(self) -> float:
        """Returns the empirical TPS over the sliding window."""
        if len(self._tick_times) < 2:
            return 0.0
        delta = self._tick_times[-1] - self._tick_times[0]
        if delta <= 0:
            return 0.0
        return (len(self._tick_times) - 1) / delta

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Returns a copy of the latest metrics snapshot."""
        with self._state_lock:
            return self._latest_metrics_snapshot.copy()

    @property
    def read_cache(self) -> ReadModelCache:
        return self._read_cache

    def add_event_listener(self, cb: Callable[[List[Any]], None]):
        with self._listeners_lock:
            self._event_listeners.append(cb)

    def remove_event_listener(self, cb: Callable[[List[Any]], None]):
        with self._listeners_lock:
            if cb in self._event_listeners:
                self._event_listeners.remove(cb)

    def add_tick_listener(self, cb: Callable[[Dict[str, Any]], None]):
        with self._listeners_lock:
            self._listeners.append(cb)

    def remove_tick_listener(self, cb: Callable[[Dict[str, Any]], None]):
        with self._listeners_lock:
            if cb in self._listeners:
                self._listeners.remove(cb)

    def _notify_listeners(self, snapshot: Dict[str, Any]):
        with self._listeners_lock:
            for cb in self._listeners:
                try:
                    cb(snapshot)
                except Exception:
                    logger.exception("Error in tick listener")

    def _build(self):
        """Construct the initial kernel and state."""
        from src.api.presenters.state_presenter import StatePresenter
        
        rng = DeterministicRNG(self._seed)
        gen = EntityGenerator(self._seed)

        entities = {}
        # Spawn hero at center
        hero_pos = (64.0, 64.0)
        hero = gen.spawn_hero(hero_pos)
        entities[hero.id] = hero

        # Spawn monsters along a diagonal from (60, 60). Skip any offset whose tile
        # (LAW-SPAWN-OCCUPANCY collides on int(x)/int(y), not exact float equality) would
        # land on the hero's own tile -- with entities_count=10 (the default used by
        # src/api/server.py's real startup path), offset 4 lands exactly on hero_pos,
        # producing a deterministic spawn-placement collision (TCK-20260817-STANDARD-
        # SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL).
        hero_tile = (int(hero_pos[0]), int(hero_pos[1]))
        placed = 0
        offset = 0
        while placed < self._entities_count - 1:
            pos = (60.0 + offset, 60.0 + offset)
            offset += 1
            if (int(pos[0]), int(pos[1])) == hero_tile:
                continue
            monster = gen.spawn_goblin(pos)
            entities[monster.id] = monster
            placed += 1
            
        state = AuthoritativeState(
            tick=0,
            seed=self._seed,
            entities=entities
        )
        
        self._kernel = Kernel(profile=self._profile, state=state, rng=rng)
        self._kernel._event_listeners = self._event_listeners
        self._update_latest_state(state)

    def _update_latest_state(self, state: AuthoritativeState):
        with self._state_lock:
            self._latest_state = state
            dirty_set = getattr(self._kernel.status, "dirty_set", None) if self._kernel else None
            force_full = getattr(self._kernel.status, "force_full_scan", False) if self._kernel else False
            self._read_cache.update(state, dirty_set, force_full)
            self._latest_snapshot = self._read_cache.get_minimal_summary()
            
            # Extract and update current snapshot for Prometheus metrics in an thread-safe manner
            from src.engine.metrics import MetricsService
            try:
                world_metrics = MetricsService.extract_metrics(state)
            except Exception:
                logger.exception("Error extracting metrics in V2EngineManager")
                world_metrics = None

            # Get recent status signals from kernel
            kernel_status = self._kernel.status if self._kernel else None
            recent_signals = kernel_status.signal_history[-1] if (kernel_status and kernel_status.signal_history) else None
            
            # Build current metrics snapshot
            self._latest_metrics_snapshot = {
                "tick": state.tick,
                "active_entities": world_metrics.alive_entities if world_metrics else len(state.entities),
                "tps": self.get_tps(),
                "tick_compute_ms": recent_signals.tick_compute_ms if recent_signals else 0.0,
                "worker_utilization": recent_signals.worker_utilization if recent_signals else 0.0,
                "queue_utilization": recent_signals.queue_utilization if recent_signals else 0.0,
                "memory_rss_bytes": (recent_signals.memory_estimate_mb * 1024 * 1024) if recent_signals else 0.0,
                "work_debt_total": recent_signals.work_debt_total if recent_signals else 0,
                "governor_mode": int(kernel_status.current_mode) if kernel_status else 0,
                "gold_circulation_total": world_metrics.total_gold if world_metrics else 0.0,
                "rejection_counts": world_metrics.rejection_counts if world_metrics else {},
                "quest_status_counts": world_metrics.quest_status_counts if world_metrics else {},
                "dropped_work_delta": kernel_status.dropped_work_delta if kernel_status else 0,
                "errors_total": self._errors_total,
                "phase_costs_ms": recent_signals.phase_costs_ms if recent_signals else {},
                "hard_law_violations_cumulative": getattr(kernel_status, "cumulative_violations", {}) if kernel_status else {},
                "last_hard_law_violation_tick": getattr(kernel_status, "last_hard_law_violation_tick", -1) if kernel_status else -1,
            }

    def get_state(self) -> Dict[str, Any]:
        """Returns the latest minimal snapshot."""
        with self._state_lock:
            if not self._latest_snapshot and self._latest_state:
                self._latest_snapshot = self._read_cache.get_minimal_summary(self._latest_state)
            return self._latest_snapshot

    def get_full_snapshot(self) -> Dict[str, Any]:
        """Returns a complete DTO snapshot (Expensive O(N))."""
        from src.api.presenters.state_presenter import StatePresenter
        with self._state_lock:
            if not self._latest_state:
                return {}
            return StatePresenter.present_full(self._latest_state)

    def get_entities_paged(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Returns a paged list of entities."""
        with self._state_lock:
            if not self._latest_state:
                return {"entities": [], "total": 0, "offset": offset, "limit": limit}
            return self._read_cache.get_entities_paged(self._latest_state, offset, limit)

    def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Returns a single entity snapshot."""
        with self._state_lock:
            if not self._latest_state or entity_id not in self._latest_state.entities:
                return None
            return self._read_cache.get_entity_dto(self._latest_state.entities[entity_id])

    def get_entity_timeline_events(self, entity_id: int) -> List[Dict[str, Any]]:
        """Returns serialized timeline events for an entity, or [] if not found."""
        with self._state_lock:
            if not self._latest_state or entity_id not in self._latest_state.entities:
                return []
            entity = self._latest_state.entities[entity_id]
            timeline = getattr(entity, "timeline", None)
            if not timeline:
                return []
            return [ev.model_dump() for ev in timeline]

    @property
    def latest_state(self) -> Optional[AuthoritativeState]:
        """Thread-safe access to the latest completed tick state."""
        with self._state_lock:
            return self._latest_state

    def start(self):
        if self._running.is_set():
            return
        self._started_at = time.time()
        self._stop_requested.clear()
        self._paused.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, name="v2-engine-loop", daemon=True)
        self._thread.start()
        logger.info("V2EngineManager started.")

    def stop(self):
        self._stop_requested.set()
        self._paused.clear()
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        if self._kernel:
            self._kernel.shutdown()
        logger.info("V2EngineManager stopped.")

    def pause(self):
        self._paused.set()

    def resume(self):
        self._paused.clear()

    def step(self):
        if not self._paused.is_set():
            self.pause()
        self._step_requested.set()

    def reset(self):
        self.stop()
        self._build()
        logger.info("V2EngineManager reset.")

    def _run_loop(self):
        logger.info("V2 Engine thread started.")
        while not self._stop_requested.is_set():
            if self._paused.is_set() and not self._step_requested.is_set():
                time.sleep(0.01)
                continue
                
            single_step = self._step_requested.is_set()
            if single_step:
                self._step_requested.clear()
                
            # Execute one tick
            try:
                self._kernel.tick_once()
                with self._state_lock:
                    self._tick_times.append(time.time())
                self._update_latest_state(self._kernel.state)
                self._notify_listeners(self._latest_snapshot)
            except Exception as e:
                logger.exception("V2 Kernel tick failed: %s", e)
                with self._state_lock:
                    self._errors_total += 1
                break
                
            if not single_step:
                time.sleep(self._tick_rate)
        
        self._running.clear()
        logger.info("V2 Engine thread exited.")

    @property
    def tick(self) -> int:
        snapshot = self.get_state()
        return snapshot.get("tick", 0) if snapshot else 0

    @property
    def is_running(self) -> bool:
        return self._running.is_set() and not self._paused.is_set()

    @property
    def is_paused(self) -> bool:
        return self._running.is_set() and self._paused.is_set()

    @property
    def is_stopped(self) -> bool:
        return not self._running.is_set() and not self._stop_requested.is_set()

    @property
    def is_stopping(self) -> bool:
        return self._stop_requested.is_set()

    @property
    def kernel(self) -> Optional[Kernel]:
        return self._kernel

    @property
    def started_at(self) -> Optional[float]:
        return self._started_at

    @property
    def errors_total(self) -> int:
        return self._errors_total
