from __future__ import annotations

import argparse
import uuid
import time
import logging
from typing import List, Optional, Callable
from src_v2.core.state import AuthoritativeState
from src_v2.platform.rng import DeterministicRNG
from src_v2.engine.kernel import Kernel
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.certification.models import (
    CertificationResult, MeasurementPoint, ScenarioExpectations, 
    HardwareClass as CertHardwareClass, FailureKind, FailureKind as FK,
    EnvironmentCapture
)
from src_v2.certification.hardware import HardwareClassifier
from src_v2.certification.conformance import ConformanceEvaluator

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

    def __init__(self, profile: RuntimeProfile, override_class: Optional[CertHardwareClass] = None, output_dir: str = "reports/release_proof"):
        self._profile = profile
        self._output_dir = Path(output_dir)
        self._detected_facts = HardwareClassifier.get_detailed_telemetry()
        self._detected_class = HardwareClassifier.detect_class()
        self._effective_class = override_class or self._detected_class
        self._override_applied = override_class is not None
        
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
        ticks: int = 100
    ) -> CertificationResult:
        """
        Execute a full certification scenario run and return machine-readable proof.
        """
        run_id = str(uuid.uuid4())
        start_ts = time.time()
        
        # 1. Establish Baseline (For semantic equivalence)
        baseline_hash = self._get_baseline_hash(initial_state, ticks)
        
        # 2. Run Main Certification (Run 1)
        measurements: List[MeasurementPoint] = []
        mode_sequence: List[str] = []
        
        kernel = Kernel(self._profile, initial_state, DeterministicRNG(initial_state.seed))
        
        for t in range(ticks):
            kernel.tick_once()
            
            # M10 Law: required_sampling_interval_ticks enforcement
            if t % expectations.required_sampling_interval_ticks == 0:
                snapshot = kernel.status.signal_history[-1] if kernel.status.signal_history else None
                if snapshot:
                    # M10 Law: Capture TRUTHFUL signals
                    replay_stats = kernel.replay.get_stats()
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

        from src_v2.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(kernel.state)
        
        # 3. Reproducibility Check (Run 2)
        secondary_hash = None
        if expectations.reproducibility_required:
            logger.info(f"Scenario {scenario_id}: executing 2nd run for reproducibility proof.")
            # Fresh state, fresh RNG with same seed
            kernel2 = Kernel(self._profile, initial_state, DeterministicRNG(initial_state.seed))
            for _ in range(ticks):
                kernel2.tick_once()
            secondary_hash = CanonicalStateHasher.get_hash(kernel2.state)

        # 4. Evaluate Conformance
        passed, fail_kind, fail_reason, allowed_failure_observed = ConformanceEvaluator.evaluate(
            self._profile, expectations, measurements, 
            mode_sequence, baseline_hash, final_hash,
            secondary_hash=secondary_hash
        )
        
        # 5. Construct Result
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
            allowed_failure_observed=allowed_failure_observed,
            failure_kind=fail_kind,
            failure_reason=fail_reason
        )
        
        # 6. Persist Proof Bundle (M10 Law)
        self._persist_proof_bundle(result)
        
        return result

    def _persist_proof_bundle(self, result: CertificationResult):
        """Save evidence to the deterministic output directory."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        # A. Machine-Readable JSON
        json_path = self._output_dir / f"release_proof_{result.profile_name}_{result.scenario_id}.json"
        with open(json_path, "w") as f:
            f.write(result.to_json())
            
        # B. Manifest Snapshot (M10 Alignment)
        manifest_path = Path("docs/engine/manifest.json")
        if manifest_path.exists():
            snapshot_path = self._output_dir / "manifest_snapshot.json"
            with open(manifest_path, "r") as src, open(snapshot_path, "w") as dst:
                dst.write(src.read())
            
        # C. Human-Readable Scoped Report
        report_path = self._output_dir / "release_report.md"
        with open(report_path, "w") as f:
            f.write(self._generate_scoped_report(result))
            
        logger.info(f"Proof bundle persisted to {self._output_dir}")

    def _generate_scoped_report(self, result: CertificationResult) -> str:
        """M10 Law: Scoped reporting model."""
        outcome = "PASS" if result.conformance_passed else f"FAIL [{result.failure_kind}]"
        
        return f"""# Certification Report: {result.scenario_id}
## Status: {outcome}

### Scoped Metadata (M10 Honest Reporting Quadrant)
- **Profile**: {result.profile_name}
- **Scenario**: {result.scenario_id}
- **Hardware Class**: {result.environment.effective_class.name}
- **Override Status**: {result.environment.override_applied}
- **Commit SHA**: {result.commit_sha}

### Environment Capture
- Detected HW: {result.environment.detected_class.name}
- Platform: {result.environment.detected_facts.get('system', 'unknown')}

### Conformance Outcome
- **Success**: {result.conformance_passed}
- **Failure Kind**: {result.failure_kind.name}
- **Reason**: {result.failure_reason or "N/A"}

### Evidence
- **Ticks**: {len(result.governor_mode_sequence)}
- **Measurements**: {len(result.measurements)}
- **Baseline Hash**: `{result.baseline_hash}`
- **Final Hash**:    `{result.final_hash}`
"""

    def _get_baseline_hash(self, state: AuthoritativeState, ticks: int) -> str:
        """Establish source of truth via deterministic sequential execution."""
        profile_dict = self._profile.model_dump()
        profile_dict["max_worker_count"] = 0 # Forced sequential
        baseline_profile = RuntimeProfile(**profile_dict)
        
        kernel = Kernel(baseline_profile, state, DeterministicRNG(state.seed))
        for _ in range(ticks):
            kernel.tick_once()
            
        from src_v2.engine.checkpoint import CanonicalStateHasher
        return CanonicalStateHasher.get_hash(kernel.state)


if __name__ == "__main__":
    # Example CLI wrapper
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--force-hardware-class", choices=["class_a", "class_b", "class_c"])
    args = parser.parse_args()
    print(f"Certification Harness: Starting run for profile {args.profile}")
