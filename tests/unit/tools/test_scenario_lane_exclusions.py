"""Guards the scenario-lane irrelevant list (roadmap D-R2): scenario-reachable code must not depend on it.

`scenario_lane_paths.IRRELEVANT_RE` skips the lane for changes under prefixes such as `tools/` and
`registries/`. That is only safe while code the scenarios execute never reads them. This AST scan fails if
tests/mechanic_scenarios/, tests/helpers/, tests/conftest.py, or any `src/` module they reach by import,
imports top-level `tools`, names a path under an irrelevant prefix in a string literal (docstrings
excluded), or builds one from a bare prefix segment in a `/` join or `Path(...)` call. A hit means the
prefix belongs out of the irrelevant list.

Choice (B4): scanning all of src/ over-approximated (6 files, none imported by scenarios: src/api dashboard,
src/lab, src/certification harness, src/engine/capability), so the scan follows the static import closure
from the scenario code instead of using a long allowlist. Limit: dynamic imports (importlib, string module
names) are not followed; the allowlist stays for a handful of justified exceptions.
"""

import ast
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from tools.test_architecture import scenario_lane_paths as slp

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOTS = ("tests/mechanic_scenarios", "tests/helpers", "tests/conftest.py")

# (relative file, flagged text): reason. Keep short; past a handful, narrow `tools/` instead.
ALLOWLIST = {}

_PREFIXES = tuple(
    p for p in re.findall(r"[A-Za-z0-9_\-]+/", slp.IRRELEVANT_RE.pattern.split("|[^/]+")[0]) if p
)
_FILE_PREFIXES = ("skills-lock.json",)
_BARE = {p.rstrip("/") for p in _PREFIXES}


def _docstring_nodes(tree: ast.AST) -> set:
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                skip.add(id(body[0].value))
    return skip


def _is_path_call(node: ast.Call) -> bool:
    f = node.func
    return (isinstance(f, ast.Name) and f.id == "Path") or (isinstance(f, ast.Attribute) and f.attr in {"joinpath", "Path"})


def find_dependencies(source: str, filename: str = "<src>") -> List[str]:
    tree = ast.parse(source, filename=filename)
    docs = _docstring_nodes(tree)
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits += [a.name for a in node.names if a.name.split(".")[0] == "tools"]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").split(".")[0] == "tools":
            hits.append(node.module or "tools")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            v = node.value
            if v.startswith(_PREFIXES) or v in _FILE_PREFIXES:
                hits.append(v)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and side.value in _BARE:
                    hits.append(str(side.value))
        elif isinstance(node, ast.Call) and _is_path_call(node):
            hits += [a.value for a in node.args if isinstance(a, ast.Constant) and a.value in _BARE]
    return sorted(set(hits))


def _module_file(name: str) -> Optional[Path]:
    base = REPO_ROOT.joinpath(*name.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _src_imports(source: str) -> Set[str]:
    """Dotted `src.*` module names a file imports, including `from pkg import submodule` candidates."""
    names: Set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names if a.name.split(".")[0] == "src")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").split(".")[0] == "src":
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


def _with_parents(name: str) -> Iterable[str]:
    parts = name.split(".")
    return (".".join(parts[: i + 1]) for i in range(len(parts)))


def reachable_files() -> List[Path]:
    seen: Dict[Path, None] = {}
    queue: List[Path] = []
    for rel in ROOTS:
        p = REPO_ROOT / rel
        queue += [p] if p.is_file() else sorted(p.rglob("*.py"))
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen[path] = None
        for name in _src_imports(path.read_text(encoding="utf-8")):
            for mod in _with_parents(name):
                f = _module_file(mod)
                if f is not None and f not in seen:
                    queue.append(f)
    return sorted(seen)


def _files() -> Iterable[Path]:
    return reachable_files()


def scan() -> List[Tuple[str, str]]:
    found = []
    for path in _files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        for hit in find_dependencies(path.read_text(encoding="utf-8"), rel):
            if (rel, hit) not in ALLOWLIST:
                found.append((rel, hit))
    return found


def test_scenario_reachable_code_does_not_depend_on_the_irrelevant_list():
    assert scan() == [], "scenario-reachable code touches an irrelevant prefix: move it out of IRRELEVANT_RE"


def test_allowlist_stays_a_handful_and_every_entry_has_a_reason():
    assert len(ALLOWLIST) <= 5, "allowlist grew: narrow `tools/` in IRRELEVANT_RE instead"
    assert all(ALLOWLIST.values())


def test_scanner_flags_imports_literals_and_path_segments_but_not_docstrings():
    src = '"""mentions registries/mechanisms.yaml"""\n' \
          "import tools.x\nfrom tools.y import z\nA = 'docs/a.md'\nB = Path('registries')\nC = root / 'tools' / 'f.py'\n" \
          "def f():\n    '''docs/ only in a docstring'''\n    return 1\n"
    assert find_dependencies(src) == ["docs/a.md", "registries", "tools", "tools.x", "tools.y"]


def test_scanner_ignores_unrelated_code():
    assert find_dependencies("import os\nx = 'src/a.py'\ny = Path('data')\n") == []


def test_prefix_extraction_covers_the_known_irrelevant_prefixes():
    assert {"docs", "tickets", "tools", "registries", "stored_artifacts"} <= _BARE


def test_reachability_follows_imports_into_src_and_skips_unreached_modules():
    rel = {p.relative_to(REPO_ROOT).as_posix() for p in reachable_files()}
    assert "tests/helpers/scenario.py" in rel
    assert any(r.startswith("src/core/") for r in rel), "scenario helpers must reach src/core"
    assert "src/api/agent_ops_dashboard/ingest.py" not in rel
