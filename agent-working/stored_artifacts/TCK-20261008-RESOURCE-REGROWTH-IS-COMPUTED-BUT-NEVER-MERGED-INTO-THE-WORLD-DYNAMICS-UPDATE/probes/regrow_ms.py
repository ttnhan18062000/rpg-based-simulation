"""All-gatherer effect probe. usage: regrow_ms.py <root> <world> <ticks> <seed> [label]. Pinned NORMAL + audit_mode + budget off."""
import collections, hashlib, json, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); LABEL = sys.argv[5] if len(sys.argv) > 5 else ""
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
prev = {}; harv = collections.Counter(); regen = collections.Counter(); dead = {}; R = {}; recovered = 0; nodes0 = len(state.resource_nodes)
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for i, n in st.resource_nodes.items():
            if i in prev:
                d = n.remaining_charges - prev[i]
                if d < 0: harv[n.kind] += -d
                elif d > 0: regen[n.kind] += d
            prev[i] = n.remaining_charges
        for e in st.entities.values():
            if e.id not in dead and not (e.combat.alive and e.lifecycle.active):
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                dead[e.id] = str(getattr(c, "value", c))
        if st.tick in (1000, 1100):
            R[f"alive_t{st.tick}"] = sum(1 for e in st.entities.values() if e.combat.alive and e.lifecycle.active)
finally:
    k.shutdown()
end = k.state
dig = hashlib.sha256(json.dumps(sorted((e.id, round(e.navigation.position[0], 3), round(e.navigation.position[1], 3), round(e.combat.hp, 2), e.combat.alive, round(e.biological.hunger, 2), e.inventory.gold) for e in end.entities.values()) + sorted(dead.items()) + sorted((i, n.remaining_charges) for i, n in end.resource_nodes.items())).encode()).hexdigest()[:16]
inv_items = sum(s.quantity for e in end.entities.values() for s in e.inventory.items)
print("MS", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, **R, deaths=len(dead), digest=dig, harvested=sum(harv.values()), regrown=sum(regen.values()), harvested_by_kind=dict(harv), regrown_by_kind=dict(regen),
      nodes_end=len(end.resource_nodes), nodes_start=nodes0, charges_end=sum(n.remaining_charges for n in end.resource_nodes.values()), items_carried_end=inv_items, **{f"d_{c}": n for c, n in collections.Counter(dead.values()).items()})))
