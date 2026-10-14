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
