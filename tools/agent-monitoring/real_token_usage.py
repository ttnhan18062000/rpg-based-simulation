"""Real token usage from local Claude Code transcripts (this repo's own sessions only).

TCK-20260921-REAL-TOKEN-TELEMETRY. Corrects `docs/agent-monitoring/schema.md`'s "no workaround
within the current platform" claim: the workflow `agent()` call still never receives token usage
per-event (that part of the schema note remains true), but the Claude Code runtime itself DOES
write real per-request `message.usage` into this machine's own local transcript JSONL files
(`~/.claude/projects/**/*.jsonl`), regardless of what the workflow script ever sees. This module
reads those files directly for a real, retrospective usage report.

Hard boundaries, load-bearing, not incidental:
- **Read-only.** Never writes to a transcript file, never mutates one.
- **Aggregates only, never raw content.** Transcripts hold private conversation text; this module
  extracts numeric usage/metadata fields (`usage.*`, `timestamp`, `model`, `gitBranch`, tool NAMES
  and Bash command strings for attribution) and tool-result byte/char COUNTS, never the prose of a
  request, a response, or a tool result body. Nothing this module returns should ever be committed
  to the repo as a cached artifact — it is meant to be run and read, not persisted.
  Bash *command strings* are the one field kept verbatim (needed to classify command families,
  e.g. "git status" vs "git log") -- everything else that could carry conversation prose is
  reduced to a length/count before ever leaving `parse_transcript_file`.
- **Developer-machine-only.** Transcripts live outside git under `~/.claude/projects/`; a fresh
  clone or CI runner has none. Every caller of this module (the CLI here, `generate_retro.py`'s
  wiring) must fail open — report the section as unavailable, never error the whole run — when the
  transcript root does not exist or no matching files are found.
- **Streams, never loads the corpus into memory at once.** Real corpus size on this machine is
  ~1.2GB across all sessions; each file is opened, read line by line, and closed before the next.

Two entry points:
  - `collect(root, since)` -- the pure, file-system-reading core: walks matching transcript files,
    parses each one streaming, returns `(records, tool_result_stats, session_meta, compact_count)`.
  - `build_report(records, tool_result_stats, session_meta, compact_count)` -- pure aggregation
    over already-collected data (no I/O), producing the JSON-serializable report dict every
    consumer (CLI, `generate_retro.py`) renders from. Separated from `collect()` so tests can
    exercise the aggregation logic against synthetic `RequestRecord` objects without touching the
    filesystem at all.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

DEFAULT_TRANSCRIPT_ROOT = Path(os.path.expanduser("~/.claude/projects"))
PROJECT_GLOB_HINT = "*rpg-based-simulation*"
_PROJECT_DIR_STRIP = "-home-u24desktop-Working-rpg-based-simulation"

_CONTEXT_BUCKETS = [
    ("<50k", 50_000),
    ("50-100k", 100_000),
    ("100-200k", 200_000),
    ("200-500k", 500_000),
    (">=500k", float("inf")),
]


@dataclass(frozen=True)
class RequestRecord:
    """One real API request, deduplicated. No conversation content -- only usage/metadata."""

    project: str
    session: str
    is_sub: bool
    sub_name: str
    day: str
    model: Optional[str]
    git_branch: Optional[str]
    in_tokens: int
    cache_write: int
    cache_read: int
    out_tokens: int
    tools: Tuple[str, ...] = field(default_factory=tuple)
    bash_commands: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def context_tokens(self) -> int:
        return self.in_tokens + self.cache_write + self.cache_read


def iter_transcript_files(
    root: Path = DEFAULT_TRANSCRIPT_ROOT, since: Optional[str] = None,
) -> Iterator[Path]:
    """Yields this repo's transcript JSONL files under `root`, coarsely pre-filtered by file mtime
    (an efficiency filter only -- the authoritative per-request filter is each row's own
    `timestamp`, applied in `parse_transcript_file`). `since` is an ISO date string "YYYY-MM-DD";
    None means no filter. Yields nothing (not an error) if `root` does not exist."""
    if not root.is_dir():
        return
    pattern = str(root / PROJECT_GLOB_HINT / "**" / "*.jsonl")
    for f in glob.glob(pattern, recursive=True):
        if since is not None:
            try:
                mtime_day = dt.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d")
            except OSError:
                continue
            if mtime_day < since:
                continue
        yield Path(f)


def _bash_family(command: str) -> str:
    cmd = command.strip()
    parts = re.split(r"\s+", cmd)
    if not parts or not parts[0]:
        return "?"
    fam = parts[0]
    if fam in ("git", "gh", "make", "python3", "cd") and len(parts) > 1:
        fam += " " + parts[1].split("/")[-1][:30]
    return fam


def _display_tool_name(raw_name: str) -> str:
    if raw_name.startswith("mcp__"):
        pieces = raw_name.split("__")
        if len(pieces) > 1:
            return "mcp:" + pieces[1]
    return raw_name


def parse_transcript_file(
    path: Path, since: Optional[str], root: Path = DEFAULT_TRANSCRIPT_ROOT,
) -> Tuple[List[RequestRecord], Dict[str, List[int]], Dict[str, dict], int]:
    """Streams one transcript file line by line (never holds the whole file in memory).

    Returns `(request_records, tool_result_stats, session_meta, compact_boundary_count)` for this
    file only -- the caller (`collect`) merges across files. `tool_result_stats` is
    `{tool_name: [call_count, total_chars]}`, sizes only, never the result content itself.
    `session_meta` is `{session_id: {"agent-name": ..., "custom-title": ...}}`.
    """
    records: List[RequestRecord] = []
    tool_result_stats: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    session_meta: Dict[str, dict] = {}
    compact_count = 0

    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts

    project = (rel_parts[0].replace(_PROJECT_DIR_STRIP, "") or "(main)") if rel_parts else "(unknown)"
    session = rel_parts[1].replace(".jsonl", "") if len(rel_parts) > 1 else path.stem
    is_sub = "subagents" in rel_parts
    sub_name = rel_parts[-1].replace(".jsonl", "") if is_sub else ""

    seen_request_ids = set()
    tool_use_names_by_id: Dict[str, str] = {}

    try:
        fh = open(path, "r", errors="replace")
    except OSError:
        return records, tool_result_stats, session_meta, compact_count

    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            row_type = row.get("type")

            if row_type == "system" and row.get("subtype") == "compact_boundary":
                compact_count += 1
                continue

            if row_type in ("custom-title", "agent-name") and not is_sub:
                session_meta.setdefault(session, {})[row_type] = (
                    row.get("customTitle") or row.get("agentName")
                )

            message = row.get("message") if isinstance(row.get("message"), dict) else None
            ts_day = (row.get("timestamp") or "")[:10]

            if row_type == "assistant" and message and message.get("usage"):
                content_blocks = message.get("content") or []
                this_msg_tools: List[str] = []
                this_msg_bash: List[str] = []
                for blk in content_blocks:
                    if isinstance(blk, dict) and blk.get("type") == "tool_use":
                        raw_name = blk.get("name") or "?"
                        tool_use_names_by_id[blk.get("id")] = raw_name
                        display_name = _display_tool_name(raw_name)
                        this_msg_tools.append(display_name)
                        if display_name == "Bash":
                            cmd = (blk.get("input") or {}).get("command", "")
                            if cmd:
                                this_msg_bash.append(cmd)

                if since is not None and ts_day and ts_day < since:
                    continue
                key = row.get("requestId") or message.get("id")
                if key in seen_request_ids:
                    continue
                seen_request_ids.add(key)

                usage = message["usage"]
                records.append(RequestRecord(
                    project=project, session=session, is_sub=is_sub, sub_name=sub_name,
                    day=ts_day, model=message.get("model"), git_branch=row.get("gitBranch"),
                    in_tokens=usage.get("input_tokens", 0) or 0,
                    cache_write=usage.get("cache_creation_input_tokens", 0) or 0,
                    cache_read=usage.get("cache_read_input_tokens", 0) or 0,
                    out_tokens=usage.get("output_tokens", 0) or 0,
                    tools=tuple(this_msg_tools), bash_commands=tuple(this_msg_bash),
                ))
            elif row_type == "user" and message and (since is None or not ts_day or ts_day >= since):
                content = message.get("content")
                blocks = content if isinstance(content, list) else []
                for blk in blocks:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        result_content = blk.get("content")
                        if isinstance(result_content, str):
                            n_chars = len(result_content)
                        else:
                            n_chars = sum(
                                len(x.get("text", ""))
                                for x in (result_content or [])
                                if isinstance(x, dict)
                            )
                        raw_name = tool_use_names_by_id.get(blk.get("tool_use_id"), "?")
                        name = _display_tool_name(raw_name)
                        tool_result_stats[name][0] += 1
                        tool_result_stats[name][1] += n_chars

    return records, tool_result_stats, session_meta, compact_count


def collect(
    root: Path = DEFAULT_TRANSCRIPT_ROOT, since: Optional[str] = None,
) -> Tuple[List[RequestRecord], Dict[str, List[int]], Dict[str, dict], int]:
    """Walks and streams every matching transcript file under `root`, merging per-file results.
    Returns an empty result (never raises) if `root` doesn't exist or no files match -- callers
    must treat an empty `records` list as "unavailable on this machine", not an error."""
    all_records: List[RequestRecord] = []
    all_tool_stats: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    all_session_meta: Dict[str, dict] = {}
    total_compacts = 0

    for f in iter_transcript_files(root, since):
        records, tool_stats, session_meta, compacts = parse_transcript_file(f, since, root=root)
        all_records.extend(records)
        for name, (n, chars) in tool_stats.items():
            all_tool_stats[name][0] += n
            all_tool_stats[name][1] += chars
        all_session_meta.update(session_meta)
        total_compacts += compacts

    return all_records, dict(all_tool_stats), all_session_meta, total_compacts


def _mb(v: float) -> str:
    return f"{v / 1e6:,.1f}M"


def _aggregate_by(records: List[RequestRecord], key_fn) -> Dict[str, dict]:
    agg: Dict[str, dict] = defaultdict(lambda: {"n": 0, "in": 0, "cw": 0, "cr": 0, "out": 0, "ctx_max": 0})
    for r in records:
        bucket = agg[key_fn(r)]
        bucket["n"] += 1
        bucket["in"] += r.in_tokens
        bucket["cw"] += r.cache_write
        bucket["cr"] += r.cache_read
        bucket["out"] += r.out_tokens
        bucket["ctx_max"] = max(bucket["ctx_max"], r.context_tokens)
    return dict(agg)


def _session_display_name(record: RequestRecord, session_meta: Dict[str, dict]) -> str:
    meta = session_meta.get(record.session, {})
    name = meta.get("agent-name") or meta.get("custom-title") or record.session[:8]
    return f"{name} [{record.project[:28]}]"


def context_size_buckets(records: List[RequestRecord]) -> Dict[str, dict]:
    counts: Dict[str, int] = defaultdict(int)
    token_totals: Dict[str, int] = defaultdict(int)
    for r in records:
        c = r.context_tokens
        for label, upper in _CONTEXT_BUCKETS:
            if c < upper:
                counts[label] += 1
                token_totals[label] += c
                break
    total_tokens = sum(token_totals.values()) or 1
    return {
        label: {
            "requests": counts.get(label, 0),
            "share_of_context_tokens": token_totals.get(label, 0) / total_tokens,
        }
        for label, _ in _CONTEXT_BUCKETS
    }


def attribute_by_tool(records: List[RequestRecord]) -> Tuple[Dict[str, dict], dict]:
    """A request that emits tool_use calls is always followed by another full-context request
    once they return, so a tool's per-call cost is approximated as a share of the context size of
    the request that invoked it -- split evenly when a single request calls more than one tool.
    Requests with no tool calls (a turn-ending, text-only reply) are tracked separately as
    `text_only`, not silently dropped from the total."""
    by_tool: Dict[str, List[float]] = defaultdict(lambda: [0, 0.0])
    text_only_calls = 0
    text_only_ctx = 0
    for r in records:
        ctx = r.context_tokens
        if not r.tools:
            text_only_calls += 1
            text_only_ctx += ctx
            continue
        share = ctx / len(r.tools)
        for t in r.tools:
            by_tool[t][0] += 1
            by_tool[t][1] += share
    result = {name: {"calls": int(n), "context_tokens": ctx} for name, (n, ctx) in by_tool.items()}
    return result, {"calls": text_only_calls, "context_tokens": text_only_ctx}


def attribute_by_bash_family(records: List[RequestRecord]) -> Dict[str, dict]:
    by_family: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for r in records:
        if not r.bash_commands:
            continue
        ctx = r.context_tokens
        for cmd in r.bash_commands:
            fam = _bash_family(cmd)
            by_family[fam][0] += 1
            by_family[fam][1] += ctx
    return {fam: {"calls": n, "context_tokens": ctx} for fam, (n, ctx) in by_family.items()}


def attribute_by_git_branch(records: List[RequestRecord]) -> Dict[str, dict]:
    """Per-branch cost -- a proxy for per-batch cost, since this repo's own convention is one
    branch per unit of work (CLAUDE.md's Worktree & Branch Isolation section)."""
    return _aggregate_by(records, lambda r: r.git_branch or "(no branch recorded)")


def build_report(
    records: List[RequestRecord],
    tool_result_stats: Dict[str, List[int]],
    session_meta: Dict[str, dict],
    compact_count: int = 0,
) -> dict:
    """Pure aggregation over already-collected data -- no filesystem access. This is what every
    consumer (the CLI, `generate_retro.py`) actually renders from, and what tests exercise
    directly against synthetic `RequestRecord` lists."""
    if not records:
        return {"available": False, "reason": "no matching transcript requests found"}

    totals = _aggregate_by(records, lambda r: "ALL")["ALL"]
    by_day = _aggregate_by(records, lambda r: r.day)
    by_model = _aggregate_by(records, lambda r: r.model or "(unknown)")
    by_main_vs_sub = _aggregate_by(records, lambda r: "subagent" if r.is_sub else "main")
    by_session = _aggregate_by(records, lambda r: _session_display_name(r, session_meta))
    by_branch = attribute_by_git_branch(records)
    buckets = context_size_buckets(records)
    tool_attribution, text_only = attribute_by_tool(records)
    bash_attribution = attribute_by_bash_family(records)

    tool_result_sizes = {
        name: {"calls": n, "total_chars": chars, "avg_chars": chars / n if n else 0}
        for name, (n, chars) in tool_result_stats.items()
    }

    return {
        "available": True,
        "request_count": len(records),
        "compact_boundary_count": compact_count,
        "totals": totals,
        "by_day": by_day,
        "by_model": by_model,
        "by_main_vs_subagent": by_main_vs_sub,
        "by_session": by_session,
        "by_git_branch": by_branch,
        "context_size_buckets": buckets,
        "attribution_by_tool": tool_attribution,
        "attribution_text_only": text_only,
        "attribution_by_bash_family": bash_attribution,
        "tool_result_sizes": tool_result_sizes,
    }


def _fmt_row(key: str, x: dict) -> str:
    avg = (x["in"] + x["cw"] + x["cr"]) / max(x["n"], 1)
    return (
        f"| {key} | {x['n']:,} | {_mb(x['in'])} | {_mb(x['cw'])} | {_mb(x['cr'])} | "
        f"{_mb(x['out'])} | {avg / 1e3:,.0f}k | {x['ctx_max'] / 1e3:,.0f}k |"
    )


def render_markdown(report: dict, top: int = 15) -> str:
    """Renders `build_report()`'s dict as the same markdown table shapes this was prototyped
    with, so a human reading the CLI output or `generate_retro.py`'s new section sees identical
    columns."""
    if not report.get("available"):
        return f"_Real token usage unavailable this run: {report.get('reason', 'unknown')}._"

    lines: List[str] = []
    lines.append(f"Requests: {report['request_count']:,}. Compaction boundaries seen: "
                 f"{report['compact_boundary_count']:,}.")
    lines.append("")

    def show(title: str, agg: Dict[str, dict], sort_key="cr+cw", limit=top):
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| key | reqs | uncached in | cache write | cache read | output | avg ctx/req | max ctx |")
        lines.append("|---|---|---|---|---|---|---|---|")
        items = sorted(agg.items(), key=lambda kv: -(kv[1]["cr"] + kv[1]["cw"]))[:limit]
        for k, x in items:
            lines.append(_fmt_row(str(k), x))
        lines.append("")

    show("Totals", {"ALL": report["totals"]}, limit=1)
    show("By day", dict(sorted(report["by_day"].items())), limit=60)
    show("By model", report["by_model"])
    show("Main session vs. subagent", report["by_main_vs_subagent"])
    show("By session", report["by_session"], limit=20)
    show("By git branch (per-batch cost)", report["by_git_branch"], limit=20)

    lines.append("### Context size per request")
    lines.append("")
    lines.append("| bucket | requests | share of context tokens |")
    lines.append("|---|---|---|")
    for label, _ in _CONTEXT_BUCKETS:
        b = report["context_size_buckets"][label]
        lines.append(f"| {label} | {b['requests']:,} | {b['share_of_context_tokens']:.0%} |")
    lines.append("")

    lines.append("### Context attribution by tool")
    lines.append("")
    lines.append("| tool | calls | context tokens attributed |")
    lines.append("|---|---|---|")
    tool_items = sorted(report["attribution_by_tool"].items(), key=lambda kv: -kv[1]["context_tokens"])
    for name, x in tool_items[:top]:
        lines.append(f"| {name} | {x['calls']:,} | {_mb(x['context_tokens'])} |")
    text_only = report["attribution_text_only"]
    lines.append(f"| _(text-only, no tool call)_ | {text_only['calls']:,} | {_mb(text_only['context_tokens'])} |")
    lines.append("")

    lines.append("### Bash command family attribution")
    lines.append("")
    lines.append("| bash family | calls | context tokens | avg ctx/call |")
    lines.append("|---|---|---|---|")
    bash_items = sorted(report["attribution_by_bash_family"].items(), key=lambda kv: -kv[1]["context_tokens"])
    for fam, x in bash_items[:25]:
        avg = x["context_tokens"] / x["calls"] if x["calls"] else 0
        lines.append(f"| `{fam}` | {x['calls']:,} | {_mb(x['context_tokens'])} | {avg / 1e3:,.0f}k |")
    lines.append("")

    lines.append("### Tool result sizes (what came back)")
    lines.append("")
    lines.append("| tool | calls | total chars | avg chars |")
    lines.append("|---|---|---|---|")
    result_items = sorted(report["tool_result_sizes"].items(), key=lambda kv: -kv[1]["total_chars"])
    for name, x in result_items[:top]:
        lines.append(f"| {name} | {x['calls']:,} | {_mb(x['total_chars'])} | {x['avg_chars']:,.0f} |")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Real token usage from local Claude Code transcripts. Developer-machine-only "
        "-- reads ~/.claude/projects/**/*.jsonl, not available in CI or from a fresh clone."
    )
    parser.add_argument("--since", default=None, help="ISO date, e.g. 2026-09-07. Default: all history found.")
    parser.add_argument("--root", default=None, help="Override the transcript root (mainly for testing).")
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else DEFAULT_TRANSCRIPT_ROOT
    records, tool_stats, session_meta, compacts = collect(root, args.since)
    report = build_report(records, tool_stats, session_meta, compacts)
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
