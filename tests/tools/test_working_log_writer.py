"""Tests for tools/working_log_writer.py (TCK-20260912-WORKING-LOG-APPEND-HELPER).

Two independent concerns are covered:

1. The writer itself: round-trips with tools/working_log_parser.py, emits LF only, appends at the
   bottom, never truncates, and its CLI (`--data-file`) survives content that would break a naive
   shell/Python string-embedding.

2. The sole-writer guard (`test_working_log_csv_has_exactly_one_writer`): an AST walk over every
   `.py` file under `tools/` that resolves each `open()`/`.open()` call's path argument back to a
   literal string (through a module-level constant, and a single hop of function-local
   parameter-default-to-module-constant resolution -- exactly the shape
   `tools/working_log_writer.py`'s own `_WORKING_LOG_PATH` / `path` parameter default uses) and
   asserts exactly one write-mode call resolves to "tickets/working_log.csv", and it lives in
   working_log_writer.py. A grep-based version of this guard was rejected during planning: the
   literal path string never appears on the same line as the `open(` call it protects (it lives
   only in `_WORKING_LOG_PATH`'s own assignment), so a literal-text grep would find zero matches
   including the helper's own -- indistinguishable from "no writer at all" and useless as a guard.
   The resolver is exercised directly against small synthetic source snippets below, independent of
   the real repo tree, to prove it actually performs that resolution rather than merely happening
   to pass against today's file layout.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = str(_REPO_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from working_log_writer import append_working_log_row, main  # noqa: E402
from working_log_parser import HEADER_FIELDS, parse_working_log  # noqa: E402

_TARGET = "tickets/working_log.csv"
_WRITE_MODES = {"a", "w", "a+", "w+", "x"}


# ─── AST resolver (mirrors plan.md Step 4's design exactly) ────────────────────────────────────


def _literal_value(node):
    """Return the literal string a node denotes: a plain string constant, or a `Path("literal")`
    call (`Path` bound either as a bare name or via attribute access, e.g. `pathlib.Path`).
    Returns None for anything else -- callers must not guess."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call):
        func = node.func
        is_path_call = (isinstance(func, ast.Name) and func.id == "Path") or (
            isinstance(func, ast.Attribute) and func.attr == "Path"
        )
        if is_path_call and node.args:
            return _literal_value(node.args[0])
    return None


def _module_level_map(tree: ast.Module) -> dict:
    """name -> literal string, from every top-level `name = "literal"` / `name = Path("literal")`
    assignment. Deliberately top-level only -- a single, unambiguous binding site to resolve
    against."""
    mapping = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            value = _literal_value(node.value)
            if value is not None:
                mapping[node.targets[0].id] = value
    return mapping


def _resolve_name(node, local_map: dict, module_map: dict):
    """Resolve `node` to a literal string: directly if it's itself a literal, otherwise if it's a
    `Name`, look it up first in the function-local map, falling back to the module-level map.
    Returns None if it can't be resolved -- never a guess."""
    value = _literal_value(node)
    if value is not None:
        return value
    if isinstance(node, ast.Name):
        if node.id in local_map:
            return local_map[node.id]
        if node.id in module_map:
            return module_map[node.id]
    return None


def _iter_same_scope_statements(node):
    """Yield every statement nested under `node` (if/for/while/with/try bodies included)
    without descending into a nested function/class/lambda's own scope -- local-assignment
    collection for one function must not pick up an inner function's own locals."""
    for field in ("body", "orelse", "finalbody", "handlers"):
        children = getattr(node, field, None)
        if not children:
            continue
        for child in children:
            if isinstance(child, ast.ExceptHandler):
                yield from _iter_same_scope_statements(child)
                continue
            yield child
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            yield from _iter_same_scope_statements(child)


def _function_local_map(func_node, module_map: dict) -> dict:
    """name -> literal string for one function: every parameter whose default is a literal
    directly, or a `Name` resolving against the module-level map (the single-hop case --
    `path: Path = _WORKING_LOG_PATH`), plus every local `name = "literal"` assignment inside the
    function body (not inside a nested function/class)."""
    mapping = {}
    args = func_node.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    offset = len(positional) - len(defaults)
    for arg, default in zip(positional[offset:], defaults):
        value = _resolve_name(default, {}, module_map)
        if value is not None:
            mapping[arg.arg] = value
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        if default is None:
            continue
        value = _resolve_name(default, {}, module_map)
        if value is not None:
            mapping[arg.arg] = value

    for stmt in _iter_same_scope_statements(func_node):
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
        ):
            value = _literal_value(stmt.value)
            if value is not None:
                mapping[stmt.targets[0].id] = value
    return mapping


def _target_and_mode_nodes(call_node: ast.Call):
    """For `open(path, mode, ...)` or `<expr>.open(mode, ...)` shaped calls, return
    (target_node, mode_node) -- the node denoting the path argument (or receiver expression) and
    the node denoting the mode argument (positional or `mode=` keyword). Returns (None, None) for
    any other call shape."""
    func = call_node.func
    if isinstance(func, ast.Name) and func.id == "open":
        target = call_node.args[0] if call_node.args else None
        mode = call_node.args[1] if len(call_node.args) >= 2 else None
    elif isinstance(func, ast.Attribute) and func.attr == "open":
        target = func.value
        mode = call_node.args[0] if call_node.args else None
    else:
        return None, None
    for kw in call_node.keywords:
        if kw.arg == "mode":
            mode = kw.value
    return target, mode


def _is_write_mode(mode_node) -> bool:
    if mode_node is None:
        return False
    value = _literal_value(mode_node)
    return value in _WRITE_MODES


def find_write_mode_open_calls(source: str, resolved_target: str) -> list:
    """Parse `source` and return the line numbers of every open()/.open() call whose path
    argument resolves (via module-level and single-hop function-local literal binding) to
    `resolved_target`, and whose mode argument indicates a write/append mode."""
    tree = ast.parse(source)
    module_map = _module_level_map(tree)
    hits = []

    def visit(node, local_map):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, _function_local_map(child, module_map))
                continue
            if isinstance(child, ast.Call):
                target, mode = _target_and_mode_nodes(child)
                if target is not None:
                    resolved = _resolve_name(target, local_map, module_map)
                    if resolved == resolved_target and _is_write_mode(mode):
                        hits.append(child.lineno)
            visit(child, local_map)

    visit(tree, module_map)
    return hits


def _scan_directory(directory: Path, resolved_target: str) -> list:
    """Every (relative posix path, lineno) hit across all .py files under `directory`."""
    hits = []
    for py_file in sorted(directory.rglob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        for lineno in find_write_mode_open_calls(source, resolved_target):
            hits.append((py_file.relative_to(directory).as_posix(), lineno))
    return hits


# ─── Resolver unit tests — synthetic snippets, independent of the real repo tree ───────────────


def test_resolver_positive_single_hop_parameter_default_to_module_constant():
    """Exact shape of tools/working_log_writer.py's own design: a module-level constant, a
    function parameter defaulting to that constant by name, and an open() call using the
    parameter -- proves the resolver actually chains through the hop, not just that the
    end-to-end repo scan happens to pass for unrelated reasons."""
    source = '''
from pathlib import Path

_WORKING_LOG_PATH = Path("tickets/working_log.csv")


def append_working_log_row(row, path=_WORKING_LOG_PATH):
    with open(path, "a", newline="") as f:
        f.write(row)
'''
    hits = find_write_mode_open_calls(source, _TARGET)
    assert len(hits) == 1


def test_resolver_no_hit_on_read_only_open():
    """Mirrors tools/working_log_parser.py's own `open(path, newline="")` call -- mode omitted
    (defaults to "r"), must not be flagged."""
    source = '''
from pathlib import Path

_WORKING_LOG_PATH = Path("tickets/working_log.csv")


def read_it(path=_WORKING_LOG_PATH):
    with open(path, newline="") as f:
        return f.read()
'''
    assert find_write_mode_open_calls(source, _TARGET) == []


def test_resolver_no_hit_on_differently_named_file_with_same_variable_name():
    """A local variable also named `path` pointing at an unrelated file must not false-positive
    just because the variable name matches."""
    source = '''
def write_other(path="some/other/file.txt"):
    with open(path, "a") as f:
        f.write("x")
'''
    assert find_write_mode_open_calls(source, _TARGET) == []


def test_resolver_no_hit_on_plain_text_mention_with_no_open_call():
    source = '''
def documented_only():
    """This function talks about tickets/working_log.csv in its docstring only."""
    return "tickets/working_log.csv"
'''
    assert find_write_mode_open_calls(source, _TARGET) == []


def test_resolver_detects_method_call_open_style():
    """`<expr>.open("a", ...)` shape, matching the original (pre-helper)
    `working_log_path.open("a", newline="", encoding="utf-8")` call site."""
    source = '''
from pathlib import Path

_WORKING_LOG_PATH = Path("tickets/working_log.csv")


def write_it(path=_WORKING_LOG_PATH):
    with path.open("a", newline="", encoding="utf-8") as f:
        f.write("x")
'''
    assert len(find_write_mode_open_calls(source, _TARGET)) == 1


def test_guard_fires_on_a_second_writer(tmp_path):
    """Proves the guard actually detects a second writer appearing, not just that it currently
    reports one -- a fixture tree with two independent modules opening the same resolved path in
    append mode."""
    (tmp_path / "good_writer.py").write_text(
        'from pathlib import Path\n'
        '_WORKING_LOG_PATH = Path("tickets/working_log.csv")\n'
        'def append_row(path=_WORKING_LOG_PATH):\n'
        '    with open(path, "a") as f:\n'
        '        f.write("x")\n'
    )
    (tmp_path / "evil_writer.py").write_text(
        'def sneaky_append():\n'
        '    target = "tickets/working_log.csv"\n'
        '    with open(target, "a") as f:\n'
        '        f.write("y")\n'
    )
    hits = _scan_directory(tmp_path, _TARGET)
    assert len(hits) == 2, hits


# ─── Sole-writer guard over the real repo tree ─────────────────────────────────────────────────


def test_working_log_csv_has_exactly_one_writer():
    hits = _scan_directory(_REPO_ROOT / "tools", _TARGET)
    assert len(hits) == 1, (
        f"expected exactly one write-mode open() call resolving to {_TARGET!r} under tools/, "
        f"found {len(hits)}: {hits}"
    )
    assert hits[0][0] == "working_log_writer.py", hits


# ─── The writer itself ──────────────────────────────────────────────────────────────────────────


_TRICKY_SUMMARY = 'Fixed "the bug", added tests,\nupdated docs.'


def _seed(tmp_path: Path) -> Path:
    log_path = tmp_path / "working_log.csv"
    log_path.write_text(",".join(HEADER_FIELDS) + "\n", encoding="utf-8")
    return log_path


def test_tricky_field_round_trips_through_the_parser(tmp_path):
    log_path = _seed(tmp_path)
    append_working_log_row(
        "2026-09-12T00:00:00Z", "TCK-FAKE", "A title", "DONE", _TRICKY_SUMMARY, "stored_artifacts/TCK-FAKE",
        path=log_path,
    )
    result = parse_working_log(log_path)
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.classification == "clean"
    assert row.record["summary"] == _TRICKY_SUMMARY
    assert row.record["ticket_id"] == "TCK-FAKE"


def test_output_ends_in_bare_lf_with_no_cr_bytes(tmp_path):
    log_path = _seed(tmp_path)
    append_working_log_row(
        "2026-09-12T00:00:00Z", "TCK-FAKE", "A title", "DONE", _TRICKY_SUMMARY, "stored_artifacts/TCK-FAKE",
        path=log_path,
    )
    raw = log_path.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")


def test_appends_after_existing_content_never_truncates_or_inserts_before_header(tmp_path):
    log_path = _seed(tmp_path)
    existing_row = "2026-09-01T00:00:00Z,TCK-EXISTING,Existing,DONE,Already there.,none\n"
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        f.write(existing_row)

    append_working_log_row(
        "2026-09-12T00:00:00Z", "TCK-NEW", "New title", "DONE", "New summary.", "none",
        path=log_path,
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(HEADER_FIELDS)
    assert "TCK-EXISTING" in lines[1]
    assert "TCK-NEW" in lines[2]
    assert len(lines) == 3


def test_two_consecutive_appends_land_in_order_at_the_bottom(tmp_path):
    log_path = _seed(tmp_path)
    append_working_log_row("2026-09-12T00:00:00Z", "TCK-A", "A", "DONE", "a", "none", path=log_path)
    append_working_log_row("2026-09-12T00:01:00Z", "TCK-B", "B", "DONE", "b", "none", path=log_path)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert "TCK-A" in lines[1]
    assert "TCK-B" in lines[2]


def test_cli_reads_data_file_and_appends(tmp_path):
    log_path = _seed(tmp_path)
    data = {
        "timestamp": "2026-09-12T00:00:00Z",
        "ticket_id": "TCK-CLI",
        "title": 'A "quoted", tricky title',
        "status": "DONE",
        "summary": _TRICKY_SUMMARY,
        "artifacts_path": "stored_artifacts/TCK-CLI",
    }
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(data), encoding="utf-8")

    original_append = append_working_log_row
    try:
        import working_log_writer

        def _patched(**kwargs):
            kwargs["path"] = log_path
            return original_append(**kwargs)

        working_log_writer.append_working_log_row = _patched
        main(["--data-file", str(data_file)])
    finally:
        working_log_writer.append_working_log_row = original_append

    result = parse_working_log(log_path)
    assert len(result.rows) == 1
    assert result.rows[0].record["title"] == data["title"]
    assert result.rows[0].record["summary"] == _TRICKY_SUMMARY
