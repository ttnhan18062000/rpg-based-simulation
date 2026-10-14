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
