#!/usr/bin/env python3
"""Read-only audit: does every tickets/done/ ticket have at least one agent-monitoring
runs.jsonl record? (TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT)

Built after TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION found 2 DONE tickets
(TCK-20260802-CODEX-PILOT-ENTRYPOINT, TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND) with zero
runs.jsonl records despite real Completion Summaries — an apparent violation of CLAUDE.md's own
Hard Rule that every implement-ticket workflow run must record a run entry. This script answers
whether that's isolated to those 2 tickets or reflects a broader gap.

Deliberately does NOT reuse tag_report.py's collect_completed_tickets() — that function filters to
tag-taxonomy-cutoff-dated, non-empty-tags tickets for its own retro-reporting purpose, which would
silently exclude older/untagged real tickets from this audit. Walks tickets/done/ directly instead,
reusing only the genuinely-shared primitives (extract_frontmatter, _load_runs_and_events).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import RUNS_FILE, load_jsonl  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_frontmatter import extract_frontmatter  # noqa: E402


def _collect_done_ticket_ids(done_dir: Path) -> tuple:
    """Returns (ticket_ids, unparseable) — every real ticket_id found under tickets/done/
    (recursive), and a list of (rel_path, reason) for files that couldn't be resolved to a
    ticket_id at all (never silently dropped from the audit)."""
    ticket_ids = []
    unparseable = []

    if not done_dir.is_dir():
        return ticket_ids, unparseable

    for md_file in sorted(done_dir.rglob("*.md")):
        if md_file.name in ("SEQUENCE.md", "README.md"):
            continue
        rel_path = str(md_file.relative_to(done_dir.parent.parent))
        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError as exc:
            unparseable.append((rel_path, f"unparseable frontmatter: {exc}"))
            continue

        ticket_id = fm.get("ticket_id") if fm else None
        if not ticket_id:
            # Legacy/no-frontmatter tickets fall back to the filename stem — real tickets this
            # old still deserve an audit answer, not a silent skip.
            ticket_id = md_file.stem
        ticket_ids.append((ticket_id, rel_path))

    return ticket_ids, unparseable


def build_coverage_section(done_dir: Path = Path("tickets/done")) -> dict:
    ticket_entries, unparseable = _collect_done_ticket_ids(done_dir)
    # Deliberately reads runs.jsonl directly rather than through generate_retro's
    # _load_runs_and_events() SQLite-index path: that index is only rebuilt when *missing*, not
    # when stale, and this audit's whole purpose is checking coverage for tickets that may have
    # just been recorded seconds ago — a stale index would false-positive them as "missing"
    # (caught during this ticket's own Test phase: TCK-20260805-COMBAT-SKILL and several other
    # same-session tickets, confirmed present in the real runs.jsonl file, were wrongly reported
    # missing before this fix).
    runs = load_jsonl(RUNS_FILE)
    run_ids_present = {r.get("run_id") for r in runs if r.get("run_id")}

    covered = []
    missing = []
    for ticket_id, rel_path in ticket_entries:
        if ticket_id in run_ids_present:
            covered.append(ticket_id)
        else:
            missing.append({"ticket_id": ticket_id, "path": rel_path})

    return {
        "total_done_tickets_checked": len(ticket_entries),
        "covered_count": len(covered),
        "missing": missing,
        "missing_count": len(missing),
        "unparseable": [{"path": p, "reason": r} for p, r in unparseable],
        "unparseable_count": len(unparseable),
        "derivation": (
            "Walks tickets/done/ recursively (excluding SEQUENCE.md/README.md index files), "
            "extracts ticket_id from each file's frontmatter via extract_frontmatter() "
            "(falling back to the filename stem for legacy/no-frontmatter tickets, never a "
            "silent skip), and checks whether that ticket_id appears as a run_id in any real "
            "agent-monitoring/runs.jsonl record (via generate_retro._load_runs_and_events()). "
            "A ticket with zero matching run_id records is reported in `missing`, regardless of "
            "tier — confirmed via real corpus inspection that epic-tier tickets' runs.jsonl "
            "records also use run_id == ticket_id, no special-casing needed. Does not check "
            "events.jsonl coverage (a run record with zero events is a different, narrower "
            "question — CLAUDE.md's Hard Rule requires 'a run entry AND at least one event "
            "entry', but a ticket with a run record and zero events is a strictly smaller gap "
            "than a ticket with no run record at all, which is what caused the original finding "
            "this audit investigates)."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="optional path to also write the JSON output to")
    args = parser.parse_args()

    report = build_coverage_section()
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
