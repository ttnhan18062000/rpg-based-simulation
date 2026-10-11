"""A held move ends on arriving in the AREA it was issued for, not only on its exact tile (divergence 2.113).

TCK-20261011-A-HELD-MOVE-STANDS-FROZEN-AFTER-ARRIVING-IN-ITS-AREA: a held ``ENTITY_MOVE`` runs no brain, so a LEASH_RETURN, REGROUP or
AVOID_HOSTILE move that arrived near (never on) its point stood frozen for hundreds of ticks. Staging asserts the completion branches
on both dispatchers and what does NOT end a move, never a death count.
"""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import TaskComponent
from src.core.work import WorkClass
from src.core.worker_protocol import WorkerPacket
from src.engine.candidate_selector import ARRIVAL_ENDS_MOVE_REASONS, MovementCandidateSelector as MCS
from src.engine.rpg_depth import LeashService
from src.engine.worker_logic import default_simulation_worker

HOME = (50.0, 50.0)


def _held(reason, at, target, **payload):
    e = (V2EntityBuilder(1).kind("goblin").location(*at).combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True)
         .navigation(home_position=HOME, leash_radius=10.0).build())
    return replace(e, task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": target, "reason": reason, **payload}))


def _ends(e):
    return MCS.move_ends_here(e, {e.id: e})


def test_the_set_other_branches_converge_on_names_the_within_a_tile_reasons():
    assert ARRIVAL_ENDS_MOVE_REASONS == frozenset({"KEEP_DISTANCE", "FLEE_THREAT"})


@pytest.mark.parametrize("reason", sorted(ARRIVAL_ENDS_MOVE_REASONS | {"AVOID_HOSTILE"}))
def test_a_step_away_ends_within_a_tile_of_its_point_and_not_before(reason):
    assert _ends(_held(reason, (30.0, 30.0), (30.0, 31.0))) is True
    assert _ends(_held(reason, (30.0, 30.0), (30.0, 33.0))) is False
    assert _ends(_held(reason, (30.0, 30.0), (30.0, 30.0))) is True


def test_a_leash_return_ends_inside_the_home_area_not_on_the_home_tile():
    assert _ends(_held("LEASH_RETURN", (55.0, 54.0), HOME)) is True     # Manhattan 9 <= 10: inside the area, 9 tiles from the home tile
    assert _ends(_held("LEASH_RETURN", (55.0, 56.0), HOME)) is False    # 11: still beyond the leash
    assert LeashService.in_home_area(_held("LEASH_RETURN", (55.0, 54.0), HOME)) is True


def test_an_unleashed_entity_is_in_no_home_area():
    e = V2EntityBuilder(1).kind("guard").location(50.0, 50.0).navigation(home_position=HOME, leash_radius=0.0).build()
    assert LeashService.in_home_area(e) is False
    assert LeashService.in_home_area(replace(e, navigation=replace(e.navigation, home_position=None, leash_radius=10.0))) is False


def test_a_regroup_ends_within_the_cohesion_radius_it_was_issued_with():
    assert _ends(_held("REGROUP", (33.0, 34.0), (30.0, 30.0), arrival_radius=5.0)) is True      # 5.0 away
    assert _ends(_held("REGROUP", (33.0, 35.0), (30.0, 30.0), arrival_radius=5.0)) is False     # 5.83 away
    assert _ends(_held("REGROUP", (30.0, 30.0), (30.0, 30.0))) is False                         # no radius recorded: not an area move


@pytest.mark.parametrize("reason", ["WANDER", "OBJECTIVE", "PANIC_RETREAT", None])
def test_a_move_without_an_area_is_not_ended_by_standing_near_its_point(reason):
    assert _ends(_held(reason, (30.0, 30.0), (30.0, 31.0))) is False


def test_keep_walking_still_ends_only_on_its_exact_tile():
    assert _ends(_held("KEEP_WALKING", (30.0, 30.0), (30.0, 30.0))) is True
    assert _ends(_held("KEEP_WALKING", (30.0, 30.0), (30.0, 31.0))) is False


def _worker_update(e):
    packet = WorkerPacket(packet_id="p", work_id="w", tick=1, world_time=1, seed=1, work_class=WorkClass.CRITICAL, subject=e,
                          neighbor_view=[], work_kind="ENTITY_MOVE", payload=dict(e.task.payload), all_entities={1: e})
    return default_simulation_worker(packet)[0].update


def test_the_worker_dispatcher_ends_the_move_by_the_same_rule():
    ended = _worker_update(_held("LEASH_RETURN", (55.0, 54.0), HOME))
    assert ended.navigation.target_clear is True and ended.task.work_kind_set == "ENTITY_ACT"
    kept = _worker_update(_held("LEASH_RETURN", (55.0, 56.0), HOME))
    assert kept.navigation.target_clear is not True and kept.task is None


def test_a_regroup_ends_by_the_radius_it_was_issued_with_whatever_the_groups_radius_becomes():
    """The radius travels in the move's payload: a cohesion radius that changes mid-move (a group growing or shrinking) does not move the end."""
    at, anchor = (33.0, 36.0), (30.0, 30.0)                     # 6.7 from the anchor
    issued_wide = _held("REGROUP", at, anchor, arrival_radius=8.0)
    issued_narrow = _held("REGROUP", at, anchor, arrival_radius=5.0)
    assert _ends(issued_wide) is True and _ends(issued_narrow) is False
    # the same entity, later in the same move, with nothing about the group in view: unchanged
    assert _ends(replace(issued_wide, navigation=replace(issued_wide.navigation, position=at))) is True
