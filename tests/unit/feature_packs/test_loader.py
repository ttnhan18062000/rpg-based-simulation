"""Tests for FeaturePackLoader (E63C)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.domains.feature_packs.loader import FeaturePackLoader
from src.domains.feature_packs.profile import RuntimeProfile
from src.domains.feature_packs.registry import FeatureRegistry


DEMO_PACK_DIR = Path("content/packs")


# ── basic discovery ───────────────────────────────────────────────────────────

def test_load_empty_profile_returns_empty_registries():
    profile = RuntimeProfile(active_pack_names=[])
    registries = FeaturePackLoader.load(profile, DEMO_PACK_DIR)
    assert registries == {}


def test_load_demo_escort_pack_registers_escort_dignitary():
    profile = RuntimeProfile(active_pack_names=["demo_escort_pack"])
    registries = FeaturePackLoader.load(profile, DEMO_PACK_DIR)
    assert "adventure_routing" in registries
    cls = registries["adventure_routing"].lookup("ESCORT_DIGNITARY")
    assert cls is not None
    assert cls.__name__ == "EscortDignitaryGenerator"


def test_load_skips_pack_not_in_active_names():
    profile = RuntimeProfile(active_pack_names=["some_other_pack"])
    registries = FeaturePackLoader.load(profile, DEMO_PACK_DIR)
    # demo_escort_pack is not activated — no registries should be created
    assert "adventure_routing" not in registries


def test_load_escort_key_in_list_all():
    profile = RuntimeProfile(active_pack_names=["demo_escort_pack"])
    registries = FeaturePackLoader.load(profile, DEMO_PACK_DIR)
    keys = registries["adventure_routing"].list_all()
    assert "ESCORT_DIGNITARY" in keys


def test_load_nonexistent_manifest_dir_returns_empty():
    profile = RuntimeProfile(active_pack_names=["demo_escort_pack"])
    registries = FeaturePackLoader.load(profile, Path("content/nonexistent_packs"))
    assert registries == {}


def test_load_extends_existing_registries():
    profile = RuntimeProfile(active_pack_names=["demo_escort_pack"])
    existing: dict[str, FeatureRegistry] = {"world_emergence": FeatureRegistry()}
    registries = FeaturePackLoader.load(profile, DEMO_PACK_DIR, registries=existing)
    # Original domain preserved
    assert "world_emergence" in registries
    # New domain added
    assert "adventure_routing" in registries


def test_escort_dignitary_generator_generate():
    """Smoke-test: generator class is callable and returns a route payload."""
    from content.packs.demo_escort_pack.generator import EscortDignitaryGenerator
    payload = EscortDignitaryGenerator.generate(context=None)
    assert payload["family"] == "ESCORT_DIGNITARY"
    assert 0.0 <= payload["score"] <= 1.0
