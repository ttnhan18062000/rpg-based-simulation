"""P3 FACTION trace (scratch, read-only). Usage: PROBE_OUT=<jsonl> python probe3.py <scenario_key>.
Logs (1) every FactionSentimentService.derive_from_bond_updates input that raises pairwise tension between two factions
(tick, source entity, target entity, factions, tension bump), (2) per tick the pairwise_tension of every faction pair above 0 and each pair's diplomatic state."""
import json, os, sys, runpy
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
from src.domains.faction.sentiment import FactionSentimentService as FS
from src.content_semantics.faction import get_faction_id_str
orig = FS.derive_from_bond_updates
def derive(state, update):
    if state.factions:
        for sid, eu in sorted(update.entity_updates.items()):
            if eu.social is None or not eu.social.bond_updates: continue
            se = state.entities.get(sid)
            if se is None: continue
            sf = get_faction_id_str(se)
            for bu in eu.social.bond_updates:
                te = state.entities.get(bu.target_id)
                if te is None: continue
                tf = get_faction_id_str(te)
                if tf == sf: continue
                bump = max(0.0, -bu.sentiment_delta * FS.FACTION_SCALE_FACTOR)
                if bump: log(k="bump", t=state.tick, s=sid, o=bu.target_id, sf=sf, tf=tf, b=bump)
    return orig(state, update)
FS.derive_from_bond_updates = staticmethod(derive)
from src.systems.world_systems.groups import GroupSystem
og = GroupSystem.update_groups
def ug(state, current_update=None):
    for fid, f in sorted(state.factions.items()):
        for o, v in sorted(f.pairwise_tension.items()):
            if v: log(k="ten", t=state.tick, f=fid, o=o, v=round(v, 6), d=str(f.diplomatic_relations.get(o)))
    return og(state, current_update)
GroupSystem.update_groups = staticmethod(ug)
sys.argv = ["evaluate_simq", "--scenario", sys.argv[1]]
try: runpy.run_path("tools/evaluate_simq.py", run_name="__main__")
except SystemExit: pass
OUT.close()
