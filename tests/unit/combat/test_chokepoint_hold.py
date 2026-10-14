"""COMB-015: a VANGUARD at a chokepoint holds its tile when its target is within 5 tiles but out of reach.

The tactical pass emits an ``ENTITY_ACT`` ``HOLD`` (reason HOLD_CHOKEPOINT) with movement mode HOLD. The action router had no
handler for it, so every hold ended as ``UNSUPPORTED_ACTION`` (a reported failure for a stand that works). The hold is now a typed
no-op success that ends its task like a survival action: the movement mode HOLD keeps the tile (its speed multiplier is 0) and the
brain re-decides on its next cadence. Keeping the payload instead would keep the holder off the brain for good (measured: it
reported HOLD SUCCESS for 60 ticks and never re-decided).
"""
from __future__ import annotations

from dataclasses import replace

from src.config.profiles import PROD_SMALL
from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.domain.action_router import ActionRouter
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.pipeline_phases.actions import ActionRoutingPhase
from src.engine.tactical import TacticalDecisionSystem
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world, empty_inventories

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
F, H = 2, 1
F_POS, H_POS = (1.0, 1.0), (1.0, 3.0)  # walls at (0, 1) and (2, 1) make (1, 1) a one-tile gap; the target is 2 tiles away, range 1


def _staged() -> AuthoritativeState:
    state = empty_inventories(compile_world(WORLD_ID))  # the scenario is about the hold, not about what the two bodies carry
    entities = dict(state.entities)
    for eid, pos in ((F, F_POS), (H, H_POS)):
        e = entities[eid]
        props = dict(e.identity.properties)
        props["need_profile_id"] = "undead_purpose"  # not cautious
        entities[eid] = replace(
            e, navigation=replace(e.navigation, position=pos, target=None), identity=replace(e.identity, properties=props),
            combat=replace(e.combat, hp=5000, max_hp=5000, atk=1, readiness=100.0, range=1,
                           tactical_role="VANGUARD" if eid == F else e.combat.tactical_role),
            task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
    object.__setattr__(state, "entities", entities)
    object.__setattr__(state, "terrain", {(0, 1): "WALL", (2, 1): "WALL"})
    object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
    return state


def test_a_vanguard_at_a_chokepoint_with_its_target_out_of_reach_decides_to_hold():
    state = _staged()
    update = TacticalDecisionSystem.evaluate_entity_intent(state, state.entities[F], [state.entities[H]], 0.0)
    assert update.task.payload_set["action"] == "HOLD" and update.task.payload_set["reason"] == "HOLD_CHOKEPOINT"
    assert update.navigation.movement_mode_set == MovementMode.HOLD


def test_the_hold_is_a_typed_success_that_ends_its_task_not_an_unsupported_action():
    state = _staged()
    payload = {"action": "HOLD", "reason": "HOLD_CHOKEPOINT", "target_id": H}
    routed = ActionRouter.execute_action(state.entities[F], payload, 1, None, state)
    assert routed[F].navigation is None or routed[F].navigation.failure_reason is None
    refined = ActionRoutingPhase.route(state, StateUpdate(entity_updates={
        F: EntityUpdate(entity_id=F, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=dict(payload)))}))
    assert refined.entity_updates[F].task.payload_set == {}  # idle: the brain re-decides on its cadence
    assert ReasonCode.UNSUPPORTED_ACTION.value not in refined.rejections_delta


def test_in_the_kernel_the_holder_stays_on_its_tile_and_its_brain_keeps_deciding():
    state = _staged()
    reasons, decisions = [], []
    orig_route, orig_decide = ActionRouter.execute_action, TacticalDecisionSystem.evaluate_entity_intent

    def route(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
        r = orig_route(entity, payload, current_tick, neighbor_view, context)
        if entity.id == F and (payload or {}).get("action") == "HOLD":
            reasons.append(getattr(getattr(r.get(F), "navigation", None), "failure_reason", None))
        return r

    def decide(st, entity, *a, **kw):
        r = orig_decide(st, entity, *a, **kw)
        if entity.id == F and r is not None and r.task is not None:
            decisions.append((r.task.payload_set or {}).get("action"))
        return r

    ActionRouter.execute_action = staticmethod(route)
    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(decide)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    try:
        positions = set()
        for _ in range(30):
            kernel.tick_once()
            positions.add(tuple(kernel._state.entities[F].navigation.position))
    finally:
        kernel.shutdown()
        ActionRouter.execute_action = staticmethod(orig_route)
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig_decide)
    assert positions == {F_POS}, "the chokepoint holder left its tile"
    assert decisions and decisions[0] == "HOLD"
    assert reasons and all(r is None for r in reasons), f"the hold was reported as a failure: {reasons}"
    assert len(decisions) >= 2, "the holder's brain never re-decided (a kept payload would hold it for good)"
