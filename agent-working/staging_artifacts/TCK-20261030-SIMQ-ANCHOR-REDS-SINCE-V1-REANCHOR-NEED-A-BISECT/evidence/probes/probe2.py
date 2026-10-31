"""Read-only probe (scratch, not in the repo). Usage: PROBE_OUT=<jsonl> python probe2.py <scenario_key>   (cwd = a commit tree)
Runs tools/evaluate_simq.py --scenario <key> in-process and logs, for ALL entities:
  sc : every GoalRegistry.get_all_scores call (tick, entity, all scores)
  rp : every scorers.retreat_pull call whose output differs from its input (only exists at d914bace7)
  st : per tick, per entity: position, hp, alive, current project, nav target, group id (from the GroupSystem.update_groups hook, every tick)
"""
import json, os, sys, runpy
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
cur = {"tick": None, "eid": None}
from src.ai.goals import base as gbase
import src.ai.goals.scorers as sc
import src.ai.goals
orig_all = gbase.GoalRegistry.get_all_scores.__func__
def get_all(cls, entity, state):
    cur["tick"], cur["eid"] = state.tick, entity.id
    res = orig_all(cls, entity, state)
    log(k="sc", t=state.tick, e=entity.id, s=[[str(s.kind), round(s.utility, 6), s.target_id] for s in res])
    return res
gbase.GoalRegistry.get_all_scores = classmethod(get_all)
if hasattr(sc, "retreat_pull"):
    orig_rp = sc.retreat_pull
    def rp(raw, hp_ratio):
        out = orig_rp(raw, hp_ratio)
        if out != raw: log(k="rp", t=cur["tick"], e=cur["eid"], raw=raw, hp=hp_ratio, out=out)
        return out
    sc.retreat_pull = rp
from src.systems.world_systems.groups import GroupSystem
orig_ug = GroupSystem.update_groups
def ug(state, current_update=None):
    for eid in sorted(state.entities):
        e = state.entities[eid]
        log(k="st", t=state.tick, e=eid, p=e.navigation.position, hp=e.combat.hp, a=e.combat.alive, pr=e.strategic.current_project_id, nt=e.navigation.target, g=e.identity.group_id)
    return orig_ug(state, current_update)
GroupSystem.update_groups = staticmethod(ug)
sys.argv = ["evaluate_simq", "--scenario", sys.argv[1]]
try:
    runpy.run_path("tools/evaluate_simq.py", run_name="__main__")
except SystemExit as ex:
    log(k="exit", code=str(ex.code))
OUT.close()
