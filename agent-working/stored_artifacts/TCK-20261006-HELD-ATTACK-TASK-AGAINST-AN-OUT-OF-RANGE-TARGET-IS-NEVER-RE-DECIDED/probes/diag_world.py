"""Constructed diagonal pair through the real Kernel. usage: diag_kernel.py <root> <ticks> [held|fresh]
held  = attacker starts with a held ATTACK task (the live loop); fresh = no task (brain decides)."""
import sys
from dataclasses import replace

ROOT, TICKS, MODE = sys.argv[1], int(sys.argv[2]), (sys.argv[3] if len(sys.argv) > 3 else "held")
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.combat import CombatResolutionSystem
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

CALLS = []
from src.engine.candidate_selector import MovementCandidateSelector as _MCS
_tmc = _MCS.tracked_move_complete


def tmc(entity, entities):
    r = _tmc(entity, entities)
    if entity.id == 1:
        print("  TMC e1 pos", entity.navigation.position, "payload", {k: v for k, v in (entity.task.payload or {}).items() if k in ("target_id", "reason", "target_position")}, "->", r)
    return r


_MCS.tracked_move_complete = staticmethod(tmc)
_ra = CombatResolutionSystem.resolve_attack


def ra(attacker, defender, state, is_opportunity_attack=False, is_lethal=True):
    CALLS.append((state.tick, attacker.id, is_opportunity_attack))
    return _ra(attacker, defender, state, is_opportunity_attack, is_lethal)


CombatResolutionSystem.resolve_attack = staticmethod(ra)


def ent(eid, pos, faction, inert=False):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos)
            .identity(role=role, faction=faction)
            .combat(hp=100, max_hp=100, attack_range=1, readiness=(0.0 if inert else 100.0), readiness_speed=(0.0 if inert else 10.0), alive=True).lifecycle(active=True).build())


a = ent(1, (10.0, 10.0), Faction.HERO_GUILD)
b = ent(2, (11.0, 11.0), Faction.MONSTER_HORDE, inert=True)
if MODE == "held":
    a = replace(a, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 2}))
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
spec, wctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context("frontier_living_world")
base, _ = WorldCompiler.compile(spec, 42, context=wctx)
anchor = next(iter(base.entities.values())).navigation.position
ax, ay = anchor
a = replace(a, navigation=replace(a.navigation, position=(ax, ay), region_id=next(iter(base.entities.values())).navigation.region_id))
b = replace(b, navigation=replace(b.navigation, position=(ax + 1.0, ay + 1.0), region_id=a.navigation.region_id))
if MODE == "held":
    a = replace(a, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 2}))
print("ANCHOR", anchor)
state = replace(base, entities={1: a, 2: b})
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
first = None
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        # Freeze the target (position, task, readiness) so the pair's geometry is the only variable; keep its hp.
        b_now = st.entities[2]
        b_fixed = replace(b, combat=replace(b.combat, hp=b_now.combat.hp, alive=b_now.combat.alive))
        k._state = st = replace(st, entities={**dict(st.entities), 2: b_fixed})
        e1, e2 = st.entities[1], st.entities[2]
        p = e1.task.payload or {}
        if st.tick <= 45:
            print("T", st.tick, "nav.target", e1.navigation.target, "nav.mode", e1.navigation.movement_mode, "a", e1.navigation.position, "b", e2.navigation.position, "a.task", e1.task.work_kind, p.get("action"), p.get("outcome"), p.get("reason"),
                  "mode", e1.navigation.movement_mode, "b.hp", e2.combat.hp, "a.hp", e1.combat.hp, "ready", e1.combat.readiness)
finally:
    k.shutdown()
non_opp = [c for c in CALLS if not c[2] and c[1] == 1]
print("A1 resolve_attack calls (non-opportunity):", len(non_opp), "first at tick", non_opp[0][0] if non_opp else None)
print("all resolve_attack calls:", len(CALLS))
