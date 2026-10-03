"""Report-only: which changed test files the Architecture-Verify reviewer has a Read row for
(TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS).

The reviewer's `test_quality_findings` is only evidence if it actually read the changed test
files; an empty list from a reviewer that never opened them looks identical to a clean read.
This reads the tools monitoring shards (`agent-monitoring/data/**/tools.jsonl`) and prints, for
each test file the branch changed, whether a `Read` row attributed to the Architecture-Verify
phase of this ticket's run names it.

Nothing is gated, written or changed: no schema field, no prompt change, always exit 0 unless
the arguments are unusable. A reader must keep in mind the limits below, which is why the output
has FOUR classes and never says "not read" when it cannot know.

Output classes per changed test file
    READ              a Read row of the Architecture-Verify phase names exactly this file.
    POSSIBLY-READ     only Read rows whose recorded path was cut at 120 characters could be this
                      file (see limit 2); the cut path is consistent with it, nothing more.
    NOT-READ          the phase HAS attributed Read rows, none names this file, and no cut row is
                      consistent with it.
    UNATTRIBUTED      the phase has no attributed rows at all (see limit 1), so "not read" cannot be
                      said; the header counts Read rows without a run_id inside the phase's time
                      window as the candidates.

Limits (do not over-read the output)
1. Attribution depends on the orchestrator writing the run sidecar BEFORE the dispatch
   (`writeSidecar`). On the hand-executed skill path that write is the most commonly forgotten
   step, and an unattributed row has run_id null. Those rows are counted, never assigned to a file.
2. `post_tool_hook.py` records a Read row's `input_summary` as the ABSOLUTE `file_path` cut to 120
   characters. A long worktree prefix therefore cuts many test paths (measured on 2026-10-02: 36% of
   all Read rows). A cut row is matched only as "possibly read": its visible tail must be a prefix of
   the test file's repo-relative path and reach into the tests/ directory.
3. Only the Read tool leaves a Read row. A reviewer that read a file through Bash (`cat`, `grep`,
   `sed -n`) leaves a Bash row, so NOT-READ means "no Read-tool row", not "never looked at".
5. The run sidecar (`.claude/current_run`) is shared across concurrent sessions, so a row tagged with this ticket's
   run_id could in principle come from another session. READ therefore means "a Read row tagged with this run_id
   and phase names the file", not proof that it came from this reviewer run. NOT-READ on its own never decides
   anything: it means only "no Read-tool row", and the reviewer's own output still has to show it read the tests.
4. Only the production reviewer (`agent == architecture-reviewer`) counts; the advisory shadow
   reviewer's rows (`architecture-reviewer-shadow`) are ignored.

Usage:
    python3 tools/agent-monitoring/arch_verify_read_check.py --ticket-id TCK-... [--base-ref origin/main]
        [--data-root agent-monitoring/data] [--json]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from monitoring_shard_paths import shard_paths  # noqa: E402

PHASE = "Architecture-Verify"
PRODUCTION_AGENT = "architecture-reviewer"
CUT = 120  # post_tool_hook._input_summary's cap for a Read's file_path


def changed_test_files(base_ref: str, run=subprocess.run) -> list[str]:
    """Test files the branch added or modified. Deleted files are excluded (--diff-filter=d): a deleted file cannot be
    read, so it would be a false NOT-READ; a renamed file is listed under its new path."""
    out = run(["git", "diff", "--name-only", "--diff-filter=d", f"{base_ref}...HEAD"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git diff failed: {out.stderr.strip()}")
    return sorted({ln.strip() for ln in out.stdout.splitlines() if ln.strip().startswith("tests/")})


def _rows(data_root: Path, kind: str):
    for path in shard_paths(data_root, kind):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def _matches_exact(summary: str, rel_path: str) -> bool:
    return len(summary) < CUT and (summary == rel_path or summary.endswith("/" + rel_path))


def _matches_cut(summary: str, rel_path: str) -> bool:
    """A path cut at CUT chars: some suffix of it, starting after a '/', is a non-trivial prefix of rel_path."""
    if len(summary) < CUT:
        return False
    for i, ch in enumerate(summary):
        if ch == "/":
            tail = summary[i + 1:]
            if len(tail) >= len("tests/") + 1 and rel_path.startswith(tail):
                return True
    return False


def phase_window(data_root: Path, ticket_id: str):
    """(start_ts, end_ts) of the Architecture-Verify phase from the events rows: its own ts to the next
    event's ts. Either may be None when the events are missing."""
    events = sorted((e for e in _rows(data_root, "events") if e.get("run_id") == ticket_id), key=lambda e: e.get("seq") or 0)
    for i, e in enumerate(events):
        if e.get("phase") == PHASE and e.get("agent") == PRODUCTION_AGENT:
            nxt = events[i + 1].get("ts") if i + 1 < len(events) else None
            return e.get("ts"), nxt
    return None, None


def check(ticket_id: str, tests: list[str], data_root: Path) -> dict:
    attributed = []
    unattributed_reads = []
    start, end = phase_window(data_root, ticket_id)
    for r in _rows(data_root, "tools"):
        if r.get("tool") != "Read":
            continue
        if r.get("run_id") == ticket_id and r.get("phase") == PHASE and r.get("agent") == PRODUCTION_AGENT:
            attributed.append(r.get("input_summary") or "")
        elif not r.get("run_id") and start and (r.get("ts") or "") >= start and (not end or (r.get("ts") or "") < end):
            unattributed_reads.append(r.get("input_summary") or "")
    files = {}
    for t in tests:
        if not attributed:
            files[t] = "UNATTRIBUTED"
        elif any(_matches_exact(s, t) for s in attributed):
            files[t] = "READ"
        elif any(_matches_cut(s, t) for s in attributed):
            files[t] = "POSSIBLY-READ"
        else:
            files[t] = "NOT-READ"
    return {
        "ticket_id": ticket_id,
        "phase_window": [start, end],
        "attributed_read_rows": len(attributed),
        "attributed_rows_cut_at_120": sum(1 for s in attributed if len(s) >= CUT),
        "unattributed_read_rows_in_window": len(unattributed_reads),
        "files": files,
    }


def render(result: dict) -> str:
    lines = [f"Architecture-Verify Read rows for {result['ticket_id']} (report only; see the module docstring for the limits)"]
    lines.append(f"  attributed Read rows: {result['attributed_read_rows']} ({result['attributed_rows_cut_at_120']} with the path cut at {CUT} chars)")
    if result["attributed_read_rows"] == 0:
        lines.append(
            "  no row is attributed to this phase: the sidecar was probably missing or the run id differs; "
            f"{result['unattributed_read_rows_in_window']} Read row(s) with no run_id fall inside the phase's time window "
            f"{result['phase_window']} and are the only candidates. 'Not read' cannot be said."
        )
    for path, cls in result["files"].items():
        lines.append(f"  {cls:<14} {path}")
    if not result["files"]:
        lines.append("  (the branch changes no file under tests/)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--data-root", default="agent-monitoring/data")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        tests = changed_test_files(args.base_ref)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    result = check(args.ticket_id, tests, Path(args.data_root))
    print(json.dumps(result) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
