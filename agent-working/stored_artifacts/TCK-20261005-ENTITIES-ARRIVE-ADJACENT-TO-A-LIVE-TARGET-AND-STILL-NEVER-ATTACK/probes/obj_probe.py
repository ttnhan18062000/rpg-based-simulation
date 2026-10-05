"""Read-only probe: how a combat-engage objective behaves on the current tree.
usage: obj_probe.py <label> <world> [ticks]
Counts, per objective sample (entity with a current objective whose project kind is COMBAT):
objective kind/status, whether `target` names a live entity, distance from the entity's navigation
target to that entity's live position, and every status transition ever observed.
Also wraps TacticalDecisionSystem._resolve_target_position to see who still calls it for combat objectives.
"""
import collections
import hashlib
import json
import sys

ROOT = "/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/lane-a-tactical-path-batch"
OUT = "/tmp/claude-1000/-home-u24desktop-Working-rpg-based-simulation/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad"
sys.path.insert(0, ROOT)
label, world = sys.argv[1], sys.argv[2]
TICKS = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
ARM = sys.argv[4] if len(sys.argv) > 4 else "fixed"

from src.config.profiles import PROD_SMALL
from src.core.strategic import ObjectiveKind, ProjectKind
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
seen_status = collections.defaultdict(set)

_orig = T._resolve_target_position


def wrapped(state, obj):
    r = _orig(state, obj)
    ent = None
    try:
        ent = state.entities.get(int(obj.target))
    except (TypeError, ValueError):
        pass
    if ent is not None:
        C["resolve.called_with_entity_target"] += 1
        C[f"resolve.kind.{getattr(obj.kind, 'value', obj.kind)}"] += 1
        if r[0] is not None and r[0] == getattr(obj, "target_position", None):
            C["resolve.returned_stale_target_position"] += 1
    return r


T._resolve_target_position = staticmethod(wrapped)
if ARM == "control":
    # Emulate the pre-change lifecycle: a combat objective is never closed by the strategic pass.
    from src.systems.strategic_systems import intelligence as _intel, work_queue as _wq
    _intel.entity_target_outcome = lambda *a, **k: None
    _wq.entity_target_outcome = lambda *a, **k: None
from src.engine.domain.combat_actions import CombatActions as _CA
from src.engine.combat import CombatResolutionSystem as _CR
_ea = _CA.execute_attack
def _w_ea(*a, **k):
    C["attacks.execute_attack_dispatch"] += 1
    return _ea(*a, **k)
_CA.execute_attack = staticmethod(_w_ea)
_ra = _CR.resolve_attack
def _w_ra(*a, **k):
    C["attacks.resolve_attack_calls"] += 1
    return _ra(*a, **k)
_CR.resolve_attack = staticmethod(_w_ra)
first_ended = {}      # (eid, pid) -> tick the end condition first held for a live holder
ended_delay = []
closed_seen = set()      # ticks from end-condition to project leaving ACTIVE
proj_status = collections.defaultdict(set)   # project id -> statuses observed
proj_kind = {}

repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(world)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
kernel = Kernel(
    profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}),
    state=state,
    rng=DeterministicRNG(42),
    flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
    executor=LocalSequentialExecutor(),
)
try:
    for _ in range(TICKS):
        kernel.tick_once()
        st = kernel.state if hasattr(kernel, "state") else state
        for e in st.entities.values():
            s = e.strategic
            for pid, pr in s.projects.items():
                if getattr(pr.kind, "value", pr.kind) == "combat_engage":
                    proj_status[(e.id, pid)].add(str(getattr(pr.status, "value", pr.status)))
                    _k = (e.id, pid)
                    if _k in first_ended and _k not in closed_seen and str(getattr(pr.status, "value", pr.status)) in ("COMPLETED", "ABANDONED"):
                        closed_seen.add(_k)
                        ended_delay.append(st.tick - first_ended[_k])
            if not e.combat.alive:
                C['dead_holder_samples_excluded'] += 1 if (s.current_objective_id and s.current_project_id) else 0
                continue
            if not s.current_objective_id or not s.current_project_id:
                continue
            proj = s.projects.get(s.current_project_id)
            if proj is None:
                continue
            obj = next((o for o in proj.objectives if o.id == s.current_objective_id), None)
            if obj is None:
                continue
            kind_v = getattr(obj.kind, "value", obj.kind)
            pk = getattr(proj.kind, "value", proj.kind)
            is_combat = (pk in ("combat", "combat_engage")) or kind_v == "defeat_enemy" or str(obj.id).startswith(
                ("combat_engage", "COMBAT_ENGAGE")
            )
            if not is_combat:
                continue
            C["samples"] += 1
            C[f"obj_kind.{kind_v}"] += 1
            C[f"status.{getattr(obj.status, 'value', obj.status)}"] += 1
            seen_status[obj.id].add(str(getattr(obj.status, "value", obj.status)))
            tgt = None
            try:
                tgt = st.entities.get(int(obj.target))
            except (TypeError, ValueError):
                pass
            if tgt is None:
                C["target_not_entity"] += 1
                continue
            C["target_is_entity"] += 1
            _ended = (not tgt.combat.alive) or (abs(e.navigation.position[0] - tgt.navigation.position[0]) + abs(e.navigation.position[1] - tgt.navigation.position[1]) > 10.0)
            if _ended and (e.id, proj.id) not in first_ended:
                first_ended[(e.id, proj.id)] = st.tick
            C["typed_set" if obj.target_entity_id is not None else "typed_NONE_but_target_is_entity"] += 1
            if obj.target_entity_id is None:
                C[f"typed_none.proj_kind.{pk}.obj_id_prefix.{str(obj.id)[:14]}"] += 1
            if not tgt.combat.alive:
                C["target_dead_while_objective_current"] += 1
            if abs(e.navigation.position[0] - tgt.navigation.position[0]) + abs(e.navigation.position[1] - tgt.navigation.position[1]) > 10.0:
                C["target_out_of_radius_while_objective_current"] += 1
            nav_t = e.navigation.target
            if nav_t is not None:
                d = abs(nav_t[0] - tgt.navigation.position[0]) + abs(nav_t[1] - tgt.navigation.position[1])
                C["nav_target_dist_to_live_target.0-1" if d <= 1 else "nav_target_dist_to_live_target.2-3" if d <= 3 else "nav_target_dist_to_live_target.4+"] += 1
            else:
                C["nav_target_none"] += 1
            if obj.target_position is not None:
                d = abs(obj.target_position[0] - tgt.navigation.position[0]) + abs(obj.target_position[1] - tgt.navigation.position[1])
                C["objective_target_position_stale_ge3"] += 1 if d >= 3 else 0
finally:
    kernel.shutdown()

_final = (kernel.state if hasattr(kernel, "state") else state).tick
for d in ended_delay:
    C["end_to_close_delay." + ("0-10" if d <= 10 else "11-20" if d <= 20 else "21-50" if d <= 50 else "51+")] += 1
for _k, t0 in first_ended.items():
    if _k not in closed_seen:
        d = _final - t0
        C["ended_never_closed_age." + ("0-10" if d <= 10 else "11-20" if d <= 20 else "21-50" if d <= 50 else "51+")] += 1
C["end_to_close_delay.max"] = max(ended_delay) if ended_delay else 0
C["distinct_combat_objective_ids"] = len(seen_status)
C["distinct_combat_projects"] = len(proj_status)
for (_eid, _pid), sts in proj_status.items():
    for x in sts:
        C[f"project_ever.{x}"] += 1
C["projects_ever_terminal"] = sum(1 for sts in proj_status.values() if sts & {"COMPLETED", "ABANDONED"})
C["distinct_objectives_ever_non_active"] = sum(1 for v in seen_status.values() if v - {"active", "ACTIVE"})
st = kernel.state if hasattr(kernel, "state") else state
h = hashlib.sha256()
for e in sorted(st.entities.values(), key=lambda e: e.id):
    h.update(json.dumps(e.to_canonical_dict(), sort_keys=True, default=str).encode())
out = dict(sorted(C.items()))
out["state_sha256"] = h.hexdigest()[:16]
json.dump(out, open(f"{OUT}/{label}.{world}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
