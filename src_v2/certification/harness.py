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
    HardwareClass as CertHardwareClass, FailureKind, FailureKind as FK
)
from src_v2.certification.hardware import HardwareClassifier
from src_v2.certification.conformance import ConformanceEvaluator

logger = logging.getLogger(__name__)


class CertificationHarness:
    """
    M9 Law: The proof-oriented runner for certification scenarios.
    """

    def __init__(self, profile: RuntimeProfile, override_class: Optional[CertHardwareClass] = None):
        self._profile = profile
        self._detected_class = HardwareClassifier.detect_class()
        self._effective_class = override_class or self._detected_class
        self._override_applied = override_class is not None

    def run_scenario(
        self, 
        scenario_id: str,
        initial_state: AuthoritativeState,
        expectations: ScenarioExpectations,
        ticks: int = 100
    ) -> CertificationResult:
        """
        Execute a full certification scenario run.
        """
        run_id = str(uuid.uuid4())
        start_ts = time.time()
        
        # 1. Establish Baseline (Sequential)
        baseline_hash = self._get_baseline_hash(initial_state, ticks)
        
        # 2. Run Main Certification (Concurrent if profile allows)
        measurements: List[MeasurementPoint] = []
        mode_sequence: List[str] = []
        
        kernel = Kernel(self._profile, initial_state, DeterministicRNG(initial_state.seed))
        
        for t in range(ticks):
            kernel.tick_once()
            
            # M9 Law: Scenario-defined sampling cadence
            if t % expectations.sampling_interval_ticks == 0:
                snapshot = kernel.status.signal_history[-1] if kernel.status.signal_history else None
                if snapshot:
                    measurements.append(MeasurementPoint(
                        tick=t,
                        mode=kernel.status.current_mode.name,
                        memory_rss_mb=snapshot.memory_estimate_mb,
                        tick_compute_ms=snapshot.tick_compute_ms,
                        work_debt=snapshot.work_debt_total,
                        queue_utilization=snapshot.queue_utilization,
                        replay_pressure=0.0 # Placeholder
                    ))
            
            mode_sequence.append(kernel.status.current_mode.name)

        from src_v2.engine.checkpoint import CanonicalStateHasher
        final_hash = CanonicalStateHasher.get_hash(kernel.state)
        
        # 3. Evaluate Conformance
        passed, fail_kind, fail_reason = ConformanceEvaluator.evaluate(
            self._profile, expectations, measurements, 
            mode_sequence, baseline_hash, final_hash
        )
        
        return CertificationResult(
            run_id=run_id,
            timestamp=start_ts,
            profile_name=self._profile.name,
            scenario_id=scenario_id,
            seed=initial_state.seed,
            detected_hardware_class=self._detected_class,
            effective_hardware_class=self._effective_class,
            hardware_class_override_applied=self._override_applied,
            platform_info=HardwareClassifier.get_detailed_telemetry(),
            measurements=measurements,
            baseline_hash=baseline_hash,
            final_hash=final_hash,
            governor_mode_sequence=mode_sequence,
            conformance_passed=passed,
            failure_kind=fail_kind,
            failure_reason=fail_reason
        )

    def _get_baseline_hash(self, state: AuthoritativeState, ticks: int) -> str:
        """Establish the semantic source of truth via sequential execution."""
        # Create a special sequential profile for the baseline
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
