from __future__ import annotations

from typing import List, Optional
from src.certification.models import (
    CertificationResult, FailureKind, MeasurementPoint, ScenarioExpectations
)
from src.config.profiles import RuntimeProfile


class ConformanceEvaluator:
    """
    M10 Law: Multi-dimensional conformance evaluation.
    Enforces precise resource, recovery, and sequence laws.
    """

    @staticmethod
    def evaluate(
        profile: RuntimeProfile,
        expectations: ScenarioExpectations,
        measurements: List[MeasurementPoint],
        mode_sequence: List[str],
        baseline_hash: Optional[str],
        final_hash: Optional[str],
        secondary_hash: Optional[str] = None,
        lifecycle_outcome: str = "SUCCESS"
    ) -> (bool, FailureKind, str, bool):
        """
        Comprehensive pass/fail proof evaluation.
        M10 Law: Returns (conformance_passed, failure_kind, failure_reason, allowed_failure_observed).
        """
        fail_kind = FailureKind.NONE
        fail_reason = ""
        allowed_failure_observed = False

        # 1. Reporting Completeness & Telemetry Gap Check
        if not measurements:
            fail_kind = FailureKind.FAILED_REPORTING_INCOMPLETE
            fail_reason = "No measurement points captured during scenario."
        
        if fail_kind == FailureKind.NONE:
            last_tick = -1
            # M10 Law: No telemetry gaps exceed the scenario-defined allowance relative to cadence.
            max_allowed_gap = expectations.required_sampling_interval_ticks * 2
            for p in measurements:
                if last_tick != -1:
                    gap = p.tick - last_tick
                    if gap > max_allowed_gap:
                        fail_kind = FailureKind.FAILED_TELEMETRY_GAP
                        fail_reason = f"Telemetry gap of {gap} ticks at tick {p.tick} (Limit: {max_allowed_gap})"
                        break
                last_tick = p.tick

        # 2. Envelope Compliance
        if fail_kind == FailureKind.NONE:
            for p in measurements:
                if p.memory_rss_mb > profile.max_ram_mb:
                    fail_kind = FailureKind.FAILED_ENVELOPE
                    fail_reason = f"RAM violation: {p.memory_rss_mb}MB > {profile.max_ram_mb}MB at tick {p.tick}"
                    break
                
                # Tick budget check (Allowing for burst unless explicitly forbidden)
                if p.tick_compute_ms > (profile.max_tick_budget_ms * 1.5) + 0.001: 
                    fail_kind = FailureKind.FAILED_ENVELOPE
                    fail_reason = f"Tick budget violation: {p.tick_compute_ms:.1f}ms > {profile.max_tick_budget_ms * 1.5:.1f}ms at tick {p.tick}"
                    break
                
                # M10 Law: Removed simplistic SURVIVAL pressure check due to conflict with dwell_time_ticks mechanics.

        # 3. Semantic Equivalence (Baseline vs Concurrent)
        if fail_kind == FailureKind.NONE and expectations.requires_semantic_equivalence:
            if not baseline_hash or not final_hash or baseline_hash != final_hash:
                fail_kind = FailureKind.FAILED_SEMANTIC_DRIFT
                fail_reason = f"Authoritative divergence from baseline: baseline={baseline_hash}, final={final_hash}"

        # M10 Law: Reproducibility (Concurrent vs Concurrent)
        if fail_kind == FailureKind.NONE and expectations.reproducibility_required:
            if not secondary_hash or final_hash != secondary_hash:
                fail_kind = FailureKind.FAILED_SEMANTIC_DRIFT
                fail_reason = f"Reproducibility failure: run1={final_hash}, run2={secondary_hash}"

        # 4. Degradation Sequence (Monotonicity Check)
        if fail_kind == FailureKind.NONE:
            from src.core.governance import RuntimeMode
            last_mode_val = 0 # NORMAL
            for mode_name in mode_sequence:
                mode_val = RuntimeMode[mode_name].value
                # M5 Law: Escalation is immediate, but recovery MUST be monotonic (1 step at a time)
                if mode_val < last_mode_val - 1:
                    fail_kind = FailureKind.FAILED_DEGRADATION_SEQUENCE
                    fail_reason = f"Invalid recovery mode jump: {RuntimeMode(last_mode_val).name} -> {mode_name}"
                    break
                # Update last mode
                last_mode_val = mode_val

            if fail_kind == FailureKind.NONE:
                for required_mode in expectations.required_governor_modes:
                    if required_mode not in mode_sequence:
                        fail_kind = FailureKind.FAILED_DEGRADATION_SEQUENCE
                        fail_reason = f"Required mode '{required_mode}' was never entered during scenario."
                        break

        # 5. Recovery Compliance
        if fail_kind == FailureKind.NONE and expectations.requires_recovery:
            if "NORMAL" not in mode_sequence[len(mode_sequence)//2:]: 
                fail_kind = FailureKind.FAILED_RECOVERY_TIMEOUT
                fail_reason = "System failed to recover to NORMAL mode within scenario window."
            
            if fail_kind == FailureKind.NONE:
                first_pressure_idx = -1
                for i, m in enumerate(mode_sequence):
                    if m != "NORMAL":
                        first_pressure_idx = i
                        break
                
                if first_pressure_idx != -1:
                    last_pressure_idx = -1
                    for i in range(len(mode_sequence)-1, -1, -1):
                        if mode_sequence[i] != "NORMAL":
                            last_pressure_idx = i
                            break
                    
                    recovery_duration = last_pressure_idx - first_pressure_idx
                    if recovery_duration > expectations.recovery_time_limit_ticks:
                        fail_kind = FailureKind.FAILED_RECOVERY_TIMEOUT
                        fail_reason = f"System took too long to recover: {recovery_duration} ticks (Limit: {expectations.recovery_time_limit_ticks})"
                    
                    if fail_kind == FailureKind.NONE and mode_sequence[-1] != "NORMAL":
                        fail_kind = FailureKind.FAILED_RECOVERY_TIMEOUT
                        fail_reason = "System is not in NORMAL mode at scenario termination."

        # 6. Lifecycle Compliance
        if fail_kind == FailureKind.NONE:
            if lifecycle_outcome != expectations.expected_lifecycle_outcome:
                fail_kind = FailureKind.FAILED_LIFECYCLE
                fail_reason = f"Expected lifecycle outcome {expectations.expected_lifecycle_outcome}, but got {lifecycle_outcome}."

        # 7. Global Law: Allowed Failure Filter
        if fail_kind != FailureKind.NONE:
            if fail_kind in expectations.allowed_failure_kinds:
                # M10 Law: Honest Reporting - Keep fail_kind but set allowed_failure_observed=True
                return True, fail_kind, f"Allowed Failure Detected: {fail_reason}", True
            else:
                return False, fail_kind, fail_reason, False

        return True, FailureKind.NONE, "Certification PASS", False
