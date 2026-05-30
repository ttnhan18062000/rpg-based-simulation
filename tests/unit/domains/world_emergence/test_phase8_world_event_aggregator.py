# tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py
import pytest
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.domains.world_emergence.aggregators import WorldEventAggregator

def test_deaths_aggregate_by_region():
    events = [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=10, region_id="north_ruin", severity=1.0),
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=12, region_id="north_ruin", severity=1.2),
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=15, region_id="south_forest", severity=0.8),
    ]
    
    aggs = WorldEventAggregator.aggregate(events, min_tick=5, max_tick=20)
    
    assert len(aggs) == 2
    
    north_agg = next(a for a in aggs if a.region_id == "north_ruin")
    assert north_agg.count == 2
    assert pytest.approx(north_agg.severity_sum) == 2.2
    assert north_agg.first_tick == 10
    assert north_agg.last_tick == 12

def test_resource_depletions_aggregate_by_resource_type():
    events = [
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=5, region_id="old_mine", subject="iron_ore"),
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=8, region_id="old_mine", subject="iron_ore"),
    ]
    
    aggs = WorldEventAggregator.aggregate(events, min_tick=0, max_tick=10)
    assert len(aggs) == 1
    assert aggs[0].count == 2
    assert aggs[0].subject == "iron_ore"

def test_low_salience_events_are_ignored():
    events = [
        WorldEvent(category=WorldEventCategory.RESOURCE_HARVESTED, tick=5, region_id="forest", subject="herb", severity=0.01),
        WorldEvent(category=WorldEventCategory.RESOURCE_HARVESTED, tick=8, region_id="forest", subject="herb", severity=0.8),
    ]
    
    aggs = WorldEventAggregator.aggregate(events, min_tick=0, max_tick=10)
    assert len(aggs) == 1
    assert aggs[0].count == 1
    assert aggs[0].severity_sum == 0.8
