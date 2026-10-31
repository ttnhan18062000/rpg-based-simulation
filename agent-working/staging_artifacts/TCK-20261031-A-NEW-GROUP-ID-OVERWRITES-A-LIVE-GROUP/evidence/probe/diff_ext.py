import json, re, sys, collections
W="/data/vboxuser/Work/groups_base/out/"
def load(p): return {r["call"]: r for r in map(json.loads, open(p))}
a, b = load(W+"ext_base_lifecycle.jsonl"), load(W+"ext_branch_lifecycle.jsonl")
def mask(line):
    o = json.loads(line)
    def m(v, key=""):
        if isinstance(v, dict): return {k: m(x, k) for k, x in v.items()}
        if isinstance(v, list): return [m(x, key) for x in v]
        if "group" in key.lower() and isinstance(v, (int, str)) and not isinstance(v, bool) and str(v).lstrip("-").isdigit(): return "G"
        if isinstance(v, str): return re.sub(r"(?i)(group[_a-z]*[_:=\-]?)\d+", r"\1G", v)
        return v
    return json.dumps(m(o), sort_keys=True)
print("calls", len(a), len(b), "tick-aligned only if same count")
moved_rows = id_only = other = 0; first_other = None; others = []
for c in sorted(a):
    if c not in b: others.append((c, "missing in branch")); continue
    for cfg, la in a[c]["results"].items():
        lb = b[c]["results"].get(cfg)
        if la == lb: continue
        moved_rows += 1
        if len(la) == len(lb) and [mask(x) for x in la] == [mask(x) for x in lb]: id_only += 1
        else:
            other += 1
            if first_other is None: first_other = (c, cfg)
            if len(others) < 30: others.append((c, cfg, len(la), len(lb)))
print("moved (call,config) rows", moved_rows, "id-only", id_only, "other", other, "first_other", first_other)
for o in others[:30]: print(o)
