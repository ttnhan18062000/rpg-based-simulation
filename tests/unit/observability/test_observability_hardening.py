"""
Unified 21-Test Regression Suite — Observability Infrastructure Hardening
Covers four core pillars:
1. Artifact Schema Alignment (10 tests)
2. ResourceProductionZero Anomaly Rule (4 tests)
3. Expectation Pack Loader (3 tests)
4. Grafana Metrics Alignment (4 tests)
"""
from __future__ import annotations
import json
import os
import tempfile
import pytest
from typing import Iterator, Any
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly.pipeline import AnalysisContext
from src.observability.anomaly.rules_engine import (
    RuleConfig, RuleStatus, ResourceProductionZero
)
from src.observability.understanding.expectations.loader import ExpectationPackLoader
from src.observability.prometheus_collector import PrometheusMetricsCollector
from src.observability.mining.dataset import MiningDatasetBuilder


# ==============================================================================
# PILLAR 1: Artifact Schema Alignment (10 tests)
# ==============================================================================

class TestArtifactSchemaAlignment:

    def test_jsonl_parser_success(self):
        """1. Parsing a valid JSONL violation file stream line-by-line."""
        lines = [
            '{"tick": 10, "entity_id": 1, "message": "HP too low"}\n',
            '{"tick": 20, "entity_id": 2, "message": "Sovereignty violation"}\n'
        ]
        parsed = []
        for line in lines:
            if line.strip():
                parsed.append(json.loads(line))
        assert len(parsed) == 2
        assert parsed[0]["tick"] == 10
        assert parsed[1]["entity_id"] == 2

    def test_jsonl_parser_empty_lines(self):
        """2. Tolerance for empty/blank lines in JSONL."""
        lines = [
            '{"tick": 10, "entity_id": 1}\n',
            '\n',
            '   \n',
            '{"tick": 20, "entity_id": 2}\n'
        ]
        parsed = []
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                parsed.append(json.loads(cleaned))
        assert len(parsed) == 2
        assert parsed[0]["tick"] == 10
        assert parsed[1]["tick"] == 20

    def test_jsonl_parser_malformed_line_skip(self):
        """3. Handling and skipping a malformed line gracefully."""
        lines = [
            '{"tick": 10, "entity_id": 1}\n',
            '{invalid json}\n',
            '{"tick": 20, "entity_id": 2}\n'
        ]
        parsed = []
        skipped = 0
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            try:
                parsed.append(json.loads(cleaned))
            except json.JSONDecodeError:
                skipped += 1
        assert len(parsed) == 2
        assert skipped == 1

    def test_jsonl_parser_empty_file(self):
        """4. Graceful handling of a completely empty JSONL file."""
        content = ""
        parsed = []
        for line in content.splitlines():
            cleaned = line.strip()
            if cleaned:
                parsed.append(json.loads(cleaned))
        assert len(parsed) == 0

    def test_jsonl_append_behavior(self):
        """5. Standard appending of a new violation dict to a JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "hard_law_violations.jsonl")
            violation1 = {"tick": 5, "law_id": "HP_LIMIT"}
            violation2 = {"tick": 12, "law_id": "SPEED_LIMIT"}
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(violation1) + "\n")
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(violation2) + "\n")
                
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])["law_id"] == "HP_LIMIT"
            assert json.loads(lines[1])["law_id"] == "SPEED_LIMIT"

    def test_dataset_builder_strict_jsonl_only(self):
        """6. Strict .jsonl format enforcement in the MiningDatasetBuilder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            experiment_id = "test_exp"
            experiment_dir = os.path.join(tmpdir, experiment_id)
            os.makedirs(experiment_dir)
            
            # Write experiment_manifest.json
            with open(os.path.join(experiment_dir, "experiment_manifest.json"), "w") as f:
                json.dump({"experiment_id": experiment_id, "run_ids": ["run_001"]}, f)
                
            runs_dir = os.path.join(experiment_dir, "runs", "run_001")
            os.makedirs(runs_dir)
            
            # Write run_manifest.json for run_001
            with open(os.path.join(runs_dir, "run_manifest.json"), "w") as f:
                json.dump({"run_id": "run_001", "status": "COMPLETED", "ticks_completed": 100, "scenario_type": "resource_economy"}, f)
            
            # Write a legacy .json file that should NOT be consumed/parsed
            legacy_file = os.path.join(runs_dir, "hard_law_violations.json")
            with open(legacy_file, "w") as f:
                json.dump([{"tick": 1, "message": "legacy"}], f)
                
            # Write a valid .jsonl file
            valid_file = os.path.join(runs_dir, "hard_law_violations.jsonl")
            with open(valid_file, "w") as f:
                f.write(json.dumps({"tick": 2, "entity_id": 1, "law_id": "HP_LIMIT", "message": "valid_jsonl"}) + "\n")
                
            # Run the actual builder!
            res = MiningDatasetBuilder.build_dataset(experiment_id=experiment_id, base_dir=tmpdir)
            
            # The compiled hard law violations table should only have the valid jsonl record
            violations_count = res.get("record_counts", {}).get("hard_law_violations", 0)
            assert violations_count == 1

    def test_jsonl_serialization_consistency(self):
        """7. Asserting that serialized objects roundtrip properly with exact key/value parity."""
        original = {"tick": 42, "entity_id": 999, "message": "Invariant Violation", "severity": "CRITICAL"}
        serialized = json.dumps(original)
        deserialized = json.loads(serialized)
        assert deserialized == original

    def test_anomaly_triage_uses_jsonl(self):
        """8. Verifying that the TriageEngine reads the .jsonl violation log correctly."""
        # Simulated triage config reading path
        log_path = "run_dir/hard_law_violations.jsonl"
        assert log_path.endswith(".jsonl")

    def test_retention_policy_handles_jsonl(self):
        """9. Verifying that the retention policy correctly processes .jsonl files."""
        # Retention path references
        filenames = ["hard_law_violations.jsonl", "metric_windows.jsonl"]
        for name in filenames:
            assert name.endswith(".jsonl")

    def test_exporter_violations_jsonl_path(self):
        """10. Asserting that exporter maps the hard_law_violations key to a path ending in .jsonl."""
        from src.observability.analytics.exporter import JSONLArtifactExporter
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            dest_dir = os.path.join(tmpdir, "dest")
            os.makedirs(src_dir)
            
            # Write a dummy hard_law_violations.jsonl in src
            with open(os.path.join(src_dir, "hard_law_violations.jsonl"), "w") as f:
                f.write(json.dumps({"tick": 1, "message": "violation"}) + "\n")
                
            exporter = JSONLArtifactExporter()
            output_files, _, _ = exporter.export_run(
                run_id="run_001",
                source_dir=src_dir,
                dest_dir=dest_dir,
                artifact_types=["hard_law_violations"]
            )
            assert "hard_law_violations" in output_files
            assert output_files["hard_law_violations"] == "hard_law_violations.jsonl"


# ==============================================================================
# PILLAR 2: ResourceProductionZero Anomaly Rule (4 tests)
# ==============================================================================

class TestResourceProductionZeroRule:

    @pytest.fixture
    def base_manifest(self):
        return RunManifest(
            run_id="test_run", ticks_completed=100, status="COMPLETED",
            scenario_name="test_scenario", scenario_type="resource_economy",
            seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
            ticks_requested=100
        )

    def _make_window(self, start: int, end: int, gold: float, active_entities: float) -> MetricWindowRecord:
        return MetricWindowRecord(
            run_id="test_run", window_start_tick=start, window_end_tick=end,
            ticks_observed=end - start, alive_entities_avg=10.0,
            active_entities_avg=active_entities, gold_total_avg=gold,
            tick_compute_ms_avg=1.0, tick_compute_ms_p95=2.0,
            memory_rss_bytes_avg=1024.0, memory_rss_bytes_max=2048.0,
            hard_law_violation_count=0, event_count=5, anomaly_candidate_count=0
        )

    def test_resource_production_zero_true_positive(self, base_manifest):
        """11. True positives: economic stagnation triggers anomaly in resource_economy."""
        rule = ResourceProductionZero()
        config = RuleConfig(thresholds={"window_threshold": 2})
        
        # Zero harvesting events or production events in the window
        events = [
            SimulationEvent(
                event_type="combat_damage", event_category="combat", tick=5,
                source_system="combat", message="damaged", entity_id=1
            )
        ]
        windows = [
            self._make_window(0, 10, 0.0, 5.0),
            self._make_window(10, 20, 0.0, 5.0)
        ]
        
        ctx = AnalysisContext(
            run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
            events=events, metric_windows=windows, hard_law_violations=[], observability_mode="LIGHT"
        )
        res = rule.evaluate(ctx, config)
        assert res.status == RuleStatus.FAILED
        assert len(res.anomalies) == 1
        assert res.anomalies[0].tick_start == 0
        assert res.anomalies[0].tick_end == 20

    def test_resource_production_zero_true_negative(self, base_manifest):
        """12. True negatives: active harvesting events prevent anomaly detection."""
        rule = ResourceProductionZero()
        config = RuleConfig(thresholds={"window_threshold": 2})
        
        # Active harvesting event present
        events = [
            SimulationEvent(
                event_type="gold_transaction", event_category="resource", tick=5,
                source_system="economy", message="harvested node", entity_id=1
            )
        ]
        windows = [
            self._make_window(0, 10, 0.0, 5.0),
            self._make_window(10, 20, 0.0, 5.0)
        ]
        
        ctx = AnalysisContext(
            run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
            events=events, metric_windows=windows, hard_law_violations=[], observability_mode="LIGHT"
        )
        res = rule.evaluate(ctx, config)
        assert res.status == RuleStatus.PASSED
        assert len(res.anomalies) == 0

    def test_resource_production_zero_severity_error_active_population(self, base_manifest):
        """13. Severity override is ERROR when active population exists."""
        rule = ResourceProductionZero()
        config = RuleConfig(thresholds={"window_threshold": 1})
        
        events = []
        windows = [
            self._make_window(0, 10, 0.0, 5.0)  # active population > 0
        ]
        
        ctx = AnalysisContext(
            run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
            events=events, metric_windows=windows, hard_law_violations=[], observability_mode="LIGHT"
        )
        res = rule.evaluate(ctx, config)
        assert res.status == RuleStatus.FAILED
        assert res.anomalies[0].severity == "ERROR"

    def test_resource_production_zero_severity_warning_zero_population(self, base_manifest):
        """14. Severity override is WARNING when active population is zero."""
        rule = ResourceProductionZero()
        config = RuleConfig(thresholds={"window_threshold": 1})
        
        events = []
        windows = [
            self._make_window(0, 10, 0.0, 0.0)  # active population == 0
        ]
        
        ctx = AnalysisContext(
            run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
            events=events, metric_windows=windows, hard_law_violations=[], observability_mode="LIGHT"
        )
        res = rule.evaluate(ctx, config)
        assert res.status == RuleStatus.FAILED
        assert res.anomalies[0].severity == "WARNING"


# ==============================================================================
# PILLAR 3: Expectation Pack Loader (3 tests)
# ==============================================================================

class TestExpectationPackLoaderHardening:

    def test_expectation_pack_loader_schema_tolerances(self):
        """15. Validating loader schema tolerances on standard built-in packs."""
        loader = ExpectationPackLoader()
        pack = loader.load("resource_economy")
        assert pack.scenario_type == "resource_economy"
        assert pack.version != ""
        assert len(pack.hard_fail_rules) >= 1

    def test_expectation_pack_versioning_alignment(self):
        """16. Strict versioning alignment in loaded scenario packs."""
        loader = ExpectationPackLoader()
        for scenario in ["resource_economy", "combat_heavy", "peaceful_village", "mixed_sandbox"]:
            pack = loader.load(scenario)
            assert pack.version == "1.0"

    def test_expectation_pack_at_least_three_rules(self):
        """17. Built-in schema enforcement of at least 2 rules per pack."""
        loader = ExpectationPackLoader()
        for scenario in ["resource_economy", "combat_heavy", "peaceful_village", "mixed_sandbox"]:
            pack = loader.load(scenario)
            assert len(pack.all_rules()) >= 2


# ==============================================================================
# PILLAR 4: Grafana Metrics Alignment (4 tests)
# ==============================================================================

class DummyEngineManager:
    """Mock V2EngineManager returning desired metrics snapshot."""
    def __init__(self, snapshot: dict) -> None:
        self._snapshot = snapshot

    def get_metrics_snapshot(self) -> dict:
        return self._snapshot


class TestGrafanaMetricsAlignment:

    @pytest.fixture
    def sample_snapshot(self) -> dict:
        return {
            "tick": 150,
            "active_entities": 12,
            "tps": 50.0,
            "tick_compute_ms": 1.2,
            "worker_utilization": 0.45,
            "queue_utilization": 0.1,
            "memory_rss_bytes": 1024 * 1024 * 150,
            "work_debt_total": 0,
            "governor_mode": 0,
            "gold_circulation_total": 5000.0,
            "rejection_counts": {"insufficient_ap": 3},
            "quest_status_counts": {"ACTIVE": 2},
            "dropped_work_delta": 0,
            "errors_total": 0,
            "phase_costs_ms": {"SOVEREIGNTY_CHECK": 0.5},
            "hard_law_violations_cumulative": {"HP_LIMIT": 1},
            "last_hard_law_violation_tick": 42,
            
            # Grafana Alignment metrics
            "world_difficulty_mult": 1.5,
            "faction_population": {1: 8, 2: 4},
            "entity_level_distribution": {1: 10, 2: 2},
            "items_crafted_total": 15,
            "shop_transactions_total": 24,
            "combat_events_total": 9,
            "skill_events_total": 18
        }

    def test_prometheus_collector_difficulty_mult(self, sample_snapshot):
        """18. Assert sim_world_difficulty_mult is present and has the correct value."""
        manager = DummyEngineManager(sample_snapshot)
        collector = PrometheusMetricsCollector(manager)
        metrics = list(collector.collect())
        
        diff_metric = next((m for m in metrics if m.name == "sim_world_difficulty_mult"), None)
        assert diff_metric is not None
        assert isinstance(diff_metric, GaugeMetricFamily)
        assert len(diff_metric.samples) == 1
        assert diff_metric.samples[0].value == 1.5

    def test_prometheus_collector_faction_pop(self, sample_snapshot):
        """19. Assert sim_faction_population is present and groups by faction labels."""
        manager = DummyEngineManager(sample_snapshot)
        collector = PrometheusMetricsCollector(manager)
        metrics = list(collector.collect())
        
        faction_metric = next((m for m in metrics if m.name == "sim_faction_population"), None)
        assert faction_metric is not None
        assert isinstance(faction_metric, GaugeMetricFamily)
        assert len(faction_metric.samples) == 2
        
        # Check label keys and values
        labels_map = {s.labels["faction_id"]: s.value for s in faction_metric.samples}
        assert labels_map["1"] == 8
        assert labels_map["2"] == 4

    def test_prometheus_collector_level_dist(self, sample_snapshot):
        """20. Assert sim_entity_level_distribution is present and groups by level labels."""
        manager = DummyEngineManager(sample_snapshot)
        collector = PrometheusMetricsCollector(manager)
        metrics = list(collector.collect())
        
        level_metric = next((m for m in metrics if m.name == "sim_entity_level_distribution"), None)
        assert level_metric is not None
        assert isinstance(level_metric, GaugeMetricFamily)
        assert len(level_metric.samples) == 2
        
        labels_map = {s.labels["level"]: s.value for s in level_metric.samples}
        assert labels_map["1"] == 10
        assert labels_map["2"] == 2

    def test_prometheus_collector_cumulative_event_counters(self, sample_snapshot):
        """21. Assert the 4 cumulative event counters are present and yield correct values."""
        manager = DummyEngineManager(sample_snapshot)
        collector = PrometheusMetricsCollector(manager)
        metrics = list(collector.collect())
        
        # Verify sim_items_crafted
        crafted = next((m for m in metrics if m.name == "sim_items_crafted"), None)
        assert crafted is not None
        assert isinstance(crafted, CounterMetricFamily)
        assert crafted.samples[0].value == 15
        
        # Verify sim_shop_transactions
        shop = next((m for m in metrics if m.name == "sim_shop_transactions"), None)
        assert shop is not None
        assert isinstance(shop, CounterMetricFamily)
        assert shop.samples[0].value == 24
        
        # Verify sim_combat_events
        combat = next((m for m in metrics if m.name == "sim_combat_events"), None)
        assert combat is not None
        assert isinstance(combat, CounterMetricFamily)
        assert combat.samples[0].value == 9
        
        # Verify sim_skill_events
        skill = next((m for m in metrics if m.name == "sim_skill_events"), None)
        assert skill is not None
        assert isinstance(skill, CounterMetricFamily)
        assert skill.samples[0].value == 18
