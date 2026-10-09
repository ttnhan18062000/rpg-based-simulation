"""Earning-chain pinned measurement. usage: chain_ms.py <root> <world> <ticks> <seed> <label>
Pinned NORMAL governor + audit_mode + budget off + LocalSequentialExecutor. Hooks the resolver to count accepted transfers by kind."""
import collections, hashlib, json, statistics, sys
ROOT, WORLD, TICKS, SEED, LABEL = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.core.conservation import ResourceTransactionResolver as R
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())


import collections, math
from src.engine.combat import CombatResolutionSystem as C
last_hit = {}
o_res = C.resolve_attack
def hit(attacker, defender, state, *a, **kw):
    out = o_res(attacker, defender, state, *a, **kw); last_hit[defender.id] = (state.tick, attacker.id); return out
C.resolve_attack = staticmethod(hit)
eats = collections.defaultdict(lambda: collections.deque(maxlen=15))
orig = R.resolve
def hook(st, ent, intent, *a, **kw):
    out = orig(st, ent, intent, *a, **kw)
    if intent.transfer_kind == "EAT" or intent.source_kind in ("TOWN_SERVICE", "CARRIED_FOOD", "FORAGE"):
        eats[ent.id].append((st.tick, intent.source_kind, intent.transfer_kind, bool(out.accepted), str(getattr(out, "reason", None))[:40], ent.inventory.gold))
    return out
R.resolve = staticmethod(hook)
def group(e):
    sp = (e.identity.properties or {}).get("species_id"); role = str(e.identity.role).split(".")[-1].lower(); kind = str(e.kind).lower()
    if sp in ("wolf", "spider", "deer", "boar", "bear", "rat", "snake") or kind in ("predator_hunter", "alpha"): return "wildlife"
    if sp in ("goblin", "orc", "bandit") or kind in ("raider", "leader"): return "raiders"
    if sp == "undead": return "undead"
    if kind == "merchant" or "merchant" in role: return "merchants"
    if sp == "human" and kind in ("worker", "blacksmith"): return "town_workers"
    if sp == "human": return "town_guards_scouts"
    return "heroes_other"
WATCH = ("heroes_other", "town_guards_scouts")
gmap = {i: group(e) for i, e in k.state.entities.items()}
ring = collections.defaultdict(lambda: collections.deque(maxlen=25)); sig = {}
def dist(a, b): return round(math.hypot(a[0]-b[0], a[1]-b[1]), 1)
def nearest(st, pos, kinds):
    best = None
    for b in st.buildings.values():
        if str(b.kind).lower() in kinds:
            d = dist(pos, b.position)
            if best is None or d < best: best = d
    return best
def nearest_food(st, pos):
    best = None
    for n in st.resource_nodes.values():
        if getattr(n, "yields_item", "") in ("berries", "berry", "wild_berries") or "berr" in str(getattr(n, "yields_item", "")) or str(n.kind).upper() in ("BERRY", "FOOD"):
            if n.remaining_charges > 0:
                d = dist(pos, n.position)
                if best is None or d < best: best = d
    return best
deaths = []; seen_dead = set()
for t in range(TICKS):
    k.tick_once()
    st = k.state
    for i, e in st.entities.items():
        g = gmap.get(i) or group(e)
        if g not in WATCH: continue
        if e.combat.alive:
            pl = e.task.payload or {}
            s = (e.task.work_kind, str(e.interaction.kind), e.interaction.target_node_id, str(e.navigation.movement_mode), e.navigation.target, e.navigation.last_failure_reason, repr(pl)[:150])
            if sig.get(i) != s:
                sig[i] = s
                pos = e.navigation.position
                ring[i].append(dict(t=t+1, wk=s[0], tk=s[1], node=s[2], mode=s[3], tgt=s[4], fail=s[5], pl=s[6], hunger=round(e.biological.hunger, 1), gold=e.inventory.gold, pos=[round(pos[0]), round(pos[1])], d_inn=nearest(st, pos, ("inn", "tavern")), d_food=nearest_food(st, pos), food_items=sum(x.quantity for x in e.inventory.items if "meal" in x.item_id or "berr" in x.item_id or "bread" in x.item_id)))
        elif i not in seen_dead:
            seen_dead.add(i); lh = last_hit.get(i); recent = lh is not None and t + 1 - lh[0] <= 3
            cause = "COMBAT" if recent else str(e.lifecycle.death_reason if e.lifecycle.death_reason else getattr(e.lifecycle.passive_death_cause, "name", e.lifecycle.passive_death_cause))
            d = dict(id=i, group=g, tick=t+1, cause=cause, gold=e.inventory.gold, ever_ate=bool((e.biological.last_meal_tick or 0) > 0), last_meal=e.biological.last_meal_tick)
            if cause != "COMBAT":
                d["ring"] = list(ring[i]); d["eats"] = list(eats[i])
            deaths.append(d)
k.shutdown()
print("TR2", json.dumps(dict(label=LABEL, world=WORLD, seed=SEED, deaths=deaths), default=str))
