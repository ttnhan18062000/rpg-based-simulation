# tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py
import pytest
from src.core.state import AuthoritativeState, RegionState
from src.domains.world_emergence.schema import WorldEventAggregate, WorldEventCategory, RegionalPressure
from src.domains.world_emergence.models import RegionalPressureModel

def test_repeated_deaths_increase_danger_pressure():
    # Setup mock RegionStates to avoid KeyErrors
    regions = {"north_ruin": RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 10, 10))}
    state = AuthoritativeState(entities={}, regions=regions, tick=0, seed=0)

    aggs = (
        WorldEventAggregate(
            region_id="north_ruin",
            category=WorldEventCategory.ENTITY_DEATH,
            subject=None,
            count=3,
            severity_sum=3.0,
            first_tick=5,
            last_tick=15
        ),
    )

    pressures = RegionalPressureModel.evaluate(state, aggs)
    danger = next(p for p in pressures if p.pressure_kind == "danger")
    assert danger.intensity > 0.4
    assert "3 entity deaths" in danger.reason


# ---------------------------------------------------------------------------
# E21E — Cross-region pressure propagation tests
# ---------------------------------------------------------------------------

def _region(rid: str, xmin: int, ymin: int, xmax: int, ymax: int) -> RegionState:
    return RegionState(id=rid, name=rid, bounds=(xmin, ymin, xmax, ymax))


def _resource_pressure(region_id: str, intensity: float) -> RegionalPressure:
    return RegionalPressure(
        region_id=region_id,
        pressure_kind="resource",
        intensity=intensity,
        confidence=0.9,
        source_aggregates=("depleted:2",),
        reason="2 depleted nodes",
    )


def test_are_adjacent_overlapping_regions():
    r1 = _region("r1", 0, 0, 100, 100)
    r2 = _region("r2", 50, 50, 150, 150)  # overlapping → distance = 0
    assert RegionalPressureModel._are_adjacent(r1, r2) is True


def test_are_adjacent_touching_regions():
    r1 = _region("r1", 0, 0, 100, 100)
    r2 = _region("r2", 100, 0, 200, 100)  # share the x=100 border → hdist=0
    assert RegionalPressureModel._are_adjacent(r1, r2) is True


def test_are_adjacent_within_gap():
    r1 = _region("r1", 0, 0, 100, 100)
    r2 = _region("r2", 140, 0, 240, 100)  # hdist = 140-100 = 40 < 50
    assert RegionalPressureModel._are_adjacent(r1, r2) is True


def test_are_not_adjacent_too_far():
    r1 = _region("r1", 0, 0, 100, 100)
    r2 = _region("r2", 200, 0, 300, 100)  # hdist = 200-100 = 100 > 50
    assert RegionalPressureModel._are_adjacent(r1, r2) is False


def test_propagate_cross_region_no_effect_when_single_region():
    region_a = _region("a", 0, 0, 100, 100)
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a})
    pressures = (_resource_pressure("a", 0.8),)
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    # Only one region — no neighbours — pressure unchanged
    res = {p.region_id: p for p in result if p.pressure_kind == "resource"}
    assert res["a"].intensity == 0.8


def test_propagate_cross_region_adjacent_regions_receive_spread():
    region_a = _region("a", 0, 0, 100, 100)
    region_b = _region("b", 100, 0, 200, 100)  # touching — adjacent
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a, "b": region_b})
    # a has high resource pressure; b has none
    pressures = (_resource_pressure("a", 0.8),)
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    res = {p.region_id: p for p in result if p.pressure_kind == "resource"}
    # b should now have some propagated pressure
    assert "b" in res
    assert res["b"].intensity == pytest.approx(0.8 * 0.30, abs=1e-6)
    # b's reason mentions propagation
    assert "adjacent" in res["b"].reason.lower() or "propagated" in res["b"].reason.lower()


def test_propagate_cross_region_bidirectional():
    region_a = _region("a", 0, 0, 100, 100)
    region_b = _region("b", 100, 0, 200, 100)  # touching
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a, "b": region_b})
    # Both regions have resource pressure
    pressures = (
        _resource_pressure("a", 0.6),
        _resource_pressure("b", 0.4),
    )
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    res = {p.region_id: p for p in result if p.pressure_kind == "resource"}
    # a gets spread from b: 0.6 + 0.4*0.30 = 0.72
    assert res["a"].intensity == pytest.approx(0.6 + 0.4 * 0.30, abs=1e-6)
    # b gets spread from a: 0.4 + 0.6*0.30 = 0.58
    assert res["b"].intensity == pytest.approx(0.4 + 0.6 * 0.30, abs=1e-6)


def test_propagate_cross_region_no_spread_between_distant_regions():
    region_a = _region("a", 0, 0, 100, 100)
    region_b = _region("b", 200, 0, 300, 100)  # hdist=100 > ADJACENCY_GAP=50
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a, "b": region_b})
    pressures = (_resource_pressure("a", 0.9),)
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    res = {p.region_id: p for p in result if p.pressure_kind == "resource"}
    # b is too far — should not receive pressure
    assert "b" not in res


def test_propagate_cross_region_intensity_capped_at_one():
    region_a = _region("a", 0, 0, 100, 100)
    region_b = _region("b", 100, 0, 200, 100)
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a, "b": region_b})
    # Both at 1.0 — spread cannot push above 1.0
    pressures = (
        _resource_pressure("a", 1.0),
        _resource_pressure("b", 1.0),
    )
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    for p in result:
        if p.pressure_kind == "resource":
            assert p.intensity <= 1.0


def test_propagate_cross_region_non_resource_pressures_unchanged():
    region_a = _region("a", 0, 0, 100, 100)
    region_b = _region("b", 100, 0, 200, 100)
    state = AuthoritativeState(tick=100, seed=42, regions={"a": region_a, "b": region_b})
    danger_a = RegionalPressure(
        region_id="a", pressure_kind="danger", intensity=0.7,
        confidence=0.85, source_aggregates=("death:2",), reason="deaths",
    )
    pressures = (danger_a, _resource_pressure("a", 0.5))
    result = RegionalPressureModel.propagate_cross_region(pressures, state)
    danger_out = next(p for p in result if p.pressure_kind == "danger")
    assert danger_out.intensity == 0.7  # unchanged
