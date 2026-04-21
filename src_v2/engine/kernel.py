from __future__ import annotations

import logging
import time
import os
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Optional

from src_v2.engine.phases import get_authoritative_phases
from src_v2.core.updates import StateUpdate, EntityUpdate
from src_v2.core.work import WorkClass
from src_v2.core.governance import PressureSignals, RuntimeMode
from src_v2.core.diagnostic import TraceEvent
from src_v2.core.lifecycle import LifecycleOutcome, ShutdownResult

from src_v2.engine.executor import IWorkExecutor, LocalSequentialExecutor, ConcurrentExecutionAdapter

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
    v2 is a deterministic, resource-bounded, profile-driven simulation runtime.
    
    Status: FROZEN (Resource Phase 4 Milestone 1)
    
    Milestone A Law: The single-process path is the absolute semantic source of truth.
    Authoritative Phases: INIT -> SCHEDULING -> COLLECTION -> RESOLUTION -> CLEANUP -> ADVANCEMENT
    Any logic outside these 6 phases is strictly non-authoritative.
    """

    __slots__ = (
        "_profile", "_state", "_rng", "_phases", 
        "_scheduler", "_governor", "_status", "_replay", "_collector",
        "_worker_manager", "_executor", "_stopped",
        "_start_perf_ts", "_current_world_time", "_platform_signals",
        "_current_signals", "_current_policy", "_current_work_items",
        "_source_packets", "_source_work_items", "_final_results", "_final_compute_ms",
        "_phase_costs"
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
        executor: Optional[IWorkExecutor] = None,
        flags: Optional[Dict[str, bool]] = None
    ) -> None:
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

        # M10 Law: Executor Injection
        if executor:
            self._executor = executor
        elif profile.max_worker_count > 0:
            self._executor = ConcurrentExecutionAdapter(self._worker_manager)
        else:
            self._executor = LocalSequentialExecutor()

        self._current_world_time = state.world_time
        self._phase_costs = {}

        # M7 Law: Formal Validation Gate
        # By default we validate on init, but this can be bypassed or re-triggered.
        self.validate(flags)

    def validate(self, flags: Optional[Dict[str, bool]] = None) -> None:
        """
        Authoritative validation of the kernel configuration.
        M7 Law: This boundary allows for patch-time validation without restart.
        """
        from src_v2.config.validator import ProfileValidator
        ProfileValidator.validate_profile(self._profile)
        if flags:
             ProfileValidator.validate_flags(flags, self._profile)

    def tick_once(self) -> None:
        """
        Execute exactly one simulation tick in the authoritative contract order.
        Status: FROZEN (Resource Phase 4 Milestone 1)
        
        Law of 6 Phases (Step 1-6):
        1. INIT        (Context & Governance)
        2. SCHEDULING  (Work selection)
        3. COLLECTION  (Execution)
        4. RESOLUTION  (Authoritative Apply)
        5. CLEANUP     (Internal metrics)
        6. ADVANCEMENT (Signal recording)
        
        Non-Authoritative (Step 7+):
        7. PERSISTENCE (Observational: Replay, Logs)
        """
        if getattr(self, "_stopped", False):
             logger.warning("Attempted tick_once after shutdown.")
             return

        # 1-6 Authoritative Sequence
        t0 = time.perf_counter_ns()
        self._phase_init()
        t1 = time.perf_counter_ns()
        self._phase_costs["init"] = (t1 - t0) / 1e6
        
        self._phase_scheduling()
        t2 = time.perf_counter_ns()
        self._phase_costs["scheduling"] = (t2 - t1) / 1e6
        
        self._phase_collection()
        t3 = time.perf_counter_ns()
        self._phase_costs["collection"] = (t3 - t2) / 1e6
        
        self._phase_resolution()
        t4 = time.perf_counter_ns()
        self._phase_costs["resolution"] = (t4 - t3) / 1e6
        
        self._phase_cleanup()
        t5 = time.perf_counter_ns()
        self._phase_costs["cleanup"] = (t5 - t4) / 1e6
        
        self._phase_advancement()
        t6 = time.perf_counter_ns()
        self._phase_costs["advancement"] = (t6 - t5) / 1e6
        
        # 7. Non-authoritative Persistence (Timed separately if needed, but not in authoritative budget)
        self._phase_persistence()
        self._phase_costs["persistence"] = (time.perf_counter_ns() - t6) / 1e6

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
            dropped_work_delta=self._status.dropped_work_delta,
            phase_costs_ms=(self._status.signal_history[-1].phase_costs_ms 
                            if self._status.signal_history else {})
        )
        
        # Policy Evaluation
        self._current_policy = self._governor.evaluate(
            self._profile, 
            self._current_signals, 
            self._status, 
            self._state.tick
        )
        
        # M8 Law: Proactive Concurrency Shedding
        self._executor.set_concurrency_limit(self._current_policy.concurrency_limit)

    def _phase_scheduling(self) -> None:
        """2. SCHEDULING (Work selection under policy)"""
        self._current_work_items, dropped_count = self._scheduler.select_work(self._state, self._current_policy)
        self._status.record_dropped_work(dropped_count)

    def _phase_collection(self) -> None:
        """3. COLLECTION (Execution Strategy delegation)"""
        # Law: The Kernel orchestrates the strategy. It does not own 
        # packetization or worker-specific protocols directly.
        self._final_results = self._executor.execute(
            self._current_work_items,
            self._state,
            self._rng,
            self._profile
        )

        # Post-execution validation remains in the kernel to ensure 
        # that the results coming from any executor are legally formatted.
        from src_v2.core.protocol_validator import ProtocolValidator
        ProtocolValidator.validate_result_batch(self._final_results, getattr(self._executor, "_source_packets", {}))

    def _phase_resolution(self) -> None:
        """4. RESOLUTION (Authoritative Apply)"""
        from src_v2.core.worker_protocol import ResultStatus
        from src_v2.core.updates import StateUpdate, EntityUpdate
        from src_v2.core.protocol_validator import ProtocolViolationError
        
        # M8 Law: Frozen Commit Key sorting
        # Deterministic precedence: Class Priority > Local Priority > Entity ID
        self._final_results.sort(key=lambda r: (r.class_priority, r.local_priority, r.entity_id))
        
        work_debt_updates: Dict[str, int] = {}
        entity_updates: Dict[int, EntityUpdate] = {}
        for res in self._final_results:
            # 1. Handle System Updates (Milestone C: De-simulation)
            if res.work_debt_update is not None and res.subsystem_id:
                # Direct application from result to state-update
                work_debt_updates[res.subsystem_id] = res.work_debt_update
                continue

            # 2. Handle Entity Updates (Option A Law)
            if res.entity_id in entity_updates:
                raise ProtocolViolationError(f"Duplicate authoritative result for entity {res.entity_id} in tick {self._state.tick}")
            
            if res.status == ResultStatus.SUCCESS:
                entity_updates[res.entity_id] = res.update
            else:
                # Failure-to-No-Op Law
                entity_updates[res.entity_id] = EntityUpdate(entity_id=res.entity_id)

        update = StateUpdate(
            entity_updates=entity_updates, 
            node_updates={}, 
            resource_updates={},
            periodic_updates={}, 
            work_debt_updates=work_debt_updates
        )
        
        # (Moved to end of phase for router integration)
        
        # --- Phase A: Logic Truth (Services & Territory) ---
        from src_v2.engine.town_resolution import TownResolutionSystem
        from src_v2.engine.shop import ShopSystem
        from src_v2.engine.blacksmith import BlacksmithSystem
        
        update = TownResolutionSystem.resolve(self._state, update)
        update = ShopSystem.enforce(self._state, update)
        update = BlacksmithSystem.enforce(self._state, update)
        
        # --- Phase B: Intent Routers (Interaction Proposals) ---
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in self._state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.identity.navigation_target
            if ent_upd.identity and ent_upd.identity.navigation_target is not None:
                nav_target = ent_upd.identity.navigation_target
            
            if nav_target and (entity.position == nav_target):
                target_node = next((n for n in self._state.resource_nodes.values() if n.position == nav_target), None)
                if target_node and target_node.remaining_charges > 0:
                    from src_v2.core.updates import InteractionUpdate
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                         refined_entity_updates[e_id] = replace(ent_upd,
                             interaction=replace(current_int, target_node_id=target_node.id, progress_delta=1)
                         )
        
        update = replace(update, entity_updates=refined_entity_updates)
        
        # --- Phase C: Authoritative Laws (Interaction Filtering) ---
        from src_v2.engine.interaction import InteractionSystem
        update = InteractionSystem.enforce(self._state, update)
        
        # --- Phase D: Strategic AI (Resolution & Redirection) ---
        from src_v2.systems.strategic import StrategicIntelligenceSystem
        update = StrategicIntelligenceSystem.resolve_blockers(self._state, update)
        
        from src_v2.systems.redirection import StrategicRedirectionSystem
        update = StrategicRedirectionSystem.enforce(self._state, update)
        
        # --- Phase E: Intent Routers (Movement Proposals) ---
        from src_v2.engine.movement import MovementSystem
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in self._state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            nav_target = entity.identity.navigation_target
            if ent_upd.identity and ent_upd.identity.navigation_target is not None:
                nav_target = ent_upd.identity.navigation_target
            
            if nav_target and (entity.position != nav_target):
                if not ent_upd.moved_this_tick and not (ent_upd.interaction and ent_upd.interaction.progress_delta > 0):
                    move_upd = MovementSystem.resolve_move(self._state, entity, nav_target)
                    refined_entity_updates[e_id] = replace(ent_upd, 
                        new_position=move_upd.new_position,
                        moved_this_tick=move_upd.moved_this_tick,
                        readiness_delta=ent_upd.readiness_delta + move_upd.readiness_delta,
                        property_updates={**ent_upd.property_updates, **move_upd.property_updates}
                    )
        
        update = replace(update, entity_updates=refined_entity_updates)

        from src_v2.engine.apply import ApplyPath
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
            dropped_work_delta=self._status.dropped_work_delta,
            phase_costs_ms=self._phase_costs.copy()
        ))

    def _phase_persistence(self) -> None:
        """
        7. PERSISTENCE (Non-authoritative hooks: Replay, logging, metrics)
        Law: This phase is observational only. It MUST NOT mutate AuthoritativeState.
        Any failure in this phase MUST NOT affect simulation integrity.
        """
        if self._status.current_mode == RuntimeMode.SURVIVAL:
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
            payload={"count": len(self._current_work_items), "mode": self._status.current_mode.name}
        ), self._current_policy)
        
        self._replay.emit(TraceEvent(
            tick=self._state.tick, 
            system="KERNEL", 
            event_type="TICK_END", 
            payload={"hash": tick_hash}
        ), self._current_policy)
        
        # Deterministic rotation check
        self._replay.on_tick_end(self._state.tick)

    def shutdown(self, timeout_s: float = 5.0) -> ShutdownResult:
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
        replay_outcome = LifecycleOutcome.SUCCESS
        try:
            replay_outcome = self._replay.finalize(timeout_s=timeout_s)
        except Exception as e:
            logger.error("Non-authoritative flush failed during shutdown: %s", e)
            replay_outcome = LifecycleOutcome.FAILED

        return ShutdownResult(
            final_tick=self._state.tick,
            final_hash=final_hash,
            replay_outcome=replay_outcome,
            overall_outcome=LifecycleOutcome.SUCCESS if replay_outcome != LifecycleOutcome.FAILED else LifecycleOutcome.FAILED
        )

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
