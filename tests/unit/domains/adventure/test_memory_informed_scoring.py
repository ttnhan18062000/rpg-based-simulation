"""Tests for AdventureRouteScorer memory-informed advice adjustment
(TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING).

Only 2 of the 10 real, reachable CausalMemoryEntry.future_advice values are mapped
in this pass: "avoid_enemy" (combat_loss fallback) suppresses HUNT_WEAK_ENEMY, and
"boost_party_trust" (party_abandoned) promotes FORM_PARTY. See
docs/mechanics/04_strategic_cognition.md §6.11 and
docs/parity_ledger/strategic_cognition.yaml STRAT-227 for the documented mapping.

Note: HUNT_WEAK_ENEMY is confirmed dead code in AdventureRouteGenerator.generate()
(docs/simulation/domains/adventure_contract.md) — the suppression tested here is
provably correct at the AdventureRouteScorer.score() unit level, but has zero
observable effect via a live generate() -> score() call chain today, since
generator.py never emits a HUNT_WEAK_ENEMY candidate.
"""

from src.core.builder import V2EntityBuilder
from src.core.cognition import CausalMemory, CausalMemoryEntry, CognitionModel, MemoryModel
from src.core.enums import EntityRole
from src.core.self_model import (
    KnowledgeModelComponent,
    NeedInterpretationComponent,
    SelfAwarenessComponent,
    SelfModelBundle,
)
from src.core.state import BiologicalComponent, CombatComponent
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
from src.domains.adventure.scoring import AdventureRouteScorer


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_entity(role: EntityRole = EntityRole.HERO, causal_entries=()) -> object:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(role=role, traits=set())
    b.replace_self_model(SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={"health": 1.0}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    ))
    b.replace_cognition(CognitionModel(
        memory=MemoryModel(causal=CausalMemory(entries=causal_entries))
    ))
    return b.build()


def _route(family: RouteFamily, benefit: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=family,
        score=0.0,
        confidence=0.8,
        expected_benefit=benefit,
        expected_risk=0.1,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_avoid_enemy_advice_suppresses_hunt_weak_enemy_score():
    """avoid_enemy after combat_loss suppresses HUNT_WEAK_ENEMY (Design Decision 1).

    HUNT_WEAK_ENEMY is confirmed dead code in AdventureRouteGenerator.generate() —
    this test proves the suppression is correct at the score() unit level, but it
    has no observable effect via a live generate() -> score() chain today.
    """
    entry = CausalMemoryEntry(
        event_id="e1",
        event_kind="combat_loss",
        interpreted_causes=("strong_enemy",),
        confidence=0.8,
        future_advice=("avoid_enemy",),
        tick=1,
    )
    entity_with_memory = _build_entity(causal_entries=(entry,))
    entity_without_memory = _build_entity(causal_entries=())
    route = _route(RouteFamily.HUNT_WEAK_ENEMY)

    result_with_memory = AdventureRouteScorer.score(entity_with_memory, route)
    result_without_memory = AdventureRouteScorer.score(entity_without_memory, route)

    assert result_with_memory.memory_adjustment == -1.0
    assert result_without_memory.memory_adjustment == 0.0
    assert result_with_memory.score < result_without_memory.score


def test_boost_party_trust_advice_promotes_form_party_score():
    """boost_party_trust after party_abandoned promotes FORM_PARTY (Design Decision 1)."""
    entry = CausalMemoryEntry(
        event_id="e2",
        event_kind="party_abandoned",
        interpreted_causes=("grudge_decay", "cohesion_lost"),
        confidence=0.8,
        future_advice=("boost_party_trust", "realign_directive"),
        tick=1,
    )
    entity_with_memory = _build_entity(causal_entries=(entry,))
    entity_without_memory = _build_entity(causal_entries=())
    route = _route(RouteFamily.FORM_PARTY)

    result_with_memory = AdventureRouteScorer.score(entity_with_memory, route)
    result_without_memory = AdventureRouteScorer.score(entity_without_memory, route)

    assert result_with_memory.memory_adjustment == 1.0
    assert result_without_memory.memory_adjustment == 0.0
    assert result_with_memory.score > result_without_memory.score


def test_no_matching_causal_memory_is_a_no_op():
    """A causal entry whose future_advice does not match either mapped string is a no-op."""
    entry = CausalMemoryEntry(
        event_id="e3",
        event_kind="combat_loss",
        interpreted_causes=("low_health",),
        confidence=0.8,
        future_advice=("heal_first",),
        tick=1,
    )
    entity_with_unmapped_memory = _build_entity(causal_entries=(entry,))
    entity_without_memory = _build_entity(causal_entries=())
    route = _route(RouteFamily.HUNT_WEAK_ENEMY)

    result_unmapped = AdventureRouteScorer.score(entity_with_unmapped_memory, route)
    result_empty = AdventureRouteScorer.score(entity_without_memory, route)

    assert result_unmapped.memory_adjustment == 0.0
    assert result_unmapped.score == result_empty.score


def test_future_advice_tuple_with_multiple_values_handled():
    """A 2-element future_advice tuple triggers the mapping via membership, not future_advice[0]."""
    entry = CausalMemoryEntry(
        event_id="e4",
        event_kind="party_abandoned",
        interpreted_causes=("grudge_decay", "cohesion_lost"),
        confidence=0.8,
        future_advice=("boost_party_trust", "realign_directive"),
        tick=1,
    )
    entity = _build_entity(causal_entries=(entry,))
    route = _route(RouteFamily.FORM_PARTY)

    result = AdventureRouteScorer.score(entity, route)

    assert result.memory_adjustment == 1.0


def test_memory_term_does_not_mutate_entity_cognition():
    """score() must remain fully read-only with respect to entity.cognition."""
    entry = CausalMemoryEntry(
        event_id="e5",
        event_kind="combat_loss",
        interpreted_causes=("strong_enemy",),
        confidence=0.8,
        future_advice=("avoid_enemy",),
        tick=1,
    )
    entity = _build_entity(causal_entries=(entry,))
    entity_cognition_before = entity.cognition
    route = _route(RouteFamily.HUNT_WEAK_ENEMY)

    AdventureRouteScorer.score(entity, route)

    assert entity.cognition is entity_cognition_before


def test_memory_term_reads_only_entity_local_state():
    """The memory term's computation involves only `entity`, no state-derived argument.

    score()'s signature already has no `state` parameter; this confirms the memory
    term's logic added in Step 2 is exercised correctly with only entity/route passed,
    no resource_nodes/quest_registry/group/faction_directives/factions/progression_plan.
    """
    entry = CausalMemoryEntry(
        event_id="e6",
        event_kind="party_abandoned",
        interpreted_causes=("grudge_decay", "cohesion_lost"),
        confidence=0.8,
        future_advice=("boost_party_trust", "realign_directive"),
        tick=1,
    )
    entity = _build_entity(causal_entries=(entry,))
    route = _route(RouteFamily.FORM_PARTY)

    result = AdventureRouteScorer.score(
        entity,
        route,
        resource_nodes=None,
        quest_registry=None,
        group=None,
        faction_directives=None,
        factions=None,
        progression_plan=None,
    )

    assert result.memory_adjustment == 1.0


def test_capacity_evicted_causal_entries_do_not_affect_scoring():
    """score() only ever sees entries passed on entity.cognition.memory.causal.entries.

    Simulates post-eviction state (the matching entry has already fallen out of the
    30-entry FIFO buffer) — no independent history lookup exists, so no adjustment fires.
    """
    surviving_entry = CausalMemoryEntry(
        event_id="e7",
        event_kind="failed_search",
        interpreted_causes=("no_leads",),
        confidence=0.6,
        future_advice=("seek_trusted_guide", "verify_intel"),
        tick=100,
    )
    entity = _build_entity(causal_entries=(surviving_entry,))
    route_hunt = _route(RouteFamily.HUNT_WEAK_ENEMY)
    route_party = _route(RouteFamily.FORM_PARTY)

    result_hunt = AdventureRouteScorer.score(entity, route_hunt)
    result_party = AdventureRouteScorer.score(entity, route_party)

    assert result_hunt.memory_adjustment == 0.0
    assert result_party.memory_adjustment == 0.0
