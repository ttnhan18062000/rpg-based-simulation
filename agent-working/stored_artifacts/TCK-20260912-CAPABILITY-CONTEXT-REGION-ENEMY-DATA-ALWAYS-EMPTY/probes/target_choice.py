"""KNOW-04 before/after on target choice. Usage: python target_choice.py <world> <ticks>

Runs one world under a PINNED NORMAL governor (audit_mode, tick budget off). At every tactical decision the same state is decided
twice, once with the real capability term (folk-belief prior) and once with the old constant term, and the chosen target ids are
compared, so the count of changed choices is measured on identical states (not between two diverging runs). The whole run is
repeated and the final canonical hashes compared (determinism check)."""
import collections, json, sys
sys.path.insert(0, ".")
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine import tactical
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.checkpoint import CanonicalStateHasher
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.core.governance import RuntimeMode

class PinnedNormal(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None

def run(world, ticks):
    spec, ctx = WorldRepository("data/worlds").load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, seed=42, context=ctx)
    prof = RuntimeProfile(name="p", hardware_class=HardwareClass.CLASS_B, max_ram_mb=2048, max_cpu_percent=100.0, max_worker_count=1,
                          max_queue_depth=2000, max_replay_buffer_kb=0, max_observability_budget_percent=0.0, max_tick_budget_ms=1e9)
    k = Kernel(profile=prof, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True, "audit_mode": True}, governor=PinnedNormal())
    c = collections.Counter(); real = tactical.combat_capability_against; orig = tactical.TacticalDecisionSystem.evaluate_entity_intent
    def tid(u):
        t = getattr(u, "task", None); p = getattr(t, "payload_set", None) or {}
        return p.get("target_id")
    def wrapped(st, ent, *a, **kw):
        new = orig(st, ent, *a, **kw)
        n = tid(new)
        if n is not None:
            c["decisions_with_target"] += 1
            tactical.combat_capability_against = lambda e, h: 0.0   # the old term: one constant for every hostile
            try: old = tid(orig(st, ent, *a, **kw))
            finally: tactical.combat_capability_against = real
            if old != n: c["changed"] += 1
        else: c["decisions_without_target"] += 1
        return new
    tactical.TacticalDecisionSystem.evaluate_entity_intent = staticmethod(wrapped)
    try:
        for _ in range(ticks): k.tick_once()
    finally:
        tactical.TacticalDecisionSystem.evaluate_entity_intent = orig
    alive = sum(1 for e in k.state.entities.values() if e.combat.alive)
    h = CanonicalStateHasher.get_hash(k.state)
    return dict(c), alive, h

world, ticks = sys.argv[1], int(sys.argv[2])
a = run(world, ticks); b = run(world, ticks)
print("RESULT", json.dumps({"world": world, "ticks": ticks, "run1": a, "run2": b, "deterministic": a == b}))
