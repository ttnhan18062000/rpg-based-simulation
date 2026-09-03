#!/usr/bin/env python3
"""One-time migration: consolidate the 3 legacy agent-monitoring physical shapes
(`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
`agent-monitoring/tools/tools-YYYY-Www.jsonl`) into the unified
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout.

TCK-20260903-MONITORING-DATA-MIGRATION (child 2 of the monitoring unified-weekly-data
epic). Generalizes `migrate_tools_shards.py` (TCK-20260902-MONITORING-SHARD-MIGRATION)
from 1 source to 3, expressing 2 genuinely different strategies as 2 distinct code
paths rather than one forced-uniform loop:

- `runs`/`events` are each one monolithic file that needs per-line re-bucketing by a
  field-priority-ordered timestamp lookup on each record (`bucket_lines_by_week_multi_
  field`), because each record was written in the past and the field it carries is the
  only correct signal for which week it belongs to.
- `tools` is a set of already-correctly-bucketed shard files (the prior epic's own
  migration already did the per-line `ts`-based bucketing once) that needs pure
  filename-based relocation (`relocate_tools_shards`), with zero per-line
  re-bucketing — re-parsing content here would be redundant and a needless second
  opportunity to introduce a bucketing bug.

Both paths converge on the same reused rename-aside + single-`write_lines()`-call
primitive (`write_week_bucket`, generalized to take a `source` + `data_dir` instead of
a hardcoded `shard_dir`/`tools-` filename prefix), and the same reused full-corpus
(non-sampled) verification primitive (`verify_migration`, generalized the same way),
run independently per source.

Verification must pass for all 3 sources, captured in the ticket's Test Summary,
strictly before the `git rm` of any of the 3 legacy paths. This script never calls
`git rm` itself — that is a separate, explicit, human-reviewed step.

Genuinely one-time: no Make target, no cron/scheduled re-run mechanism. Re-running it
after all 3 legacy paths have been retired is a no-op failure (every source absent).

Route-only, content-preserving: this script never repairs or normalizes malformed/
off-schema historical lines. It only routes them to the correct week bucket by
whatever timestamp-like field they carry (per source's own field-priority list), or to
the shared `unknown-week` fallback bucket if none is usable.

Cross-worktree `git rm` merge-conflict runbook (extends TCK-20260902-MONITORING-SHARD-
MIGRATION decision 5 to all 3 retired paths, per this ticket's own ratified Assumptions
decision): this script's own `git rm` step (run separately, once this script's
verification passes) is a one-time, irreversible-from-the-working-tree removal of
`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and the entire
`agent-monitoring/tools/` directory. Any other worktree/branch that has not yet merged
past this ticket's commit and is still appending to its own local copy of any of these
3 paths will produce a `CONFLICT (modify/delete)` when it later merges past this point.
`merge=union` does NOT apply to modify/delete conflicts. Resolution: take the deletion
side (`git rm <path>` at the conflict) for each of the 3 paths explicitly, and if that
other branch's interim rows need to be preserved, re-run this same script against that
branch's pre-merge copy of the file(s) (or a targeted subset of new lines) before
finalizing the merge, rather than resurrecting any of the 3 legacy shapes.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_tools_shards import _parse_ts_to_week, UNKNOWN_WEEK_KEY  # noqa: E402
from writer import write_lines  # noqa: E402

RUNS_FIELD_PRIORITY = [
    "start_ts", "ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]

EVENTS_FIELD_PRIORITY = [
    "ts", "start_ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]


def _target_path_for_week(week_key: str, source: str, data_dir: Path) -> Path:
    return data_dir / week_key / f"{source}.jsonl"


def bucket_lines_by_week_multi_field(lines: list[str], field_priority: list[str]) -> dict[str, list[str]]:
    """Group raw JSONL line strings (no trailing newline) by the ISO week of the first
    usable (present and truthy) field in `field_priority`, checked in order.

    Preserves each line's original relative order within its bucket — a single forward
    pass appending to `dict[key].append(line)`, never re-sorted. Route-only: does not
    repair, coerce, or normalize any line's content.
    """
    buckets: dict[str, list[str]] = {}
    for line in lines:
        record = json.loads(line)
        value = next((record.get(f) for f in field_priority if record.get(f)), None)
        key = UNKNOWN_WEEK_KEY if not value else _parse_ts_to_week(value)
        buckets.setdefault(key, []).append(line)
    return buckets


def relocate_tools_shards(tools_dir: Path) -> dict[str, list[str]]:
    """Relocate already-correctly-bucketed `tools` shard files by parsing the ISO week
    directly out of each shard's filename — no per-line `json.loads()`/re-bucketing.

    Each shard's entire file content becomes one bucket, keyed by the week parsed from
    its own filename (`tools-2026-W24.jsonl` -> `2026-W24`; `tools-unknown-week.jsonl`
    -> `unknown-week`, equal to UNKNOWN_WEEK_KEY by construction).
    """
    buckets: dict[str, list[str]] = {}
    for shard_path in sorted(tools_dir.glob("tools-*.jsonl")):
        week_key = shard_path.stem[len("tools-"):]
        buckets[week_key] = shard_path.read_text().splitlines()
    return buckets


def write_week_bucket(week_key: str, lines: list[str], source: str, data_dir: Path) -> tuple[bool, list[str]]:
    """Append `lines` for one (week, source) bucket into its target file via exactly one
    write_lines() call.

    Returns (ok, live_snapshot) — live_snapshot is the pre-existing content of the
    target file at the moment this bucket was processed (empty list for Case A).

    Case A (target absent or empty): a single direct write_lines() call.
    Case B (target already has live post-cutover content, e.g. the in-progress current
    week): rename the live file aside, build combined = migrated_lines + live_snapshot,
    write it as one single write_lines() call (never two), then reconcile that the new
    file's trailing len(live_snapshot) lines exactly match the pre-migration
    live_snapshot before discarding the backup. Never truncates or overwrites the live
    file directly.
    """
    target_path = _target_path_for_week(week_key, source, data_dir)
    # write_lines()'s internal _acquire_lock() creates the lock file at
    # target_path.parent / "<name>.lock" before write_lines() gets a chance to run its
    # own target_path.parent.mkdir() (that mkdir only runs after the lock is already
    # held) — the parent directory must already exist before the first lock-file
    # os.open() call.
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if not target_path.exists() or target_path.stat().st_size == 0:
        ok = write_lines(target_path, lines)
        return ok, []

    live_snapshot = target_path.read_text().splitlines()
    backup_path = target_path.with_name(target_path.name + ".pre-migration-backup")
    os.replace(target_path, backup_path)

    combined = lines + live_snapshot
    ok = write_lines(target_path, combined)
    if not ok:
        raise RuntimeError(
            f"write_lines() failed writing combined content for {target_path}; "
            f"pre-migration live content preserved at {backup_path} for manual recovery."
        )

    new_lines = target_path.read_text().splitlines()
    tail = new_lines[len(new_lines) - len(live_snapshot):] if live_snapshot else []
    if tail != live_snapshot:
        raise RuntimeError(
            f"Reconciliation failed for {target_path}: pre-existing live rows were not preserved "
            f"intact after migration (expected trailing {len(live_snapshot)} lines to match exactly). "
            f"ABORTING — pre-migration live content preserved at {backup_path} for manual recovery. "
            "Do not proceed to verification or retirement."
        )

    backup_path.unlink()
    return True, live_snapshot


def verify_migration(
    source_lines: list[str],
    buckets: dict[str, list[str]],
    source: str,
    data_dir: Path,
    live_snapshots: dict[str, list[str]],
) -> dict:
    """Full-corpus (not sampled) zero-data-loss verification for one source.

    Re-reads every target file this run touched for this source, confirms: (1) exact
    line-count reconciliation (original_total + explained_delta == migrated_total,
    never approximate); (2) every target file's on-disk content (minus any pre-existing
    live suffix) matches the exact lines this run bucketed for it, byte-for-byte, in
    order; (3) every persisted line still round-trips through json.loads().

    Run once per source with that source's own source_lines/buckets/live_snapshots,
    never combined across sources.
    """
    original_total = len(source_lines)
    migrated_total = 0
    explained_delta = 0
    per_shard_counts: dict[str, int] = {}
    content_mismatches: list[str] = []
    parse_failures: list[str] = []

    for week_key, expected_lines in buckets.items():
        target_path = _target_path_for_week(week_key, source, data_dir)
        actual_lines = target_path.read_text().splitlines()
        per_shard_counts[str(target_path.relative_to(data_dir))] = len(actual_lines)
        migrated_total += len(actual_lines)

        live_snapshot = live_snapshots.get(week_key, [])
        explained_delta += len(live_snapshot)

        if live_snapshot:
            split_at = len(actual_lines) - len(live_snapshot)
            migrated_part = actual_lines[:split_at]
            live_part = actual_lines[split_at:]
            if live_part != live_snapshot:
                content_mismatches.append(
                    f"{target_path}: live suffix does not match pre-migration snapshot"
                )
        else:
            migrated_part = actual_lines

        if migrated_part != expected_lines:
            content_mismatches.append(
                f"{target_path}: migrated content does not match bucketed input "
                f"(expected {len(expected_lines)} lines, found {len(migrated_part)})"
            )

        for line in actual_lines:
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                parse_failures.append(f"{target_path}: {e}")

    reconciles_exactly = migrated_total == (original_total + explained_delta)

    return {
        "original_total": original_total,
        "migrated_total": migrated_total,
        "explained_delta": explained_delta,
        "reconciles_exactly": reconciles_exactly,
        "content_preserved": content_mismatches == [],
        "content_mismatches": content_mismatches,
        "all_lines_parse": parse_failures == [],
        "parse_failures": parse_failures,
        "per_shard_counts": per_shard_counts,
        "week_count": len(buckets),
        "verification_passed": (
            reconciles_exactly and content_mismatches == [] and parse_failures == []
        ),
    }


def _migrate_rebucketed_source(
    source_path: Path, source: str, field_priority: list[str], data_dir: Path
) -> dict:
    """Shared runs/events orchestration sequence: abort-if-missing -> read lines ->
    bucket_lines_by_week_multi_field -> per-week write_week_bucket loop (collecting
    live_snapshots) -> verify_migration.
    """
    if not source_path.exists():
        print(f"ABORT: source file {source_path} does not exist (already migrated?).", file=sys.stderr)
        return {"verification_passed": False, "abort_reason": f"{source_path} missing"}

    source_lines = source_path.read_text().splitlines()
    print(f"[{source}] Read {len(source_lines)} lines from {source_path} at run start.")

    buckets = bucket_lines_by_week_multi_field(source_lines, field_priority)
    print(f"[{source}] Bucketed into {len(buckets)} week(s): {sorted(buckets.keys())}")

    live_snapshots: dict[str, list[str]] = {}
    for week_key in sorted(buckets.keys()):
        lines = buckets[week_key]
        try:
            ok, live_snapshot = write_week_bucket(week_key, lines, source, data_dir)
        except RuntimeError as e:
            print(f"ABORT [{source}]: {e}", file=sys.stderr)
            return {"verification_passed": False, "abort_reason": str(e)}
        if not ok:
            reason = (
                f"write_week_bucket reported failure for {source}/{week_key} "
                "(see agent-monitoring/data/.writer_health.jsonl for diagnostics)."
            )
            print(f"ABORT: {reason}", file=sys.stderr)
            return {"verification_passed": False, "abort_reason": reason}
        if live_snapshot:
            live_snapshots[week_key] = live_snapshot
        print(f"  [{source}] {week_key}: wrote {len(lines)} migrated line(s)" + (
            f", preceding {len(live_snapshot)} pre-existing live line(s)" if live_snapshot else ""
        ))

    return verify_migration(source_lines, buckets, source, data_dir, live_snapshots)


def _migrate_tools_relocation(tools_dir: Path, data_dir: Path) -> dict:
    """`tools` source orchestration: abort-if-missing -> relocate_tools_shards ->
    per-week write_week_bucket loop -> verify_migration. Parallel to
    `_migrate_rebucketed_source` but never calls `bucket_lines_by_week_multi_field`.
    """
    source = "tools"
    if not tools_dir.is_dir():
        print(f"ABORT: source directory {tools_dir} does not exist (already migrated?).", file=sys.stderr)
        return {"verification_passed": False, "abort_reason": f"{tools_dir} missing"}

    buckets = relocate_tools_shards(tools_dir)
    source_lines: list[str] = []
    for week_key in sorted(buckets.keys()):
        source_lines.extend(buckets[week_key])
    print(f"[{source}] Read {len(source_lines)} lines across {len(buckets)} shard(s) at run start.")
    print(f"[{source}] Relocating into {len(buckets)} week(s): {sorted(buckets.keys())}")

    live_snapshots: dict[str, list[str]] = {}
    for week_key in sorted(buckets.keys()):
        lines = buckets[week_key]
        try:
            ok, live_snapshot = write_week_bucket(week_key, lines, source, data_dir)
        except RuntimeError as e:
            print(f"ABORT [{source}]: {e}", file=sys.stderr)
            return {"verification_passed": False, "abort_reason": str(e)}
        if not ok:
            reason = (
                f"write_week_bucket reported failure for {source}/{week_key} "
                "(see agent-monitoring/data/.writer_health.jsonl for diagnostics)."
            )
            print(f"ABORT: {reason}", file=sys.stderr)
            return {"verification_passed": False, "abort_reason": reason}
        if live_snapshot:
            live_snapshots[week_key] = live_snapshot
        print(f"  [{source}] {week_key}: relocated {len(lines)} line(s)" + (
            f", preceding {len(live_snapshot)} pre-existing live line(s)" if live_snapshot else ""
        ))

    return verify_migration(source_lines, buckets, source, data_dir, live_snapshots)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    data_dir = repo_root / "agent-monitoring" / "data"
    reports = {}

    runs_path = repo_root / "agent-monitoring" / "runs.jsonl"
    reports["runs"] = _migrate_rebucketed_source(runs_path, "runs", RUNS_FIELD_PRIORITY, data_dir)

    events_path = repo_root / "agent-monitoring" / "events.jsonl"
    reports["events"] = _migrate_rebucketed_source(events_path, "events", EVENTS_FIELD_PRIORITY, data_dir)

    tools_dir = repo_root / "agent-monitoring" / "tools"
    reports["tools"] = _migrate_tools_relocation(tools_dir, data_dir)

    print(json.dumps(reports, indent=2, sort_keys=True))
    all_passed = all(r.get("verification_passed") for r in reports.values())
    if not all_passed:
        print(
            "VERIFICATION FAILED for at least one source — DO NOT run any git rm. "
            "Investigate the mismatches above before proceeding.",
            file=sys.stderr,
        )
        return 1
    print(
        "VERIFICATION PASSED for all 3 sources. None of the 3 legacy paths have been "
        "touched by this script — retirement (git rm) is a separate, explicit step to "
        "run only now that this report is captured in the ticket's Test Summary."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
