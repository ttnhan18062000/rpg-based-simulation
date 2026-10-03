import ast,yaml,sys
from pathlib import Path
sys.path.insert(0,'.')
from tools.mechanism_registry.registry import parse_implemented_by_entry
INFRA={"api","cli","certification","config","logging","observability","perf","platform","rendering","replay","runtime","testing","views"}
SUF=("Service","System","Gate","Phase","Evaluator","Resolver","Manager")
src=Path("src"); bound=set()
for m in yaml.safe_load(open("registries/mechanisms.yaml"))["mechanisms"]:
    for e in m.get("implemented_by") or []: bound.add(parse_implemented_by_entry(e)[0])
files=[p for p in sorted(src.rglob("*.py")) if "tests" not in p.parts]
trees={p:ast.parse(p.read_text()) for p in files}
top=lambda p:p.relative_to(src).parts[0]
scope=[p for p in files if p.name!="__init__.py" and len(p.relative_to(src).parts)>1 and top(p) not in INFRA|{"domains","systems"}]
used={p:{n.id for n in ast.walk(t) if isinstance(n,ast.Name)}|{n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute)} for p,t in trees.items()}
unbound=[p for p in scope if str(p) not in bound]
cands=[(p,n.name) for p in unbound for n in trees[p].body if isinstance(n,ast.ClassDef) and n.name.endswith(SUF)]
def callers(p,c,cross):
    return [q for q in files if q!=p and q.name!="__init__.py" and c in used[q] and (not cross or top(q)!=top(p))]
print(len(scope),len(unbound),len(cands))
for cross in (False,True):
    w=[(p,c) for p,c in cands if callers(p,c,cross)]
    print('cross' if cross else 'any',len(w))
w=[(p,c) for p,c in cands if callers(p,c,True)]
for p,c in w: print(p,c,[str(q) for q in callers(p,c,True)][:2])
