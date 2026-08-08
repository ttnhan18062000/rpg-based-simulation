"""TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION — real SimQ-corpus perf baseline coverage."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from bench_corpus_world import bench_corpus_world  # noqa: E402

BASELINES_DIR = Path("tests/perf/baselines")
COMMITTED_WORLDS = ["frontier_extended", "frontier_marches", "crowded_frontier"]


def test_bench_corpus_world_loads_real_state():
    result = bench_corpus_world("frontier_extended", seed=42, warmup_ticks=5, sample_ticks=10)
    assert result["source_world"] == "frontier_extended"
    assert result["source_entity_count"] == 59
    assert result["avg_tick_compute_ms"] > 0


def test_perf_baseline_scenario_id_matches_run_key_convention():
    for world in COMMITTED_WORLDS:
        path = BASELINES_DIR / f"simq_corpus_{world}.json"
        assert path.exists(), f"missing committed baseline for {world}"
        data = json.loads(path.read_text())
        assert data["scenario_id"] == f"simq_corpus_{world}"
        # Distinguishable from the pre-existing synthetic scenario_ids (combat_10_local etc.)
        assert data["scenario_id"] not in {
            "combat_10_local", "idle_100_local", "movement_100_local",
        }


def test_corpus_baseline_json_schema_matches_existing_baselines():
    existing = json.loads((BASELINES_DIR / "idle_100_local.json").read_text())
    for world in COMMITTED_WORLDS:
        new = json.loads((BASELINES_DIR / f"simq_corpus_{world}.json").read_text())
        # Real, live raw-dict shape (test_perf_regression_baseline.py's own convention) —
        # NOT src/perf/regression_gate.py's PerfBaseline dataclass field names, confirmed unused.
        for required_field in ("profile", "avg_tick_compute_ms", "tick_ms", "mem_rss_mb"):
            assert required_field in existing
            assert required_field in new
