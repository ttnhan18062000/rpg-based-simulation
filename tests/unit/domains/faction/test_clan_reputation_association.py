"""
Idea 54/M5 (SOC-268): ClanState.clan_reputation association wiring --
party-defection live-pipeline ClanUpdate production and the
find_clan_id_for_entity() reverse-lookup's determinism.

Ticket: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
"""
from src.core.enums import Faction, EntityRole
from src.core.state import AuthoritativeState, ClanState, GroupRecord
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline_phases.groups import GroupPhase
from src.systems.social_systems.clan_lifecycle import ClanLifecycleService


def _make_entity(e_id: int, pos=(0.0, 0.0)):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("actor")
        .location(pos[0], pos[1])
        .identity(role=EntityRole.HERO)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .build())


def test_party_defection_produces_clan_reputation_clan_update():
    """GroupPhase.resolve() produces both the existing entity-level
    notoriety_delta=2.0 AND a measurable ClanUpdate change to
    clans[clan_id].clan_reputation for the defector's clan, applied only
    through apply.py's clan_updates path (AC2)."""
    member = _make_entity(10)
    leader = _make_entity(11)

    group = GroupRecord(
        id=500,
        leader_id=11,
        member_ids={10, 11},
        anchor=(0.0, 0.0),
        grievance_log=("g1", "g2", "g3"),
    )

    clan = ClanState(clan_id="ironfang", member_entity_ids=(10,), clan_reputation=1.0)
    state = AuthoritativeState(
        tick=5, seed=0,
        entities={10: member, 11: leader},
        groups={500: group},
        clans={"ironfang": clan},
    )

    result = GroupPhase.resolve(state, StateUpdate())

    clan_ups = [cu for cu in result.clan_updates if cu.clan_id == "ironfang"]
    assert clan_ups, "Expected a ClanUpdate for the defector's clan"
    assert clan_ups[0].clan_reputation_delta < 0.0

    # AC2 requires the applied state to change, not just the raw ClanUpdate.
    new_state = ApplyPath.apply_partial(state, result)
    assert new_state.clans["ironfang"].clan_reputation < 1.0

    # Existing entity-level notoriety_delta=2.0 behavior stays intact/additive.
    defector_id = min(group.member_ids)
    assert result.entity_updates[defector_id].social.notoriety_delta == 2.0


def test_party_defection_with_no_clan_produces_no_clan_update():
    """A defector with no clan membership produces no ClanUpdate and does
    not crash."""
    member = _make_entity(10)
    leader = _make_entity(11)

    group = GroupRecord(
        id=501,
        leader_id=11,
        member_ids={10, 11},
        anchor=(0.0, 0.0),
        grievance_log=("g1", "g2", "g3"),
    )

    state = AuthoritativeState(
        tick=5, seed=0,
        entities={10: member, 11: leader},
        groups={501: group},
        clans={},
    )

    result = GroupPhase.resolve(state, StateUpdate())
    assert result.clan_updates == []


def test_clan_reputation_aggregation_is_deterministic():
    """find_clan_id_for_entity() must produce bit-identical output across
    repeated calls regardless of state.clans' dict insertion order
    (Determinism constraint, CLAUDE.md)."""
    clan_a = ClanState(clan_id="zzz_clan", member_entity_ids=(1, 2))
    clan_b = ClanState(clan_id="aaa_clan", member_entity_ids=(3, 4))
    clan_c = ClanState(clan_id="mmm_clan", member_entity_ids=(5,))

    state_order_1 = AuthoritativeState(
        tick=1, seed=0,
        clans={"zzz_clan": clan_a, "aaa_clan": clan_b, "mmm_clan": clan_c},
    )
    state_order_2 = AuthoritativeState(
        tick=1, seed=0,
        clans={"mmm_clan": clan_c, "zzz_clan": clan_a, "aaa_clan": clan_b},
    )

    for entity_id in (1, 2, 3, 4, 5):
        result_1 = ClanLifecycleService.find_clan_id_for_entity(state_order_1, entity_id)
        result_2 = ClanLifecycleService.find_clan_id_for_entity(state_order_2, entity_id)
        assert result_1 == result_2

    for _ in range(3):
        assert ClanLifecycleService.find_clan_id_for_entity(state_order_1, 3) == "aaa_clan"

    assert ClanLifecycleService.find_clan_id_for_entity(state_order_1, 999) is None
