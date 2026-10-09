"""CONFLICT-04 at the movement layer (divergence 2.89): an entity beside an engaged hostile takes no step from a stored target.

Scenario: an idle walker (empty ENTITY_ACT payload) with a strategic-seeded stored navigation target stands orthogonally beside a
hostile that is engaged with it. Main arm: it does not step and no opportunity attack lands on it. Control arm: the same walker
with the hostile out of reach walks toward its target, so the main arm holds because of the rule, not because it cannot move.
Invariant (pinned run): no entity with an engaged adjacent hostile takes a movement step on a tick it made no decision.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List

from src.config.profiles import PROD_SMALL
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.combat import CombatResolutionSystem
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.movement import MovementSystem
from src.engine.tactical import TacticalDecisionSystem
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
W, H = 2, 1  # W the walker (the strong orc), H the hostile
W_POS, ADJ, FAR = (1.0, 1.0), (1.0, 2.0), (3.0, 3.0)
STORED = (3.0, 1.0)  # a stored target away from the hostile (so the first step leaves adjacency)


def _stage(state: AuthoritativeState, *, h_pos) -> AuthoritativeState:
    entities = dict(state.entities)
    for eid, pos in ((W, W_POS), (H, h_pos)):
        e = entities[eid]
        combat = replace(e.combat, hp=5000, max_hp=5000, atk=60, readiness=0.0 if eid == H else 100.0, readiness_speed=0.0 if eid == H else 10.0)
        if eid == W:
            nav = replace(e.navigation, position=pos, target=STORED, movement_mode=MovementMode.PURSUE)
            task = TaskComponent(work_kind="ENTITY_ACT", payload={})
        else:
            nav = replace(e.navigation, position=pos, target=None)
            task = TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": W})
        entities[eid] = replace(e, combat=combat, navigation=nav, task=task)
    object.__setattr__(state, "entities", entities)
    object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
    return state


def _kernel(state: AuthoritativeState) -> Kernel:
    return Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                  flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())


def _walk(state: AuthoritativeState, ticks: int) -> Dict[str, Any]:
    orig = CombatResolutionSystem.resolve_multi_attack
    oa_on_walker: List[int] = []

    def wrapped(attackers, target, c, is_opportunity_attack=False, **kw):
        r = orig(attackers, target, c, is_opportunity_attack=is_opportunity_attack, **kw)
        if is_opportunity_attack and target.id == W and getattr(r, "hp_delta", 0) and r.hp_delta < 0:
            oa_on_walker.append(1)
        return r

    CombatResolutionSystem.resolve_multi_attack = staticmethod(wrapped)
    kernel = _kernel(state)
    positions = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            positions.append(tuple(kernel._state.entities[W].navigation.position))
        return dict(positions=positions, oa=len(oa_on_walker))
    finally:
        kernel.shutdown()
        CombatResolutionSystem.resolve_multi_attack = staticmethod(orig)


def is_step_without_a_decision(entity, decided_this_tick, entities) -> bool:
    """True for a step the CONFLICT-04 movement rule forbids: an engaged hostile adjacent, no decision this tick, and not a decided flight.
    A decided flight steps and pays the opportunity attack (CONFLICT-04, divergence 2.89): the same predicate the rule uses."""
    return (not decided_this_tick and not MovementCandidateSelector.is_decided_flight(entity)
            and MovementCandidateSelector.engaged_adjacent_hostile(entity, entities))


def test_the_invariant_predicate_exempts_a_held_decided_flight_and_counts_every_other_undecided_step():
    from dataclasses import replace as _replace
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    def fighter(eid, pos, faction):
        role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
        return (V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos).identity(role=role, faction=faction)
                .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build())

    hostile = _replace(fighter(2, (10.0, 11.0), Faction.MONSTER_HORDE), task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1}))

    def held(reason):
        return _replace(fighter(1, (10.0, 10.0), Faction.HERO_GUILD),
                        task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (40.0, 40.0), "reason": reason}))

    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    try:
        for reason in ("PANIC_RETREAT", "SAFETY_PRESSURE_RETREAT", "LEASH_RETURN", "AVOID_HOSTILE"):
            e = held(reason)
            assert is_step_without_a_decision(e, False, {1: e, 2: hostile}) is False   # a decided flight steps and pays the opportunity attack
        e = held("REGROUP")
        assert is_step_without_a_decision(e, False, {1: e, 2: hostile}) is True        # any other undecided step beside an engaged hostile counts
        assert is_step_without_a_decision(e, True, {1: e, 2: hostile}) is False        # a decision this tick is allowed
    finally:
        reset_behavior_consumers()


def test_an_idle_walker_beside_an_engaged_hostile_does_not_step_and_takes_no_opportunity_attack():
    out = _walk(_stage(compile_world(WORLD_ID), h_pos=ADJ), 6)  # inside the first brain cadence: only the stored target could move it
    assert set(out["positions"]) == {W_POS}, "the walker stepped off adjacency without a decision"
    assert out["oa"] == 0


def test_control_the_same_walker_without_an_adjacent_hostile_walks_its_stored_target():
    out = _walk(_stage(compile_world(WORLD_ID), h_pos=FAR), 6)
    assert out["positions"][-1] != W_POS, "the control walker did not move, so the main arm proves nothing"


def test_invariant_no_step_with_an_engaged_adjacent_hostile_on_a_tick_without_a_decision():
    """Pinned run (urban_political, seed 45, 400 ticks): count movement steps of entities with an engaged adjacent hostile that
    made no ENTITY_MOVE decision that tick. After the fix the count is 0."""
    state = compile_world("urban_political", 45)
    decided: set = set()
    violations: List[Any] = []
    orig_decide, orig_move = TacticalDecisionSystem.evaluate_entity_intent, MovementSystem.resolve_move
    kernel_ref: Dict[str, Kernel] = {}

    def decide(st, entity, *a, **kw):
        r = orig_decide(st, entity, *a, **kw)
        if r is not None and r.task is not None and r.task.work_kind_set == "ENTITY_MOVE":
            decided.add((entity.id, kernel_ref["k"].state.tick))
        return r

    def move(state_or_context, entity, target_pos, mode=MovementMode.WANDER):
        tick = kernel_ref["k"].state.tick
        if is_step_without_a_decision(entity, (entity.id, tick) in decided, state_or_context.entities):
            violations.append((tick, entity.id))
        return orig_move(state_or_context, entity, target_pos, mode=mode)

    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(decide)
    MovementSystem.resolve_move = staticmethod(move)
    kernel = _kernel(state)
    kernel_ref["k"] = kernel
    try:
        for _ in range(400):
            kernel.tick_once()
    finally:
        kernel.shutdown()
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig_decide)
        MovementSystem.resolve_move = staticmethod(orig_move)
    assert violations == [], f"{len(violations)} step(s) without a decision beside an engaged hostile, first: {violations[:3]}"


def test_invariant_no_entity_stays_blocked_by_the_rule_for_more_than_one_brain_cadence_plus_one():
    """The rule must not freeze anyone: a blocked held move is released to the brain, an idle entity's brain decides within its
    cadence (``strategic_intelligence`` 10). Pinned run (urban_political, seed 45, 600 ticks): the longest run of consecutive ticks
    one entity is blocked is at most 11."""
    state = compile_world("urban_political", 45)
    blocked: Dict[int, List[int]] = {}
    orig = MovementCandidateSelector.engaged_adjacent_hostile
    kernel_ref: Dict[str, Kernel] = {}

    def spy(entity, entities, index=None):
        r = orig(entity, entities, index)
        if r:
            ticks = blocked.setdefault(entity.id, [])
            t = kernel_ref["k"].state.tick
            if not ticks or ticks[-1] != t:
                ticks.append(t)
        return r

    MovementCandidateSelector.engaged_adjacent_hostile = staticmethod(spy)
    kernel = _kernel(state)
    kernel_ref["k"] = kernel
    try:
        for _ in range(600):
            kernel.tick_once()
    finally:
        kernel.shutdown()
        MovementCandidateSelector.engaged_adjacent_hostile = staticmethod(orig)
    longest = 0
    for ticks in blocked.values():
        run = best = 1
        for a, b in zip(ticks, ticks[1:]):
            run = run + 1 if b == a + 1 else 1
            best = max(best, run)
        longest = max(longest, best)
    assert blocked, "the pinned run never exercised the rule"
    assert longest <= 11, f"an entity stayed blocked {longest} consecutive ticks (cadence 10 + 1)"
