"""Tests for CulturalBiasApplicator — axis-to-tag delta rules (E62C)."""

from src.domains.culture.applicator import CulturalBiasApplicator
from src.domains.culture.model import CultureState


def test_zero_culture_produces_zero_delta():
    cs = CultureState()
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["caution", "combat", "loyalty"])
    assert delta == 0.0


def test_high_fatalism_increases_caution_delta():
    cs = CultureState(fatalism=0.8)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["caution"])
    assert delta > 0.0


def test_high_fatalism_decreases_combat_delta():
    cs = CultureState(fatalism=0.8)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["combat"])
    assert delta < 0.0


def test_high_hero_veneration_increases_loyalty_delta():
    cs = CultureState(hero_veneration=0.7)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["loyalty"])
    assert delta > 0.0


def test_high_scarcity_memory_increases_survival_delta():
    cs = CultureState(resource_scarcity_memory=0.6)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["survival"])
    assert delta > 0.0


def test_high_conflict_exposure_increases_caution_delta():
    cs = CultureState(faction_conflict_exposure=0.9)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["caution"])
    assert delta > 0.0


def test_high_conflict_exposure_decreases_loyalty_delta():
    cs = CultureState(faction_conflict_exposure=0.9)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["loyalty"])
    assert delta < 0.0


def test_delta_bounded_upper():
    # Max possible: fatalism=1.0 with many positive tags + scarcity + conflict
    cs = CultureState(
        fatalism=1.0,
        hero_veneration=1.0,
        resource_scarcity_memory=1.0,
        faction_conflict_exposure=1.0,
    )
    tags = ["caution", "recovery", "flee", "survival", "loyalty", "party", "combat"]
    delta = CulturalBiasApplicator.compute_culture_delta(cs, tags)
    assert delta <= 1.0


def test_delta_bounded_lower():
    cs = CultureState(fatalism=1.0, faction_conflict_exposure=1.0)
    tags = ["pride", "combat", "aggressive", "loyalty"]
    delta = CulturalBiasApplicator.compute_culture_delta(cs, tags)
    assert delta >= -0.5


def test_below_threshold_no_effect():
    # Axis at exactly threshold boundary (0.3) — must NOT activate
    cs = CultureState(fatalism=0.3)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, ["caution"])
    assert delta == 0.0


def test_empty_tags_zero_delta():
    cs = CultureState(fatalism=1.0, hero_veneration=1.0)
    delta = CulturalBiasApplicator.compute_culture_delta(cs, [])
    assert delta == 0.0
