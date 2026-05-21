"""
Integration test — UnderstandingPipeline end-to-end (Phase 8)

Validates:
- Pipeline runs without error on clean and fault-injected contexts
- All six subsystems produce output
- Report serializes to JSON and Markdown
- Pipeline runtime is tracked
- Review store integration (read-only)
"""
import json
import os
import pytest
import tempfile

from src.observability.understanding.pipeline import UnderstandingPipeline, UnderstandingReport
from src.observability.understanding.review.models import ReviewLabel, FindingReview
from src.observability.understanding.review.store import ReviewStore
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _event(category, event_type, tick, entity_id=None, payload=None):
    return SimulationEvent(
        event_type=event_type,
        event_category=category,
        tick=tick,
        source_system="test_system",
        message="event",
        entity_id=entity_id,
        payload=payload or {},
        run_id="int-test"
    )


def _anomaly(rule_name, context=None):
    return Anomaly(
        rule_name=rule_name,
        severity="WARNING",
        tick_detected=10,
        message="anomaly",
        context=context or {}
    )


class TestUnderstandingPipeline:

    def test_pipeline_runs_on_empty_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox", events=[], anomalies=[])
            assert isinstance(report, UnderstandingReport)
            assert report.errors == []

    def test_pipeline_generates_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox", events=[], anomalies=[])
            report_path = os.path.join(tmpdir, "understanding_report.json")
            assert os.path.exists(report_path)
            with open(report_path) as f:
                data = json.load(f)
            assert "run_id" in data
            assert "domain_results" in data
            assert "root_cause" in data

    def test_pipeline_generates_markdown_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox", events=[], anomalies=[])
            md_path = os.path.join(tmpdir, "understanding_report.md")
            assert os.path.exists(md_path)
            content = open(md_path).read()
            assert "Phase 8 Understanding Report" in content

    def test_pipeline_domain_findings_on_stuck_entities(self):
        events = [_event("movement", "movement", tick=10, entity_id=i) for i in range(1, 4)]
        anomalies = [
            _anomaly("NavigationStuckRule", {"position": f"({i},{i})", "stuck_duration_ticks": 60})
            for i in range(1, 4)
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(
                run_dir=tmpdir,
                scenario_type="mixed_sandbox",
                events=events,
                anomalies=anomalies,
                run_id="stuck-test-001"
            )
            assert report.total_domain_findings() >= 1
            movement_result = next(r for r in report.domain_results if r.domain_id == "movement")
            assert any("Stuck" in f.title for f in movement_result.findings)

    def test_pipeline_root_cause_hypotheses_generated(self):
        events = [_event("economy", "gold_transaction", tick=5),
                  _event("economy", "gold_transaction", tick=10)]
        anomalies = [
            _anomaly("ResourceNodeCrowdingRule", {"node_id": f"n{i}", "entities_count": 5})
            for i in range(6)
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(
                run_dir=tmpdir, scenario_type="resource_economy",
                events=events, anomalies=anomalies
            )
            assert report.root_cause_result is not None
            assert len(report.root_cause_result.hypotheses) >= 1

    def test_pipeline_reads_existing_reviews(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-populate review store
            store = ReviewStore(tmpdir)
            store.add(FindingReview(
                run_id="test",
                finding_id="f1",
                label=ReviewLabel.CONFIRMED_BUG,
                comment="Verified"
            ))
            pipeline = UnderstandingPipeline()
            report = pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox", events=[], anomalies=[])
            assert len(report.existing_reviews) == 1
            assert report.existing_reviews[0].label == ReviewLabel.CONFIRMED_BUG

    def test_pipeline_runtime_is_tracked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox")
            assert report.pipeline_runtime_ms > 0.0

    def test_pipeline_run_id_defaults_to_dir_basename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox")
            assert report.run_id == os.path.basename(tmpdir)

    def test_pipeline_to_dict_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(run_dir=tmpdir, scenario_type="mixed_sandbox")
            d = report.to_dict()
            # Must be serializable without error
            json_str = json.dumps(d)
            assert len(json_str) > 10

    def test_pipeline_expectation_violations_on_missing_combat(self):
        """resource_economy pack requires economy signal to be > 0 — but we pass no events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = UnderstandingPipeline()
            report = pipeline.run(
                run_dir=tmpdir,
                scenario_type="resource_economy",
                events=[],
                anomalies=[]
            )
            # economy_events_count = 0, rule expects > 0 → violation
            violation_rule_ids = [v["rule_id"] for v in report.expectation_violations]
            assert "economy_events_present" in violation_rule_ids
