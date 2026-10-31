"""Prefix check from the sweep's own run dirs (no re-run). For each commit, run X (shorter) vs run Y (longer): the full simulation_events.jsonl
records with tick <= N, event_id and run_id excluded (event_id is a uuid4 default, src/observability/events.py:56), must be identical, in order.
Also metric_windows.jsonl windows ending <= N (alive_entities_avg, gold_total_avg, event_count). Usage: prefix_check.py   (prints a table)"""
import json, glob, os
S = "/data/vboxuser/Work/simq_sweep/"
def run(sha, world, seed, ticks):
    key = f"{world}_seed{seed}_{ticks}t"   # the run dir is the one the key's own quality_report.json names (several keys share a world/seed/ticks)
    rid = json.load(open(f"{S}{sha}/data/calibration/{key}/quality_report.json"))["run_id"]
    return f"{S}{sha}/data/runs/{rid}"
def events(d, n):
    out = []
    last = json.load(open(d + "/run_manifest.json"))["ticks_completed"]
    for l in open(d + "/simulation_events.jsonl"):
        e = json.loads(l)
        if e.get("tick", 0) <= n and not (e.get("event_type", "").endswith("_tally") and e.get("tick") == last):   # run-end tally events exist only at a run's own last tick
            e.pop("event_id", None); e.pop("run_id", None); out.append(json.dumps(e, sort_keys=True))
    return out
def windows(d, n):
    out = []
    for l in open(d + "/metric_windows.jsonl"):
        w = json.loads(l)
        if w["window_end_tick"] <= n: out.append((w["window_start_tick"], w["window_end_tick"], w["alive_entities_avg"], w["gold_total_avg"], w["event_count"]))
    return out
cases = [("urban_political", 42, 200, 500, 200), ("urban_political", 42, 500, 1000, 500), ("urban_political", 42, 500, 2000, 500),
         ("urban_political", 123, 500, 1000, 500)]
print("| world seed | shorter run | longer run | compared up to tick | commit | events compared | event streams identical | metric windows compared | windows identical |")
print("|---|---|---|---|---|---|---|---|---|")
for w, s, tx, ty, n in cases:
    for sha in ("a25619971", "d914bace7"):
        x, y = run(sha, w, s, tx), run(sha, w, s, ty)
        ex, ey, wx, wy = events(x, n), events(y, n), windows(x, n), windows(y, n)
        print(f"| {w} s{s} | {tx}t | {ty}t | {n} | {sha} | {len(ex)} | {ex == ey} | {len(wx)} | {wx == wy} |")
