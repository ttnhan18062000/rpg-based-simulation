"""Tests for SettlementPersonalityService — settlement-personality read-side consumer (idea 61)."""

from src.domains.culture.applicator import CULTURE_ACTIVATION_THRESHOLD
from src.domains.culture.model import CultureState
from src.domains.culture.settlement_personality import (
    SettlementPersonalityDescriptor,
    SettlementPersonalityService,
)


def test_describe_with_none_culture_returns_neutral_descriptor():
    descriptor = SettlementPersonalityService.describe(None)
    assert isinstance(descriptor, SettlementPersonalityDescriptor)
    assert descriptor.is_neutral is True
    assert descriptor.traits == ()
    assert descriptor.tag_deltas == {}


def test_describe_with_zero_axes_culture_returns_neutral_descriptor():
    descriptor = SettlementPersonalityService.describe(CultureState())
    assert descriptor.is_neutral is True
    assert descriptor.traits == ()
    assert all(delta == 0.0 for delta in descriptor.tag_deltas.values())


def test_describe_with_high_fatalism_axis_produces_fatalistic_signal():
    descriptor = SettlementPersonalityService.describe(CultureState(fatalism=0.8))
    assert descriptor.is_neutral is False
    assert "fatalistic" in descriptor.traits
    assert descriptor.tag_deltas["caution"] > 0.0
    assert descriptor.tag_deltas["combat"] < 0.0


def test_describe_with_high_hero_veneration_produces_hero_venerating_signal():
    descriptor = SettlementPersonalityService.describe(CultureState(hero_veneration=0.7))
    assert "hero_venerating" in descriptor.traits
    assert descriptor.tag_deltas["loyalty"] > 0.0


def test_describe_with_high_resource_scarcity_memory_produces_scarcity_scarred_signal():
    descriptor = SettlementPersonalityService.describe(
        CultureState(resource_scarcity_memory=0.6)
    )
    assert "scarcity_scarred" in descriptor.traits
    assert descriptor.tag_deltas["survival"] > 0.0


def test_describe_with_high_faction_conflict_exposure_produces_conflict_hardened_signal():
    descriptor = SettlementPersonalityService.describe(
        CultureState(faction_conflict_exposure=0.9)
    )
    assert "conflict_hardened" in descriptor.traits
    assert descriptor.tag_deltas["caution"] > 0.0
    assert descriptor.tag_deltas["loyalty"] < 0.0


def test_describe_below_threshold_axis_does_not_activate():
    descriptor = SettlementPersonalityService.describe(
        CultureState(fatalism=CULTURE_ACTIVATION_THRESHOLD)
    )
    assert descriptor.is_neutral is True
    assert "fatalistic" not in descriptor.traits


def test_describe_delta_bounded():
    saturated = CultureState(
        fatalism=1.0,
        hero_veneration=1.0,
        resource_scarcity_memory=1.0,
        faction_conflict_exposure=1.0,
    )
    descriptor = SettlementPersonalityService.describe(saturated)
    assert all(-0.5 <= delta <= 1.0 for delta in descriptor.tag_deltas.values())
    assert set(descriptor.tag_deltas.keys()) == {
        "caution", "recovery", "flee", "pride", "combat",
        "aggressive", "loyalty", "party", "survival",
    }
