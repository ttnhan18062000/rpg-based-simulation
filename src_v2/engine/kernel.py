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
        "_worker_manager", "_stopped",
        "_start_perf_ts", "_current_world_time", "_platform_signals",
        "_current_signals", "_current_policy", "_current_work_items",
        "_source_packets", "_final_results", "_final_compute_ms"
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
            ProfileValidator.validate_flags(flags, profile)
        self._stopped = False

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
        """
        Execute exactly one simulation tick in the authoritative contract order.
        Authoritative Phases: INIT -> SCHEDULING -> COLLECTION -> RESOLUTION -> CLEANUP -> ADVANCEMENT
        """
        if getattr(self, "_stopped", False):
             logger.warning("Attempted tick_once after shutdown.")
             return

        # 1-6 Authoritative Sequence
        self._phase_init()
        self._phase_scheduling()
        self._phase_collection()
        self._phase_resolution()
        self._phase_cleanup()
        self._phase_advancement()
        
        # 7. Non-authoritative Persistence
        self._phase_persistence()

    def _phase_init(self) -> None:
        """1. INIT (Context setup, Governance, policy evaluation)"""
        self._start_perf_ts = time.perf_counter()
        self._current_world_time = self._state.world_time + 1
        
        # Capture Primary Pressure Inputs (M7 Real Sensors)
        worker_stats = self._worker_manager.get_stats()
        replay_stats = self._replay.get_stats()
        self._platform_signals = self._collector.collect_platform_signals(self._state.tick)
        
        self._current_signals = PressureSignals(
            work_debt_total=sum(self._state.work_debt.values()),
            tick_compute_ms=(self._status.signal_history[-1].tick_compute_ms 
                             if self._status.signal_history else 0.0),
            worker_utilization=worker_stats["capacity_utilization"], # Renamed from capacity
            queue_utilization=0.0, # Will be updated in ADVANCEMENT based on selected work
            memory_estimate_mb=self._platform_signals["rss_mb"],
            replay_backlog_kb=replay_stats["backlog_kb"],
            active_workers=worker_stats["active_workers"],
            dropped_work_delta=self._status.dropped_work_delta
        )
        
        # Policy Evaluation
        self._current_policy = self._governor.evaluate(
            self._profile, 
            self._current_signals, 
            self._status, 
            self._state.tick
        )

    def _phase_scheduling(self) -> None:
        """2. SCHEDULING (Work selection under policy)"""
        self._current_work_items, dropped_count = self._scheduler.select_work(self._state, self._current_policy)
        self._status.record_dropped_work(dropped_count)

    def _phase_collection(self) -> None:
        """3. COLLECTION (Packetization & Concurrent Execution dispatch)"""
        from src_v2.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
        from src_v2.engine.worker_logic import default_simulation_worker
        from src_v2.core.protocol_validator import ProtocolValidator
        from src_v2.core.concurrency_law import ConcurrencyLaw
        
        packets: List[WorkerPacket] = []
        self._source_packets = {}
        
        for i, item in enumerate(self._current_work_items):
            if item.work_class == WorkClass.CRITICAL and item.work_kind == "ENTITY_ACT" and isinstance(item.owner_id, int):
                subject = self._state.entities.get(item.owner_id)
                if subject:
                    neighbor_view = [] 
                    packet_id = f"{self._state.tick}:{i}"
                    packet = WorkerPacket(
                        packet_id=packet_id,
                        tick=self._state.tick,
                        world_time=self._state.world_time,
                        seed=self._rng.next_int(0, 1000000), 
                        subject=subject,
                        neighbor_view=neighbor_view, 
                        work_kind=item.work_kind,
                        payload=item.payload
                    )
                    packets.append(packet)
                    self._source_packets[packet_id] = packet

        # Pre-dispatch validation
        ProtocolValidator.validate_packet_batch(packets)

        # Execution remains inside the COLLECTION phase boundary
        worker_results = self._worker_manager.execute_batch(
            packets, default_simulation_worker
        )
        
        # Inject priorities for commit sorting
        self._final_results = []
        for res in worker_results:
            source = self._source_packets.get(res.source_packet_id)
            if source:
                item = next((wi for wi in self._current_work_items if wi.owner_id == res.entity_id), None)
                local_pri = item.priority if item else 0
                
                final_res = WorkerResult(
                    source_packet_id=res.source_packet_id,
                    entity_id=res.entity_id,
                    update=res.update,
                    status=res.status,
                    class_priority=ConcurrencyLaw.get_class_priority(item.work_class if item else WorkClass.CRITICAL),
                    local_priority=local_pri,
                    compute_time_ns=res.compute_time_ns
                )
                self._final_results.append(final_res)

        # Post-execution validation
        ProtocolValidator.validate_result_batch(self._final_results, self._source_packets)

    def _phase_resolution(self) -> None:
        """4. RESOLUTION (Authoritative Apply)"""
        from src_v2.core.worker_protocol import ResultStatus
        from src_v2.core.updates import StateUpdate, EntityUpdate
        
        # M8 Law: Frozen Commit Key sorting
        self._final_results.sort(key=lambda r: (r.class_priority, r.local_priority, r.entity_id))
        
        entity_updates: Dict[int, EntityUpdate] = {}
        for res in self._final_results:
            if res.status == ResultStatus.SUCCESS:
                entity_updates[res.entity_id] = res.update
            else:
                entity_updates[res.entity_id] = EntityUpdate(entity_id=res.entity_id)

        update = StateUpdate(entity_updates=entity_updates, periodic_updates={}, work_debt_updates={})
        
        from src_v2.engine.apply import ApplyPath
        next_tick = self._state.tick + 1
        self._state = ApplyPath.apply_generation(self._state, update, next_tick, self._current_world_time)

    def _phase_cleanup(self) -> None:
        """5. CLEANUP (Internal metrics & State finalization)"""
        end_time = time.perf_counter()
        self._final_compute_ms = (end_time - self._start_perf_ts) * 1000.0

    def _phase_advancement(self) -> None:
        """6. ADVANCEMENT (Recording signals into status)"""
        terminal_worker_stats = self._worker_manager.get_stats()
        terminal_replay_stats = self._replay.get_stats()
        
        self._status.record_signals(PressureSignals(
            work_debt_total=sum(self._state.work_debt.values()),
            tick_compute_ms=self._final_compute_ms,
            worker_utilization=terminal_worker_stats["capacity_utilization"],
            queue_utilization=len(self._current_work_items) / self._profile.max_queue_depth if self._profile.max_queue_depth else 0.0,
            memory_estimate_mb=self._platform_signals["rss_mb"],
            replay_backlog_kb=terminal_replay_stats["backlog_kb"],
            active_workers=terminal_worker_stats["active_workers"],
            dropped_work_delta=self._status.dropped_work_delta
        ))

    def _phase_persistence(self) -> None:
        """7. PERSISTENCE (Non-authoritative hooks: Replay, logging, metrics)"""
        if self._status.current_mode == "SURVIVAL":
            # In SURVIVAL mode, we might want to skip some non-authoritative work
            # to save compute budget, but basic traces are usually kept.
            pass

        from src_v2.engine.checkpoint import CanonicalStateHasher
        tick_hash = CanonicalStateHasher.get_hash(self._state)
        
        # M6/M10 Law: Uniform work_kind naming in traces
        self._replay.emit(TraceEvent(
            tick=self._state.tick,
            system="KERNEL",
            event_type="WORK_SCHEDULED",
            payload={"count": len(self._current_work_items), "mode": str(self._status.current_mode)}
        ), self._current_policy)
        
        self._replay.emit(TraceEvent(
            tick=self._state.tick, 
            system="KERNEL", 
            event_type="TICK_END", 
            payload={"hash": tick_hash}
        ), self._current_policy)
        
        # Deterministic rotation check
        self._replay.on_tick_end(self._state.tick)

    def shutdown(self, timeout_s: float = 5.0) -> None:
        """
        Properly close the kernel with deterministic cleanup.
        M7 Law: Shutdown is a bounded non-authoritative flush budget.
        """
        # 1. SUSPEND (Stop work arrival and producers)
        self._stopped = True
        self._worker_manager.shutdown()

        # 2. FINAL AUTHORITATIVE HASH
        # Capture this before any non-authoritative flushes potentially fail.
        from src_v2.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(self._state)
        logger.info("Kernel Shutdown: Final Auth Hash: %s", final_hash)
        
        # 3. NON-AUTHORITATIVE FLUSH (Bounded)
        # Attempt to persist final replay chunk and manifest index.
        try:
            self._replay.finalize(timeout_s=timeout_s)
        except Exception as e:
            logger.error("Non-authoritative flush failed during shutdown: %s", e)

    @property
    def replay(self) -> ReplayManager:
        return self._replay

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    @property
    def state(self) -> AuthoritativeState:
        return self._state
