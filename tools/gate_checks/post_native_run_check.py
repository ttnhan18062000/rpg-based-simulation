#!/usr/bin/env python3
"""Orchestrator-side re-run of the static gates after a native Workflow run returns
(TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP).

A native implement-ticket run has no shell, so each gate result reaches the script as an agent's
report, and an agent that wants to can forge it (stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-
ATTESTATION-DESIGN/design.md). The top-level session has a shell: it runs this one command after the
run returns and before committing. It re-derives three results itself and trusts none of the run's own
gate verdicts:

  1. done_checker_static.py   Finalize conditions (migration, ticket location, one working_log row,
                              REGISTRY regenerated) and, for a ticket still in inprogress/, the precheck
  2. validate_frontmatter.py  the ticket's frontmatter
  3. ticket_field_values.py   the ticket's Tier / Priority / Status body fields

Read-only: runs the existing checkers, writes nothing. Exit 0 only if all three pass; non-zero names
the failing check. Usage: python3 tools/gate_checks/post_native_run_check.py --ticket-id TCK-...
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TICKET_DIRS = ("inprogress", "done")


def find_ticket(ticket_id, repo=REPO):
    for sub in TICKET_DIRS:
        p = repo / "tickets" / sub / f"{ticket_id}.md"
        if p.exists():
            return p
    return None


def build_checks(ticket_id, ticket_path, repo=REPO):
    py = sys.executable
    rel = str(ticket_path.relative_to(repo))
    return [
        ("done_checker_static", [py, "tools/gate_checks/done_checker_static.py", "--ticket-id", ticket_id]),
        ("validate_frontmatter", [py, "tools/validate_frontmatter.py", rel]),
        ("ticket_field_values", [py, "tools/ticket_field_values.py", rel]),
    ]


def run(ticket_id, repo=REPO, out=print):
    ticket = find_ticket(ticket_id, repo)
    if ticket is None:
        out(f"FAIL ticket_location: no tickets/inprogress|done/{ticket_id}.md")
        return 1
    failed = []
    for name, cmd in build_checks(ticket_id, ticket, repo):
        proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
        status = "PASS" if proc.returncode == 0 else "FAIL"
        out(f"{status} {name}")
        if proc.returncode != 0:
            failed.append(name)
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
            for line in tail:
                out(f"    {line}")
    out(f"RESULT: {'FAIL (' + ', '.join(failed) + ')' if failed else 'PASS'} for {ticket_id}")
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ticket-id", required=True)
    args = ap.parse_args(argv)
    return run(args.ticket_id)


if __name__ == "__main__":
    sys.exit(main())
