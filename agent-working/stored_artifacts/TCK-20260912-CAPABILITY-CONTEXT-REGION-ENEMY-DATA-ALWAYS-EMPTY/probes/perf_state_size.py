import sys, time, dataclasses, json
sys.path.insert(0, ".")
from src.perf.scenarios import build_movement_state
from src.cognition.common_knowledge import default_self_model
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.checkpoint import CanonicalStateHasher
from src.platform.rng import DeterministicRNG
from src.core.governance import RuntimeMode
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, p, s): return RuntimeMode.NORMAL
    def force_mode(self, *a, **k): return None
def make(n, seeded):
    st = build_movement_state(entity_count=n)
    if seeded:
        sm = default_self_model()
        st = dataclasses.replace(st, entities={i: dataclasses.replace(e, self_model=sm) for i, e in st.entities.items()})
    return st
def run(n, seeded, warm=2, samp=8):
    st = make(n, seeded)
    prof = RuntimeProfile(name="p", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=100.0, max_worker_count=1, max_queue_depth=20000, max_replay_buffer_kb=0, max_observability_budget_percent=0.0, max_tick_budget_ms=1e9)
    k = Kernel(profile=prof, state=st, rng=DeterministicRNG(42), flags={"no_frame_pacing": True, "audit_mode": True}, governor=Pin())
    for _ in range(warm): k.tick_once()
    t = time.perf_counter()
    for _ in range(samp): k.tick_once()
    tick_ms = (time.perf_counter() - t) / samp * 1000
    t = time.perf_counter(); CanonicalStateHasher.get_hash(k.state); hash_ms = (time.perf_counter() - t) * 1000
    return tick_ms, hash_ms
n = int(sys.argv[1]); out = {"bare": [], "seeded": []}
for _ in range(2):
    for name, seeded in (("bare", False), ("seeded", True)):
        out[name].append(run(n, seeded))
print("RESULT", json.dumps(out))
