"""Integration test for TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE Step 3
(corrected call site).

`StrategicIntelligenceSystem.evaluate_all_strategic_intents()` (intelligence.py:884-929), the
function plan.md's Step 3 originally targeted, is NOT wired into the live tick pipeline anywhere
in `src/` -- confirmed by a repo-wide grep during Implement. The actual live strategic-intelligence
merge site is `StrategicIntelligenceSystem.fused_strategic_pass()`
(intelligence.py:291-642), wired via `src/engine/pipeline.py:333`
(`run_phase("strategic_intelligence", update, lambda u:
StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))`). This test proves
AC2/AC3's real requirement against the actually-live code path: a winning ADVENTURE_ROUTE
candidate's materialization produces a committed `EntityUpdate` carrying
`last_routing_family`/`last_routing_tick` in `property_updates` when driven through
`fused_strategic_pass()`, not just the dead `evaluate_all_strategic_intents()` path (still covered
separately by `test_evaluate_all_strategic_intents_routing_family.py` since that function remains
real, callable code even though unreferenced by the pipeline).
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


def _fake_decide_factory(raw_score, family, target_node_id=None):
    def _fake_decide(entity, candidates, tick=0, resource_nodes=None, faction_directives=None, factions=None):
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


def test_fused_strategic_pass_property_updates_carries_last_routing_family(monkeypatch):
    monkeypatch.setattr(
        "src.ai.goals.adventure_scorer._supports_adventure_routing",
        lambda entity, cache: True,
    )
    monkeypatch.setattr(
        AdventureDecisionService, "decide",
        _fake_decide_factory(2.0, family=RouteFamily.TAKE_EASY_QUEST, target_node_id=777),
    )
    hero = _entity(eid=1)
    tick = 42
    state = AuthoritativeState(tick=tick, seed=42, entities={1: hero}, town_center=(50.0, 50.0))
    update = StateUpdate(force_full_scan=True)
    cadence = SystemCadence(strategic_intelligence=1, concern_evaluation=1)

    result = StrategicIntelligenceSystem.fused_strategic_pass(state, update, cadence=cadence)

    assert 1 in result.entity_updates
    ent_upd = result.entity_updates[1]
    assert ent_upd.property_updates.get("last_routing_family") == "take_easy_quest"
    assert ent_upd.property_updates.get("last_routing_tick") == tick
    assert ent_upd.strategic is not None
    assert ent_upd.strategic.last_routing_family_set == "take_easy_quest"
