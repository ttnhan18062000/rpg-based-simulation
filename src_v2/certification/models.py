from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class FailureKind(str, Enum):
    """M9 Law: Precise failure taxonomy."""
    NONE = "none"
    FAILED_ENVELOPE = "failed_envelope"
    FAILED_DEGRADATION_ORDER = "failed_degradation_order"
    FAILED_RECOVERY = "failed_recovery"
    FAILED_SEMANTIC_DRIFT = "failed_semantic_drift"
    FAILED_REPORTING_INCOMPLETE = "failed_reporting_incomplete"
    FAILED_INVALID_SCENARIO = "failed_invalid_scenario"
    FAILED_ENVIRONMENT_MISMATCH = "failed_environment_mismatch"


class HardwareClass(str, Enum):
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_C = "class_c"


@dataclass(frozen=True, slots=True)
class MeasurementPoint:
    """M9 Law: Closed, bounded telemetry point."""
    tick: int
    mode: str
    memory_rss_mb: float
    tick_compute_ms: float
    work_debt: int
    queue_utilization: float
    replay_pressure: float
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class ScenarioExpectations:
    """Formal requirements for a scenario pass."""
    required_governor_modes: List[str] = field(default_factory=list)
    requires_recovery: bool = False
    requires_semantic_equivalence: bool = True
    max_recovery_ticks: int = 50
    sampling_interval_ticks: int = 10


@dataclass
class CertificationResult:
    """M9 Law: The machine-readable source of truth."""
    run_id: str
    timestamp: float
    
    # Context
    profile_name: str
    scenario_id: str
    seed: int
    
    # Environment
    detected_hardware_class: HardwareClass
    effective_hardware_class: HardwareClass
    hardware_class_override_applied: bool
    platform_info: Dict[str, Any]
    
    # Evidence
    measurements: List[MeasurementPoint]
    baseline_hash: Optional[str]
    final_hash: Optional[str]
    governor_mode_sequence: List[str]
    
    # Outcome
    conformance_passed: bool
    failure_kind: FailureKind
    failure_reason: Optional[str]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
