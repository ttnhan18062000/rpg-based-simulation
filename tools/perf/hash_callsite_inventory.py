#!/usr/bin/env python3
"""Re-runnable inventory of every state-hash and fingerprint call site in ``src/`` (PA-03A, call-site half).

Scans ``src/`` with ``ast`` -- engine code is never imported or executed -- for calls to the
mechanisms that digest authoritative state, and records for each: file, line, enclosing function,
mechanism, and the guard expressions around it as written in source. It also lists the functions
in ``src/engine/checkpoint.py`` / ``src/replay/fingerprint.py`` / ``AuthoritativeState`` that
produce a digest, direct ``hashlib`` digests of canonical state data, and the references made
from ``tests/``.

Evidence only: nothing here measures cost, runs the kernel, changes a schedule, or edits a document.
Output has no timestamps, so two runs on one tree are byte-identical.

    python3 tools/perf/hash_callsite_inventory.py --format json
    python3 tools/perf/hash_callsite_inventory.py --format md
    python3 tools/perf/hash_callsite_inventory.py --check docs/performance/hash_callsite_inventory.json
    python3 tools/perf/hash_callsite_inventory.py --update-doc docs/performance/hash_callsite_inventory.md

Ticket: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

SRC_ROOT = "src"
TEST_ROOT = "tests"

# class name -> {method name -> mechanism label}
MECHANISM_CLASSES: Dict[str, Dict[str, str]] = {
    "CanonicalStateHasher": {"get_hash": "CanonicalStateHasher.get_hash"},
    "BudgetedCanonicalHasher": {"get_hash": "BudgetedCanonicalHasher.get_hash"},
    "CanonicalHashScheduler": {"compute_hash": "CanonicalHashScheduler.compute_hash"},
    "StateFingerprinter": {"get_fingerprint": "StateFingerprinter.get_fingerprint"},
}
FINGERPRINT_MECHANISM = "AuthoritativeState.fingerprint"
DIRECT_DIGEST_MECHANISM = "hashlib digest of canonical state data"

# What each mechanism produces, stated once so the report does not repeat it per call site.
SCHEMES: Dict[str, str] = {
    "CanonicalStateHasher.get_hash": "flat SHA-256 over compact canonical JSON of the whole state",
    "BudgetedCanonicalHasher.get_hash": "same flat SHA-256, rate limited; returns a stale value when over budget",
    "CanonicalHashScheduler.compute_hash": "FULL: same flat SHA-256 at a sanctioned boundary; LIGHT: MD5 of tick/seed/entity and region counts",
    "StateFingerprinter.get_fingerprint": "dict whose 'state_hash' is an MD5 over a hand-built string of selected state domains",
    FINGERPRINT_MECHANISM: "delegates to StateFingerprinter.get_fingerprint (same dict, MD5 state_hash)",
    DIRECT_DIGEST_MECHANISM: "hashlib digest computed by the caller itself, not through CanonicalStateHasher.get_hash",
}

PRODUCER_MODULES = ("src/engine/checkpoint.py", "src/replay/fingerprint.py")

_GUARD_NODES = (ast.If, ast.While)


# --------------------------------------------------------------------------- ast helpers

def _children(node: ast.AST) -> List[ast.AST]:
    return list(ast.iter_child_nodes(node))


def _dfs(node: ast.AST):
    yield node
    for child in _children(node):
        yield from _dfs(child)


def _parent_map(root: ast.AST) -> Dict[ast.AST, ast.AST]:
    parents: Dict[ast.AST, ast.AST] = {}
    for node in _dfs(root):
        for child in _children(node):
            parents[child] = node
    return parents


def _unparse(node: ast.AST) -> str:
    return ast.unparse(node)


def _in(node: ast.AST, container: List[ast.AST]) -> bool:
    return any(node is c or any(node is d for d in _dfs(c)) for c in container)


# --------------------------------------------------------------------------- name resolution

def _import_aliases(tree: ast.AST) -> Dict[str, str]:
    """local name -> imported dotted name, from every import in the module (any scope)."""
    aliases: Dict[str, str] = {}
    for node in _dfs(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
        elif isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
    return aliases


def _class_of_name(name: str, aliases: Dict[str, str]) -> Optional[str]:
    """The known mechanism class a bare name refers to (directly or through an import alias)."""
    target = aliases.get(name, name)
    leaf = target.split(".")[-1]
    return leaf if leaf in MECHANISM_CLASSES else None


def _resolve_class(expr: ast.AST, aliases: Dict[str, str], instances: Dict[str, str]) -> Optional[str]:
    """Resolve a call receiver to a known mechanism class by name, never by type inference."""
    if isinstance(expr, ast.Name):
        return _class_of_name(expr.id, aliases) or instances.get(expr.id)
    if isinstance(expr, ast.Attribute):
        text = _unparse(expr)
        if text in instances:
            return instances[text]
        # module.alias.Class form: the final attribute names the class.
        if expr.attr in MECHANISM_CLASSES:
            return expr.attr
        return None
    if isinstance(expr, ast.Call):  # ClassName(...).method(...)
        return _resolve_class(expr.func, aliases, instances)
    return None


def _instance_assignments(tree: ast.AST, aliases: Dict[str, str]) -> Dict[str, str]:
    """``x = KnownClass(...)`` / ``self._x = KnownClass(...)`` -> {target text: class}."""
    found: Dict[str, str] = {}
    for node in _dfs(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            cls = _resolve_class(node.value.func, aliases, {})
            if cls:
                for t in node.targets:
                    found[_unparse(t)] = cls
    return found


# --------------------------------------------------------------------------- scope and guards

def _enclosing_function(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> str:
    names: List[str] = []
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(cur.name)
        cur = parents.get(cur)
    names.reverse()
    return ".".join(names) if names else "<module>"


def _guards(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> List[str]:
    """Conditions that control whether ``node`` runs, innermost first, as written in source.

    Stops at the enclosing function boundary: a guard in a caller is not visible here and is
    reported by hand in the document, not guessed by the scanner.
    """
    guards: List[str] = []
    child: ast.AST = node
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            break
        if isinstance(cur, ast.If):
            if _in(child, cur.body):
                guards.append(f"if {_unparse(cur.test)}")
            elif _in(child, cur.orelse):
                guards.append(f"else of: if {_unparse(cur.test)}")
        elif isinstance(cur, ast.While) and _in(child, cur.body):
            guards.append(f"while {_unparse(cur.test)}")
        elif isinstance(cur, ast.IfExp):
            if child is cur.body:
                guards.append(f"if {_unparse(cur.test)} (conditional expression)")
            elif child is cur.orelse:
                guards.append(f"else of: {_unparse(cur.test)} (conditional expression)")
        elif isinstance(cur, ast.BoolOp):
            idx = next((i for i, v in enumerate(cur.values) if child is v), None)
            if idx:
                joiner = " and " if isinstance(cur.op, ast.And) else " or "
                guards.append(f"{'after: ' if isinstance(cur.op, ast.And) else 'unless: '}{joiner.join(_unparse(v) for v in cur.values[:idx])}")
        elif isinstance(cur, ast.Try) and _in(child, cur.body):
            guards.append("try")
        child = cur
        cur = parents.get(cur)
    return guards


# --------------------------------------------------------------------------- scanning one module

# A module can contain a hash call, an unresolved candidate or a direct digest only if its text has one
# of these substrings, so everything else is skipped without parsing (a superset test, never a miss).
_PREFILTER = ("get_hash", "compute_hash", "get_fingerprint", "fingerprint", "to_canonical_data", "to_canonical_json")


def scan_source(source: str, rel_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Call sites, unresolved candidates and direct digests found in one module's source text."""
    if not any(token in source for token in _PREFILTER):
        return {"call_sites": [], "unresolved_candidates": []}
    tree = ast.parse(source)
    parents = _parent_map(tree)
    aliases = _import_aliases(tree)
    instances = _instance_assignments(tree, aliases)

    sites: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []
    method_names = {m for methods in MECHANISM_CLASSES.values() for m in methods}

    for node in _dfs(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        receiver = node.func.value
        if method == "fingerprint" and not node.args and not node.keywords:
            sites.append(_site(node, parents, rel_path, FINGERPRINT_MECHANISM, receiver, resolved=False))
            continue
        if method not in method_names:
            continue
        cls = _resolve_class(receiver, aliases, instances)
        if cls and method in MECHANISM_CLASSES[cls]:
            sites.append(_site(node, parents, rel_path, MECHANISM_CLASSES[cls][method], receiver, resolved=True))
        else:
            unresolved.append({
                "file": rel_path,
                "line": node.lineno,
                "enclosing_function": _enclosing_function(node, parents),
                "call": _unparse(node.func),
                "reason": "method name matches a hash mechanism but the receiver is not a known class by name",
            })

    # Direct digests: a function that serialises canonical state data and digests it itself.
    for fn in (n for n in _dfs(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        calls = [n for n in _dfs(fn) if isinstance(n, ast.Call)]
        serialises = any(
            isinstance(c.func, ast.Attribute) and c.func.attr in ("to_canonical_data", "to_canonical_json")
            for c in calls
        )
        if not serialises:
            continue
        if _qualified(fn, parents) == "CanonicalStateHasher.get_hash":
            continue  # the mechanism's own implementation, not a caller bypassing it
        for c in calls:
            if (
                isinstance(c.func, ast.Attribute)
                and isinstance(c.func.value, ast.Name)
                and c.func.value.id == "hashlib"
                and c.func.attr in ("sha256", "md5", "sha1", "sha512", "blake2b")
            ):
                site = _site(c, parents, rel_path, DIRECT_DIGEST_MECHANISM, c.func.value, resolved=True)
                site["call"] = f"hashlib.{c.func.attr}"
                sites.append(site)
    return {"call_sites": sites, "unresolved_candidates": unresolved}


def _site(node: ast.Call, parents: Dict[ast.AST, ast.AST], rel_path: str, mechanism: str,
          receiver: ast.AST, resolved: bool) -> Dict[str, Any]:
    guards = _guards(node, parents)
    enclosing = _enclosing_function(node, parents)
    delegation = rel_path in PRODUCER_MODULES or enclosing == "AuthoritativeState.fingerprint"
    return {
        "kind": "delegation inside a mechanism" if delegation else "caller",
        "file": rel_path,
        "line": node.lineno,
        "enclosing_function": enclosing,
        "mechanism": mechanism,
        "call": _unparse(node.func),
        "receiver_resolved_by_name": resolved,
        "guards": guards,
        "guarded": bool(guards),
    }


def scan_digest_producers(source: str, rel_path: str) -> List[Dict[str, Any]]:
    """Functions in a producer module that compute a digest or delegate to a mechanism."""
    tree = ast.parse(source)
    parents = _parent_map(tree)
    producers: List[Dict[str, Any]] = []
    for fn in (n for n in _dfs(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        algos: List[str] = []
        delegates: List[str] = []
        for c in (n for n in _dfs(fn) if isinstance(n, ast.Call)):
            if isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Name) and c.func.value.id == "hashlib":
                if c.func.attr not in algos:
                    algos.append(c.func.attr)
            elif isinstance(c.func, ast.Attribute):
                cls = c.func.value.id if isinstance(c.func.value, ast.Name) else None
                if cls in MECHANISM_CLASSES and c.func.attr in MECHANISM_CLASSES[cls]:
                    label = MECHANISM_CLASSES[cls][c.func.attr]
                    if label not in delegates:
                        delegates.append(label)
        if algos or delegates:
            producers.append({
                "file": rel_path,
                "line": fn.lineno,
                "function": _qualified(fn, parents),
                "hashlib_algorithms": algos,
                "delegates_to": delegates,
            })
    return producers


def _qualified(fn: ast.AST, parents: Dict[ast.AST, ast.AST]) -> str:
    names = [fn.name]  # type: ignore[attr-defined]
    cur = parents.get(fn)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(cur.name)
        cur = parents.get(cur)
    return ".".join(reversed(names))


def scan_test_references(source: str, rel_path: str) -> List[Dict[str, Any]]:
    """Calls to the same mechanisms made from a test module (consumers, listed separately)."""
    found = scan_source(source, rel_path)
    return [
        {"file": s["file"], "line": s["line"], "mechanism": s["mechanism"], "enclosing_function": s["enclosing_function"]}
        for s in found["call_sites"]
    ]


# --------------------------------------------------------------------------- whole-tree report

def _python_files(root: Path, sub: str) -> List[Path]:
    base = root / sub
    return sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts) if base.is_dir() else []


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def build_report(root: Path = REPO_ROOT) -> Dict[str, Any]:
    call_sites: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []
    unparsed: List[str] = []
    for path in _python_files(root, SRC_ROOT):
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        if text is None:
            unparsed.append(rel)
            continue
        try:
            found = scan_source(text, rel)
        except SyntaxError:
            unparsed.append(rel)
            continue
        call_sites += found["call_sites"]
        unresolved += found["unresolved_candidates"]

    # The mechanism definitions themselves are not call sites of anything outside their own class.
    producers: List[Dict[str, Any]] = []
    for rel in PRODUCER_MODULES:
        text = _read(root / rel)
        if text is not None:
            producers += scan_digest_producers(text, rel)
    state_text = _read(root / "src/core/state.py")
    if state_text is not None:
        tree = ast.parse(state_text)
        parents = _parent_map(tree)
        for fn in (n for n in _dfs(tree) if isinstance(n, ast.FunctionDef) and n.name == "fingerprint"):
            delegates = sorted({
                MECHANISM_CLASSES[c.func.value.id][c.func.attr]
                for c in (n for n in _dfs(fn) if isinstance(n, ast.Call))
                if isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Name)
                and c.func.value.id in MECHANISM_CLASSES and c.func.attr in MECHANISM_CLASSES[c.func.value.id]
            })
            producers.append({
                "file": "src/core/state.py", "line": fn.lineno, "function": _qualified(fn, parents),
                "hashlib_algorithms": [], "delegates_to": delegates,
            })

    tests: List[Dict[str, Any]] = []
    for path in _python_files(root, TEST_ROOT):
        text = _read(path)
        if text is None:
            continue
        try:
            tests += scan_test_references(text, path.relative_to(root).as_posix())
        except SyntaxError:
            continue

    call_sites.sort(key=lambda s: (s["file"], s["line"], s["mechanism"]))
    for i, s in enumerate(call_sites, start=1):
        s["ordinal"] = i
    return {
        "tool": "tools/perf/hash_callsite_inventory.py",
        "ticket": "TCK-20261003-PERF-HASH-CALLSITE-INVENTORY",
        "scanned": {"source_root": SRC_ROOT, "test_root": TEST_ROOT, "unparsed_files": sorted(unparsed)},
        "schemes": SCHEMES,
        "call_sites": call_sites,
        "unresolved_candidates": sorted(unresolved, key=lambda u: (u["file"], u["line"])),
        "digest_producers": sorted(producers, key=lambda p: (p["file"], p["line"])),
        "test_references": sorted(tests, key=lambda t: (t["file"], t["line"], t["mechanism"])),
    }


def to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- markdown (generated block)

BEGIN_MARK = "<!-- BEGIN GENERATED: tools/perf/hash_callsite_inventory.py -->"
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
    out: List[str] = [
        BEGIN_MARK,
        "",
        f"Generated from commit `{source_commit}` by `tools/perf/hash_callsite_inventory.py`. Regenerate this block with:",
        "",
        "```",
        "python3 tools/perf/hash_callsite_inventory.py --update-doc docs/performance/hash_callsite_inventory.md",
        "python3 tools/perf/hash_callsite_inventory.py --format json > docs/performance/hash_callsite_inventory.json",
        "python3 tools/perf/hash_callsite_inventory.py --check docs/performance/hash_callsite_inventory.json",
        "```",
        "",
        "### G1. Call sites in `src/` (static scan; guards are the conditions inside the enclosing function, as written)",
        "",
        "| # | File | Line | Enclosing function | Mechanism | Kind | Guards in the function |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in report["call_sites"]:
        guards = "; ".join(s["guards"]) if s["guards"] else "none in this function"
        out.append(f"| {s['ordinal']} | `{s['file']}` | {s['line']} | `{s['enclosing_function']}` | "
                   f"{s['mechanism']} | {s['kind']} | {_cell(guards)} |")
    out += [
        "",
        "### G2. Functions that produce a digest or delegate to a mechanism",
        "",
        "| File | Line | Function | hashlib algorithms | Delegates to |",
        "|---|---|---|---|---|",
    ]
    for p in report["digest_producers"]:
        out.append(f"| `{p['file']}` | {p['line']} | `{p['function']}` | {_cell(', '.join(p['hashlib_algorithms']))} | "
                   f"{_cell(', '.join(p['delegates_to']))} |")
    out += ["", "### G3. Schemes", "", "| Mechanism | What it produces |", "|---|---|"]
    for k, v in report["schemes"].items():
        out.append(f"| {k} | {_cell(v)} |")
    out += ["", "### G4. Calls whose receiver the scanner could not resolve by name", ""]
    if report["unresolved_candidates"]:
        out += ["| File | Line | Enclosing function | Call |", "|---|---|---|---|"]
        for u in report["unresolved_candidates"]:
            out.append(f"| `{u['file']}` | {u['line']} | `{u['enclosing_function']}` | `{u['call']}` |")
    else:
        out.append("None.")
    by_file: Dict[Tuple[str, str], List[int]] = {}
    for t in report["test_references"]:
        by_file.setdefault((t["file"], t["mechanism"]), []).append(t["line"])
    out += ["", "### G5. References from `tests/` (consumers; lines listed per file and mechanism)", "",
            "| File | Mechanism | Lines |", "|---|---|---|"]
    for (file, mech), lines in sorted(by_file.items()):
        out.append(f"| `{file}` | {mech} | {', '.join(str(n) for n in lines)} |")
    out += ["", END_MARK]
    return "\n".join(out)


def update_doc(doc_path: Path, block: str) -> None:
    text = doc_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN_MARK) + r".*?" + re.escape(END_MARK), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{doc_path}: no generated-block markers found ({BEGIN_MARK} ... {END_MARK})")
    doc_path.write_text(pattern.sub(lambda _m: block, text, count=1), encoding="utf-8")


# --------------------------------------------------------------------------- --check

def _site_keys(report: Dict[str, Any]) -> List[str]:
    """Identity of a call site ignoring line numbers; repeats of the same identity are numbered."""
    seen: Dict[Tuple[str, str, str, str], int] = {}
    keys: List[str] = []
    for s in report.get("call_sites", []):
        base = (s["file"], s["enclosing_function"], s["mechanism"], " & ".join(s.get("guards", [])))
        seen[base] = seen.get(base, 0) + 1
        keys.append(f"{base[0]} :: {base[1]} :: {base[2]} :: guards[{base[3] or 'none'}] #{seen[base]}")
    return keys


def diff_reports(committed: Dict[str, Any], live: Dict[str, Any]) -> List[str]:
    old, new = _site_keys(committed), _site_keys(live)
    lines = [f"call site added: {k}" for k in new if k not in old]
    lines += [f"call site removed: {k}" for k in old if k not in new]
    for name in ("unresolved_candidates", "digest_producers"):
        a = {json.dumps({k: v for k, v in x.items() if k != "line"}, sort_keys=True) for x in committed.get(name, [])}
        b = {json.dumps({k: v for k, v in x.items() if k != "line"}, sort_keys=True) for x in live.get(name, [])}
        lines += [f"{name} added: {x}" for x in sorted(b - a)]
        lines += [f"{name} removed: {x}" for x in sorted(a - b)]
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
    parser.add_argument("--check", metavar="COMMITTED_JSON", help="exit 0 if call sites equal this report, 1 if they differ, 2 if unreadable")
    parser.add_argument("--update-doc", metavar="DOC_MD", help="rewrite the generated block of this document in place")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to scan (default: this checkout)")
    parser.add_argument("--source-commit", default=None, help="commit id for the markdown header (default: git HEAD)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = build_report(root)

    if args.check:
        code, diff = check_against(Path(args.check), report)
        if code == 0:
            print("hash call sites match the committed report (line numbers ignored)")
        else:
            print("hash call sites differ from the committed report:", file=sys.stderr)
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
