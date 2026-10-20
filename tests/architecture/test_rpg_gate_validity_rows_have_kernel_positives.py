"""Every required rpg gate validity id has a real-kernel positive test (TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE).

V1 and V4 were blind on the first full-size gate run (a 0-gold charge counted as a payment; a counter cleared before the ledger saw it) and read 0 violations, so they
looked green. A validity row is therefore not accepted without a positive test that forces a violation through ``build_kernel`` (the run path the gate harness uses)
and asserts ``violations > 0`` on the row the metric module emits. This lint checks the map ``tests/simulation_quality/rpg_gate/kernel_positives.yaml`` statically:

* every id in ``config.required_validity`` (either level) has an entry, and no entry names an id that is not required;
* every named node id exists (parsed with ``ast``, no import of the test);
* the named test reaches a call to ``build_kernel`` AND a call to the metric module's ``compute`` or ``pool`` (the emitted row, not a private counter), directly or through
  helpers it calls, following same-module functions and one-hop imports from repo modules.

What a test asserts is left to review (see the format doc, "Kernel positives").
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "tests" / "simulation_quality" / "rpg_gate" / "kernel_positives.yaml"
CONFIG = ROOT / "tests" / "simulation_quality" / "rpg_gate" / "config.yaml"
KERNEL = {"build_kernel"}
ROW = {"compute", "pool"}
MAX_DEPTH = 4


def _parse(path: Path) -> Optional[ast.Module]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None


def _functions(tree: ast.Module) -> Dict[str, ast.AST]:
    return {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _imports(tree: ast.Module) -> Dict[str, Tuple[str, str]]:
    """local name -> (dotted module, original name) for every ``from X import a as b`` in the module, at any depth."""
    out: Dict[str, Tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                out[alias.asname or alias.name] = (node.module, alias.name)
    return out


def _calls(func: ast.AST) -> List[str]:
    names = []
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            names.append(node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else "")
    return names


def reached(root: Path, path: Path, func_name: str, depth: int = 0, seen: Optional[Set[Tuple[Path, str]]] = None) -> Set[str]:
    """The kernel / row calls (``build_kernel``, ``compute``, ``pool``) reachable from ``func_name`` in ``path``."""
    seen = set() if seen is None else seen
    if depth > MAX_DEPTH or (path, func_name) in seen:
        return set()
    seen.add((path, func_name))
    tree = _parse(path)
    func = _functions(tree).get(func_name) if tree else None
    if func is None:
        return set()
    found: Set[str] = set()
    imports = _imports(tree)
    for name in _calls(func):
        if name in KERNEL or name in ROW:
            found.add(name)
        elif name in _functions(tree):
            found |= reached(root, path, name, depth + 1, seen)
        elif name in imports:
            module, original = imports[name]
            target = root / (module.replace(".", "/") + ".py")
            if target.is_file():
                found |= reached(root, target, original, depth + 1, seen)
    return found


def problems(root: Path, required: Sequence[str], mapping: Mapping[str, Sequence[str]]) -> List[str]:
    out: List[str] = []
    for rid in sorted(set(required) - set(mapping)):
        out.append(f"{rid}: required validity id has no kernel positive in the map")
    for rid in sorted(set(mapping) - set(required)):
        out.append(f"{rid}: map entry for an id that is not required (stale)")
    for rid, nodes in sorted(mapping.items()):
        if not nodes:
            out.append(f"{rid}: entry names no test")
        for node in nodes or []:
            file_part, _, func_name = str(node).partition("::")
            path = root / file_part
            tree = _parse(path)
            if not func_name or tree is None or func_name not in {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}:
                out.append(f"{rid}: {node} is not a test function in that file")
                continue
            calls = reached(root, path, func_name)
            if not calls & KERNEL:
                out.append(f"{rid}: {node} never reaches build_kernel (a hand-built update is a unit test, not a kernel positive)")
            elif not calls & ROW:
                out.append(f"{rid}: {node} reaches build_kernel but never reads the emitted row (no call to compute or pool)")
    return out


def _required() -> List[str]:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return sorted({rid for ids in config["required_validity"].values() for rid in ids})


def test_every_required_validity_id_has_a_real_kernel_positive():
    mapping = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    assert problems(ROOT, _required(), mapping) == []


# ---- regression cases: each failure mode fails the lint

GOOD = '''
def run(): 
    from tools.test_architecture.rpg_gate_run import build_kernel
    from src.observability import rpg_gate_metrics
    kernel = build_kernel("w", 1, "x")
    return rpg_gate_metrics.compute(kernel)


def test_v1_fires():
    assert run()
'''


def _tree(tmp_path: Path, source: str = GOOD, name: str = "tests/t.py") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return tmp_path


def test_a_covered_id_passes(tmp_path):
    assert problems(_tree(tmp_path), ["V1"], {"V1": ["tests/t.py::test_v1_fires"]}) == []


def test_a_required_id_without_an_entry_fails(tmp_path):
    assert problems(_tree(tmp_path), ["V1", "V2"], {"V1": ["tests/t.py::test_v1_fires"]}) == ["V2: required validity id has no kernel positive in the map"]


def test_a_node_id_that_does_not_exist_fails(tmp_path):
    found = problems(_tree(tmp_path), ["V1"], {"V1": ["tests/t.py::test_gone", "tests/missing.py::test_v1_fires"]})
    assert len(found) == 2 and all("is not a test function in that file" in p for p in found)


def test_a_test_that_never_calls_build_kernel_fails(tmp_path):
    source = "def test_v1_fires():\n    update = object()\n    assert update\n"
    assert "never reaches build_kernel" in problems(_tree(tmp_path, source), ["V1"], {"V1": ["tests/t.py::test_v1_fires"]})[0]


def test_a_test_that_runs_the_kernel_but_never_reads_the_emitted_row_fails(tmp_path):
    source = "def test_v1_fires():\n    from tools.test_architecture.rpg_gate_run import build_kernel\n    kernel = build_kernel('w', 1, 'x')\n    assert kernel._ledger.private_counter > 0\n"
    assert "never reads the emitted row" in problems(_tree(tmp_path, source), ["V1"], {"V1": ["tests/t.py::test_v1_fires"]})[0]


def test_an_entry_for_an_id_that_is_not_required_fails(tmp_path):
    found = problems(_tree(tmp_path), ["V1"], {"V1": ["tests/t.py::test_v1_fires"], "V9": ["tests/t.py::test_v1_fires"]})
    assert found == ["V9: map entry for an id that is not required (stale)"]


def test_the_kernel_is_followed_through_a_same_module_helper_and_a_one_hop_import(tmp_path):
    _tree(tmp_path, GOOD.replace("def test_v1_fires", "def test_unused"), "tests/helper.py")
    source = "from tests.helper import run\n\n\ndef test_v1_fires():\n    assert run()\n"
    assert problems(_tree(tmp_path, source), ["V1"], {"V1": ["tests/t.py::test_v1_fires"]}) == []


@pytest.mark.parametrize("entry", [[], None])
def test_an_entry_naming_no_test_fails(tmp_path, entry):
    assert "names no test" in problems(_tree(tmp_path), ["V1"], {"V1": entry})[0]
