"""PartnerCandidateIndex must give exactly the tuple the exhaustive per-requester scan gave
(TCK-20261023-COOPERATION-CANDIDATES-ENUMERATED-PER-ENTITY-PER-TICK).

``_legacy_get_candidates`` is the pre-index implementation kept verbatim as the reference.
"""
import random

import pytest

from src.content_semantics.faction import are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.domains.cooperation.providers import CandidateBudget, PartnerCandidate, PartnerCandidateProvider

FACTIONS = {
    "goblin_warband": Faction.MONSTER_HORDE,
    "orc_clan": Faction.MONSTER_HORDE,
    "hero_guild": Faction.HERO_GUILD,
    "town_council": Faction.TOWN_COUNCIL,
    "neutral": Faction.NEUTRAL,
}


def _legacy_get_candidates(entity, state, budget):
    candidates = []
    my_pos = entity.navigation.position
    for cand_id, cand in state.entities.items():
        if cand_id == entity.id:
            continue
        if not cand.lifecycle.active or not cand.combat.alive:
            continue
        manhattan = abs(my_pos[0] - cand.navigation.position[0]) + abs(my_pos[1] - cand.navigation.position[1])
        if are_entities_hostile(entity, cand, RelationContext(distance=float(manhattan), combat_engaged=True)):
            if cand.identity.role != 1:
                continue
        c_pos = cand.navigation.position
        dx = my_pos[0] - c_pos[0]
        dy = my_pos[1] - c_pos[1]
        if abs(dx) > budget.spatial_radius or abs(dy) > budget.spatial_radius:
            trust = entity.social.trust_history.get(cand_id, 0.5)
            if trust <= 0.7:
                continue
            dist = (dx**2 + dy**2)**0.5
        else:
            dist = (dx**2 + dy**2)**0.5
        trust = entity.social.trust_history.get(cand_id, 0.5)
        familiarity = entity.social.familiarity_history.get(cand_id, 0.0)
        if dist <= budget.spatial_radius or trust > 0.7:
            availability = 1.0 - (dist / budget.spatial_radius) if dist > 0.0 else 1.0
            availability = max(0.1, min(availability, 1.0))
            if cand.strategic.contracts:
                availability = max(0.05, availability - 0.3)
            role_fit = 0.5
            if cand.combat.tactical_role == "SUPPORT":
                role_fit = 0.8
            elif cand.combat.tactical_role == "VANGUARD":
                role_fit = 0.7
            cost = 20 if cand.identity.role == 1 else 0
            grudge = entity.social.grudge_history.get(cand_id, 0.0)
            risk_pen = grudge * 0.5
            reason_str = "Within spatial radius" if dist <= budget.spatial_radius else "Highly trusted ally"
            candidates.append(PartnerCandidate(
                entity_id=cand_id, relationship_score=familiarity, trust_score=trust,
                role_fit_score=role_fit, availability_score=availability, cost_gold=cost,
                risk_penalty=risk_pen, reason=reason_str))
    candidates.sort(key=lambda x: (x.trust_score * 0.4 + x.role_fit_score * 0.3 + x.availability_score * 0.3 - x.risk_penalty), reverse=True)
    return tuple(candidates[:budget.max_candidates])


def _make_state(rng, n, span):
    ids = list(range(1, n + 1))
    rng.shuffle(ids)  # insertion order differs from id order: ties must keep state order
    ents = []
    for eid in ids:
        fid = rng.choice(list(FACTIONS))
        alive = rng.random() > 0.15
        # Integer and fractional positions, including negatives and exact radius boundaries.
        x = rng.choice([rng.randint(-span, span), rng.uniform(-span, span), 15.0, -15.0, 0.0])
        y = rng.choice([rng.randint(-span, span), rng.uniform(-span, span), 15.0, -15.0, 0.0])
        role = 1 if rng.random() < 0.15 else 0
        trole = rng.choice(["SUPPORT", "VANGUARD", "OTHER"]) if rng.random() < 0.3 else None
        e = (V2EntityBuilder(eid).kind("HERO").location(x, y)
             .identity(role=role, faction=FACTIONS[fid], properties={"faction_id": fid})
             .combat(hp=100 if alive else 0, max_hp=100, atk=20, def_stat=5, attack_range=10, readiness=100.0,
                     alive=alive, tactical_role=trole)
             .lifecycle(active=rng.random() > 0.1)
             .build())
        ents.append(e)
    for e in ents:
        for other in rng.sample(ents, min(8, len(ents))):
            e.social.trust_history[other.id] = rng.choice([0.2, 0.5, 0.7, 0.71, 0.9])
            e.social.familiarity_history[other.id] = rng.random()
            if rng.random() < 0.3:
                e.social.grudge_history[other.id] = rng.random()
    return AuthoritativeState(entities={e.id: e for e in ents}, tick=1, seed=7)


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("radius,span", [(15.0, 40), (15.0, 12), (7.5, 30), (4.0, 10)])
def test_index_matches_exhaustive_scan(seed, radius, span):
    rng = random.Random(seed * 101 + int(radius))
    state = _make_state(rng, 60, span)
    for max_c in (5, 100):
        budget = CandidateBudget(max_candidates=max_c, spatial_radius=radius)
        index = PartnerCandidateProvider.build_index(state, budget)
        for entity in state.entities.values():
            want = _legacy_get_candidates(entity, state, budget)
            assert PartnerCandidateProvider.get_candidates(entity, state, (), budget, index) == want
            assert PartnerCandidateProvider.get_candidates(entity, state, (), budget) == want


def test_index_with_other_radius_is_not_used():
    rng = random.Random(3)
    state = _make_state(rng, 30, 20)
    stale = PartnerCandidateProvider.build_index(state, CandidateBudget(spatial_radius=4.0))
    budget = CandidateBudget(spatial_radius=15.0)
    for entity in state.entities.values():
        assert (PartnerCandidateProvider.get_candidates(entity, state, (), budget, stale)
                == _legacy_get_candidates(entity, state, budget))
