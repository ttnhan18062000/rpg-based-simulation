"""Tests for MotivationBiasService culture_values extension (E62C)."""

from dataclasses import replace

from src.core.cognition import CognitionModel, IdentityDoctrine, MotivationModel
from src.core.state import EntityState
from src.domains.culture.model import CultureState
from src.domains.motivation.service import MotivationBiasService


def _entity(preferred: dict | None = None, avoided: dict | None = None) -> EntityState:
    doctrine = IdentityDoctrine(
        class_id="warrior",
        preferred_route_tags=preferred or {},
        avoided_route_tags=avoided or {},
    )
    cognition = CognitionModel(motivation=MotivationModel(doctrine=doctrine))
    return replace(EntityState(id=1, kind="HERO"), cognition=cognition)


def test_compute_bias_multiplier_no_culture_unchanged():
    entity = _entity(preferred={"caution": 0.3})
    tags = ["caution"]
    # Baseline: no culture_values → same as pre-E62C behaviour
    result_without = MotivationBiasService.compute_bias_multiplier(entity, tags)
    result_none = MotivationBiasService.compute_bias_multiplier(entity, tags, culture_values=None)
    assert result_without == result_none


def test_compute_bias_multiplier_with_zero_culture_unchanged():
    entity = _entity()
    tags = ["caution"]
    without = MotivationBiasService.compute_bias_multiplier(entity, tags)
    with_zero = MotivationBiasService.compute_bias_multiplier(
        entity, tags, culture_values=CultureState()
    )
    assert without == with_zero


def test_compute_bias_multiplier_with_fatalism_raises_caution():
    entity = _entity()
    tags = ["caution"]
    without = MotivationBiasService.compute_bias_multiplier(entity, tags)
    with_culture = MotivationBiasService.compute_bias_multiplier(
        entity, tags, culture_values=CultureState(fatalism=0.8)
    )
    assert with_culture > without


def test_compute_bias_multiplier_result_at_least_0_1():
    entity = _entity(avoided={"caution": 5.0})  # heavy penalty to drive multiplier low
    tags = ["caution"]
    result = MotivationBiasService.compute_bias_multiplier(
        entity, tags, culture_values=CultureState(fatalism=0.8)
    )
    assert result >= 0.1
