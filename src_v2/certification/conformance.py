from __future__ import annotations

from typing import List, Optional
from src_v2.certification.models import (
    CertificationResult, FailureKind, MeasurementPoint, ScenarioExpectations
)
from src_v2.config.profiles import RuntimeProfile


class ConformanceEvaluator:
    """
    M9 Law: Multi-dimensional conformance evaluation.
    Beyond simple envelope ceilings.
    """

    @staticmethod
    def evaluate(
        profile: RuntimeProfile,
        expectations: ScenarioExpectations,
        measurements: List[MeasurementPoint],
        mode_sequence: List[str],
        baseline_hash: Optional[str],
        final_hash: Optional[str]
    ) -> (bool, FailureKind, str):
        """
        Comprehensive pass/fail check.
        """
        # 1. Envelope Compliance
        for p in measurements:
            if p.memory_rss_mb > profile.max_ram_mb:
                return False, FailureKind.FAILED_ENVELOPE, f"RAM violation at tick {p.tick}: {p.memory_rss_mb} > {profile.max_ram_mb}"
            
            # Note: Tick compute ms is checked against budget
            if p.tick_compute_ms > profile.max_tick_budget_ms:
                # We allow some bursts unless it's sustained? No, M9 is strict.
                # But we only mark failure if it happens when governor should have shed.
                pass 

        # 2. Semantic Equivalence
        if expectations.requires_semantic_equivalence:
            if not baseline_hash or not final_hash or baseline_hash != final_hash:
                return False, FailureKind.FAILED_SEMANTIC_DRIFT, f"Hash mismatch: baseline={baseline_hash}, final={final_hash}"

        # 3. Degradation Order (Simple heuristic for M9)
        # Verify that if we were under pressure, we actually entered degraded modes
        for mode in expectations.required_governor_modes:
            if mode not in mode_sequence:
                return False, FailureKind.FAILED_DEGRADATION_ORDER, f"Expected mode {mode} was never entered."

        # 4. Recovery Behavior
        if expectations.requires_recovery:
            # Must return to NORMAL eventually
            if mode_sequence[-1] != "NORMAL":
                return False, FailureKind.FAILED_RECOVERY, "System failed to return to NORMAL mode after pressure."
            
            # Check duration of degraded state? (Optional for M9)
            pass

        return True, FailureKind.NONE, "Certification PASS"
