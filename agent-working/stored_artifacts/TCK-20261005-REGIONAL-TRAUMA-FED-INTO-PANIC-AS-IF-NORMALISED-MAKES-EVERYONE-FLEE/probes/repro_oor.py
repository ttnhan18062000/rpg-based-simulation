"""Constructed reproduction: a melee ATTACK task against a live hostile at Manhattan distance 2 (diagonal).
usage: repro_oor.py <root>. Run against a tree WITHOUT the dread change to show independence."""
import sys

sys.path.insert(0, sys.argv[1])
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.pipeline_phases.actions import ActionRoutingPhase


def mk(eid, x, y, faction, readiness=100.0):
    return (V2EntityBuilder(eid).kind("monster").location(x, y)
            .combat(hp=100, max_hp=100, alive=True, readiness=readiness, attack_range=1)
            .lifecycle(active=True).identity(faction=faction).build())


payload = {"action": "ATTACK", "target_id": 2}
for dist_name, (tx, ty) in {"orthogonal (dist 1)": (10.0, 11.0), "diagonal (dist 2)": (11.0, 11.0), "far (dist 5)": (10.0, 15.0)}.items():
    state = AuthoritativeState(tick=1, seed=42, entities={1: mk(1, 10.0, 10.0, Faction.HERO_GUILD), 2: mk(2, tx, ty, Faction.MONSTER_HORDE)})
    upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=dict(payload)))})
    refined = ActionRoutingPhase.route(state, upd)
    task = refined.entity_updates[1].task
    p = task.payload_set
    is_idle_act = bool(p) is False
    print(f"{dist_name}: payload_after={p} -> scheduler is_idle_act={is_idle_act} (False means the brain is NOT re-run next tick);",
          "readiness_delta", refined.entity_updates[1].readiness_delta)
