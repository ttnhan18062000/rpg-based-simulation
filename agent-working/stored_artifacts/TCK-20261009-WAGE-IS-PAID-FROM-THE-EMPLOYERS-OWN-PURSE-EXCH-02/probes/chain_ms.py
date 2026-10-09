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
cur = {"tick": 0}
kinds = collections.Counter(); tax_total = 0; tax_payers = collections.Counter(); events = collections.defaultdict(list)
orig = R.resolve
def hook(st, ent, intent, *a, **kw):
    global tax_total
    out = orig(st, ent, intent, *a, **kw)
    if out.accepted:
        kinds[(intent.source_kind, intent.transfer_kind)] += 1
        if intent.source_kind == "TAX" and ent.inventory.gold < 10:
            tax_total += abs(intent.gold_delta); tax_payers[ent.id] += abs(intent.gold_delta)
        if intent.source_kind == "SHOP_SELL": events[ent.id].append(("sale", st.tick))
        if intent.source_kind in ("TOWN_SERVICE", "CARRIED_FOOD") and intent.transfer_kind == "EAT": events[ent.id].append(("meal", st.tick))
        if intent.source_kind == "TOWN_SERVICE" and intent.transfer_kind == "EAT": pass
    return out
R.resolve = staticmethod(hook)
def group(e):
    sp = (e.identity.properties or {}).get("species_id"); role = str(e.identity.role).split(".")[-1].lower(); kind = str(e.kind).lower()
    if sp in ("wolf", "spider", "deer", "boar", "bear", "rat", "snake") or kind in ("predator_hunter", "alpha"): return "wildlife"
    if sp in ("goblin", "orc", "bandit") or kind in ("raider", "leader"): return "raiders" if not (sp == "goblin" and kind == "scout") else "raiders"
    if sp == "undead": return "undead"
    if kind == "merchant" or "merchant" in role: return "merchants"
    if sp == "human" and kind in ("worker", "blacksmith"): return "town_workers"
    if sp == "human": return "town_guards_scouts"
    return "heroes_other"
alive = {}; galive = collections.defaultdict(dict)
for t in range(TICKS):
    k.tick_once()
    if t + 1 in (1000, 2500, 5000):
        alive[t + 1] = sum(1 for e in k.state.entities.values() if e.combat.alive)
        for e in k.state.entities.values():
            if e.combat.alive: galive[group(e)][t + 1] = galive[group(e)].get(t + 1, 0) + 1
st = k.state
dead = collections.Counter(str(e.lifecycle.death_reason) for e in st.entities.values() if not e.combat.alive)
gstat = {}
for e in st.entities.values():
    g = gstat.setdefault(group(e), dict(n=0, dead=collections.Counter(), ate=0, hunger_sum=0.0))
    g["n"] += 1; g["hunger_sum"] += e.biological.hunger
    if not e.combat.alive: g["dead"][str(e.lifecycle.death_reason)] += 1
    if e.biological.last_meal_tick and e.biological.last_meal_tick > 0: g["ate"] += 1
groups = {k_: dict(n=v["n"], dead=dict(v["dead"]), ever_ate=v["ate"], mean_hunger_end=round(v["hunger_sum"] / max(1, v["n"]), 1), alive_at=galive.get(k_, {})) for k_, v in gstat.items()}
digest = hashlib.sha256(repr(sorted((i, e.combat.alive, round(e.biological.hunger, 3), e.inventory.gold, e.navigation.position) for i, e in st.entities.items())).encode()).hexdigest()[:16]
fed = taxed = 0; gaps = []
for eid, ev in events.items():
    for j, (kind, tk) in enumerate(ev):
        if kind != "sale": continue
        nxt = next((t2 for k2, t2 in ev[j + 1:] if k2 == "meal"), None)
        if nxt is None: taxed += 1
        else: fed += 1; gaps.append(nxt - tk)
k.shutdown()
print("CH", json.dumps(dict(label=LABEL, world=WORLD, seed=SEED, ticks=TICKS, alive=alive, deaths_by_reason=dict(dead), kinds={f"{a}/{b}": v for (a, b), v in kinds.items()},
    tax_poor_total=tax_total, tax_poor_payers=len(tax_payers), sales=fed + taxed, sales_then_meal=fed, sales_no_meal_after=taxed,
    groups=groups, median_sale_to_meal=(statistics.median(gaps) if gaps else None), digest=digest)))
