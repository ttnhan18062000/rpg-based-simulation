from __future__ import annotations
import logging
import threading
import time
from typing import Optional, Any, Dict, List, Callable
import copy

from src_v2.core.state import AuthoritativeState
from src_v2.engine.kernel import Kernel
from src_v2.platform.rng import DeterministicRNG
from src_v2.config.profiles import RuntimeProfile
from src_v2.systems.generator import EntityGenerator

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
        self._state_lock = threading.Lock()
        
        self._listeners: List[Callable[[AuthoritativeState], None]] = []
        self._listeners_lock = threading.Lock()
        
        self._build()

    def add_tick_listener(self, cb: Callable[[AuthoritativeState], None]):
        with self._listeners_lock:
            self._listeners.append(cb)

    def remove_tick_listener(self, cb: Callable[[AuthoritativeState], None]):
        with self._listeners_lock:
            if cb in self._listeners:
                self._listeners.remove(cb)

    def _notify_listeners(self, state: AuthoritativeState):
        with self._listeners_lock:
            for cb in self._listeners:
                try:
                    cb(state)
                except Exception:
                    logger.exception("Error in tick listener")

    def _build(self):
        """Construct the initial kernel and state."""
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
            # In V2, we deep copy to ensure the API doesn't see mutations mid-tick
            self._latest_state = copy.deepcopy(state)

    def get_state(self) -> Optional[AuthoritativeState]:
        with self._state_lock:
            return self._latest_state

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
                self._notify_listeners(self._kernel.state)
            except Exception as e:
                logger.exception("V2 Kernel tick failed: %s", e)
                break
                
            if not single_step:
                time.sleep(self._tick_rate)
        
        self._running.clear()
        logger.info("V2 Engine thread exited.")

    @property
    def tick(self) -> int:
        state = self.get_state()
        return state.tick if state else 0
