#!/usr/bin/env python3
"""Which CI test lanes does this branch touch, read from `.github/workflows/test.yml` (TCK-20261014-PRE-PUSH-CI-LANE-PARITY).

`test.yml` is the single source: no lane list is copied here. A lane is a `test.yml` job. Mapping agreed with
testing-planner (who owns `test.yml`; this module only reads it):

- Always-on lane: a job that does not need `changed-files`. CI runs it on every PR, so the verdict is always
  `runs`, never "not affected". A changed file under one of its pytest step paths is shown as a separate
  *hint* (a relevant test changed); there is no src->test mapping, and picking tests is test-scoper's job.
- Path-filtered lane: a job whose `if:` reads `needs.changed-files.outputs.<flag>`. The flag comes from the
  `changed-files` step: the `PERF_RE` / `MIG_RE` / `FRONTEND_RE` / `DOCKER_RE` regexes (read from that step's
  shell text; Python `re` matches `grep -P` and `grep -E` for all four) and, for `run_scenario_lane`,
  `tools.test_architecture.scenario_lane_paths` run in-process the way CI runs it.
- Changed files are `git diff --name-only <base>...HEAD`: three dots, committed changes only. Uncommitted files
  are a separate warning.
- Fail open, like CI: a diff, regex, classifier or `if:` evaluation error gives `runs (fail-open)`, never
  `skipped`. A problem with `test.yml` itself (a missing/duplicate/uncompilable regex variable, an output or a
  pytest step the resolver cannot map) is listed in `Workflow.problems`; a test on the real file asserts it is empty.
- Models a `pull_request` against `main` only (other events run everything). `resync-gate` only skips a
  re-push whose content is unchanged, which a pre-push resolver cannot know, so it is assumed not to skip.
- `slow-regression*.yml` lanes are listed as "not on PR": their absence is not coverage.

CLI: `python3 -m tools.delivery.ci_lanes [--list] [--run] [--lane NAME ...] [--all] [--base origin/main]`.
`--run` runs, in `test.yml` order, the touched path-filtered lanes and the always-on lanes with a hint (all
`runs` lanes with `--all`, or exactly the `--lane` ones) and exits non-zero if one fails. It is a command the
implementer chooses to run; no hook runs it.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
TEST_WORKFLOW = WORKFLOWS_DIR / "test.yml"
CHANGED_FILES_JOB = "changed-files"
# Jobs that gate or feed other jobs rather than being a test lane.
GATE_JOBS = frozenset({"resync-gate"})

# changed-files output -> the regex variable its step computes it from. run_scenario_lane is the classifier.
OUTPUT_REGEX_VAR = {
    "run_perf_cert_arena": "PERF_RE",
    "run_migration_lanes": "MIG_RE",
    "run_frontend": "FRONTEND_RE",
    "run_docker_build": "DOCKER_RE",
}
SCENARIO_OUTPUT = "run_scenario_lane"

_REGEX_ASSIGN = re.compile(r"^\s*(\w+_RE)='(.*)'\s*$", re.MULTILINE)
_STEP_COMMAND_LINE = re.compile(r"^\s*(?:make|python3?\s+-m)\s", re.MULTILINE)
_TEST_PATH = re.compile(r"^tests/[\w./\-]+$")
_IGNORE_GLOB = re.compile(r"--ignore-glob=(?:'([^']*)'|\"([^\"]*)\"|(\S+))")
_JUNIT = re.compile(r"\s*--junit-xml=\S+")
_BASE_COLLECTION = "Base branch test collection"


@dataclass
class Step:
    name: str
    command: str  # line continuations folded
    paths: List[str] = field(default_factory=list)
    ignore_globs: List[str] = field(default_factory=list)


@dataclass
class Lane:
    name: str
    needs: List[str]
    if_expr: str
    steps: List[Step]
    flags: List[str]  # changed-files outputs its `if:` reads
    always_on: bool


@dataclass
class Workflow:
    lanes: List[Lane]
    regexes: Dict[str, "re.Pattern[str]"]
    problems: List[str]


@dataclass
class LaneVerdict:
    lane: str
    verdict: str  # "runs" | "skipped" | "runs (fail-open)"
    reason: str
    hints: List[str] = field(default_factory=list)  # changed files under the lane's pytest paths


def _fold(run: str) -> str:
    return re.sub(r"\\\n\s*", " ", run).strip()


def _is_command_step(run: str, name: str) -> bool:
    if name == _BASE_COLLECTION or "/tmp/base-checkout" in run:
        return False
    return bool(re.search(r"\bpytest\b", run) or _STEP_COMMAND_LINE.search(run))


def _make_step(name: str, run: str) -> Step:
    folded = _fold(run)
    globs = [a or b or c for a, b, c in _IGNORE_GLOB.findall(folded)]
    paths = [t for t in re.split(r"\s+", _IGNORE_GLOB.sub("", folded)) if _TEST_PATH.match(t)]
    return Step(name=name, command=run.strip(), paths=paths, ignore_globs=globs)


def load_workflow(path: Path = TEST_WORKFLOW) -> Workflow:
    import yaml  # local: the hook degrades to "no finding" when PyYAML is absent

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    problems: List[str] = []

    cf = jobs.get(CHANGED_FILES_JOB)
    cf_text = "\n".join(s.get("run", "") for s in (cf or {}).get("steps", []))
    regexes: Dict[str, "re.Pattern[str]"] = {}
    found: Dict[str, List[str]] = {}
    for var, pattern in _REGEX_ASSIGN.findall(cf_text):
        found.setdefault(var, []).append(pattern)
    for var in OUTPUT_REGEX_VAR.values():
        values = found.get(var, [])
        if len(values) != 1:
            problems.append(f"{var}: expected exactly one assignment in the {CHANGED_FILES_JOB} step, found {len(values)}")
            continue
        try:
            regexes[var] = re.compile(values[0])
        except re.error as exc:
            problems.append(f"{var}: pattern does not compile ({exc})")
    for out in (cf or {}).get("outputs", {}):
        if out != SCENARIO_OUTPUT and out not in OUTPUT_REGEX_VAR:
            problems.append(f"{CHANGED_FILES_JOB} output {out} has no mapping in ci_lanes.OUTPUT_REGEX_VAR")

    lanes: List[Lane] = []
    for name, job in jobs.items():
        if name == CHANGED_FILES_JOB or name in GATE_JOBS:
            continue
        needs = job.get("needs") or []
        needs = [needs] if isinstance(needs, str) else list(needs)
        if_expr = str(job.get("if", ""))
        flags = re.findall(r"needs\.changed-files\.outputs\.(\w+)", if_expr)
        steps = [
            _make_step(s.get("name") or "(unnamed)", s["run"])
            for s in job.get("steps", [])
            if "run" in s and _is_command_step(s["run"], s.get("name") or "")
        ]
        always_on = CHANGED_FILES_JOB not in needs
        for s in steps:
            if "pytest" in s.command and not s.paths:
                problems.append(f"{name}: pytest step {s.name!r} names no tests/ path the resolver can map")
        if not always_on and not flags:
            problems.append(f"{name}: needs {CHANGED_FILES_JOB} but its if: reads no changed-files output")
        lanes.append(Lane(name, needs, if_expr, steps, flags, always_on))
    return Workflow(lanes, regexes, problems)


def compute_flags(workflow: Workflow, changed: Sequence[str]) -> Dict[str, bool]:
    """The changed-files outputs for a pull_request diff, as CI computes them."""
    flags: Dict[str, bool] = {}
    for out, var in OUTPUT_REGEX_VAR.items():
        pattern = workflow.regexes.get(var)
        if pattern is None:
            raise ValueError(f"{var} unavailable")
        flags[out] = any(pattern.search(p) for p in changed)
    from tools.test_architecture import scenario_lane_paths

    result = scenario_lane_paths.classify(changed)
    flags[SCENARIO_OUTPUT] = bool(result["run"]) or not changed  # empty diff: fail open, as the classifier's main does
    return flags


_ATOMS = [
    (re.compile(r"!cancelled\(\)"), lambda m, f: "True"),
    (re.compile(r"needs\.changed-files\.result\s*!=\s*'success'"), lambda m, f: "False"),
    (re.compile(r"needs\.changed-files\.outputs\.(\w+)\s*==\s*'true'"), lambda m, f: repr(f[m.group(1)])),
    (re.compile(r"needs\.changed-files\.outputs\.(\w+)\s*!=\s*'true'"), lambda m, f: repr(not f[m.group(1)])),
    # resync-gate only skips a re-push of unchanged content; a pre-push resolver cannot know that, so it never skips.
    (re.compile(r"needs\.resync-gate\.result\s*!=\s*'success'"), lambda m, f: "True"),
    (re.compile(r"needs\.resync-gate\.outputs\.pr_content_unchanged\s*!=\s*'true'"), lambda m, f: "True"),
]


def evaluate_if(expr: str, flags: Dict[str, bool]) -> bool:
    """Evaluate a job `if:` over the known atoms; raises ValueError on anything else (the caller fails open)."""
    e = expr.strip()
    if e.startswith("${{") and e.endswith("}}"):
        e = e[3:-2]
    for pattern, repl in _ATOMS:
        e = pattern.sub(lambda m, r=repl: r(m, flags), e)
    e = e.replace("&&", " and ").replace("||", " or ")
    if not re.fullmatch(r"(?:\s|True|False|and|or|\(|\))*", e):
        raise ValueError(f"unrecognised condition: {e.strip()}")
    return _eval_bool(ast.parse(e.strip(), mode="eval").body)


def _eval_bool(node: "ast.expr") -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BoolOp):
        values = [_eval_bool(v) for v in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    raise ValueError(f"unsupported condition node {type(node).__name__}")


def _hints(lane: Lane, changed: Sequence[str]) -> List[str]:
    out: List[str] = []
    for step in lane.steps:
        for path in changed:
            if path in out or any(fnmatch.fnmatch(path, g) for g in step.ignore_globs):
                continue
            if any(path == t or path.startswith(t.rstrip("/") + "/") for t in step.paths):
                out.append(path)
    return out


def resolve(workflow: Workflow, changed: Sequence[str], diff_ok: bool = True) -> List[LaneVerdict]:
    """One verdict per `test.yml` job, in file order. Never returns `skipped` for an always-on lane."""
    flags: Optional[Dict[str, bool]] = None
    flag_error = "" if diff_ok else "the changed-file diff failed"
    if diff_ok:
        try:
            flags = compute_flags(workflow, changed)
        except Exception as exc:  # fail open
            flag_error = f"path-filter evaluation failed ({exc})"
    verdicts: List[LaneVerdict] = []
    for lane in workflow.lanes:
        hints = _hints(lane, changed)
        if lane.always_on:
            verdicts.append(LaneVerdict(lane.name, "runs", "always on (no path filter)", hints))
            continue
        if flags is None:
            verdicts.append(LaneVerdict(lane.name, "runs (fail-open)", flag_error, hints))
            continue
        try:
            runs = evaluate_if(lane.if_expr, flags)
        except Exception as exc:
            verdicts.append(LaneVerdict(lane.name, "runs (fail-open)", f"cannot evaluate its if: ({exc})", hints))
            continue
        reason = "path filter: " + ", ".join(f"{f}={'true' if flags.get(f) else 'false'}" for f in lane.flags)
        verdicts.append(LaneVerdict(lane.name, "runs" if runs else "skipped", reason, hints))
    return verdicts


def touched(workflow: Workflow, verdicts: Sequence[LaneVerdict]) -> List[LaneVerdict]:
    """Lanes this branch specifically touches: a path-filtered lane that runs, or an always-on lane with a hint."""
    always = {l.name: l.always_on for l in workflow.lanes}
    return [v for v in verdicts if v.verdict.startswith("runs") and (not always[v.lane] or v.hints)]


def slow_lanes(workflows_dir: Path = WORKFLOWS_DIR) -> List[str]:
    import yaml

    out = []
    for path in sorted(workflows_dir.glob("slow-regression*.yml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            triggers = data.get("on", data.get(True, {}))
            names = list(triggers) if isinstance(triggers, dict) else [triggers]
            out.append(f"{path.name}: not on PR (triggers: {', '.join(map(str, names))})")
        except Exception:
            out.append(f"{path.name}: not on PR (triggers unreadable)")
    return out


def git_changed(base: str, run=subprocess.run) -> Optional[List[str]]:
    r = run(["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
    return None if r.returncode != 0 else [p for p in r.stdout.splitlines() if p.strip()]


def git_uncommitted(run=subprocess.run) -> List[str]:
    r = run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO_ROOT)
    return [] if r.returncode != 0 else [ln[3:] for ln in r.stdout.splitlines() if ln.strip()]


def lane_commands(lane: Lane) -> List[str]:
    return [_JUNIT.sub("", s.command) for s in lane.steps]


def render_list(workflow: Workflow, verdicts: Sequence[LaneVerdict], base: str, uncommitted: Sequence[str] = ()) -> str:
    by_name = {l.name: l for l in workflow.lanes}
    touched_names = {v.lane for v in touched(workflow, verdicts)}
    out = [
        f"CI lanes for `git diff --name-only {base}...HEAD` (pull_request against main; resync-gate assumed not to skip).",
        "Unfiltered lanes run on every PR; `hint` = a changed file sits under that lane's pytest paths.",
        "",
    ]
    for v in verdicts:
        mark = "*" if v.lane in touched_names else " "
        out.append(f"{mark} {v.lane}: {v.verdict} -- {v.reason}")
        if v.hints:
            shown = ", ".join(v.hints[:5]) + (f" (+{len(v.hints) - 5} more)" if len(v.hints) > 5 else "")
            out.append(f"      hint: {shown}")
        if v.lane in touched_names:
            for cmd in lane_commands(by_name[v.lane]):
                out.append("      $ " + cmd.replace("\n", "\n        "))
    out.append("")
    out.append("* = touched by this branch (what `--run` runs). `--all` runs every `runs` lane; `--lane NAME` picks one.")
    out.extend(slow_lanes())
    if uncommitted:
        out.append(f"warning: {len(uncommitted)} uncommitted path(s) are not in the diff above (CI sees committed changes only).")
    if workflow.problems:
        out.append("warning: test.yml has parts this resolver cannot map: " + "; ".join(workflow.problems))
    return "\n".join(out)


def run_lanes(workflow: Workflow, names: Sequence[str], runner=subprocess.run) -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    by_name = {l.name: l for l in workflow.lanes}
    for name in names:
        ok = True
        for cmd in lane_commands(by_name[name]):
            print(f"[{name}] $ {cmd}", flush=True)
            ok = runner(["bash", "-ec", cmd], cwd=REPO_ROOT).returncode == 0 and ok
            if not ok:
                break
        results[name] = ok
        print(f"{'PASS' if ok else 'FAIL'}: {name}", flush=True)
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print the lane verdicts (default)")
    ap.add_argument("--run", action="store_true", help="run the touched lanes locally; non-zero exit on a failing lane")
    ap.add_argument("--all", action="store_true", help="with --run: every lane that runs, not only the touched ones")
    ap.add_argument("--lane", action="append", default=[], help="with --run: exactly this lane (repeatable)")
    ap.add_argument("--base", default="origin/main")
    args = ap.parse_args(argv)

    workflow = load_workflow()
    changed = git_changed(args.base)
    verdicts = resolve(workflow, changed or [], diff_ok=changed is not None)
    print(render_list(workflow, verdicts, args.base, git_uncommitted()))
    if changed is None:
        print(f"warning: `git diff --name-only {args.base}...HEAD` failed; every path-filtered lane is shown as fail-open.")
    if not args.run:
        return 0
    known = {l.name for l in workflow.lanes}
    bad = [n for n in args.lane if n not in known]
    if bad:
        print(f"unknown lane(s): {', '.join(bad)}", file=sys.stderr)
        return 2
    if args.lane:
        names = args.lane
    elif args.all:
        names = [v.lane for v in verdicts if v.verdict.startswith("runs")]
    else:
        names = [v.lane for v in touched(workflow, verdicts)]
    print("")
    results = run_lanes(workflow, names)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
