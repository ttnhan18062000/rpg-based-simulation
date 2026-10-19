"""TCK-20261014-SOME-MOVE-STEPS-LOSE-THEIR-STEP-TIME-BETWEEN-RESOLVE-MOVE-AND-APPLY (divergence 2.126 residual).

The strategic pass's fast path sends a loaded entity back to town by REGROUP. When the entity already carries a move update
this tick, that REGROUP must be merged into the move's navigation update, not replace it: a fresh NavigationUpdate dropped
`step_ready_tick_set` (and `moved_recently_set`, `region_id_set`, `last_position_set`), so the step applied untimed.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.movement_modes import MovementMode
from src.core.inventory import ItemStack
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic import StrategicIntelligenceSystem


def _loaded_walker():
    return V2EntityBuilder(1).kind("worker").location(10.0, 10.0).inventory(items=[ItemStack(item_id="wood", quantity=1)]).build()


def _pass(move_nav):
    state = AuthoritativeState(tick=5, seed=1, entities={1: _loaded_walker()}, town_center=(50.0, 50.0))
    move = EntityUpdate(entity_id=1, new_position=(11.0, 10.0), moved_this_tick=True, navigation=move_nav)
    cadence = SystemCadence(strategic_intelligence=1000, concern_evaluation=1000)
    result = StrategicIntelligenceSystem.fused_strategic_pass(state, StateUpdate(entity_updates={1: move}), cadence=cadence)
    return result.entity_updates[1]


def test_regroup_keeps_the_step_time_of_the_move_it_joins():
    nav = _pass(NavigationUpdate(step_ready_tick_set=7.0, moved_recently_set=True, region_id_set="r1", last_position_set=(10.0, 10.0))).navigation
    assert nav.movement_mode_set == MovementMode.REGROUP and nav.target_set is not None
    assert nav.step_ready_tick_set == 7.0
    assert nav.moved_recently_set is True and nav.region_id_set == "r1" and nav.last_position_set == (10.0, 10.0)


def test_regroup_alone_still_sets_target_and_mode():
    nav = _pass(None).navigation
    assert nav.movement_mode_set == MovementMode.REGROUP and nav.step_ready_tick_set is None
