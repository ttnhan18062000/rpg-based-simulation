"""
tests/integration/domains/information/test_phase5_branch_b_realworld.py

TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE — real-world regression guard.

Prior to this ticket's fix, InformationQueryRouter.route() +
InformationIntentResolver.resolve() against urban_political's real compiled state
(actor_id 23, 0 gold) dead-ended: candidates[0] (traveling_merchant_rumors, cost=5)
resolved to None on the affordability gate, and InformationBeliefPhase.apply()'s
Branch B never tried candidates[1] (town_notice_board, cost=0, free). This test
proves the fix (phase-level fallback + structured insufficient_gold signal) makes
Branch B route successfully end-to-end against the real compiled world, across all
3 anchor seeds — not just a hand-built single-candidate scenario.
"""
from __future__ import annotations

from dataclasses import replace as dataclass_replace

import pytest

from src.worldbuilding.schema import load_world_spec_from_yaml
from src.worldbuilding.compiler import WorldCompiler
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.domains.information.phase import InformationBeliefPhase


@pytest.mark.parametrize("seed", [42, 123, 456])
def test_branch_b_query_routing_fails_silently_on_real_urban_political_state(seed: int):
    """Post-fix: Branch B resolves a real ASK_INFORMATION query for entity 23 (0 gold)
    against urban_political's real compiled state, for at least one of the two available
    candidates, seed-invariantly. (Test name retained from the parent investigation's
    test_plan.md — assertion flipped from the pre-fix "dead-ends silently" finding to a
    post-fix success confirmation, per that plan's own instruction.)"""
    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=seed)

    actor = state.entities[23]
    assert actor.inventory.gold == 0, "regression guard assumes entity 23 starts with 0 gold"

    unk = UnknownFact(subject="material.moon_resin.source", reason="provider_unknown", recorded_tick=0)
    km = KnowledgeModelComponent(unknowns={"material.moon_resin.source": unk})
    actor_with_unknown = dataclass_replace(actor, self_model=SelfModelBundle(knowledge=km))
    state = dataclass_replace(state, entities={**state.entities, 23: actor_with_unknown})

    update = InformationBeliefPhase.apply(state, state.information_source_profiles)

    assert 23 in update.entity_updates, "expected Branch B to route a query for entity 23"
    eu = update.entity_updates[23]
    assert eu.property_updates.get("last_routed_query_subject") == "material.moon_resin.source"
    assert len(eu.intent_results) == 1
    intent = eu.intent_results[0]
    assert intent.kind == "ASK_INFORMATION"
    assert intent.target_id == "town_notice_board", "expected fallback to the free candidate"
    assert intent.payload.get("cost_paid") == 0
