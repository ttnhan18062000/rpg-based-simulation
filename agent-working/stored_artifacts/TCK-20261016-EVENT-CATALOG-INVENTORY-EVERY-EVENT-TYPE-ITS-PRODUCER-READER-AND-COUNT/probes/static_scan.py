"""Static producer scan for the event catalog inventory (read-only): every construction of a SimulationEvent (or a typed subclass) under src/.

Writes JSON: {sites: [...], classes: {...}, consts: {...}}.  A site = file, line, enclosing function, the event type (literal, resolved constant, or the
unresolved expression), category, severity, source_system, and the payload (literal dict keys, or the expression text).
"""
import ast, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1]); OUT = sys.argv[2]
files = sorted((ROOT / "src").rglob("*.py"))
trees = {}
for f in files:
    try: trees[f] = ast.parse(f.read_text(encoding="utf-8"))
    except Exception as e: print("PARSE FAIL", f, e, file=sys.stderr)

def lit(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

consts = {}   # NAME -> set(values) across files
local = {}    # (file, NAME) -> value
for f, t in trees.items():
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and lit(n.value) is not None:
            if n.targets[0].id.isupper(): consts.setdefault(n.targets[0].id, set()).add(lit(n.value)); local[(f, n.targets[0].id)] = lit(n.value)
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None and lit(n.value) is not None:
            if n.target.id.isupper(): consts.setdefault(n.target.id, set()).add(lit(n.value)); local[(f, n.target.id)] = lit(n.value)

CUR = [None]
def resolve(node):
    s = lit(node)
    if s is not None: return [s], "literal"
    if isinstance(node, ast.Name) and (CUR[0], node.id) in local: return [local[(CUR[0], node.id)]], "const:" + node.id
    if isinstance(node, ast.Name) and node.id in consts: return sorted(consts[node.id]), "const:" + node.id + (" AMBIGUOUS" if len(consts[node.id]) > 1 else "")
    if isinstance(node, ast.Attribute) and node.attr in consts: return sorted(consts[node.attr]), "const:" + node.attr
    return [], "dynamic: " + ast.unparse(node)[:100]

# event classes: subclasses of SimulationEvent (transitively by name) with a default event_type
classes = {}
bases = {"SimulationEvent"}
changed = True
while changed:
    changed = False
    for f, t in trees.items():
        for n in ast.walk(t):
            if isinstance(n, ast.ClassDef) and n.name not in bases:
                if any((isinstance(b, ast.Name) and b.id in bases) or (isinstance(b, ast.Attribute) and b.attr in bases) for b in n.bases):
                    bases.add(n.name); changed = True
for f, t in trees.items():
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef) and n.name in bases and n.name != "SimulationEvent":
            for b in n.body:
                if isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name) and b.target.id == "event_type" and b.value is not None:
                    vals, how = resolve(b.value)
                    classes[n.name] = {"file": str(f.relative_to(ROOT)), "line": n.lineno, "types": vals, "how": how}
                    for kw in ("event_category", "severity", "source_system"):
                        for c in n.body:
                            if isinstance(c, ast.AnnAssign) and isinstance(c.target, ast.Name) and c.target.id == kw and c.value is not None:
                                classes[n.name][kw] = lit(c.value) if lit(c.value) is not None else ast.unparse(c.value)[:60]

def payload_info(node):
    if node is None: return None
    if isinstance(node, ast.Dict):
        return {"literal_keys": [lit(k) if lit(k) is not None else ast.unparse(k) for k in node.keys if k is not None], "splat": any(k is None for k in node.keys),
                "values": {(lit(k) if lit(k) is not None else ast.unparse(k)): ast.unparse(v)[:70] for k, v in zip(node.keys, node.values) if k is not None}}
    return {"expr": ast.unparse(node)[:100]}

class V(ast.NodeVisitor):
    def __init__(self, f): CUR[0] = f; self.f = f; self.stack = []; self.sites = []; self.ctx = []
    def visit_If(self, n):
        self.ctx.append('if ' + ast.unparse(n.test)[:150]); self.generic_visit(n); self.ctx.pop()
    def visit_For(self, n):
        self.ctx.append('for ' + ast.unparse(n.target)[:30] + ' in ' + ast.unparse(n.iter)[:120]); self.generic_visit(n); self.ctx.pop()
    def visit_FunctionDef(self, n): self.stack.append(n.name); self.generic_visit(n); self.stack.pop()
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, n): self.stack.append(n.name); self.generic_visit(n); self.stack.pop()
    def visit_Call(self, n):
        name = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else None
        kws = {k.arg: k.value for k in n.keywords if k.arg}
        site = None
        if name == "SimulationEvent" or "event_type" in kws:
            vals, how = resolve(kws["event_type"]) if "event_type" in kws else ([], "missing")
            site = {"kind": "SimulationEvent" if name == "SimulationEvent" else f"call:{name}", "types": vals, "how": how}
        elif name in classes:
            site = {"kind": "typed:" + name, "types": classes[name]["types"], "how": "class " + name}
        elif isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id in classes:
            name = n.func.value.id
            site = {"kind": "typed:" + name + "." + n.func.attr, "types": classes[name]["types"], "how": "class " + name}
        if site:
            site.update({"file": str(self.f.relative_to(ROOT)), "line": n.lineno, "func": ".".join(self.stack), "ctx": list(self.ctx),
                         "category": resolve(kws["event_category"])[0] if "event_category" in kws else classes.get(name, {}).get("event_category"),
                         "severity": ast.unparse(kws["severity"])[:40] if "severity" in kws else classes.get(name, {}).get("severity"),
                         "source_system": ast.unparse(kws["source_system"])[:40] if "source_system" in kws else classes.get(name, {}).get("source_system"),
                         "payload": payload_info(kws.get("payload"))})
            self.sites.append(site)
        self.generic_visit(n)

sites = []
for f, t in trees.items():
    v = V(f); v.visit(t); sites += v.sites
# second pass: helpers that take the event type as a parameter (the SimulationEvent inside them is built from that parameter)
def helper_sites():
    out = []
    for f, t in trees.items():
        CUR[0] = f
        funcs = {n.name: n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for fn in funcs.values():
            params = [a.arg for a in fn.args.args]
            for c in ast.walk(fn):
                if isinstance(c, ast.Call) and (getattr(c.func, "id", None) == "SimulationEvent"):
                    kws = {k.arg: k.value for k in c.keywords if k.arg}
                    et = kws.get("event_type")
                    if isinstance(et, ast.Name) and et.id in params:
                        idx = params.index(et.id) - (1 if params and params[0] in ("self", "cls") else 0)
                        pidx = None
                        pl = kws.get("payload")
                        if isinstance(pl, ast.Name) and pl.id in params:
                            pidx = params.index(pl.id) - (1 if params[0] in ("self", "cls") else 0)
                        for call in ast.walk(t):
                            if isinstance(call, ast.Call) and (getattr(call.func, "id", None) == fn.name or getattr(call.func, "attr", None) == fn.name):
                                arg = call.args[idx] if len(call.args) > idx else next((k.value for k in call.keywords if k.arg == et.id), None)
                                if arg is None: continue
                                vals, how = resolve(arg)
                                payload = None
                                if pidx is not None:
                                    pa = call.args[pidx] if len(call.args) > pidx else next((k.value for k in call.keywords if k.arg == pl.id), None)
                                    payload = payload_info(pa)
                                cat = resolve(kws["event_category"])[0] if "event_category" in kws else None
                                out.append({"kind": f"helper:{fn.name}", "types": vals, "how": how, "file": str(f.relative_to(ROOT)), "line": call.lineno, "func": fn.name,
                                            "category": cat, "severity": ast.unparse(kws["severity"])[:40] if "severity" in kws else None,
                                            "source_system": ast.unparse(kws["source_system"])[:40] if "source_system" in kws else None, "payload": payload})
    return out
sites += helper_sites()
json.dump({"sites": sites, "classes": classes, "consts": {k: sorted(v) for k, v in consts.items() if len(v) == 1 or True}}, open(OUT, "w"), indent=1, sort_keys=True)
dyn = [s for s in sites if not s["types"]]
print(len(sites), "sites;", len({t for s in sites for t in s["types"]}), "distinct resolved types;", len(dyn), "unresolved sites;", len(classes), "typed classes")
