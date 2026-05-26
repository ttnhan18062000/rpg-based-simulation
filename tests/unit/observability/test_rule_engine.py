import pytest
from src.observability.anomaly.pipeline import AnalysisContext
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.anomaly.rules_engine import (
    RuleEngine, BaseRule, RuleRegistry, RuleConfig, RuleResult, RuleStatus
)

class DummyRule(BaseRule):
    rule_id = "DummyRule"
    required_signals = ["metric_windows"]
    valid_scenarios = ["resource_economy"]
    domain = "system"

    def evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult:
        if not context.metric_windows:
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_MISSING_SIGNAL)
        if context.scenario_type != "resource_economy":
            return RuleResult(rule_id=self.rule_id, status=RuleStatus.SKIPPED_SCENARIO_TYPE)
        return RuleResult(rule_id=self.rule_id, status=RuleStatus.PASSED)

def test_rule_registry():
    registry = RuleRegistry()
    initial_count = len(registry.get_rules())
    registry.register(DummyRule())
    assert len(registry.get_rules()) == initial_count + 1
    assert any(r.rule_id == "DummyRule" for r in registry.get_rules())

def test_rule_engine_loading_defaults():
    engine = RuleEngine()
    engine.load_config("nonexistent_rules_core.json")
    assert not engine.config  # empty config maps to defaults

def test_rule_engine_evaluation_gating():
    registry = RuleRegistry()
    dummy = DummyRule()
    registry.register(dummy)
    engine = RuleEngine(registry=registry)

    # Context with missing signal
    manifest = RunManifest(
        run_id="test_run", ticks_completed=100, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="resource_economy",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    ctx_no_signal = AnalysisContext(
        run_id="test_run",
        run_manifest=manifest,
        scenario_type="resource_economy",
        events=[],
        metric_windows=[],
        hard_law_violations=[],
        observability_mode="LIGHT"
    )

    results = engine.evaluate_all(ctx_no_signal)
    dummy_res = next(r for r in results if r.rule_id == "DummyRule")
    assert dummy_res.status == RuleStatus.SKIPPED_MISSING_SIGNAL

    # Context with mismatched scenario
    from src.observability.reporting.metric_recorder import MetricWindowRecord
    dummy_window = MetricWindowRecord(
        run_id="test_run", window_start_tick=0, window_end_tick=10, ticks_observed=10,
        alive_entities_avg=1.0, active_entities_avg=1.0, gold_total_avg=10.0,
        tick_compute_ms_avg=1.0, tick_compute_ms_p95=2.0, memory_rss_bytes_avg=1024.0,
        memory_rss_bytes_max=2048.0, hard_law_violation_count=0, event_count=5,
        anomaly_candidate_count=0
    )
    manifest_wrong = RunManifest(
        run_id="test_run", ticks_completed=100, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="combat_arena",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    ctx_wrong_scenario = AnalysisContext(
        run_id="test_run",
        run_manifest=manifest_wrong,
        scenario_type="combat_arena",
        events=[],
        metric_windows=[dummy_window],
        hard_law_violations=[],
        observability_mode="LIGHT"
    )

    results2 = engine.evaluate_all(ctx_wrong_scenario)
    dummy_res2 = next(r for r in results2 if r.rule_id == "DummyRule")
    assert dummy_res2.status == RuleStatus.SKIPPED_SCENARIO_TYPE

def test_rule_engine_disable():
    registry = RuleRegistry()
    registry.register(DummyRule())
    engine = RuleEngine(registry=registry)
    engine.config["DummyRule"] = RuleConfig(enabled=False)

    manifest = RunManifest(
        run_id="test_run", ticks_completed=100, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="resource_economy",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    ctx = AnalysisContext(
        run_id="test_run",
        run_manifest=manifest,
        scenario_type="resource_economy",
        events=[],
        metric_windows=[],
        hard_law_violations=[],
        observability_mode="LIGHT"
    )

    results = engine.evaluate_all(ctx)
    assert not any(r.rule_id == "DummyRule" for r in results)
