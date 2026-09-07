"""Integration test for TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE Step 3.

Exercises the OUTER refine loop, `StrategicIntelligenceSystem.evaluate_all_strategic_intents()`
(`intelligence.py:884-929`), which previously had zero test coverage. Proves AC2's literal
requirement -- a winning ADVENTURE_ROUTE candidate's materialization produces a committed
`EntityUpdate` carrying `last_routing_family`/`last_routing_tick` in `property_updates`, the exact
dict key names `event_shapers.py:751`/`event_extractor.py:~595` read.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.adventure.schema import AdventureDecisionResult, AdventureRouteOption, RouteFamily
from src.domains.adventure.service import AdventureDecisionService
from src.engine.cadence import SystemCadence
from src.systems.strategic import StrategicIntelligenceSystem


def _entity(eid: int = 1, pos: tuple = (0.0, 0.0)):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .build()
    )


def _state(entities=None, tick=10):
    return AuthoritativeState(
        tick=tick,
        seed=42,
        entities=entities or {},
        town_center=(50.0, 50.0),
    )


def _eligible(monkeypatch):
    monkeypatch.setattr(
        "src.ai.goals.adventure_scorer._supports_adventure_routing",
        lambda entity, cache: True,
    )


def _fake_decide_factory(raw_score, family, target_node_id=None):
    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None, culture_state=None):
        selected = AdventureRouteOption(
            family=family,
            score=raw_score,
            confidence=1.0,
            expected_benefit=0.5,
            expected_risk=0.0,
            target_node_id=target_node_id,
        )
        return AdventureDecisionResult(
            selected=selected, rejected=(), proposed_project=None, proposed_objective=None, trace={},
        )

    return _fake_decide


def test_adventure_route_win_property_updates_carries_last_routing_family(monkeypatch):
    _eligible(monkeypatch)
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.TAKE_EASY_QUEST, target_node_id=777),
    )
    hero = _entity(eid=1)
    tick = 42
    state = _state(entities={1: hero}, tick=tick)
    update = StateUpdate()
    # Cadence of 1 bypasses the (tick + entity_id) % cadence staggering so the entity is always
    # eligible this tick -- the default strategic_intelligence cadence is 10.
    cadence = SystemCadence(strategic_intelligence=1)

    result = StrategicIntelligenceSystem.evaluate_all_strategic_intents(state, update, cadence=cadence)

    assert 1 in result.entity_updates
    ent_upd = result.entity_updates[1]
    assert ent_upd.property_updates["last_routing_family"] == "take_easy_quest"
    assert ent_upd.property_updates["last_routing_tick"] == tick
    # Also confirm the StrategicUpdate-level field made it through the merge, not just
    # property_updates (both must stay in sync -- Step 1 + Step 3 together).
    assert ent_upd.strategic is not None
    assert ent_upd.strategic.last_routing_family_set == "take_easy_quest"
