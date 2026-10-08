"""Multi-seed need metrics. usage: need_ms.py <root> <world> <ticks> <seed> [label]. Env NEED_ONSET/NEED_FULL/NEED_AMP override the curve."""
import collections, hashlib, json, os, sys
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
try:
    import src.ai.goals.need_pull as NP
    for env, attr in (("NEED_ONSET", "ESCALATION_ONSET"), ("NEED_FULL", "ESCALATION_FULL"), ("NEED_AMP", "ESCALATION_AMPLITUDE")):
        if os.environ.get(env): setattr(NP, attr, float(os.environ[env]))
except ImportError:
    pass
class PinnedNormalGovernor(ResourceGovernor):
    """Pins NORMAL (host speed and the mid-tick wall-clock throttle must not change the run), as test_catalog_entity_spawn_wiring does."""
    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick):
        return None

spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
           governor=(None if os.environ.get('NEED_UNPINNED') else PinnedNormalGovernor()), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
dead = {}; GOLD = {}; R = {}; NA = collections.Counter(); NA_ENT = collections.defaultdict(set)
try:
    from src.ai.goals.scorers import EatScorer
    _sc = EatScorer.score
    def _score(self, entity, state):
        r = _sc(self, entity, state)
        a = getattr(r, "need_access", None)
        if a is not None and entity.biological.hunger >= 60.0:
            NA[str(a.value)] += 1; NA_ENT[str(a.value)].add(entity.id)
        return r
    EatScorer.score = _score
except Exception:
    pass
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        for e in st.entities.values():
            if e.id not in dead and e.combat.alive and e.lifecycle.active:
                GOLD[e.id] = e.inventory.gold
            if e.id not in dead and not (e.combat.alive and e.lifecycle.active):
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                dead[e.id] = str(getattr(c, "value", c))
        if st.tick in (1000, 1100):
            R[f"alive_t{st.tick}"] = sum(1 for e in st.entities.values() if e.combat.alive and e.lifecycle.active)
finally:
    k.shutdown()
dig = hashlib.sha256(json.dumps(sorted((e.id, round(e.navigation.position[0], 3), round(e.navigation.position[1], 3), round(e.combat.hp, 2), e.combat.alive, round(e.biological.hunger, 2), round(e.biological.sleep_debt, 2), e.inventory.gold) for e in k.state.entities.values()) + sorted(dead.items())).encode()).hexdigest()[:16]
starved = [i for i, c in dead.items() if c == "STARVATION"]
poverty = dict(starved_broke=sum(1 for i in starved if GOLD.get(i, 0) < 5), starved_could_pay=sum(1 for i in starved if GOLD.get(i, 0) >= 5))
out = dict(R, **poverty, **{f'eat_hot.{a}.calls': n for a, n in NA.items()}, **{f'eat_hot.{a}.entities': len(v) for a, v in NA_ENT.items()}, digest=dig, pinned=not os.environ.get("NEED_UNPINNED"), deaths=len(dead), **{f"d_{c}": n for c, n in collections.Counter(dead.values()).items()})
print("MS", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, **out)))
