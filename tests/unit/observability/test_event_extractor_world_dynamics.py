"""Unit tests for EventExtractor WORLD-DYNAMICS event emission (TCK-20260701-SIMQ-EMIT-WORLD-DYNAMICS).

Tests for: ecology_cycle_completed, spawn_cadence_fired, threat_evolved, node_recharged.
camp_constructed is blocked (CampService has no event recorder).

building_sabotaged added by TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL.
"""
from __future__ import annotations
from unittest.mock import MagicMock, patch

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _entity(eid: int = 1, kind: str = "hero"):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    e.combat = MagicMock(); e.combat.hp = 100; e.combat.max_hp = 100
    e.lifecycle = MagicMock(); e.lifecycle.active = True
    e.navigation = MagicMock(); e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock(); e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0; e.identity.evolution_level = 1
    e.identity.learned_skills = frozenset(); e.identity.traits = frozenset()
    e.identity.active_breakthroughs = frozenset(); e.identity.unspent_ap = 0
    e.strategic = MagicMock()
    e.strategic.projects = {}; e.strategic.leads = {}
    e.strategic.current_project_id = None; e.strategic.concerns = {}
    e.group_id = None
    return e


def _region(region_id: str, trauma_score: float = 0.0):
    r = MagicMock()
    r.region_id = region_id
    r.trauma_score = trauma_score
    return r


def _node(node_id: str, remaining_charges: int = 0, max_charges: int = 10):
    n = MagicMock()
    n.node_id = node_id
    n.remaining_charges = remaining_charges
    n.max_charges = max_charges
    return n


def _state(entities: dict, tick: int = 0, regions: dict | None = None,
           resource_nodes: dict | None = None):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.regions = regions or {}
    s.resource_nodes = resource_nodes or {}
    s.factions = {}
    return s


def _update(world_updates=None, entities_add=None, building_updates=None):
    u = MagicMock()
    u.entity_updates = {}
    u.world_updates = world_updates or {}
    u.last_calamity_tick_set = None
    u.entities_add = entities_add or []
    u.faction_updates = []
    u.world_events_add = []
    u.building_updates = building_updates or {}
    return u


def _world_upd(trauma_delta: float = 0.0, prior_trauma: float = 0.0):
    w = MagicMock()
    w.trauma_delta = trauma_delta
    w.prior_trauma = prior_trauma
    return w


def _building_upd(hp_delta: float = 0.0, functional_set=None):
    b = MagicMock()
    b.hp_delta = hp_delta
    b.functional_set = functional_set
    return b


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def reset_extractor():
    EventExtractor.reset_run_state()
    yield
    EventExtractor.reset_run_state()


# ── ecology_cycle_completed ────────────────────────────────────────────────────

class TestEcologyCycleCompleted:
    def test_fires_at_tick_200_with_regions(self):
        entity = _entity()
        region = _region("r1", trauma_score=0.0)
        events = EventExtractor.extract(
            _state({1: entity}, tick=200, regions={"r1": region}),
            _state({1: entity}, tick=200, regions={"r1": region}),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "ecology_cycle_completed" in _types(events)

    def test_fires_once_per_region_at_cycle_tick(self):
        entity = _entity()
        regions = {"r1": _region("r1"), "r2": _region("r2")}
        events = EventExtractor.extract(
            _state({1: entity}, tick=200, regions=regions),
            _state({1: entity}, tick=200, regions=regions),
            _update(), ObservabilityMode.NORMAL,
        )
        cycle_evts = [e for e in events if e.event_type == "ecology_cycle_completed"]
        assert len(cycle_evts) == 2

    def test_not_fired_at_non_cycle_tick(self):
        entity = _entity()
        region = _region("r1")
        events = EventExtractor.extract(
            _state({1: entity}, tick=201, regions={"r1": region}),
            _state({1: entity}, tick=201, regions={"r1": region}),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "ecology_cycle_completed" not in _types(events)

    def test_not_fired_with_no_regions(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}, tick=200),
            _state({1: entity}, tick=200),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "ecology_cycle_completed" not in _types(events)


# ── spawn_cadence_fired ────────────────────────────────────────────────────────

class TestSpawnCadrenceFired:
    def _spawn_entity(self, kind: str = "hero"):
        e = MagicMock()
        e.kind = kind
        return e

    def test_fires_at_tick_50_with_non_boss_spawn(self):
        entity = _entity()
        spawned = self._spawn_entity("wolf")
        events = EventExtractor.extract(
            _state({1: entity}, tick=50),
            _state({1: entity}, tick=50),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        assert "spawn_cadence_fired" in _types(events)

    def test_not_fired_for_boss_spawn(self):
        entity = _entity()
        spawned = self._spawn_entity("world_boss")
        events = EventExtractor.extract(
            _state({1: entity}, tick=50),
            _state({1: entity}, tick=50),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        assert "spawn_cadence_fired" not in _types(events)

    def test_not_fired_for_lair_occupant_spawn(self):
        """TCK-20260904-LAIR-ENTITY-ANCHOR: dragonkin Lair occupants are boss-tier
        spawns, excluded from spawn_cadence_fired just like world_boss/ancient_sentinel."""
        entity = _entity()
        spawned = self._spawn_entity("dragonkin")
        events = EventExtractor.extract(
            _state({1: entity}, tick=50),
            _state({1: entity}, tick=50),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        assert "spawn_cadence_fired" not in _types(events)

    def test_not_fired_at_non_cadence_tick(self):
        entity = _entity()
        spawned = self._spawn_entity("wolf")
        events = EventExtractor.extract(
            _state({1: entity}, tick=51),
            _state({1: entity}, tick=51),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        assert "spawn_cadence_fired" not in _types(events)

    def test_not_fired_without_spawned_entities(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}, tick=50),
            _state({1: entity}, tick=50),
            _update(entities_add=[]), ObservabilityMode.NORMAL,
        )
        assert "spawn_cadence_fired" not in _types(events)


# ── threat_evolved ─────────────────────────────────────────────────────────────

class TestThreatEvolved:
    def test_fires_when_trauma_crosses_25_threshold(self):
        entity = _entity()
        region = _region("r1", trauma_score=20.0)
        w_upd = _world_upd(trauma_delta=10.0, prior_trauma=20.0)
        events = EventExtractor.extract(
            _state({1: entity}, regions={"r1": region}),
            _state({1: entity}, regions={"r1": region}),
            _update(world_updates={"r1": w_upd}), ObservabilityMode.NORMAL,
        )
        assert "threat_evolved" in _types(events)

    def test_not_fired_when_trauma_stays_below_threshold(self):
        entity = _entity()
        region = _region("r1", trauma_score=10.0)
        w_upd = _world_upd(trauma_delta=5.0, prior_trauma=10.0)
        events = EventExtractor.extract(
            _state({1: entity}, regions={"r1": region}),
            _state({1: entity}, regions={"r1": region}),
            _update(world_updates={"r1": w_upd}), ObservabilityMode.NORMAL,
        )
        assert "threat_evolved" not in _types(events)

    def test_not_fired_when_trauma_decreases(self):
        entity = _entity()
        region = _region("r1", trauma_score=80.0)
        w_upd = _world_upd(trauma_delta=-10.0, prior_trauma=80.0)
        events = EventExtractor.extract(
            _state({1: entity}, regions={"r1": region}),
            _state({1: entity}, regions={"r1": region}),
            _update(world_updates={"r1": w_upd}), ObservabilityMode.NORMAL,
        )
        assert "threat_evolved" not in _types(events)


# ── node_recharged ─────────────────────────────────────────────────────────────

class TestNodeRecharged:
    def test_fires_when_node_charges_go_from_zero_to_positive(self):
        entity = _entity()
        prior_node = _node("n1", remaining_charges=0)
        curr_node = _node("n1", remaining_charges=5)
        events = EventExtractor.extract(
            _state({1: entity}, resource_nodes={"n1": prior_node}),
            _state({1: entity}, resource_nodes={"n1": curr_node}),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "node_recharged" in _types(events)

    def test_not_fired_when_node_already_had_charges(self):
        entity = _entity()
        prior_node = _node("n1", remaining_charges=3)
        curr_node = _node("n1", remaining_charges=8)
        events = EventExtractor.extract(
            _state({1: entity}, resource_nodes={"n1": prior_node}),
            _state({1: entity}, resource_nodes={"n1": curr_node}),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "node_recharged" not in _types(events)

    def test_not_fired_when_node_depletes(self):
        entity = _entity()
        prior_node = _node("n1", remaining_charges=5)
        curr_node = _node("n1", remaining_charges=0)
        events = EventExtractor.extract(
            _state({1: entity}, resource_nodes={"n1": prior_node}),
            _state({1: entity}, resource_nodes={"n1": curr_node}),
            _update(), ObservabilityMode.NORMAL,
        )
        assert "node_recharged" not in _types(events)


# ── building_sabotaged ──────────────────────────────────────────────────────────

class TestBuildingSabotaged:
    def test_emitted_on_negative_hp_delta(self):
        entity = _entity()
        b_upd = _building_upd(hp_delta=-50, functional_set=True)
        region = _region("r1")
        region.id = "r1"
        with patch(
            "src.engine.spatial_query.SpatialQueryService.get_building_region",
            return_value=region,
        ):
            events = EventExtractor.extract(
                _state({1: entity}),
                _state({1: entity}),
                _update(building_updates={7: b_upd}), ObservabilityMode.NORMAL,
            )
        sabotage_evts = [e for e in events if e.event_type == "building_sabotaged"]
        assert len(sabotage_evts) == 1
        assert sabotage_evts[0].payload["building_id"] == 7
        assert sabotage_evts[0].payload["hp_delta"] == -50
        assert sabotage_evts[0].payload["region_id"] == "r1"

    def test_not_emitted_on_functional_only_update(self):
        entity = _entity()
        b_upd = _building_upd(hp_delta=0, functional_set=False)
        events = EventExtractor.extract(
            _state({1: entity}),
            _state({1: entity}),
            _update(building_updates={7: b_upd}), ObservabilityMode.NORMAL,
        )
        assert "building_sabotaged" not in _types(events)

    def test_not_emitted_on_positive_hp_delta(self):
        entity = _entity()
        b_upd = _building_upd(hp_delta=25, functional_set=True)
        events = EventExtractor.extract(
            _state({1: entity}),
            _state({1: entity}),
            _update(building_updates={7: b_upd}), ObservabilityMode.NORMAL,
        )
        assert "building_sabotaged" not in _types(events)


# ── boss_spawned ────────────────────────────────────────────────────────────────

class TestBossSpawned:
    def _spawn_entity(self, kind: str, eid: int = 7):
        e = MagicMock()
        e.id = eid
        e.kind = kind
        return e

    def test_emitted_for_dragonkin_lair_occupant(self):
        """TCK-20260904-LAIR-ENTITY-ANCHOR: dragonkin Lair occupants are classified as
        boss-tier spawns by _BOSS_KINDS, same as world_boss/ancient_sentinel."""
        entity = _entity()
        spawned = self._spawn_entity("dragonkin")
        events = EventExtractor.extract(
            _state({1: entity}),
            _state({1: entity}),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        boss_evts = [e for e in events if e.event_type == "boss_spawned"]
        assert len(boss_evts) == 1
        assert boss_evts[0].payload["kind"] == "dragonkin"

    def test_not_emitted_for_non_boss_kind(self):
        entity = _entity()
        spawned = self._spawn_entity("wolf")
        events = EventExtractor.extract(
            _state({1: entity}),
            _state({1: entity}),
            _update(entities_add=[spawned]), ObservabilityMode.NORMAL,
        )
        assert "boss_spawned" not in _types(events)
