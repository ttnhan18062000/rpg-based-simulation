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
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = str(_REPO_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from working_log_writer import append_working_log_row, consolidate_pending_rows, main  # noqa: E402
from working_log_parser import (  # noqa: E402
    HEADER_FIELDS,
    parse_working_log,
    parse_pending_working_log_shards,
)

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


def test_comma_bearing_title_round_trips(tmp_path):
    # TCK-20260915-MONITORING-INTEGRITY-BACKLOG: 9 of 2,013 real working_log.csv rows had an
    # unescaped comma in the title field (e.g. "Clan lifecycle -- joining, leaving, and
    # succession-on-death"), shifting every later column -- all 9 predate this helper's own
    # introduction (TCK-20260912-WORKING-LOG-APPEND-HELPER), written by an earlier, now-removed
    # ad-hoc writer. csv.writer's QUOTE_MINIMAL (used below) already quotes any field containing
    # the delimiter, so this proves the CURRENT writer cannot reproduce that defect.
    log_path = _seed(tmp_path)
    tricky_title = "Clan lifecycle -- joining, leaving, and succession-on-death (M4 idea 40)"
    append_working_log_row(
        "2026-09-15T00:00:00Z", "TCK-COMMA-TITLE", tricky_title, "DONE", "A summary.", "none",
        path=log_path,
    )
    result = parse_working_log(log_path)
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.classification == "clean"
    assert row.record["title"] == tricky_title
    assert row.record["status"] == "DONE"


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


# ---------------------------------------------------------------------------
# TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET: staging + consolidation
# ---------------------------------------------------------------------------


def test_append_working_log_row_stages_without_touching_canonical_csv(tmp_path, monkeypatch):
    """No `path` given (the only way a real caller invokes it) -- stages to a per-batch shard
    under agent-monitoring/data/, never touches tickets/working_log.csv directly."""
    monkeypatch.chdir(tmp_path)
    append_working_log_row(
        "2026-09-25T00:00:00Z", "TCK-STAGE", "A title", "DONE", "A summary.", "none"
    )
    assert not (tmp_path / "tickets" / "working_log.csv").exists()
    pending = parse_pending_working_log_shards(tmp_path / "agent-monitoring" / "data")
    assert len(pending) == 1
    assert pending[0]["ticket_id"] == "TCK-STAGE"


def test_consolidate_pending_rows_orders_by_timestamp_across_multiple_shards(tmp_path):
    """AC4: a consolidation run that sees several different batches' shards at once reconstructs
    true chronological order from each row's own timestamp, not file-glob order."""
    data_root = tmp_path / "agent-monitoring" / "data"
    csv_path = tmp_path / "working_log.csv"
    csv_path.write_text(",".join(HEADER_FIELDS) + "\n", encoding="utf-8")

    # Deliberately name the "later" batch's file so it sorts BEFORE the "earlier" one
    # alphabetically -- proves ordering comes from the timestamp field, not the glob.
    (data_root / "2026-W01").mkdir(parents=True)
    (data_root / "2026-W01" / "aaa-later-batch.working_log.jsonl").write_text(
        json.dumps({
            "timestamp": "2026-09-25T12:00:00Z", "ticket_id": "TCK-LATER", "title": "Later",
            "status": "DONE", "summary": "s", "artifacts_path": "none",
        }) + "\n",
        encoding="utf-8",
    )
    (data_root / "2026-W01" / "zzz-earlier-batch.working_log.jsonl").write_text(
        json.dumps({
            "timestamp": "2026-09-25T08:00:00Z", "ticket_id": "TCK-EARLIER", "title": "Earlier",
            "status": "DONE", "summary": "s", "artifacts_path": "none",
        }) + "\n",
        encoding="utf-8",
    )

    result = consolidate_pending_rows(data_root=data_root, csv_path=csv_path)
    assert result == {"consolidated_rows": 2, "shard_files": 2}

    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert "TCK-EARLIER" in lines[1]  # earlier timestamp lands first, despite the filename sort
    assert "TCK-LATER" in lines[2]


def test_consolidate_pending_rows_is_idempotent(tmp_path):
    data_root = tmp_path / "agent-monitoring" / "data"
    csv_path = tmp_path / "working_log.csv"
    csv_path.write_text(",".join(HEADER_FIELDS) + "\n", encoding="utf-8")
    (data_root / "2026-W01").mkdir(parents=True)
    (data_root / "2026-W01" / "batch-a.working_log.jsonl").write_text(
        json.dumps({
            "timestamp": "2026-09-25T00:00:00Z", "ticket_id": "TCK-A", "title": "A",
            "status": "DONE", "summary": "s", "artifacts_path": "none",
        }) + "\n",
        encoding="utf-8",
    )

    first = consolidate_pending_rows(data_root=data_root, csv_path=csv_path)
    assert first == {"consolidated_rows": 1, "shard_files": 1}
    second = consolidate_pending_rows(data_root=data_root, csv_path=csv_path)
    assert second == {"consolidated_rows": 0, "shard_files": 0}

    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # header + exactly one row, not duplicated


def test_consolidate_pending_rows_merges_with_pre_existing_canonical_content(tmp_path):
    data_root = tmp_path / "agent-monitoring" / "data"
    csv_path = tmp_path / "working_log.csv"
    csv_path.write_text(
        ",".join(HEADER_FIELDS) + "\n2026-09-01T00:00:00Z,TCK-OLD,Old,DONE,s,none\n",
        encoding="utf-8",
    )
    (data_root / "2026-W01").mkdir(parents=True)
    (data_root / "2026-W01" / "batch-a.working_log.jsonl").write_text(
        json.dumps({
            "timestamp": "2026-09-25T00:00:00Z", "ticket_id": "TCK-NEW", "title": "New",
            "status": "DONE", "summary": "s", "artifacts_path": "none",
        }) + "\n",
        encoding="utf-8",
    )

    consolidate_pending_rows(data_root=data_root, csv_path=csv_path)
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert "TCK-OLD" in lines[1]
    assert "TCK-NEW" in lines[2]


def test_consolidate_pending_rows_no_shards_is_a_no_op(tmp_path):
    data_root = tmp_path / "agent-monitoring" / "data"
    csv_path = tmp_path / "working_log.csv"
    csv_path.write_text(",".join(HEADER_FIELDS) + "\n", encoding="utf-8")
    result = consolidate_pending_rows(data_root=data_root, csv_path=csv_path)
    assert result == {"consolidated_rows": 0, "shard_files": 0}
    assert csv_path.read_text(encoding="utf-8").splitlines() == [",".join(HEADER_FIELDS)]


def test_consolidate_pending_rows_missing_data_root_is_a_no_op(tmp_path):
    csv_path = tmp_path / "working_log.csv"
    csv_path.write_text(",".join(HEADER_FIELDS) + "\n", encoding="utf-8")
    result = consolidate_pending_rows(data_root=tmp_path / "does-not-exist", csv_path=csv_path)
    assert result == {"consolidated_rows": 0, "shard_files": 0}


# ---------------------------------------------------------------------------
# AC1 — real throwaway git repo: two working_log shards can never conflict, even under a
# simulated GitHub squash-merge. Mirrors test_monitoring_consolidation.py's own
# test_two_per_ticket_files_never_conflict_under_sequential_squash_merges exactly, for the
# working_log shard shape (TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET's own AC1).
# ---------------------------------------------------------------------------


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True, check=True)


def _init_repo(repo):
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("base\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "-M", "main")


def test_two_working_log_shards_never_conflict_under_sequential_squash_merges(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    week_dir = repo / "agent-monitoring" / "data" / "2026-W01"
    week_dir.mkdir(parents=True)

    _git(repo, "checkout", "-q", "-b", "ticket-a")
    (week_dir / "ticket-a.working_log.jsonl").write_text(
        json.dumps({"timestamp": "t", "ticket_id": "TCK-A", "title": "A", "status": "DONE", "summary": "s", "artifacts_path": "none"}) + "\n"
    )
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-A: add working_log shard")

    _git(repo, "checkout", "-q", "main")
    _git(repo, "checkout", "-q", "ticket-a", "--", "agent-monitoring")
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-A: add working_log shard (squashed) (#1)")

    _git(repo, "checkout", "-q", "-b", "ticket-b", "main~1")
    week_dir_b = repo / "agent-monitoring" / "data" / "2026-W01"
    week_dir_b.mkdir(parents=True)
    (week_dir_b / "ticket-b.working_log.jsonl").write_text(
        json.dumps({"timestamp": "t", "ticket_id": "TCK-B", "title": "B", "status": "DONE", "summary": "s", "artifacts_path": "none"}) + "\n"
    )
    _git(repo, "add", "agent-monitoring")
    _git(repo, "commit", "-q", "-m", "TCK-B: add working_log shard")

    _git(repo, "checkout", "-q", "main")
    merge = subprocess.run(
        ["git", "-C", str(repo), "merge", "--no-ff", "-m", "merge ticket-b", "ticket-b"],
        capture_output=True, text=True,
    )
    assert merge.returncode == 0, f"expected a clean merge, got a conflict:\n{merge.stdout}\n{merge.stderr}"
    assert (week_dir / "ticket-a.working_log.jsonl").exists()
    assert (week_dir / "ticket-b.working_log.jsonl").exists()
