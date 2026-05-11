from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional

class ArenaStopCondition(str, Enum):
    """Predicates for scenario termination in Arena Harness."""
    WIPE = "wipe"           # One side eliminated
    TIMEOUT = "timeout"     # Max ticks reached
    STALL = "stall"         # No activity for too long
    WATCHDOG = "watchdog"   # Tick hang detected
    MANUAL = "manual"       # Explicitly stopped

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
    stop_condition: ArenaStopCondition = ArenaStopCondition.TIMEOUT
    allowed_failure_observed: bool = False # M10 Law: Honest Reporting Flag
    failure_kind: FailureKind = FailureKind.NONE
    failure_reason: Optional[str] = None
    
    # NEW: Aggregate Resource Metrics
    peak_rss_mb: float = 0.0
    total_cpu_sec: float = 0.0
    
    # NEW: Emergent Behavior Evidence (Optional for large states)
    final_state: Optional[Any] = None
    
    def to_json(self) -> str:
        import json
        from dataclasses import asdict, is_dataclass
        from enum import Enum

        def safe_asdict(obj, memo=None):
            if memo is None: memo = set()
            
            # Basic types
            if obj is None or isinstance(obj, (int, float, str, bool)):
                return obj

            if id(obj) in memo:
                return f"<CYCLE DETECTED: {type(obj).__name__}>"
            
            if is_dataclass(obj):
                memo.add(id(obj))
                res = {}
                for f in obj.__dataclass_fields__.values():
                    # M10 Law: Skip internal caches/private fields for serialization
                    if f.name.startswith("_"):
                        continue
                    val = getattr(obj, f.name)
                    res[f.name] = safe_asdict(val, memo)
                memo.remove(id(obj))
                return res
            elif isinstance(obj, dict):
                memo.add(id(obj))
                # Use str(k) to ensure keys are serializable in JSON
                res = {str(k): safe_asdict(v, memo) for k, v in obj.items()}
                memo.remove(id(obj))
                return res
            elif isinstance(obj, (list, tuple, set, frozenset)):
                memo.add(id(obj))
                res = [safe_asdict(x, memo) for x in obj]
                memo.remove(id(obj))
                return res
            elif isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, "__dict__"):
                return f"<{type(obj).__name__}>"
            return str(obj)

        try:
            # Try standard asdict first (faster)
            data = asdict(self)
        except RecursionError:
            # Fallback to safe version if depth is too great or cycle exists
            data = safe_asdict(self)

        def custom_serializer(obj):
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, (set, frozenset)):
                return sorted(list(obj))
            return str(obj)

        return json.dumps(data, default=custom_serializer, indent=2)
