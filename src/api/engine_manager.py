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
        self._listeners_lock = threading.Lock()
        
        self._build()

    @property
    def read_cache(self) -> ReadModelCache:
        return self._read_cache

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
        hero = gen.spawn_hero((64.0, 64.0))
        entities[hero.id] = hero
        
        # Spawn monsters
        for i in range(self._entities_count - 1):
            monster = gen.spawn_goblin((60.0 + i, 60.0 + i))
            entities[monster.id] = monster
            
        state = AuthoritativeState(
            tick=0,
            seed=self._seed,
            entities=entities
        )
        
        self._kernel = Kernel(profile=self._profile, state=state, rng=rng)
        self._update_latest_state(state)

    def _update_latest_state(self, state: AuthoritativeState):
        with self._state_lock:
            self._latest_state = state
            dirty_set = getattr(self._kernel.status, "dirty_set", None) if self._kernel else None
            force_full = getattr(self._kernel.status, "force_full_scan", False) if self._kernel else False
            self._read_cache.update(state, dirty_set, force_full)
            self._latest_snapshot = self._read_cache.get_minimal_summary()

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

    def start(self):
        if self._running.is_set():
            return
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
                self._update_latest_state(self._kernel.state)
                self._notify_listeners(self._latest_snapshot)
            except Exception as e:
                logger.exception("V2 Kernel tick failed: %s", e)
                break
                
            if not single_step:
                time.sleep(self._tick_rate)
        
        self._running.clear()
        logger.info("V2 Engine thread exited.")

    @property
    def tick(self) -> int:
        snapshot = self.get_state()
        return snapshot.get("tick", 0) if snapshot else 0
