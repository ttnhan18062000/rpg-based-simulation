#!/usr/bin/env python3
"""Re-runnable inventory of every wall-clock and host-resource read in ``src/`` (PERF-D1 evidence).

Scans ``src/`` with ``ast`` -- engine code is never imported or executed -- for calls to clocks,
CPU-time and memory counters, host topology and load sources, entropy sources, and reads of the process
environment. For each read it records: file, line, enclosing function, source, source kind, the guard
expressions around it as written in source (inside the enclosing function only), and whether the module is
reachable from ``src/engine/kernel.py`` through the import graph (module-level or function-level imports,
an over-approximation of "can run inside a tick"). Imports and aliases are resolved by name, the same way
``tools/perf/hash_callsite_inventory.py`` resolves them; a call whose method name matches a source but
whose receiver cannot be resolved by name is listed as unresolved instead of being guessed.

Evidence only: nothing here measures anything, runs the kernel, changes a read, or edits a document. Output
has no timestamps, so two runs on one tree are byte-identical.

    python3 tools/perf/wall_clock_inventory.py --format json
    python3 tools/perf/wall_clock_inventory.py --format md
    python3 tools/perf/wall_clock_inventory.py --check docs/performance/wall_clock_inventory.json
    python3 tools/perf/wall_clock_inventory.py --update-doc docs/performance/wall_clock_inventory.md

Ticket: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # allow `python3 tools/perf/wall_clock_inventory.py`
    sys.path.insert(0, str(REPO_ROOT))

from tools.perf.hash_callsite_inventory import (  # noqa: E402  (shared ast and scope helpers)
    _dfs,
    _enclosing_function,
    _guards,
    _import_aliases,
    _parent_map,
    _unparse,
)

SRC_ROOT = "src"
TICK_ROOT_MODULE = "src.engine.kernel"

WALL = "wall-clock"
CPU = "CPU time"
MEM = "memory"
HOST = "CPU/host topology"
ENV = "environment"
ENTROPY = "entropy"

# canonical dotted name -> source kind
SOURCES: Dict[str, str] = {
    "time.time": WALL, "time.time_ns": WALL,
    "time.perf_counter": WALL, "time.perf_counter_ns": WALL,
    "time.monotonic": WALL, "time.monotonic_ns": WALL,
    "time.process_time": CPU, "time.process_time_ns": CPU,
    "time.thread_time": CPU, "time.thread_time_ns": CPU,
    "datetime.datetime.now": WALL, "datetime.datetime.utcnow": WALL, "datetime.datetime.today": WALL,
    "datetime.date.today": WALL,
    "os.getloadavg": HOST, "os.cpu_count": HOST, "os.sched_getaffinity": HOST,
    "resource.getrusage": CPU,
    "tracemalloc.get_traced_memory": MEM,
    "gc.get_count": MEM, "gc.get_stats": MEM,
    # beyond the ticket's minimum list: sources of host entropy, which can reach ids and seeds
    "os.urandom": ENTROPY, "uuid.uuid1": ENTROPY, "uuid.uuid4": ENTROPY,
    "random.SystemRandom": ENTROPY, "random.seed": ENTROPY,
}
ENTROPY_NOTE = "beyond the ticket's minimum list; listed because host entropy can reach ids and seeds"

# method names that make a call a candidate when its receiver cannot be resolved
CANDIDATE_METHODS: Set[str] = {
    "now", "utcnow", "today", "time", "time_ns", "perf_counter", "perf_counter_ns", "monotonic",
    "monotonic_ns", "process_time", "process_time_ns", "thread_time", "thread_time_ns", "getloadavg",
    "cpu_count", "sched_getaffinity", "getrusage", "get_traced_memory", "get_count", "get_stats",
}

_MEMORY_WORDS = ("mem", "swap", "rss")
_HOST_WORDS = ("cpu", "load", "boot", "sensors", "disk", "net")


def psutil_kind(name: str) -> str:
    low = name.lower()
    if any(w in low for w in _MEMORY_WORDS):
        return MEM
    if "cpu_times" in low or low in ("cpu_percent", "num_ctx_switches"):
        return CPU
    return HOST


# --------------------------------------------------------------------------- name resolution

def _dotted(expr: ast.AST) -> Optional[str]:
    """``a.b.c`` for a pure Name/Attribute chain, else None."""
    parts: List[str] = []
    cur = expr
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _canonical(expr: ast.AST, aliases: Dict[str, str]) -> Optional[str]:
    """Resolve the first segment of a dotted expression through the module's imports."""
    text = _dotted(expr)
    if text is None:
        return None
    head, _, rest = text.partition(".")
    if head in aliases:
        return aliases[head] + ("." + rest if rest else "")
    return text


def _psutil_instances(tree: ast.AST, aliases: Dict[str, str]) -> Dict[str, str]:
    """``x = psutil.Process(...)`` / ``self._p = psutil.Process(...)`` -> {target text: "psutil.Process"}."""
    found: Dict[str, str] = {}
    for node in _dfs(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            canon = _canonical(node.value.func, aliases)
            if canon and canon.startswith("psutil.") and canon.split(".")[1][:1].isupper():
                for t in node.targets:
                    found[_unparse(t)] = canon
    return found


def _is_environ(expr: ast.AST, aliases: Dict[str, str]) -> bool:
    return _canonical(expr, aliases) == "os.environ"


def _first_const(call: ast.Call) -> Optional[str]:
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        return call.args[0].value
    return None


# --------------------------------------------------------------------------- scanning one module

_PREFILTER = (
    "time", "datetime", "getloadavg", "cpu_count", "sched_getaffinity", "getrusage", "tracemalloc",
    "gc.", "psutil", "environ", "getenv", "urandom", "uuid", "random", "perf_counter", "monotonic",
)


def _read(node: ast.AST, parents: Dict[ast.AST, ast.AST], rel: str, source: str, kind: str, call: str,
          resolved: bool, env_name: Optional[str] = None, note: str = "") -> Dict[str, Any]:
    guards = _guards(node, parents)
    return {
        "file": rel,
        "line": node.lineno,  # type: ignore[attr-defined]
        "enclosing_function": _enclosing_function(node, parents),
        "source": source,
        "kind": kind,
        "call": call,
        "env_var": env_name,
        "receiver_resolved_by_name": resolved,
        "guards": guards,
        "guarded": bool(guards),
        "note": note,
    }


def scan_source(source_text: str, rel: str) -> Dict[str, List[Dict[str, Any]]]:
    """Reads and unresolved candidates found in one module's source text."""
    if not any(token in source_text for token in _PREFILTER):
        return {"reads": [], "unresolved_candidates": []}
    tree = ast.parse(source_text)
    parents = _parent_map(tree)
    aliases = _import_aliases(tree)
    psutil_instances = _psutil_instances(tree, aliases)

    reads: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []
    counted_attrs: Set[int] = set()  # id() of Attribute nodes already reported as part of a call

    for node in _dfs(tree):
        if isinstance(node, ast.Call):
            func = node.func
            canon = _canonical(func, aliases)
            call_text = _unparse(func)
            # environment: os.getenv(...) and os.environ.get(...)/os.environ.setdefault is a read of a key
            if canon == "os.getenv":
                reads.append(_read(node, parents, rel, "os.getenv", ENV, call_text, True, _first_const(node)))
                continue
            if isinstance(func, ast.Attribute) and _is_environ(func.value, aliases) and func.attr in ("get", "pop", "setdefault"):
                counted_attrs.add(id(func.value))
                reads.append(_read(node, parents, rel, f"os.environ.{func.attr}", ENV, call_text, True, _first_const(node)))
                continue
            if canon in SOURCES:
                kind = SOURCES[canon]
                reads.append(_read(node, parents, rel, canon, kind, call_text, True,
                                   note=ENTROPY_NOTE if kind == ENTROPY else ""))
                continue
            if canon and canon.startswith("psutil."):
                name = canon.split(".", 1)[1]
                reads.append(_read(node, parents, rel, canon, psutil_kind(name), call_text, True))
                continue
            if isinstance(func, ast.Attribute):
                receiver_text = _unparse(func.value)
                if receiver_text in psutil_instances:
                    reads.append(_read(node, parents, rel, f"psutil.Process.{func.attr}", psutil_kind(func.attr),
                                       call_text, True))
                    continue
                if func.attr in CANDIDATE_METHODS and canon not in SOURCES:
                    unresolved.append({
                        "file": rel,
                        "line": node.lineno,
                        "enclosing_function": _enclosing_function(node, parents),
                        "call": call_text,
                        "reason": "method name matches a clock or host source but the receiver is not a known module by name",
                    })
        elif isinstance(node, ast.Subscript) and _is_environ(node.value, aliases):
            counted_attrs.add(id(node.value))
            key = node.slice.value if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str) else None
            reads.append(_read(node, parents, rel, "os.environ[...]", ENV, _unparse(node), True, key))

    # any other use of os.environ (iteration, `in`, passing it on) is a read of the whole environment
    for node in _dfs(tree):
        if isinstance(node, (ast.Attribute, ast.Name)) and _is_environ(node, aliases) and id(node) not in counted_attrs:
            parent = parents.get(node)
            if isinstance(parent, ast.Attribute) and parent.value is node and _canonical(parent, aliases) != "os.environ":
                continue  # os.environ.<method> already handled above (or an unrelated attribute)
            if isinstance(parent, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name) and not isinstance(parent, (ast.Compare, ast.Call, ast.Assign, ast.For, ast.comprehension, ast.Return, ast.keyword, ast.Dict)):
                continue
            if isinstance(node, ast.Attribute) and isinstance(parent, ast.Attribute):
                continue
            if isinstance(parent, ast.Subscript) and parent.value is node:
                continue
            reads.append(_read(node, parents, rel, "os.environ (whole mapping)", ENV, _unparse(parent or node), True, None))
    return {"reads": reads, "unresolved_candidates": unresolved}


# --------------------------------------------------------------------------- import-graph reachability

def _module_name(rel: str) -> str:
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imports_of(tree: ast.AST, this_module: str, known: Set[str]) -> Set[str]:
    out: Set[str] = set()
    package = this_module.rsplit(".", 1)[0] if "." in this_module else this_module
    for node in _dfs(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in known:
                    out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = this_module.split(".")[: -node.level] if this_module.split(".") else []
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            if base in known:
                out.add(base)
            for a in node.names:
                sub = f"{base}.{a.name}"
                if sub in known:
                    out.add(sub)
    return out


def tick_reachable_modules(trees: Dict[str, ast.AST]) -> Set[str]:
    """Modules transitively imported from the kernel module (package ``__init__`` modules included)."""
    known = set(trees)
    graph = {mod: _imports_of(tree, mod, known) for mod, tree in trees.items()}
    seen: Set[str] = set()
    stack = [TICK_ROOT_MODULE] if TICK_ROOT_MODULE in known else []
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        stack.extend(graph.get(mod, ()))
        # importing a.b.c also runs a/__init__ and a.b/__init__
        parts = mod.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent in known:
                stack.append(parent)
    return seen


# --------------------------------------------------------------------------- the whole scan

def build_report(root: Path) -> Dict[str, Any]:
    reads: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []
    unparsed: List[str] = []
    trees: Dict[str, ast.AST] = {}
    sources: Dict[str, str] = {}
    for path in sorted((root / SRC_ROOT).rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except (OSError, UnicodeDecodeError, SyntaxError):
            unparsed.append(rel)
            continue
        trees[_module_name(rel)] = tree
        sources[rel] = text

    reachable = tick_reachable_modules(trees)
    for rel, text in sorted(sources.items()):
        found = scan_source(text, rel)
        in_tick = _module_name(rel) in reachable
        for r in found["reads"]:
            r["reachable_from_kernel"] = in_tick
        reads += found["reads"]
        for u in found["unresolved_candidates"]:
            u["reachable_from_kernel"] = in_tick
        unresolved += found["unresolved_candidates"]

    reads.sort(key=lambda r: (r["file"], r["line"], r["source"]))
    for i, r in enumerate(reads, start=1):
        r["ordinal"] = i
    return {
        "tool": "tools/perf/wall_clock_inventory.py",
        "ticket": "TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY",
        "scanned": {"source_root": SRC_ROOT, "unparsed_files": sorted(unparsed), "kernel_module": TICK_ROOT_MODULE,
                    "modules_reachable_from_kernel": len(reachable)},
        "reads": reads,
        "unresolved_candidates": sorted(unresolved, key=lambda u: (u["file"], u["line"], u["call"])),
    }


def to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- markdown (generated block)

BEGIN_MARK = "<!-- BEGIN GENERATED: tools/perf/wall_clock_inventory.py -->"
END_MARK = "<!-- END GENERATED -->"


def _cell(value: Any) -> str:
    text = "-" if value in (None, "", []) else str(value)
    return text.replace("|", "\\|")


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def to_markdown_block(report: Dict[str, Any], source_commit: str) -> str:
    reads = report["reads"]
    tick = [r for r in reads if r["reachable_from_kernel"]]
    outside = [r for r in reads if not r["reachable_from_kernel"]]
    out: List[str] = [
        BEGIN_MARK,
        "",
        f"Generated from commit `{source_commit}` by `tools/perf/wall_clock_inventory.py`. Regenerate this block with:",
        "",
        "```",
        "python3 tools/perf/wall_clock_inventory.py --update-doc docs/performance/wall_clock_inventory.md",
        "python3 tools/perf/wall_clock_inventory.py --format json > docs/performance/wall_clock_inventory.json",
        "python3 tools/perf/wall_clock_inventory.py --check docs/performance/wall_clock_inventory.json",
        "```",
        "",
        f"Reads found: {len(reads)} ({len(tick)} in modules reachable from `{report['scanned']['kernel_module']}` "
        f"through the import graph, {len(outside)} elsewhere). Modules reachable from the kernel: "
        f"{report['scanned']['modules_reachable_from_kernel']}.",
        "",
        "### G1. Reads in modules reachable from the kernel (guards are the conditions inside the enclosing function, as written)",
        "",
        "| # | File | Line | Enclosing function | Source | Kind | Env var | Guards in the function |",
        "|---|---|---|---|---|---|---|---|",
    ]

    def row(r: Dict[str, Any]) -> str:
        guards = "; ".join(r["guards"]) if r["guards"] else "none in this function"
        return (f"| {r['ordinal']} | `{r['file']}` | {r['line']} | `{r['enclosing_function']}` | {r['source']} | "
                f"{r['kind']} | {_cell(r['env_var'])} | {_cell(guards)} |")

    out += [row(r) for r in tick]
    out += ["", "### G2. Reads in modules not reachable from the kernel", "",
            "| # | File | Line | Enclosing function | Source | Kind | Env var | Guards in the function |",
            "|---|---|---|---|---|---|---|---|"]
    out += [row(r) for r in outside]
    by_kind: Dict[str, int] = {}
    for r in reads:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    out += ["", "### G3. Counts by kind", "", "| Kind | Reads |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(by_kind.items())]
    out += ["", "### G4. Calls whose receiver the scanner could not resolve by name", ""]
    if report["unresolved_candidates"]:
        out += ["| File | Line | Enclosing function | Call | Reachable from kernel |", "|---|---|---|---|---|"]
        for u in report["unresolved_candidates"]:
            out.append(f"| `{u['file']}` | {u['line']} | `{u['enclosing_function']}` | `{u['call']}` | "
                       f"{'yes' if u['reachable_from_kernel'] else 'no'} |")
    else:
        out.append("None.")
    out += ["", END_MARK]
    return "\n".join(out)


def update_doc(doc_path: Path, block: str) -> None:
    text = doc_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN_MARK) + r".*?" + re.escape(END_MARK), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{doc_path}: no generated-block markers found ({BEGIN_MARK} ... {END_MARK})")
    doc_path.write_text(pattern.sub(lambda _m: block, text, count=1), encoding="utf-8")


# --------------------------------------------------------------------------- --check

def _read_keys(report: Dict[str, Any]) -> List[str]:
    """Identity of a read ignoring line numbers; repeats of the same identity are numbered."""
    seen: Dict[Tuple[str, str, str, str, str], int] = {}
    keys: List[str] = []
    for r in report.get("reads", []):
        base = (r["file"], r["enclosing_function"], r["source"], str(r.get("env_var") or ""), " & ".join(r.get("guards", [])))
        seen[base] = seen.get(base, 0) + 1
        keys.append(f"{base[0]} :: {base[1]} :: {base[2]} :: env[{base[3] or '-'}] :: guards[{base[4] or 'none'}] #{seen[base]}")
    return keys


def diff_reports(committed: Dict[str, Any], live: Dict[str, Any]) -> List[str]:
    old, new = _read_keys(committed), _read_keys(live)
    lines = [f"read added: {k}" for k in new if k not in old]
    lines += [f"read removed: {k}" for k in old if k not in new]
    a = {json.dumps({k: v for k, v in x.items() if k != "line"}, sort_keys=True) for x in committed.get("unresolved_candidates", [])}
    b = {json.dumps({k: v for k, v in x.items() if k != "line"}, sort_keys=True) for x in live.get("unresolved_candidates", [])}
    lines += [f"unresolved_candidates added: {x}" for x in sorted(b - a)]
    lines += [f"unresolved_candidates removed: {x}" for x in sorted(a - b)]
    return lines


def check_against(path: Path, live: Dict[str, Any]) -> Tuple[int, List[str]]:
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
    parser.add_argument("--check", metavar="COMMITTED_JSON", help="exit 0 if reads equal this report, 1 if they differ, 2 if unreadable")
    parser.add_argument("--update-doc", metavar="DOC_MD", help="rewrite the generated block of this document in place")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to scan (default: this checkout)")
    parser.add_argument("--source-commit", default=None, help="commit id for the markdown header (default: git HEAD)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = build_report(root)

    if args.check:
        code, diff = check_against(Path(args.check), report)
        if code == 0:
            print("wall-clock reads match the committed report (line numbers ignored)")
        else:
            print("wall-clock reads differ from the committed report:", file=sys.stderr)
            for line in diff:
                print(f"  {line}", file=sys.stderr)
        return code

    commit = args.source_commit or git_head(root)
    if args.update_doc:
        update_doc(Path(args.update_doc), to_markdown_block(report, commit))
        return 0
    if args.format == "json":
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(to_markdown_block(report, commit) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
