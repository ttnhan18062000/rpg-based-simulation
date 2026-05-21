"""
UnderstandingPipeline — Phase 8 post-run orchestrator.

Runs all Phase 8 subsystems in sequence against a completed simulation run:
  1. Domain Analyzer Registry (M42)
  2. Expectation Pack evaluation (M43)
  3. Root-Cause Hypothesis Engine (M44)
  4. Balance Diagnosis Engine (M45)
  5. Story Detector (M46)
  6. Review Store (M47, read-only)
  7. Quality Reporter (M48, optional)

All processing is post-run only. The pipeline never touches the engine tick path.
"""
from __future__ import annotations
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import DomainAnalyzerRegistry, DomainAnalysisResult
from src.observability.understanding.expectations.loader import ExpectationPackLoader
from src.observability.understanding.rootcause.engine import RootCauseEngine, RootCauseEngineResult
from src.observability.understanding.balance.engine import BalanceDiagnosisEngine
from src.observability.understanding.balance.models import ScenarioBalanceSummary
from src.observability.understanding.stories.detector import StoryDetector
from src.observability.understanding.stories.models import StoryCandidate
from src.observability.understanding.review.store import ReviewStore
from src.observability.understanding.review.models import FindingReview
from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import Anomaly

logger = logging.getLogger(__name__)


@dataclass
class UnderstandingReport:
    """Aggregated output from the full Phase 8 understanding pipeline."""
    run_id: str
    scenario_type: str
    domain_results: List[DomainAnalysisResult] = field(default_factory=list)
    root_cause_result: Optional[RootCauseEngineResult] = None
    balance_summary: Optional[ScenarioBalanceSummary] = None
    story_candidates: List[StoryCandidate] = field(default_factory=list)
    existing_reviews: List[FindingReview] = field(default_factory=list)
    expectation_violations: List[Dict[str, Any]] = field(default_factory=list)
    pipeline_runtime_ms: float = 0.0
    errors: List[str] = field(default_factory=list)

    def total_domain_findings(self) -> int:
        return sum(len(r.findings) for r in self.domain_results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_type": self.scenario_type,
            "pipeline_runtime_ms": round(self.pipeline_runtime_ms, 2),
            "errors": self.errors,
            "domain_results": [r.to_dict() for r in self.domain_results],
            "root_cause": self.root_cause_result.to_dict() if self.root_cause_result else {},
            "balance_summary": self.balance_summary.to_dict() if self.balance_summary else {},
            "story_candidates": [s.to_dict() for s in self.story_candidates],
            "existing_reviews_count": len(self.existing_reviews),
            "expectation_violations": self.expectation_violations,
            "total_domain_findings": self.total_domain_findings(),
        }


class UnderstandingPipeline:
    """
    Orchestrates all Phase 8 understanding subsystems post-run.

    Typical usage:
        pipeline = UnderstandingPipeline()
        report = pipeline.run(
            run_dir="data/runs/my-run-001",
            scenario_type="resource_economy",
            events=events,
            anomalies=anomalies,
        )
    """

    def __init__(
        self,
        domain_registry: Optional[DomainAnalyzerRegistry] = None,
        root_cause_engine: Optional[RootCauseEngine] = None,
        balance_engine: Optional[BalanceDiagnosisEngine] = None,
        story_detector: Optional[StoryDetector] = None,
        expectation_loader: Optional[ExpectationPackLoader] = None,
    ) -> None:
        self._domain_registry = domain_registry or DomainAnalyzerRegistry.default()
        self._root_cause_engine = root_cause_engine or RootCauseEngine()
        self._balance_engine = balance_engine or BalanceDiagnosisEngine()
        self._story_detector = story_detector or StoryDetector()
        self._expectation_loader = expectation_loader or ExpectationPackLoader()

    def run(
        self,
        run_dir: str,
        scenario_type: str,
        events: Optional[List[SimulationEvent]] = None,
        anomalies: Optional[List[Anomaly]] = None,
        run_id: Optional[str] = None,
    ) -> UnderstandingReport:
        """
        Run the full Phase 8 pipeline against a completed simulation run.

        Args:
            run_dir: path to the run artifact directory
            scenario_type: scenario type identifier
            events: pre-loaded events (or None to load from run_dir)
            anomalies: pre-loaded anomalies (or None to load from run_dir)
            run_id: run identifier (defaults to basename of run_dir)
        """
        t0 = time.perf_counter_ns()
        run_id = run_id or os.path.basename(run_dir)

        if events is None:
            events = self._load_events(run_dir)
        if anomalies is None:
            anomalies = self._load_anomalies(run_dir)

        # Load expectation pack
        try:
            pack = self._expectation_loader.load(scenario_type)
        except Exception as e:
            logger.warning(f"Could not load expectation pack for '{scenario_type}': {e}. Using default.")
            from src.observability.understanding.expectations.models import ScenarioExpectationPack
            pack = ScenarioExpectationPack.default()

        ctx = AnalysisContext(
            run_id=run_id,
            scenario_type=scenario_type,
            events=events,
            anomalies=anomalies,
            expectation_pack=pack,
            run_dir=run_dir,
        )

        report = UnderstandingReport(run_id=run_id, scenario_type=scenario_type)
        errors: List[str] = []

        # ── Step 1: Domain Analyzers ──────────────────────────────────────────
        try:
            report.domain_results = self._domain_registry.run_all(ctx)
        except Exception as e:
            errors.append(f"Domain registry failed: {e}")
            logger.error(f"UnderstandingPipeline domain registry error: {e}", exc_info=True)

        # ── Step 2: Expectation Pack Violations ───────────────────────────────
        try:
            report.expectation_violations = self._evaluate_expectations(ctx)
        except Exception as e:
            errors.append(f"Expectation pack evaluation failed: {e}")

        # ── Step 3: Root-Cause Hypotheses ─────────────────────────────────────
        try:
            report.root_cause_result = self._root_cause_engine.run(ctx)
        except Exception as e:
            errors.append(f"Root-cause engine failed: {e}")
            logger.error(f"UnderstandingPipeline root-cause engine error: {e}", exc_info=True)

        # ── Step 4: Balance Diagnosis ─────────────────────────────────────────
        try:
            report.balance_summary = self._balance_engine.diagnose(ctx)
        except Exception as e:
            errors.append(f"Balance engine failed: {e}")
            logger.error(f"UnderstandingPipeline balance engine error: {e}", exc_info=True)

        # ── Step 5: Story Detection ───────────────────────────────────────────
        try:
            report.story_candidates = self._story_detector.detect(ctx)
        except Exception as e:
            errors.append(f"Story detector failed: {e}")
            logger.error(f"UnderstandingPipeline story detector error: {e}", exc_info=True)

        # ── Step 6: Load Existing Reviews (read-only) ─────────────────────────
        try:
            store = ReviewStore(run_dir)
            report.existing_reviews = store.list_all()
        except Exception as e:
            errors.append(f"Review store load failed: {e}")

        report.errors = errors
        report.pipeline_runtime_ms = (time.perf_counter_ns() - t0) / 1e6

        # Persist Phase 8 output
        try:
            self._save_report(run_dir, report)
        except Exception as e:
            logger.error(f"UnderstandingPipeline failed to save report: {e}", exc_info=True)

        return report

    def _evaluate_expectations(self, ctx: AnalysisContext) -> List[Dict[str, Any]]:
        """Evaluate expectation pack rules against available metrics."""
        if ctx.expectation_pack is None:
            return []

        violations = []
        pack = ctx.expectation_pack

        # Simple metric extraction from context
        metrics = {
            "hard_law_violations_count": float(len(ctx.anomalies_by_severity("CRITICAL"))),
            "economy_events_count": float(len(ctx.events_by_category("economy"))),
            "combat_events_count": float(len(ctx.events_by_category("combat"))),
            "quest_events_count": float(len(ctx.events_by_category("quest"))),
            "movement_events_count": float(len(ctx.events_by_category("movement"))),
            "crowding_anomalies_count": float(len(ctx.anomalies_by_rule("ResourceNodeCrowdingRule"))),
            "combat_never_ends_anomalies_count": float(len(ctx.anomalies_by_rule("CombatNeverEndsRule"))),
        }

        for rule in pack.all_rules():
            if pack.is_metric_ignored(rule.metric_key):
                continue
            if rule.metric_key not in metrics:
                continue  # Skip rules for metrics not measurable here
            measured = metrics[rule.metric_key]
            if not rule.evaluate(measured):
                violations.append({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "metric_key": rule.metric_key,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "measured_value": measured,
                    "severity": rule.severity_if_violated,
                })
        return violations

    def _save_report(self, run_dir: str, report: UnderstandingReport) -> None:
        os.makedirs(run_dir, exist_ok=True)
        out_path = os.path.join(run_dir, "understanding_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"UnderstandingPipeline saved report to {out_path}")

        md_path = os.path.join(run_dir, "understanding_report.md")
        self._write_markdown(md_path, report)
        logger.info(f"UnderstandingPipeline saved markdown to {md_path}")

    def _write_markdown(self, filepath: str, report: UnderstandingReport) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Phase 8 Understanding Report — {report.run_id}\n\n")
            f.write(f"> Scenario: `{report.scenario_type}` | Runtime: {report.pipeline_runtime_ms:.1f}ms\n\n")

            if report.errors:
                f.write("## ⚠️ Pipeline Errors\n\n")
                for err in report.errors:
                    f.write(f"- {err}\n")
                f.write("\n")

            # Domain Findings
            all_findings = [
                (r.domain_id, f)
                for r in report.domain_results
                for f in r.findings
            ]
            f.write(f"## 🔍 Domain Findings ({len(all_findings)} total)\n\n")
            if all_findings:
                for domain_id, finding in all_findings:
                    emoji = "🟥" if finding.severity == "CRITICAL" else "🟧" if finding.severity == "ERROR" else "🟨"
                    f.write(f"### {emoji} [{domain_id.upper()}] {finding.title}\n\n")
                    f.write(f"> {finding.summary}\n\n")
                    if finding.evidence:
                        f.write("**Evidence:**\n")
                        for e in finding.evidence:
                            f.write(f"- {e}\n")
                    if finding.suspected_causes:
                        f.write("\n**Suspected Causes:**\n")
                        for c in finding.suspected_causes:
                            f.write(f"- {c}\n")
                    if finding.recommended_next_steps:
                        f.write("\n**Next Steps:**\n")
                        for s in finding.recommended_next_steps:
                            f.write(f"- {s}\n")
                    f.write("\n")
            else:
                f.write("> No domain findings. All analyzed domains passed.\n\n")

            # Expectation Violations
            if report.expectation_violations:
                f.write(f"## 📋 Expectation Pack Violations ({len(report.expectation_violations)})\n\n")
                for v in report.expectation_violations:
                    emoji = "🟥" if v["severity"] == "CRITICAL" else "🟧" if v["severity"] == "ERROR" else "🟨"
                    f.write(
                        f"- {emoji} **{v['rule_id']}**: `{v['metric_key']}` "
                        f"should be {v['operator']} {v['threshold']} "
                        f"but was `{v['measured_value']}`\n"
                    )
                f.write("\n")

            # Root-cause hypotheses
            if report.root_cause_result and report.root_cause_result.hypotheses:
                top = report.root_cause_result.top_by_confidence(5)
                f.write(f"## 🧠 Root-Cause Hypotheses (top {len(top)})\n\n")
                for h in top:
                    conf_emoji = "🔴" if h.confidence.value == "HIGH" else "🟡" if h.confidence.value == "MEDIUM" else "⚪"
                    f.write(f"### {conf_emoji} {h.title} ({h.confidence.value})\n\n")
                    if h.supporting_evidence:
                        f.write("**Supporting Evidence:**\n")
                        for e in h.supporting_evidence:
                            f.write(f"- {e}\n")
                    if h.recommended_checks:
                        f.write("\n**Recommended Checks:**\n")
                        for c in h.recommended_checks:
                            f.write(f"- {c}\n")
                    f.write("\n")

            # Balance
            if report.balance_summary and report.balance_summary.findings:
                f.write(f"## ⚖️ Balance Diagnosis ({len(report.balance_summary.findings)} findings)\n\n")
                for bf in report.balance_summary.findings:
                    f.write(f"- **[{bf.dimension.value}]** {bf.summary}\n")
                f.write("\n")

            # Stories
            if report.story_candidates:
                f.write(f"## 📖 Emergent Stories ({len(report.story_candidates)} detected)\n\n")
                for s in report.story_candidates[:5]:
                    f.write(f"### ✨ {s.title}\n\n")
                    f.write(f"> {s.summary}\n\n")
                f.write("\n")

            # Reviews
            if report.existing_reviews:
                f.write(f"## 🏷️ Existing Reviews ({len(report.existing_reviews)} findings reviewed)\n\n")
                from collections import Counter
                label_counts = Counter(r.label.value for r in report.existing_reviews)
                for label, count in label_counts.most_common():
                    f.write(f"- `{label}`: {count}\n")
                f.write("\n")

    def _load_events(self, run_dir: str) -> List[SimulationEvent]:
        """Load SimulationEvents from run_dir/simulation_events.jsonl."""
        events = []
        path = os.path.join(run_dir, "simulation_events.jsonl")
        if not os.path.exists(path):
            return events
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(SimulationEvent.model_validate_json(line))
                        except Exception as e:
                            logger.warning(f"Skipping bad event line: {e}")
        except Exception as e:
            logger.error(f"Failed loading events from {path}: {e}")
        return events

    def _load_anomalies(self, run_dir: str) -> List[Anomaly]:
        """Load Anomaly objects from run_dir/anomalies.json."""
        anomalies = []
        path = os.path.join(run_dir, "anomalies.json")
        if not os.path.exists(path):
            return anomalies
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                try:
                    anomalies.append(Anomaly(**item))
                except Exception as e:
                    logger.warning(f"Skipping bad anomaly entry: {e}")
        except Exception as e:
            logger.error(f"Failed loading anomalies from {path}: {e}")
        return anomalies
