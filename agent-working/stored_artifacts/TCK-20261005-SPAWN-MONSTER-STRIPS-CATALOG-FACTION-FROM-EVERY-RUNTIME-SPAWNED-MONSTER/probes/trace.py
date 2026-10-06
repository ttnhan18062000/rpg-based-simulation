import sys
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
st = compile_world("frontier_living_world", DEFAULT_SEED)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=st, rng=DeterministicRNG(DEFAULT_SEED), flags={**DEFAULT_FLAGS, "audit_mode": True})
for t in range(1503):
    k.tick_once()
    if t >= 1496:
        s = k._state
        print("tick_after", t+1, "state.tick", s.tick, {i: (s.entities[i].navigation.position, s.entities[i].combat.alive) for i in (22,52,54) if i in s.entities}, flush=True)
