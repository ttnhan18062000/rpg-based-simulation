#!/usr/bin/env python3
"""Folds per-ticket `<TCK-ID>.{runs,events,tools}.jsonl` shard files back into the canonical
per-week `runs.jsonl`/`events.jsonl`/`tools.jsonl` shape every existing reader (`validate.py`,
`query.py`, `generate_retro.py`'s own aggregation, `tools/gate_checks/*`) already expects
(TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE).

Per-ticket files exist so two different tickets closing on two different branches can never
collide on a git diff hunk, even under a GitHub squash-merge (the one gap `.gitattributes`'
`merge=union` doesn't cover — it only engages for a real git merge). Consolidation is the sync
point that keeps every consumer's read contract unchanged: nothing downstream needs to know
per-ticket files exist at all.

**Idempotent by delete, not by a tracked manifest.** A per-ticket file's lines are appended to the
canonical file, and the per-ticket file is deleted only *after* that append succeeds — so a second
run finds nothing left to reprocess. A manifest file recording "already consolidated" would itself
be new, non-append-only state with its own merge-conflict exposure, reintroducing at a smaller
scale the exact problem this module exists to remove. The disclosed residual risk (see this
ticket's own investigation.md) is a crash between a successful canonical write and the delete,
which could fold one file's lines in twice on the next run — tolerable for `tools.jsonl` (an
advisory-only row-count signal) and already covered for `runs.jsonl`/`events.jsonl` by the
existing `duplicate_run_record_check.py`/`event_seq_integrity_check.py` anomaly detectors, which
exist precisely to surface this class of issue rather than let it corrupt silently.

**Scope note**: `tickets/working_log.csv` is NOT consolidated here — a disclosed scope reduction,
not an oversight. See this ticket's own investigation.md for why (a synchronous done-checker
dependency this ticket does not touch).

Never raises to its own caller — `main()`'s only failure mode is a genuine internal error, matching
every other tool in this module's fail-open convention (monitoring write/consolidation failure
must never fail the workflow it's measuring).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_lines  # noqa: E402

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "agent-monitoring" / "data"
JSONL_KINDS = ("runs", "events", "tools")


def consolidate_jsonl_kind(week_dir: Path, kind: str) -> int:
    """Folds every `<TCK-ID>.<kind>.jsonl` in `week_dir` into the canonical `<kind>.jsonl`.
    Returns the count of per-ticket files consolidated (0 if none found or the canonical write
    failed -- in the failure case, every per-ticket file is left in place for a future retry)."""
    canonical = week_dir / f"{kind}.jsonl"
    per_ticket_files = sorted(week_dir.glob(f"*.{kind}.jsonl"))
    if not per_ticket_files:
        return 0

    new_lines = []
    for f in per_ticket_files:
        lines = [line for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
        new_lines.extend(lines)

    if new_lines:
        ok = write_lines(canonical, new_lines)
        if not ok:
            return 0  # leave every per-ticket file in place; nothing consolidated this run

    for f in per_ticket_files:
        f.unlink()
    return len(per_ticket_files)


def consolidate_week(week_dir: Path) -> dict:
    return {kind: consolidate_jsonl_kind(week_dir, kind) for kind in JSONL_KINDS}


def consolidate_all(data_dir: Path = DEFAULT_DATA_DIR) -> dict:
    if not data_dir.exists():
        return {}
    results = {}
    for week_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        week_result = consolidate_week(week_dir)
        if any(week_result.values()):
            results[week_dir.name] = week_result
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fold per-ticket agent-monitoring shard files into the canonical per-week "
        "runs.jsonl/events.jsonl/tools.jsonl. Read-only for the working tree except appending to "
        "and deleting already-folded-in per-ticket files; never touches consumer read contracts."
    )
    parser.add_argument("--data-dir", default=None, help="Override agent-monitoring/data/ (mainly for testing).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
        result = consolidate_all(data_dir)
    except Exception as exc:  # noqa: BLE001 - the one deliberate non-zero-exit path
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if not result:
            print("Nothing to consolidate.")
        for week, counts in result.items():
            total = sum(counts.values())
            print(f"{week}: consolidated {total} per-ticket file(s) ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
