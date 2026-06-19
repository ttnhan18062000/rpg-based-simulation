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
from src.core.enums import Domain

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
        "_phase_costs", "_metrics", "_audit_mode", "_no_frame_pacing", "_no_replay", "_audit_dirty_set", "_perf_tracker", "_force_full_scan", "_current_update", "_cache_registry", "_cache_policy", "_opt_profile", "_event_listeners", "_event_recorder", "_entity_timeline_store",
        "_run_id", "_artifact_repo", "_metric_recorder", "_current_tick_event_count", "_current_tick_violation_count", "_cognition_recorder",
        "_workers_started", "_last_shutdown_report",
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
        flags: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        resolved_world_path: Optional[str] = None,
        compile_context_path: Optional[str] = None,
        provenance_manifest_path: Optional[str] = None,
        assembly_report_path: Optional[str] = None,
        validation_report_path: Optional[str] = None,
        compile_report_path: Optional[str] = None,
        runtime_content_source: Optional[str] = None,
        catalog_fingerprint: Optional[str] = None,
        module_fingerprints: Optional[Dict[str, str]] = None
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
        
        from src.observability.config import ObservabilityConfig, ObservabilityMode
        obs_mode = ObservabilityConfig.get_mode()

        self._run_id = run_id
        if self._run_id is None:
            _run_suffix = self._rng.get_int(Domain.INIT, 0, 0, 1000, 9999)
            self._run_id = f"run_{int(time.time())}_{_run_suffix}"

        self._artifact_repo = None
        if obs_mode != ObservabilityMode.OFF:
            from datetime import datetime, timezone
            import os
            from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
            self._artifact_repo = RunArtifactRepository()
            
            # Load metadata from provenance manifest if available
            prov_manifest_data = None
            if provenance_manifest_path and os.path.exists(provenance_manifest_path):
                try:
                    with open(provenance_manifest_path, "r", encoding="utf-8") as f:
                        prov_manifest_data = json.load(f)
                except Exception:
                    pass

            catalog_fp = catalog_fingerprint
            if not catalog_fp and prov_manifest_data:
                catalog_fp = prov_manifest_data.get("catalog_fingerprint")
            
            module_fps = module_fingerprints
            if not module_fps and prov_manifest_data:
                module_fps = prov_manifest_data.get("module_fingerprints")

            from src.core.registries import runtime_content_source as registries_source, catalog_fingerprint as registries_fingerprint
            actual_content_source = runtime_content_source or registries_source
            actual_catalog_fp = catalog_fp or registries_fingerprint

            # Create standard manifest
            manifest = RunManifest(
                run_id=self._run_id,
                scenario_name=profile.name,
                scenario_type="mixed_sandbox",
                seed=state.seed,
                observability_mode=obs_mode.value,
                started_at=datetime.now(timezone.utc).isoformat(),
                ticks_requested=profile.cadence.max_ticks if hasattr(profile, "cadence") and hasattr(profile.cadence, "max_ticks") else 100,
                status="CREATED",
                resolved_world_path=resolved_world_path,
                compile_context_path=compile_context_path,
                provenance_manifest_path=provenance_manifest_path,
                assembly_report_path=assembly_report_path,
                validation_report_path=validation_report_path,
                compile_report_path=compile_report_path,
                runtime_content_source=actual_content_source,
                catalog_fingerprint=actual_catalog_fp,
                module_fingerprints=module_fps,
                state_hash=None
            )
            self._artifact_repo.create_run(self._run_id, manifest, overwrite=True)
            self._artifact_repo.update_manifest(self._run_id, status="RUNNING")

        if replay is None:
            import os
            run_dir = Path(self._artifact_repo.resolve_path(self._run_id, "manifest")).parent if self._artifact_repo else Path(f"data/runs/{self._run_id}")
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
        self._event_listeners = []

        from src.observability.event_recorder import EventRecorder
        from src.observability.entity_timeline import EntityTimelineStore

        run_dir_str = None
        if self._artifact_repo:
            run_dir_str = os.path.join(self._artifact_repo.base_dir, self._run_id)
        elif hasattr(self._replay, "_run_dir"):
            run_dir_str = str(self._replay._run_dir)

        self._event_recorder = EventRecorder(
            run_dir=run_dir_str,
            max_events=5000,
            enabled=(obs_mode != ObservabilityMode.OFF)
        )
        self._entity_timeline_store = EntityTimelineStore(mode=obs_mode)

        self._metric_recorder = None
        self._cognition_recorder = None
        if obs_mode != ObservabilityMode.OFF:
            from src.observability.reporting.metric_recorder import MetricWindowRecorder
            from src.observability.cognition.recorder import ObservabilityCognitionRecorder
            self._metric_recorder = MetricWindowRecorder(
                run_id=self._run_id,
                run_dir=run_dir_str,
                window_size=100,
                enabled=True
            )
            self._cognition_recorder = ObservabilityCognitionRecorder(
                run_id=self._run_id,
                run_dir=run_dir_str
            )

        self._current_tick_event_count = 0
        self._current_tick_violation_count = 0

        # Lifecycle supervisor: count registered workers for shutdown accounting.
        # 1 = EventRecorder._worker (QueueDrainWorker), started when obs is enabled.
        self._workers_started = 1 if (obs_mode != ObservabilityMode.OFF) else 0
        self._last_shutdown_report = None

        self.validate(flags)

        # WORLD-CAT-004: warm all content singletons before the first tick so that
        # CatalogRepository.load_all() is never triggered from inside tick_once().
        try:
            from src.content.warmup import ContentWarmupService
            ContentWarmupService.warmup()
        except Exception as _warmup_err:
            logger.warning("ContentWarmupService.warmup() failed (non-fatal): %s", _warmup_err)

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

        # WORLD-CAT-004: mark tick context active so CatalogRepository.load_all()
        # raises ContentHotPathViolation if called from inside the tick pipeline.
        from src.content.repository import _tick_context_active
        _tick_context_active.active = True
        try:
            self._tick_once_inner()
        finally:
            _tick_context_active.active = False

    def _tick_once_inner(self) -> None:
        """Inner tick body — never call directly, use tick_once()."""
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
             try:
                 from src.observability.alerts.manager import AlertsManager
                 from src.observability.alerts.models import AlertEvent
                 router = AlertsManager.get_router()
                 event = AlertEvent.create_watchdog_trip(
                     run_id=self._run_id,
                     tick=self._state.tick,
                     message=f"Tick compute time {self._final_compute_ms:.2f}ms exceeded watchdog threshold of {min(hard_cap, limit_ms):.2f}ms",
                     details={
                         "compute_ms": self._final_compute_ms,
                         "threshold_ms": min(hard_cap, limit_ms),
                         "phase_costs": self._phase_costs.copy()
                     }
                 )
                 router.route(event)
             except Exception:
                 logger.exception("Failed to route watchdog budget alert")
        
        self._record_runtime_signals()

        if self._metric_recorder:
            try:
                from src.engine.metrics import MetricsService
                world_metrics = MetricsService.extract_metrics(self._state)
            except Exception:
                logger.exception("Failed to extract WorldMetrics")
                world_metrics = None

            signals = self._status.signal_history[-1] if self._status.signal_history else None
            event_count = getattr(self, "_current_tick_event_count", 0)
            violation_count = getattr(self, "_current_tick_violation_count", 0)

            self._metric_recorder.record_tick(
                tick=self._state.tick,
                world_metrics=world_metrics,
                pressure_signals=signals,
                runtime_status=self._status,
                event_count_delta=event_count,
                violation_count_delta=violation_count
            )

    def _phase_init(self) -> None:
        from src.world.providers.requirements import PerformanceBudgets
        PerformanceBudgets.reset()
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
        
        prior_mode = self._status.current_mode
        self._current_policy = self._governor.evaluate(
            self._profile, 
            self._current_signals, 
            self._status, 
            self._state.tick,
            opt_profile=getattr(self, "_opt_profile", None)
        )
        if prior_mode != self._status.current_mode:
            self._status.previous_mode = prior_mode.name
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
                    try:
                        from src.observability.alerts.manager import AlertsManager
                        from src.observability.alerts.models import AlertEvent
                        router = AlertsManager.get_router()
                        event = AlertEvent.create_watchdog_trip(
                            run_id=self._run_id,
                            tick=self._state.tick,
                            message=f"Mid-tick emergency throttle triggered: tick compute took {elapsed:.2f}ms, forced governor DEGRADED",
                            details={
                                "elapsed_ms": elapsed,
                                "dropped_count": len(self._final_results) - i
                            }
                        )
                        router.route(event)
                    except Exception:
                        logger.exception("Failed to route emergency throttle alert")
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
            
        prior_state = self._state
        self._state = ApplyPath.apply_generation(
            self._state, 
            update, 
            next_tick=self._state.tick + 1,
            next_world_time=self._current_world_time,
            cadence=self._profile.cadence,
            audit_mode=self._audit_mode,
            audit_dirty_set=self._audit_dirty_set
        )
        
        self._run_hard_law_checks(update.dirty_set)
        self._phase_observability(prior_state, update)
        
        self._current_update = None
        try:
            object.__setattr__(self._state, "_opt_profile", self._opt_profile)
            object.__setattr__(self._state, "_force_full_scan", self._force_full_scan)
        except Exception:
            pass
        
        # Keep movement_cache registered across state advancements
        if getattr(self._state, "movement_cache", None) is not None:
            self._cache_registry.register_cache("movement_plan_cache", self._state.movement_cache)

    def _run_hard_law_checks(self, dirty_set: Optional[Any]) -> None:
        from src.observability.config import ObservabilityConfig, ObservabilityMode
        from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError

        mode = ObservabilityConfig.get_mode()
        if mode == ObservabilityMode.OFF:
            return

        # Expose dirty set on status for ReadModelCache/V2EngineManager access
        if dirty_set is not None:
            self._status.dirty_set = dirty_set
        else:
            if hasattr(self._status, "dirty_set"):
                delattr(self._status, "dirty_set")

        violations = HardLawMonitor.check(self._state, dirty_set)
        self._status.current_tick_violations = violations
        if not violations:
            return

        if not hasattr(self._status, "cumulative_violations"):
            self._status.cumulative_violations = {}
        if not hasattr(self._status, "hard_law_violations"):
            self._status.hard_law_violations = []

        self._status.hard_law_violations.extend(violations)
        self._status.last_hard_law_violation_tick = self._state.tick

        for v in violations:
            self._status.cumulative_violations[v.law_id] = self._status.cumulative_violations.get(v.law_id, 0) + 1

        # Route hard law violations to alerts and persist them to jsonl
        if self._artifact_repo and self._run_id:
            try:
                import os
                import json
                v_path = self._artifact_repo.resolve_path(self._run_id, "violations")
                os.makedirs(os.path.dirname(v_path), exist_ok=True)
                with open(v_path, "a", encoding="utf-8") as f:
                    for v in violations:
                        record = {
                            "tick": self._state.tick,
                            "law_id": v.law_id,
                            "entity_id": v.entity_id,
                            "severity": v.severity,
                            "message": v.message,
                            "details": v.details
                        }
                        f.write(json.dumps(record) + "\n")
            except Exception:
                logger.exception("Failed to write to hard_law_violations.jsonl")

        try:
            from src.observability.alerts.manager import AlertsManager
            from src.observability.alerts.models import AlertEvent
            router = AlertsManager.get_router()
            for v in violations:
                event = AlertEvent.create_hard_law_violation(self._run_id, self._state.tick, v)
                router.route(event)
        except Exception:
            logger.exception("Failed to route hard law violation alerts")

        if mode in (ObservabilityMode.DEBUG, ObservabilityMode.CERTIFICATION):
            raise HardLawViolationError(violations)
        elif mode == ObservabilityMode.LIGHT:
            for v in violations:
                logger.warning(f"[{v.severity}] Hard Law Violation: {v.law_id} on entity {v.entity_id}: {v.message}")

    def _phase_observability(self, prior_state: AuthoritativeState, update: Any) -> None:
        from src.observability.config import ObservabilityConfig, ObservabilityMode
        obs_mode = ObservabilityConfig.get_mode()
        if obs_mode == ObservabilityMode.OFF:
            return

        from src.observability.event_extractor import EventExtractor
        from src.observability.events import SimulationEvent

        tick = self._state.tick
        
        # 1. Extract domain events
        generated_events = EventExtractor.extract(prior_state, self._state, update, obs_mode)

        # 2. Convert hard law violations to SimulationEvents
        current_violations = getattr(self._status, "current_tick_violations", [])
        for v in current_violations:
            event = SimulationEvent(
                event_type="InvariantViolation",
                event_category="hard_law",
                tick=tick,
                severity=v.severity,
                source_system="hard_law_monitor",
                message=v.message,
                entity_id=v.entity_id,
                payload=v.details
            )
            generated_events.append(event)

        # Emit GovernorModeChanged if a transition happened this tick
        if getattr(self._status, "last_transition_tick", -1) == tick:
            prev_mode = getattr(self._status, "previous_mode", "NORMAL")
            event = SimulationEvent(
                event_type="GovernorModeChanged",
                event_category="infrastructure",
                tick=tick,
                severity="WARNING" if self._status.current_mode.name != "NORMAL" else "INFO",
                source_system="resource_governor",
                message=f"Governor operational mode transitioned from {prev_mode} to {self._status.current_mode.name}",
                payload={
                    "previous_mode": prev_mode,
                    "current_mode": self._status.current_mode.name,
                    "mode_dwell_ticks": self._status.mode_dwell_ticks
                }
            )
            generated_events.append(event)

        self._current_tick_event_count = len(generated_events)
        self._current_tick_violation_count = len(current_violations)

        # Clear current tick violations from status
        if hasattr(self._status, "current_tick_violations"):
            delattr(self._status, "current_tick_violations")

        # 3. Record events to buffers and timeline store
        for event in generated_events:
            self._event_recorder.record(event)
            self._entity_timeline_store.record(event)

            # Fallback for backwards compatibility with legacy tests/code accessing entity.timeline
            if event.entity_id is not None:
                entity = self._state.entities.get(event.entity_id)
                if entity and hasattr(entity, "timeline") and entity.timeline is not None:
                    entity.timeline.append(event)

        # 4. Notify any external event listeners
        if generated_events and hasattr(self, "_event_listeners"):
            for listener in self._event_listeners:
                try:
                    listener(generated_events)
                except Exception:
                    logger.exception("Error notifying event listener in Kernel")

        # 5. Record strategic cognition snapshots post-commit
        if getattr(self, "_cognition_recorder", None) is not None:
            try:
                self._cognition_recorder.record_tick(
                    state=self._state,
                    tick=tick,
                    events=generated_events,
                    event_recorder=self._event_recorder
                )
            except Exception:
                logger.exception("Failed to record strategic cognition snapshot in Kernel")

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
        from src.core.lifecycle import ShutdownReport
        self._stopped = True
        report = ShutdownReport(workers_started=getattr(self, "_workers_started", 0))
        workers_stopped = 0

        self._worker_manager.shutdown()

        if hasattr(self, "_event_recorder") and self._event_recorder:
            self._event_recorder.shutdown()
            workers_stopped += 1

        if hasattr(self, "_metric_recorder") and self._metric_recorder:
            self._metric_recorder.shutdown(self._state.tick)

        # Wire BehaviorWorker into shutdown: join any running behavior-normalization threads.
        import threading
        for t in threading.enumerate():
            if t.name == "behavior-normalization-worker" and t.is_alive():
                t.join(timeout=1.0)
                if t.is_alive():
                    report.warnings.append(f"behavior-normalization-worker did not stop within 1s")
                    report.outcome = "PARTIAL"

        from src.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(self._state)
        logger.info(f"Final Auth Hash: {final_hash}")
        replay_outcome = self._replay.finalize(timeout_s=timeout_s)

        # Collect replay backpressure metrics.
        if hasattr(self._replay, "replay_metrics"):
            rm = self._replay.replay_metrics()
            report.pending_replay_flushes = rm.get("pending_replay_flushes", rm.get("pending_flushes", 0))
            if report.pending_replay_flushes > 0:
                report.warnings.append(
                    f"pending_replay_flushes={report.pending_replay_flushes} at shutdown"
                )

        # Collect survival event counts from observability mode controller.
        if hasattr(self, "_event_recorder") and self._event_recorder:
            report.survival_event_counts = dict(
                getattr(self._event_recorder, "_survival_event_counts", {})
            )

        # Open file handle count via psutil (advisory, non-fatal).
        try:
            import psutil
            report.open_file_handles = len(psutil.Process().open_files())
        except Exception:
            report.open_file_handles = -1

        report.workers_stopped = workers_stopped
        if report.outcome == "SUCCESS" and workers_stopped < report.workers_started:
            report.outcome = "PARTIAL"
            report.warnings.append(
                f"workers_started={report.workers_started} but workers_stopped={workers_stopped}"
            )

        if replay_outcome == LifecycleOutcome.FAILED and report.outcome == "SUCCESS":
            report.outcome = "FAILED"

        self._last_shutdown_report = report

        # Update manifest status to COMPLETED/FAILED
        if hasattr(self, "_artifact_repo") and self._artifact_repo and self._run_id:
            from datetime import datetime, timezone
            status = "COMPLETED" if replay_outcome != LifecycleOutcome.FAILED else "FAILED"
            self._artifact_repo.update_manifest(
                self._run_id,
                status=status,
                ticks_completed=self._state.tick,
                ended_at=datetime.now(timezone.utc).isoformat(),
                state_hash=final_hash
            )

        self._cache_registry.clear_all()
        return ShutdownResult(
            final_tick=self._state.tick,
            final_hash=final_hash,
            replay_outcome=replay_outcome,
            overall_outcome=LifecycleOutcome.SUCCESS if replay_outcome != LifecycleOutcome.FAILED else LifecycleOutcome.FAILED
        )

    def shutdown_report(self):
        """Return the ShutdownReport cached by the last shutdown() call, or None."""
        return getattr(self, "_last_shutdown_report", None)

    def resource_snapshot(self) -> list:
        """Return a list of SubsystemPressureReport from all subsystems (RESOURCE-DASHBOARD).

        Non-blocking. Each report is advisory only.
        """
        reports = []
        try:
            if hasattr(self, "_event_recorder") and self._event_recorder:
                reports.append(self._event_recorder.pressure_report())
        except Exception:
            pass
        try:
            if hasattr(self, "_replay") and self._replay:
                reports.append(self._replay.pressure_report())
        except Exception:
            pass
        return reports

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    @property
    def event_recorder(self) -> Any:
        return self._event_recorder

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def entity_timeline_store(self) -> Any:
        return self._entity_timeline_store

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
