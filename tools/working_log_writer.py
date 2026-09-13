#!/usr/bin/env python3
"""Sole sanctioned writer for tickets/working_log.csv rows (TCK-20260912-WORKING-LOG-APPEND-HELPER).

Before this module, every closing agent (the pipeline's own Finalize prompt, and the hand-
orchestrated-closure script) hand-rolled the row write however it chose. Two independent
improvisations produced the identical defect (`csv.writer`'s default `lineterminator="\\r\\n"`),
which is what turned 3 of 4 recent batch PR merges into a duplicated `working_log.csv` block
(`merge=union` sees the same rows added on both branches with different line endings as two
different additions). Centralizing the write in one module, called from both sites, closes the
*class* of defect rather than patching each improvisation's own symptom.

Read-side parsing of this same file stays in `tools/working_log_parser.py`; this module is its
write-side counterpart and owns the row format: LF line endings, `QUOTE_MINIMAL`, the documented
6-column order (`working_log_parser.HEADER_FIELDS`), bottom-append only, `newline=""` (so
`csv.writer`, not the platform, controls line-ending bytes).

No monitoring side effects live here (no run/event recording) -- that stays with
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, which is one of this module's two
call sites. The other is `.claude/workflows/implement-ticket.js`'s Finalize step 4, which invokes
this module's CLI (`main()`, below) via `python3 tools/working_log_writer.py --data-file <path>`
rather than passing field values through a shell/Python `-c` argument -- title/summary text is
arbitrary agent-authored prose (this very ticket's own title contains backticks and an em-dash),
and a `--data-file` JSON contract avoids ever needing to escape that text for a shell or a Python
source string.

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
from pathlib import Path

_WORKING_LOG_PATH = Path("tickets/working_log.csv")


def append_working_log_row(
    timestamp: str,
    ticket_id: str,
    title: str,
    status: str,
    summary: str,
    artifacts_path: str,
    path: Path = _WORKING_LOG_PATH,
) -> None:
    """Append one row to `path` (defaults to `tickets/working_log.csv`) in the documented
    6-column order, LF-terminated, `QUOTE_MINIMAL`. Never truncates, never inserts before the
    header, never touches any existing row -- always a pure bottom-append."""
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n").writerow(
            [timestamp, ticket_id, title, status, summary, artifacts_path]
        )


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
