"""
tests/integration/tools/test_calibrate_simq_campaign_mode.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for tools/calibrate_simq.py's campaign-mode entry point
(TCK-20260824-GRIEF-NEMESIS-REACHABILITY, AC1).

_run_campaign_engine() is the real production entry point that makes
CampaignOrchestrator.run_episode() reachable outside test scaffolding, selected by
main() when a profile YAML (e.g. config/simulation_quality/profiles/
campaign_life_arc.yaml) declares campaign_episodes: N.
"""
from __future__ import annotations

import json
import os

import pytest

import tools.calibrate_simq as cal_mod


@pytest.mark.slow
def test_calibrate_simq_campaign_profile_runs_multiple_episodes(monkeypatch):
    """AC1: the campaign-mode branch actually drives CampaignOrchestrator.run_episode()
    at least twice and merges every episode's own per-Kernel JSONL into one file that
    main()'s _replay_jsonl_through_hub() can read.
    """
    from src.domains.campaigns.orchestrator import CampaignOrchestrator

    episode_calls = []
    real_run_episode = CampaignOrchestrator.run_episode

    def _spy_run_episode(self):
        summary = real_run_episode(self)
        episode_calls.append(summary)
        return summary

    monkeypatch.setattr(CampaignOrchestrator, "run_episode", _spy_run_episode)

    run_dir, elapsed, run_id = cal_mod._run_campaign_engine(
        name="campaign_life_arc_test",
        seed=42,
        ticks=5,
        episodes=2,
        entity_count=4,
    )

    assert len(episode_calls) == 2, "run_episode() must be called once per manifest episode"
    assert run_id.startswith("campaign_")
    assert os.path.isdir(run_dir)

    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    assert os.path.exists(jsonl_path)

    with open(jsonl_path, encoding="utf-8") as fh:
        lines = [ln for ln in fh if ln.strip()]
    assert lines, "merged simulation_events.jsonl must not be empty"

    event_types = {json.loads(line)["event_type"] for line in lines}
    # scenario_objective_completed only reaches the merged JSONL because Step 1b
    # (orchestrator.py:172) wires self._event_recorder through to ScenarioRuntimeService —
    # this is the real end-to-end proof that a genuine CampaignOrchestrator.run_episode()
    # call, not test scaffolding, produced this data.
    assert "scenario_objective_completed" in event_types, (
        "each episode's own scenario-lifecycle event must be present in the merged JSONL"
    )


def test_load_profile_campaign_episodes_reads_new_profile():
    """AC1: the new campaign_life_arc.yaml profile is read correctly by
    _load_profile_campaign_episodes()."""
    assert cal_mod._load_profile_campaign_episodes("campaign_life_arc") == 3


def test_load_profile_campaign_episodes_defaults_zero_for_non_campaign_profile():
    """A profile without campaign_episodes: (e.g. default) must resolve to 0, selecting
    the single-episode _run_engine() path in main()."""
    assert cal_mod._load_profile_campaign_episodes("default") == 0


def test_load_profile_campaign_episodes_missing_profile_defaults_zero():
    assert cal_mod._load_profile_campaign_episodes("__no_such_profile__") == 0
