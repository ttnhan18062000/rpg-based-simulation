"""Narrowed context-search PreToolUse hook (TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING)."""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

_MON = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
if str(_MON) not in sys.path:
    sys.path.insert(0, str(_MON))

import context_search_hook as hook  # noqa: E402


@pytest.fixture(autouse=True)
def _tmp_sentinels(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path / "sentinels"))
    (tmp_path / "sentinels").mkdir()


def _transcript(tmp_path, called_search_docs: bool, mention_only: bool = False) -> str:
    lines = [json.dumps({"type": "user", "message": {"content": "hi"}})]
    if mention_only:  # the tool NAME appears in a tool list, not as a tool_use block
        lines.append(json.dumps({"type": "attachment", "text": 'tools: {"name":"mcp__knowledge-search__search_docs"}'}))
    if called_search_docs:
        lines.append(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "mcp__knowledge-search__search_docs", "input": {"query": "x"}}]}}))
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def _payload(command, transcript, session="s1"):
    return {"session_id": session, "transcript_path": transcript, "tool_input": {"command": command}}


@pytest.mark.parametrize("command", [
    "git status", "git commit -m 'fix grep of src/ output'", "gh pr checks 12", "python3 tools/x.py --src src/",
    "python3 -m pytest tests/tools -k grep", "make knowledge-index", "cat > docs/new.md <<'EOF'\ngrep src/ docs/\nEOF",
    "echo hi > src/x.txt", "sed -i s/a/b/ src/a.py", "grep -rn foo tests/", "find . -name '*.py'", "ls docs/",
])
def test_ordinary_commands_and_non_src_docs_targets_give_no_reminder(command, tmp_path):
    assert hook.decide(_payload(command, _transcript(tmp_path, False))) is None


@pytest.mark.parametrize("command", [
    "grep -rn foo src/", "rg foo docs/", "find src -name '*.py'", "cat docs/guides/delivery_process.md", "head -20 src/core/state.py",
    "sed -n 1,40p src/a.py", "FOO=1 grep -n x ./docs/a.md", "git log | grep fix && cat src/a.py",
])
def test_an_investigation_read_of_src_or_docs_before_search_docs_gives_the_reminder(command, tmp_path):
    message = hook.decide(_payload(command, _transcript(tmp_path, False)))
    assert message and "search_docs" in message


def test_the_same_command_after_search_docs_gives_no_reminder(tmp_path):
    assert hook.decide(_payload("grep -rn foo src/", _transcript(tmp_path, True))) is None


def test_a_tool_name_that_only_appears_in_a_tool_list_is_not_a_call(tmp_path):
    assert hook.decide(_payload("grep -rn foo src/", _transcript(tmp_path, False, mention_only=True)))


def test_the_cli_fallback_counts_as_a_search(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": "python3 tools/knowledge_search.py query \"x\" --top-k 5"}}]}}) + "\n")
    assert hook.decide(_payload("grep -rn foo src/", str(path))) is None


def test_once_found_the_answer_is_cached_so_the_transcript_is_not_read_again(tmp_path):
    transcript = _transcript(tmp_path, True)
    assert hook.search_docs_called({"session_id": "cache-me", "transcript_path": transcript}) is True
    Path(transcript).unlink()
    assert hook.search_docs_called({"session_id": "cache-me", "transcript_path": transcript}) is True


@pytest.mark.parametrize("payload", [
    {"tool_input": {"command": "grep -rn foo src/"}},
    {"transcript_path": "/nonexistent/t.jsonl", "tool_input": {"command": "grep -rn foo src/"}},
    {"tool_input": {}}, {},
])
def test_when_it_cannot_tell_it_stays_silent(payload):
    assert hook.decide(payload) is None


def _run_main(monkeypatch, capsys, stdin):
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    code = hook.main()
    return code, capsys.readouterr().out


def test_main_prints_an_advisory_json_and_exits_zero(tmp_path, monkeypatch, capsys):
    code, out = _run_main(monkeypatch, capsys, json.dumps(_payload("grep -rn foo src/", _transcript(tmp_path, False))))
    doc = json.loads(out)
    assert code == 0 and doc["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "decision" not in doc and "permissionDecision" not in doc["hookSpecificOutput"]


def test_main_is_silent_and_exits_zero_on_garbage_and_on_any_exception(tmp_path, monkeypatch, capsys):
    assert _run_main(monkeypatch, capsys, "not json at all") == (0, "")
    monkeypatch.setattr(hook, "decide", lambda payload: (_ for _ in ()).throw(RuntimeError("boom")))
    assert _run_main(monkeypatch, capsys, json.dumps(_payload("git status", ""))) == (0, "")


def test_the_script_runs_as_a_hook_subprocess(tmp_path):
    out = subprocess.run([sys.executable, str(_MON / "context_search_hook.py")], input=json.dumps(_payload("git status", "")),
                         capture_output=True, text=True, check=False)
    assert out.returncode == 0 and out.stdout == ""
