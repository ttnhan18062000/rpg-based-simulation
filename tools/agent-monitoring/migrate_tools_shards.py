#!/usr/bin/env python3
"""One-time migration: split agent-monitoring/tools.jsonl into weekly ISO-week shard files.

TCK-20260902-MONITORING-SHARD-MIGRATION (child 2 of the monitoring weekly-sharding epic).
Buckets every historical line by its own `ts` field's ISO week (`%G-W%V`), appends each
bucket into `agent-monitoring/tools/tools-YYYY-Www.jsonl` via writer.py::write_lines()
(one locked batch per week), and runs a strict full-corpus zero-data-loss verification
BEFORE this ticket's implementer runs `git rm agent-monitoring/tools.jsonl` as a separate,
explicit, human-reviewed step. This script never calls `git rm` itself.

Genuinely one-time: no Make target, no cron/scheduled re-run mechanism. Re-running it after
`agent-monitoring/tools.jsonl` has been retired is a no-op failure (source file absent).

Route-only, content-preserving: this script never repairs or normalizes malformed/off-schema
historical lines (a documented handful missing `tool`/`run_id`/`seq` per
docs/agent-monitoring/schema.md's Known Limitations) — it only routes them to the correct
week bucket by whatever `ts` they carry, or to the `tools-unknown-week.jsonl` fallback shard
if `ts` itself is missing/unparseable. It never dedupes or re-keys by `(run_id, seq)` — known
historical `seq` collisions exist; the only ordering key is each line's original append
position within its `ts`-derived week bucket.

Cross-worktree `git rm` merge-conflict runbook (TCK-20260902-MONITORING-SHARD-MIGRATION
decision 5): this script performs a one-time, irreversible-from-the-working-tree `git rm` of
agent-monitoring/tools.jsonl (in a separate step, gated on this script's verification
passing). Any other worktree/branch that has not yet merged past this ticket's commit and is
still appending to its own local copy of agent-monitoring/tools.jsonl will produce a
`CONFLICT (modify/delete)` when it later merges past this point — confirmed via
`git merge-base --is-ancestor` against every other live worktree at investigation time.
`merge=union` does NOT apply to modify/delete conflicts (it is a content-merge driver, only
invoked when a path exists on both sides of a 3-way merge). Resolution: take the deletion
side (`git rm agent-monitoring/tools.jsonl` at the conflict), and if that other branch's
interim rows need to be preserved, re-run this same script against that branch's pre-merge
copy of tools.jsonl (or a targeted subset of its new lines) before finalizing the merge,
rather than resurrecting the monolithic file.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writer import write_lines  # noqa: E402

UNKNOWN_WEEK_KEY = "unknown-week"


def _parse_ts_to_week(ts: str) -> str:
    """Tolerant `ts` -> ISO-week (`%G-W%V`) parser.

    Handles the 2 real shape variants confirmed by investigation: the standard
    `%Y-%m-%dT%H:%M:%S.%fZ` form, and a rare bare no-timezone/no-fraction form. Falls back to
    UNKNOWN_WEEK_KEY (never raises) if `ts` cannot be parsed by either attempt.
    """
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return UNKNOWN_WEEK_KEY
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def bucket_lines_by_week(lines: list[str]) -> dict[str, list[str]]:
    """Group raw JSONL line strings (no trailing newline) by their `ts` field's ISO week.

    Preserves each line's original relative order within its bucket — a single forward pass
    appending to `dict[key].append(line)`, never re-sorted by `ts` or any other key. Route-only:
    does not repair, coerce, or normalize any line's content.
    """
    buckets: dict[str, list[str]] = {}
    for line in lines:
        record = json.loads(line)
        ts = record.get("ts")
        key = UNKNOWN_WEEK_KEY if not ts else _parse_ts_to_week(ts)
        buckets.setdefault(key, []).append(line)
    return buckets


def _shard_path_for_week(week_key: str, shard_dir: Path) -> Path:
    return shard_dir / f"tools-{week_key}.jsonl"


def write_week_bucket(week_key: str, lines: list[str], shard_dir: Path) -> tuple[bool, list[str]]:
    """Append `lines` for one week bucket into its shard file via exactly one write_lines() call.

    Returns (ok, live_snapshot) — live_snapshot is the pre-existing content of the shard file
    at the moment this bucket was processed (empty list for Case A). Exposing it here (rather
    than write_week_bucket returning a bare bool per the plan's initial sketch) is what lets the
    live-row count be captured at the exact moment this bucket is written, not earlier, per the
    plan's own "minimizes the window between snapshot and rename" requirement — verify_migration
    needs the actual live content, not just its count, to do a real content-preservation check.

    Case A (target absent or empty): a single direct write_lines() call.
    Case B (target already has live post-cutover content, e.g. the in-progress current week):
    rename the live file aside, build combined = migrated_lines + live_snapshot, write it as one
    single write_lines() call (never two), then reconcile that the new file's trailing
    len(live_snapshot) lines exactly match the pre-migration live_snapshot before discarding the
    backup. Never truncates or overwrites the live file directly.
    """
    target_path = _shard_path_for_week(week_key, shard_dir)
    # write_lines()'s internal _acquire_lock() creates the lock file at
    # target_path.parent / "<name>.lock" before write_lines() gets a chance to run its own
    # target_path.parent.mkdir() (that mkdir only runs after the lock is already held) — the
    # parent directory must already exist before the first lock-file os.open() call, matching
    # the same pre-mkdir pattern post_tool_hook.py already uses ahead of its own write_line()
    # call.
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
    shard_dir: Path,
    live_snapshots: dict[str, list[str]],
) -> dict:
    """Full-corpus (not sampled) zero-data-loss verification.

    Re-reads every shard file this run touched, confirms: (1) exact line-count reconciliation
    (original_total + explained_delta == migrated_total, never approximate); (2) every shard's
    on-disk content (minus any pre-existing live suffix) matches the exact lines this run
    bucketed for it, byte-for-byte, in order — this both proves content preservation and proves
    no line was duplicated across shards (bucket_lines_by_week's single-pass dict assignment
    already guarantees each source line is a member of exactly one bucket list; this step proves
    write_lines() faithfully persisted that partition, not just that the partition was correct in
    memory); (3) every persisted line still round-trips through json.loads().
    """
    original_total = len(source_lines)
    migrated_total = 0
    explained_delta = 0
    per_shard_counts: dict[str, int] = {}
    content_mismatches: list[str] = []
    parse_failures: list[str] = []

    for week_key, expected_lines in buckets.items():
        shard_path = _shard_path_for_week(week_key, shard_dir)
        actual_lines = shard_path.read_text().splitlines()
        per_shard_counts[shard_path.name] = len(actual_lines)
        migrated_total += len(actual_lines)

        live_snapshot = live_snapshots.get(week_key, [])
        explained_delta += len(live_snapshot)

        if live_snapshot:
            split_at = len(actual_lines) - len(live_snapshot)
            migrated_part = actual_lines[:split_at]
            live_part = actual_lines[split_at:]
            if live_part != live_snapshot:
                content_mismatches.append(
                    f"{shard_path.name}: live suffix does not match pre-migration snapshot"
                )
        else:
            migrated_part = actual_lines

        if migrated_part != expected_lines:
            content_mismatches.append(
                f"{shard_path.name}: migrated content does not match bucketed input "
                f"(expected {len(expected_lines)} lines, found {len(migrated_part)})"
            )

        for line in actual_lines:
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                parse_failures.append(f"{shard_path.name}: {e}")

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


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    source_path = repo_root / "agent-monitoring" / "tools.jsonl"
    shard_dir = repo_root / "agent-monitoring" / "tools"

    if not source_path.exists():
        print(f"ABORT: source file {source_path} does not exist (already migrated?).", file=sys.stderr)
        return 1

    source_lines = source_path.read_text().splitlines()
    print(f"Read {len(source_lines)} lines from {source_path} at run start.")

    buckets = bucket_lines_by_week(source_lines)
    print(f"Bucketed into {len(buckets)} week(s): {sorted(buckets.keys())}")

    live_snapshots: dict[str, list[str]] = {}
    for week_key in sorted(buckets.keys()):
        lines = buckets[week_key]
        try:
            ok, live_snapshot = write_week_bucket(week_key, lines, shard_dir)
        except RuntimeError as e:
            print(f"ABORT: {e}", file=sys.stderr)
            return 1
        if not ok:
            print(
                f"ABORT: write_week_bucket reported failure for {week_key} "
                "(see agent-monitoring/tools/.writer_health.jsonl for diagnostics).",
                file=sys.stderr,
            )
            return 1
        if live_snapshot:
            live_snapshots[week_key] = live_snapshot
        print(f"  {week_key}: wrote {len(lines)} migrated line(s)" + (
            f", preceding {len(live_snapshot)} pre-existing live line(s)" if live_snapshot else ""
        ))

    report = verify_migration(source_lines, buckets, shard_dir, live_snapshots)
    print(json.dumps(report, indent=2, sort_keys=True))

    if not report["verification_passed"]:
        print(
            "VERIFICATION FAILED — DO NOT run `git rm agent-monitoring/tools.jsonl`. "
            "Investigate the mismatches above before proceeding.",
            file=sys.stderr,
        )
        return 1

    print(
        "VERIFICATION PASSED. agent-monitoring/tools.jsonl has NOT been touched by this script — "
        "retirement (git rm) is a separate, explicit step to run only now that this report is "
        "captured in the ticket's Test Summary."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
