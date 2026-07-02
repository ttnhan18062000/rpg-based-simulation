"""
E41H — Multi-hero party scenario: HERO-kind entities can form and lead parties.

Ticket: TCK-20260628-E41H-MULTI-HERO
Compliance: SOC-232 (composition-score cohesion), SOC-160 (contract-driven formation)

Verifies:
  1. Three HERO entities with an active recruitment network form a party.
  2. The 500-tick run completes without error.
  3. At least one group is formed during the run, led by a HERO-role entity.
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, PersonalityComponent
from src.core.strategic import (
    ContractState, ContractKind, ContractStatus, StrategicComponent,
)


# ── State builder ─────────────────────────────────────────────────────────────

def _hero(eid: int, x: float, y: float) -> "EntityState":
    """Minimal HERO entity with high sociability so FORM_PARTY routes generate."""
    personality = PersonalityComponent(bravery=0.7, sociability=0.8, greed=0.3, industry=0.4)
    contract_h1_h2 = ContractState(
        id="hero_pact_12", kind=ContractKind.RECRUITMENT,
        source_id=1, target_id=2, status=ContractStatus.ACTIVE,
    )
    contract_h1_h3 = ContractState(
        id="hero_pact_13", kind=ContractKind.RECRUITMENT,
        source_id=1, target_id=3, status=ContractStatus.ACTIVE,
    )
    contracts = {
        "hero_pact_12": contract_h1_h2,
        "hero_pact_13": contract_h1_h3,
    }
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(x, y)
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            evolution_level=3,
            personality=personality,
        )
        .combat(hp=100, max_hp=100, atk=20, def_stat=8, readiness=100.0)
        .strategic(contracts=contracts)
        .build()
    )


def _build_multi_hero_state(seed: int = 7) -> "AuthoritativeState":
    """
    Three HERO entities clustered within 3 units of each other.
    All share the same recruitment contracts so GroupSystem can form a party
    on the first tick that satisfies proximity (< 10 units).
    """
    h1 = _hero(1, 0.0, 0.0)
    h2 = _hero(2, 1.0, 0.5)
    h3 = _hero(3, 0.5, 1.0)

    state = AuthoritativeState(
        tick=0, seed=seed,
        entities={1: h1, 2: h2, 3: h3},
    )
    flags = dict(state.feature_flags)
    flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
    return replace(state, feature_flags=flags)


# ── Unit: group forms from contract on single GroupSystem call ────────────────

def test_hero_party_forms_from_contract():
    """
    HERO entities with an active contract and proximity form a group in one
    GroupSystem pass (SOC-160, SOC-187).
    """
    from src.systems.world_systems.groups import GroupSystem

    state = _build_multi_hero_state()
    update = GroupSystem.update_groups(state)

    assert len(update.groups_add_or_update) >= 1, "Expected at least one group to form"
    group = update.groups_add_or_update[0]
    assert len(group.member_ids) >= 2, "Group must have ≥ 2 members"

    leader_entity = state.entities[group.leader_id]
    assert leader_entity.identity.role == EntityRole.HERO, (
        f"Group leader must be HERO role, got {leader_entity.identity.role}"
    )


def test_hero_party_composition_score_nonzero():
    """
    A party of HERO entities receives a positive composition_score via
    PartyCompositionScorer at formation (E41F + E41G integration).
    """
    from src.systems.world_systems.groups import GroupSystem

    state = _build_multi_hero_state()
    update = GroupSystem.update_groups(state)

    assert update.groups_add_or_update, "Expected a group"
    group = update.groups_add_or_update[0]
    assert group.composition_score > 0.0, (
        f"Expected composition_score > 0, got {group.composition_score:.3f}"
    )


# ── Integration: 500-tick run ─────────────────────────────────────────────────

@pytest.mark.slow
def test_multi_hero_500_tick_run():
    """
    500-tick smoke test: three HERO entities in a minimal world run without
    error, and at least one HERO-led group is observed during the run.

    Acceptance criterion: run completes (no exception), hero_led_group_seen=True.
    """
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    TICKS = 500
    SEED = 7

    profile = RuntimeProfile(
        name="multi-hero-500",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=500,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )

    state = _build_multi_hero_state(seed=SEED)
    kernel = Kernel(
        profile=profile,
        state=state,
        rng=DeterministicRNG(SEED),
        flags={"no_frame_pacing": True},
    )

    hero_led_group_seen = False
    try:
        for _ in range(TICKS):
            kernel.tick_once()
            # Check whether any group has a HERO leader
            for group in kernel.state.groups.values():
                leader = kernel.state.entities.get(group.leader_id)
                if leader and leader.identity.role == EntityRole.HERO:
                    hero_led_group_seen = True
    finally:
        kernel.shutdown()

    assert hero_led_group_seen, (
        "Expected a HERO-led group to appear at some point during 500 ticks"
    )
