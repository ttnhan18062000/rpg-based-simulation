#!/usr/bin/env python3
"""Sole sanctioned writer for tickets/working_log.csv rows (TCK-20260912-WORKING-LOG-APPEND-HELPER).

Before this module, every closing agent (the pipeline's own Finalize prompt, and the hand-
orchestrated-closure script) hand-rolled the row write however it chose. Two independent
improvisations produced the identical defect (`csv.writer`'s default `lineterminator="\\r\\n"`),
which is what turned 3 of 4 recent batch PR merges into a duplicated `working_log.csv` block
(`merge=union` sees the same rows added on both branches with different line endings as two
different additions). Centralizing the write in one module, called from both sites, closes the
*class* of defect rather than patching each improvisation's own symptom.

**TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET: `append_working_log_row()` no longer writes
directly to the canonical CSV.** `.gitattributes`' `merge=union` never engages under a GitHub
squash-merge (only a real `git merge` runs a merge driver), so two branches each appending one row
at the bottom of the same shared file are the exact shape that produced a real ~1586-row
duplication (`TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`) -- the identical class of
defect `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` fixed for the JSONL shards
by giving every write a disjoint per-batch file instead of a shared insertion point. This module
now does the same for `working_log.csv`: `append_working_log_row()` writes one JSON line to a
per-batch staging shard (`monitoring_batch_identifier.resolve_write_target("working_log")` --
`agent-monitoring/data/<week>/<batch-id>.working_log.jsonl`), and `consolidate_pending_rows()`
below folds every pending shard's rows -- sorted by their own `timestamp` field, so chronological
order across multiple batches consolidated in one pass matches what direct sequential appends
would have produced -- into the real CSV via `_append_csv_row()`, then deletes the consumed
shards (idempotent-by-delete, mirroring `monitoring_consolidation.py`'s existing pattern).

Both consolidation and every direct CSV write stay in *this* module (never
`monitoring_consolidation.py` itself) so the AST guard below keeps meaning what it says: no other
file ever opens `tickets/working_log.csv` in write mode, including the consolidator.

Read-side parsing of the canonical CSV stays in `tools/working_log_parser.py`; that module also
gained `parse_pending_working_log_shards()` (TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET) so
a just-staged, not-yet-consolidated row is visible to callers that need to see it at a ticket's own
close, without waiting for a later consolidation run.

No monitoring side effects live here (no run/event recording) -- that stays with
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, which is one of this module's two
call sites. The other is `.claude/workflows/implement-ticket.js`'s Finalize step 4, which invokes
this module's CLI (`main()`, below) via `python3 tools/working_log_writer.py --data-file <path>`
rather than passing field values through a shell/Python `-c` argument -- title/summary text is
arbitrary agent-authored prose (this very ticket's own title contains backticks and an em-dash),
and a `--data-file` JSON contract avoids ever needing to escape that text for a shell or a Python
source string. Neither caller changed -- both already call `append_working_log_row()`, which is
what changed underneath them (TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET's own AC6: the two
callers agree on the write path by construction, not by being separately updated).

`tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer` walks the
AST of every `.py` file under `tools/` and asserts this module is the only one that opens
`tickets/working_log.csv` in a write/append mode. `_WORKING_LOG_PATH` below must stay a genuine
module-level constant -- not inlined into a function default expression or the `open()` call
itself -- because that guard's resolver depends on it being a single, unambiguous, named binding
site it can walk back to.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_TOOLS_DIR / "agent-monitoring") not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR / "agent-monitoring"))

from monitoring_batch_identifier import resolve_write_target  # noqa: E402

_REPO_ROOT = _TOOLS_DIR.parent
_WORKING_LOG_PATH = Path("tickets/working_log.csv")
_DEFAULT_DATA_ROOT = Path("agent-monitoring/data")


def _anchored(path: Path) -> Path:
    """TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS: a relative `path` is
    resolved against this module's own checkout (`_REPO_ROOT`, from `Path(__file__)`), not cwd --
    `consolidate_pending_rows()`'s defaults must resolve the same checkout as
    `monitoring_consolidation.DEFAULT_DATA_DIR`, which is already `__file__`-anchored. A
    cwd-relative default here is what let a foreign-cwd consolidation run move rows into whatever
    checkout happened to be cwd instead of the one that owns them. An already-absolute `path`
    (every real caller that overrides the default, and every test seeding a scratch path) passes
    through untouched. `_WORKING_LOG_PATH`/`_DEFAULT_DATA_ROOT` stay literal, relative, genuine
    module-level constants -- not inlined into a function default -- so the AST single-writer
    guard in tests/tools/test_working_log_writer.py can still resolve the default parameter back
    to "tickets/working_log.csv"; the anchoring happens at the point of use instead."""
    return path if path.is_absolute() else _REPO_ROOT / path


def _append_csv_row(fields: list, path: Path = _WORKING_LOG_PATH) -> None:
    """The one place that actually opens `tickets/working_log.csv` in append mode -- LF-
    terminated, `QUOTE_MINIMAL`, `newline=""` (so `csv.writer`, not the platform, controls
    line-ending bytes). Never truncates, never inserts before the header, always a pure
    bottom-append. Used by `consolidate_pending_rows()`; never called directly by an external
    ticket-closing caller (see module docstring)."""
    path = _anchored(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n").writerow(fields)


def append_working_log_row(
    timestamp: str,
    ticket_id: str,
    title: str,
    status: str,
    summary: str,
    artifacts_path: str,
    path: Path = None,
) -> None:
    """Stage one row for `tickets/working_log.csv` in a per-batch shard, never the canonical CSV
    directly (see module docstring, TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET) --
    `consolidate_pending_rows()` folds it in later.

    `path`, if explicitly given, instead writes the CSV row directly to that path (the pre-this-
    ticket behavior, unchanged) -- every real ticket-closing caller omits it and gets the staged
    path; this escape hatch exists only so the many existing tests seeding a scratch CSV directly
    via `path=` (round-trip/LF/tricky-field correctness against `_append_csv_row` itself) don't
    need to be rewritten around a consolidation step they aren't testing."""
    if path is not None:
        _append_csv_row([timestamp, ticket_id, title, status, summary, artifacts_path], path=path)
        return

    target = resolve_write_target("working_log")
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": timestamp,
        "ticket_id": ticket_id,
        "title": title,
        "status": status,
        "summary": summary,
        "artifacts_path": artifacts_path,
    }
    with open(target, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def consolidate_pending_rows(
    data_root: Path = _DEFAULT_DATA_ROOT, csv_path: Path = _WORKING_LOG_PATH
) -> dict:
    """Folds every pending `<batch-id>.working_log.jsonl` shard under `data_root` into `csv_path`,
    sorted by each row's own `timestamp` (Python's stable sort keeps file/line order as the
    tiebreak for equal timestamps) -- so a consolidation run that sees several different batches'
    shards at once reconstructs the same chronological order direct sequential appends would have
    produced (AC4). Idempotent by delete, mirroring `monitoring_consolidation.py`'s own JSONL-kind
    pattern: rows are appended to the canonical CSV, then their shard files are deleted only after
    that append succeeds, so a second run finds nothing left to reprocess.

    Returns `{"consolidated_rows": N, "shard_files": M}` (both 0 if nothing was pending)."""
    data_root = _anchored(data_root)
    csv_path = _anchored(csv_path)
    if not data_root.exists():
        return {"consolidated_rows": 0, "shard_files": 0}

    shard_files = sorted(data_root.glob("*/*.working_log.jsonl"))
    if not shard_files:
        return {"consolidated_rows": 0, "shard_files": 0}

    rows = []
    for f in shard_files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))

    rows.sort(key=lambda r: r.get("timestamp", ""))
    for row in rows:
        _append_csv_row(
            [
                row["timestamp"], row["ticket_id"], row["title"],
                row["status"], row["summary"], row["artifacts_path"],
            ],
            path=csv_path,
        )

    for f in shard_files:
        f.unlink()

    return {"consolidated_rows": len(rows), "shard_files": len(shard_files)}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-file",
        required=True,
        help="Path to a JSON file: "
        '{"timestamp": ..., "ticket_id": ..., "title": ..., "status": ..., "summary": ..., '
        '"artifacts_path": ...} -- read from a file, never a shell/CLI argument, so arbitrary '
        "title/summary text (quotes, backticks, $, embedded newlines) needs no escaping.",
    )
    args = parser.parse_args(argv)
    fields = json.loads(Path(args.data_file).read_text(encoding="utf-8"))
    append_working_log_row(**fields)


if __name__ == "__main__":
    main()
