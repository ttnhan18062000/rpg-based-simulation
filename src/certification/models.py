from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class EvidenceLevel(str, Enum):
    """Controls how much state evidence is captured alongside the proof bundle.

    SUMMARY (default): compact counts only. No side files written.
    COMPACT: compact counts + entity_sample (first 5 entity IDs, sorted ascending)
             + resource_snapshot (top 5 resource node IDs by quantity descending).
             No side files written.
    FULL: same summary as COMPACT + writes CanonicalStateHasher output to
          <output_dir>/state/<run_id>.final_state.canonical.json.
          Includes final_state_hash in the artifact dict.
    """
    SUMMARY = "summary"
    COMPACT = "compact"
    FULL    = "full"


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

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "mode": self.mode,
            "memory_rss_mb": self.memory_rss_mb,
            "memory_trend_mb_per_tick": self.memory_trend_mb_per_tick,
            "tick_compute_ms": self.tick_compute_ms,
            "tick_compute_ms_avg": self.tick_compute_ms_avg,
            "work_debt": self.work_debt,
            "worker_utilization": self.worker_utilization,
            "queue_utilization": self.queue_utilization,
            "replay_pressure": self.replay_pressure,
            "active_workers": self.active_workers,
            "timestamp": self.timestamp,
        }


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
    
    def _final_state_summary(self) -> "dict | None":
        """Return a compact summary of final_state using only safe getattr access.

        Uses getattr for all field access so that PoisonState-style test objects
        can verify exactly which attributes are touched. Never calls asdict(),
        vars(), or __dict__ on the state object.
        """
        state = self.final_state
        if state is None:
            return None
        entities = getattr(state, "entities", {})
        resource_nodes = getattr(state, "resource_nodes", {})
        regions = getattr(state, "regions", {})
        buildings = getattr(state, "buildings", {})
        corpses = getattr(state, "corpses", {})
        ground_items = getattr(state, "ground_items", {})
        return {
            "tick": getattr(state, "tick", None),
            "seed": getattr(state, "seed", None),
            "entity_count": len(entities),
            "resource_node_count": len(resource_nodes),
            "region_count": len(regions),
            "building_count": len(buildings),
            "corpse_count": len(corpses),
            "ground_item_count": len(ground_items),
            "final_hash": self.final_hash,
        }

    def _final_state_summary_compact(self) -> "dict | None":
        """Extends _final_state_summary() with entity_sample and resource_snapshot.

        entity_sample: first 5 entity IDs sorted ascending (as strings).
        resource_snapshot: top 5 resource node IDs by quantity descending (as strings).
        Uses getattr for all access — PoisonState-safe.
        """
        base = self._final_state_summary()
        if base is None:
            return None
        state = self.final_state
        entities = getattr(state, "entities", {})
        resource_nodes = getattr(state, "resource_nodes", {})
        base["entity_sample"] = sorted(str(eid) for eid in entities.keys())[:5]
        rn_sorted = sorted(
            resource_nodes.items(),
            key=lambda kv: getattr(kv[1], "quantity", 0),
            reverse=True,
        )
        base["resource_snapshot"] = [str(k) for k, _ in rn_sorted[:5]]
        return base

    def to_artifact_dict(
        self,
        evidence_level: "EvidenceLevel" = None,
        final_state_artifact_path: Optional[str] = None,
        final_state_hash: Optional[str] = None,
    ) -> dict:
        """Build the proof artifact dict field-by-field without calling asdict().

        Never walks final_state — always sets final_state to None in the artifact.
        Raises ValueError if required scoped metadata is missing
        (certification_contract_me.md §5 Honest Reporting Law).

        Args:
            evidence_level: Controls final_state_summary richness. Defaults to SUMMARY.
            final_state_artifact_path: Relative path to the canonical state file when FULL
                write succeeds; None otherwise. Never speculatively computed here.
            final_state_hash: SHA-256 hex of compact canonical JSON; None unless FULL succeeds.
        """
        if evidence_level is None:
            evidence_level = EvidenceLevel.SUMMARY
        if not self.profile_name:
            raise ValueError(
                "to_artifact_dict(): profile_name is required (certification_contract_me.md §5)"
            )
        if not self.scenario_id:
            raise ValueError(
                "to_artifact_dict(): scenario_id is required (certification_contract_me.md §5)"
            )
        if self.environment is None:
            raise ValueError(
                "to_artifact_dict(): environment is required (certification_contract_me.md §5)"
            )
        env = self.environment
        return {
            "schema_version": "certification_result.v1",
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
            "profile_name": self.profile_name,
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "environment": {
                "detected_hardware_class": env.detected_class.value,
                "effective_hardware_class": env.effective_class.value,
                "override_applied": env.override_applied,
                "detected_facts": env.detected_facts,
                "os_name": env.os_name,
                "python_version": env.python_version,
            },
            "measurements": [m.to_dict() for m in self.measurements],
            "baseline_hash": self.baseline_hash,
            "final_hash": self.final_hash,
            "governor_mode_sequence": self.governor_mode_sequence,
            "conformance_passed": self.conformance_passed,
            "stop_condition": self.stop_condition.value,
            "allowed_failure_observed": self.allowed_failure_observed,
            "failure_kind": self.failure_kind.value,
            "failure_reason": self.failure_reason,
            "peak_rss_mb": self.peak_rss_mb,
            "total_cpu_sec": self.total_cpu_sec,
            "final_state": None,
            "final_state_summary": (
                self._final_state_summary_compact()
                if evidence_level in (EvidenceLevel.COMPACT, EvidenceLevel.FULL)
                else self._final_state_summary()
            ),
            "final_state_artifact": final_state_artifact_path,
            "final_state_hash": final_state_hash,
        }

    def to_json(self) -> str:
        from enum import Enum

        def _default(obj):
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, (set, frozenset)):
                return sorted(list(obj))
            return str(obj)

        return json.dumps(self.to_artifact_dict(), default=_default, indent=2)
