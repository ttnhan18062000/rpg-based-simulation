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


# --- TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST: age-bracket transition guard -------------


def test_age_bracket_warning_for_default_ticks_names_both_real_boundaries():
    """The tool's own 5000-tick default cannot reach either real fantasy-year-scaled boundary --
    the warning must name both, not just one."""
    warning = slro.age_bracket_transition_warning(5000)
    assert warning is not None
    assert "3,456,000" in warning
    assert "17,280,000" in warning


def test_age_bracket_warning_for_ticks_between_boundaries_names_only_the_elder_gap():
    warning = slro.age_bracket_transition_warning(4_000_000)
    assert warning is not None
    assert "reaches the young->adult boundary" in warning
    assert "but not the adult->elder boundary" in warning
    assert "17,280,000" in warning


def test_age_bracket_warning_none_once_ticks_reaches_real_elder_boundary():
    assert slro.age_bracket_transition_warning(17_280_000) is None
    assert slro.age_bracket_transition_warning(20_000_000) is None
