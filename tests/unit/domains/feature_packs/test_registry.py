"""Tests for FeatureRegistry[T] (E63C)."""

from __future__ import annotations

import pytest

from src.domains.adventure.schema import RouteFamily
from src.domains.feature_packs.registry import FeatureRegistry


class _FakeGen:
    pass


class _AnotherGen:
    pass


# ── register / lookup ─────────────────────────────────────────────────────────

def test_register_and_lookup():
    reg: FeatureRegistry[type] = FeatureRegistry()
    reg.register("ESCORT_DIGNITARY", _FakeGen)
    assert reg.lookup("ESCORT_DIGNITARY") is _FakeGen


def test_lookup_unknown_raises_key_error():
    reg: FeatureRegistry[type] = FeatureRegistry()
    with pytest.raises(KeyError):
        reg.lookup("NONEXISTENT")


def test_duplicate_register_overwrites():
    reg: FeatureRegistry[type] = FeatureRegistry()
    reg.register("KEY", _FakeGen)
    reg.register("KEY", _AnotherGen)
    assert reg.lookup("KEY") is _AnotherGen


# ── list_all without enum_class ───────────────────────────────────────────────

def test_list_all_no_enum_returns_pack_keys():
    reg: FeatureRegistry[type] = FeatureRegistry()
    reg.register("ZZZ", _FakeGen)
    reg.register("AAA", _AnotherGen)
    result = reg.list_all()
    assert result == ["AAA", "ZZZ"]


def test_list_all_empty_registry():
    reg: FeatureRegistry[type] = FeatureRegistry()
    assert reg.list_all() == []


# ── list_all with enum_class ──────────────────────────────────────────────────

def test_list_all_with_enum_class_canonical_first():
    reg: FeatureRegistry[type] = FeatureRegistry(enum_class=RouteFamily)
    reg.register("ESCORT_DIGNITARY", _FakeGen)
    result = reg.list_all()
    # Canonical values are present
    assert "recover" in result
    assert "buy_upgrade" in result
    # Pack-registered key appended after canonical section
    assert "ESCORT_DIGNITARY" in result
    # All canonical come before pack-only key
    canonical_values = {m.value for m in RouteFamily}
    canonical_indices = [result.index(v) for v in canonical_values]
    escort_index = result.index("ESCORT_DIGNITARY")
    assert escort_index > max(canonical_indices)


def test_list_all_with_enum_class_no_duplicates_for_shadowing_key():
    reg: FeatureRegistry[type] = FeatureRegistry(enum_class=RouteFamily)
    # "recover" is an existing canonical value — registering it as a pack entry
    # should NOT produce a duplicate in list_all()
    reg.register("recover", _FakeGen)
    result = reg.list_all()
    assert result.count("recover") == 1


def test_list_all_canonical_sorted_alphabetically():
    reg: FeatureRegistry[type] = FeatureRegistry(enum_class=RouteFamily)
    canonical_in_result = [k for k in reg.list_all() if k in {m.value for m in RouteFamily}]
    assert canonical_in_result == sorted(canonical_in_result)


def test_list_all_pack_keys_sorted_alphabetically():
    reg: FeatureRegistry[type] = FeatureRegistry()
    reg.register("ZZZ", _FakeGen)
    reg.register("AAA", _AnotherGen)
    reg.register("MMM", _FakeGen)
    result = reg.list_all()
    assert result == ["AAA", "MMM", "ZZZ"]
