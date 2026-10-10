"""Canonical PERF_* variants (TCK-20261010-PERF-M2-T07-CANONICAL-VARIANTS)."""
from __future__ import annotations

import pytest

from src.config.profiles import SignalContract
from src.engine.signal_source import CanonicalSignalSource, LiveSignalSource, select_signal_source
from src.perf.profiles import (
    CANONICAL_SUFFIX,
    PERF_CANONICAL_PROFILES,
    PERF_MATRIX,
    PERF_PROFILES,
    canonical_variant,
)

ORIGINAL_KEYS = [
    "PERF_512MB_LOCAL",
    "PERF_1GB_LOCAL",
    "PERF_2GB_LOCAL",
    "PERF_4GB_LOCAL",
    "PERF_512MB_CONC",
    "PERF_1GB_CONC",
    "PERF_2GB_CONC",
    "PERF_4GB_CONC",
]


def test_the_eight_original_profiles_are_unchanged_in_shape() -> None:
    assert list(PERF_PROFILES) == ORIGINAL_KEYS


@pytest.mark.parametrize("key", ORIGINAL_KEYS)
def test_every_profile_has_a_canonical_variant(key: str) -> None:
    assert PERF_CANONICAL_PROFILES[key].signal_contract is SignalContract.CANONICAL


@pytest.mark.parametrize("key", ORIGINAL_KEYS)
def test_a_variant_differs_from_its_default_only_in_contract_and_name(key: str) -> None:
    default, variant = PERF_PROFILES[key].model_dump(), PERF_CANONICAL_PROFILES[key].model_dump()
    assert {k for k in default if default[k] != variant[k]} == {"name", "signal_contract"}
    assert variant["name"] == key + CANONICAL_SUFFIX
    for same in ("max_ram_mb", "max_worker_count", "max_tick_budget_ms", "cadence", "hardware_class"):
        assert default[same] == variant[same]


@pytest.mark.parametrize("key", ORIGINAL_KEYS)
def test_defaults_stay_live(key: str) -> None:
    assert PERF_PROFILES[key].signal_contract is SignalContract.LIVE


def test_the_matrix_maps_only_to_the_original_live_profiles() -> None:
    names = {entry for scale in PERF_MATRIX.values() for modes in scale.values() for entry in modes.values()}
    assert names <= set(PERF_PROFILES)
    assert not any(name.endswith(CANONICAL_SUFFIX) for name in names)


def test_signal_source_routing() -> None:
    assert isinstance(select_signal_source(PERF_CANONICAL_PROFILES["PERF_1GB_LOCAL"], audit_mode=False), CanonicalSignalSource)
    live = select_signal_source(PERF_PROFILES["PERF_1GB_LOCAL"], audit_mode=False)
    assert type(live) is LiveSignalSource


def test_canonical_variant_does_not_mutate_its_source() -> None:
    source = PERF_PROFILES["PERF_2GB_CONC"]
    canonical_variant(source)
    assert source.signal_contract is SignalContract.LIVE and source.name == "PERF_2GB_CONC"
