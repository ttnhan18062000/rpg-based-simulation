from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.reporting.run_report import RunReportGenerator
from src.observability.anomaly.rules import (
    Anomaly, HardLawViolationRule, NavigationStuckRule,
    QuestStalledRule, CombatNeverEndsRule, ResourceNodeCrowdingRule
)
from src.observability.anomaly.rules_engine import RuleEngine

logger = logging.getLogger(__name__)

class AnalysisContext(BaseModel):
    """
    Immutable input container representing the complete loaded context of a simulation run.
    """
    run_id: str
    run_manifest: RunManifest
    events: List[SimulationEvent] = Field(default_factory=list)
    metric_windows: List[MetricWindowRecord] = Field(default_factory=list)
    hard_law_violations: List[Dict[str, Any]] = Field(default_factory=list)
    observability_mode: str
    scenario_type: str
    rule_config: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }

class AnalysisResult(BaseModel):
    """
    Structured outcome model for pipeline executions.
    """
    run_id: str
    status: str  # "COMPLETED", "FAILED"
    anomaly_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    health_score: float = 100.0
    output_paths: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

class AnalysisInputLoader:
    """
    Orchestrates the loading, parsing, and validation of simulation run artifacts.
    """
    def __init__(self, repo: Optional[RunArtifactRepository] = None) -> None:
        self.repo = repo or RunArtifactRepository()

    def load(self, run_id: str, allow_partial: bool = False) -> AnalysisContext:
        """
        Loads standard artifacts from the run directory.
        Raises FileNotFoundError if the run directory or manifest is missing.
        Raises ValueError if the run is incomplete and allow_partial is False.
        """
        manifest = self.repo.read_manifest(run_id)
        
        # Enforce partial run protection
        if manifest.status != "COMPLETED" and not allow_partial:
            raise ValueError(
                f"Cannot analyze incomplete run '{run_id}' with status '{manifest.status}'. "
                "Provide allow_partial=True to proceed."
            )

        events: List[SimulationEvent] = []
        events_path = self.repo.resolve_path(run_id, "events")
        if os.path.exists(events_path):
            try:
                with open(events_path, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                events.append(SimulationEvent.model_validate_json(line))
                            except Exception as e:
                                logger.error(f"Error parsing event line {line_idx}: {e}")
            except Exception as e:
                logger.error(f"Error reading event log: {e}")

        metric_windows: List[MetricWindowRecord] = []
        metrics_path = os.path.join(self.repo.base_dir, run_id, "metric_windows.jsonl")
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                metric_windows.append(MetricWindowRecord.model_validate_json(line))
                            except Exception as e:
                                logger.error(f"Error parsing metric window line {line_idx}: {e}")
            except Exception as e:
                logger.error(f"Error reading metric windows: {e}")

        hard_law_violations: List[Dict[str, Any]] = []
        violations_path = self.repo.resolve_path(run_id, "violations")
        if os.path.exists(violations_path):
            try:
                with open(violations_path, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                hard_law_violations.append(json.loads(line))
                            except Exception as e:
                                logger.error(f"Error parsing violation line {line_idx}: {e}")
            except Exception as e:
                logger.error(f"Error reading violations log: {e}")

        return AnalysisContext(
            run_id=run_id,
            run_manifest=manifest,
            events=events,
            metric_windows=metric_windows,
            hard_law_violations=hard_law_violations,
            observability_mode=manifest.observability_mode,
            scenario_type=manifest.scenario_type,
            rule_config={}
        )

class BaseAnalyzer:
    """
    Interface for structured post-run analyzers.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        raise NotImplementedError

class HardLawAnalyzer(BaseAnalyzer):
    """
    Analyzes hard law violations logged during execution.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        rule = HardLawViolationRule()
        return rule.evaluate(context.events)

class BasicMovementAnalyzer(BaseAnalyzer):
    """
    Analyzes navigation, movement blocks, and combat infinite loops.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        stuck_rule = NavigationStuckRule(tick_threshold=50)
        combat_rule = CombatNeverEndsRule(tick_threshold=40)
        
        anomalies = []
        anomalies.extend(stuck_rule.evaluate(context.events))
        anomalies.extend(combat_rule.evaluate(context.events))
        return anomalies

class BasicEconomyAnalyzer(BaseAnalyzer):
    """
    Analyzes economic transaction anomalies and resource node crowding.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        crowding_rule = ResourceNodeCrowdingRule(entity_limit=4)
        return crowding_rule.evaluate(context.events)

class BasicQuestAnalyzer(BaseAnalyzer):
    """
    Analyzes stalled quests or completion rate warnings.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        quest_rule = QuestStalledRule(tick_threshold=100)
        return quest_rule.evaluate(context.events)

class BasicRuntimeAnalyzer(BaseAnalyzer):
    """
    Scans persistent rolling metric windows for pressure warnings and leaks.
    """
    def analyze(self, context: AnalysisContext) -> List[Anomaly]:
        anomalies = []
        for w in context.metric_windows:
            # High CPU average compute > 50ms
            if w.tick_compute_ms_avg > 50.0:
                anomalies.append(Anomaly(
                    rule_name="HighCPULatencyRule",
                    severity="WARNING",
                    tick_detected=w.window_end_tick,
                    message=f"High CPU latency: average {w.tick_compute_ms_avg:.2f} ms exceeds 50ms limit",
                    context={"tick_compute_ms_avg": w.tick_compute_ms_avg}
                ))
            # Memory leak > 2GB
            if w.memory_rss_bytes_max > 2 * 1024 * 1024 * 1024:
                anomalies.append(Anomaly(
                    rule_name="MemoryRSSLeakRule",
                    severity="WARNING",
                    tick_detected=w.window_end_tick,
                    message=f"Excessive memory footprint: max RSS {w.memory_rss_bytes_max / (1024*1024):.2f} MB exceeds 2GB limit",
                    context={"memory_rss_bytes_max": w.memory_rss_bytes_max}
                ))
            # High queue utilization > 80%
            if w.queue_utilization_avg > 0.8:
                anomalies.append(Anomaly(
                    rule_name="HighQueueSaturationRule",
                    severity="WARNING",
                    tick_detected=w.window_end_tick,
                    message=f"High queue saturation: average {w.queue_utilization_avg * 100:.1f}% exceeds 80%",
                    context={"queue_utilization_avg": w.queue_utilization_avg}
                ))
        return anomalies

class AnalyzerRegistry:
    """
    Manages extensible analyzer registration and stable ordered execution.
    """
    def __init__(self) -> None:
        self._analyzers: List[BaseAnalyzer] = [
            HardLawAnalyzer(),
            BasicMovementAnalyzer(),
            BasicEconomyAnalyzer(),
            BasicQuestAnalyzer(),
            BasicRuntimeAnalyzer()
        ]

    def register(self, analyzer: BaseAnalyzer) -> None:
        self._analyzers.append(analyzer)

    def run_all(self, context: AnalysisContext) -> tuple[List[Anomaly], List[str]]:
        """
        Executes registered analyzers in order, catching errors gracefully.
        """
        anomalies: List[Anomaly] = []
        errors: List[str] = []

        for analyzer in self._analyzers:
            try:
                anomalies.extend(analyzer.analyze(context))
            except Exception as e:
                err_msg = f"Analyzer {analyzer.__class__.__name__} failed: {e}"
                logger.error(err_msg)
                errors.append(err_msg)

        return anomalies, errors

class AnalysisPipeline:
    """
    Central orchestrator managing loading, executing diagnostic analyzers,
    saving structured outcomes, and generating human-friendly markdown reports.
    """
    def __init__(
        self,
        loader: Optional[AnalysisInputLoader] = None,
        registry: Optional[AnalyzerRegistry] = None,
        repo: Optional[RunArtifactRepository] = None,
        rule_engine: Optional[RuleEngine] = None
    ) -> None:
        self.repo = repo or RunArtifactRepository()
        self.loader = loader or AnalysisInputLoader(self.repo)
        self.registry = registry or AnalyzerRegistry()
        self.rule_engine = rule_engine or RuleEngine()

    def run(self, run_id: str, allow_partial: bool = False) -> AnalysisResult:
        """
        Runs the full post-simulation diagnostic analysis pipeline.
        """
        errors: List[str] = []
        
        try:
            # 1. Load run context
            context = self.loader.load(run_id, allow_partial=allow_partial)
        except Exception as e:
            err_msg = f"Failed loading run {run_id}: {e}"
            logger.error(err_msg)
            return AnalysisResult(
                run_id=run_id,
                status="FAILED",
                errors=[err_msg]
            )

        # 2. Run registry analyzers
        anomalies, analyzer_errors = self.registry.run_all(context)
        errors.extend(analyzer_errors)

        # Run RuleEngine and Triage/Clustering
        rule_results = []
        clusters = []
        try:
            config_path = os.path.join("config", "observability", "rules_core.json")
            self.rule_engine.load_config(config_path)
            rule_results = self.rule_engine.evaluate_all(context)
            
            from src.observability.anomaly.triage import EvidenceBuilder, TriageEngine
            all_anomalies = []
            
            for res in rule_results:
                if res.status == "ERROR" and res.error_message:
                    errors.append(res.error_message)
                for rec in res.anomalies:
                    # Enrich anomalies with evidence context
                    try:
                        rec.evidence = EvidenceBuilder.build_evidence(rec, context)
                    except Exception as e:
                        logger.error(f"Failed to build evidence for anomaly {rec.rule_id}: {e}")
                    
                    all_anomalies.append(rec)
                    
                    # Map to legacy Anomaly to include in summaries
                    legacy_a = Anomaly(
                        anomaly_id=rec.anomaly_id,
                        rule_name=rec.rule_id,
                        severity=rec.severity,
                        entity_id=rec.affected_entity_ids[0] if rec.affected_entity_ids else None,
                        tick_detected=rec.tick_start,
                        message=rec.message,
                        context={
                            "domain": rec.domain,
                            "tick_end": rec.tick_end,
                            "evidence": rec.evidence,
                            "suggested_causes": rec.suggested_causes,
                            "affected_quest_ids": rec.affected_quest_ids,
                            "affected_region_ids": rec.affected_region_ids,
                            "affected_resource_ids": rec.affected_resource_ids
                        }
                    )
                    anomalies.append(legacy_a)
            
            # Deterministic Spacetime Triage Clustering
            try:
                clusters = TriageEngine.cluster_anomalies(all_anomalies)
            except Exception as e:
                logger.error(f"Clustering engine failed: {e}")
                errors.append(f"Clustering engine failed: {e}")
        except Exception as e:
            errors.append(f"RuleEngine execution failed: {e}")

        # Deduplicate anomalies to prevent double-counting between legacy and new rules
        unique_anomalies = []
        seen = set()
        for a in anomalies:
            norm_msg = a.message.lower().replace("hard law violation detected:", "").replace("invariant violation logged:", "").strip()
            key = (a.tick_detected, a.entity_id, norm_msg)
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(a)
        anomalies = unique_anomalies

        # Count severities
        critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")
        warning_count = sum(1 for a in anomalies if a.severity == "WARNING")
        error_count = sum(1 for a in anomalies if a.severity == "ERROR")

        # 3. Compute Health Score
        health_score = 100.0 - (critical_count * 40.0) - (error_count * 15.0) - (warning_count * 5.0)
        health_score = max(0.0, health_score)

        # Ensure run directory exists
        run_dir = os.path.join(self.repo.base_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        # 4. Save structured anomalies JSON
        json_path = self.repo.resolve_path(run_id, "anomalies")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([a.model_dump() for a in anomalies], f, indent=2)
        except Exception as e:
            errors.append(f"Failed saving anomalies.json: {e}")

        # 5. Save human-friendly Markdown anomaly summary
        md_summary_path = os.path.join(run_dir, "anomaly_summary.md")
        try:
            # Emulates the PostRunAnomalyAnalyzer style or invokes it
            from src.observability.anomaly.post_run_analyzer import PostRunAnomalyAnalyzer
            PostRunAnomalyAnalyzer(rules=[]).write_markdown_summary(md_summary_path, anomalies)
        except Exception as e:
            errors.append(f"Failed saving anomaly_summary.md: {e}")

        # 6. Generate run report via RunReportGenerator
        try:
            # Reconstruct shutdown result context if possible
            class SyntheticShutdownResult:
                def __init__(self, manifest: RunManifest, health_score: float) -> None:
                    self.final_tick = manifest.ticks_completed
                    self.final_hash = "DETERMINISTIC"
                    self.overall_outcome = "PARTIAL_SUCCESS" if manifest.status != "COMPLETED" else "COMPLETED"

            shutdown_result = SyntheticShutdownResult(context.run_manifest, health_score)
            RunReportGenerator.generate(
                run_dir,
                shutdown_result=shutdown_result,
                rule_results=rule_results,
                clusters=clusters,
                anomalies=anomalies
            )
        except Exception as e:
            errors.append(f"Failed generating run report: {e}")

        # 7. Update manifest status to ANALYZED
        try:
            self.repo.update_manifest(run_id, status="ANALYZED")
        except Exception as e:
            errors.append(f"Failed updating manifest status: {e}")

        status = "FAILED" if errors else "COMPLETED"
        output_paths = {
            "anomalies": json_path,
            "anomaly_summary": md_summary_path,
            "report_json": self.repo.resolve_path(run_id, "report_json"),
            "report_md": self.repo.resolve_path(run_id, "report_md")
        }

        # If partial-run, let's modify the report markdown header to include the "PARTIAL REPORT" warning
        if context.run_manifest.status != "COMPLETED":
            report_md_path = self.repo.resolve_path(run_id, "report_md")
            if os.path.exists(report_md_path):
                try:
                    with open(report_md_path, "r", encoding="utf-8") as f:
                        report_content = f.read()
                    
                    # Prepend CAUTION block indicating a partial report to prevent false confidence
                    partial_warning = (
                        "> [!CAUTION]\n"
                        "> **PARTIAL RUN ANALYSIS**\n"
                        f"> This run was not completed successfully (Manifest status: {context.run_manifest.status}). "
                        "The report metrics are partial and should not be relied upon for final behavioral validation.\n\n"
                    )
                    
                    # Insert after the main title
                    lines = report_content.split("\n")
                    if lines and lines[0].startswith("# "):
                        new_content = lines[0] + "\n\n" + partial_warning + "\n".join(lines[1:])
                    else:
                        new_content = partial_warning + report_content
                        
                    with open(report_md_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                except Exception as e:
                    logger.error(f"Failed to prepend partial run caution block: {e}")

        return AnalysisResult(
            run_id=run_id,
            status=status,
            anomaly_count=len(anomalies),
            critical_count=critical_count,
            warning_count=warning_count,
            health_score=health_score,
            output_paths=output_paths,
            errors=errors
        )
