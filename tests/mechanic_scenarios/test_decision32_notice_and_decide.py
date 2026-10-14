"""Owner decision 32 ("notice and decide"), kernel level.

MAIN: a walker beside a hostile it is not engaged with gets a brain decision within ADJACENCY_WAKE_COOLDOWN ticks of the adjacency, far
ahead of its brain cadence (10). CONTROL: the same walker with the hostile two tiles away is not woken. INVARIANT (pinned run): no
adjacency episode of two or more ticks with an unengaged perceived hostile ends without a brain decision for that entity.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple

from src.config.profiles import PROD_SMALL
from src.core.movement_modes import MovementMode
from src.core.state import TaskComponent
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.scheduler import ADJACENCY_WAKE_COOLDOWN
from src.engine.tactical import TacticalDecisionSystem
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world
from tests.helpers.kernel_pinning import PinnedNormalGovernor

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
W, H = 2, 1
W_POS, ADJ, APART = (1.0, 1.0), (1.0, 2.0), (1.0, 3.0)



def _kernel(state):
    return Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED), governor=PinnedNormalGovernor(),
                  flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())


def _stage(h_pos):
    state = compile_world(WORLD_ID)
    entities = dict(state.entities)
    for eid, pos in ((W, W_POS), (H, h_pos)):
        e = entities[eid]
        props = dict(e.identity.properties)
        props["need_profile_id"] = "undead_purpose"
        nav = replace(e.navigation, position=pos, target=(3.0, 1.0) if eid == W else None, movement_mode=MovementMode.PURSUE if eid == W else e.navigation.movement_mode)
        entities[eid] = replace(e, navigation=nav, identity=replace(e.identity, properties=props),
                                combat=replace(e.combat, hp=5000, max_hp=5000, atk=60, readiness=100.0),
                                task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
    object.__setattr__(state, "entities", entities)
    object.__setattr__(state, "feature_flags", {**(state.feature_flags or {}), "ENABLE_COMBAT_ENGAGEMENT": "OFF"})
    return state


def _first_decision_tick(h_pos, ticks=12):
    seen: List[int] = []
    orig = TacticalDecisionSystem.evaluate_entity_intent

    def spy(st, entity, *a, **kw):
        if entity.id == W:
            seen.append(st.tick)
        return orig(st, entity, *a, **kw)

    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(spy)
    kernel = _kernel(_stage(h_pos))
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        kernel.shutdown()
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig)
    return seen[0] if seen else None


def test_main_a_walker_beside_an_unengaged_hostile_decides_within_the_wake_cooldown():
    first = _first_decision_tick(ADJ)
    assert first is not None and first <= ADJACENCY_WAKE_COOLDOWN + 1, f"first decision at tick {first}"


def test_control_without_the_adjacent_hostile_the_walker_waits_for_its_cadence():
    first = _first_decision_tick(APART)
    assert first is None or first > ADJACENCY_WAKE_COOLDOWN + 1, f"the control was woken at tick {first}"


def test_invariant_no_adjacency_episode_of_two_ticks_ends_without_a_brain_decision():
    state = compile_world("urban_political", 45)
    decisions: Dict[int, set] = {}
    orig = TacticalDecisionSystem.evaluate_entity_intent
    holder: Dict[str, Kernel] = {}

    def spy(st, entity, *a, **kw):
        decisions.setdefault(entity.id, set()).add(st.tick)
        return orig(st, entity, *a, **kw)

    TacticalDecisionSystem.evaluate_entity_intent = staticmethod(spy)
    kernel = _kernel(state)
    runs: Dict[int, List[int]] = {}
    try:
        for _ in range(400):
            st = kernel.state
            index = MovementCandidateSelector.position_index(st.entities)
            for e in st.entities.values():
                holding = e.task.work_kind == "ENTITY_ACT" and bool(e.task.payload)
                if (e.lifecycle.active and e.combat.alive and not holding
                        and MovementCandidateSelector.unengaged_adjacent_hostile(e, st.entities, index)):
                    runs.setdefault(e.id, []).append(st.tick)
            kernel.tick_once()
    finally:
        kernel.shutdown()
        TacticalDecisionSystem.evaluate_entity_intent = staticmethod(orig)
    violations: List[Tuple[int, int, int]] = []
    for eid, ticks in runs.items():
        start = prev = ticks[0]
        for t in ticks[1:] + [None]:
            if t is not None and t == prev + 1:
                prev = t
                continue
            if prev - start + 1 >= 2 and not any(d in decisions.get(eid, ()) for d in range(start, prev + 2)):
                violations.append((eid, start, prev))
            if t is not None:
                start = prev = t
    assert runs, "the pinned run never exercised the wake"
    assert violations == [], f"{len(violations)} adjacency episode(s) ended without a decision, first {violations[:3]}"
