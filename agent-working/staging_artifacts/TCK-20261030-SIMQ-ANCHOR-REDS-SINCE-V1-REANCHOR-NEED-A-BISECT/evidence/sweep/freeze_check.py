"""Existing-log check (no run): last event tick, events per 250-tick window, deaths/spawns, alive count, final state_hash, per sweep run dir. Usage: freeze_check.py <rundir>..."""
import json, sys, collections
for d in sys.argv[1:]:
    m = json.load(open(d + "/run_manifest.json"))
    ev = collections.Counter(); last = 0; win = collections.Counter(); dead = set(); born = 0; types = collections.Counter(); lastby = {}
    for l in open(d + "/simulation_events.jsonl"):
        e = json.loads(l); t = e.get("tick", 0); et = e.get("event_type"); types[et] += 1; last = max(last, t); win[t // 250] += 1; lastby[et] = max(lastby.get(et, 0), t)
        if et in ("entity_killed", "entity_died", "death"): dead.add(e.get("payload", {}).get("entity_id") or e.get("entity_id"))
        if et in ("entity_born", "entity_spawned", "birth"): born += 1
    ps = {k: lastby[k] for k in ("entity_killed", "combat_resolved", "hazard_drain_applied", "region_trauma_delta", "ecology_cycle_completed", "xp_gained", "level_up", "quest_completed", "reward_granted") if k in lastby}
    print(d.split("/")[0], d.split("/")[-1][:34], "ticks", m["ticks_completed"], "state_hash", m["state_hash"][:16], "| last event tick", last, "| events per 250t", [win[i] for i in range(0, 8)], "| deaths(entity_killed)", types.get("entity_killed", 0), "| last tick of", ps)
