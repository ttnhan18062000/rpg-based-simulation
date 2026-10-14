"""name_literal_scan.py - find every string literal in src/ that names a content id (D56: code reads no names).

Read-only AST scan. It loads the content catalogs (and the place/region ids declared by data/worlds) and walks src/ for string literals used as:
  eq/in   a literal on either side of ==, !=, in, not in (also a module-level constant set/list/tuple the comparison names)
  subs    a literal subscript key, x["k"]
  get     the first argument or the default of .get(...) / .setdefault(...)
  match   a match-statement value arm
  dictkey a literal key of a dict display
  call    a literal positional or keyword argument of a call
  default a literal default of a function parameter
A literal is reported when it equals a catalog id exactly, equals one in another letter case (or with '-' or ' ' for '_'), or when the expression it is
compared with names a catalog (terrain, species, role, item, place, building, faction, ...) and the literal is in no catalog. Logging calls, docstrings,
f-strings and raise messages are skipped; presenter areas (src/api, src/rendering) are counted, not listed.

Columns: file:line, kind, literal, catalog (the catalog the id is in, or the one the expression hints at), match (exact | case | missing | other-catalog), role
(decision | default), callers (how many other places in src use the enclosing function's name; 0 = nothing calls it).

Usage: python3 tools/name_literal_scan.py [--out FILE.md] [--json FILE.json]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LOG_NAMES = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
PRESENTER_DIRS = ("src/api/", "src/rendering/")
# Words in the compared-with expression that name a catalog. "kind" alone is not one (event, work and status kinds are not content); an entity's `.kind`
# is its species id, so it counts only on an entity-like receiver (ENTITY_KIND below).
HINTS = {
    "terrain": ("terrain",),
    "species": ("species", "archetype"),
    "roles": ("role",),
    "items": ("item_id", "item_kind", "loot", "item_type"),
    "regions": ("region", "place", "poi"),
    "buildings": ("building_kind", "building_type", "building_id"),
    "factions": ("faction",),
    "resources": ("resource",),
    "biomes": ("biome",),
    "recipes": ("recipe",),
    "services": ("service",),
    "ecologies": ("ecology",),
    "traits": ("trait",),
    "elements": ("element",),
    "materials": ("material",),
}
ENTITY_KIND = re.compile(r"(^|[.])(e|ent|entity|target|attacker|defender|victim|monster|other|actor|hero|npc|n)[.]kind$|^(entity|monster|target)_kind$")
REPO_ATTRS = [
    "materials", "traits", "themes", "relationship_axes", "attributes", "elements", "species", "need_profiles", "sense_profiles", "body_models",
    "drive_profiles", "cognition_profiles", "stats_profiles", "combat_profiles", "inventory_profiles", "skill_profiles", "populations", "entity_archetypes",
    "roles", "factions", "perspectives", "buildings", "terrain", "services", "regions", "recipes", "resources", "items", "biomes", "ecologies", "spawn_tables",
    "class_tables",
]


def norm(s: str) -> str:
    return re.sub(r"[\s\-]+", "_", s.strip()).lower()


def load_catalogs() -> Dict[str, Set[str]]:
    from src.content.paths import ContentPathConfig
    from src.content.repository import CatalogRepository

    repo = CatalogRepository(ContentPathConfig().content_root)
    repo.load_all()
    cats: Dict[str, Set[str]] = {}
    for attr in REPO_ATTRS:
        ids = getattr(repo, attr, None)
        if isinstance(ids, dict) and ids:
            cats[attr] = {str(k) for k in ids}
    world_ids: Set[str] = set()
    try:
        import yaml

        for wf in (ROOT / "data" / "worlds").glob("*/world.yaml"):
            data = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
            stack = [data]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    v = cur.get("id")
                    if isinstance(v, str):
                        world_ids.add(v)
                    stack.extend(cur.values())
                elif isinstance(cur, list):
                    stack.extend(cur)
    except Exception:  # a world file that does not parse is not this scan's business
        pass
    if world_ids:
        cats["world_ids"] = world_ids
    return cats


class Finding:
    __slots__ = ("file", "line", "kind", "literal", "catalog", "match", "role", "callers", "func", "expr")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def row(self) -> Dict[str, object]:
        return {k: getattr(self, k) for k in self.__slots__}


def classify(literal: str, expr_text: str, cats: Dict[str, Set[str]], exact_idx, norm_idx) -> Optional[Tuple[str, str]]:
    hint = None
    low = expr_text.lower()
    for cat, words in HINTS.items():
        if any(w in low for w in words):
            hint = cat
            break
    if hint is None and ENTITY_KIND.search(low):
        hint = "species"
    exact = exact_idx.get(literal, [])
    if exact:
        if hint and hint in exact:
            return hint, "exact"
        return exact[0], "exact" if not hint or hint not in cats else "other-catalog"
    ci = norm_idx.get(norm(literal), [])
    if ci:
        return ci[0], "case"
    if hint and hint in cats and re.fullmatch(r"[A-Za-z][A-Za-z0-9_\- ]{1,40}", literal):
        if literal.isupper() and hint != "terrain" and "_" in literal:
            return None  # an enum token (ENTITY_ACT, NEAR_DEATH), not a content name
        return hint, "missing"
    return None


class Scanner(ast.NodeVisitor):
    def __init__(self, path: str, tree: ast.AST, cats, exact_idx, norm_idx):
        self.path, self.cats, self.exact_idx, self.norm_idx = path, cats, exact_idx, norm_idx
        self.findings: List[Finding] = []
        self.func_stack: List[str] = []
        self.consts: Dict[str, List[str]] = {}
        self.docstrings: Set[int] = set()
        self.skip: Set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    self.docstrings.add(id(first.value))
            if isinstance(node, ast.Raise):
                for sub in ast.walk(node):
                    self.skip.add(id(sub))
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                base = ast.unparse(f.value).lower() if isinstance(f, ast.Attribute) else ""
                if name in LOG_NAMES and ("log" in base or base in ("logging", "")):
                    for sub in ast.walk(node):
                        self.skip.add(id(sub))
            if isinstance(node, ast.JoinedStr):
                for sub in ast.walk(node):
                    self.skip.add(id(sub))
        for node in tree.body if isinstance(tree, ast.Module) else []:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                lits = self._literals(node.value)
                if lits:
                    self.consts[node.targets[0].id] = lits

    def _literals(self, node: ast.AST) -> List[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            out: List[str] = []
            for e in node.elts:
                out.extend(self._literals(e))
            return out
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("frozenset", "set", "tuple", "list") and node.args:
            return self._literals(node.args[0])
        if isinstance(node, ast.Name) and node.id in self.consts:
            return self.consts[node.id]
        return []

    def _add(self, node: ast.AST, kind: str, literal: str, expr: str, role: str = "decision") -> None:
        if id(node) in self.skip or id(node) in self.docstrings:
            return
        got = classify(literal, expr, self.cats, self.exact_idx, self.norm_idx)
        if got is None:
            return
        cat, match = got
        self.findings.append(Finding(file=self.path, line=getattr(node, "lineno", 0), kind=kind, literal=literal, catalog=cat, match=match, role=role,
                                     func=self.func_stack[-1] if self.func_stack else "<module>", expr=expr[:60], callers=None))

    def visit_FunctionDef(self, node):
        defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
        names = [a.arg for a in node.args.args][-len(node.args.defaults):] if node.args.defaults else []
        names += [a.arg for a, d in zip(node.args.kwonlyargs, node.args.kw_defaults) if d is not None]
        for name, d in zip(names, defaults):
            for lit in self._literals(d) if isinstance(d, ast.Constant) else []:
                self._add(d, "default", lit, name, role="default")
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Compare(self, node: ast.Compare):
        operands = [node.left] + list(node.comparators)
        for i, op in enumerate(node.ops):
            left, right = operands[i], operands[i + 1]
            if not isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Is, ast.IsNot)):
                continue
            for lit_side, other in ((left, right), (right, left)):
                lits = self._literals(lit_side)
                if not lits:
                    continue
                other_text = ast.unparse(other)
                for lit in lits:
                    self._add(node, "eq/in", lit, other_text)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        sl = node.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            self._add(node, "subs", sl.value, ast.unparse(node.value))
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                exact = self.exact_idx.get(k.value) or self.norm_idx.get(norm(k.value))
                if exact:
                    self._add(k, "dictkey", k.value, "")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        recv = ast.unparse(f.value) if isinstance(f, ast.Attribute) else ""
        if name in ("get", "setdefault", "pop") and node.args:
            a0 = node.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                self._add(node, "get", a0.value, recv)
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                self._add(node, "get", node.args[1].value, ast.unparse(a0), role="default")
        else:
            for a in list(node.args) + [kw.value for kw in node.keywords]:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    exact = self.exact_idx.get(a.value) or self.norm_idx.get(norm(a.value))
                    if exact:
                        self._add(node, "call", a.value, f"{recv}.{name}" if recv else name)
        self.generic_visit(node)

    def visit_Match(self, node):
        subject = ast.unparse(node.subject)
        for case in node.cases:
            for sub in ast.walk(case.pattern):
                if isinstance(sub, ast.MatchValue) and isinstance(sub.value, ast.Constant) and isinstance(sub.value.value, str):
                    self._add(sub, "match", sub.value.value, subject)
        self.generic_visit(node)


def scan(root: Path) -> Tuple[List[Finding], Dict[str, int], Dict[str, Set[str]]]:
    cats = load_catalogs()
    exact_idx: Dict[str, List[str]] = defaultdict(list)
    norm_idx: Dict[str, List[str]] = defaultdict(list)
    for cat, ids in cats.items():
        for i in ids:
            exact_idx[i].append(cat)
            norm_idx[norm(i)].append(cat)
    findings: List[Finding] = []
    presenter: Dict[str, int] = Counter()
    sources = sorted((root / "src").rglob("*.py"))
    texts: Dict[str, str] = {}
    for p in sources:
        rel = str(p.relative_to(root))
        try:
            texts[rel] = p.read_text(encoding="utf-8")
            tree = ast.parse(texts[rel])
        except (SyntaxError, UnicodeDecodeError):
            continue
        sc = Scanner(rel, tree, cats, exact_idx, norm_idx)
        sc.visit(tree)
        if rel.startswith(PRESENTER_DIRS):
            presenter[rel.split("/")[1]] += len(sc.findings)
        else:
            findings.extend(sc.findings)
    alltext = "\n".join(texts.values())
    cache: Dict[str, int] = {}
    for f in findings:
        if f.func == "<module>":
            f.callers = None
            continue
        if f.func not in cache:
            cache[f.func] = max(0, len(re.findall(r"\b%s\b" % re.escape(f.func), alltext)) - 1)  # minus its own def
        f.callers = cache[f.func]
    return findings, dict(presenter), cats


def render(findings: List[Finding], presenter: Dict[str, int], cats: Dict[str, Set[str]]) -> str:
    out = ["# Name literals in src/ that name a content id (D56)", ""]
    out.append("Catalog sizes: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(cats.items())) + ".")
    by = Counter((f.match, f.role) for f in findings)
    out.append("")
    out.append("Findings: %d (%s). Presenter areas not listed: %s." % (len(findings), ", ".join(f"{m}/{r} {n}" for (m, r), n in sorted(by.items())), presenter or "none"))
    out.append("")
    out.append("| file:line | kind | literal | catalog | match | role | function | callers | compared with |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    order = {"missing": 0, "case": 1, "other-catalog": 2, "exact": 3}
    for f in sorted(findings, key=lambda f: (order.get(f.match, 9), f.role, f.file, f.line)):
        out.append(f"| {f.file}:{f.line} | {f.kind} | `{f.literal}` | {f.catalog} | {f.match} | {f.role} | {f.func} | {'-' if f.callers is None else f.callers} | `{f.expr.replace('|', '/')}` |")
    return "\n".join(out) + "\n"


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out")
    ap.add_argument("--json")
    ns = ap.parse_args(list(argv) if argv is not None else None)
    findings, presenter, cats = scan(ROOT)
    md = render(findings, presenter, cats)
    if ns.out:
        Path(ns.out).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    if ns.json:
        Path(ns.json).write_text(json.dumps([f.row() for f in findings], indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
