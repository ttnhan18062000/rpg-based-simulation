"""Ruling 7 'same record' confirmation. For each length of a world/seed, the first differing event record (event_id and run_id excluded; run-end *_tally events at a run's own last tick excluded)
between a25619971 and d914bace7 in the sweep's run directories is compared with the same first differing record of the probe pair (P3 for s42, P1 for s123).
State equality inside the prefix is inferred from the event stream, not hashed (there is no per-tick state hash in the logs)."""
import json
S = "/data/vboxuser/Work/simq_sweep/"; O = "/data/vboxuser/Work/simq_probes/out/"
def evs(d):
    last = json.load(open(d + "/run_manifest.json"))["ticks_completed"]; out = []
    for l in open(d + "/simulation_events.jsonl"):
        e = json.loads(l)
        if e.get("event_type", "").endswith("_tally") and e.get("tick") == last: continue
        e.pop("event_id", None); e.pop("run_id", None); out.append(e)
    return out
def rundir(sha, key): return f"{S}{sha}/data/runs/" + json.load(open(f"{S}{sha}/data/calibration/{key}/quality_report.json"))["run_id"]
def first(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: return i, x, y
    return None
def brief(e): return f"t{e['tick']} {e['event_type']} entity {e.get('entity_id')}"
print("| world seed | run | first differing record index | parent record | d914bace7 record | same index and records as the probe pair |")
print("|---|---|---|---|---|---|")
for world, seed, lens, probe in (("urban_political", 42, (200, 500, 1000, 2000), "P3"), ("urban_political", 123, (500, 1000), "P1")):
    pa, pd = open(f"{O}{probe}_a.rundir").read().strip(), open(f"{O}{probe}_d.rundir").read().strip()
    pf = first(evs(pa), evs(pd))
    for n in lens:
        key = f"{world}_seed{seed}_{n}t"
        f = first(evs(rundir("a25619971", key)), evs(rundir("d914bace7", key)))
        same = f is not None and pf is not None and f[0] == pf[0] and f[1] == pf[1] and f[2] == pf[2]
        print(f"| {world} s{seed} | {n}t | {f[0]} | {brief(f[1])} | {brief(f[2])} | {same} |")
    print(f"| {world} s{seed} | probe ({probe}) | {pf[0]} | {brief(pf[1])} | {brief(pf[2])} | - |")
