from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class FailureKind(str, Enum):
    """
    M10 Law: Standardized FAILED_* taxonomy.
    SENTINEL: 'NONE' is the sole non-failure identifier, exempt from FAILED_* prefix.
    """
    NONE = "none"
    FAILED_ENVELOPE = "failed_envelope"
    FAILED_DEGRADATION_SEQUENCE = "failed_degradation_sequence"
    FAILED_RECOVERY_TIMEOUT = "failed_recovery_timeout"
    FAILED_SEMANTIC_DRIFT = "failed_semantic_drift"
    FAILED_TELEMETRY_GAP = "failed_telemetry_gap"
    FAILED_REPORTING_INCOMPLETE = "failed_reporting_incomplete"
    FAILED_INVALID_SCENARIO = "failed_invalid_scenario"
    FAILED_ENVIRONMENT_MISMATCH = "failed_environment_mismatch"
    FAILED_REPLAY_PERSISTENCE = "failed_replay_persistence"
    FAILED_MANIFEST_INCOMPLETE = "failed_manifest_incomplete"
    FAILED_MISSING_SCENARIO = "failed_missing_scenario"
    FAILED_WORKER_PROPAGATION = "failed_worker_propagation"
    FAILED_LIFECYCLE = "failed_lifecycle"


class HardwareClass(str, Enum):
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_C = "class_c"


@dataclass(frozen=True, slots=True)
class MeasurementPoint:
    """M10 Law: Closed, bounded telemetry point."""
    tick: int
    mode: str
    memory_rss_mb: float
    memory_trend_mb_per_tick: float  # Trending signal
    tick_compute_ms: float
    tick_compute_ms_avg: float       # Trending signal
    work_debt: int
    worker_utilization: float        # Explicit worker pressure
    queue_utilization: float         # Explicit queue pressure
    replay_pressure: float
    active_workers: int
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class ScenarioExpectations:
    """M10 Law: Explicit requirements for a scenario pass."""
    required_governor_modes: List[str] = field(default_factory=list)
    requires_recovery: bool = False
    requires_semantic_equivalence: bool = True
    max_recovery_ticks: int = 50
    recovery_time_limit_ticks: int = 100
    sampling_interval_ticks: int = 10
    required_sampling_interval_ticks: int = 10
    allowed_failure_kinds: List[FailureKind] = field(default_factory=lambda: [FailureKind.NONE])
    reproducibility_required: bool = True
    expected_lifecycle_outcome: str = "SUCCESS"
    shutdown_timeout_s: float = 5.0
    required_artifacts: List[str] = field(default_factory=list)
    allowed_execution_modes: List[str] = field(default_factory=lambda: ["local", "concurrent"])
    allowed_profiles: List[str] = field(default_factory=lambda: ["standard_gaming_profile"])


@dataclass(frozen=True, slots=True)
class EnvironmentCapture:
    """M10 Law: Explicit separation of host facts and classification metadata."""
    detected_facts: Dict[str, Any]
    detected_class: HardwareClass
    effective_class: HardwareClass
    override_applied: bool
    os_name: str = "linux"
    python_version: str = "3.13"


@dataclass
class CertificationResult:
    """M10 Law: The machine-readable proof artifact (Source of Truth)."""
    run_id: str
    timestamp: float
    commit_sha: str # M10 Provenance Rule
    
    # Context
    profile_name: str
    scenario_id: str
    seed: int
    
    # Environment
    environment: EnvironmentCapture
    
    # Evidence
    measurements: List[MeasurementPoint]
    baseline_hash: Optional[str]
    final_hash: Optional[str]
    governor_mode_sequence: List[str]
    
    # Outcome
    conformance_passed: bool
    allowed_failure_observed: bool = False # M10 Law: Honest Reporting Flag
    failure_kind: FailureKind = FailureKind.NONE
    failure_reason: Optional[str] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
