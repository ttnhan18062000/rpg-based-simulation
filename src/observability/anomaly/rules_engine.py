from __future__ import annotations
import os
import uuid
import json
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from src.observability.events import SimulationEvent

if TYPE_CHECKING:
    from src.observability.anomaly.pipeline import AnalysisContext

logger = logging.getLogger(__name__)

class AnomalyRecord(BaseModel):
    """
    Highly detailed structured record for detected simulation anomalies.
    """
    anomaly_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    rule_id: str
    severity: str  # "WARNING", "ERROR", "CRITICAL"
    domain: str  # "combat", "movement", "economy", "quest", "system"
    message: str
    tick_start: int
    tick_end: int
    affected_entity_ids: List[int] = Field(default_factory=list)
    affected_resource_ids: List[str] = Field(default_factory=list)
    affected_region_ids: List[str] = Field(default_factory=list)
    affected_quest_ids: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    suggested_causes: List[str] = Field(default_factory=list)

class RuleStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED_MISSING_SIGNAL = "SKIPPED_MISSING_SIGNAL"
    SKIPPED_SCENARIO_TYPE = "SKIPPED_SCENARIO_TYPE"
    ERROR = "ERROR"

class RuleResult(BaseModel):
    """
    Container for single rule evaluation outcomes.
    """
    rule_id: str
    status: RuleStatus
    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    error_message: Optional[str] = None

class RuleConfig(BaseModel):
    """
    Data-driven configuration parameters for a rule.
    """
    enabled: bool = True
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    scenario_types: List[str] = Field(default_factory=list)
    severity_override: Optional[str] = None

class BaseRule:
    """
    Formal interface for post-run simulation rules.
    """
    rule_id: str
    required_signals: List[str] = []
    valid_scenarios: List[str] = []
    domain: str = "system"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        raise NotImplementedError

# ----------------- Core Rules -----------------

class HardLawViolationDetected(BaseRule):
    rule_id = "HardLawViolationDetected"
    required_signals = ["events"]
    domain = "system"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        # Gating on scenarios if configured
        if config.scenario_types and context.scenario_type not in config.scenario_types:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)

        anomalies = []
        # Check hard_law_violations first
        for idx, violation in enumerate(context.hard_law_violations, 1):
            severity = config.severity_override or "CRITICAL"
            anomalies.append(AnomalyRecord(
                rule_id=self.rule_id,
                severity=severity,
                domain=self.domain,
                message=f"Invariant violation logged: {violation.get('message', 'Unknown breach')}",
                tick_start=violation.get("tick", 0),
                tick_end=violation.get("tick", 0),
                affected_entity_ids=[violation.get("entity_id")] if violation.get("entity_id") is not None else [],
                evidence=violation,
                suggested_causes=["Breach of authoritative regional sovereignty or sleep invariants."]
            ))

        # Check event stream for InvariantViolation events too
        for ev in context.events:
            if ev.event_category == "hard_law" or ev.event_type == "InvariantViolation":
                severity = config.severity_override or ev.severity or "CRITICAL"
                # Avoid duplicates if already logged in violations
                if not any(a.tick_start == ev.tick and a.message == f"Invariant violation logged: {ev.message}" for a in anomalies):
                    anomalies.append(AnomalyRecord(
                        rule_id=self.rule_id,
                        severity=severity,
                        domain=self.domain,
                        message=f"Invariant violation logged: {ev.message}",
                        tick_start=ev.tick,
                        tick_end=ev.tick,
                        affected_entity_ids=[ev.entity_id] if ev.entity_id is not None else [],
                        evidence=ev.payload,
                        suggested_causes=["Simulation state invariant failed regional checks."]
                    ))

        status = RuleStatus.FAILED if anomalies else RuleStatus.PASSED
        return RuleResult(rule_id=self.rule_id, status=status, anomalies=anomalies)

class NavigationStuckBasic(BaseRule):
    rule_id = "NavigationStuckBasic"
    required_signals = ["events"]
    domain = "movement"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        if config.scenario_types and context.scenario_type not in config.scenario_types:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)

        threshold = config.thresholds.get("tick_threshold", 50)
        severity = config.severity_override or "WARNING"

        anomalies = []
        entity_movements: Dict[int, List[SimulationEvent]] = {}
        for ev in context.events:
            if ev.event_type == "movement" and ev.entity_id is not None:
                entity_movements.setdefault(ev.entity_id, []).append(ev)

        for eid, m_events in entity_movements.items():
            if len(m_events) < 2:
                continue
            m_events.sort(key=lambda x: x.tick)

            consecutive_stuck_ticks = 0
            last_pos = None
            last_tick = None
            stuck_start_tick = None

            for ev in m_events:
                end_pos = ev.payload.get("end_pos") or getattr(ev, "end_pos", None)
                if last_pos is not None and last_pos == end_pos:
                    if stuck_start_tick is None:
                        stuck_start_tick = last_tick
                    consecutive_stuck_ticks += (ev.tick - last_tick)
                    if consecutive_stuck_ticks >= threshold:
                        anomalies.append(AnomalyRecord(
                            rule_id=self.rule_id,
                            severity=severity,
                            domain=self.domain,
                            message=f"Entity {eid} stuck at position {end_pos} for {consecutive_stuck_ticks} ticks",
                            tick_start=stuck_start_tick,
                            tick_end=ev.tick,
                            affected_entity_ids=[eid],
                            evidence={"position": end_pos, "duration_ticks": consecutive_stuck_ticks},
                            suggested_causes=["Pathfinding obstacles, mesh generation gaps, or movement lockups."]
                        ))
                        # Reset stuck window to avoid flooding duplicates
                        consecutive_stuck_ticks = 0
                        stuck_start_tick = None
                else:
                    consecutive_stuck_ticks = 0
                    stuck_start_tick = None
                last_pos = end_pos
                last_tick = ev.tick

        status = RuleStatus.FAILED if anomalies else RuleStatus.PASSED
        return RuleResult(rule_id=self.rule_id, status=status, anomalies=anomalies)

class QuestStalledBasic(BaseRule):
    rule_id = "QuestStalledBasic"
    required_signals = ["events"]
    domain = "quest"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        if config.scenario_types and context.scenario_type not in config.scenario_types:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)

        threshold = config.thresholds.get("tick_threshold", 100)
        severity = config.severity_override or "WARNING"

        anomalies = []
        quest_states: Dict[str, Dict[str, Any]] = {}
        for ev in context.events:
            if ev.event_category == "quest" or ev.event_type == "quest_event":
                qid = ev.payload.get("quest_id") or getattr(ev, "quest_id", None)
                status = ev.payload.get("status") or getattr(ev, "status", None)
                if not qid or not status:
                    continue

                if status == "started":
                    quest_states[qid] = {
                        "entity_id": ev.entity_id,
                        "started_tick": ev.tick,
                        "last_update_tick": ev.tick,
                        "status": "started"
                    }
                elif qid in quest_states:
                    quest_states[qid]["status"] = status
                    quest_states[qid]["last_update_tick"] = ev.tick

        final_tick = max(
            context.run_manifest.ticks_completed if context.run_manifest else 0,
            max((ev.tick for ev in context.events), default=0)
        )

        for qid, qstate in quest_states.items():
            if qstate["status"] in ("started", "progress"):
                duration = final_tick - qstate["started_tick"]
                if duration >= threshold:
                    anomalies.append(AnomalyRecord(
                        rule_id=self.rule_id,
                        severity=severity,
                        domain=self.domain,
                        message=f"Quest {qid} stalled in status {qstate['status']} for {duration} ticks",
                        tick_start=qstate["started_tick"],
                        tick_end=final_tick,
                        affected_entity_ids=[qstate["entity_id"]] if qstate["entity_id"] is not None else [],
                        affected_quest_ids=[qid],
                        evidence={"quest_id": qid, "duration_ticks": duration},
                        suggested_causes=["Unreachable target coordinates, vendor inventory deficits, or quest handler crash."]
                    ))

        status = RuleStatus.FAILED if anomalies else RuleStatus.PASSED
        return RuleResult(rule_id=self.rule_id, status=status, anomalies=anomalies)

class ResourceProductionZero(BaseRule):
    rule_id = "ResourceProductionZero"
    required_signals = ["metric_windows"]
    domain = "economy"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        # Check missing signal
        if not context.metric_windows:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_MISSING_SIGNAL)

        # Skip on unsupported scenario types
        target_scenarios = config.scenario_types or ["resource_economy", "mixed_sandbox"]
        if context.scenario_type not in target_scenarios:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)

        window_threshold = config.thresholds.get("window_threshold", 3)
        
        consecutive_zero_windows = 0
        zero_start_tick = None
        anomalies = []

        for w in context.metric_windows:
            # Check gold_total_avg as primary proxy for resource production
            if w.gold_total_avg == 0:
                if zero_start_tick is None:
                    zero_start_tick = w.window_start_tick
                consecutive_zero_windows += 1
                if consecutive_zero_windows >= window_threshold:
                    # ERROR if active workers/entities exist, WARNING otherwise
                    severity = config.severity_override
                    if severity is None:
                        severity = "ERROR" if w.active_entities_avg > 0 else "WARNING"

                    anomalies.append(AnomalyRecord(
                        rule_id=self.rule_id,
                        severity=severity,
                        domain=self.domain,
                        message=f"Economic freeze: zero resource production for {consecutive_zero_windows} consecutive windows",
                        tick_start=zero_start_tick,
                        tick_end=w.window_end_tick,
                        evidence={"consecutive_zero_windows": consecutive_zero_windows, "gold_total_avg": w.gold_total_avg},
                        suggested_causes=["Resource node exhaustions, pathfinding freezes to nodes, or trading system deadlock."]
                    ))
            else:
                consecutive_zero_windows = 0
                zero_start_tick = None

        status = RuleStatus.FAILED if anomalies else RuleStatus.PASSED
        return RuleResult(rule_id=self.rule_id, status=status, anomalies=anomalies)

class GovernorDegradedTooLong(BaseRule):
    rule_id = "GovernorDegradedTooLong"
    required_signals = ["metric_windows"]
    domain = "system"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        # Check missing signal
        if not context.metric_windows:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_MISSING_SIGNAL)

        if config.scenario_types and context.scenario_type not in config.scenario_types:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)

        window_threshold = config.thresholds.get("window_threshold", 3)
        severity = config.severity_override or "ERROR"

        consecutive_degraded_windows = 0
        degraded_start_tick = None
        anomalies = []

        for w in context.metric_windows:
            # Degraded modes are DEGRADED and SURVIVAL
            if w.governor_mode_dominant in ("DEGRADED", "SURVIVAL"):
                if degraded_start_tick is None:
                    degraded_start_tick = w.window_start_tick
                consecutive_degraded_windows += 1
                if consecutive_degraded_windows >= window_threshold:
                    anomalies.append(AnomalyRecord(
                        rule_id=self.rule_id,
                        severity=severity,
                        domain=self.domain,
                        message=f"Critical system pressure: Governor dominant mode degraded/survival for {consecutive_degraded_windows} consecutive windows",
                        tick_start=degraded_start_tick,
                        tick_end=w.window_end_tick,
                        evidence={"consecutive_degraded_windows": consecutive_degraded_windows, "governor_mode_dominant": w.governor_mode_dominant},
                        suggested_causes=["Continuous compute latency spikes, massive heap utilization, or CPU starvation."]
                    ))
            else:
                consecutive_degraded_windows = 0
                degraded_start_tick = None

        status = RuleStatus.FAILED if anomalies else RuleStatus.PASSED
        return RuleResult(rule_id=self.rule_id, status=status, anomalies=anomalies)

# ----------------- Rule Engine -----------------

class RuleRegistry:
    """
    Maintains a stable catalog of diagnostic rules.
    """
    def __init__(self) -> None:
        self._rules: List[BaseRule] = [
            HardLawViolationDetected(),
            NavigationStuckBasic(),
            QuestStalledBasic(),
            ResourceProductionZero(),
            GovernorDegradedTooLong()
        ]

    def register(self, rule: BaseRule) -> None:
        self._rules.append(rule)

    def get_rules(self) -> List[BaseRule]:
        return self._rules

class RuleEngine:
    """
    Orchestrates post-run analysis evaluation against all registered BaseRules.
    """
    def __init__(self, registry: Optional[RuleRegistry] = None) -> None:
        self.registry = registry or RuleRegistry()
        self.config: Dict[str, RuleConfig] = {}

    def load_config(self, config_path: str) -> None:
        """
        Loads rules config from file. Fallbacks to default configs if missing.
        """
        if not os.path.exists(config_path):
            logger.info(f"Rules config not found at {config_path}. Falling back to default configs.")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for rule_id, rule_data in data.items():
                try:
                    self.config[rule_id] = RuleConfig.model_validate(rule_data)
                except Exception as e:
                    logger.error(f"Failed parsing rule config for '{rule_id}': {e}")
        except Exception as e:
            logger.error(f"Error loading rule engine config file: {e}")

    def evaluate_all(self, context: AnalysisContext) -> List[RuleResult]:
        """
        Evaluates all registered rules in stable registration order.
        """
        results: List[RuleResult] = []
        for rule in self.registry.get_rules():
            # Get specific rule config or use default enabled rule config
            rule_config = self.config.get(rule.rule_id) or RuleConfig()

            if not rule_config.enabled:
                continue

            try:
                result = rule.evaluate(context, rule_config)
                results.append(result)
            except Exception as e:
                err_msg = f"Rule '{rule.rule_id}' crashed: {e}"
                logger.error(err_msg)
                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    status=RuleStatus.ERROR,
                    error_message=err_msg
                ))

        return results
