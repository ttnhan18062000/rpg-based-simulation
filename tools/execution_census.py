#!/usr/bin/env python3
"""Execution census: branch coverage over the SimQ corpus, differenced against unit-test coverage.

Design: docs/plans/simulation_execution_census_initiative.md (see especially §7, "Proposed
Design"). On-demand only — this tool has no scheduled/CI invocation and is not a gate; see that
document's §7.5 for why. Nothing here fails a build or blocks a merge under any configuration.

Two axes, not one taxonomy with a sixth value (peer review, 2026-09-15):
  - REACHABILITY (D09's five statuses, computed here): never-called / test-only / tick-live,
    at branch granularity so a line that executes but never takes one of its branches (the
    `check_for_boss_spawn()` shape — every line ran, the guarded branch never fired) is visible,
    which line coverage alone cannot show.
  - EFFECTIVENESS: NOT automated in this version. Every finding reports
    effectiveness="not_automated" with a note explaining why (see LIMITATION_HEADER below) --
    determining whether a reachable branch's result is ever consumed by anything downstream is a
    data-flow/call-graph question, not a coverage question, and is out of scope for a first build.
    Reporting the axis honestly as unautomated is preferred over a heuristic that would silently
    overclaim precision.

Subcommands:
  unit-baseline   Run the unit/integration test suite under branch coverage.
  corpus-run      Run one or more corpus worlds under branch coverage, combine into one dataset.
  report          Diff corpus coverage against the unit baseline and emit a census report.
  stability-check Run one corpus world twice and diff branch-hit sets (determinism precondition,
                  §7.2 of the design doc -- an unstable run cannot be trusted).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

COVERAGE_SOURCES = ["src", "tools"]
DATA_DIR = REPO_ROOT / "data" / "execution_census"
UNIT_DATA_FILE = DATA_DIR / ".coverage.unit"
CORPUS_DATA_FILE = DATA_DIR / ".coverage.corpus"
CORPUS_REGISTRY = REPO_ROOT / "config" / "simulation_quality" / "corpus_registry.yaml"
SUPPRESSIONS_FILE = REPO_ROOT / "config" / "execution_census" / "suppressions.yaml"
BASELINE_FILE = REPO_ROOT / "config" / "execution_census" / "baseline.json"

LIMITATION_HEADER = (
    "PRECONDITION: this report is provisional until a 'stability-check' run for the world(s) in "
    "scope returns STABLE. The first real stability-check (crowded_frontier, 300 ticks) reported "
    "UNSTABLE -- 382 files with differing branch-arc coverage across two identical runs, tied to "
    "the kernel's wall-clock watchdog (TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2). "
    "Treat findings below as directional, not fact, until stability is confirmed for this run. "
    "This census finds code that never executes, or never takes a branch, across the SimQ "
    "corpus. It cannot detect a live mechanism producing a wrong outcome -- a branch reported as "
    "taken here may still be behaving incorrectly. See SimQ pillar scores for outcome quality. "
    "The effectiveness axis (does a reached branch's result get consumed by anything) is not "
    "automated in this version; every finding below reports effectiveness=\"not_automated\"."
)


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUPPRESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# unit-baseline
# ---------------------------------------------------------------------------

def cmd_unit_baseline(args: argparse.Namespace) -> int:
    _ensure_dirs()
    if UNIT_DATA_FILE.exists():
        UNIT_DATA_FILE.unlink()
    src_arg = ",".join(COVERAGE_SOURCES)
    cmd = [
        sys.executable, "-m", "coverage", "run", "--branch",
        f"--source={src_arg}", f"--data-file={UNIT_DATA_FILE}",
        "-m", "pytest",
        "tests/unit", "tests/integration",
        "-m", "not slow and not extra_slow",
        "-q",
    ]
    print(f"[execution_census] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    # pytest's own exit code (test failures) is not this tool's concern -- the coverage data
    # file is written regardless, and a census run should not be blocked by an unrelated test
    # failure elsewhere in the suite.
    if not UNIT_DATA_FILE.exists():
        print("[execution_census] ERROR: no coverage data produced", file=sys.stderr)
        return 1
    print(f"[execution_census] unit baseline written: {UNIT_DATA_FILE}")
    return 0


# ---------------------------------------------------------------------------
# corpus-run
# ---------------------------------------------------------------------------

def _load_corpus_world_names() -> List[str]:
    with open(CORPUS_REGISTRY, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    return sorted(registry.get("_worlds", {}).keys())


def _run_one_world_under_coverage(world: str, seed: int, ticks: int, data_file: Path) -> bool:
    """Runs `world` for `ticks` ticks under branch coverage instrumentation.

    Returns True on success. Any world load/compile/run failure is reported and skipped rather
    than aborting the whole corpus-run -- one bad world should not prevent measuring the rest.
    """
    import coverage as coverage_mod

    cov = coverage_mod.Coverage(
        data_file=str(data_file), branch=True, source=COVERAGE_SOURCES,
    )
    cov.start()
    try:
        from src.worldbuilding.compiler import WorldCompiler
        from src.worldbuilding.repository import WorldRepository
        from src.engine.kernel import Kernel
        from src.config.profiles import PROD_SMALL
        from src.platform.rng import DeterministicRNG

        repo = WorldRepository(str(REPO_ROOT / "data" / "worlds"))
        spec, context = repo.load_world_with_context(world)
        state, _report = WorldCompiler.compile(spec, seed, context=context)

        kernel = Kernel(
            profile=PROD_SMALL, state=state, rng=DeterministicRNG(seed),
            flags={"no_frame_pacing": True},
        )
        try:
            for _ in range(ticks):
                kernel.tick_once()
        finally:
            kernel.shutdown()
        return True
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: one world's failure must not
        print(f"[execution_census] WARNING: world '{world}' failed: {exc}", file=sys.stderr)
        return False
    finally:
        cov.stop()
        cov.save()


def cmd_corpus_run(args: argparse.Namespace) -> int:
    _ensure_dirs()
    worlds = args.worlds.split(",") if args.worlds else _load_corpus_world_names()
    print(f"[execution_census] running {len(worlds)} corpus world(s) under branch coverage: {worlds}")

    per_world_files = []
    for world in worlds:
        data_file = DATA_DIR / f".coverage.corpus.{world}"
        if data_file.exists():
            data_file.unlink()
        ok = _run_one_world_under_coverage(world, args.seed, args.ticks, data_file)
        if ok:
            per_world_files.append(str(data_file))
            print(f"[execution_census]   {world}: OK ({args.ticks} ticks, seed {args.seed})")

    if not per_world_files:
        print("[execution_census] ERROR: no worlds ran successfully", file=sys.stderr)
        return 1

    if CORPUS_DATA_FILE.exists():
        CORPUS_DATA_FILE.unlink()
    import coverage as coverage_mod
    combined = coverage_mod.Coverage(data_file=str(CORPUS_DATA_FILE), branch=True, source=COVERAGE_SOURCES)
    combined.combine(per_world_files, keep=True)
    combined.save()
    print(f"[execution_census] corpus coverage combined into: {CORPUS_DATA_FILE}")
    return 0


# ---------------------------------------------------------------------------
# report (the diff/classification engine)
# ---------------------------------------------------------------------------

@dataclass
class BranchFinding:
    file: str
    line: int
    reachability: str  # "never-called" | "test-only" | "tick-live"
    branch_complete: Optional[bool]  # None if not a branch line
    total_exits: Optional[int] = None
    taken_exits: Optional[int] = None
    effectiveness: str = "not_automated"
    suppressed: bool = False
    suppression_reason: Optional[str] = None

    def key(self) -> str:
        return f"{self.file}:{self.line}"


def _load_suppressions() -> Dict[str, Dict[str, str]]:
    if not SUPPRESSIONS_FILE.exists():
        return {}
    with open(SUPPRESSIONS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("suppressions", {}) or {}


def _relativize(filename: str) -> str:
    """Repo-relative path, so suppression-list keys are portable across clones/worktrees."""
    try:
        return str(Path(filename).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return filename


def _classify(unit_cov, corpus_cov, filename: str) -> List[BranchFinding]:
    findings: List[BranchFinding] = []
    display_filename = _relativize(filename)
    try:
        unit_analysis = unit_cov._analyze(filename) if unit_cov else None
    except Exception:
        unit_analysis = None
    try:
        corpus_analysis = corpus_cov._analyze(filename) if corpus_cov else None
    except Exception:
        corpus_analysis = None

    if corpus_analysis is None:
        return findings

    unit_executed = set(unit_analysis.statements) - set(unit_analysis.missing) if unit_analysis else set()
    corpus_executed = set(corpus_analysis.statements) - set(corpus_analysis.missing)
    all_statements = set(corpus_analysis.statements)
    if unit_analysis:
        all_statements |= set(unit_analysis.statements)

    corpus_branch_stats = corpus_analysis.branch_stats() if corpus_analysis else {}

    for line in sorted(all_statements):
        if line in corpus_executed:
            reachability = "tick-live"
        elif line in unit_executed:
            reachability = "test-only"
        else:
            reachability = "never-called"

        branch_complete: Optional[bool] = None
        total_exits = taken_exits = None
        if line in corpus_branch_stats:
            total_exits, taken_exits = corpus_branch_stats[line]
            branch_complete = taken_exits >= total_exits

        findings.append(BranchFinding(
            file=display_filename, line=line, reachability=reachability,
            branch_complete=branch_complete, total_exits=total_exits, taken_exits=taken_exits,
        ))
    return findings


def cmd_report(args: argparse.Namespace) -> int:
    import coverage as coverage_mod

    if not CORPUS_DATA_FILE.exists():
        print(f"[execution_census] ERROR: no corpus coverage data at {CORPUS_DATA_FILE} -- run 'corpus-run' first", file=sys.stderr)
        return 1

    unit_cov = None
    if UNIT_DATA_FILE.exists():
        unit_cov = coverage_mod.Coverage(data_file=str(UNIT_DATA_FILE), branch=True, source=COVERAGE_SOURCES)
        unit_cov.load()
    else:
        print("[execution_census] WARNING: no unit baseline found -- 'test-only' status cannot be distinguished from 'never-called'", file=sys.stderr)

    corpus_cov = coverage_mod.Coverage(data_file=str(CORPUS_DATA_FILE), branch=True, source=COVERAGE_SOURCES)
    corpus_cov.load()

    measured_files = sorted(corpus_cov.get_data().measured_files())
    if unit_cov:
        measured_files = sorted(set(measured_files) | set(unit_cov.get_data().measured_files()))

    all_findings: List[BranchFinding] = []
    for filename in measured_files:
        all_findings.extend(_classify(unit_cov, corpus_cov, filename))

    # Interesting = signature this census exists to find: reachable-by-tests but never
    # corpus-reached, OR reachable but with an incomplete branch (a line that ran but a branch
    # of it never fired).
    interesting = [
        f for f in all_findings
        if f.reachability == "test-only" or (f.reachability == "tick-live" and f.branch_complete is False)
    ]

    suppressions = _load_suppressions()
    for f in interesting:
        entry = suppressions.get(f.key())
        if entry:
            f.suppressed = True
            f.suppression_reason = entry.get("reason")

    unsuppressed = [f for f in interesting if not f.suppressed]

    baseline_count = None
    is_new_beyond_baseline = None
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE, "r", encoding="utf-8") as bf:
            baseline = json.load(bf)
        baseline_count = baseline.get("finding_count")
        is_new_beyond_baseline = len(unsuppressed) > baseline_count if baseline_count is not None else None

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "limitation": LIMITATION_HEADER,
        "gate_status": "REPORT-ONLY -- never gates. See docs/plans/simulation_execution_census_initiative.md §7.3 "
                       "for the exit condition (suppression list stable AND false-positive rate known).",
        "sources_scanned": COVERAGE_SOURCES,
        "unit_baseline_present": unit_cov is not None,
        "total_findings": len(interesting),
        "suppressed_findings": len(interesting) - len(unsuppressed),
        "unsuppressed_findings": len(unsuppressed),
        "baseline_count": baseline_count,
        "new_beyond_baseline": is_new_beyond_baseline,
        "findings": [
            {
                "file": f.file, "line": f.line, "reachability": f.reachability,
                "branch_complete": f.branch_complete,
                "total_exits": f.total_exits, "taken_exits": f.taken_exits,
                "effectiveness": f.effectiveness,
                "suppressed": f.suppressed, "suppression_reason": f.suppression_reason,
            }
            for f in interesting
        ],
    }

    output_path = Path(args.output) if args.output else DATA_DIR / "report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(LIMITATION_HEADER)
    print()
    print(f"Total findings: {len(interesting)} ({len(unsuppressed)} unsuppressed, "
          f"{len(interesting) - len(unsuppressed)} suppressed)")
    if baseline_count is not None:
        print(f"Baseline: {baseline_count} -- {'NEW findings beyond baseline' if is_new_beyond_baseline else 'within baseline'}")
    else:
        print("No baseline set yet -- run 'bootstrap-baseline' after human triage to establish one.")
    print()
    for f in unsuppressed[:args.max_print]:
        shape = "test-only, never corpus-executed" if f.reachability == "test-only" else \
            f"tick-live but branch incomplete ({f.taken_exits}/{f.total_exits} exits taken)"
        print(f"  {f.file}:{f.line}  {shape}")
    if len(unsuppressed) > args.max_print:
        print(f"  ... and {len(unsuppressed) - args.max_print} more (see {output_path})")

    print(f"\n[execution_census] full report written: {output_path}")
    return 0


def cmd_bootstrap_baseline(args: argparse.Namespace) -> int:
    """Sets the ratchet baseline from the most recent report -- never asserts zero.

    Per docs/plans/simulation_execution_census_initiative.md §7.3: a detector landing in an
    already-dirty corpus must ratchet from the current state, not assert zero. This command is
    meant to be run once, deliberately, after a human has reviewed the report -- not automatically.
    """
    report_path = Path(args.report) if args.report else DATA_DIR / "report.json"
    if not report_path.exists():
        print(f"[execution_census] ERROR: no report at {report_path} -- run 'report' first", file=sys.stderr)
        return 1
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    baseline = {
        "finding_count": report["unsuppressed_findings"],
        "set_at": datetime.now(timezone.utc).isoformat(),
        "set_from_report": str(report_path),
    }
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    print(f"[execution_census] baseline set to {baseline['finding_count']} findings -> {BASELINE_FILE}")
    return 0


# ---------------------------------------------------------------------------
# stability-check
# ---------------------------------------------------------------------------

def cmd_stability_check(args: argparse.Namespace) -> int:
    """Runs one world twice under coverage and diffs the executed-arc sets.

    Per §7.2 of the design doc: this census depends on
    TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2's deferred kernel wall-clock
    determinism fix. Before any census report is trusted, this check must report STABLE.
    """
    import coverage as coverage_mod

    data_a = DATA_DIR / ".coverage.stability_a"
    data_b = DATA_DIR / ".coverage.stability_b"
    for p in (data_a, data_b):
        if p.exists():
            p.unlink()

    ok_a = _run_one_world_under_coverage(args.world, args.seed, args.ticks, data_a)
    ok_b = _run_one_world_under_coverage(args.world, args.seed, args.ticks, data_b)
    if not (ok_a and ok_b):
        print("[execution_census] STABILITY: UNKNOWN -- one or both runs failed to complete", file=sys.stderr)
        return 1

    cov_a = coverage_mod.Coverage(data_file=str(data_a), branch=True, source=COVERAGE_SOURCES)
    cov_a.load()
    cov_b = coverage_mod.Coverage(data_file=str(data_b), branch=True, source=COVERAGE_SOURCES)
    cov_b.load()

    files = sorted(set(cov_a.get_data().measured_files()) | set(cov_b.get_data().measured_files()))
    diffs = 0
    for filename in files:
        arcs_a = set(cov_a.get_data().arcs(filename) or [])
        arcs_b = set(cov_b.get_data().arcs(filename) or [])
        if arcs_a != arcs_b:
            diffs += 1
            if args.verbose:
                print(f"  DIFF in {filename}: only-in-run-A={arcs_a - arcs_b} only-in-run-B={arcs_b - arcs_a}")

    if diffs == 0:
        print(f"STABILITY: STABLE -- identical branch-arc coverage across 2 runs of '{args.world}' "
              f"(seed {args.seed}, {args.ticks} ticks)")
        return 0
    else:
        print(f"STABILITY: UNSTABLE -- {diffs} file(s) had differing branch-arc coverage across 2 "
              f"identical runs. See TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 "
              f"(kernel wall-clock throttle non-determinism). Census results are NOT yet "
              f"trustworthy until this is resolved or worked around.", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_unit = sub.add_parser("unit-baseline", help="Run the unit/integration suite under branch coverage")
    p_unit.set_defaults(func=cmd_unit_baseline)

    p_corpus = sub.add_parser("corpus-run", help="Run corpus world(s) under branch coverage")
    p_corpus.add_argument("--worlds", default=None, help="Comma-separated world names (default: every world in corpus_registry.yaml)")
    p_corpus.add_argument("--seed", type=int, default=42)
    p_corpus.add_argument("--ticks", type=int, default=300)
    p_corpus.set_defaults(func=cmd_corpus_run)

    p_report = sub.add_parser("report", help="Diff corpus coverage against the unit baseline")
    p_report.add_argument("--output", default=None)
    p_report.add_argument("--max-print", type=int, default=30)
    p_report.set_defaults(func=cmd_report)

    p_baseline = sub.add_parser("bootstrap-baseline", help="Set the ratchet baseline from the latest report (run once, deliberately, after human triage)")
    p_baseline.add_argument("--report", default=None)
    p_baseline.set_defaults(func=cmd_bootstrap_baseline)

    p_stab = sub.add_parser("stability-check", help="Run one world twice and diff branch-arc coverage")
    p_stab.add_argument("--world", required=True)
    p_stab.add_argument("--seed", type=int, default=42)
    p_stab.add_argument("--ticks", type=int, default=300)
    p_stab.add_argument("--verbose", action="store_true")
    p_stab.set_defaults(func=cmd_stability_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
