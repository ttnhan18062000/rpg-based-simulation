#!/usr/bin/env python3
"""Read-only Bash-command-mix and search-tool-usage baseline over
agent-monitoring/data/*/tools.jsonl (TCK-20260923-BASH-COMMAND-MIX-BASELINE).

Promotes a peer session's already-measured scratch prototype (`bash_mix.py`) into a tested,
repeatable module. This corpus can answer two questions neither existing sibling tool already
covers:

1. What share of ALL Bash calls opens with `cd` vs `grep` vs `git` vs `python3` etc -- the raw
   call-count mix, not context-token attribution. `real_token_usage.py::attribute_by_bash_family`
   answers a related but different question (context TOKENS per bash family, read from
   developer-machine-only transcripts, and it further splits `cd` by its OWN destination
   directory -- which fragments the single "cd" total this module needs to keep as one number).
   `agent_tool_usage_baseline.py` breaks Bash down per-agent but never classifies the command
   head itself.
2. How many Bash calls are grep-flavored (head == `grep`/`rg`) against how many real
   `mcp__knowledge-search__search_docs` calls happened in the same window. CLAUDE.md's Context
   Scan mandates `search_docs` before grep; `generate_retro.py::build_raw_investigation_count_
   section` already computes a Read-based proxy for a related ratio and documents explicitly why
   it can't use grep directly ("no distinct `Grep` tool name is ever recorded ... grep-equivalent
   work runs through the catch-all `Bash` tool"). This module closes that documented gap by
   classifying Bash's own `input_summary` command head instead of substituting a proxy.

Sourced from `agent-monitoring/data/*/tools.jsonl` -- committed to git, available to any session
or CI, unlike `real_token_usage.py`'s developer-machine-only transcript corpus. Re-runnable over
an arbitrary ISO-week range (`--since-week`/`--through-week`) so a before/after comparison for
Batch B's advisory hooks (cd-prefix nudge, search-before-grep nudge) is a single command, diffed
against a prior run's `--json` output.

Read-only: never opens `agent-monitoring/data/` for writing.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import load_jsonl_with_line_count  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "agent-monitoring" / "data"

TICKET_ID = "TCK-20260923-BASH-COMMAND-MIX-BASELINE"
SEARCH_DOCS_TOOL_NAME = "mcp__knowledge-search__search_docs"
GREP_HEADS = ("grep", "rg")
# Heads worth a second-word breakdown (matches the batch's own measured granularity: "grep -n",
# "git status", "git diff", "git add", "python3 -c"). Everything else stays a bare head count.
_SUBCOMMAND_HEADS = frozenset(("git", "gh", "make", "python3") + GREP_HEADS)


def week_shards(
    data_dir: Path = DEFAULT_DATA_DIR, source: str = "tools",
    since_week: "str | None" = None, through_week: "str | None" = None,
) -> list:
    """Sorted shard paths under data_dir/*/source.jsonl, optionally bounded to an inclusive ISO
    week range. String comparison is correct for "YYYY-Wnn" labels (matches iso_week() /
    week_range()'s own convention in generate_retro.py). None on either side means unbounded."""
    shards = []
    for shard in sorted(data_dir.glob(f"*/{source}.jsonl")):
        week = shard.parent.name
        if since_week and week < since_week:
            continue
        if through_week and week > through_week:
            continue
        shards.append(shard)
    return shards


def load_tools_rows_with_line_count(
    data_dir: Path = DEFAULT_DATA_DIR,
    since_week: "str | None" = None, through_week: "str | None" = None,
) -> "tuple[list, int]":
    """Race-free: one read per shard (via load_jsonl_with_line_count), never a separate
    count-read and parse-read of the same live, concurrently-written file (same rationale as
    agent_tool_usage_baseline.py's own with_line_count variant)."""
    rows = []
    total_lines = 0
    for shard in week_shards(data_dir, "tools", since_week, through_week):
        shard_rows, shard_lines = load_jsonl_with_line_count(shard)
        rows.extend(shard_rows)
        total_lines += shard_lines
    return rows, total_lines


def load_tools_rows(
    data_dir: Path = DEFAULT_DATA_DIR,
    since_week: "str | None" = None, through_week: "str | None" = None,
) -> list:
    rows, _ = load_tools_rows_with_line_count(data_dir, since_week, through_week)
    return rows


def bash_head(input_summary: str) -> str:
    if not input_summary:
        return "?"
    parts = input_summary.strip().split()
    return parts[0] if parts else "?"


def bash_subcommand_key(head: str, input_summary: str) -> str:
    """head alone for most commands; head + truncated second word for the heads this batch's
    own measurement broke down further (git/gh/make/python3/grep/rg)."""
    if head not in _SUBCOMMAND_HEADS:
        return head
    parts = input_summary.strip().split()
    if len(parts) < 2:
        return head
    return f"{head} {parts[1][:20]}"


def build_bash_mix_report(
    rows: list, since_week: "str | None" = None, through_week: "str | None" = None,
) -> dict:
    bash_rows = [r for r in rows if r.get("tool") == "Bash"]
    search_docs_calls = sum(1 for r in rows if r.get("tool") == SEARCH_DOCS_TOOL_NAME)

    head_counts: Counter = Counter()
    sub_counts: Counter = Counter()
    cd_calls = 0
    grep_calls = 0
    for row in bash_rows:
        summary = row.get("input_summary") or ""
        head = bash_head(summary)
        head_counts[head] += 1
        sub_counts[bash_subcommand_key(head, summary)] += 1
        if head == "cd":
            cd_calls += 1
        if head in GREP_HEADS:
            grep_calls += 1

    total_bash = len(bash_rows)
    total_all = len(rows)

    if search_docs_calls > 0:
        grep_to_search_docs_ratio = round(grep_calls / search_docs_calls, 4)
    else:
        grep_to_search_docs_ratio = (
            "undefined: zero search_docs calls in window, cannot compute a ratio without a "
            "fabricated denominator"
        )

    return {
        "ticket_id": TICKET_ID,
        "since_week": since_week,
        "through_week": through_week,
        "total_rows_seen": total_all,
        "total_bash_calls": total_bash,
        "bash_share_of_all_calls": (total_bash / total_all) if total_all else 0.0,
        "bash_head_counts": dict(head_counts),
        "bash_head_shares": {
            head: (count / total_bash if total_bash else 0.0)
            for head, count in head_counts.items()
        },
        "bash_subcommand_counts": dict(sub_counts),
        "cd_calls": cd_calls,
        "cd_share_of_bash_calls": (cd_calls / total_bash) if total_bash else 0.0,
        "grep_calls": grep_calls,
        "search_docs_calls": search_docs_calls,
        "grep_to_search_docs_ratio": grep_to_search_docs_ratio,
    }


def _pct(x: float) -> str:
    return f"{x:.1%}"


def render_markdown(report: dict, top: int = 12) -> str:
    lines = []
    window = f"{report['since_week'] or 'earliest'}..{report['through_week'] or 'latest'}"
    lines.append(f"Window: {window}. Rows seen: {report['total_rows_seen']:,}. "
                 f"Bash calls: {report['total_bash_calls']:,} "
                 f"({_pct(report['bash_share_of_all_calls'])} of all rows).")
    lines.append("")
    lines.append(f"`cd`: {report['cd_calls']:,} calls "
                 f"({_pct(report['cd_share_of_bash_calls'])} of Bash calls).")
    ratio = report["grep_to_search_docs_ratio"]
    ratio_str = ratio if isinstance(ratio, str) else f"{ratio:.2f}"
    lines.append(f"`grep`/`rg`: {report['grep_calls']:,} calls vs. "
                 f"`search_docs`: {report['search_docs_calls']:,} calls "
                 f"(grep:search_docs ratio = {ratio_str}).")
    lines.append("")

    lines.append("### Bash command head mix")
    lines.append("")
    lines.append("| head | calls | share of Bash calls |")
    lines.append("|---|---|---|")
    for head, count in sorted(report["bash_head_counts"].items(), key=lambda kv: -kv[1])[:top]:
        lines.append(f"| `{head}` | {count:,} | {_pct(report['bash_head_shares'][head])} |")
    lines.append("")

    lines.append("### Bash subcommand breakdown (git/gh/make/python3/grep/rg)")
    lines.append("")
    lines.append("| subcommand | calls |")
    lines.append("|---|---|")
    sub_items = sorted(report["bash_subcommand_counts"].items(), key=lambda kv: -kv[1])
    sub_items = [(k, v) for k, v in sub_items if " " in k][:top]
    for key, count in sub_items:
        lines.append(f"| `{key}` | {count:,} |")

    return "\n".join(lines)


def main(argv: "list | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=None, help="Override agent-monitoring/data/ (mainly for testing).")
    parser.add_argument("--since-week", default=None, help='Inclusive lower ISO week bound, e.g. "2026-W30".')
    parser.add_argument("--through-week", default=None, help='Inclusive upper ISO week bound, e.g. "2026-W39".')
    parser.add_argument("--json", action="store_true", help="Print the raw report dict as JSON instead of markdown.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    rows = load_tools_rows(data_dir, args.since_week, args.through_week)
    report = build_bash_mix_report(rows, args.since_week, args.through_week)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_markdown(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
