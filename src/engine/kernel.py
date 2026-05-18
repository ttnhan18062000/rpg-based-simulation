# Compliance IDs: COMBAT-017, COMBAT-018, COMBAT-034, INFRA-003, PERF-003, PERF-006, PERF-009, WORLD-008, WORLD-018
# Compliance IDs: COMB-007, COMB-008, INFRA-018, INFRA-101, INFRA-102, INFRA-103, INFRA-104, INFRA-105, INFRA-106, INFRA-117, PROG-102, STRAT-041, STRAT-064, STRAT-065, STRAT-216, SUB-005, SUB-008, SUB-010, SUB-011, SUB-012, SUB-013, SUB-020, SUB-021, SUB-023, TOWN-007, TOWN-133, TOWN-134, TOWN-135, TOWN-158
# Compliance IDs: STRAT-041, STRAT-064, STRAT-065, SUB-010, SUB-011, SUB-012, SUB-013, SUB-020, SUB-021, SUB-023, PERF-019
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, List, Dict, Optional, Any
import time
import logging
import gc
from pathlib import Path

from src.engine.phases import get_authoritative_phases
from src.core.updates import StateUpdate, EntityUpdate
from src.core.governance import PressureSignals, RuntimeMode
from src.core.diagnostic import TraceEvent
from src.core.lifecycle import LifecycleOutcome, ShutdownResult

from src.engine.executor import IWorkExecutor, LocalSequentialExecutor, ConcurrentExecutionAdapter
from src.engine.cache_registry import CacheRegistry, CacheBudgetPolicy

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
    """

    __slots__ = (
        "_profile", "_state", "_rng", "_phases", 
        "_scheduler", "_governor", "_status", "_replay", "_collector",
        "_worker_manager", "_executor", "_stopped",
        "_start_perf_ts", "_current_world_time", "_platform_signals",
        "_current_signals", "_current_policy", "_current_work_items",
        "_source_packets", "_source_work_items", "_final_results", "_final_compute_ms",
        "_phase_costs", "_metrics", "_audit_mode", "_no_frame_pacing", "_no_replay", "_audit_dirty_set", "_perf_tracker", "_force_full_scan", "_current_update", "_cache_registry", "_cache_policy", "_opt_profile"
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
        flags: Optional[Dict[str, Any]] = None
    ) -> None:
        self._stopped = False
        self._profile = profile
        self._state = state
        self._rng = rng
        self._phases = get_authoritative_phases()
        self._audit_mode = flags.get("audit_mode", False) if flags else False
        self._audit_dirty_set = flags.get("audit_dirty_set", False) if flags else False
        self._perf_tracker = flags.get("perf_tracker", False) if flags else False
        self._force_full_scan = flags.get("force_full_scan", False) if flags else False
        self._current_update = None
        
        from src.config.optimization_profiles import OptimizationProfileResolver
        self._opt_profile = OptimizationProfileResolver.resolve(profile, flags)
        try:
            object.__setattr__(self._state, "_opt_profile", self._opt_profile)
            object.__setattr__(self._state, "_force_full_scan", self._force_full_scan)
        except Exception:
            pass

        self._cache_registry = CacheRegistry()
        self._cache_policy = self._opt_profile.cache_budget_policy
        if getattr(self._state, "movement_cache", None) is not None:
            self._cache_registry.register_cache("movement_plan_cache", self._state.movement_cache)
        
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

        if executor:
            self._executor = executor
        elif profile.max_worker_count > 0:
            self._executor = ConcurrentExecutionAdapter(self._worker_manager)
        else:
            self._executor = LocalSequentialExecutor()

        self._current_world_time = state.world_time
        
        from src.engine.policy import GovernorPolicy
        from src.core.governance import RuntimeMode
        self._current_policy = GovernorPolicy.from_mode(RuntimeMode.NORMAL)
        
        if flags and flags.get("no_replay", False):
            self._current_policy = replace(self._current_policy, replay_allowed=False)
            
        self._current_signals = None
        self._current_work_items = []
        self._source_packets = {}
        self._source_work_items = {}
        self._final_results = []
        self._final_compute_ms = 0.0
        self._phase_costs = {}
        self._metrics = {}
        self._start_perf_ts = time.perf_counter_ns()
        self._no_frame_pacing = flags.get("no_frame_pacing", False) if flags else False
        self._no_replay = flags.get("no_replay", False) if flags else False

        self.validate(flags)

    def validate(self, flags: Optional[Dict[str, bool]] = None) -> None:
        from src.config.validator import ProfileValidator
        ProfileValidator.validate_profile(self._profile)
        if flags:
             ProfileValidator.validate_flags(flags, self._profile)

    def tick_once(self) -> None:
        """
        Main simulation loop.
        VERIFIED v2: engine_phase_order
        """
        if getattr(self, "_stopped", False):
             return

        t0 = time.perf_counter_ns()
        self._start_perf_ts = t0
        self._phase_init()
        t1 = time.perf_counter_ns()
        self._phase_costs["init"] = (t1 - t0) / 1e6
        
        start_fingerprint = None
        if self._audit_mode:
            start_fingerprint = self._state.fingerprint()

        self._phase_scheduling()
        t2 = time.perf_counter_ns()
        self._phase_costs["scheduling"] = (t2 - t1) / 1e6
        
        if self._audit_mode and start_fingerprint:
            self._guard_stability("Scheduling", start_fingerprint)
            
        self._phase_collection()
        t3 = time.perf_counter_ns()
        self._phase_costs["collection"] = (t3 - t2) / 1e6
        
        if self._audit_mode and start_fingerprint:
            self._guard_stability("Collection", start_fingerprint)
            
        self._phase_resolution()
        t4 = time.perf_counter_ns()
        res_total = (t4 - t3) / 1e6
        sub_sum = sum(v for k, v in self._phase_costs.items() if k.startswith("res_") or k in ["trust_validity", "contracts_production", "locomotion", "interaction", "governance_ecology", "economy", "final_integrity"])
        self._phase_costs["resolution_overhead"] = max(0.0, res_total - sub_sum)
        
        self._phase_cleanup()
        t5 = time.perf_counter_ns()
        self._phase_costs["cleanup"] = (t5 - t4) / 1e6
        
        self._phase_advancement()
        t6 = time.perf_counter_ns()
        self._phase_costs["advancement"] = (t6 - t5) / 1e6
        
        target_ms = self._profile.max_tick_budget_ms
        if target_ms > 0 and not self._no_frame_pacing:
            elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
            sleep_ms = target_ms - elapsed_ms
            if sleep_ms > 5.0:
                gc.collect(0)
                remaining_ms = target_ms - ((time.perf_counter_ns() - t0) / 1e6)
                if remaining_ms > 0:
                    time.sleep(remaining_ms / 1000.0)
            elif sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
            else:
                pass

        t_persist_start = time.perf_counter_ns()
        self._phase_persistence()
        self._phase_costs["persistence"] = (time.perf_counter_ns() - t_persist_start) / 1e6
        
        self._final_compute_ms = sum(self._phase_costs.values())
        
        avg_ms = (self._status.signal_history[-1].tick_compute_ms if self._status.signal_history else 10.0)
        limit_ms = max(20.0, avg_ms * 2.0)
        hard_cap = self._profile.max_tick_budget_ms
        if not self._audit_mode and self._state.tick > 5 and self._final_compute_ms > min(hard_cap, limit_ms):
             logger.warning(f"Tick {self._state.tick} exceeded budget: {self._final_compute_ms:.2f}ms vs limit {min(hard_cap, limit_ms):.2f}ms. Aborting next tick if sustained.")
             self._status.record_dropped_work(9999)
        
        self._record_runtime_signals()

    def _phase_init(self) -> None:
        from src.engine.occupancy_snapshot import OccupancySnapshot
        object.__setattr__(self._state, "occupancy_snapshot", OccupancySnapshot.from_state(self._state))
        self._worker_manager.reset_tick_stats()
        self._current_world_time = self._state.world_time + 1
        
        worker_stats = self._worker_manager.get_stats()
        replay_stats = self._replay.get_stats()
        self._platform_signals = self._collector.collect_platform_signals(
            self._state.tick, 
            interval_override=self._profile.sampling_interval_ticks
        )
        
        if self._audit_mode:
            self._current_signals = PressureSignals(
                work_debt_total=sum(self._state.work_debt.values()),
                tick_compute_ms=0.0,
                worker_utilization=0.0,
                queue_utilization=0.0,
                memory_estimate_mb=0.0,
                replay_backlog_kb=0,
                active_workers=0,
                dropped_work_delta=self._status.dropped_work_delta,
                phase_costs_ms={},
                metrics=self._metrics.copy()
            )
        else:
            compute_ms = self._status.signal_history[-1].tick_compute_ms if self._status.signal_history else 0.0
            if not self._audit_mode and self._state.tick <= 5:
                compute_ms = min(compute_ms, self._profile.max_tick_budget_ms * 0.5)
            self._current_signals = PressureSignals(
                work_debt_total=sum(self._state.work_debt.values()),
                tick_compute_ms=compute_ms,
                worker_utilization=worker_stats["worker_utilization"],
                queue_utilization=worker_stats["queue_utilization"],
                memory_estimate_mb=self._platform_signals["rss_mb"],
                replay_backlog_kb=replay_stats["backlog_kb"],
                active_workers=worker_stats["active_workers"],
                dropped_work_delta=self._status.dropped_work_delta,
                phase_costs_ms=(self._status.signal_history[-1].phase_costs_ms 
                                if self._status.signal_history else {}),
                metrics=self._metrics.copy()
            )
        
        self._current_policy = self._governor.evaluate(
            self._profile, 
            self._current_signals, 
            self._status, 
            self._state.tick,
            opt_profile=getattr(self, "_opt_profile", None)
        )
        if getattr(self, "_no_replay", False):
            self._current_policy = replace(self._current_policy, replay_allowed=False)
        self._executor.set_concurrency_limit(self._current_policy.concurrency_limit)

    def _phase_scheduling(self) -> None:
        self._current_work_items, dropped_count = self._scheduler.select_work(self._state, self._current_policy)
        self._status.record_dropped_work(dropped_count)

    def _phase_collection(self) -> None:
        state_view = self._state.readonly_view()
        
        self._final_results = self._executor.execute(
            self._current_work_items,
            state_view,
            self._rng,
            self._profile
        )
        from src.core.protocol_validator import ProtocolValidator
        ProtocolValidator.validate_result_batch(self._final_results, getattr(self._executor, "_source_packets", {}))

    def _phase_resolution(self) -> None:
        from src.core.worker_protocol import ResultStatus
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.protocol_validator import ProtocolViolationError
        from src.engine.pipeline import AuthoritativeApplyPipeline
        
        self._final_results.sort(key=lambda r: (r.class_priority, -r.local_priority, r.entity_id))
        
        work_debt_updates: Dict[str, int] = {}
        entity_updates: Dict[int, EntityUpdate] = {}
        for i, res in enumerate(self._final_results):
            if i % 10 == 0:
                elapsed = (time.perf_counter_ns() - self._start_perf_ts) / 1e6
                hard_cap = self._profile.max_tick_budget_ms
                should_throttle = not self._audit_mode and elapsed > hard_cap
                
                if should_throttle:
                    logger.warning(f"Mid-tick emergency throttle triggered at {elapsed:.2f}ms. Dropping {len(self._final_results) - i} items.")
                    self._status.record_dropped_work(len(self._final_results) - i)
                    from src.core.governance import RuntimeMode
                    self._governor.force_mode(RuntimeMode.DEGRADED, self._status, self._state.tick)
                    break

            if res.work_debt_update is not None and res.subsystem_id:
                work_debt_updates[res.subsystem_id] = res.work_debt_update
                continue

            if res.entity_id in entity_updates:
                raise ProtocolViolationError(f"Duplicate authoritative result for entity {res.entity_id}")
            
            if res.status == ResultStatus.SUCCESS:
                entity_updates[res.entity_id] = res.update
            else:
                entity_updates[res.entity_id] = EntityUpdate(entity_id=res.entity_id)

        if self._current_signals is None:
            debt_ratio = 0.0
            compute_ratio = 0.0
        else:
            debt_ratio = self._current_signals.work_debt_total / self._profile.max_work_debt
            compute_ratio = self._current_signals.tick_compute_ms / self._profile.max_tick_budget_ms
        global_salience = min(2.0, debt_ratio + compute_ratio)
        
        pressure_dict = {
            "global_salience": global_salience,
            "debt_ratio": debt_ratio,
            "compute_ratio": compute_ratio
        }

        raw_update = StateUpdate(
            entity_updates=entity_updates, 
            work_debt_updates=work_debt_updates,
            pressure_signals_set=pressure_dict,
            current_mode_set=self._current_policy.mode,
            current_policy_set=self._current_policy
        )
        
        refined_update = AuthoritativeApplyPipeline.refine(
            self._state, 
            raw_update, 
            cadence=self._profile.cadence,
            force_full_scan=self._force_full_scan
        )
        
        if refined_update.sub_phase_costs:
            self._phase_costs.update(refined_update.sub_phase_costs)

        self._metrics = dict(refined_update.metric_counters) if getattr(refined_update, "metric_counters", None) is not None else {}
        if getattr(self._state, "movement_cache", None) is not None:
            self._metrics["movement_cache_hits"] = getattr(self._state.movement_cache, "hits", 0)
            self._metrics["movement_cache_misses"] = getattr(self._state.movement_cache, "misses", 0)
        self._metrics["spatial_index_hits"] = getattr(self._state, "_index_hits", 0)
        self._metrics["spatial_index_misses"] = getattr(self._state, "_index_misses", 0)
        
        if self._current_policy.replay_allowed:
            self._replay.emit(TraceEvent(
                tick=self._state.tick,
                system="KERNEL",
                event_type="REFINED_UPDATE",
                payload={
                    "tick": self._state.tick,
                    "world_time": self._state.world_time,
                    "seed": self._state.seed,
                    "update": refined_update,
                    "fingerprint": self._state.fingerprint()
                }
            ), self._current_policy)
        
        self._current_update = refined_update

    def _phase_cleanup(self) -> None:
        signals = self._collector.collect_platform_signals(
            self._state.tick, 
            interval_override=self._profile.sampling_interval_ticks
        )
        self._platform_signals.update(signals)
        
        # M19 Law: Centralized optimization cache sweep
        if self._state.tick % self._cache_policy.sweep_interval_ticks == 0:
            pruned_map = self._cache_registry.sweep_caches(self._state.tick, self._cache_policy)
            if pruned_map:
                for c_name, count in pruned_map.items():
                    self._metrics[f"{c_name}_pruned"] = count
                    
        self._final_compute_ms = (time.perf_counter_ns() - self._start_perf_ts) / 1e6

    def _record_runtime_signals(self) -> None:
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
            phase_costs_ms=self._phase_costs.copy(),
            metrics=self._metrics.copy()
        ))

    def _phase_advancement(self) -> None:
        from src.engine.apply import ApplyPath
        
        update = self._current_update
        if update is None:
            from src.core.updates import StateUpdate
            update = StateUpdate()
            
        self._state = ApplyPath.apply_generation(
            self._state, 
            update, 
            next_tick=self._state.tick + 1,
            next_world_time=self._current_world_time,
            cadence=self._profile.cadence,
            audit_mode=self._audit_mode,
            audit_dirty_set=self._audit_dirty_set
        )
        self._current_update = None
        try:
            object.__setattr__(self._state, "_opt_profile", self._opt_profile)
            object.__setattr__(self._state, "_force_full_scan", self._force_full_scan)
        except Exception:
            pass
        
        # Keep movement_cache registered across state advancements
        if getattr(self._state, "movement_cache", None) is not None:
            self._cache_registry.register_cache("movement_plan_cache", self._state.movement_cache)

    def _guard_stability(self, phase_name: str, start_fingerprint: Dict[str, Any]) -> None:
        from src.core.protocol_validator import ProtocolViolationError
        current = self._state.fingerprint()
        if current["state_hash"] != start_fingerprint["state_hash"]:
             raise ProtocolViolationError(
                 f"Isolation Breach: Authoritative state mutated during {phase_name} phase. "
                 f"Expected hash {start_fingerprint['state_hash']}, got {current['state_hash']}"
             )

    def _phase_persistence(self) -> None:
        tick_hash = "SKIPPED"
        if self._current_policy.replay_allowed and (self._audit_mode or self._current_policy.replay_richness == "FULL"):
            from src.engine.checkpoint import CanonicalStateHasher
            tick_hash = CanonicalStateHasher.get_hash(self._state)
            
        if self._current_policy.replay_allowed:
            self._replay.emit(TraceEvent(
                tick=self._state.tick,
                system="KERNEL",
                event_type="TICK_END",
                payload={"hash": tick_hash}
            ), self._current_policy)
            
        self._replay.on_tick_end(self._state.tick)

    def shutdown(self, timeout_s: float = 5.0) -> ShutdownResult:
        self._stopped = True
        self._worker_manager.shutdown()
        from src.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(self._state)
        logger.info(f"Final Auth Hash: {final_hash}")
        replay_outcome = self._replay.finalize(timeout_s=timeout_s)
        self._cache_registry.clear_all()
        return ShutdownResult(
            final_tick=self._state.tick,
            final_hash=final_hash,
            replay_outcome=replay_outcome,
            overall_outcome=LifecycleOutcome.SUCCESS if replay_outcome != LifecycleOutcome.FAILED else LifecycleOutcome.FAILED
        )

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    @property
    def state(self) -> AuthoritativeState:
        try:
            if getattr(self._state, "_opt_profile", None) is None:
                object.__setattr__(self._state, "_opt_profile", self._opt_profile)
                object.__setattr__(self._state, "_force_full_scan", self._force_full_scan)
        except Exception:
            pass
        return self._state

    def _get_deterministic_neighbor_view(
        self, 
        subject: EntityState, 
        radius: float
    ) -> List[tuple[int, EntityState]]:
        from src.engine.domain_logic import SimulationDomainLogic
        return SimulationDomainLogic.get_neighbor_view(self._state, subject, radius)
