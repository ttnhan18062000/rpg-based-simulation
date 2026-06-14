# Compliance IDs: INFRA-001, INFRA-002
from __future__ import annotations

import argparse
import hashlib
import uuid
import time
import logging
from typing import List, Optional, Callable, Tuple
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.certification.models import (
    CertificationResult, MeasurementPoint, ScenarioExpectations,
    HardwareClass as CertHardwareClass, FailureKind, FailureKind as FK,
    EnvironmentCapture, EvidenceLevel
)
from src.certification.hardware import HardwareClassifier
from src.certification.conformance import ConformanceEvaluator
from src.certification.recorder import CertificationRecorder

logger = logging.getLogger(__name__)


import os
import json
import subprocess
from dataclasses import asdict
from pathlib import Path


class CertificationHarness:
    """
    M10 Law: The proof-oriented runner for certification scenarios.
    Generated evidence is the definitive source of truth for production readiness.
    """

    def __init__(self, profile: RuntimeProfile, override_class: Optional[CertHardwareClass] = None, output_dir: str = "reports/certification", manifest_path: Optional[Path] = None):
        self._profile = profile
        self._output_dir = Path(output_dir)
        self._detected_facts = HardwareClassifier.get_detailed_telemetry()
        self._detected_class = HardwareClassifier.detect_class()
        self._effective_class = override_class or self._detected_class
        self._override_applied = override_class is not None
        self._manifest_path: Optional[Path] = manifest_path if manifest_path is not None else Path("docs/engine/manifest.json")

        # M10 Law: Initialize the authoritative recorder
        self._recorder = CertificationRecorder(output_dir)
        
        # M10 Law: Commit Provenance
        self._commit_sha = self._get_current_sha()

    def _get_current_sha(self) -> str:
        """Capture engine commit identity."""
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                stderr=subprocess.STDOUT
            ).decode().strip()
        except Exception:
            return "unknown-dirty"

    def run_scenario(
        self,
        scenario_id: str,
        initial_state: AuthoritativeState,
        expectations: ScenarioExpectations,
        ticks: int = 100,
        evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY,
    ) -> CertificationResult:
        """
        Execute a full certification scenario run and return machine-readable proof.
        """
        run_id = str(uuid.uuid4())
        start_ts = time.time()
        
        from src.certification.models import EnvironmentCapture, MeasurementPoint, CertificationResult
        from src.engine.kernel import Kernel
        from src.platform.rng import DeterministicRNG
        from src.certification.conformance import ConformanceEvaluator
        from src.engine.checkpoint import CanonicalStateHasher
        
        start_ts = time.time()
        measurements: List[MeasurementPoint] = []
        
        # 1. Reproducibility Check (Run 1)
        baseline_hash = self._get_baseline_hash(initial_state, ticks)
        kernel = Kernel(self._profile, initial_state, DeterministicRNG(initial_state.seed), flags={"audit_mode": True})
        
        # M10 Law: Boot state must be captured before tick mutations
        mode_sequence = [kernel.status.current_mode.name]
        
        # 2. RUN (Subject Execution)
        # Note: We capture measurements during this loop.
        from src.certification.models import ArenaStopCondition
        stop_condition = ArenaStopCondition.TIMEOUT
        
        import concurrent.futures
        
        for t in range(1, ticks + 1):
            # Arena WIPE check: Are all enemies or all allies dead?
            alive_factions = {e.identity.faction for e in kernel.state.entities.values() if e.combat.alive}
            if len(alive_factions) <= 1 and t > 1:
                logger.info(f"Scenario {scenario_id}: WIPE detected at tick {t}. Terminating early.")
                stop_condition = ArenaStopCondition.WIPE
                break
            
            # Watchdog: Run tick in executor with timeout
            # M10 Law: Protect against tick hangs
            t1 = time.perf_counter_ns()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(kernel.tick_once)
                try:
                    # Timeout based on profile + buffer
                    timeout = (self._profile.max_tick_budget_ms * 5.0) / 1000.0
                    if timeout < 1.0: timeout = 1.0 # Minimum 1s for safety
                    future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    logger.critical(f"Scenario {scenario_id}: Watchdog triggered at tick {t}. Tick hung.")
                    stop_condition = ArenaStopCondition.WATCHDOG
                    break
                except Exception as e:
                    logger.error(f"Scenario {scenario_id}: Tick failed with error: {e}")
                    raise
                
            # M10 Law: Fast-Tick Watchdog (Task 5.4 Hardening)
            # If compute is extremely low (< 0.1ms) for many consecutive ticks, 
            # it might indicate a loop logic failure or 'ghost' simulation.
            tick_ms = (time.perf_counter_ns() - t1) / 1e6
            if tick_ms < 0.1:
                 fast_tick_count = getattr(self, "_fast_tick_count", 0) + 1
                 self._fast_tick_count = fast_tick_count
                 if fast_tick_count > 100:
                      logger.warning(f"Scenario {scenario_id}: Fast-Tick Watchdog triggered. 100 ticks at <0.1ms.")
                      # We don't necessarily stop, but we record it.
            else:
                 self._fast_tick_count = 0
            
            # M10 Law: required_sampling_interval_ticks enforcement
            if t % expectations.required_sampling_interval_ticks == 0 or t == ticks:
                snapshot = kernel.status.signal_history[-1] if kernel.status.signal_history else None
                if snapshot:
                    # M10 Law: Capture TRUTHFUL signals
                    # We access internal stats for certification-level precision
                    replay_stats = kernel._replay.get_stats()
                    measurements.append(MeasurementPoint(
                        tick=t,
                        mode=kernel.status.current_mode.name,
                        memory_rss_mb=snapshot.memory_estimate_mb,
                        memory_trend_mb_per_tick=snapshot.memory_trend_mb_per_tick,
                        tick_compute_ms=snapshot.tick_compute_ms,
                        tick_compute_ms_avg=snapshot.tick_compute_ms_avg,
                        work_debt=snapshot.work_debt_total,
                        worker_utilization=snapshot.worker_utilization,
                        queue_utilization=snapshot.queue_utilization,
                        replay_pressure=replay_stats["buffer_utilization"],
                        active_workers=snapshot.active_workers
                    ))
            
            mode_sequence.append(kernel.status.current_mode.name)

        # 3. FINALIZATION (Lifecycle Truth Propagation)
        # M7/M10 Law: Derive lifecycle result from real runtime shutdown.
        shutdown_res = kernel.shutdown(timeout_s=expectations.shutdown_timeout_s)
        final_hash = shutdown_res.final_hash
        lifecycle_outcome = shutdown_res.overall_outcome.value
        
        # 4. Reproducibility Check (Run 2)
        secondary_hash = None
        if expectations.reproducibility_required:
            logger.info(f"Scenario {scenario_id}: executing 2nd run for reproducibility proof.")
            # Fresh state, fresh RNG with same seed
            kernel2 = Kernel(self._profile, initial_state, DeterministicRNG(initial_state.seed), flags={"audit_mode": True})
            for t in range(1, ticks + 1):
                # Phase 9 Fix: Reproducibility must respect the same stop conditions
                alive_factions = {e.identity.faction for e in kernel2.state.entities.values() if e.combat.alive}
                if len(alive_factions) <= 1 and t > 1:
                    break
                    
                kernel2.tick_once()
            # We don't necessarily need a clean shutdown for the 2nd run's hash,
            # but we use the state hash directly for performance.
            from src.engine.checkpoint import CanonicalHashScheduler, HashMode
            secondary_hash = CanonicalHashScheduler().compute_hash(
                kernel2.state, tick=kernel2.state.tick, mode=HashMode.FULL, reason="certification"
            )

        # 5. Evaluate Conformance
            
        passed, fail_kind, fail_reason, allowed_failure_observed = ConformanceEvaluator.evaluate(
            self._profile, expectations, measurements, 
            mode_sequence, baseline_hash, final_hash,
            secondary_hash=secondary_hash,
            lifecycle_outcome=lifecycle_outcome
        )
        
        # 5. Construct Result
        peak_rss = max([p.memory_rss_mb for p in measurements]) if measurements else 0.0
        total_cpu = sum([p.tick_compute_ms for p in measurements]) / 1000.0 if measurements else 0.0
        
        result = CertificationResult(
            run_id=run_id,
            timestamp=start_ts,
            commit_sha=self._commit_sha,
            profile_name=self._profile.name,
            scenario_id=scenario_id,
            seed=initial_state.seed,
            environment=EnvironmentCapture(
                detected_facts=self._detected_facts,
                detected_class=self._detected_class,
                effective_class=self._effective_class,
                override_applied=self._override_applied,
                os_name="linux",
                python_version="3.13"
            ),
            measurements=measurements,
            baseline_hash=baseline_hash,
            final_hash=final_hash,
            governor_mode_sequence=mode_sequence,
            conformance_passed=passed,
            stop_condition=stop_condition,
            allowed_failure_observed=allowed_failure_observed,
            failure_kind=fail_kind,
            failure_reason=fail_reason,
            peak_rss_mb=peak_rss,
            total_cpu_sec=total_cpu,
            final_state=kernel.state
        )
        
        # 6. Persist Proof Bundle (M10 Law)
        self._persist_proof_bundle(result, evidence_level)
        
        return result

    def _write_full_evidence(self, result: CertificationResult) -> "Optional[Tuple[str, str]]":
        """Write canonical state to <output_dir>/state/<run_id>.final_state.canonical.json.

        Returns (relative_path, sha256_hex) on success, None on failure.
        Failure is non-fatal — logged as a warning, never raises.
        Uses CanonicalStateHasher.to_canonical_data() — never asdict().
        """
        if result.final_state is None:
            return None
        try:
            from src.engine.checkpoint import CanonicalStateHasher
            state_dir = self._output_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = state_dir / f"{result.run_id}.final_state.canonical.json"
            canonical_data = CanonicalStateHasher.to_canonical_data(result.final_state)
            # Pretty for human readability; compact for hash (matching get_hash())
            pretty_json = json.dumps(canonical_data, sort_keys=True, indent=2)
            compact_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
            final_state_hash = hashlib.sha256(compact_json.encode("utf-8")).hexdigest()
            state_path.write_text(pretty_json, encoding="utf-8")
            relative_path = f"state/{result.run_id}.final_state.canonical.json"
            logger.info(f"Full canonical state written to {state_path}")
            return (relative_path, final_state_hash)
        except Exception as exc:
            logger.warning(f"Full evidence write failed (non-fatal): {exc}")
            return None

    def _persist_proof_bundle(self, result: CertificationResult, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY):
        """Save evidence to the deterministic output directory."""
        # OPEN-1 resolution: write the state file FIRST so the actual path (or None on
        # failure) is passed into to_artifact_dict() — never a speculative path string.
        artifact_path: Optional[str] = None
        artifact_hash: Optional[str] = None
        if evidence_level == EvidenceLevel.FULL:
            write_result = self._write_full_evidence(result)
            if write_result is not None:
                artifact_path, artifact_hash = write_result

        # 1. Authoritative Recording (M10 Law)
        # This handles JSON persistence and human-readable MD generation.
        self._recorder.record(result, evidence_level, artifact_path, artifact_hash)

        # 2. Manifest Snapshot (certification_contract_me.md §1)
        try:
            if self._manifest_path is None or not self._manifest_path.exists():
                logger.warning("manifest_snapshot.json not written: manifest path unavailable or missing")
            else:
                snapshot_path = self._output_dir / "manifest_snapshot.json"
                snapshot_path.write_text(self._manifest_path.read_text())
        except Exception as exc:
            logger.warning(f"manifest_snapshot.json write failed (non-fatal): {exc}")

        logger.info(f"Proof bundle persisted to {self._output_dir}")


    def _get_baseline_hash(self, state: AuthoritativeState, ticks: int) -> str:
        """Establish source of truth via deterministic sequential execution."""
        profile_dict = self._profile.model_dump()
        profile_dict["max_worker_count"] = 0 # Forced sequential
        baseline_profile = RuntimeProfile(**profile_dict)
        
        kernel = Kernel(baseline_profile, state, DeterministicRNG(state.seed), flags={"audit_mode": True})
        for t in range(1, ticks + 1):
            # Phase 9 Fix: Baseline must respect the same stop conditions as the subject run
            alive_factions = {e.identity.faction for e in kernel.state.entities.values() if e.combat.alive}
            if len(alive_factions) <= 1 and t > 1:
                break

            kernel.tick_once()
            
        from src.engine.checkpoint import CanonicalHashScheduler, HashMode
        return CanonicalHashScheduler().compute_hash(
            kernel.state, tick=kernel.state.tick, mode=HashMode.FULL, reason="certification"
        )


if __name__ == "__main__":
    # Example CLI wrapper
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--force-hardware-class", choices=["class_a", "class_b", "class_c"])
    args = parser.parse_args()
    print(f"Certification Harness: Starting run for profile {args.profile}")
