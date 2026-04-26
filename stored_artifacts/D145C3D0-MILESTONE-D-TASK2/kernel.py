from __future__ import annotations

import logging
import time
import os
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Optional

from src.engine.phases import get_authoritative_phases
from src.core.updates import StateUpdate, EntityUpdate
from src.core.work import WorkClass
from src.core.governance import PressureSignals
from src.core.diagnostic import TraceEvent

if TYPE_CHECKING:
    from src.config.profiles import RuntimeProfile
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.engine.scheduler import DeterministicScheduler
    from src.engine.governor import ResourceGovernor
    from src.engine.runtime_status import RuntimeStatus
    from src.engine.replay_manager import ReplayManager

logger = logging.getLogger(__name__)


class Kernel:
    """
    v2 is a deterministic, resource-bounded, profile-driven simulation runtime.
    
    Milestone A Law: The single-process path is the absolute semantic source of truth.
    Authoritative Phases: INIT -> SCHEDULING -> COLLECTION -> RESOLUTION -> CLEANUP -> ADVANCEMENT
    Any logic outside these 6 phases is strictly non-authoritative.
    """

    __slots__ = (
        "_profile", "_state", "_rng", "_phases", 
        "_scheduler", "_governor", "_status", "_replay", "_collector",
        "_worker_manager", "_stopped",
        "_start_perf_ts", "_current_world_time", "_platform_signals",
        "_current_signals", "_current_policy", "_current_work_items",
        "_source_packets", "_source_work_items", "_final_results", "_final_compute_ms"
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
        from src.config.validator import ProfileValidator
        ProfileValidator.validate_profile(profile)
        if flags:
            ProfileValidator.validate_flags(flags, profile)
        self._stopped = False

        self._profile = profile
        self._state = state
        self._rng = rng
        self._phases = get_authoritative_phases()
        
        from src.engine.scheduler import DeterministicScheduler as DefaultScheduler
        from src.engine.governor import ResourceGovernor as DefaultGovernor
        from src.engine.runtime_status import RuntimeStatus as DefaultStatus
        from src.engine.replay_manager import ReplayManager as DefaultReplayManager
        from src.engine.observability import SignalCollector
        from src.engine.worker_manager import WorkerManager
        
        self._scheduler = scheduler or DefaultScheduler()
        self._governor = governor or DefaultGovernor()
        self._status = status or DefaultStatus()
        self._collector = SignalCollector(profile.name)
        self._platform_signals = {"rss_mb": 0.0, "cpu_percent": 0.0}
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

        self._current_world_time = state.world_time

    def tick_once(self) -> None:
        """
        Execute exactly one simulation tick in the authoritative contract order.
        Milestone A Sequence: 1. INIT, 2. SCHEDULING, 3. COLLECTION, 4. RESOLUTION, 5. CLEANUP, 6. ADVANCEMENT.
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
        # Law: Reset peak accounting for the new tick
        self._worker_manager.reset_tick_stats()
        
        self._start_perf_ts = time.perf_counter_ns()
        self._current_world_time = self._state.world_time + 1
        
        # Capture Primary Pressure Inputs (M7 Real Sensors)
        worker_stats = self._worker_manager.get_stats()
        replay_stats = self._replay.get_stats()
        self._platform_signals = self._collector.collect_platform_signals(
            self._state.tick, 
            interval_override=self._profile.sampling_interval_ticks
        )
        
        self._current_signals = PressureSignals(
            work_debt_total=sum(self._state.work_debt.values()),
            tick_compute_ms=(self._status.signal_history[-1].tick_compute_ms 
                             if self._status.signal_history else 0.0),
            worker_utilization=worker_stats["worker_utilization"],
            queue_utilization=worker_stats["queue_utilization"],
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
        from src.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
        from src.engine.worker_logic import default_simulation_worker
        from src.core.protocol_validator import ProtocolValidator
        from src.core.concurrency_law import ConcurrencyLaw
        
        packets: List[WorkerPacket] = []
        self._source_packets = {}
        self._source_work_items = {}
        
        for i, item in enumerate(self._current_work_items):
            if item.work_class == WorkClass.CRITICAL and item.work_kind == "ENTITY_ACT" and isinstance(item.owner_id, int):
                subject = self._state.entities.get(item.owner_id)
                if subject:
                    # Milestone A Law: Isolate properties from worker mutation.
                    subject_snapshot = replace(subject, properties=dict(subject.properties))
                    
                    # M8 Law: Neighbor context must be deterministic and sorted.
                    # radius = 10.0 per MC plan
                    neighbor_view = self._get_deterministic_neighbor_view(subject, 10.0)
                    
                    packet_id = f"{self._state.tick}:{i}"
                    work_id = f"{self._state.tick}:{item.owner_id}:{item.work_kind}"
                    
                    packet = WorkerPacket(
                        packet_id=packet_id,
                        work_id=work_id,
                        tick=self._state.tick,
                        world_time=self._state.world_time,
                        seed=self._rng.next_int(0, 1000000), 
                        work_class=item.work_class,
                        subject=subject_snapshot,
                        neighbor_view=neighbor_view, 
                        work_kind=item.work_kind,
                        payload=item.payload
                    )
                    packets.append(packet)
                    self._source_packets[packet_id] = packet
                    self._source_work_items[packet_id] = item

        # Pre-dispatch validation
        ProtocolValidator.validate_packet_batch(packets)

        # Execution remains inside the COLLECTION phase boundary
        worker_results = self._worker_manager.execute_batch(
            packets, 
            default_simulation_worker,
            concurrency_limit=self._current_policy.concurrency_limit
        )
        
        # Inject priorities for commit sorting
        self._final_results = []
        for res in worker_results:
            source_packet = self._source_packets.get(res.source_packet_id)
            item = self._source_work_items.get(res.source_packet_id)
            if source_packet and item:
                local_pri = item.priority if item else 0
                
                final_res = WorkerResult(
                    source_packet_id=res.source_packet_id,
                    work_id=source_packet.work_id,
                    entity_id=res.entity_id,
                    work_class=source_packet.work_class,
                    update=res.update,
                    status=res.status,
                    class_priority=ConcurrencyLaw.get_class_priority(source_packet.work_class),
                    local_priority=local_pri,
                    compute_time_ns=res.compute_time_ns
                )
                self._final_results.append(final_res)

        # Post-execution validation
        ProtocolValidator.validate_result_batch(self._final_results, self._source_packets)

    def _phase_resolution(self) -> None:
        """4. RESOLUTION (Authoritative Apply)"""
        from src.core.worker_protocol import ResultStatus
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.protocol_validator import ProtocolViolationError
        
        # M8 Law: Frozen Commit Key sorting
        # Deterministic precedence: Class Priority > Local Priority > Entity ID
        self._final_results.sort(key=lambda r: (r.class_priority, r.local_priority, r.entity_id))
        
        entity_updates: Dict[int, EntityUpdate] = {}
        for res in self._final_results:
            # Option A Enforcement: One result per entity per tick.
            if res.entity_id in entity_updates:
                raise ProtocolViolationError(f"Duplicate authoritative result for entity {res.entity_id} in tick {self._state.tick}")
            
            if res.status == ResultStatus.SUCCESS:
                entity_updates[res.entity_id] = res.update
            else:
                # Failure-to-No-Op Law
                entity_updates[res.entity_id] = EntityUpdate(entity_id=res.entity_id)

        update = StateUpdate(entity_updates=entity_updates, periodic_updates={}, work_debt_updates={})
        
        from src.engine.apply import ApplyPath
        next_tick = self._state.tick + 1
        self._state = ApplyPath.apply_generation(self._state, update, next_tick, self._current_world_time)

    def _phase_cleanup(self) -> None:
        """5. CLEANUP (Internal metrics & State finalization)"""
        # RSS, etc (Using profile cadence override if needed)
        signals = self._collector.collect_platform_signals(
            self._state.tick, 
            interval_override=self._profile.sampling_interval_ticks
        )
        self._platform_signals.update(signals)
            
        # Compute pressure (nanoseconds to milliseconds)
        self._final_compute_ms = (time.perf_counter_ns() - self._start_perf_ts) / 1e6

    def _phase_advancement(self) -> None:
        """6. ADVANCEMENT (Recording signals into status)"""
        terminal_worker_stats = self._worker_manager.get_stats()
        terminal_replay_stats = self._replay.get_stats()
        
        self._status.record_signals(PressureSignals(
            work_debt_total=sum(self._state.work_debt.values()),
            tick_compute_ms=self._final_compute_ms,
            worker_utilization=terminal_worker_stats["worker_utilization"],
            queue_utilization=terminal_worker_stats["queue_utilization"],
            memory_estimate_mb=self._platform_signals["rss_mb"],
            replay_backlog_kb=terminal_replay_stats["backlog_kb"],
            active_workers=terminal_worker_stats["active_workers"],
            dropped_work_delta=self._status.dropped_work_delta
        ))

    def _phase_persistence(self) -> None:
        """
        7. PERSISTENCE (Non-authoritative hooks: Replay, logging, metrics)
        Law: This phase is observational only. It MUST NOT mutate AuthoritativeState.
        """
        if self._status.current_mode == "SURVIVAL":
            # In SURVIVAL mode, we might want to skip some non-authoritative work
            # to save compute budget, but basic traces are usually kept.
            pass

        from src.engine.checkpoint import CanonicalStateHasher
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
        from src.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(self._state)
        logger.info("Kernel Shutdown: Final Auth Hash: %s", final_hash)
        
        # 3. NON-AUTHORITATIVE FLUSH (Bounded)
        # Attempt to persist final replay chunk and manifest index.
        try:
            self._replay.finalize(timeout_s=timeout_s)
        except Exception as e:
            logger.error("Non-authoritative flush failed during shutdown: %s", e)

    def _get_deterministic_neighbor_view(self, subject: EntityState, radius: float) -> List[Tuple[int, EntityState]]:
        """
        Produce a deterministic context for a worker packet.
        Sorted by entity_id to ensure bit-identical input regardless of engine internal dict order.
        """
        neighbors = []
        radius_sq = radius * radius
        sx, sy = subject.position
        
        # M8 Law: Linear scan is fine for prototype, but sorting by ID is non-negotiable.
        for e_id, ent in self._state.entities.items():
            if e_id == subject.id:
                continue
            
            ex, ey = ent.position
            dist_sq = (ex - sx)**2 + (ey - sy)**2
            if dist_sq <= radius_sq:
                # Snapshot context to prevent any mutation reach-through
                neighbors.append((e_id, replace(ent, properties=dict(ent.properties))))
        
        # Explicit sorting by deterministic key
        neighbors.sort(key=lambda x: x[0])
        return neighbors

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    @property
    def state(self) -> AuthoritativeState:
        return self._state
