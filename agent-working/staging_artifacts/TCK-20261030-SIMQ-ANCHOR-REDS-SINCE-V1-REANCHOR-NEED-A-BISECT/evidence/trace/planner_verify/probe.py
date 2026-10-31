"""Planner verification probe (local only): logs every group objective issued by GroupSystem.update_groups, read-only."""
import json, sys
sys.path.insert(0, ".")
OUT = open(sys.argv[1], "w")
from src.systems.world_systems.groups import GroupSystem
orig = GroupSystem.update_groups
def ug(state, current_update=None):
    res = orig(state, current_update)
    for eid, u in sorted((getattr(res, "entity_updates", None) or {}).items()):
        s = getattr(u, "strategic", None)
        for d in (getattr(s, "directives_add_or_update", None) or []):
            if d.kind == "GROUP_OBJECTIVE":
                OUT.write(json.dumps({"tick": state.tick, "e": eid, "id": d.id, "target": str(d.target)}) + "\n")
    return res
GroupSystem.update_groups = staticmethod(ug)
from tools.calibrate_simq import _load_profile_feature_flags, _resolve_profile, _run_engine
flags = _load_profile_feature_flags(_resolve_profile("urban_political_selfmodel_probe"))
r = _run_engine("urban_political", 42, 200, extra_flags=flags, audit_mode=True)
OUT.close(); print("DONE", r[2])
