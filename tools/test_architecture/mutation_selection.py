"""Reproducible, import-based test selection for a mutation target (roadmap §6, baseline v2).

The rule resolves to a list of test files so a baseline record can name the rule, the resolved list and a
hash of it, and the report can tell when re-resolving the rule gives a different list (`selection-changed`).

Rule `import-based-one-hop`: a test file `tests/**/test_*.py` (excluding `tests/mutation/`) is selected when it
imports the target module, or imports a `src/` module that itself imports the target directly. Imports are read
from the AST (module level and function level); `from pkg import name` counts as importing `pkg.name`.
Curated additions are appended by hand and recorded separately.

It is a starting point, NOT proof that every relevant test is selected: dynamic imports, tests that reach the
target only through two or more hops, and tests that exercise it through fixtures are not found.
"""

import ast
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

RULE_KIND = "import-based-one-hop"


def _imports(path: Path) -> Set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


def _module_name(rel: Path) -> str:
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _test_files(repo_root: Path) -> Iterable[Path]:
    for p in sorted((repo_root / "tests").rglob("test_*.py")):
        if "mutation" not in p.relative_to(repo_root).parts:
            yield p


def resolve(repo_root: Path, target_module: str, curated_additions: Sequence[str] = ()) -> Dict[str, Any]:
    one_hop = sorted(
        _module_name(p.relative_to(repo_root))
        for p in (repo_root / "src").rglob("*.py")
        if _module_name(p.relative_to(repo_root)) != target_module and target_module in _imports(p)
    )
    hop_set = set(one_hop)
    rule_files: List[str] = []
    for p in _test_files(repo_root):
        imported = _imports(p)
        if target_module in imported or imported & hop_set:
            rule_files.append(p.relative_to(repo_root).as_posix())
    files = sorted(set(rule_files) | set(curated_additions))
    return {
        "rule": RULE_KIND, "target_module": target_module, "one_hop_src_modules": one_hop,
        "rule_files": sorted(rule_files), "curated_additions": sorted(curated_additions), "files": files,
        "resolved_files_sha256": files_hash(files),
    }


def files_hash(files: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(files)).encode("utf-8")).hexdigest()
