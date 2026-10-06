"""Per-tick trace of one entity holding an ATTACK task. usage: trace49.py <root> <world> <ticks> <entity_id>"""
import sys

ROOT, WORLD, TICKS, EID = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
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
shown = 0
last = None
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        e = st.entities.get(EID)
        if e is None:
            continue
        p = e.task.payload or {}
        tid = p.get("target_id")
        t = st.entities.get(tid) if tid is not None else None
        row = (e.task.work_kind, p.get("action"), tid, p.get("outcome"), p.get("reason"), e.combat.alive)
        if p.get("action") == "ATTACK" and p.get("outcome") == "FAILURE":
            if shown < 14 or shown % 40 == 0:
                print("T", st.tick, "pos", e.navigation.position, "hp", e.combat.hp, "ready", e.combat.readiness, "task", row,
                      "tgt_pos", t.navigation.position if t else None, "tgt_alive", t.combat.alive if t else None,
                      "tgt_active", t.lifecycle.active if t else None, "nav_dest", getattr(e.navigation, "destination", None),
                      "stale", p.get("stale_ticks"))
            shown += 1
        elif last is not None and last[1] == "ATTACK" and last[3] == "FAILURE" and row != last:
            print("LOOP-END T", st.tick, "task", row, "after", shown, "failing ticks")
            shown = 0
        last = row
finally:
    k.shutdown()
print("TOTAL failing ATTACK ticks held (since last end):", shown)
