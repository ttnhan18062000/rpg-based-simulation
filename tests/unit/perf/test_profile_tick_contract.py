"""The contract options of the profiling tools (TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION): option mapping only, no heavy process."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from src.config import profiles as profiles_module
from src.perf.profiles import canonical_variant
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tools.perf import _profiling_common as common
from tools.perf import profile_tick

BASE_FLAGS = {"no_replay": True, "no_frame_pacing": True, "audit_mode": False}


def test_live_is_todays_behaviour_unchanged() -> None:
    profile = profiles_module.PROD_LARGE
    got_profile, governor, flags = common.contract_kernel_args(profile, "live")
    assert got_profile is profile and governor is None and flags == BASE_FLAGS


def test_pinned_passes_the_shared_pinned_governor_and_changes_nothing_else() -> None:
    profile = profiles_module.PROD_LARGE
    got_profile, governor, flags = common.contract_kernel_args(profile, "pinned")
    assert got_profile is profile and isinstance(governor, PinnedNormalGovernor) and flags == BASE_FLAGS


def test_canonical_uses_the_canonical_variant_of_the_profile() -> None:
    got_profile, governor, flags = common.contract_kernel_args(profiles_module.PROD_LARGE, "canonical")
    assert got_profile == canonical_variant(profiles_module.PROD_LARGE) and governor is None and flags == BASE_FLAGS


def test_audit_sets_audit_mode_and_nothing_else() -> None:
    _, governor, flags = common.contract_kernel_args(profiles_module.PROD_LARGE, "audit")
    assert governor is None and flags == {**BASE_FLAGS, "audit_mode": True}


def test_an_unknown_contract_is_an_error() -> None:
    with pytest.raises(ValueError):
        common.contract_kernel_args(profiles_module.PROD_LARGE, "fast")


def test_the_child_command_carries_the_contract_and_it_defaults_to_live() -> None:
    args = argparse.Namespace(scenario="idle", entities=10, seed=1, warmup=1, ticks=2, profile="PROD_LARGE", flag=None, flag_mode=None, contract="pinned")
    cmd = profile_tick.child_command(args, Path("out.json"))
    assert cmd[cmd.index("--contract") + 1] == "pinned"
    assert common.CONTRACTS[0] == "live"  # the default stays the historical behaviour


def test_the_pinned_note_names_what_still_moves() -> None:
    for text in ("RuntimeMode only", "audit_mode", "DEV-014", "scheduler"):
        assert text in common.PINNED_NOTE


def test_a_torn_byte_in_a_raw_folded_file_is_replaced_not_fatal(tmp_path) -> None:
    raw = tmp_path / "raw.folded"
    raw.write_bytes(b"main;_measured_ticks;work\xff 3\nmain;other 2\n")
    text = common.read_folded_text(raw)
    assert "_measured_ticks" in text and "\ufffd" in text
    assert common.parse_folded(text)


def test_a_corpus_scenario_goes_through_the_one_loader_in_rerun_baselines(monkeypatch) -> None:
    from tools.perf import rerun_baselines

    seen = {}
    monkeypatch.setattr(rerun_baselines, "load_corpus_state", lambda world, seed: (seen.update(world=world, seed=seed) or ("STATE", {})))
    assert common.build_state("corpus:frontier_marches", 0, 7) == "STATE"
    assert seen == {"world": "frontier_marches", "seed": 7}


def test_world_option_selects_the_corpus_scenario_and_an_unknown_scenario_is_a_usage_error(capsys) -> None:
    with pytest.raises(SystemExit):
        profile_tick.main(["--scenario", "nonsense", "--child", "--out-json", "x"])
    assert "unknown scenario" in capsys.readouterr().err


def test_profile_tick_writes_no_loader_of_its_own() -> None:
    here = Path(profile_tick.__file__).parent
    for name in ("profile_tick.py", "_profiling_common.py"):
        assert "_load_world_state" not in (here / name).read_text(encoding="utf-8"), name  # the loader lives in rerun_baselines only


# --- TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED: --replay -------------------------------------------------


def test_replay_off_is_the_default_and_the_flag_maps_to_no_replay_false() -> None:
    profile = profiles_module.PROD_LARGE
    assert common.contract_kernel_args(profile, "live")[2]["no_replay"] is True  # every earlier caller is unchanged
    for contract in common.CONTRACTS:
        _, _, flags = common.contract_kernel_args(profile, contract, replay=True)
        assert flags["no_replay"] is False
        assert flags["no_frame_pacing"] is True  # only replay changes
    assert common.contract_kernel_args(profile, "audit", replay=True)[2]["audit_mode"] is True


def test_the_replay_option_defaults_off_in_the_parser_and_reaches_the_child_under_out_dir(tmp_path) -> None:
    ns = argparse.Namespace(scenario="idle", entities=10, seed=1, warmup=1, ticks=2, profile="PROD_LARGE", flag=None, flag_mode=None, contract="canonical")
    assert "--replay" not in profile_tick.child_command(ns, tmp_path / "child.json")
    ns.replay = True
    cmd = profile_tick.child_command(ns, tmp_path / "child.json")
    assert "--replay" in cmd
    replay_dir = Path(cmd[cmd.index("--replay-dir") + 1])
    assert tmp_path in replay_dir.parents  # under the run's out-dir, never data/runs/


def test_a_replay_run_without_a_directory_is_refused() -> None:
    with pytest.raises(ValueError, match="replay_dir"):
        common.make_replay_manager(profiles_module.PROD_LARGE, {"audit_mode": False}, None)


def test_the_summary_counts_ticks_where_replay_was_not_allowed() -> None:
    ticks = [{"replay_allowed": True, "replay_richness": "FULL"}, {"replay_allowed": False, "replay_richness": "MINIMAL"}, {"replay_allowed": True, "replay_richness": "FULL"}]
    got = common.replay_summary({"ticks": ticks, "replay_stats": {"total_bytes_written": 5}})
    assert got == {"replay_allowed_ticks": 2, "replay_disallowed_ticks": 1, "replay_richness": ["FULL", "MINIMAL"], "replay_stats": {"total_bytes_written": 5}}
    assert common.replay_summary({"ticks": ticks}) is None  # a run without --replay records nothing


def test_a_tiny_replay_run_records_the_policy_the_stats_and_writes_only_under_the_given_directory(tmp_path) -> None:
    runs = Path("data/runs")
    before = set(runs.iterdir()) if runs.exists() else set()
    data = common.run_scenario_ticks("idle", 10, 42, 1, 2, contract="canonical", replay=True, replay_dir=tmp_path / "replay")
    summary = common.summarize_ticks(data)
    assert summary["replay"]["replay_allowed_ticks"] + summary["replay"]["replay_disallowed_ticks"] == 2
    assert "total_bytes_written" in summary["replay"]["replay_stats"]
    assert list((tmp_path / "replay").glob("chunk_*.json")) and (tmp_path / "replay" / "manifest.json").exists()  # the replay writer wrote here
    new_run_dirs = (set(runs.iterdir()) if runs.exists() else set()) - before  # the kernel's own run directory is its observability, replay on or off
    assert not [p for d in new_run_dirs for p in d.glob("chunk_*.json")]  # no replay chunk landed in data/runs/
    off = common.run_scenario_ticks("idle", 10, 42, 1, 2, contract="canonical")
    assert common.summarize_ticks(off)["replay"] is None and all("replay_allowed" in t for t in off["ticks"])
