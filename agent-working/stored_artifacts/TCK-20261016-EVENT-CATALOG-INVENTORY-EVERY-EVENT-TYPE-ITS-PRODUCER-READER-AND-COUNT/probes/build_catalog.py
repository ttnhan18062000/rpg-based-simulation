"""Build the event catalog inventory (stored-artifact table) from the static scan, the SimQ scorer registry and the lossless measured runs. Read-only."""
import collections, glob, importlib, json, pkgutil, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1]); SCR = Path(sys.argv[2]); OUT = Path(sys.argv[3])
sys.path.insert(0, str(ROOT))
static = json.load(open(SCR / "static.json"))
runs = [json.load(open(p)) for p in sorted(glob.glob(str(SCR / "out" / "*_4[2-6].json")))]
WORLDS = ["frontier_living_world", "urban_political", "crowded_frontier"]
ABBR = {"frontier_living_world": "F", "urban_political": "U", "crowded_frontier": "C"}

# ---- SimQ side ----
import src.simulation_quality.scorers as spkg
from src.simulation_quality import quality_hub as qh
scorer_types = collections.defaultdict(list)   # contract type -> [pillar]
for m in pkgutil.iter_modules(spkg.__path__):
    if m.name in ("base", "__init__"): continue
    mod = importlib.import_module("src.simulation_quality.scorers." + m.name)
    for n, c in vars(mod).items():
        if isinstance(c, type) and getattr(c, "EVENT_TYPES", None) and c.__module__ == mod.__name__:
            for t in c.EVENT_TYPES: scorer_types[t].append(c.PILLAR_ID.value if hasattr(c.PILLAR_ID, "value") else str(c.PILLAR_ID))
CONDITIONAL_OUT = {   # outputs of the payload-conditional translators in quality_hub (read from their bodies)
    "quest_event": ["quest_completed", "quest_failed", "quest_started"],
    "lifecycle": ["level_up", "entity_killed", "lifecycle"],
    "StrategicProjectChanged": ["project_completed", "project_abandoned", "project_started"],
    "InvariantViolation": sorted(set(qh._LAW_ID_TO_EVENT_TYPE.values()) | {"spawn_occupancy_violation", "InvariantViolation"}),
    "betrayal_desertion": ["faction_tension_delta", "contract_lapsed"],
}
def contract_types(t):
    if t in qh._TRANSLATE_SIMPLE: return [qh._TRANSLATE_SIMPLE[t]]
    if t in CONDITIONAL_OUT: return CONDITIONAL_OUT[t]
    return [t]
def simq_readers(t):
    out = []
    for c in contract_types(t):
        for p in scorer_types.get(c, []): out.append(f"{p}" + ("" if c == t else f" (as {c})"))
    return sorted(set(out))

# ---- static sites by type ----
sites = collections.defaultdict(list)
for s in static["sites"]:
    for t in s["types"]: sites[t].append(s)
def prod_kind(f):
    if f.endswith("event_extractor.py"): return "EventExtractor"
    if f.endswith("event_shapers.py"): return "event_shapers"
    if f.startswith("src/engine/scenario_runtime"): return "scenario_runtime"
    if f.startswith("src/engine/"): return "engine"
    if "campaigns" in f: return "campaigns"
    if f.startswith("src/domains/"): return "domains"
    if f.startswith("src/observability/"): return "observability(" + Path(f).stem + ")"
    return Path(f).parts[1] if len(Path(f).parts) > 1 else f

# ---- measured ----
meas = collections.defaultdict(lambda: collections.defaultdict(dict))  # type -> world -> seed -> count
chan = collections.defaultdict(set); shape = {}
evidence = []
for r in runs:
    st = r["stats"]; w = r["world"]; seed = r["seed"]
    rec, lis, fil = st["recorder_counts"], r["listener_counts"], r["file_counts"]
    for t in set(rec) | set(lis) | set(fil):
        meas[t][w][seed] = max(rec.get(t, 0), lis.get(t, 0), fil.get(t, 0))
        if rec.get(t): chan[t].add("R")
        if lis.get(t): chan[t].add("L")
        if fil.get(t): chan[t].add("F")
    for t, sh in r["shape"].items():
        a = shape.setdefault(t, {"category": collections.Counter(), "severity": collections.Counter(), "source": collections.Counter(), "keys": collections.defaultdict(lambda: [0, collections.Counter()]), "n": 0, "example": sh["example"]})
        a["n"] += sh["n"]
        for k in ("category", "severity", "source"): a[k].update(sh[k])
        for key, v in sh["keys"].items():
            a["keys"][key][0] += v["n"]; a["keys"][key][1].update(v["types"])
    rb, fb = st.get("recorder_by_tick_bucket"), r.get("file_by_tick_bucket")
    cut = None
    if rb and fb:
        for b in sorted(rb, key=int):
            if fb.get(b, 0) < 0.9 * rb[b]: cut = int(b) * 500; break
    crit = sum(sh["severity"].get("CRITICAL", 0) for sh in r["shape"].values())
    evidence.append((w, seed, st["events_dropped_by_mode"], st["queue_dropped"], st["modes_seen"], st["max_queue_fill"], st["obs_mode_final"], r["obs_mode"],
                     sum(rec.values()), sum(fil.values()), sum(lis.values()), cut, crit, st.get('inmemory_dropped')))

def total(t, w=None):
    ws = [w] if w else WORLDS
    return sum(sum(meas[t][x].values()) for x in ws if x in meas[t])

# ---- other readers (literal mentions outside the producing files) ----
src_files = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="ignore") for p in (ROOT / "src").rglob("*.py")}
def readers(t, prod_files):
    pat = re.compile(r"""["']""" + re.escape(t) + r"""["']""")
    return sorted(f for f, txt in src_files.items() if f not in prod_files and pat.search(txt))

def simq_note(t, ss):
    ids = set()
    for s in ss:
        lines = src_files.get(s["file"], "").splitlines()
        lo, hi = max(0, s["line"] - 30), min(len(lines), s["line"] + 6)
        for ln in lines[lo:hi]:
            ids.update(re.findall(r"TCK-[0-9]{8}-[A-Z0-9-]*SIMQ[A-Z0-9-]*|SIMQ-[A-Z0-9-]+|SQ-\d+", ln))
    return sorted(ids)

def derived(ss):
    bits = []
    for s in ss:
        if s["kind"].startswith("typed:"): bits.append("typed event class " + s["kind"][6:])
    s0 = next((s for s in ss if "event_extractor" in s["file"] or "event_shapers" in s["file"]), ss[0] if ss else None)
    if s0:
        toks = []
        txt = " ".join((s0.get("ctx") or [])[-3:]) + " " + " ".join(((s0.get("payload") or {}).get("values") or {}).values())
        for m in re.findall(r"\b(?:update|upd|e_upd\w*|u_\w+|intent_results|ir|result|prior_ent|prior_\w+|entity|ent|current_state|prior_state|state|bio|stam|prop|props|properties)\b(?:\.[a-z_]+)*(?:\.get\(\"[a-z_]+\"\))?", txt):
            if m not in toks and "." in m or m in ("intent_results",): toks.append(m) if m not in toks else None
        if toks: bits.append("reads " + ", ".join(toks[:5]))
        pl = s0.get("payload")
        if pl is None: bits.append("no payload")
        elif "literal_keys" in pl: bits.append("payload: free dict (literal keys)")
        else: bits.append("payload: free dict (" + pl["expr"][:40] + ")")
    return "; ".join(bits)

def gates(ss):
    g = set()
    for s in ss:
        for c in s.get("ctx") or []:
            if re.search(r"mode|push_shaper|flag|_active|enabled", c): g.add(c[3:90] if c.startswith("if ") else c[:90])
    return sorted(g)

all_types = sorted(set(sites) | set(meas))
rows = {}
for t in all_types:
    ss = sites.get(t, [])
    pf = {s["file"] for s in ss}
    sh = shape.get(t)
    cat = ", ".join(f"{k}" for k, _ in (sh["category"].most_common(2) if sh else [])) or ", ".join(sorted({c for s in ss for c in (s["category"] if isinstance(s["category"], list) else [s["category"]]) if c})) or "?"
    sev = ", ".join(k for k, _ in (sh["severity"].most_common(3) if sh else [])) or ", ".join(sorted({str(s["severity"]) for s in ss if s["severity"]}))
    payload = ", ".join(f"{k}:{'/'.join(sorted(v[1]))}" + ("" if v[0] == sh["n"] else "?") for k, v in sorted(sh["keys"].items())) if sh else ""
    if not payload:
        for s in ss:
            if s.get("payload") and "literal_keys" in s["payload"]:
                payload = ", ".join(s["payload"]["literal_keys"]) + " (static)"; break
    rows[t] = {"type": t, "sites": [f"{s['file']}:{s['line']} [{prod_kind(s['file'])}" + (f", {s['kind'][5:]}" if s['kind'].startswith('call:') else "") + "]" for s in ss], "kinds": sorted({prod_kind(s['file']) for s in ss}),
               "derived": derived(ss), "payload": payload, "category": cat, "severity": sev, "simq": simq_readers(t), "gates": gates(ss),
               "chan": "".join(sorted(chan.get(t, []))), "counts": {w: total(t, w) for w in WORLDS}, "total": total(t), "readers": readers(t, pf),
               "simq_ids": simq_note(t, ss), "authoritative": sorted({s['file'] for s in ss if not s['file'].startswith("src/observability/")})}
json.dump({"rows": rows, "evidence": evidence, "scorer_types": scorer_types}, open(OUT.with_suffix(".json"), "w"), indent=1, sort_keys=True, default=list)
print(len(rows), "types;", sum(1 for r in rows.values() if r["total"]), "measured;", len(runs), "runs")

# ---- flags ----
notes = json.load(open(SCR / "notes.json")) if (SCR / "notes.json").exists() else {"goes": {}, "d33": {}}
produced_contract = collections.defaultdict(set)   # contract type -> source engine types (static or measured)
for t in rows:
    for c in contract_types(t): produced_contract[c].add(t)
never = {c: ps for c, ps in scorer_types.items() if c not in produced_contract}
dormant = {}
for c, ps in scorer_types.items():
    srcs = produced_contract.get(c)
    if not srcs: continue
    if sum(rows[s]["total"] for s in srcs) == 0:
        dormant[c] = {"pillars": ", ".join(sorted(set(ps))), "via": ", ".join(f"`{s}`" for s in sorted(srcs)), "sites": "; ".join(sorted({x for s in srcs for x in rows[s]["sites"][:2]}))[:240]}
unread = {t: {"f": r["counts"][WORLDS[0]], "u": r["counts"][WORLDS[1]], "c": r["counts"][WORLDS[2]], "readers": r["readers"]} for t, r in rows.items() if not r["simq"] and (r["total"] or r["sites"])}
auth = {t: {"sites": [x for x in r["sites"] if not x.split(":")[0].startswith("src/observability/")], "goes": "; ".join(sorted({notes["goes"].get(x.split(":")[0], "?") for x in r["sites"] if not x.split(":")[0].startswith("src/observability/")})),
            "f": r["counts"][WORLDS[0]], "u": r["counts"][WORLDS[1]], "c": r["counts"][WORLDS[2]]} for t, r in rows.items() if any(not x.split(":")[0].startswith("src/observability/") for x in r["sites"])}
seeds = [dict(sd, counts={e: [rows[e]["counts"][w] if e in rows else None for w in WORLDS] for e in sd["events"]}) for sd in notes.get("seeds", [])]
per_seed = {t: {w: {str(s): c for s, c in meas[t][w].items()} for w in meas[t]} for t in rows}
doc = json.load(open(OUT.with_suffix(".json")))
doc.update({"never_emitted": never, "producer_never_fired": dormant, "unread": unread, "authoritative": auth, "simq_seeds": seeds, "per_seed": per_seed})
json.dump(doc, open(OUT.with_suffix(".json"), "w"), indent=1, sort_keys=True, default=list)
print("never:", sorted(never), "| dormant:", len(dormant), "| unread:", len(unread), "| authoritative:", len(auth), "| simq seeds:", len(seeds))
