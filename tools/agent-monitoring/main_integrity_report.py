#!/usr/bin/env python3
"""Report-only integrity check of a git ref (default `origin/main`), never the working tree
(TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT).

Per-ticket checks (the done-checker) cannot see problems that only exist across the merged tree:
working-log rows landing in another checkout's CSV, evidence written as a gitignored `.json` that
never reached the remote, shards left behind for a finished week. This reads the ref through
`git ls-tree` / `git show` (the `delivery_cost_measurement.py --ref` pattern) and labels the output
as a snapshot of that ref and SHA: a closed week can still receive late shards, so a count here is
as of that commit, not final.

Checks (each finding names its ticket or path):
  working_log      every closed ticket (tickets/done/**/TCK-*.md) has exactly one working-log row,
                   counting `tickets/working_log.csv` plus any pending `*.working_log.jsonl` shard
  shards           no per-batch `<id>.{runs,events,tools,working_log}.jsonl` shard left for a finished ISO week
  cited_evidence   every backticked `stored_artifacts/...` path a closed ticket cites exists at the ref
  duplicate_runs   `duplicate_run_record_check.check_duplicate_run_records` over the ref's run rows
  event_seq        `event_seq_integrity_check.find_seq_duplicates_and_gaps` over the ref's event rows

Report-only: prints findings, exits 0 unless `--strict` is passed (local use). Repairs nothing.
`--since-date YYYYMMDD` limits the ticket-based checks to tickets whose id date is on or after it.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "gate_checks"))

REPO_ROOT = _HERE.parent.parent
_TICKET_RE = re.compile(r"^tickets/done/(?:[^/]+/)?(TCK-(\d{8})-[A-Z0-9-]+)\.md$")
_SHARD_RE = re.compile(r"^agent-monitoring/data/(\d{4}-W\d{2})/[^/]+\.(runs|events|tools|working_log)\.jsonl$")
_CITE_RE = re.compile(r"`(stored_artifacts/[^`\s]+)`")
_KINDS = ("runs", "events")


def _git(repo_root, *args, text=True):
    return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=text, check=True).stdout


class RefReader:
    """Everything is read from one resolved commit; the working tree is never opened."""

    def __init__(self, ref: str, repo_root: Path = REPO_ROOT):
        self.repo_root = Path(repo_root)
        self.ref = ref
        self.sha = _git(self.repo_root, "rev-parse", ref).strip()
        self.paths = set(_git(self.repo_root, "ls-tree", "-r", "--name-only", self.sha).splitlines())

    def show(self, path: str) -> str:
        return _git(self.repo_root, "show", f"{self.sha}:{path}")

    def exists(self, path: str) -> bool:
        path = path.rstrip("/")
        return path in self.paths or any(p.startswith(path + "/") for p in self.paths)


def _closed_tickets(reader: RefReader, since_date: str | None):
    for p in sorted(reader.paths):
        m = _TICKET_RE.match(p)
        if m and (not since_date or m.group(2) >= since_date):
            yield m.group(1), p


def check_working_log(reader: RefReader, since_date: str | None) -> list[str]:
    counts: Counter = Counter()
    if "tickets/working_log.csv" in reader.paths:
        for row in csv.DictReader(io.StringIO(reader.show("tickets/working_log.csv"))):
            counts[row.get("ticket_id", "")] += 1
    for p in reader.paths:
        m = _SHARD_RE.match(p)
        if m and m.group(2) == "working_log":
            for line in reader.show(p).splitlines():
                if line.strip():
                    counts[json.loads(line).get("ticket_id", "")] += 1
    findings = []
    for tid, path in _closed_tickets(reader, since_date):
        if counts[tid] != 1:
            findings.append(f"{tid}: {counts[tid]} working-log row(s) ({path})")
    return findings


def check_leftover_shards(reader: RefReader, today: date) -> list[str]:
    from week_close import is_finished
    findings = []
    for p in sorted(reader.paths):
        m = _SHARD_RE.match(p)
        if m and is_finished(m.group(1), today):
            findings.append(f"{p}: per-batch shard left for finished week {m.group(1)}")
    return findings


def check_cited_evidence(reader: RefReader, since_date: str | None) -> list[str]:
    findings = []
    for tid, path in _closed_tickets(reader, since_date):
        for cited in sorted(set(_CITE_RE.findall(reader.show(path)))):
            cited = cited.rstrip(".,;:)")
            if "..." in cited or any(ch in cited for ch in "*<>{}"):
                continue  # a glob or placeholder, not a concrete path
            if not reader.exists(cited):
                findings.append(f"{tid}: cites {cited}, which does not exist at {reader.sha[:9]}")
    return findings


def _load_rows(reader: RefReader, kind: str) -> list[dict]:
    rows = []
    for p in sorted(reader.paths):
        if re.match(rf"^agent-monitoring/data/[^/]+/(?:[^/]+\.)?{kind}\.jsonl$", p):
            for line in reader.show(p).splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows


def check_duplicate_runs(reader: RefReader) -> list[str]:
    from duplicate_run_record_check import check_duplicate_run_records
    return [r["evidence"] for r in check_duplicate_run_records(runs=_load_rows(reader, "runs")) if r["status"] != "PASS"]


def check_event_seq(reader: RefReader) -> list[str]:
    from event_seq_integrity_check import find_seq_duplicates_and_gaps
    dups, gaps = find_seq_duplicates_and_gaps(events=_load_rows(reader, "events"))
    out = [f"{rid}: duplicate event seq" for rid in sorted(dups)]
    out += [f"{rid}: event seq gap" for rid in sorted(gaps)]
    return out


def build_report(ref: str, repo_root: Path = REPO_ROOT, today: date | None = None, since_date: str | None = None) -> dict:
    reader = RefReader(ref, repo_root)
    today = today or date.today()
    findings = {
        "working_log": check_working_log(reader, since_date),
        "shards": check_leftover_shards(reader, today),
        "cited_evidence": check_cited_evidence(reader, since_date),
        "duplicate_runs": check_duplicate_runs(reader),
        "event_seq": check_event_seq(reader),
    }
    return {"ref": ref, "sha": reader.sha, "since_date": since_date, "findings": findings,
            "total": sum(len(v) for v in findings.values())}


def render(report: dict, limit: int) -> str:
    lines = [f"Snapshot of {report['ref']} @ {report['sha']} (not the working tree; late shards can still arrive)"]
    if report["since_date"]:
        lines.append(f"Ticket checks limited to ticket ids dated on or after {report['since_date']}")
    for name, items in report["findings"].items():
        lines.append(f"{name}: {len(items)} finding(s)")
        for item in items[:limit]:
            lines.append(f"  - {item}")
        if len(items) > limit:
            lines.append(f"  ... {len(items) - limit} more (use --limit or --json)")
    lines.append("RESULT: clean" if not report["total"] else f"RESULT: {report['total']} finding(s) (report only)")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Report-only integrity check of a git ref's monitoring and ticket data.")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--since-date", default=None, help="YYYYMMDD; limit ticket-based checks to ticket ids on/after it")
    ap.add_argument("--today", default=None, help="Override today's date, YYYY-MM-DD (testing).")
    ap.add_argument("--limit", type=int, default=20, help="Max findings printed per check.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when any finding exists (local use only).")
    args = ap.parse_args(argv)
    report = build_report(args.ref, REPO_ROOT, date.fromisoformat(args.today) if args.today else None, args.since_date)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render(report, args.limit))
    return 1 if (args.strict and report["total"]) else 0


if __name__ == "__main__":
    sys.exit(main())
