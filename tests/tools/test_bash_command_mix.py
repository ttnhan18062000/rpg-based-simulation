"""Tests for tools/agent-monitoring/bash_command_mix.py (TCK-20260923-BASH-COMMAND-MIX-BASELINE).

Mirrors tests/tools/test_agent_tool_usage_baseline.py's design: inline-dict unit tests per
function (no file I/O for synthetic-fixture cases), an ast-based reuse guard proving this module
composes validate.py's load_jsonl_with_line_count rather than reimplementing a shard reader, a
tmp_path-constructed fixture for the week-range-filtered glob case, and real-corpus integration
tests (sanity-check reconciliation, read-only guard via file-size snapshotting, CLI smoke test in
both markdown and --json modes) — never fixtures for those, which would make the corresponding
assertion vacuous.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "bash_command_mix.py"
_REAL_DATA_DIR = _REPO_ROOT / "agent-monitoring" / "data"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from bash_command_mix import (  # noqa: E402
    SEARCH_DOCS_TOOL_NAME,
    bash_head,
    bash_subcommand_key,
    build_bash_mix_report,
    load_tools_rows,
    load_tools_rows_from_ref,
    load_tools_rows_with_line_count,
    render_markdown,
    resolve_ref_sha,
    week_shards,
)

_MODULE_SOURCE = _MODULE_PATH.read_text()
_MODULE_AST = ast.parse(_MODULE_SOURCE)


def _imported_names() -> set:
    names = set()
    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


# ---------------------------------------------------------------------------
# bash_head / bash_subcommand_key — pure classification
# ---------------------------------------------------------------------------

def test_bash_head_returns_first_word():
    assert bash_head("cd /home/u/Working/repo") == "cd"
    assert bash_head("grep -n 'foo' -r src/") == "grep"
    assert bash_head("  git status  ") == "git"


def test_bash_head_handles_empty_or_missing_summary():
    assert bash_head("") == "?"
    assert bash_head(None) == "?"
    assert bash_head("   ") == "?"


def test_bash_subcommand_key_breaks_down_known_heads_only():
    assert bash_subcommand_key("git", "git status") == "git status"
    assert bash_subcommand_key("git", "git diff --stat") == "git diff"
    assert bash_subcommand_key("grep", "grep -n foo") == "grep -n"
    assert bash_subcommand_key("python3", "python3 -c 'print(1)'") == "python3 -c"


def test_bash_subcommand_key_leaves_non_breakdown_heads_bare():
    assert bash_subcommand_key("ls", "ls -la") == "ls"
    assert bash_subcommand_key("cd", "cd /some/path") == "cd"
    assert bash_subcommand_key("echo", "echo hi") == "echo"


def test_bash_subcommand_key_single_word_command_falls_back_to_head():
    assert bash_subcommand_key("git", "git") == "git"


# ---------------------------------------------------------------------------
# build_bash_mix_report — synthetic fixtures
# ---------------------------------------------------------------------------

def _row(tool, summary=None):
    r = {"tool": tool}
    if summary is not None:
        r["input_summary"] = summary
    return r


def test_report_counts_cd_and_head_mix_correctly():
    rows = [
        _row("Bash", "cd /a"),
        _row("Bash", "cd /b"),
        _row("Bash", "git status"),
        _row("Bash", "grep -n foo"),
        _row("Read", "src/foo.py"),
    ]
    report = build_bash_mix_report(rows)

    assert report["total_rows_seen"] == 5
    assert report["total_bash_calls"] == 4
    assert report["bash_share_of_all_calls"] == 4 / 5
    assert report["cd_calls"] == 2
    assert report["cd_share_of_bash_calls"] == 2 / 4
    assert report["bash_head_counts"]["cd"] == 2
    assert report["bash_head_counts"]["git"] == 1
    assert report["bash_head_counts"]["grep"] == 1
    assert report["bash_head_shares"]["cd"] == 2 / 4


def test_report_grep_to_search_docs_ratio_computed_when_search_docs_present():
    rows = (
        [_row("Bash", "grep -n foo")] * 10
        + [_row(SEARCH_DOCS_TOOL_NAME)] * 2
    )
    report = build_bash_mix_report(rows)

    assert report["grep_calls"] == 10
    assert report["search_docs_calls"] == 2
    assert report["grep_to_search_docs_ratio"] == 5.0


def test_report_ratio_is_labeled_string_not_fabricated_when_zero_search_docs():
    rows = [_row("Bash", "grep -n foo")] * 3
    report = build_bash_mix_report(rows)

    assert report["search_docs_calls"] == 0
    assert isinstance(report["grep_to_search_docs_ratio"], str)
    assert "undefined" in report["grep_to_search_docs_ratio"]


def test_report_empty_corpus_does_not_divide_by_zero():
    report = build_bash_mix_report([])
    assert report["total_rows_seen"] == 0
    assert report["total_bash_calls"] == 0
    assert report["bash_share_of_all_calls"] == 0.0
    assert report["cd_share_of_bash_calls"] == 0.0


def test_report_rg_head_counts_toward_grep_calls_too():
    rows = [_row("Bash", "rg -n foo")]
    report = build_bash_mix_report(rows)
    assert report["grep_calls"] == 1


def test_report_carries_since_through_week_labels_through():
    report = build_bash_mix_report([], since_week="2026-W30", through_week="2026-W39")
    assert report["since_week"] == "2026-W30"
    assert report["through_week"] == "2026-W39"


# ---------------------------------------------------------------------------
# render_markdown — smoke test on synthetic report
# ---------------------------------------------------------------------------

def test_render_markdown_includes_cd_and_ratio_lines():
    rows = [_row("Bash", "cd /a"), _row("Bash", "grep -n foo"), _row(SEARCH_DOCS_TOOL_NAME)]
    report = build_bash_mix_report(rows, since_week="2026-W30", through_week="2026-W39")
    md = render_markdown(report)

    assert "2026-W30..2026-W39" in md
    assert "`cd`:" in md
    assert "search_docs" in md
    assert "### Bash command head mix" in md


# ---------------------------------------------------------------------------
# week_shards / load_tools_rows — week-range filtering, tmp_path fixture
# ---------------------------------------------------------------------------

def test_week_shards_filters_to_inclusive_range(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    for week in ("2026-W28", "2026-W29", "2026-W30", "2026-W31"):
        (data_dir / week).mkdir(parents=True)
        (data_dir / week / "tools.jsonl").write_text(
            json.dumps({"tool": "Bash", "input_summary": f"echo {week}"}) + "\n"
        )

    shards = week_shards(data_dir, since_week="2026-W29", through_week="2026-W30")
    weeks_matched = {s.parent.name for s in shards}
    assert weeks_matched == {"2026-W29", "2026-W30"}


def test_load_tools_rows_respects_week_range(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    (data_dir / "2026-W02").mkdir(parents=True)
    (data_dir / "2026-W01" / "tools.jsonl").write_text(
        json.dumps({"tool": "Bash", "input_summary": "cd /a"}) + "\n"
    )
    (data_dir / "2026-W02" / "tools.jsonl").write_text(
        json.dumps({"tool": "Bash", "input_summary": "cd /b"}) + "\n"
    )

    all_rows = load_tools_rows(data_dir)
    assert len(all_rows) == 2

    w1_only = load_tools_rows(data_dir, since_week="2026-W01", through_week="2026-W01")
    assert len(w1_only) == 1
    assert w1_only[0]["input_summary"] == "cd /a"


def test_load_tools_rows_with_line_count_matches_row_count(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    (data_dir / "2026-W01" / "tools.jsonl").write_text(
        json.dumps({"tool": "Bash", "input_summary": "cd /a"}) + "\n"
        + json.dumps({"tool": "Read", "input_summary": "b"}) + "\n"
    )

    rows, line_count = load_tools_rows_with_line_count(data_dir)
    assert len(rows) == 2
    assert line_count == 2


# ---------------------------------------------------------------------------
# Reuse guard — must compose validate.py's shard reader, not reimplement one
# ---------------------------------------------------------------------------

def test_reuses_load_jsonl_with_line_count_not_a_fresh_reader():
    imported = _imported_names()
    assert "load_jsonl_with_line_count" in imported

    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.Import):
            assert node.names[0].name != "sqlite3", "must not connect to the index db directly"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"read_text", "read_bytes", "readlines"}, (
                "must not read a *.jsonl file directly — reuse load_jsonl_with_line_count"
            )


# ---------------------------------------------------------------------------
# Real-corpus integration — sanity check, read-only guard, CLI smoke test
# ---------------------------------------------------------------------------

def test_sum_of_head_counts_matches_total_bash_calls_on_real_corpus():
    rows, real_total = load_tools_rows_with_line_count(_REAL_DATA_DIR)
    report = build_bash_mix_report(rows)

    assert report["total_rows_seen"] == real_total
    assert sum(report["bash_head_counts"].values()) == report["total_bash_calls"]


def _file_size_snapshot() -> dict:
    return {str(p): p.stat().st_size for p in _REAL_DATA_DIR.rglob("*") if p.is_file()}


def test_script_is_read_only_against_real_agent_monitoring_data():
    """Same rationale as test_agent_tool_usage_baseline.py's sibling test: proves this script
    never truncates or deletes existing content under agent-monitoring/data/, without racing a
    concurrent session's own append-only PostToolUse hook writes during the test's wall-clock
    window (growth and new files are expected and not attributable to this script)."""
    assert _REAL_DATA_DIR.is_dir()
    assert "tmp" not in str(_REAL_DATA_DIR).lower()

    pre_sizes = _file_size_snapshot()
    rows = load_tools_rows(_REAL_DATA_DIR)
    build_bash_mix_report(rows)
    post_sizes = _file_size_snapshot()

    deleted = set(pre_sizes) - set(post_sizes)
    assert not deleted, f"bash_command_mix appears to have deleted real files: {sorted(deleted)}"
    shrunk = {
        path: (pre_sizes[path], post_sizes[path])
        for path in pre_sizes
        if path in post_sizes and post_sizes[path] < pre_sizes[path]
    }
    assert not shrunk, f"bash_command_mix appears to have truncated real files: {shrunk}"


def test_cli_runs_against_real_corpus_and_prints_markdown():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--since-week", "2026-W30", "--through-week", "2026-W39"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    assert "Bash command head mix" in result.stdout
    assert "cd" in result.stdout


def test_cli_runs_with_json_flag_and_prints_valid_report():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--json", "--since-week", "2026-W30", "--through-week", "2026-W39"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["ticket_id"] == "TCK-20260923-BASH-COMMAND-MIX-BASELINE"
    assert report["since_week"] == "2026-W30"
    assert report["through_week"] == "2026-W39"
    assert sum(report["bash_head_counts"].values()) == report["total_bash_calls"]
    assert report["measured_ref"] is None
    assert report["measured_sha"] is None


# ---------------------------------------------------------------------------
# --ref mode — git-blob-based reading, immune to worktree staleness
# (TCK-20260923-BASH-MIX-REF-PINNING)
# ---------------------------------------------------------------------------

def test_resolve_ref_sha_returns_a_real_sha_for_head():
    sha = resolve_ref_sha("HEAD")
    assert len(sha) == 40
    assert all(c in "0123456789abcdef" for c in sha)


def test_load_tools_rows_from_ref_is_a_prior_or_equal_snapshot_of_the_working_tree():
    """HEAD's committed tools.jsonl shards can never exceed the live working tree's row count —
    the corpus is append-only between commits (every session's own PostToolUse hook only adds
    rows), so a --ref HEAD read is always a prior-or-equal snapshot, never a divergent one. Exact
    equality is NOT asserted here on purpose: this test runs against the real, live corpus, and a
    concurrent session's hook write between this test's two reads would make the working tree
    strictly ahead of HEAD — which is precisely the staleness gap this feature exists to make
    checkable via measured_sha, not a bug in either read."""
    fs_rows = load_tools_rows(_REAL_DATA_DIR)
    ref_rows, sha = load_tools_rows_from_ref("HEAD")

    assert len(sha) == 40
    assert len(ref_rows) > 0
    assert len(ref_rows) <= len(fs_rows)


def test_load_tools_rows_from_ref_respects_week_range():
    all_rows, _ = load_tools_rows_from_ref("HEAD")
    bounded_rows, _ = load_tools_rows_from_ref("HEAD", since_week="2026-W30", through_week="2026-W30")
    assert len(bounded_rows) <= len(all_rows)
    assert len(bounded_rows) > 0


def test_build_bash_mix_report_carries_measured_ref_and_sha_when_given():
    report = build_bash_mix_report([], measured_ref="origin/main", measured_sha="abc123")
    assert report["measured_ref"] == "origin/main"
    assert report["measured_sha"] == "abc123"


def test_render_markdown_shows_measured_ref_when_present():
    report = build_bash_mix_report([], measured_ref="origin/main", measured_sha="deadbeef")
    md = render_markdown(report)
    assert "origin/main" in md
    assert "deadbeef" in md


def test_render_markdown_warns_local_working_tree_when_ref_absent():
    report = build_bash_mix_report([])
    md = render_markdown(report)
    assert "local working tree" in md


def test_cli_ref_mode_prints_measured_ref_and_sha_in_json():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--json", "--ref", "HEAD",
         "--since-week", "2026-W30", "--through-week", "2026-W30"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["measured_ref"] == "HEAD"
    assert len(report["measured_sha"]) == 40
    assert sum(report["bash_head_counts"].values()) == report["total_bash_calls"]


def test_cli_ref_mode_never_touches_working_tree():
    """Read-only guard, ref-mode variant: --ref must never write to agent-monitoring/data/, same
    property the filesystem-mode test proves for the default path."""
    pre_sizes = _file_size_snapshot()
    subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--ref", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    post_sizes = _file_size_snapshot()

    deleted = set(pre_sizes) - set(post_sizes)
    assert not deleted
    shrunk = {p: (pre_sizes[p], post_sizes[p]) for p in pre_sizes if p in post_sizes and post_sizes[p] < pre_sizes[p]}
    assert not shrunk
