import cProfile, pstats, io, sys, collections
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, ROOT)
from src.engine.scheduler import DeterministicScheduler as DS
from src.engine.lod import LODService
from src.engine.candidate_selector import MovementCandidateSelector as MCS
C = collections.Counter()
_w = DS._is_woken
def w(ent, state, work_kind, idx):
    r = _w(ent, state, work_kind, idx)
    if r:
        C["wakes"] += 1
        if not LODService.should_execute(state.tick, ent, [state.town_center]): C["wakes_lod_would_skip"] += 1
    return r
DS._is_woken = staticmethod(w)
sys.argv = ['x', ROOT, WORLD, str(TICKS), str(SEED), 'base']
src = open(sys.argv[0] if False else '/tmp/claude-1000/ZZ').read() if False else None
import runpy
pr = cProfile.Profile(); pr.enable()
g = runpy.run_path(__import__('os').environ['PROBE'], run_name='__main__')
pr.disable()
s = io.StringIO(); ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(r'scheduler\.py|candidate_selector\.py.*(unengaged|_adjacent|position_index)|hostility\.py.*perceived', 10)
print("WAKES", dict(C)); print(s.getvalue()[-2600:])
