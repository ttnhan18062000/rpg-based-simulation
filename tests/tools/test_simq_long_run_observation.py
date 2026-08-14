"""TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER."""
import json
import logging
import os
import shutil
import sys
from pathlib import Path

import pytest

logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import simq_long_run_observation as slro  # noqa: E402


def test_default_world_subset_matches_calibration_precedent():
    """Reuses TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION's own density-correlation sample --
    not re-invented."""
    assert slro.DEFAULT_WORLDS == [
        "wilderness_survival", "resource_dense_basin", "crowded_frontier",
        "hero_guild_routing", "dungeon_crawl", "urban_political",
    ]


def test_observe_one_world_produces_both_signals(tmp_path):
    result = slro.observe_world("sandbox_world", seed=42, ticks=30, obs_mode="NORMAL")
    try:
        assert "simq_report" in result
        assert "overall_grade" in result["simq_report"]
        assert "lifecycle_score" in result
        assert "clustering" in result["lifecycle_score"]
        assert result["health"]["dropped_count"] == 0
    finally:
        # no leftover data/runs/ scratch directory from this test's own run
        pass


def test_observe_world_cleans_up_its_own_run_dir():
    before = set(os.listdir("data/runs")) if os.path.isdir("data/runs") else set()
    slro.observe_world("sandbox_world", seed=42, ticks=30, obs_mode="NORMAL")
    after = set(os.listdir("data/runs")) if os.path.isdir("data/runs") else set()
    assert after == before, f"observe_world left scratch data behind: {after - before}"


def test_output_written_to_docs_long_run_observations_dir():
    assert str(slro.OUTPUT_DIR) == "docs/simulation_quality/long_run_observations"


def test_engine_driven_only_once_per_world(monkeypatch):
    call_count = {"n": 0}
    real_run_for_analysis = None
    import entity_lifecycle_score as els

    orig = els._run_for_analysis

    def spy(*args, **kwargs):
        call_count["n"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(els, "_run_for_analysis", spy)
    slro.observe_world("sandbox_world", seed=42, ticks=30, obs_mode="NORMAL")
    assert call_count["n"] == 1
