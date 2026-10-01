"""Report-only cost view over supplied JUnit XML (roadmap §9, Epic A).

Reads the JUnit files or directories you supply and prints, per run and per test directory, what the
artifacts recorded: testcase and unique-node counts, the sum of recorded `time` attributes (labelled
"observed test duration": a sum of per-test durations as pytest wrote them, NOT wall time or compute cost),
outcomes, and the slowest files and nodes. It never runs tests and changes no exit code from its findings.

It enables cleanup *investigation* and authorizes nothing: a §9 cleanup still needs its per-target record and
an owner decision. CI uploads JUnit only from the api-tools job today, so most directories will honestly read
`not-in-supplied-runs`; that is "no evidence", never zero seconds.

Run: `python3 -m tools.test_architecture.junit_cost_report PATH [PATH ...] [--sha SHA] [--source LABEL]
      [--repo-root DIR] [--top N] [--format json|markdown]`
Each XML file is one run; a directory contributes every `*.xml` beneath it. Runs are never merged.
"""

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

SCHEMA_VERSION = 1
NO_ARTIFACT = "no-junit-artifact"
MISSING_DURATION = "missing-duration"
NOT_IN_RUNS = "not-in-supplied-runs"
DURATION_LABEL = "observed test duration"
_OUTCOMES = ("passed", "failed", "errors", "skipped")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_xml(paths: Iterable[Path]) -> List[Path]:
    """Every supplied XML file, directories expanded, de-duplicated by path and sorted."""
    found: Set[Path] = set()
    for p in paths:
        if p.is_dir():
            found.update(x for x in p.rglob("*.xml") if x.is_file())
        elif p.is_file():
            found.add(p)
    return sorted(found)


def _resolve_file(classname: str, repo_root: Optional[Path]) -> Optional[str]:
    """Longest classname prefix that is a real `.py` under repo_root, else None (never guessed)."""
    if not classname or repo_root is None:
        return None
    parts = classname.split(".")
    for i in range(len(parts), 0, -1):
        cand = "/".join(parts[:i]) + ".py"
        if (repo_root / cand).is_file():
            return cand
    return None


def _outcome(tc: ET.Element) -> str:
    if tc.find("failure") is not None:
        return "failed"
    if tc.find("error") is not None:
        return "errors"
    if tc.find("skipped") is not None:
        return "skipped"
    return "passed"


def _dir_of(file: Optional[str]) -> str:
    return file.rsplit("/", 1)[0] if file and "/" in file else ("." if file else "unmapped")


def parse_run(path: Path, repo_root: Optional[Path]) -> Dict[str, Any]:
    data = path.read_bytes()
    digest = _sha256(data)
    root = ET.fromstring(data)
    outcomes = dict.fromkeys(_OUTCOMES, 0)
    nodes: Set[str] = set()
    per_file: Dict[str, Dict[str, Any]] = {}
    per_node: Dict[str, float] = {}
    per_dir: Dict[str, Dict[str, Any]] = {}
    missing = 0
    testcases = 0
    for tc in root.iter("testcase"):
        testcases += 1
        kind = _outcome(tc)
        outcomes[kind] += 1
        classname, name = tc.get("classname", ""), tc.get("name", "")
        node = f"{classname}::{name}"
        nodes.add(node)
        raw = tc.get("time")
        try:
            seconds: Optional[float] = float(raw) if raw is not None else None
        except ValueError:
            seconds = None
        if seconds is None:
            missing += 1
        file = _resolve_file(classname, repo_root)
        fkey = file or f"unmapped:{classname}"
        for table, key in ((per_file, fkey), (per_dir, _dir_of(file))):
            row = table.setdefault(key, {"testcases": 0, "duration": 0.0, "missing": 0, **dict.fromkeys(_OUTCOMES, 0)})
            row["testcases"] += 1
            row[kind] += 1
            if seconds is None:
                row["missing"] += 1
            else:
                row["duration"] += seconds
        if seconds is not None:
            per_node[node] = per_node.get(node, 0.0) + seconds
    return {
        "artifact": path.name, "path": path.as_posix(), "sha256": digest, "run_id": f"{path.stem}-{digest[:12]}",
        "testcases": testcases, "unique_nodes": len(nodes), "outcomes": outcomes,
        "duration_label": DURATION_LABEL,
        "duration_state": MISSING_DURATION if missing else "recorded",
        "testcases_missing_duration": missing,
        "observed_test_duration_s": round(sum(r["duration"] for r in per_file.values()), 6),
        "per_directory": per_dir, "per_file": per_file, "per_node": per_node, "node_set": sorted(nodes),
    }


def _slowest(table: Dict[str, Any], top: int, field: Optional[str]) -> List[Dict[str, Any]]:
    rows = [(k, v[field] if field else v) for k, v in table.items()]
    rows.sort(key=lambda kv: (-kv[1], kv[0]))  # slowest first, name breaks ties deterministically
    return [{"name": k, "observed_test_duration_s": round(v, 6)} for k, v in rows[:top]]


def build_report(xml_paths: Sequence[Path], supplied: Sequence[str], sha: str = "unknown", source: str = "unspecified",
                 repo_root: Optional[Path] = None, top: int = 10) -> Dict[str, Any]:
    runs = [parse_run(p, repo_root) for p in xml_paths]
    all_dirs = sorted({d for r in runs for d in r["per_directory"]})
    by_sha: Dict[str, List[str]] = {}
    for r in runs:
        by_sha.setdefault(r["sha256"], []).append(r["run_id"])
    duplicates = [{"sha256": s, "runs": sorted(ids)} for s, ids in sorted(by_sha.items()) if len(ids) > 1]
    overlaps = []
    for i, a in enumerate(runs):
        for b in runs[i + 1:]:
            common = set(a["node_set"]) & set(b["node_set"])
            if common and a["sha256"] != b["sha256"]:
                overlaps.append({"runs": sorted([a["run_id"], b["run_id"]]), "shared_nodes": len(common)})
    out_runs = []
    for r in runs:
        dirs = {d: ({**r["per_directory"][d], "duration": round(r["per_directory"][d]["duration"], 6)}
                    if d in r["per_directory"] else {"state": NOT_IN_RUNS}) for d in all_dirs}
        out_runs.append({
            **{k: r[k] for k in ("run_id", "artifact", "path", "sha256", "testcases", "unique_nodes", "outcomes",
                                 "duration_label", "duration_state", "testcases_missing_duration",
                                 "observed_test_duration_s")},
            "per_directory": dirs,
            "slowest_files": _slowest(r["per_file"], top, "duration"),
            "slowest_nodes": _slowest(r["per_node"], top, None),
        })
    return {
        "schema_version": SCHEMA_VERSION, "kind": "junit_cost_view", "report_only": True,
        "identity": {"sha": sha, "source": source, "input_scope": sorted(supplied)},
        "state": "junit-supplied" if runs else NO_ARTIFACT,
        "duration_label": DURATION_LABEL,
        "duration_note": "sum of per-testcase `time` as recorded; not wall time and not compute cost",
        "runs": out_runs, "directories_seen": all_dirs,
        "duplicate_artifacts": duplicates, "overlapping_node_sets": overlaps,
        "failure_history": "unavailable",
        "authorizes": "nothing: roadmap §9 per-target record and owner decision still apply",
    }


def render_markdown(report: Dict[str, Any]) -> str:
    ident = report["identity"]
    out = ["# JUnit cost view (report only)", "",
           f"- SHA `{ident['sha']}`, source `{ident['source']}`, input scope: {', '.join(ident['input_scope']) or 'none'}",
           f"- State: `{report['state']}`. Durations are **{DURATION_LABEL}** (sum of recorded per-test time, not wall "
           "time or compute cost). Failure history: **unavailable**. Authorizes nothing (§9).", ""]
    if report["state"] == NO_ARTIFACT:
        out.append(f"No JUnit artifact supplied (`{NO_ARTIFACT}`): no cost evidence exists in this report.")
        return "\n".join(out) + "\n"
    for d in report["duplicate_artifacts"]:
        out.append(f"- **Duplicate artifacts** (same sha256 `{d['sha256'][:12]}`): {', '.join(d['runs'])}")
    for o in report["overlapping_node_sets"]:
        out.append(f"- **Overlapping node sets**: {' and '.join(o['runs'])} share {o['shared_nodes']} nodes")
    for r in report["runs"]:
        oc = r["outcomes"]
        out += ["", f"## Run `{r['run_id']}`", "",
                f"- {r['testcases']} testcases, {r['unique_nodes']} unique nodes; passed {oc['passed']}, "
                f"failed {oc['failed']}, error {oc['errors']}, skipped {oc['skipped']}",
                f"- {DURATION_LABEL}: {r['observed_test_duration_s']} s ({r['duration_state']}"
                + (f", {r['testcases_missing_duration']} testcases without a recorded time" if r["testcases_missing_duration"] else "")
                + ")", "", f"| Directory | Testcases | {DURATION_LABEL} (s) | Pass/Fail/Err/Skip |", "|---|---|---|---|"]
        for d, row in r["per_directory"].items():
            if row.get("state") == NOT_IN_RUNS:
                out.append(f"| `{d}` | {NOT_IN_RUNS} | {NOT_IN_RUNS} | - |")
            else:
                out.append(f"| `{d}` | {row['testcases']} | {row['duration']}"
                           + (" (partial: missing time)" if row["missing"] else "")
                           + f" | {row['passed']}/{row['failed']}/{row['errors']}/{row['skipped']} |")
        out += ["", "Slowest files: " + ", ".join(f"`{s['name']}` {s['observed_test_duration_s']} s" for s in r["slowest_files"]),
                "", "Slowest nodes: " + ", ".join(f"`{s['name']}` {s['observed_test_duration_s']} s" for s in r["slowest_nodes"])]
    return "\n".join(out) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--sha", default="unknown")
    ap.add_argument("--source", default="unspecified")
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = ap.parse_args(argv)
    report = build_report(collect_xml(args.paths), [p.as_posix() for p in args.paths], args.sha, args.source,
                          args.repo_root, args.top)
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n" if args.format == "json" else render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
