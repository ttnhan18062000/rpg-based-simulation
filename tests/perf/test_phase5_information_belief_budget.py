"""
tests/perf/test_phase5_information_belief_budget.py

Phase 5 — Performance budget gate test.
Benchmarks 100+ entities with strategic unknowns to verify update overhead is strictly <5ms.
"""

import time
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, UnknownFact
from src.domains.information.schema import InformationSourceProfile
from src.domains.information.phase import InformationBeliefPhase
from tests.tools.perf_assertions import assert_perf_threshold


def _entity(e_id, unknowns=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    b.location(0.0, 0.0)
    
    if unknowns:
        km = KnowledgeModelComponent(unknowns=unknowns)
        sm = SelfModelBundle(knowledge=km)
        b.replace_self_model(sm)
        
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def test_performance_budget_100_entities():
    unk = UnknownFact(subject="iron_ore", reason="test", recorded_tick=1)
    
    entities = []
    for i in range(1, 101):
        entities.append(_entity(i, unknowns={"iron_ore": unk}))
        
    state = _state(entities)
    
    profiles = [
        InformationSourceProfile(
            source_id=999,
            source_kind="guide",
            knowledge_scopes=("common_resource_sources",),
            accuracy=0.8,
            freshness=0.9,
        )
    ]
    
    # Warmup
    InformationBeliefPhase.apply(state, profiles)
    
    # Benchmark
    start = time.perf_counter()
    update = InformationBeliefPhase.apply(state, profiles)
    end = time.perf_counter()
    
    duration_ms = (end - start) * 1000.0
    print(f"\n100 Entities InformationBeliefPhase Update Time: {duration_ms:.4f} ms")

    assert_perf_threshold(duration_ms, 5.0, "InformationBeliefPhase update (100 entities)", op="<")
