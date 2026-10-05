"""Per-tick regional trauma_score for the first ticks, plus which entities died. usage: trauma_ticks.py <root> <world> <ticks>"""
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
prev_alive = {e.id for e in state.entities.values() if e.combat.alive}
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        alive = {e.id for e in st.entities.values() if e.combat.alive}
        died = sorted(prev_alive - alive)
        prev_alive = alive
        print("T", st.tick, {r.id: round(r.trauma_score, 2) for r in st.regions.values()}, "died", died,
              "stability", {r.id: round(r.stability, 2) for r in st.regions.values()} if st.tick <= 2 else "")
finally:
    k.shutdown()
