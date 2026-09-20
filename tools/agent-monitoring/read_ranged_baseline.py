#!/usr/bin/env python3
"""Read-only baseline over agent-monitoring/data/*/tools.jsonl for Read-call ranged-vs-whole-file
behavior (TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS).

`read_ranged` is a new field this ticket adds to `post_tool_hook.py`'s own record schema — no
historical row has it (key absent, not `null`), since `input_summary` alone was verified
insufficient to reconstruct it retroactively (see the ticket's own investigation). This script
therefore reports two honestly distinct things rather than fabricating a single "before" number:
(1) the real, available "before" — total Read-call volume and its window, which the ticket's own
Acceptance Criteria ask for; (2) a `known`/`unknown` split for `read_ranged` itself, where `unknown`
is expected to be the entire historical corpus until real usage accumulates after this field ships.
Re-running this script later is the actual "after" comparison.

Prints a JSON report to stdout by default; never writes into agent-monitoring/ itself.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_retro import DEFAULT_TOOLS_FILE, load_data_glob  # noqa: E402
from manifest import _assert_safe_output_path  # noqa: E402


def compute_read_ranged_baseline(tools: list) -> dict:
    read_rows = [t for t in tools if t.get("tool") == "Read"]
    timestamps = sorted(t["ts"] for t in tools if t.get("ts"))

    ranged_true = sum(1 for r in read_rows if r.get("read_ranged") is True)
    ranged_false = sum(1 for r in read_rows if r.get("read_ranged") is False)
    # Absent key (pre-ticket historical row) and present-but-null (defensive; the hook never
    # actually writes null for tool=="Read") are both "unknown" for this measurement's purpose.
    ranged_unknown = sum(
        1 for r in read_rows if r.get("read_ranged") is not True and r.get("read_ranged") is not False
    )

    return {
        "window_start_ts": timestamps[0] if timestamps else None,
        "window_end_ts": timestamps[-1] if timestamps else None,
        "total_tool_calls": len(tools),
        "total_read_calls": len(read_rows),
        "read_ranged_true_count": ranged_true,
        "read_ranged_false_count": ranged_false,
        "read_ranged_unknown_count": ranged_unknown,
        "note": (
            "read_ranged_unknown_count is expected to equal total_read_calls until real usage "
            "accumulates after TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS "
            "ships — it is not a data quality problem, it is every row predating this field. "
            "Re-run this script after enough new activity to see the real known/unknown split "
            "shift; that shift, not this snapshot alone, is the actual before/after comparison."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="optional path to also write the JSON output to")
    args = parser.parse_args()

    tools = load_data_glob(DEFAULT_TOOLS_FILE, "tools")
    report = compute_read_ranged_baseline(tools)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output is not None:
        _assert_safe_output_path(args.output)
        args.output.write_text(output)

    sys.stdout.write(output)


if __name__ == "__main__":
    main()
