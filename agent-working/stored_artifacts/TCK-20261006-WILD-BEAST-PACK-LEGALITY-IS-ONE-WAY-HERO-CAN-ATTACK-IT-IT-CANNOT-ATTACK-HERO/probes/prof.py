import cProfile, pstats
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
st = build_movement_state(entity_count=1000)
k = Kernel(profile=PERF_PROFILES["PERF_2GB_LOCAL"], state=st, rng=DeterministicRNG(42))
k.tick_once(); k.tick_once()
pr = cProfile.Profile(); pr.enable(); k.tick_once(); pr.disable()
pstats.Stats(pr).sort_stats("cumulative").print_stats(r"faction|relation|legality|combat_engagement|hostil|project", 22)
