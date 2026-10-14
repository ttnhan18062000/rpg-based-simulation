#!/usr/bin/env python3
"""Short command lines for the attested gate sites of implement-ticket.js (TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY).

A native gate command is handed to a dispatched agent as base64 and copied back out of it, so a long command is a
long lossy copy (run wf_e2dc6921-bdd lost the tail of a 900-character inline ``python3 -c`` and died at
``test_scope_coverage``). Each sub-command here replaces one inline-Python site with a few dozen characters and prints
the same marker line the script already parses, so the parsing code in the workflow is unchanged.

The changed-file list no longer travels through the agent. The list-carrying sites (``doc_staleness``,
``test_scope``, ``p0_scan``, ``parity_xref``) take ``--start-sha`` (the run's start commit, captured at Scope) and
derive the list themselves: ``git diff --name-only <start_sha>`` (working tree against that commit) plus untracked
files, minus the paths the run writes for bookkeeping (``EXCLUDED_PREFIXES``). ``test_scope`` also prints
``DERIVED_FILES_JSON:`` so the workflow can show, as an advisory, any file the implementer left out of its own report.

usage: gate_cli.py <site> [options]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_TOOLS = str(Path(__file__).resolve().parents[1])
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

# Paths a run writes as bookkeeping, never as the ticket's own change. A path is excluded when it starts with one of
# these, or contains one of the fragments.
EXCLUDED_PREFIXES = (
    "agent-working/agent-monitoring/",  # run, event, tool and gate-verdict shards
    "data/runs/",                       # simulation run output
    "reports/release_proof/",           # release-proof output
    "graphify-out/",                    # the knowledge graph
    ".claude/current_run",              # the per-session run sidecar
)
EXCLUDED_FRAGMENTS = ("/__pycache__/", "/.pytest_cache/")


def is_excluded(path: str) -> bool:
    return path.startswith(EXCLUDED_PREFIXES) or any(fragment in "/" + path for fragment in EXCLUDED_FRAGMENTS)


def _git(*args: str) -> list[str]:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return [line for line in done.stdout.splitlines() if line.strip()]


def derive_changed_files(start_sha: str) -> list[str]:
    """Tracked changes since ``start_sha`` (working tree included) plus untracked files, bookkeeping removed, sorted."""
    paths = set(_git("diff", "--name-only", start_sha, "--")) | set(_git("ls-files", "--others", "--exclude-standard"))
    return sorted(p for p in paths if not is_excluded(p))


def _touched_ledger_lines() -> list[str]:
    return _git("status", "--porcelain", "--", "docs/parity_ledger/")


def site_tag_check(args: argparse.Namespace) -> None:
    from tag_registry import check_tags_registered
    print("TAG_CHECK_JSON:" + json.dumps(check_tags_registered(args.tags)))


def site_plan_unresolved(args: argparse.Namespace) -> None:
    from gate_checks.plan_gate_static import plan_has_unresolved_questions_heading
    path = f"agent-working/staging_artifacts/{args.ticket_id}/plan.md"
    print("UNRESOLVED_CHECK_JSON:" + json.dumps(plan_has_unresolved_questions_heading(path)))


def site_doc_staleness(args: argparse.Namespace) -> None:
    from gate_checks.doc_staleness_check import check_doc_staleness
    files = derive_changed_files(args.start_sha)
    print("MARKER:" + json.dumps(check_doc_staleness(files, args.behavior_changed == "true", args.docs_to_update)))


def site_test_scope(args: argparse.Namespace) -> None:
    from gate_checks.test_scope_coverage_static import check_test_scope_coverage
    files = derive_changed_files(args.start_sha)
    print("DERIVED_FILES_JSON:" + json.dumps(files))
    print("TEST_SCOPE_CHECK_JSON:" + json.dumps(check_test_scope_coverage(files, args.pytest_command)))


def site_data_runs_cleanup(args: argparse.Namespace) -> None:
    from gate_checks.done_checker_static import clean_data_runs_early
    status, evidence = clean_data_runs_early(args.start_ts or None)
    print(status + "|" + evidence)


def site_p0_scan(args: argparse.Namespace) -> None:
    from parity_ledger_scan import find_p0_intersection
    hits = find_p0_intersection(derive_changed_files(args.start_sha))
    print("P0_INTERSECTION_FOUND" if hits else "P0_NO_INTERSECTION")
    if hits:
        print(hits)


def site_parity_xref(args: argparse.Namespace) -> None:
    from gate_checks.parity_updater_static import cross_reference_touched
    results = cross_reference_touched(derive_changed_files(args.start_sha), _touched_ledger_lines())
    print("PARITY_CHECK_JSON:" + json.dumps(results))


def site_finalize_selfcheck(args: argparse.Namespace) -> None:
    from gate_checks.done_checker_static import run_finalize_selfcheck
    print("FINALIZE_CHECK_JSON:" + json.dumps(run_finalize_selfcheck(args.ticket_id, args.tier)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="site", required=True)

    p = sub.add_parser("tag_check")
    p.add_argument("tags", nargs="*")
    p.set_defaults(run=site_tag_check)

    p = sub.add_parser("plan_unresolved")
    p.add_argument("--ticket-id", required=True)
    p.set_defaults(run=site_plan_unresolved)

    p = sub.add_parser("doc_staleness")
    p.add_argument("--start-sha", required=True)
    p.add_argument("--behavior-changed", choices=("true", "false"), required=True)
    p.add_argument("--docs-to-update", nargs="*", default=[])
    p.set_defaults(run=site_doc_staleness)

    p = sub.add_parser("test_scope")
    p.add_argument("--start-sha", required=True)
    p.add_argument("--pytest-command", required=True)
    p.set_defaults(run=site_test_scope)

    p = sub.add_parser("data_runs_cleanup")
    p.add_argument("--start-ts", default="")
    p.set_defaults(run=site_data_runs_cleanup)

    p = sub.add_parser("p0_scan")
    p.add_argument("--start-sha", required=True)
    p.set_defaults(run=site_p0_scan)

    p = sub.add_parser("parity_xref")
    p.add_argument("--start-sha", required=True)
    p.set_defaults(run=site_parity_xref)

    p = sub.add_parser("finalize_selfcheck")
    p.add_argument("--ticket-id", required=True)
    p.add_argument("--tier", required=True)
    p.set_defaults(run=site_finalize_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
