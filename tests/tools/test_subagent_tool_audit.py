"""Tests for tools/agent-monitoring/subagent_tool_audit.py
(TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2).

Fixture-based: builds a synthetic ~/.claude/projects-shaped tree under tmp_path (never touches
real ~/.claude/projects or real .claude/agents/*.md), matching the real layout discovered against
this machine's own transcripts:
  <projects_root>/<session-id>/subagents/agent-<id>.{meta.json,jsonl}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring"))

import subagent_tool_audit  # noqa: E402


def _write_agent_md(agents_dir: Path, name: str, tools_line: str | None) -> None:
    fm = "---\nstatus: active\nlayer: ai\n"
    if tools_line is not None:
        fm += f"tools: {tools_line}\n"
    fm += "---\n\n# body\n"
    (agents_dir / f"{name}.md").write_text(fm, encoding="utf-8")


def _write_transcript(projects_root: Path, session_id: str, transcript_id: str, agent_type: str, lines: list) -> None:
    subagents_dir = projects_root / session_id / "subagents"
    subagents_dir.mkdir(parents=True, exist_ok=True)
    meta_path = subagents_dir / f"agent-{transcript_id}.meta.json"
    meta_path.write_text(json.dumps({"agentType": agent_type}), encoding="utf-8")
    jsonl_path = subagents_dir / f"agent-{transcript_id}.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _assistant_line(ts: str, tool_name: str) -> dict:
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"role": "assistant", "content": [{"type": "tool_use", "name": tool_name, "input": {}}]},
    }


def _no_such_tool_line(ts: str, tool_name: str) -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "message": {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "is_error": True,
                "content": f"<tool_use_error>Error: No such tool available: {tool_name}. "
                            f"{tool_name} is disabled for this session.</tool_use_error>",
            }],
        },
    }


def _setup_agents_dir(tmp_path, monkeypatch, *, scoped_tools=None):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    _write_agent_md(agents_dir, "scoped-agent", scoped_tools or "Read, Bash")
    _write_agent_md(agents_dir, "unscoped-agent", None)
    monkeypatch.setattr(subagent_tool_audit, "AGENTS_DIR", agents_dir)
    return agents_dir


def test_tool_calls_counted_under_meta_json_agent_type_not_transcript_body(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(
        projects_root, "s1", "t1", "scoped-agent",
        [{"type": "assistant", "timestamp": "2026-01-01T00:00:00Z",
          "message": {"role": "assistant", "content": [{"type": "text", "text": "the caller field says scoped-agent"}]}},
         _assistant_line("2026-01-01T00:00:01Z", "Read")],
    )
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert report["agents"]["scoped-agent"]["tool_calls_post"] == {"Read": 1}


def test_invocation_count_is_one_per_transcript_split_by_first_timestamp(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t-pre", "scoped-agent",
                       [_assistant_line("2026-01-01T00:00:00Z", "Read"),
                        _assistant_line("2026-01-01T00:00:01Z", "Read")])
    _write_transcript(projects_root, "s1", "t-post", "scoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Read")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since="2026-01-03T00:00:00Z")
    entry = report["agents"]["scoped-agent"]
    assert entry["invocations_pre"] == 1
    assert entry["invocations_post"] == 1
    # both Read calls in t-pre count toward pre, not split within the transcript
    assert entry["tool_calls_pre"] == {"Read": 2}
    assert entry["tool_calls_post"] == {"Read": 1}


def test_outside_allowlist_call_reported_only_after_since(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch, scoped_tools="Read, Bash")
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t-pre", "scoped-agent",
                       [_assistant_line("2026-01-01T00:00:00Z", "Edit")])
    _write_transcript(projects_root, "s1", "t-post", "scoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Edit")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since="2026-01-03T00:00:00Z")
    entry = report["agents"]["scoped-agent"]
    assert len(entry["outside_allowlist_post"]) == 1
    assert entry["outside_allowlist_post"][0]["tool"] == "Edit"
    assert entry["outside_allowlist_post"][0]["transcript"] == "agent-t-post.jsonl"


def test_no_such_tool_available_error_reported_with_agent_and_tool_name(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t1", "scoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "ListAgents"),
                        _no_such_tool_line("2026-01-05T00:00:01Z", "ListAgents")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since="2026-01-01T00:00:00Z")
    errors = report["agents"]["scoped-agent"]["no_such_tool_errors_post"]
    assert len(errors) == 1
    assert errors[0]["tool"] == "ListAgents"
    assert errors[0]["timestamp"] == "2026-01-05T00:00:01Z"


def test_agent_with_no_tools_line_reports_usage_but_no_outside_allowlist_entries(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t1", "unscoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Edit"),
                        _assistant_line("2026-01-05T00:00:01Z", "AnyTool")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since="2026-01-01T00:00:00Z")
    entry = report["agents"]["unscoped-agent"]
    assert entry["has_tools_allowlist"] is False
    assert entry["invocations_post"] == 1
    assert entry["outside_allowlist_post"] == []


def test_malformed_json_line_is_skipped_not_fatal(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    subagents_dir = projects_root / "s1" / "subagents"
    subagents_dir.mkdir(parents=True)
    (subagents_dir / "agent-t1.meta.json").write_text(json.dumps({"agentType": "scoped-agent"}))
    (subagents_dir / "agent-t1.jsonl").write_text(
        json.dumps(_assistant_line("2026-01-05T00:00:00Z", "Read")) + "\n"
        + "{not valid json,,,\n"
        + json.dumps(_assistant_line("2026-01-05T00:00:01Z", "Bash")) + "\n"
    )
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert report["agents"]["scoped-agent"]["tool_calls_post"] == {"Read": 1, "Bash": 1}


def test_transcript_missing_meta_json_is_skipped_not_fatal(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    subagents_dir = projects_root / "s1" / "subagents"
    subagents_dir.mkdir(parents=True)
    # jsonl with no sibling .meta.json
    (subagents_dir / "agent-orphan.jsonl").write_text(
        json.dumps(_assistant_line("2026-01-05T00:00:00Z", "Read")) + "\n"
    )
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert report["transcripts_seen"] == 0
    assert report["transcripts_skipped_unmatched_or_missing_meta"] == 0  # never yielded, not "skipped"


def test_run_is_read_only_fixture_untouched(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t1", "scoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Read")])
    jsonl_path = projects_root / "s1" / "subagents" / "agent-t1.jsonl"
    before_bytes = jsonl_path.read_bytes()
    before_mtime = jsonl_path.stat().st_mtime
    subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert jsonl_path.read_bytes() == before_bytes
    assert jsonl_path.stat().st_mtime == before_mtime


def test_output_states_projects_glob_and_date_range(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t1", "scoped-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Read")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert report["projects_dir_glob"] == str(projects_root) + "*"
    assert report["date_range_covered"]["earliest"] == "2026-01-05T00:00:00Z"
    assert report["date_range_covered"]["latest"] == "2026-01-05T00:00:00Z"
    assert "machine" in report


def test_unregistered_agent_type_is_skipped_and_counted(tmp_path, monkeypatch):
    _setup_agents_dir(tmp_path, monkeypatch)
    projects_root = tmp_path / "projects"
    _write_transcript(projects_root, "s1", "t1", "not-a-real-registered-agent",
                       [_assistant_line("2026-01-05T00:00:00Z", "Read")])
    report = subagent_tool_audit.build_report(str(projects_root) + "*", since=None)
    assert "not-a-real-registered-agent" not in report["agents"]
    assert report["transcripts_skipped_unmatched_or_missing_meta"] == 1


def test_default_projects_glob_strips_worktree_suffix_for_repo_slug():
    worktree_root = Path("/home/u/Working/repo/.claude/worktrees/some-feature")
    main_root = subagent_tool_audit._main_repo_root(worktree_root)
    assert main_root == Path("/home/u/Working/repo")
