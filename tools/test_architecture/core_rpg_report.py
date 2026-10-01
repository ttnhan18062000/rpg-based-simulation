"""Core-RPG test report v0 -- a deterministic, report-only producer.

Reads only what it is given (the repo tree, supplied JUnit XML, a supplied coverage JSON) and writes
versioned JSON plus markdown. It never runs tests or mutation, changes no exit code based on what it
finds, and nothing may use it as a gate (roadmap docs/plans/test_architecture/roadmap.md §3.4, §3.8).

Honest states: missing, skipped, stale, not-in-supplied-runs and uncertain data are reported as such, never as 0
or pass. Every count carries its denominator. The output regenerates byte-identically from the same
inputs: no wall clock (`sha` and `as_of` are inputs), no absolute paths, stable ordering.

Usage:
    python3 tools/test_architecture/core_rpg_report.py --as-of 2026-09-30 \
        [--sha SHA] [--junit run1.xml ...] [--coverage coverage.json] [--repo-root DIR] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import fnmatch
import hashlib
import json
import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import yaml

SCHEMA_VERSION = 2

# ── classification rules (v0 heuristics) ────────────────────────────────────────────────────────
# Directory signal: the planner's directory list, docs/plans/test_architecture/reference/
# current_test_system_overview.md §10.
_CORE_RPG_UNIT_DIRS = (
    "combat", "movement", "progression", "resource", "economy", "quest", "entity", "entities", "tactical",
)
_CORE_RPG_DOMAIN_DIRS = ("combat_engagement", "progression")
_CORE_RPG_INTEGRATION_DIRS = _CORE_RPG_UNIT_DIRS  # integration sub-directories named like the gameplay ones
_CORE_RPG_PREFIXES = (
    "tests/mechanic_scenarios/",
    *(f"tests/unit/{d}/" for d in _CORE_RPG_UNIT_DIRS),
    *(f"tests/unit/domains/{d}/" for d in _CORE_RPG_DOMAIN_DIRS),
    *(f"tests/integration/{d}/" for d in _CORE_RPG_INTEGRATION_DIRS),
)

# Import signals: the component roots of the ownership map, docs/plans/test_architecture/reference/
# architecture_design_notes.md §3.1 -- the single source for these three tuples. A trailing `*` is a
# module-name stem wildcard (`src.systems.crafting*` matches src.systems.crafting and
# src.systems.crafting_x); any other entry matches that module and everything beneath it.
_SUBSTRATE_IMPORT_PREFIXES = (  # "Shared substrate" row: not gameplay, so never a core-RPG signal
    "src.core", "src.engine.pipeline*", "src.engine.kernel*", "src.platform",
)
# Per-domain roots; the `domain` marker values in docs/testing/test_taxonomy.md §10 use these keys.
DOMAIN_IMPORT_PREFIXES = {
    "movement": ("src.engine.movement*",),
    "combat": ("src.engine.combat*", "src.engine.domain.combat_actions", "src.domains.combat_engagement"),
    "progression": ("src.progression", "src.domains.progression", "src.entities"),
    # `src.core.conservation` and `src.core.inventory` sit under the substrate root `src/core/` but ARE the
    # ch03 economic laws (§1 Atomic Conservation; §2 Inventory & Logistics, parity TOWN-011/012 in
    # town_resource.yaml). Evidence: the core-RPG pilot mapped a conservation change to substrate only and
    # recommended no scenario level (docs/testing/core_rpg_test_pilot_2026-09-30.md). They stay substrate
    # too: the impact report names both owners.
    "economy": ("src.systems.economy*", "src.systems.market*", "src.systems.crafting*",
                "src.systems.harvest*", "src.economy", "src.core.conservation*", "src.core.inventory*"),
    "quests_guild": ("src.systems.quest*", "src.systems.guild_system*", "src.quests"),
}
_GAMEPLAY_IMPORT_PREFIXES = tuple(p for prefixes in DOMAIN_IMPORT_PREFIXES.values() for p in prefixes)
_UNOWNED_DOMAIN_IMPORT_PREFIXES = (  # "Party / group" row: no oracle and no owner (decision D-P, deferred)
    "src.systems.party*", "src.systems.social_systems.party*",
)

V0_LIMITS = (
    "Execution data is a supplied input: in CI only the `api-tools` job uploads JUnit, so most lanes have no "
    "JUnit artifact to supply unless a local run produces one.",
    "There is no CI coverage job. Package coverage comes only from a supplied local run (`provisional-local`); "
    "otherwise it shows `no-coverage-artifact`.",
    "Package coverage is not domain coverage. Domain coverage stays `not-derived` until a defensible mapping exists.",
    "Classification is heuristic (directory and import signals). `domain`/`level` markers a file declares are "
    "listed beside its class and never override it; few tests declare them yet. Disagreeing signals stay `uncertain`.",
    "Import signals follow the ownership map in architecture_design_notes.md §3.1; party/group code has no "
    "oracle or owner (decision D-P, deferred), so files that only import it are `unowned-domain`, outside the "
    "core-RPG candidate set.",
    "The manifest hashes the supplied artifacts, the workflow, the tag registry and the mutation records; the "
    "scanned tests/, tickets/ and parity ledger are covered only by the `scanned_inputs_dirty` flag, which needs a git checkout. "
    "That flag covers only those scanned inputs, not the whole repository (renamed from `worktree_dirty` in schema_version 2).",
    "`not-in-supplied-runs` means a candidate file has no testcase in any supplied JUnit run. It does not mean the file "
    "was never executed anywhere; with no run supplied at all the state is `no-junit-artifact`.",
    "Lane triggers and path filters are not derived; the lane layer records which pytest steps list which paths.",
    "Mutation evidence covers one declared target. `mutmut` is not a project dependency, so the run is not "
    "reproducible from a clean install.",
    "Equivalent mutants are not classified (`equivalent: not-classified`); every survivor is unreviewed.",
    "`mutmut` 3.x cannot run in this repo: its trampoline rejects modules whose import path starts with `src.`.",
    "SimQ and census states are fixed read-only states in v0; the parity layer counts ledger statuses and "
    "`test_path` presence (a recorded path, not a passing test) and is not proof.",
    "Escaped defects depend on tagging discipline (`escaped-defect`); history before the tag was registered is not "
    "backfilled. A defect's month is its ticket's creation date, and open tickets (todos/, inprogress/) are counted.",
    "The report never runs tests and is not a gate.",
)


# ── small helpers ───────────────────────────────────────────────────────────────────────────────
def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _pct(covered: int, total: int) -> Optional[float]:
    return round(100 * covered / total, 2) if total else None


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


# ── layer 1: inventory + classification ─────────────────────────────────────────────────────────
def _imports_of(path: Path) -> Optional[List[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None
    found: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append(node.module)
            found.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def _matches(name: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return name.startswith(pattern[:-1])
    return name == pattern or name.startswith(pattern + ".")


def _has_prefix(names: Iterable[str], prefixes: Sequence[str]) -> bool:
    return any(_matches(n, p) for n in names for p in prefixes)


def declared_markers(path: Path) -> Dict[str, List[str]]:
    """`domain(...)` / `level(...)` marker arguments a test file declares (module, class or test level)."""
    out: Dict[str, List[str]] = {"domains": [], "levels": []}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return out
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("domain", "level")):
            continue
        base = node.func.value  # must be `<x>.mark`, i.e. pytest.mark.domain(...)
        if not (isinstance(base, ast.Attribute) and base.attr == "mark"):
            continue
        key = "domains" if node.func.attr == "domain" else "levels"
        out[key].extend(a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str))
    return out


def classify_file(rel_path: str, imports: Optional[List[str]]) -> Dict[str, Any]:
    dir_signal = any(rel_path.startswith(p) for p in _CORE_RPG_PREFIXES)
    if imports is None:
        return {"file": rel_path, "class": "parse-error", "directory_signal": dir_signal,
                "import_signal": None, "substrate_only_import": None}
    import_signal = _has_prefix(imports, _GAMEPLAY_IMPORT_PREFIXES)
    substrate_only = (not import_signal) and _has_prefix(imports, _SUBSTRATE_IMPORT_PREFIXES)
    if dir_signal and import_signal:
        cls = "classified"
    elif dir_signal or import_signal:
        cls = "uncertain"
    elif _has_prefix(imports, _UNOWNED_DOMAIN_IMPORT_PREFIXES):
        cls = "unowned-domain"
    else:
        cls = "not-core-rpg"
    return {"file": rel_path, "class": cls, "directory_signal": dir_signal,
            "import_signal": import_signal, "substrate_only_import": substrate_only}


def scan_tests(repo_root: Path) -> List[Dict[str, Any]]:
    tests_dir = repo_root / "tests"
    files = sorted(p for p in tests_dir.rglob("test_*.py") if "__pycache__" not in p.parts)
    records = []
    for p in files:
        record = classify_file(_rel(p, repo_root), _imports_of(p))
        record.update({f"declared_{k}": v for k, v in declared_markers(p).items()})
        records.append(record)
    return records


def _declared_marker_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Files declaring `domain`/`level` markers, listed by path so a newly marked test is locatable.

    Declared markers are reported next to the heuristic class; they never override it."""
    marked = [r for r in records if r.get("declared_domains") or r.get("declared_levels")]
    return {
        "files": len(marked),
        "by_file": {r["file"]: {"class": r["class"], "domains": sorted(set(r["declared_domains"])),
                                "levels": sorted(set(r["declared_levels"]))} for r in marked},
    }


def classification_layer(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    counts = {k: 0 for k in ("classified", "uncertain", "unowned-domain", "not-core-rpg", "parse-error")}
    for r in records:
        counts[r["class"]] += 1
    directory_only = sum(1 for r in records if r["directory_signal"] and r["import_signal"] is False)
    import_only = sum(1 for r in records if r["import_signal"] and not r["directory_signal"])
    return {
        "state": "heuristic",
        "denominator": {"test_files": total},
        "counts": counts,
        "signal_disagreement": {"directory_only": directory_only, "import_only": import_only},
        "substrate_only_import_files": sum(1 for r in records if r["substrate_only_import"]),
        "declared_markers": _declared_marker_summary(records),
        "rules": {
            "classified": "directory signal and gameplay-import signal both present",
            "uncertain": "exactly one of the two signals present",
            "unowned-domain": "neither signal present, but imports party/group code, which has no oracle or owner",
            "not-core-rpg": "neither signal present",
        },
    }


# ── layer 2: CI lanes ───────────────────────────────────────────────────────────────────────────
def _pytest_commands(run_text: str) -> List[List[str]]:
    joined = re.sub(r"\\\n\s*", " ", run_text)
    commands: List[List[str]] = []
    for line in joined.splitlines():
        if "pytest" not in line or "--collect-only" in line:
            continue
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError:
            continue
        if "pytest" in tokens:
            commands.append(tokens[tokens.index("pytest") + 1:])
    return commands


def parse_lanes(workflow_path: Path) -> List[Dict[str, Any]]:
    if not workflow_path.is_file():
        return []
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
    lanes: List[Dict[str, Any]] = []
    for job_id in sorted((data.get("jobs") or {})):
        job = data["jobs"][job_id] or {}
        steps = job.get("steps") or []
        upload_globs = [
            str(((s.get("with") or {}).get("path")) or "")
            for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact")
        ]
        upload_patterns = [ln.strip() for g in upload_globs for ln in g.splitlines() if ln.strip()]
        for index, step in enumerate(steps):
            run_text = step.get("run")
            if not isinstance(run_text, str):
                continue
            for cmd in _pytest_commands(run_text):
                paths = sorted({t.rstrip("/") for t in cmd if t == "tests" or t.startswith("tests/")})
                if not paths:
                    continue
                marker = next((cmd[i + 1] for i, t in enumerate(cmd[:-1]) if t == "-m"), None)
                junit = next((t.split("=", 1)[1] for t in cmd if t.startswith("--junit-xml=")), None)
                lanes.append({
                    "lane": f"{job_id}/{step.get('name') or f'step-{index}'}",
                    "paths": paths,
                    "marker_filter": marker,
                    "fast": bool(marker and "not slow" in marker),
                    "junit_xml": junit,
                    "junit_uploaded": bool(junit and any(fnmatch.fnmatch(junit, pat) for pat in upload_patterns)),
                })
    return sorted(lanes, key=lambda lane: lane["lane"])


def _lane_covers(lane: Dict[str, Any], rel_path: str) -> bool:
    return any(p == "tests" or rel_path == p or rel_path.startswith(p + "/") for p in lane["paths"])


def lanes_layer(lanes: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    fast = [lane for lane in lanes if lane["fast"]]
    per_file = []
    for rec in candidates:
        covering = sorted(lane["lane"] for lane in fast if _lane_covers(lane, rec["file"]))
        per_file.append({"file": rec["file"], "fast_lanes": covering,
                         "state": "covered" if covering else "no-fast-lane"})
    return {
        "state": "parsed" if lanes else "no-workflow-found",
        "denominator": {"core_rpg_candidate_files": len(candidates), "pytest_lane_steps": len(lanes)},
        "counts": {
            "covered_by_a_fast_lane": sum(1 for f in per_file if f["state"] == "covered"),
            "no_fast_lane": sum(1 for f in per_file if f["state"] == "no-fast-lane"),
            "lane_steps_uploading_junit": sum(1 for lane in lanes if lane["junit_uploaded"]),
        },
        "lane_steps": lanes,
        "files": per_file,
        "not_derived": ["triggers", "path filters"],
    }


# ── layer 3: execution (supplied JUnit) ─────────────────────────────────────────────────────────
def _map_classname(classname: str, name: str, known: set) -> Optional[str]:
    parts = classname.split(".") if classname else []
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i]) + ".py"
        if candidate in known:
            return "::".join([candidate, *parts[i:], name])
    return None


def parse_junit(path: Path, known_files: set) -> Dict[str, Any]:
    digest = _sha256_file(path)
    run_id = f"{path.stem}-{digest[:12]}"
    root = ET.parse(path).getroot()
    per_file: Dict[str, Dict[str, int]] = {}
    outcomes = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    failing: List[str] = []
    unmapped = 0
    for tc in root.iter("testcase"):
        kind = "passed"
        if tc.find("failure") is not None:
            kind = "failed"
        elif tc.find("error") is not None:
            kind = "errors"
        elif tc.find("skipped") is not None:
            kind = "skipped"
        outcomes[kind] += 1
        nodeid = _map_classname(tc.get("classname", ""), tc.get("name", ""), known_files)
        if nodeid is None:
            unmapped += 1
            if kind in ("failed", "errors"):
                failing.append(f"?::{tc.get('classname', '')}::{tc.get('name', '')}")
            continue
        file = nodeid.split("::", 1)[0]
        bucket = per_file.setdefault(file, {"passed": 0, "failed": 0, "errors": 0, "skipped": 0})
        bucket[kind] += 1
        if kind in ("failed", "errors"):
            failing.append(nodeid)
    return {"run_id": run_id, "artifact": path.name, "sha256": digest, "testcases": sum(outcomes.values()),
            "outcomes": outcomes, "unmapped_testcases": unmapped, "per_file": per_file,
            "failing_tests": sorted(failing)}


def _file_state(counts: Dict[str, int]) -> str:
    if counts["failed"] or counts["errors"]:
        return "fail"
    if counts["passed"]:
        return "pass"
    return "skipped"


def execution_layer(runs: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(candidates)
    if not runs:
        return {
            "state": "no-junit-artifact",
            "denominator": {"core_rpg_candidate_files": n},
            "runs": [],
            "files": [{"file": c["file"], "class": c["class"], "state": "no-junit-artifact"} for c in candidates],
            "summary": {},
        }
    runs = sorted(runs, key=lambda r: r["run_id"])
    files = []
    summary: Dict[str, Dict[str, int]] = {
        r["run_id"]: {"pass": 0, "fail": 0, "skipped": 0, "not-in-supplied-runs": 0, "denominator": n} for r in runs
    }
    for c in candidates:
        per_run = {}
        for r in runs:
            counts = r["per_file"].get(c["file"])
            state = _file_state(counts) if counts else "not-in-supplied-runs"
            entry: Dict[str, Any] = {"state": state}
            if counts:
                entry.update(counts)
            per_run[r["run_id"]] = entry
            summary[r["run_id"]][state] += 1
        files.append({"file": c["file"], "class": c["class"], "runs": per_run})
    return {
        "state": "junit-supplied",
        "denominator": {"core_rpg_candidate_files": n},
        "runs": [{k: v for k, v in r.items() if k != "per_file"} for r in runs],
        "files": files,
        "summary": summary,
    }


# ── layer 4: package coverage (supplied coverage JSON) ──────────────────────────────────────────
def coverage_layer(coverage_path: Optional[Path]) -> Dict[str, Any]:
    domain = {"state": "not-derived", "reason": "no defensible package-to-domain mapping yet"}
    if coverage_path is None:
        return {"state": "no-coverage-artifact", "package_coverage": {}, "domain_coverage": domain}
    data = json.loads(coverage_path.read_text(encoding="utf-8"))
    packages: Dict[str, Dict[str, int]] = {}
    for filename, info in (data.get("files") or {}).items():
        norm = filename.replace("\\", "/")
        marker = norm.find("src/")
        if marker < 0:
            continue
        segments = norm[marker + 4:].split("/")
        package = segments[0] if len(segments) > 1 else "(top-level)"
        summary = info.get("summary") or {}
        bucket = packages.setdefault(package, {"num_statements": 0, "covered_lines": 0,
                                               "num_branches": 0, "covered_branches": 0})
        bucket["num_statements"] += int(summary.get("num_statements", 0))
        bucket["covered_lines"] += int(summary.get("covered_lines", 0))
        bucket["num_branches"] += int(summary.get("num_branches", 0))
        bucket["covered_branches"] += int(summary.get("covered_branches", 0))
    rows = {}
    for package in sorted(packages):
        b = packages[package]
        rows[package] = {**b, "line_pct": _pct(b["covered_lines"], b["num_statements"]),
                         "branch_pct": _pct(b["covered_branches"], b["num_branches"])}
    totals = {k: sum(b[k] for b in packages.values())
              for k in ("num_statements", "covered_lines", "num_branches", "covered_branches")}
    return {
        "state": "provisional-local",
        "source": "supplied coverage.py JSON from a local run",
        "denominator": {"statements": totals["num_statements"], "branches": totals["num_branches"]},
        "total_line_pct": _pct(totals["covered_lines"], totals["num_statements"]),
        "package_coverage": rows,
        "domain_coverage": domain,
    }


# ── layer 5-7: parity (read-only), SimQ and census (fixed states) ───────────────────────────────
def parity_layer(repo_root: Path) -> Dict[str, Any]:
    directory = repo_root / "docs" / "parity_ledger"
    if not directory.is_dir():
        return {"state": "no-ledger-found", "denominator": {"entries": 0}, "counts": {}}
    by_status: Dict[str, int] = {}
    per_file: Dict[str, int] = {}
    tp_counts = {"P0": {"with": 0, "without": 0}, "other": {"with": 0, "without": 0}}
    p0_without: Dict[str, List[str]] = {}
    unreadable: List[str] = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            entries = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            unreadable.append(path.name)
            continue
        if not isinstance(entries, list):
            unreadable.append(path.name)
            continue
        per_file[path.name] = len(entries)
        for entry in entries:
            entry = entry or {}
            status = str(entry.get("status", "unknown"))
            by_status[status] = by_status.get(status, 0) + 1
            tp = entry.get("test_path")
            has_tp = isinstance(tp, str) and tp.strip() not in ("", "null", "None")
            bucket = "P0" if entry.get("priority") == "P0" else "other"
            tp_counts[bucket]["with" if has_tp else "without"] += 1
            if bucket == "P0" and not has_tp:
                p0_without.setdefault(path.name, []).append(str(entry.get("id", "?")))
    return {
        "state": "read-only",
        "note": "ledger statuses as recorded; not proof and not re-derived here",
        "denominator": {"entries": sum(per_file.values())},
        "counts": dict(sorted(by_status.items())),
        "entries_per_file": per_file,
        "test_path": {
            "note": "a test_path is a recorded path, not evidence that the test exists or passes",
            "p0": tp_counts["P0"],
            "other_priorities": tp_counts["other"],
            "p0_without_test_path": {name: sorted(ids) for name, ids in sorted(p0_without.items())},
        },
        "unreadable_files": unreadable,
    }


def simq_layer() -> Dict[str, Any]:
    return {"state": "skipped-no-data",
            "reason": "SimQ anchor checks skip when no corpus data is present; v0 reads no corpus"}


def census_layer() -> Dict[str, Any]:
    return {"state": "unstable", "reason": "census reachability is not yet a stable input; v0 reports the state only"}


# ── layer 8: mutation evidence ──────────────────────────────────────────────────────────────────
def mutation_layer(repo_root: Path, as_of: dt.date) -> Dict[str, Any]:
    directory = repo_root / "tests" / "mutation" / "baselines"
    records = sorted(directory.glob("*.json")) if directory.is_dir() else []
    if not records:
        return {"state": "not-run", "records": []}
    rows = []
    declared: Dict[str, Dict[str, Any]] = {}
    for path in records:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            declared[path.name] = {"target": rec["target"]["path"], "supersedes": rec.get("supersedes")}
            rows.append(_mutation_row(path, repo_root, as_of, rec))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rows.append({"record": path.name, "state": "unreadable", "reason": type(exc).__name__})
    _apply_baseline_roles(rows, declared)
    return {"state": "recorded", "records": rows}


def _apply_baseline_roles(rows: List[Dict[str, Any]], declared: Dict[str, Dict[str, Any]]) -> None:
    """Which record applies to a target comes from a declared `supersedes` link, never from file recency.

    A record another record names in `supersedes` is `superseded` (history: no staleness verdict). Of the rest,
    exactly one per target is `current`; more than one unlinked record on a target is `ambiguous-current` and
    is left unjudged rather than guessing by name or date."""
    superseded_by = {d["supersedes"]: name for name, d in declared.items() if d["supersedes"]}
    by_target: Dict[str, List[str]] = {}
    for name, d in declared.items():
        if name not in superseded_by:
            by_target.setdefault(d["target"], []).append(name)
    for row in rows:
        name = row["record"]
        if name not in declared:
            continue
        row["supersedes"] = declared[name]["supersedes"]
        if name in superseded_by:
            row.update({"role": "superseded", "superseded_by": superseded_by[name], "stale_reasons": [],
                        "state": "superseded"})
        elif len(by_target[declared[name]["target"]]) > 1:
            row.update({"role": "ambiguous-current", "state": "ambiguous-current"})
        else:
            row["role"] = "current"


def _selection_changed(rec: Dict[str, Any], repo_root: Path) -> Optional[bool]:
    """True when re-resolving the record's declared selection rule differs from its recorded list hash.

    None when the record declares no machine-resolvable rule (v1 records): no verdict, not "unchanged"."""
    sel = rec.get("selection")
    if not isinstance(sel, dict) or sel.get("rule") != "import-based-one-hop":
        return None
    from tools.test_architecture import mutation_selection

    resolved = mutation_selection.resolve(repo_root, sel["target_module"], sel.get("curated_additions", []))
    return resolved["resolved_files_sha256"] != sel["resolved_files_sha256"]


def _mutation_row(path: Path, repo_root: Path, as_of: dt.date, rec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rec = rec if rec is not None else json.loads(path.read_text(encoding="utf-8"))
    target = repo_root / rec["target"]["path"]
    reasons: List[str] = []
    if _selection_changed(rec, repo_root):
        reasons.append("selection-changed")
    current_sha = _sha256_file(target) if target.is_file() else None
    if current_sha is None:
        reasons.append("target-missing")
    elif current_sha != rec["target"]["sha256"]:
        reasons.append("target-changed")
    started = dt.date.fromisoformat(rec["run"]["started_utc"][:10])
    age_days = (as_of - started).days
    if age_days > int(rec["stale_after"]["days"]):
        reasons.append("older-than-stale-after-days")
    counts = rec["counts"]
    return {
        "record": path.name,
        "baseline_id": rec.get("baseline_id", path.stem),
        "target": rec["target"]["path"],
        "state": "stale" if reasons else "fresh",
        "stale_reasons": reasons,
        "age_days": age_days,
        "run_kind": rec["run"]["kind"],
        "source_sha": rec["run"]["source_sha"],
        "tool": f"{rec['tool']['name']} {rec['tool']['version']}",
        "tests": {"files": len(rec["tests"]["files"]), "count": rec["tests"]["count"]},
        "denominator": {"mutants": counts["total"]},
        "counts": {k: counts[k] for k in ("killed", "survived", "timeout", "suspicious", "equivalent")},
        "survivors_listed": len(rec["survivors"]),
        "material_survivors": sum(1 for s in rec["survivors"] if s.get("material_sample")),
    }


# ── layer 9: escaped defects ────────────────────────────────────────────────────────────────────
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_FAILURE_CLASS = re.compile(r"^Failure class:\s*(.+)$", re.M)


def _month_range(start: dt.date, end: dt.date) -> List[str]:
    months: List[str] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def escaped_defects_layer(repo_root: Path, as_of: dt.date) -> Dict[str, Any]:
    registry = repo_root / "registries" / "tag_registry.jsonl"
    added: Optional[dt.date] = None
    if registry.is_file():
        for line in registry.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                if entry.get("tag") == "escaped-defect":
                    added = dt.date.fromisoformat(entry["added_date"])
    if added is None:
        return {"state": "tag-not-registered", "months": {}, "tickets": []}
    tickets_dir = repo_root / "tickets"
    scanned = 0
    tagged: List[Dict[str, Any]] = []
    for path in sorted(tickets_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        head = _FRONTMATTER.match(text)
        if not head or "ticket_id:" not in head.group(1):
            continue
        scanned += 1
        if "escaped-defect" not in head.group(1):
            continue
        meta = yaml.safe_load(head.group(1)) or {}
        if "escaped-defect" not in (meta.get("tags") or []):
            continue
        fc = _FAILURE_CLASS.search(text)
        tagged.append({"ticket_id": meta.get("ticket_id"), "date": str(meta.get("date")),
                       "failure_class": fc.group(1).strip() if fc else "unrecorded"})
    months = {m: 0 for m in _month_range(added, as_of)}
    outside = 0
    for t in tagged:
        month = t["date"][:7]
        if month in months:
            months[month] += 1
        else:
            outside += 1
    return {
        "state": "counting",
        "tag_registered": added.isoformat(),
        "month_basis": "ticket creation date (frontmatter `date`); all tickets, open and closed (todos/, inprogress/ and done/)",
        "denominator": {"tickets_scanned": scanned},
        "months": months,
        "total_in_window": sum(months.values()),
        "tagged_outside_window": outside,
        "tickets": sorted(tagged, key=lambda t: t["ticket_id"] or ""),
    }


# ── assembly ────────────────────────────────────────────────────────────────────────────────────
def _git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True, timeout=30)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


_SCANNED_PREFIXES = ("tests/", "docs/parity_ledger/", "registries/tag_registry.jsonl", ".github/workflows/test.yml")


def _dirty_inputs(repo_root: Path, target_paths: Sequence[str]) -> Any:
    """Uncommitted changes under the paths the report scans: a list of paths, or "unknown" without git."""
    try:
        out = subprocess.run(["git", "-C", str(repo_root), "status", "--porcelain"], capture_output=True,
                             text=True, check=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    dirty = set()
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        scanned = path.startswith(_SCANNED_PREFIXES) or path in target_paths or (
            path.startswith("tickets/") and path.endswith(".md"))
        if scanned:
            dirty.add(path)
    return sorted(dirty)


def build_report(repo_root: Path, sha: str, as_of: dt.date, junit_paths: Sequence[Path] = (),
                 coverage_path: Optional[Path] = None) -> Dict[str, Any]:
    records = scan_tests(repo_root)
    known = {r["file"] for r in records}
    candidates = [r for r in records if r["class"] in ("classified", "uncertain")]
    workflow = repo_root / ".github" / "workflows" / "test.yml"
    lanes = parse_lanes(workflow)
    runs = [parse_junit(p, known) for p in junit_paths]

    inputs: List[Dict[str, str]] = [{"kind": "junit", "artifact": r["artifact"], "sha256": r["sha256"]} for r in runs]
    if coverage_path is not None:
        inputs.append({"kind": "coverage", "artifact": coverage_path.name, "sha256": _sha256_file(coverage_path)})
    for kind, path in (("workflow", workflow), ("tag-registry", repo_root / "registries" / "tag_registry.jsonl")):
        if path.is_file():
            inputs.append({"kind": kind, "artifact": _rel(path, repo_root), "sha256": _sha256_file(path)})
    baselines = repo_root / "tests" / "mutation" / "baselines"
    for path in sorted(baselines.glob("*.json")) if baselines.is_dir() else []:
        inputs.append({"kind": "mutation-record", "artifact": _rel(path, repo_root), "sha256": _sha256_file(path)})
    inputs.sort(key=lambda i: (i["kind"], i["artifact"], i["sha256"]))
    mutation_targets = []
    for path in sorted(baselines.glob("*.json")) if baselines.is_dir() else []:
        try:
            mutation_targets.append(json.loads(path.read_text(encoding="utf-8"))["target"]["path"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    dirty = _dirty_inputs(repo_root, mutation_targets)

    return {
        "schema_version": SCHEMA_VERSION,
        "report": "core-rpg-test-report-v0",
        "manifest": {"sha": sha, "as_of": as_of.isoformat(), "inputs": inputs,
                     "test_files_scanned": len(records), "dirty_input_paths": dirty,
                     "scanned_inputs_dirty": dirty if dirty == "unknown" else bool(dirty)},
        "layers": {
            "classification": classification_layer(records),
            "lanes": lanes_layer(lanes, candidates),
            "execution": execution_layer(runs, candidates),
            "coverage": coverage_layer(coverage_path),
            "parity": parity_layer(repo_root),
            "simq": simq_layer(),
            "census": census_layer(),
            "mutation": mutation_layer(repo_root, as_of),
            "escaped_defects": escaped_defects_layer(repo_root, as_of),
        },
        "limits": list(V0_LIMITS),
    }


def to_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: Dict[str, Any]) -> str:
    m, layers = report["manifest"], report["layers"]
    out: List[str] = [f"# Core-RPG test report v0", "",
                      f"- SHA: `{m['sha']}`", f"- As of: {m['as_of']}",
                      f"- Test files scanned: {m['test_files_scanned']}",
                      f"- Uncommitted changes under scanned inputs: {m['scanned_inputs_dirty']}"
                      + (f" ({', '.join(m['dirty_input_paths'])})" if m["dirty_input_paths"] not in ("unknown", []) else ""),
                      "", "## Inputs", ""]
    out += [f"- {i['kind']}: `{i['artifact']}` (sha256 `{i['sha256'][:12]}`)" for i in m["inputs"]] or ["- none"]

    c = layers["classification"]
    d = c["denominator"]["test_files"]
    out += ["", "## Classification (heuristic)", "", f"Denominator: {d} test files.", ""]
    out += [f"- {k}: {v} / {d}" for k, v in c["counts"].items()]
    out += [f"- directory-only signal: {c['signal_disagreement']['directory_only']}, "
            f"import-only signal: {c['signal_disagreement']['import_only']}"]

    ln = layers["lanes"]
    nd = ln["denominator"]["core_rpg_candidate_files"]
    out += ["", "## CI lanes", "", f"State: {ln['state']}. Candidate files: {nd}; pytest lane steps: "
            f"{ln['denominator']['pytest_lane_steps']}.", ""]
    out += [f"- covered by a fast lane: {ln['counts']['covered_by_a_fast_lane']} / {nd}",
            f"- no fast lane: {ln['counts']['no_fast_lane']} / {nd}",
            f"- lane steps uploading JUnit: {ln['counts']['lane_steps_uploading_junit']} / "
            f"{ln['denominator']['pytest_lane_steps']}"]

    ex = layers["execution"]
    out += ["", "## Execution", "", f"State: **{ex['state']}**. Denominator: "
            f"{ex['denominator']['core_rpg_candidate_files']} core-RPG candidate files.", ""]
    for run in ex["runs"]:
        s = ex["summary"][run["run_id"]]
        o = run["outcomes"]
        out.append(f"- run `{run['run_id']}`: {run['testcases']} testcases "
                   f"(passed {o['passed']}, failed {o['failed']}, errors {o['errors']}, skipped {o['skipped']}, "
                   f"unmapped {run['unmapped_testcases']}); candidate files pass {s['pass']}, fail {s['fail']}, "
                   f"skipped {s['skipped']}, not-in-supplied-runs {s['not-in-supplied-runs']} / {s['denominator']}")
        for nodeid in run["failing_tests"]:
            out.append(f"  - failing: `{nodeid}`")
    if not ex["runs"]:
        out.append("- every candidate file is `no-junit-artifact`")

    cv = layers["coverage"]
    out += ["", "## Package coverage", "", f"State: **{cv['state']}**. Domain coverage: "
            f"{cv['domain_coverage']['state']}.", ""]
    if cv["package_coverage"]:
        out += [f"Total line coverage: {cv['total_line_pct']}% of {cv['denominator']['statements']} statements.", "",
                "| package | statements | line % | branch % |", "|---|---|---|---|"]
        for pkg, b in cv["package_coverage"].items():
            out.append(f"| {pkg} | {b['num_statements']} | {b['line_pct']} | {b['branch_pct']} |")

    p = layers["parity"]
    out += ["", "## Parity ledger (read-only)", "", f"Denominator: {p['denominator']['entries']} entries."]
    out += [f"- {k}: {v}" for k, v in p["counts"].items()]
    tp = p["test_path"]
    out += ["", f"`test_path` presence: P0 with {tp['p0']['with']} / without {tp['p0']['without']}; "
                f"other priorities with {tp['other_priorities']['with']} / without {tp['other_priorities']['without']}. "
                "P0 entries without a `test_path` (ids in the JSON report), by file:"]
    out += [f"- {name}: {len(ids)}" for name, ids in tp["p0_without_test_path"].items()]

    out += ["", "## SimQ and census", "", f"- SimQ: {layers['simq']['state']} ({layers['simq']['reason']})",
            f"- census: {layers['census']['state']} ({layers['census']['reason']})"]

    mu = layers["mutation"]
    out += ["", "## Mutation evidence", "", f"State: **{mu['state']}**.", ""]
    for r in mu["records"]:
        if r["state"] == "unreadable":
            out.append(f"- `{r['record']}`: **unreadable** ({r['reason']})")
            continue
        c2 = r["counts"]
        if r.get("role") == "superseded":
            out.append(f"- `{r['record']}` (`{r['target']}`): **superseded** by `{r['superseded_by']}`, history only; "
                       f"its counts (killed {c2['killed']}, survived {c2['survived']} / {r['denominator']['mutants']} mutants) "
                       "come from a different test selection and are not comparable with the current record's")
            continue
        label = f"`{r['record']}` " if r.get("supersedes") else ""
        out.append(f"- {label}`{r['target']}`: **{r['state']}** {r['stale_reasons'] or ''} (age {r['age_days']} d, "
                   f"{r['run_kind']}, {r['tool']}); killed {c2['killed']}, survived {c2['survived']}, "
                   f"timeout {c2['timeout']}, suspicious {c2['suspicious']}, equivalent {c2['equivalent']} / "
                   f"{r['denominator']['mutants']} mutants; {r['material_survivors']} material survivors flagged")

    ed = layers["escaped_defects"]
    out += ["", "## Escaped defects", "", f"State: **{ed['state']}**."]
    if ed["state"] == "counting":
        out += [f"Tag registered {ed['tag_registered']}; {ed['denominator']['tickets_scanned']} tickets scanned. "
                f"Month = {ed['month_basis']}.", ""]
        out += [f"- {month}: {count}" for month, count in ed["months"].items()]
        out += [f"- tagged outside the window: {ed['tagged_outside_window']}"]

    out += ["", "## v0 limits", ""] + [f"- {item}" for item in report["limits"]] + [""]
    return "\n".join(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--sha", default=None, help="commit the inputs describe (default: git HEAD of --repo-root)")
    parser.add_argument("--as-of", required=True, help="YYYY-MM-DD; an input, so output is reproducible")
    parser.add_argument("--junit", type=Path, nargs="*", default=[])
    parser.add_argument("--coverage", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    sha = args.sha or _git_sha(repo_root)
    report = build_report(repo_root, sha, dt.date.fromisoformat(args.as_of), args.junit, args.coverage)
    out_dir = args.out_dir or (repo_root / "reports" / "test_architecture" / sha)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(to_json(report), encoding="utf-8")
    (out_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {out_dir / 'report.json'} and report.md (report-only; exit 0 regardless of findings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
