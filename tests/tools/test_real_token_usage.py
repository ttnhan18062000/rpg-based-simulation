"""Tests for tools/agent-monitoring/real_token_usage.py.

TCK-20260921-REAL-TOKEN-TELEMETRY. Every fixture here is synthetic, built in-test — nothing real
is read from `~/.claude/projects/` or committed. This mirrors the module's own hard rule: real
transcripts hold private conversation text and must never land in this repo, even as a test
fixture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from real_token_usage import (  # noqa: E402
    RequestRecord,
    attribute_by_bash_family,
    attribute_by_git_branch,
    attribute_by_tool,
    build_report,
    collect,
    context_size_buckets,
    iter_transcript_files,
    parse_transcript_file,
    render_markdown,
)


# ---------------------------------------------------------------------------
# Synthetic transcript fixture builder
# ---------------------------------------------------------------------------


def _assistant_row(
    request_id, ts, usage, model="claude-sonnet-5", git_branch="main",
    tool_use=None,
):
    content = []
    if tool_use:
        for name, tool_id, tool_input in tool_use:
            content.append({"type": "tool_use", "id": tool_id, "name": name, "input": tool_input})
    else:
        content.append({"type": "text", "text": "a reply"})
    return {
        "type": "assistant",
        "timestamp": ts,
        "requestId": request_id,
        "gitBranch": git_branch,
        "message": {"id": request_id, "model": model, "usage": usage, "content": content},
    }


def _user_tool_result_row(ts, tool_use_id, result_text):
    return {
        "type": "user",
        "timestamp": ts,
        "message": {"content": [
            {"type": "tool_result", "tool_use_id": tool_use_id, "content": result_text},
        ]},
    }


def _write_transcript(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _usage(inp=1000, cw=0, cr=0, out=200):
    return {
        "input_tokens": inp, "cache_creation_input_tokens": cw,
        "cache_read_input_tokens": cr, "output_tokens": out,
    }


# ---------------------------------------------------------------------------
# parse_transcript_file
# ---------------------------------------------------------------------------


def test_parse_transcript_file_extracts_basic_usage(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-abc.jsonl"
    rows = [
        {"type": "custom-title", "customTitle": "my-role"},
        _assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(1000, 0, 0, 200)),
    ]
    _write_transcript(session_file, rows)

    records, tool_stats, session_meta, compacts = parse_transcript_file(session_file, since=None, root=root)

    assert len(records) == 1
    r = records[0]
    assert r.in_tokens == 1000 and r.out_tokens == 200
    assert r.day == "2026-09-10"
    assert r.git_branch == "main"
    assert r.session == "session-abc"
    assert r.is_sub is False
    assert session_meta["session-abc"]["custom-title"] == "my-role"
    assert compacts == 0


def test_parse_transcript_file_dedupes_by_request_id(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-dup.jsonl"
    rows = [
        _assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(1000)),
        # same requestId repeated -- happens because usage repeats on every content block
        _assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(1000)),
    ]
    _write_transcript(session_file, rows)

    records, _, _, _ = parse_transcript_file(session_file, since=None, root=root)
    assert len(records) == 1


def test_parse_transcript_file_since_filter_excludes_earlier_rows(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-since.jsonl"
    rows = [
        _assistant_row("req-old", "2026-09-01T10:00:00Z", _usage(1000)),
        _assistant_row("req-new", "2026-09-15T10:00:00Z", _usage(2000)),
    ]
    _write_transcript(session_file, rows)

    records, _, _, _ = parse_transcript_file(session_file, since="2026-09-07", root=root)
    assert len(records) == 1
    assert records[0].in_tokens == 2000


def test_parse_transcript_file_detects_subagent_path(tmp_path):
    root = tmp_path / "projects"
    session_file = (
        root / "-home-u24desktop-Working-rpg-based-simulation" / "session-x"
        / "subagents" / "fork-1.jsonl"
    )
    rows = [_assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(500))]
    _write_transcript(session_file, rows)

    records, _, _, _ = parse_transcript_file(session_file, since=None, root=root)
    assert records[0].is_sub is True
    assert records[0].sub_name == "fork-1"


def test_parse_transcript_file_counts_compact_boundaries(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-c.jsonl"
    rows = [
        _assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(500)),
        {"type": "system", "subtype": "compact_boundary"},
        _assistant_row("req-2", "2026-09-10T10:05:00Z", _usage(500)),
    ]
    _write_transcript(session_file, rows)

    records, _, _, compacts = parse_transcript_file(session_file, since=None, root=root)
    assert len(records) == 2
    assert compacts == 1


def test_parse_transcript_file_tool_result_sizes_are_char_counts_not_content(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-tools.jsonl"
    rows = [
        _assistant_row(
            "req-1", "2026-09-10T10:00:00Z", _usage(500),
            tool_use=[("Bash", "tu-1", {"command": "git status"})],
        ),
        _user_tool_result_row("2026-09-10T10:00:01Z", "tu-1", "0123456789"),
    ]
    _write_transcript(session_file, rows)

    records, tool_stats, _, _ = parse_transcript_file(session_file, since=None, root=root)
    assert tool_stats["Bash"] == [1, 10]
    assert records[0].bash_commands == ("git status",)


def test_parse_transcript_file_mcp_tool_name_shortened(tmp_path):
    root = tmp_path / "projects"
    session_file = root / "-home-u24desktop-Working-rpg-based-simulation" / "session-mcp.jsonl"
    rows = [
        _assistant_row(
            "req-1", "2026-09-10T10:00:00Z", _usage(500),
            tool_use=[("mcp__knowledge-search__search_docs", "tu-1", {})],
        ),
        _user_tool_result_row("2026-09-10T10:00:01Z", "tu-1", "abc"),
    ]
    _write_transcript(session_file, rows)

    records, tool_stats, _, _ = parse_transcript_file(session_file, since=None, root=root)
    assert records[0].tools == ("mcp:knowledge-search",)
    assert "mcp:knowledge-search" in tool_stats


def test_parse_transcript_file_missing_file_returns_empty_not_error(tmp_path):
    records, tool_stats, meta, compacts = parse_transcript_file(
        tmp_path / "does-not-exist.jsonl", since=None, root=tmp_path,
    )
    assert records == []
    assert tool_stats == {}
    assert meta == {}
    assert compacts == 0


# ---------------------------------------------------------------------------
# iter_transcript_files / collect
# ---------------------------------------------------------------------------


def test_iter_transcript_files_returns_nothing_for_missing_root(tmp_path):
    missing = tmp_path / "does-not-exist"
    assert list(iter_transcript_files(missing)) == []


def test_collect_walks_synthetic_project_tree_end_to_end(tmp_path):
    root = tmp_path / "projects"
    proj = root / "-home-u24desktop-Working-rpg-based-simulation--claude-worktrees-foo"
    _write_transcript(proj / "session-1.jsonl", [
        {"type": "agent-name", "agentName": "implementer"},
        _assistant_row("req-1", "2026-09-10T10:00:00Z", _usage(1000, 0, 0, 200), git_branch="feature-a"),
    ])
    _write_transcript(proj / "session-1" / "subagents" / "fork-a.jsonl", [
        _assistant_row("req-2", "2026-09-10T10:01:00Z", _usage(500, 0, 0, 50), git_branch="feature-a"),
    ])

    records, tool_stats, session_meta, compacts = collect(root, since=None)
    assert len(records) == 2
    assert sum(1 for r in records if r.is_sub) == 1
    assert session_meta["session-1"]["agent-name"] == "implementer"


def test_collect_returns_empty_for_nonexistent_root_not_error(tmp_path):
    records, tool_stats, meta, compacts = collect(tmp_path / "nope", since=None)
    assert records == []
    assert tool_stats == {}
    assert meta == {}
    assert compacts == 0


# ---------------------------------------------------------------------------
# Aggregation — synthetic RequestRecord objects, no filesystem at all
# ---------------------------------------------------------------------------


def _rec(**kwargs):
    defaults = dict(
        project="proj", session="s1", is_sub=False, sub_name="", day="2026-09-10",
        model="claude-sonnet-5", git_branch="main", in_tokens=1000, cache_write=0,
        cache_read=0, out_tokens=100, tools=(), bash_commands=(),
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


def test_context_tokens_property_sums_in_cache_write_cache_read():
    r = _rec(in_tokens=100, cache_write=20, cache_read=30)
    assert r.context_tokens == 150


def test_context_size_buckets_places_records_in_correct_bucket():
    records = [
        _rec(in_tokens=10_000),      # <50k
        _rec(in_tokens=600_000),     # >=500k
    ]
    buckets = context_size_buckets(records)
    assert buckets["<50k"]["requests"] == 1
    assert buckets[">=500k"]["requests"] == 1
    assert buckets["50-100k"]["requests"] == 0


def test_attribute_by_tool_splits_context_evenly_across_multiple_tools():
    records = [_rec(in_tokens=1000, tools=("Bash", "Read"))]
    by_tool, text_only = attribute_by_tool(records)
    assert by_tool["Bash"]["context_tokens"] == 500
    assert by_tool["Read"]["context_tokens"] == 500
    assert text_only["calls"] == 0


def test_attribute_by_tool_tracks_text_only_requests_separately():
    records = [_rec(in_tokens=1000, tools=())]
    by_tool, text_only = attribute_by_tool(records)
    assert by_tool == {}
    assert text_only == {"calls": 1, "context_tokens": 1000}


def test_attribute_by_bash_family_classifies_git_subcommand():
    records = [_rec(in_tokens=1000, bash_commands=("git status", "git log --oneline"))]
    by_family = attribute_by_bash_family(records)
    assert "git status" in by_family
    assert "git log" in by_family
    assert by_family["git status"]["calls"] == 1


def test_attribute_by_git_branch_groups_correctly():
    records = [
        _rec(git_branch="feature-a", in_tokens=100),
        _rec(git_branch="feature-a", in_tokens=200),
        _rec(git_branch="feature-b", in_tokens=50),
        _rec(git_branch=None, in_tokens=10),
    ]
    by_branch = attribute_by_git_branch(records)
    assert by_branch["feature-a"]["n"] == 2
    assert by_branch["feature-a"]["in"] == 300
    assert by_branch["feature-b"]["n"] == 1
    assert by_branch["(no branch recorded)"]["n"] == 1


def test_build_report_returns_unavailable_for_empty_records():
    report = build_report([], {}, {}, 0)
    assert report["available"] is False
    assert "reason" in report


def test_build_report_full_shape_with_synthetic_records():
    records = [
        _rec(day="2026-09-10", model="claude-sonnet-5", git_branch="feature-a",
             tools=("Bash",), bash_commands=("git status",)),
        _rec(day="2026-09-11", model="claude-opus-5", git_branch="feature-b",
             is_sub=True, tools=()),
    ]
    tool_stats = {"Bash": [1, 500]}
    session_meta = {"s1": {"agent-name": "implementer"}}
    report = build_report(records, tool_stats, session_meta, compact_count=2)

    assert report["available"] is True
    assert report["request_count"] == 2
    assert report["compact_boundary_count"] == 2
    assert report["totals"]["n"] == 2
    assert "2026-09-10" in report["by_day"]
    assert "claude-sonnet-5" in report["by_model"]
    assert report["by_main_vs_subagent"]["main"]["n"] == 1
    assert report["by_main_vs_subagent"]["subagent"]["n"] == 1
    assert "feature-a" in report["by_git_branch"]
    assert report["attribution_text_only"]["calls"] == 1
    assert "Bash" in report["tool_result_sizes"]


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------


def test_render_markdown_unavailable_report_is_a_short_note():
    out = render_markdown({"available": False, "reason": "no matching transcript requests found"})
    assert "unavailable" in out
    assert "no matching transcript requests found" in out


def test_render_markdown_available_report_includes_expected_sections():
    records = [_rec(tools=("Bash",), bash_commands=("git status",))]
    report = build_report(records, {"Bash": [1, 100]}, {}, 0)
    out = render_markdown(report)
    assert "### By day" in out
    assert "### By git branch (per-batch cost)" in out
    assert "### Context size per request" in out
    assert "### Context attribution by tool" in out
    assert "### Bash command family attribution" in out
    assert "### Tool result sizes (what came back)" in out
