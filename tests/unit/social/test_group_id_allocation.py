# Compliance IDs: SOC-166
"""TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP: a group id is never re-issued, an add never replaces a record."""
import itertools
import pathlib
import re
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import (
    GROUP_ID_BASE,
    AuthoritativeState,
    GroupRecord,
    seeded_next_group_id,
)
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.apply_plan import GROUP_ADD_ID_TAKEN, resolve_group_adds
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.pipeline_phases.groups import GroupPhase
from src.systems.world_systems.groups import GroupSystem


def _contract(cid="r", a=1, b=2):
    return ContractState(id=cid, kind=ContractKind.RECRUITMENT, source_id=a, target_id=b, status=ContractStatus.ACTIVE)


def _pair(a, b, x, cid):
    c = _contract(cid, a, b)
    return {
        a: V2EntityBuilder(a).kind("actor").location(x, x).strategic(contracts={cid: c}).build(),
        b: V2EntityBuilder(b).kind("actor").location(x + 0.2, x + 0.2).strategic(contracts={cid: c}).build(),
    }


def _member(i, gid, x):
    return V2EntityBuilder(i).kind("actor").location(x, x).identity(group_id=gid).build()


def _gap_state():
    """Two dissolved records and one live group at 10004: the old count (3 groups + 1 update) re-issues 10004."""
    entities = {**_pair(1, 2, 1.0, "r"), 11: _member(11, 10004, 50.0), 12: _member(12, 10004, 50.5)}
    groups = {
        10000: GroupRecord(id=10000, leader_id=99, member_ids={99}, anchor=(0, 0), dissolution_tick=3),
        10001: GroupRecord(id=10001, leader_id=98, member_ids={98}, anchor=(0, 0), dissolution_tick=4),
        10004: GroupRecord(id=10004, leader_id=11, member_ids={11, 12}, anchor=(50, 50)),
    }
    return AuthoritativeState(tick=10, seed=1, entities=entities, groups=groups)


def _resolves(state):
    return [
        e.id for e in state.entities.values()
        if e.combat.alive and e.identity.group_id is not None and e.identity.group_id >= 0
        and (e.identity.group_id not in state.groups or e.id not in state.groups[e.identity.group_id].member_ids)
    ]


def test_formation_over_a_gap_does_not_overwrite_a_live_group():
    state = _gap_state()
    upd = GroupSystem.update_groups(state)
    new = ApplyPath.apply_generation(state, upd)
    assert new.groups[10004].member_ids == {11, 12}
    formed = [g for g in new.groups.values() if g.member_ids == {1, 2}]
    assert len(formed) == 1 and formed[0].id not in state.groups
    assert _resolves(new) == []


def test_ids_are_never_reissued_across_dissolve_then_form():
    state = _gap_state()
    seen = set(state.groups)
    # tick A forms (1,2); tick B dissolves it (leader gone) and forms (3,4)
    state = ApplyPath.apply_generation(state, GroupSystem.update_groups(state))
    first = max(set(state.groups) - seen)
    seen |= set(state.groups)
    entities = dict(state.entities)
    entities.update(_pair(3, 4, 20.0, "r2"))
    state = replace(state, entities=entities)
    state = ApplyPath.apply_generation(state, GroupSystem.update_groups(state, StateUpdate(
        entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(alive_set=False))})))
    new_ids = set(state.groups) - seen
    assert len(new_ids) == 1 and not (new_ids & seen)
    assert state.groups[first].dissolution_tick is not None  # kept, not replaced
    assert _resolves(state) == []


def test_two_formations_in_one_tick_get_distinct_ids():
    entities = {**_pair(1, 2, 1.0, "a"), **_pair(5, 6, 30.0, "b")}
    state = AuthoritativeState(tick=1, seed=1, entities=entities)
    upd = GroupSystem.update_groups(state)
    assert len(upd.groups_add) == 2
    assert len({g.id for g in upd.groups_add}) == 2
    assert upd.next_group_id_set == max(g.id for g in upd.groups_add) + 1
    assert upd.groups_add_or_update == []


def test_allocator_steps_past_a_squad_hash_id_in_the_store_and_in_the_update():
    entities = _pair(1, 2, 1.0, "r")
    squad = GroupRecord(id=GROUP_ID_BASE, leader_id=7, member_ids={7, 8}, anchor=(0, 0), roles={7: "FACTION_SQUAD", 8: "FACTION_SQUAD"})
    state = AuthoritativeState(tick=1, seed=1, entities=entities, groups={squad.id: squad})
    assert GroupSystem.update_groups(state).groups_add[0].id != squad.id
    other = GroupRecord(id=GROUP_ID_BASE + 5, leader_id=9, member_ids={9, 10}, anchor=(0, 0), roles={9: "FACTION_SQUAD"})
    state2 = AuthoritativeState(tick=1, seed=1, entities=entities)
    got = GroupSystem.update_groups(state2, StateUpdate(groups_add=[replace(other, id=GROUP_ID_BASE)])).groups_add[0].id
    assert got == GROUP_ID_BASE + 1


def test_apply_rejects_an_add_over_any_existing_id_and_leaves_members_alone():
    state = _gap_state()
    for target in (10004, 10000):  # live and dissolved
        intruder = GroupRecord(id=target, leader_id=1, member_ids={1, 2}, anchor=(1, 1))
        upd = StateUpdate(groups_add=[intruder], entity_updates={
            1: EntityUpdate(entity_id=1, group_id_set=target), 2: EntityUpdate(entity_id=2, group_id_set=target)})
        new = ApplyPath.apply_generation(state, upd)
        assert new.groups[target] == state.groups[target]
        assert new.rejection_registry[GROUP_ADD_ID_TAKEN] == 1
        assert new.entities[1].identity.group_id is None and new.entities[2].identity.group_id is None
        assert _resolves(new) == []


def test_in_place_update_and_dissolve_are_not_rejected_while_an_add_on_the_same_id_is():
    state = _gap_state()
    live = state.groups[10004]
    dissolved = replace(live, dissolution_tick=10)
    updated = replace(state.groups[10000], last_updated_tick=10)
    intruder = GroupRecord(id=10001, leader_id=1, member_ids={1, 2}, anchor=(1, 1))
    new = ApplyPath.apply_generation(state, StateUpdate(
        groups_add_or_update=[dissolved, updated], groups_add=[intruder],
        entity_updates={m: EntityUpdate(entity_id=m, group_id_set=-1) for m in (11, 12)}))
    assert new.groups[10004].dissolution_tick == 10
    assert new.groups[10000].last_updated_tick == 10
    assert new.groups[10001] == state.groups[10001]
    assert new.rejection_registry[GROUP_ADD_ID_TAKEN] == 1


def test_duplicate_adds_in_one_tick_keep_the_first():
    state = AuthoritativeState(tick=1, seed=1)
    a = GroupRecord(id=10000, leader_id=1, member_ids={1, 2}, anchor=(0, 0))
    b = GroupRecord(id=10000, leader_id=3, member_ids={3, 4}, anchor=(0, 0))
    out = resolve_group_adds(state.groups, StateUpdate(groups_add=[a, b]))
    assert out.groups_add == [a] and out.rejections_delta[GROUP_ADD_ID_TAKEN] == 1


def test_squad_adds_do_not_advance_the_counter_but_formations_do():
    state = AuthoritativeState(tick=1, seed=1)
    squad = GroupRecord(id=1234567, leader_id=7, member_ids={7}, anchor=(0, 0), roles={7: "FACTION_SQUAD"})
    assert ApplyPath.apply_generation(state, StateUpdate(groups_add=[squad])).next_group_id == GROUP_ID_BASE
    assert ApplyPath.apply_generation(state, StateUpdate(next_group_id_set=GROUP_ID_BASE + 3)).next_group_id == GROUP_ID_BASE + 3
    advanced = ApplyPath.apply_generation(state, StateUpdate(next_group_id_set=GROUP_ID_BASE + 3))
    assert ApplyPath.apply_generation(advanced, StateUpdate(next_group_id_set=GROUP_ID_BASE + 1)).next_group_id == GROUP_ID_BASE + 3


def test_merge_keeps_both_adds_and_takes_the_larger_counter():
    a = StateUpdate(groups_add=[GroupRecord(id=10000, leader_id=1, member_ids={1}, anchor=(0, 0))], next_group_id_set=10001)
    b = StateUpdate(groups_add=[GroupRecord(id=10000, leader_id=2, member_ids={2}, anchor=(0, 0))], next_group_id_set=10005)
    m = a.merge(b)
    assert [g.leader_id for g in m.groups_add] == [1, 2] and m.next_group_id_set == 10005
    assert not StateUpdate(groups_add=a.groups_add).is_noop()
    assert not StateUpdate(next_group_id_set=1).is_noop()


def _roundtrip(s):
    """No state loader exists in src/: the canonical dump omits the counter at the seed, so the 'load' is the constructor's seed."""
    dump = CanonicalStateHasher.to_canonical_data(s)
    value = dump.get("next_group_id")
    return AuthoritativeState(tick=s.tick, seed=s.seed, groups=s.groups, **({} if value is None else {"next_group_id": value}))


def test_counter_round_trips_for_no_groups_squad_only_and_formed_groups():
    squad = GroupRecord(id=1999999999, leader_id=7, member_ids={7}, anchor=(0, 0), roles={7: "FACTION_SQUAD"})
    formed = GroupRecord(id=10007, leader_id=1, member_ids={1, 2}, anchor=(0, 0))
    for groups, counter in (({}, GROUP_ID_BASE), ({squad.id: squad}, GROUP_ID_BASE), ({formed.id: formed, squad.id: squad}, 10009)):
        s = AuthoritativeState(tick=3, seed=1, groups=groups, next_group_id=counter)
        assert _roundtrip(s).next_group_id == s.next_group_id
        assert ("next_group_id" in CanonicalStateHasher.to_canonical_data(s)) == (s.next_group_id != GROUP_ID_BASE)


def test_seed_skips_squads_and_covers_the_highest_non_squad_id():
    squad = GroupRecord(id=1999999999, leader_id=7, member_ids={7}, anchor=(0, 0), roles={7: "FACTION_SQUAD"})
    formed = GroupRecord(id=10041, leader_id=1, member_ids={1}, anchor=(0, 0))
    assert seeded_next_group_id({}) == GROUP_ID_BASE
    assert seeded_next_group_id({squad.id: squad}) == GROUP_ID_BASE
    assert seeded_next_group_id({squad.id: squad, formed.id: formed}) == 10042
    assert AuthoritativeState(tick=0, seed=1, groups={formed.id: formed}).next_group_id == 10042


def test_no_id_is_reissued_over_a_long_form_and_dissolve_run():
    """Hard-law style check: across many ticks of forming and dissolving, every GroupRecord id appears once."""
    state = AuthoritativeState(tick=0, seed=1)
    issued = []
    pair_ids = itertools.count(100, 2)
    for t in range(1, 13):
        a = next(pair_ids); b = a + 1
        entities = dict(state.entities)
        entities.update(_pair(a, b, float(a), f"c{a}"))
        state = replace(state, entities=entities, tick=t)
        before = set(state.groups)
        state = ApplyPath.apply_generation(state, GroupSystem.update_groups(state))
        issued.extend(sorted(set(state.groups) - before))
        if t % 3 == 0:  # kill the newest group's leader: dissolves it and keeps the record
            leader = max(state.groups.values(), key=lambda g: g.id).leader_id
            state = ApplyPath.apply_generation(state, GroupSystem.update_groups(
                state, StateUpdate(entity_updates={leader: EntityUpdate(entity_id=leader, combat=CombatUpdate(alive_set=False))})))
        assert _resolves(state) == []
    assert len(issued) == len(set(issued)) and len(issued) >= 10


def test_group_phase_carries_adds_and_the_counter_and_a_squad_collision_leaves_no_ghost():
    """The phase concatenates adds (no merge by id), so a squad add and a formation add on one id reach apply as two rows: the
    second is rejected and its members keep their group_id."""
    state = AuthoritativeState(tick=1, seed=1, entities=_pair(1, 2, 1.0, "a"))
    squad = GroupRecord(id=GROUP_ID_BASE, leader_id=7, member_ids={7}, anchor=(0, 0), roles={7: "FACTION_SQUAD"})
    phased = GroupPhase.resolve(state, StateUpdate(groups_add=[squad]))
    assert [g.id for g in phased.groups_add][0] == squad.id and len(phased.groups_add) == 2
    assert phased.groups_add[1].id != squad.id  # the allocator saw the squad row
    assert phased.next_group_id_set == phased.groups_add[1].id + 1
    # force the case the allocator cannot see (squad row merged after the phase): same id twice
    clash = replace(phased, groups_add=[phased.groups_add[0], replace(phased.groups_add[1], id=squad.id)], entity_updates={
        m: EntityUpdate(entity_id=m, group_id_set=squad.id) for m in (1, 2)})
    new = ApplyPath.apply_generation(state, clash)
    assert new.groups[squad.id] == squad and new.rejection_registry[GROUP_ADD_ID_TAKEN] == 1
    assert new.entities[1].identity.group_id is None and new.entities[2].identity.group_id is None
    assert _resolves(new) == []


def test_every_reader_of_the_update_list_also_reads_the_add_list():
    """A missed consumer drops adds silently. Every src file naming groups_add_or_update must also name groups_add, or be listed here."""
    update_only = {"domains/cooperation/phase.py"}  # rebuilds the update with dataclasses.replace, so groups_add rides along untouched
    src = pathlib.Path(__file__).resolve().parents[3] / "src"
    missing = [
        str(p.relative_to(src)) for p in sorted(src.rglob("*.py"))
        if "groups_add_or_update" in p.read_text(encoding="utf-8") and not re.search(r"\bgroups_add\b", p.read_text(encoding="utf-8"))
        and str(p.relative_to(src)) not in update_only
    ]
    assert missing == []
