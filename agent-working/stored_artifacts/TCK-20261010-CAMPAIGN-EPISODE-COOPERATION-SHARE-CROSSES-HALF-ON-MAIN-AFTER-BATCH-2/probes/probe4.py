"""Re-introduce the original co-location (scratch only): every entity spawns on ONE tile; report the cooperation basis, share and per-entity-tick volume."""
import json, sys
sys.path.insert(0, ".")
from collections import Counter
from dataclasses import replace
from tests.integration.campaigns import test_catalog_entity_spawn_wiring as t
from src.domains.campaigns.orchestrator import CampaignOrchestrator
from src.domains.cooperation.services import CooperationDecisionService as S
CO = len(sys.argv) > 1 and sys.argv[1] == "colocate"
orig_build = CampaignOrchestrator._build_initial_state
def build(self, seed, spec):
    st = orig_build(self, seed, spec)
    if CO:
        first = next(iter(st.entities.values())).navigation.position
        ents = {i: replace(e, navigation=replace(e.navigation, position=first)) for i, e in st.entities.items()}
        object.__setattr__(st, "entities", ents)
    return st
CampaignOrchestrator._build_initial_state = build
basis = Counter(); needkeys = Counter(); alive_ticks = [0]
o_sel, o_acc = S.select_for_own_needs, S.accept_pending_offer
def sel(entity, help_needs, *a, **k):
    alive_ticks[0] += 0
    if help_needs:
        basis["help_need"] += 1
        for n in help_needs: needkeys[n.key] += 1
    elif entity.identity.group_id is not None: basis["group_member_no_need"] += 1
    else: basis["other"] += 1
    return o_sel(entity, help_needs, *a, **k)
def acc(entity, offer, *a, **k):
    basis["incoming_offer"] += 1
    return o_acc(entity, offer, *a, **k)
S.select_for_own_needs = staticmethod(sel); S.accept_pending_offer = staticmethod(acc)
from src.domains.cooperation.evaluators import HelpNeedEvaluator
ev_count = [0]
o_eval = HelpNeedEvaluator.evaluate
def ev(entity, state):
    ev_count[0] += 1
    return o_eval(entity, state)
HelpNeedEvaluator.evaluate = staticmethod(ev)
out = {}; pc = pt = pe = 0
for seed in t._EPISODE_SEEDS:
    basis.clear(); needkeys.clear(); ev_count[0] = 0
    try:
        evt, _ = t._run_episode(seed)
    except AssertionError as e:
        out[str(seed)] = {"precondition_failed": str(e)[:160]}; continue
    c = evt.get("cooperation_event", 0); tot = sum(evt.values())
    pc += c; pt += tot; pe += ev_count[0]
    out[str(seed)] = {"coop": c, "total": tot, "alive_entity_ticks": ev_count[0], "per_entity_tick": round(c / max(1, ev_count[0]), 4), "basis": dict(basis), "needkeys": dict(needkeys)}
out["pooled_share"] = round(pc / max(1, pt), 4); out["pooled_per_entity_tick"] = round(pc / max(1, pe), 4)
print("PROBE " + json.dumps(out, sort_keys=True))
