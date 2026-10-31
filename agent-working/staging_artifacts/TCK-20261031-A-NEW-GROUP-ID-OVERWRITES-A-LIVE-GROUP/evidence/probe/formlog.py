import sys, runpy, json
sys.path.insert(0, ".")
from src.systems.world_systems.groups import GroupSystem
import src.core.state as st
ou = GroupSystem.update_groups
cur = []
oi = st.GroupRecord.__init__
def ini(self, *a, **k):
    oi(self, *a, **k)
    if sys._getframe(1).f_globals.get("__name__") == "src.systems.world_systems.groups": cur.append(self)
st.GroupRecord.__init__ = ini
def ug(state, *a, **k):
    cur.clear(); r = ou(state, *a, **k)
    for g in cur:
        sys.stderr.write("FORM %s\n" % json.dumps([state.tick, g.id, sorted(g.member_ids), g.id in state.groups]))
    return r
GroupSystem.update_groups = staticmethod(ug)
sys.argv = ["kernel_scenario"] + sys.argv[1:]
runpy.run_module("tests.unit.observability.extractor_characterization.kernel_scenario", run_name="__main__")
