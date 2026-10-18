"""TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION — real SimQ-corpus perf baseline coverage."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from bench_corpus_world import bench_corpus_world  # noqa: E402
from tools.perf import baseline_lifecycle, tripwire  # noqa: E402

BASELINES_DIR = baseline_lifecycle.DEFAULT_BASELINES_DIR
COMMITTED_WORLDS = ["frontier_extended", "frontier_marches", "crowded_frontier"]


def test_bench_corpus_world_loads_real_state():
    result = bench_corpus_world("frontier_extended", seed=42, warmup_ticks=5, sample_ticks=10)
    assert result["source_world"] == "frontier_extended"
    # 59 -> 65 (2026-10-14, #536): +6 small_plant_eater bodies (faction wild_fauna) from the generic plant-eater archetype
    # (owner decisions 45-50); the same +6 the corpus registry regeneration shows for frontier_extended.
    assert result["source_entity_count"] == 65
    assert result["avg_tick_compute_ms"] > 0


#: The keys the nightly lane reads from a raw-dict corpus file (``test_perf_regression_baseline.py``'s convention); fixed here, not copied from another baseline.
RAW_DICT_KEYS = ("scenario_id", "profile", "avg_tick_compute_ms", "tick_ms", "mem_rss_mb")
SYNTHETIC_SCENARIOS = {"combat_10_local", "idle_100_local", "movement_100_local"}


def _is_promoted(world: str) -> bool:
    return bool(baseline_lifecycle.version_files(BASELINES_DIR, f"simq_corpus_{world}"))


@pytest.mark.parametrize("world", COMMITTED_WORLDS)
def test_perf_baseline_scenario_id_matches_run_key_convention(world):
    name = f"simq_corpus_{world}"
    # Distinguishable from the pre-existing synthetic scenario_ids (combat_10_local etc.)
    assert name not in SYNTHETIC_SCENARIOS
    if _is_promoted(world):
        record, reason = tripwire.load_baseline(name)
        assert record is not None, reason
        assert record.identity.scenario.id == name
    else:
        path = BASELINES_DIR / f"{name}.json"
        assert path.exists(), f"missing committed baseline for {world}"
        assert json.loads(path.read_text())["scenario_id"] == name


@pytest.mark.parametrize("world", COMMITTED_WORLDS)
def test_corpus_baseline_shape(world):
    name = f"simq_corpus_{world}"
    if _is_promoted(world):
        record, reason = tripwire.load_baseline(name)
        assert record is not None, reason
        assert record.schema_version
        assert record.result.latency_ms["avg"] > 0
        memory = record.result.memory_mb
        assert memory["rss_high_water"] > 0  # every promoted record carries it, whatever the schema minor
        if "rss_after_trim_mb" in memory:
            assert memory["rss_after_trim_mb"] <= memory["rss_high_water"]
    else:
        data = json.loads((BASELINES_DIR / f"{name}.json").read_text())
        for required_field in RAW_DICT_KEYS:
            assert required_field in data
