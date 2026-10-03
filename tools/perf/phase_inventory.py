#!/usr/bin/env python3
"""Re-runnable inventory of the authoritative pipeline's phase calls (PA-05A, evidence only).

Parses ``src/engine/pipeline.py`` with ``ast`` -- engine code is never imported or executed -- and
reports, in source order, every ``run_phase()`` call inside ``AuthoritativeApplyPipeline.refine``
plus the direct (non-``run_phase``) assignments to ``update``. It then compares that executable
inventory with the phase lists and counts the repository documents state, and with the phase names
the dependency graph and domain-permission declarations know.

Report-only: nothing here changes engine code, edits a document, or decides which count is right
(that is PERF-D6). No timestamps, so two runs on one tree are byte-identical.

    python3 tools/perf/phase_inventory.py --format json
    python3 tools/perf/phase_inventory.py --format md
    python3 tools/perf/phase_inventory.py --check docs/performance/phase_inventory.json

Ticket: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

PIPELINE_PATH = "src/engine/pipeline.py"
PIPELINE_CLASS = "AuthoritativeApplyPipeline"
PIPELINE_METHOD = "refine"
PHASE_GRAPH_PATH = "src/engine/phase_graph.py"
PHASE_GRAPH_CLASS = "PhaseDependencyGraph"
DOMAIN_PERMISSIONS_PATH = "src/engine/phase_domain_permissions.py"
DOC_PIPELINE_PATH = "docs/engine/authoritative_pipeline.md"
DOC_D19_PATH = "docs/audits/D19_domain_phase_inventory.md"
GENERATOR_PATH = "tools/agent_orchestration_codex_adapter/generator.py"
EPIC_PATH = "docs/plans/design_enhancement/subphase_domain_contracts_epic.md"

# Statement types that make a node "conditional or loop" context.
_CONTEXT_NODES = {
    ast.If: "if",
    ast.For: "for",
    ast.While: "while",
    ast.Try: "try",
    ast.With: "with",
}


# --------------------------------------------------------------------------- pipeline (AST)

def _children(node: ast.AST) -> List[ast.AST]:
    return list(ast.iter_child_nodes(node))


def _dfs(node: ast.AST):
    """Pre-order, source-order traversal (ast.walk is breadth-first)."""
    yield node
    for child in _children(node):
        yield from _dfs(child)


def _parent_map(root: ast.AST) -> Dict[ast.AST, ast.AST]:
    parents: Dict[ast.AST, ast.AST] = {}
    for node in _dfs(root):
        for child in _children(node):
            parents[child] = node
    return parents


def _context(node: ast.AST, parents: Dict[ast.AST, ast.AST], stop: ast.AST) -> List[str]:
    """Enclosing conditional/loop statements between ``node`` and ``stop``, outermost first."""
    found: List[str] = []
    cur = parents.get(node)
    while cur is not None and cur is not stop:
        kind = _CONTEXT_NODES.get(type(cur))
        if kind:
            found.append(f"{kind}@L{cur.lineno}")
        cur = parents.get(cur)
    return list(reversed(found))


def _unparse(node: Optional[ast.AST]) -> Optional[str]:
    return None if node is None else ast.unparse(node)


def _dispatch_target(fn_node: Optional[ast.AST]) -> Optional[str]:
    """The callable a phase dispatches to, as written.

    For a ``lambda u: X.apply(state, u)`` it is the first call in the body whose function is not an
    attribute of the lambda's own argument (so ``u.merge(X.apply(...))`` reports ``X.apply``).
    For a bare name or attribute it is that expression.
    """
    if fn_node is None:
        return None
    if isinstance(fn_node, ast.Lambda):
        arg_names = {a.arg for a in fn_node.args.args}
        for sub in _dfs(fn_node.body):
            if not isinstance(sub, ast.Call):
                continue
            func = sub.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in arg_names
            ):
                continue
            return _unparse(func)
        return _unparse(fn_node.body)
    return _unparse(fn_node)


def _call_arg(call: ast.Call, index: int, keyword: str) -> Optional[ast.AST]:
    if len(call.args) > index:
        return call.args[index]
    for kw in call.keywords:
        if kw.arg == keyword:
            return kw.value
    return None


def _is_run_phase_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run_phase"


def _outside_phase_scopes(node: ast.AST, parents: Dict[ast.AST, ast.AST], stop: ast.AST) -> bool:
    """True when ``node`` is not inside a lambda, a nested def, or a ``run_phase()`` call."""
    cur = parents.get(node)
    while cur is not None and cur is not stop:
        if isinstance(cur, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)) or _is_run_phase_call(cur):
            return False
        cur = parents.get(cur)
    return True


def find_method(tree: ast.AST, class_name: str, method_name: str) -> Optional[ast.FunctionDef]:
    for node in _dfs(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    return None


def inventory_pipeline(
    source: str,
    class_name: str = PIPELINE_CLASS,
    method_name: str = PIPELINE_METHOD,
) -> Dict[str, Any]:
    """Executable inventory of ``class_name.method_name`` from source text alone."""
    tree = ast.parse(source)
    method = find_method(tree, class_name, method_name)
    if method is None:
        return {
            "found": False,
            "class": class_name,
            "method": method_name,
            "run_phase_calls": [],
            "direct_operations": [],
            "direct_calls": [],
            "summary": {},
        }
    parents = _parent_map(method)

    calls: List[Dict[str, Any]] = []
    for node in _dfs(method):
        if not _is_run_phase_call(node):
            continue
        name_node = _call_arg(node, 0, "phase_name")
        flag_node = _call_arg(node, 3, "feature_flag")
        name_is_literal = isinstance(name_node, ast.Constant) and isinstance(name_node.value, str)
        flag_is_literal = isinstance(flag_node, ast.Constant) and isinstance(flag_node.value, str)
        context = _context(node, parents, method)
        calls.append({
            "ordinal": len(calls) + 1,
            "name": name_node.value if name_is_literal else None,
            "name_dynamic": not name_is_literal,
            "name_expression": None if name_is_literal else _unparse(name_node),
            "line": node.lineno,
            "feature_flag": (flag_node.value if flag_is_literal else _unparse(flag_node)),
            "dispatch": _dispatch_target(_call_arg(node, 2, "phase_fn")),
            "conditional_or_loop": bool(context),
            "context": context,
        })

    direct: List[Dict[str, Any]] = []
    for node in _dfs(method):
        if not isinstance(node, (ast.Assign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "update" for t in targets):
            continue
        value = node.value
        if any(_is_run_phase_call(sub) for sub in _dfs(value)):
            continue
        context = _context(node, parents, method)
        if isinstance(value, ast.Call):
            expr = _unparse(value.func)
        else:
            expr = f"<{type(value).__name__}> {_unparse(value)}"
        direct.append({
            "ordinal": len(direct) + 1,
            "line": node.lineno,
            "statement": "augmented-assign" if isinstance(node, ast.AugAssign) else "assign",
            "operation": expr,
            "conditional_or_loop": bool(context),
            "context": context,
        })

    # Direct calls: ``ClassName.method(...)`` made by refine() itself, outside every run_phase()
    # call, lambda and nested def. This is a structural heuristic (a call on a capitalised name), so
    # it finds phase-like services wired in directly; it does not claim every hit is a phase.
    direct_calls: List[Dict[str, Any]] = []
    for node in _dfs(method):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id[:1].isupper()
        ):
            continue
        if not _outside_phase_scopes(node, parents, method):
            continue
        context = _context(node, parents, method)
        direct_calls.append({
            "ordinal": len(direct_calls) + 1,
            "line": node.lineno,
            "call": _unparse(node.func),
            "conditional_or_loop": bool(context),
            "context": context,
        })

    names = [c["name"] for c in calls if c["name"] is not None]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    return {
        "found": True,
        "class": class_name,
        "method": method_name,
        "run_phase_calls": calls,
        "direct_operations": direct,
        "direct_calls": direct_calls,
        "summary": {
            "run_phase_calls": len(calls),
            "distinct_literal_names": len(set(names)),
            "duplicate_names": duplicates,
            "dynamic_name_calls": sum(1 for c in calls if c["name_dynamic"]),
            "conditional_or_loop_calls": sum(1 for c in calls if c["conditional_or_loop"]),
            "feature_flagged_calls": sum(1 for c in calls if c["feature_flag"]),
            "direct_operations": len(direct),
            "direct_calls": len(direct_calls),
        },
    }


# --------------------------------------------------------------------------- declarations (AST)

def extract_dependency_graph_names(source: str, class_name: str = PHASE_GRAPH_CLASS) -> List[str]:
    """Keys of ``<class_name>.PHASES`` (a dict literal), in source order."""
    tree = ast.parse(source)
    for node in _dfs(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                value = None
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == "PHASES":
                    value = item.value
                elif isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PHASES" for t in item.targets):
                    value = item.value
                if isinstance(value, ast.Dict):
                    return [k.value for k in value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    return []


def extract_domain_permission_keys(source: str) -> List[str]:
    """Distinct ``TickPhase.<MEMBER>`` keys used by the ``PHASE_*_DOMAINS`` dict literals."""
    tree = ast.parse(source)
    keys: List[str] = []
    for node in tree.body:
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.startswith("PHASE_"):
            value = node.value
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("PHASE_") for t in node.targets):
            value = node.value
        if isinstance(value, ast.Dict):
            for k in value.keys:
                if isinstance(k, ast.Attribute) and k.attr not in keys:
                    keys.append(k.attr)
    return keys


# --------------------------------------------------------------------------- documents (text)

def extract_pipeline_doc(text: str) -> Dict[str, Any]:
    """``authoritative_pipeline.md``: heading count and the numbered phase table."""
    heading = re.search(r"^##\s+The\s+(\d+)\s+Phases", text, re.M)
    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|", text, re.M)
    return {
        "stated_count": int(heading.group(1)) if heading else None,
        "stated_in": "heading 'The N Phases of Refinement'" if heading else None,
        "entries": [name for _, name in rows],
    }


def extract_d19_doc(text: str) -> Dict[str, Any]:
    """D19 audit: Part A ``PP-NN`` rows and the pipeline total in its summary table."""
    part_a = text
    start = re.search(r"^##\s+Part A", text, re.M)
    if start:
        end = re.search(r"^##\s+Part B", text[start.end():], re.M)
        part_a = text[start.start(): start.end() + (end.start() if end else len(text))]
    rows = re.findall(r"^\|\s*PP-\d+\s*\|\s*`([^`]+)`\s*\|", part_a, re.M)
    total = re.search(r"^\|\s*`pipeline\.py:refine\(\)`\s*\|\s*(\d+)\s*\|", text, re.M)
    return {
        "stated_count": int(total.group(1)) if total else None,
        "stated_in": "summary table row 'pipeline.py:refine()'" if total else None,
        "entries": rows,
    }


def extract_generator_note(text: str) -> Dict[str, Any]:
    """The generator's ``_AUTHORITATIVE_PIPELINE_NOTE``: a count in prose, no names."""
    note = re.search(r"^_AUTHORITATIVE_PIPELINE_NOTE\s*=\s*(.+)$", text, re.M)
    count = re.search(r"(\d+)-phase", note.group(1)) if note else None
    return {
        "stated_count": int(count.group(1)) if count else None,
        "stated_in": "_AUTHORITATIVE_PIPELINE_NOTE" if count else None,
        "entries": [],
    }


def extract_epic_counts(text: str) -> Dict[str, Any]:
    """The subphase-contracts epic: counts stated in prose, no names."""
    counts = [int(n) for n in re.findall(r"\b(\d+)\s+(?:named\s+)?(?:sub-phases|Resolution phases)", text)]
    distinct = sorted(set(counts))
    return {
        "stated_count": distinct[0] if len(distinct) == 1 else None,
        "stated_in": "prose ('N sub-phases' / 'N Resolution phases')" if counts else None,
        "stated_counts_seen": distinct,
        "mentions": len(counts),
        "entries": [],
    }


def compare_source(
    source_id: str,
    path: str,
    extracted: Optional[Dict[str, Any]],
    executable_names: List[str],
    read_error: Optional[str] = None,
) -> Dict[str, Any]:
    if extracted is None:
        return {"id": source_id, "path": path, "readable": False, "read_error": read_error}
    entries = extracted["entries"]
    exe = set(executable_names)
    listed = set(entries)
    out: Dict[str, Any] = {
        "id": source_id,
        "path": path,
        "readable": True,
        "stated_count": extracted["stated_count"],
        "stated_in": extracted["stated_in"],
        "names_listed": len(entries),
        "duplicate_entries": sorted({e for e in entries if entries.count(e) > 1}),
    }
    if "stated_counts_seen" in extracted:
        out["stated_counts_seen"] = extracted["stated_counts_seen"]
    if entries:
        out["executable_phases_without_entry"] = [n for n in executable_names if n not in listed]
        out["entries_matching_no_executable_phase"] = [e for e in entries if e not in exe]
        out["order_differs_from_executable"] = [e for e in entries if e in exe] != [
            n for n in executable_names if n in listed
        ]
    else:
        out["note"] = "states a count only; no phase names to compare"
    return out


def compare_declarations(executable_names: List[str], graph_names: List[str], permission_keys: List[str]) -> Dict[str, Any]:
    exe, graph = set(executable_names), set(graph_names)
    return {
        "dependency_graph": {
            "path": f"{PHASE_GRAPH_PATH}::{PHASE_GRAPH_CLASS}.PHASES",
            "names": len(graph_names),
            "in_pipeline_not_in_graph": [n for n in executable_names if n not in graph],
            "in_graph_not_in_pipeline": [n for n in graph_names if n not in exe],
        },
        "domain_permissions": {
            "path": DOMAIN_PERMISSIONS_PATH,
            "granularity": "TickPhase members (kernel phases), not refine() phases",
            "keys": permission_keys,
            "pipeline_names_matching_a_key": [n for n in executable_names if n.upper() in permission_keys],
            "note": "keys are kernel TickPhase members, a different counted unit from refine() phase names",
        },
    }


# --------------------------------------------------------------------------- report

def _read(root: Path, rel: str) -> "tuple[Optional[str], Optional[str]]":
    try:
        return (root / rel).read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def build_report(root: Path = REPO_ROOT) -> Dict[str, Any]:
    pipeline_src, pipeline_err = _read(root, PIPELINE_PATH)
    if pipeline_src is None:
        raise SystemExit(f"cannot read {PIPELINE_PATH}: {pipeline_err}")
    pipeline = inventory_pipeline(pipeline_src)
    executable = [c["name"] for c in pipeline["run_phase_calls"] if c["name"] is not None]

    sources: List[Dict[str, Any]] = []
    for source_id, rel, extractor in (
        ("authoritative_pipeline_md", DOC_PIPELINE_PATH, extract_pipeline_doc),
        ("d19_domain_phase_inventory", DOC_D19_PATH, extract_d19_doc),
        ("codex_generator_note", GENERATOR_PATH, extract_generator_note),
        ("subphase_domain_contracts_epic", EPIC_PATH, extract_epic_counts),
    ):
        text, err = _read(root, rel)
        sources.append(compare_source(source_id, rel, extractor(text) if text is not None else None, executable, err))

    graph_src, _ = _read(root, PHASE_GRAPH_PATH)
    perm_src, _ = _read(root, DOMAIN_PERMISSIONS_PATH)
    graph_names = extract_dependency_graph_names(graph_src) if graph_src else []
    perm_keys = extract_domain_permission_keys(perm_src) if perm_src else []

    return {
        "tool": "tools/perf/phase_inventory.py",
        "ticket": "TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT",
        "pipeline_source": f"{PIPELINE_PATH}::{PIPELINE_CLASS}.{PIPELINE_METHOD}",
        "pipeline": pipeline,
        "documented_sources": sources,
        "declarations": compare_declarations(executable, graph_names, perm_keys),
    }


def to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- markdown

def _cell(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).replace("|", "\\|")


def _list(items: List[str]) -> str:
    return ", ".join(f"`{i}`" for i in items) if items else "none"


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def to_markdown(report: Dict[str, Any], source_commit: str) -> str:
    pipe = report["pipeline"]
    summary = pipe.get("summary", {})
    out: List[str] = [
        "---",
        "status: active",
        "layer: performance",
        "authority: P2",
        "audience: agent",
        "tags: [performance, architecture, engine]",
        "---",
        "",
        "# Authoritative Pipeline Phase Inventory",
        "",
        f"Generated from commit `{source_commit}` by `tools/perf/phase_inventory.py`.",
        "Regenerate with:",
        "",
        "```",
        "python3 tools/perf/phase_inventory.py --format md > docs/performance/phase_inventory.md",
        "python3 tools/perf/phase_inventory.py --format json > docs/performance/phase_inventory.json",
        "python3 tools/perf/phase_inventory.py --check docs/performance/phase_inventory.json",
        "```",
        "",
        "Evidence only (PA-05A, `TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT`). This report states",
        "discrepancies; it does not decide which count is right (PERF-D6) and edits no document.",
        "Counts below are measured, not asserted anywhere in a test: `refine()` changes on purpose.",
        "",
        f"## 1. Executable inventory (`{report['pipeline_source']}`)",
        "",
        f"- `run_phase()` calls: **{summary.get('run_phase_calls')}**; distinct literal names: "
        f"**{summary.get('distinct_literal_names')}**; duplicate names: {_list(summary.get('duplicate_names', []))}",
        f"- dynamic-name calls: {summary.get('dynamic_name_calls')}; conditional/loop calls: "
        f"{summary.get('conditional_or_loop_calls')}; feature-flagged calls: {summary.get('feature_flagged_calls')}",
        f"- direct operations on `update` (not through `run_phase`): {summary.get('direct_operations')}; "
        f"direct class-method calls outside `run_phase`: {summary.get('direct_calls')}",
        "",
        "### 1.1 `run_phase()` calls in source order",
        "",
        "| # | Phase name | Line | Feature flag | Dispatch | Conditional/loop |",
        "|---|---|---|---|---|---|",
    ]
    for c in pipe["run_phase_calls"]:
        name = f"`{c['name']}`" if not c["name_dynamic"] else f"dynamic: `{c['name_expression']}`"
        ctx = ", ".join(c["context"]) if c["context"] else "no"
        out.append(f"| {c['ordinal']} | {name} | {c['line']} | {_cell(c['feature_flag'])} | "
                   f"{_cell(c['dispatch'])} | {_cell(ctx)} |")
    out += [
        "",
        "### 1.2 Direct operations on `update` that do not go through `run_phase()`",
        "",
        "Every assignment to the name `update` inside `refine` whose value contains no `run_phase()` call.",
        "These are a separate counted unit: they transform the update between phases.",
        "",
        "| # | Line | Statement | Operation | Conditional/loop |",
        "|---|---|---|---|---|",
    ]
    for d in pipe["direct_operations"]:
        ctx = ", ".join(d["context"]) if d["context"] else "no"
        out.append(f"| {d['ordinal']} | {d['line']} | {d['statement']} | `{_cell(d['operation'])}` | {_cell(ctx)} |")
    out += [
        "",
        "### 1.3 Direct class-method calls made by `refine()` outside `run_phase()`",
        "",
        "Calls of the form `ClassName.method(...)` that sit outside every `run_phase()` call, lambda and",
        "nested function. A structural heuristic: it finds services wired in directly, which a count of",
        "`run_phase()` calls does not see. Not every hit is a phase.",
        "",
        "| # | Line | Call | Conditional/loop |",
        "|---|---|---|---|",
    ]
    for d in pipe.get("direct_calls", []):
        ctx = ", ".join(d["context"]) if d["context"] else "no"
        out.append(f"| {d['ordinal']} | {d['line']} | `{d['call']}` | {_cell(ctx)} |")
    out += ["", "## 2. Documented sources against the executable phases", ""]
    out += ["| Source | Path | Stated count | Names listed | Executable phases with no entry | Entries matching no executable phase |",
            "|---|---|---|---|---|---|"]
    for s in report["documented_sources"]:
        if not s["readable"]:
            out.append(f"| {s['id']} | `{s['path']}` | unreadable: {_cell(s.get('read_error'))} | - | - | - |")
            continue
        count = _cell(s["stated_count"])
        if s.get("stated_counts_seen") and len(s["stated_counts_seen"]) > 1:
            count = f"mixed: {s['stated_counts_seen']}"
        if s["names_listed"]:
            missing = _list(s["executable_phases_without_entry"])
            extra = _list(s["entries_matching_no_executable_phase"])
        else:
            missing = extra = "n/a (count only)"
        out.append(f"| {s['id']} | `{s['path']}` | {count} | {s['names_listed']} | {missing} | {extra} |")
    out += ["", "Notes:", ""]
    for s in report["documented_sources"]:
        if s["readable"] and s["names_listed"]:
            out.append(f"- `{s['id']}`: order differs from the executable order for the shared names: "
                       f"{_cell(s['order_differs_from_executable'])}; duplicate entries: {_list(s['duplicate_entries'])}.")
        elif s["readable"]:
            out.append(f"- `{s['id']}`: {s.get('note', '')}.")
    decl = report["declarations"]
    graph, perms = decl["dependency_graph"], decl["domain_permissions"]
    out += [
        "",
        "## 3. Declarations against the executable phases",
        "",
        f"### 3.1 `PhaseDependencyGraph.PHASES` ({graph['names']} names)",
        "",
        f"- In the pipeline but not in the graph: {_list(graph['in_pipeline_not_in_graph'])}",
        f"- In the graph but not in the pipeline: {_list(graph['in_graph_not_in_pipeline'])}",
        "",
        "### 3.2 `phase_domain_permissions.py`",
        "",
        f"- Granularity: {perms['granularity']}",
        f"- Keys: {_list(perms['keys'])}",
        f"- Pipeline phase names matching a key: {_list(perms['pipeline_names_matching_a_key'])}",
        f"- {perms['note']}",
        "",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------------- --check

def _strip_lines(obj: Any) -> Any:
    """Drop source line numbers and the context line suffixes so unrelated edits don't read as drift."""
    if isinstance(obj, dict):
        return {k: _strip_lines(v) for k, v in obj.items() if k != "line"}
    if isinstance(obj, list):
        return [_strip_lines(v) for v in obj]
    if isinstance(obj, str):
        return re.sub(r"@L\d+", "@L", obj)
    return obj


def _phase_names(report: Dict[str, Any]) -> List[str]:
    return [
        c["name"] if c.get("name") is not None else f"<dynamic:{c.get('name_expression')}>"
        for c in report.get("pipeline", {}).get("run_phase_calls", [])
    ]


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flat.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list) and obj and all(not isinstance(i, (dict, list)) for i in obj):
        flat[prefix] = obj
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flat.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        flat[prefix] = obj
    return flat


def diff_reports(committed: Dict[str, Any], live: Dict[str, Any]) -> List[str]:
    """Readable differences. Source line numbers are ignored: only structure counts as drift."""
    lines: List[str] = []
    old, new = _phase_names(committed), _phase_names(live)
    added = [n for n in new if n not in old]
    removed = [n for n in old if n not in new]
    for n in added:
        lines.append(f"phase added: {n} (live position {new.index(n) + 1})")
    for n in removed:
        lines.append(f"phase removed: {n} (committed position {old.index(n) + 1})")
    common_old = [n for n in old if n in new]
    common_new = [n for n in new if n in old]
    if common_old != common_new:
        for i, (a, b) in enumerate(zip(common_old, common_new), start=1):
            if a != b:
                lines.append(f"phase reordered: shared position {i} was {a}, is now {b}")
                break
    flat_old = _flatten(_strip_lines(committed))
    flat_new = _flatten(_strip_lines(live))
    for key in sorted(set(flat_old) | set(flat_new)):
        if flat_old.get(key) != flat_new.get(key) and not key.startswith("pipeline.run_phase_calls"):
            lines.append(f"changed {key}: {flat_old.get(key)!r} -> {flat_new.get(key)!r}")
    if not lines and _strip_lines(committed) != _strip_lines(live):
        lines.append("reports differ in per-call details (flag, dispatch or context) with the same phase order")
        flat_calls_old = _flatten(_strip_lines(committed.get("pipeline", {}).get("run_phase_calls", [])))
        flat_calls_new = _flatten(_strip_lines(live.get("pipeline", {}).get("run_phase_calls", [])))
        for key in sorted(set(flat_calls_old) | set(flat_calls_new)):
            if flat_calls_old.get(key) != flat_calls_new.get(key):
                lines.append(f"changed run_phase_calls{key}: {flat_calls_old.get(key)!r} -> {flat_calls_new.get(key)!r}")
    return lines


def check_against(path: Path, live: Dict[str, Any]) -> "tuple[int, List[str]]":
    try:
        committed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return 2, [f"cannot read committed report {path}: {exc}"]
    diff = diff_reports(committed, live)
    return (1 if diff else 0), diff


# --------------------------------------------------------------------------- CLI

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--check", metavar="COMMITTED_JSON", help="exit 0 if the live inventory equals this report, else 1")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to read (default: this checkout)")
    parser.add_argument("--source-commit", default=None, help="commit id for the markdown header (default: git HEAD)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = build_report(root)

    if args.check:
        code, diff = check_against(Path(args.check), report)
        if code == 0:
            print("phase inventory matches the committed report (source line numbers ignored)")
        else:
            print("phase inventory differs from the committed report:", file=sys.stderr)
            for line in diff:
                print(f"  {line}", file=sys.stderr)
        return code

    if args.format == "json":
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(to_markdown(report, args.source_commit or git_head(root)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
