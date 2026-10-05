"""contamination.py <dir-of-zones-jsonl> [world ...]: one JSON line per world.
Per world: deaths by cause enum (outcome kind and passive cause); HAZARD deaths split by whether the victim took attacker damage within the last
N ticks (N = 50, 200, any) and that attacker's faction; boss / dragonkin counts and cadence; boss spawn tiles; victim provenance for non-boss
HAZARD deaths (does the spawn row carry a catalog faction_id / population_id?); and four trauma series from a replay of the producer
(+1.0 per death credited to a region, -0.0005 per tick, floor 0): ALL deaths, boss deaths removed, (d) killer-only, and (d') violent-within-50
(killer present OR attacker damage within the last 50 ticks). The ALL arm is checked against the real per-region trauma checkpoints (control)."""
import sys, json, glob, os, collections
def replay(deaths, regions, ticks, keep, decay_first):
    tr = {r: 0.0 for r in regions}; by = collections.defaultdict(list)
    for d in deaths:
        if d["credited"] and keep(d): by[d["tick"]].append(d["credited"])
    s = {}
    for t in range(ticks):
        if decay_first:
            for r in tr: tr[r] = max(0.0, tr[r] - 0.0005) if tr[r] > 0 else 0.0
        for r in by.get(t, ()): tr[r] += 1.0
        if not decay_first:
            for r in tr: tr[r] = max(0.0, tr[r] - 0.0005) if tr[r] > 0 else 0.0
        s[t + 1] = dict(tr)
    return s
def first_over(s, r, th=50.0):
    for t, v in s.items():
        if v[r] > th: return t
def is_boss(d): return "boss" in str(d["victim"]["role"])
def violent50(d): return d["killer"] is not None or (d.get("last_hit") is not None and d["last_hit"]["ago"] <= 50)
d_ = sys.argv[1]; names = sys.argv[2:] or sorted(os.path.basename(f)[:-6] for f in glob.glob(d_ + "/*.jsonl"))
for w in names:
    try: rows = [json.loads(l) for l in open(f"{d_}/{w}.jsonl")]
    except Exception as e: print(json.dumps({"world": w, "error": str(e)})); continue
    if not any(r.get("final") for r in rows): print(json.dumps({"world": w, "error": "run did not finish"})); continue
    hdr = rows[0]; deaths = [r for r in rows[1:] if "tick" in r]; spawns = {r["who"]["id"]: r for r in rows if "spawn" in r and r.get("who")}
    cps = {r["cp"]: r["trauma"] for r in rows if "cp" in r}; regions = list(hdr["bounds"]); ticks = hdr["ticks"]
    haz = [x for x in deaths if x["outcome"] == "HAZARD"]
    def win(n): return [x for x in haz if x.get("last_hit") and x["last_hit"]["ago"] <= n]
    boss = [x for x in deaths if is_boss(x)]; drag = [x for x in deaths if "dragon" in str(x["victim"]["role"])]
    bt = sorted(x["tick"] for x in boss); gaps = sorted(b - a for a, b in zip(bt, bt[1:]))
    nb = [x for x in haz if not is_boss(x)]
    def prov(x):
        sp = spawns.get(x["victim"]["id"])
        return "initial_population" if sp is None else ("catalog(faction_id)" if sp["props"].get("faction_id") else "no_faction_id")
    best = None
    for df in (False, True):
        s = replay(deaths, regions, ticks, lambda d: True, df)
        diff = max((abs(s[c][r] - cps[c][r]) for c in cps for r in regions), default=0.0)
        if best is None or diff < best[0]: best = (diff, df, s)
    diff, df, s_all = best
    arms = {"all": s_all, "boss_removed": replay(deaths, regions, ticks, lambda d: not is_boss(d), df),
            "d_killer_only": replay(deaths, regions, ticks, lambda d: d["killer"] is not None, df),
            "d_violent_within_50": replay(deaths, regions, ticks, violent50, df)}
    print(json.dumps({"world": w, "deaths": len(deaths),
        "by_outcome": dict(collections.Counter(x["outcome"] for x in deaths)), "by_passive": dict(collections.Counter(x["passive"] for x in deaths if x["passive"] != "None")),
        "hazard_deaths": len(haz), "hazard_wounded_within": {"50": len(win(50)), "200": len(win(200)), "any": len(win(10**9))},
        "hazard_wounded_within_50_attacker_factions": dict(collections.Counter((x["last_hit"]["attacker"] or {}).get("faction") for x in win(50))),
        "boss_deaths": len(boss), "dragonkin_deaths": len(drag), "boss_first_tick": bt[0] if bt else None, "boss_median_gap": gaps[len(gaps) // 2] if gaps else None,
        "boss_spawn_tiles": dict(collections.Counter((tuple(r["pos"]), "+".join(r["zone"])) .__str__() for r in rows if "spawn" in r and r.get("who") and ("boss" in str(r["who"]["role"]) or "dragon" in str(r["who"]["role"])))),
        "nonboss_hazard_victim_provenance": dict(collections.Counter((prov(x), x["victim"]["faction"], x["victim"]["role"]) .__str__() for x in nb)),
        "replay_control_max_abs_diff": round(diff, 4), "replay_decay_first": df,
        "trauma_final": {k: {r: round(s[ticks][r], 1) for r in regions} for k, s in arms.items()}, "trauma_final_real": cps[max(cps)] if cps else None,
        "first_over_50": {k: {r: first_over(s, r) for r in regions if first_over(s, r)} for k, s in arms.items()}}))
