#!/usr/bin/env python3
"""Append-only history and per-dimension trend scorecard over
`tools/codebase_health_baseline.py::build_report()`'s live metrics.

Built for TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD, item 3 of
`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` (see
`docs/audits/D24_codebase_health_observatory.md` §J/§M and
`docs/plans/codebase_health_observatory_tooling_epic.md`). This module never
recomputes or re-derives any individual metric — it imports `build_report`
directly and only adds persistence (an append-only JSONL history file,
mirroring `agent-monitoring/runs.jsonl`'s own pattern) and a read-side
per-dimension trend view on top of it.

**Snapshot write path**: `write_snapshot` reuses
`tools/agent-monitoring/writer.py::write_line` — the same hardened,
lock-protected, never-raising append primitive `record_run.py`/
`record_events.py`/`post_tool_hook.py` already use for `agent-monitoring/*.jsonl`
— rather than a plain unlocked `open(path, "a")`. `tools/agent-monitoring/`'s
hyphen makes it unimportable as a dotted package name (no `__init__.py`-based
package name can contain a hyphen), so its directory is added to `sys.path`
directly, mirroring `tools/agent-monitoring/record_run.py`'s own
`sys.path.insert(0, str(Path(__file__).resolve().parent))` pattern, pointed at
the sibling directory instead of the file's own parent.

**Schema freeze**: `EXPECTED_SNAPSHOT_KEYS` is a frozen, hand-copied allowlist
of `build_report()`'s real return-dict keys. `build_snapshot_record` validates
`set(report.keys()) == EXPECTED_SNAPSHOT_KEYS` exactly (not a subset/superset
check) and raises `RuntimeError` loudly on any mismatch — a future
`build_report()` field rename/add/remove becomes a visible breaking change
instead of a silently drifting snapshot shape. `SNAPSHOT_SCHEMA_VERSION` is
stamped onto every written record and must be bumped by hand, in the same
commit as any `EXPECTED_SNAPSHOT_KEYS` edit.

**No aggregate/combined score, anywhere** — the source audit (D24 §J/§M) and
this epic's own "Out of scope" bullet are explicit: trend arrows per
dimension, never a single collapsed health score, not even a bare "N up / M
down" count. `build_scorecard`'s returned dict and `format_scorecard`'s
printed text are both audited to carry no `score`/`overall`/`combined`/
`summary`-shaped key or line.

**`history_path` has no default on `write_snapshot`/`build_snapshot_record`**
(the latter does not even take one — it never touches the history file).
`DEFAULT_HISTORY_PATH` is applied exactly once, at the `main()`/argparse
layer, where a real CLI default is actually needed. This is load-bearing for
test isolation: `write_line`'s own real signature has no default for its
target path either, which is exactly why `tests/tools/test_monitoring_writer.py`'s
literal-source-scan guard can catch a hardcoded real-corpus path — a default
on `write_snapshot` would let a test that simply omits the keyword argument
silently target the real `agent-monitoring/codebase_health_history.jsonl` with
nothing textually present in that test's source for such a scan to catch.
"""

import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent

if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
from codebase_health_baseline import build_report  # noqa: E402

sys.path.insert(0, str(_REPO_ROOT / "tools" / "agent-monitoring"))
from writer import write_line  # noqa: E402

# Hand-copied once from the real `build_report()` return statement
# (`tools/codebase_health_baseline.py:238-253`) — the single source of truth
# for what a valid snapshot record must contain. Never edit this without also
# bumping SNAPSHOT_SCHEMA_VERSION and updating
# docs/agent-monitoring/codebase_health_history_schema.md in the same commit.
EXPECTED_SNAPSHOT_KEYS = frozenset({
    "source_loc", "source_files", "test_loc", "test_files", "test_source_ratio",
    "top_level_src_packages", "test_subdirectories", "commit_count", "doc_count",
    "registry_size_bytes", "registry_size_lines", "dead_bytecode_files",
    "unused_core_dependencies", "churn_lines_changed_excl_bookkeeping",
})
SNAPSHOT_SCHEMA_VERSION = 1
DEFAULT_HISTORY_PATH = _REPO_ROOT / "agent-monitoring" / "codebase_health_history.jsonl"

# The 11 scalar dimensions that get a Δ + arrow trend row.
SCALAR_DIMENSIONS = (
    "source_loc", "source_files", "test_loc", "test_files", "test_source_ratio",
    "top_level_src_packages", "test_subdirectories", "commit_count", "doc_count",
    "dead_bytecode_files", "churn_lines_changed_excl_bookkeeping",
)
# registry_size_bytes/registry_size_lines fold to one scorecard row: only the
# more human-legible lines unit is trended. registry_size_bytes is still
# captured in every snapshot record (it's part of EXPECTED_SNAPSHOT_KEYS) but
# never rendered as its own scorecard dimension.
REGISTRY_DIMENSION_KEY = "registry_size_lines"
# list[str], not a scalar — rendered as a raw value/count, never through the
# Δ/arrow branch.
NON_SCALAR_DIMENSION_KEY = "unused_core_dependencies"

DIMENSION_ORDER = SCALAR_DIMENSIONS + (REGISTRY_DIMENSION_KEY, NON_SCALAR_DIMENSION_KEY)

DIMENSION_LABELS = {
    "source_loc": "Source LoC",
    "source_files": "Source files",
    "test_loc": "Test LoC",
    "test_files": "Test files",
    "test_source_ratio": "Test:source ratio (LoC)",
    "top_level_src_packages": "Top-level src/ packages",
    "test_subdirectories": "Test subdirectories",
    "commit_count": "Commits (full history)",
    "doc_count": "Docs (.md, under docs/)",
    "dead_bytecode_files": "Dead bytecode files",
    "churn_lines_changed_excl_bookkeeping": "Churn (lines changed, excl. bookkeeping)",
    "registry_size_lines": "docs/REGISTRY.yaml size (lines)",
    "unused_core_dependencies": "Declared-but-unused core dependencies",
}

NO_TREND_DATA_LABEL = "no trend data yet"


def build_snapshot_record(repo_root: Path) -> dict:
    """Build one snapshot record from a real, live `build_report()` call.

    Never re-derives/recomputes any individual metric — `report` is used
    exactly as `build_report()` returns it, with only a schema-version field
    stamped on top.
    """
    report = build_report(repo_root)
    actual_keys = set(report.keys())
    if actual_keys != EXPECTED_SNAPSHOT_KEYS:
        missing = sorted(EXPECTED_SNAPSHOT_KEYS - actual_keys)
        added = sorted(actual_keys - EXPECTED_SNAPSHOT_KEYS)
        raise RuntimeError(
            "build_report()'s return shape no longer matches "
            f"EXPECTED_SNAPSHOT_KEYS — missing keys: {missing}, unexpected "
            f"keys: {added}. If this is an intentional build_report() change, "
            "update EXPECTED_SNAPSHOT_KEYS, bump SNAPSHOT_SCHEMA_VERSION, and "
            "update docs/agent-monitoring/codebase_health_history_schema.md "
            "in the same commit."
        )
    return {**report, "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION}


def write_snapshot(repo_root: Path, history_path: Path) -> bool:
    """Append one snapshot record to `history_path`.

    `history_path` has no default (see module docstring) — every call site
    must pass it explicitly. Never wraps `write_line`'s own already-never-
    raises contract in a try/except; a `False` return is the caller's signal
    to warn, not this function's job to escalate.
    """
    record = build_snapshot_record(repo_root)
    line = json.dumps(record, separators=(",", ":"))
    # write_line acquires its lock file (a sibling of history_path) before
    # its own mkdir call, so the parent directory must already exist —
    # mirrors record_run.py's own `RUNS_FILE.parent.mkdir(...)` call site,
    # made just before its write_line call, for the identical reason.
    history_path.parent.mkdir(parents=True, exist_ok=True)
    return write_line(history_path, line)


def read_snapshots(history_path: Path) -> list:
    """Return all historical snapshot records, oldest first.

    Returns `[]` if `history_path` does not exist yet — the expected
    first-run state, not an error.
    """
    if not history_path.exists():
        return []
    snapshots = []
    with history_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            snapshots.append(json.loads(line))
    return snapshots


def _build_scalar_row(latest: dict, previous: dict | None, key: str) -> dict:
    if previous is None:
        return {
            "latest": latest[key],
            "previous": None,
            "diff": None,
            "arrow": None,
            "trend_label": NO_TREND_DATA_LABEL,
        }
    diff = latest[key] - previous[key]
    arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
    return {
        "latest": latest[key],
        "previous": previous[key],
        "diff": diff,
        "arrow": arrow,
        "trend_label": None,
    }


def _build_non_scalar_row(latest: dict, previous: dict | None) -> dict:
    latest_value = latest[NON_SCALAR_DIMENSION_KEY]
    if previous is None:
        return {
            "latest": latest_value,
            "previous": None,
            "changed": None,
            "trend_label": NO_TREND_DATA_LABEL,
        }
    previous_value = previous[NON_SCALAR_DIMENSION_KEY]
    return {
        "latest": latest_value,
        "previous": previous_value,
        "changed": latest_value != previous_value,
        "trend_label": None,
    }


def build_scorecard(snapshots: list) -> dict:
    """Build the per-dimension trend scorecard from historical snapshots.

    Always compares only the two most recent snapshots
    (`snapshots[-1]` vs. `snapshots[-2]`), regardless of how many total
    snapshots exist. Degrades gracefully: zero snapshots returns an explicit
    `no_snapshots_yet` marker with no dimension rows; exactly one snapshot
    returns every dimension labeled `NO_TREND_DATA_LABEL` rather than
    fabricating a trend from a single point.

    No aggregate/combined signal, not even a count, is ever included in the
    returned dict — this is deliberate (D24 §J/§M, epic Out of Scope).
    """
    if not snapshots:
        return {"no_snapshots_yet": True, "dimensions": {}}

    latest = snapshots[-1]
    previous = snapshots[-2] if len(snapshots) >= 2 else None

    dimensions = {}
    for key in SCALAR_DIMENSIONS + (REGISTRY_DIMENSION_KEY,):
        dimensions[key] = _build_scalar_row(latest, previous, key)
    dimensions[NON_SCALAR_DIMENSION_KEY] = _build_non_scalar_row(latest, previous)

    return {"no_snapshots_yet": False, "dimensions": dimensions}


def _format_scalar_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return f"{value:,}"


def _format_dependency_list(values) -> str:
    return f"{len(values)} ({', '.join(values) if values else 'none'})"


def format_scorecard(scorecard: dict) -> str:
    """Pure presentation over `build_scorecard`'s returned dict.

    Renders, per dimension: label, latest value, and either the arrow + Δ
    suffix, the no-trend-data label, or (zero-snapshot case) a whole-table
    message. Contains no aggregate/combined line anywhere in the printed
    text — a second, independent enforcement point alongside the structured
    dict's own guarantee.
    """
    header = "Codebase Health Scorecard (per-dimension trend)"
    rule = "=" * 74

    if scorecard.get("no_snapshots_yet"):
        return "\n".join([
            header,
            rule,
            "no snapshots yet — run `make codebase-health-snapshot` at least "
            "once (twice to see a trend) before viewing the scorecard.",
            rule,
        ])

    lines = [header, rule]
    dimensions = scorecard["dimensions"]
    for key in DIMENSION_ORDER:
        row = dimensions[key]
        label = DIMENSION_LABELS[key]

        if key == NON_SCALAR_DIMENSION_KEY:
            latest_repr = _format_dependency_list(row["latest"])
            if row["trend_label"]:
                lines.append(f"{label:<50} {latest_repr}  [{row['trend_label']}]")
            elif row["changed"]:
                previous_repr = _format_dependency_list(row["previous"])
                lines.append(
                    f"{label:<50} {latest_repr}  (changed from {previous_repr})"
                )
            else:
                lines.append(f"{label:<50} {latest_repr}  (unchanged)")
            continue

        latest_repr = _format_scalar_value(row["latest"])
        if row["trend_label"]:
            lines.append(f"{label:<50} {latest_repr}  [{row['trend_label']}]")
        else:
            diff = row["diff"]
            diff_repr = f"{diff:+.2f}" if isinstance(diff, float) else f"{diff:+,}"
            lines.append(f"{label:<50} {latest_repr}  {row['arrow']} {diff_repr}")

    lines.append(rule)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Append a codebase-health snapshot to the history file."
    )
    snapshot_parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    snapshot_parser.add_argument(
        "--history-path", type=Path, default=DEFAULT_HISTORY_PATH
    )

    scorecard_parser = subparsers.add_parser(
        "scorecard", help="Print a per-dimension trend scorecard over codebase-health history."
    )
    scorecard_parser.add_argument(
        "--history-path", type=Path, default=DEFAULT_HISTORY_PATH
    )

    args = parser.parse_args(argv)

    if args.mode == "snapshot":
        ok = write_snapshot(args.repo_root, args.history_path)
        if not ok:
            print(
                f"WARNING: failed to append snapshot to {args.history_path}, "
                "see the writer's .writer_health.jsonl diagnostic sidecar",
                file=sys.stderr,
            )
        else:
            print(f"DONE: appended codebase-health snapshot to {args.history_path}")
        return 0

    snapshots = read_snapshots(args.history_path)
    scorecard = build_scorecard(snapshots)
    print(format_scorecard(scorecard))
    return 0


if __name__ == "__main__":
    sys.exit(main())
