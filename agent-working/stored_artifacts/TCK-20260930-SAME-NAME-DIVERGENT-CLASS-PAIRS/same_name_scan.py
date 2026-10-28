"""Top-level class names defined in more than one module under src/ (read-only).

Run from the repo root: python3 same_name_scan.py > same_name_scan.jsonl
One row per duplicated name: the modules, whether the name is mechanism-shaped (suffix list from the ticket),
and per module the files under src/ and tests/ that import it (`from <module> import ... <Name>` or `<module>.<Name>`).
"""
import ast
import json
import re
from collections import defaultdict
from pathlib import Path

SUFFIX = ("Service", "System", "Gate", "Phase", "Evaluator", "Resolver", "Manager", "Registry")
defs = defaultdict(list)
for f in sorted(Path("src").rglob("*.py")):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            defs[n.name].append(str(f))
files = {f: f.read_text(encoding="utf-8", errors="replace") for f in list(Path("src").rglob("*.py")) + list(Path("tests").rglob("*.py"))}


def importers(module_path: str, name: str):
    mod = module_path[:-3].replace("/", ".")
    pat = re.compile(rf"from\s+{re.escape(mod)}\s+import\s+[^\n]*\b{name}\b|{re.escape(mod)}\.{name}\b")
    multi = re.compile(rf"from\s+{re.escape(mod)}\s+import\s*\(([^)]*)\)")
    hits = []
    for f, text in files.items():
        if str(f) == module_path:
            continue
        if pat.search(text) or any(re.search(rf"\b{name}\b", m.group(1)) for m in multi.finditer(text)):
            hits.append(str(f))
    return hits


for name, mods in sorted(defs.items()):
    if len(mods) < 2:
        continue
    print(json.dumps({
        "name": name,
        "mechanism_shaped": name.endswith(SUFFIX),
        "modules": {m: {"src_importers": [h for h in importers(m, name) if h.startswith("src/")],
                        "test_importers": [h for h in importers(m, name) if h.startswith("tests/")]} for m in mods},
    }))
