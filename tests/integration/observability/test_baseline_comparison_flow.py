import os
import sys
import json
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.observability.reporting.baseline_generator import BaselineGenerator
from src.observability.reporting.baseline_comparator import BaselineComparator
from src.cli.entry import _run_compare_run, _run_compare_sweep


SLOW_TICK_MS = 59.0  # above the HighCPULatencyRule's 50 ms limit: what a loaded host produced


def _sweep(tmp_path, sweep_id):
    output_dir = str(tmp_path / "run_sets")
    ScenarioSweeper.run_sweep(ScenarioSweepConfig(
        sweep_id=sweep_id, scenario_name="idle", scenario_type="sandbox", seeds=[1, 2, 3], ticks=2,
        observability_mode=ObservabilityMode.LIGHT, output_dir=output_dir))
    return output_dir


def _compute_ms_avgs(output_dir, sweep_id):
    records = RunSetArtifactRepository(base_dir=output_dir).read_run_index(sweep_id)
    scores = []
    for r in records:
        with open(os.path.join(output_dir, sweep_id, "runs", r.run_id, "metric_windows.jsonl"), encoding="utf-8") as f:
            scores.append(max(json.loads(line)["tick_compute_ms_avg"] for line in f if line.strip()))
    return scores


def test_a_slow_tick_is_what_trips_the_cpu_latency_rule(tmp_path, tick_cost_ms):
    """The injection is real: with every tick recorded at 59 ms the runs' average compute is over the rule's 50 ms limit, which is what made the flow WARNING."""
    tick_cost_ms(SLOW_TICK_MS)
    assert all(ms > 50.0 for ms in _compute_ms_avgs(_sweep(tmp_path, "slow_sweep"), "slow_sweep"))


def test_baseline_comparison_and_cli_flow(tmp_path, tick_cost_ms):
    tick_cost_ms(5.0)  # the verdict below is a comparison of identical idle runs, not a measurement of this host's speed
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_compare_sweep"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2, 3],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # 1. Execute sequential sweep
    ScenarioSweeper.run_sweep(config)

    # 2. Generate baseline
    baseline = BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)
    baseline_path = os.path.join(output_dir, sweep_id, "baseline.json")
    with open(baseline_path, "r", encoding="utf-8") as f:
        # the generator itself stamps the cost accounting, nothing patches the file
        assert json.load(f)["cost_accounting_version"]

    # 3. Test single run comparison (Good run passes)
    records = RunSetArtifactRepository(base_dir=output_dir).read_run_index(sweep_id)
    for r in records:
        run_dir = os.path.join(output_dir, sweep_id, "runs", r.run_id)
        # Ensure anomalies.json exists
        with open(os.path.join(run_dir, "anomalies.json"), "w") as f:
            json.dump([], f)
        # Ensure metric_windows.jsonl exists
        mw_path = os.path.join(run_dir, "metric_windows.jsonl")
        if not os.path.exists(mw_path):
            with open(mw_path, "w") as f:
                f.write(json.dumps({"tick_compute_ms_p95": 10.0, "memory_rss_bytes_max": 1000.0, "event_count": 5}) + "\n")

    run_id = records[0].run_id

    res_run = BaselineComparator.compare_run(run_id, baseline_path, run_dir=os.path.join(output_dir, sweep_id, "runs"))
    assert res_run.status == "PASS"

    # 4. Test compare-run CLI command launcher
    # Patch RunSetArtifactRepository default instantiation path
    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.run_id = run_id
        cli_args.baseline = baseline_path
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_compare_run(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 0  # Passed run exit code 0
        cli_output = captured_out.getvalue()
        assert "Comparison Result: PASS" in cli_output

    # 5. Test compare-sweep CLI command launcher
    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.sweep_id = sweep_id
        cli_args.baseline = baseline_path
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_compare_sweep(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 0  # Passed sweep exit code 0
        cli_output = captured_out.getvalue()
        assert "Comparison Result: PASS" in cli_output
        assert "Statistical Metric Drifts" in cli_output



def test_freshly_generated_baseline_gives_a_tick_cost_verdict_not_inconclusive(tmp_path):
    from src.perf.benchmark_record import COST_ACCOUNTING_VERSION
    sweep_id = "fresh_baseline_cost_sweep"
    output_dir = str(tmp_path / "run_sets")
    config = ScenarioSweepConfig(
        sweep_id=sweep_id, scenario_name="idle", scenario_type="sandbox", seeds=[1, 2, 3],
        ticks=2, observability_mode=ObservabilityMode.LIGHT, output_dir=output_dir
    )
    ScenarioSweeper.run_sweep(config)
    BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)
    baseline_path = os.path.join(output_dir, sweep_id, "baseline.json")
    with open(baseline_path, "r", encoding="utf-8") as f:
        assert json.load(f)["cost_accounting_version"] == COST_ACCOUNTING_VERSION

    result = BaselineComparator.compare_sweep(sweep_id, baseline_path, base_dir=output_dir)

    assert result.tick_cost_incomparable_reason is None
    assert "tick_compute_ms_p95" in result.drifts  # a verdict, not INCONCLUSIVE
