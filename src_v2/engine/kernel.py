from __future__ import annotations

import logging
import time
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Optional

from src_v2.engine.phases import get_authoritative_phases
from src_v2.core.updates import StateUpdate, EntityUpdate
from src_v2.core.work import WorkClass
from src_v2.core.governance import PressureSignals
from src_v2.core.diagnostic import TraceEvent

if TYPE_CHECKING:
    from src_v2.config.profiles import RuntimeProfile
    from src_v2.core.state import AuthoritativeState
    from src_v2.platform.rng import DeterministicRNG
    from src_v2.engine.scheduler import DeterministicScheduler
    from src_v2.engine.governor import ResourceGovernor
    from src_v2.engine.runtime_status import RuntimeStatus
    from src_v2.engine.replay_manager import ReplayManager

logger = logging.getLogger(__name__)


class Kernel:
    """
    The skeletal simulation kernel orchestrator.
    Responsible for executing phases in the frozen contract order.
    Now with Milestone 6 Streaming Replay.
    """

    __slots__ = (
        "_profile", "_state", "_rng", "_phases", 
        "_scheduler", "_governor", "_status", "_replay", "_collector",
        "_worker_manager"
    )

    def __init__(
        self,
        profile: RuntimeProfile,
        state: AuthoritativeState,
        rng: DeterministicRNG,
        scheduler: Optional[DeterministicScheduler] = None,
        governor: Optional[ResourceGovernor] = None,
        status: Optional[RuntimeStatus] = None,
        replay: Optional[ReplayManager] = None,
        flags: Optional[Dict[str, bool]] = None
    ) -> None:
        # M7 Law: Startup Validation
        from src_v2.config.validator import ProfileValidator
        ProfileValidator.validate_profile(profile)
        if flags:
            ProfileValidator.validate_flags(flags)

        self._profile = profile
        self._state = state
        self._rng = rng
        self._phases = get_authoritative_phases()
        
        from src_v2.engine.scheduler import DeterministicScheduler as DefaultScheduler
        from src_v2.engine.governor import ResourceGovernor as DefaultGovernor
        from src_v2.engine.runtime_status import RuntimeStatus as DefaultStatus
        from src_v2.engine.replay_manager import ReplayManager as DefaultReplayManager
        from src_v2.engine.observability import SignalCollector
        from src_v2.engine.worker_manager import WorkerManager
        
        self._scheduler = scheduler or DefaultScheduler()
        self._governor = governor or DefaultGovernor()
        self._status = status or DefaultStatus()
        self._collector = SignalCollector(profile.name)
        self._worker_manager = WorkerManager(
            max_workers=profile.max_worker_count,
            max_queue_depth=profile.max_queue_depth
        )
        
        if replay is None:
            run_id = int(time.time())
            run_dir = Path(f"data/runs/run_{run_id}")
            self._replay = DefaultReplayManager(
                run_dir=run_dir,
                profile_name=profile.name,
                buffer_capacity_kb=profile.max_replay_buffer_kb
            )
        else:
            self._replay = replay

    def tick_once(self) -> None:
        """Execute exactly one simulation tick."""
        start_time = time.perf_counter()
        
        # 1. INIT
        next_world_time = self._state.world_time + 1
        
        # 2. GOVERNANCE
        platform_signals = self._collector.collect_platform_signals(self._state.tick)
        total_debt = sum(self._state.work_debt.values())
        signals = PressureSignals(
            work_debt_total=total_debt,
            tick_compute_ms=(self._status.signal_history[-1].tick_compute_ms 
                             if self._status.signal_history else 0.0),
            queue_utilization=0.0,
            memory_estimate_mb=platform_signals["rss_mb"]
        )
        policy = self._governor.evaluate(self._profile, signals, self._status)
        
        # 3. SCHEDULING
        work_items = self._scheduler.select_work(self._state, policy)
        
        self._replay.emit(TraceEvent(
            tick=self._state.tick,
            system="KERNEL",
            event_type="WORK_SCHEDULED",
            payload={"count": len(work_items), "mode": str(self._status.current_mode)}
        ), policy)
        
        # 4. PACKETIZATION & CONCURRENT EXECUTION
        # M8 Law: Map work items to compact worker packets
        from src_v2.core.worker_protocol import WorkerPacket
        from src_v2.engine.worker_logic import default_simulation_worker
        
        packets = []
        for item in work_items:
            if item.work_class == WorkClass.CRITICAL and item.action_type == "ENTITY_ACT":
                subject = self._state.entities.get(item.owner_id)
                if subject:
                    # M8 Law: Neighbor view must be restricted. 
                    # Placeholder: Empty view for M8 proof of concept
                    packets.append(WorkerPacket(
                        tick=self._state.tick,
                        world_time=self._state.world_time,
                        seed=self._rng.next_int(0, 1000000), # Individual seed for worker
                        subject=subject,
                        neighbor_view={}, # To be expanded in real use
                        action_type=item.action_type,
                        payload=item.payload
                    ))

        # Dispatch via Bounded WorkerManager
        worker_results = self._worker_manager.execute_batch(
            packets, default_simulation_worker
        )

        # 5. RESOLUTION
        # Map worker results back to authoritative updates
        entity_updates: Dict[int, EntityUpdate] = {}
        for res in worker_results:
            entity_updates[res.entity_id] = res.update

        update = StateUpdate(entity_updates=entity_updates, periodic_updates={}, work_debt_updates={})
        
        from src_v2.engine.apply import ApplyPath
        next_tick = self._state.tick + 1
        self._state = ApplyPath.apply_generation(self._state, update, next_tick, next_world_time)
        
        # 6. PERSISTENCE
        from src_v2.engine.checkpoint import CanonicalStateHasher
        tick_hash = CanonicalStateHasher.get_hash(self._state)
        
        self._replay.emit(TraceEvent(tick=self._state.tick, system="KERNEL", event_type="TICK_END", payload={"hash": tick_hash}), policy)
        self._replay.on_tick_end(self._state.tick)
        
        # Finalize measurement
        end_time = time.perf_counter()
        final_compute_ms = (end_time - start_time) * 1000.0
        
        # Aggregate worker compute time into status metrics if needed
        self._status.record_signals(PressureSignals(
            work_debt_total=total_debt,
            tick_compute_ms=final_compute_ms,
            memory_estimate_mb=platform_signals["rss_mb"]
        ))

    def shutdown(self) -> None:
        """Properly close the kernel with deterministic cleanup."""
        # Clean up worker pool
        self._worker_manager.shutdown()

        # 1. Authoritative Hash Finalization
        from src_v2.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(self._state)
        logger.info("M8 Graceful Shutdown: Final Auth Hash: %s", final_hash)
        
        self._replay.finalize()

    @property
    def state(self) -> AuthoritativeState:
        return self._state
    
    @property
    def status(self) -> RuntimeStatus:
        return self._status

    @property
    def replay(self) -> ReplayManager:
        return self._replay
