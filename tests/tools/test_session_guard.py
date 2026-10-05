"""Tests for tools/sessions/guard.py (TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK).

Decision table over (role function, writer or not, grant or not, class), role resolution from the session
binding record with two concurrent sessions, and the fail-closed discipline from the M0n result: an exception on
an authority-class input exits 2 (an unguarded traceback exits 1 and lets the call run), while a non-authority
input never blocks.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.sessions import guard
from tools.sessions import state as st
from tools.sessions.classify import classify
from tools.sessions.roster import load_authority, load_roster

_REPO_ROOT = Path(__file__).parent.parent.parent
_GUARD = _REPO_ROOT / "tools" / "sessions" / "guard.py"
ROSTER, AUTHORITY = load_roster(), load_authority()


def _caller(role_id):
    role = ROSTER.role(role_id)
    return guard.Caller(True, role_id, role.role, role.function, "binding")


def _decide(command, role_id, lease_role=None, lease_found=True, tool="Bash", tool_input=None):
    c = classify(tool, tool_input if tool_input is not None else {"command": command})
    return guard.decide(c, _caller(role_id), AUTHORITY, lease_role, lease_found)


# ---- decision table ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_id", ["rpg-designer", "agent-working-planner", "testing-planner"])
@pytest.mark.parametrize("command", ["git commit -m x", "git push origin b", "gh pr create --title t"])
def test_designers_and_planners_are_denied_commit_push_and_open_pr(role_id, command):
    decision, reason = _decide(command, role_id, lease_role="rpg-implementer")
    assert decision == guard.DENY and "must not" in reason


def test_non_writer_implementer_is_denied():
    decision, reason = _decide("git push origin b", "rpg-implementer", lease_role="rpg-implementer-2")
    assert decision == guard.DENY and "writer is rpg-implementer-2" in reason


def test_writer_implementer_with_a_grant_pushes_without_asking():
    assert _decide("git push origin b", "agent-working-implementer", lease_role="agent-working-implementer")[0] is None
    assert _decide("gh pr create --title t", "agent-working-implementer", lease_role="agent-working-implementer")[0] is None


def test_writer_implementer_without_a_grant_is_asked_to_push():
    decision, reason = _decide("git push origin b", "rpg-implementer", lease_role="rpg-implementer")
    assert decision == guard.ASK and "no grant" in reason


def test_writer_commit_is_allowed_because_commit_is_not_in_needs_user():
    assert _decide("git commit -m x", "rpg-implementer", lease_role="rpg-implementer")[0] is None


def test_missing_lease_asks_for_an_implementer():
    decision, reason = _decide("git commit -m x", "agent-working-implementer", lease_found=False)
    assert decision == guard.ASK and "no writer lease" in reason


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-implementer"])
@pytest.mark.parametrize("command", ["gh pr merge 5", "git push origin --delete old", "gh api -X DELETE repos/o/r/git/refs/heads/x"])
def test_merge_and_remote_deletion_ask_even_for_a_granted_writer(role_id, command):
    decision, _ = _decide(command, role_id, lease_role=role_id)
    assert decision == guard.ASK


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-planner", "testing-designer"])
def test_governing_and_authority_file_edits_ask_for_every_role(role_id):
    for path in ("CLAUDE.md", ".claude/settings.json", "registries/session_authority.yaml"):
        for tool in ("Edit", "Write", "MultiEdit"):
            decision, _ = _decide("", role_id, tool=tool, tool_input={"file_path": path})
            assert decision == guard.ASK, (role_id, tool, path)


def test_uncertain_command_asks_for_a_role_that_could_otherwise_proceed():
    decision, reason = _decide("bash -c 'git push origin x'", "agent-working-implementer", lease_role="agent-working-implementer")
    assert decision == guard.ASK and "uncertain" in reason


def test_non_authority_call_is_allowed_for_everyone():
    for role_id in ("rpg-designer", "rpg-implementer"):
        assert _decide("ls -la", role_id)[0] is None
        assert _decide("", role_id, tool="Edit", tool_input={"file_path": "src/x.py"})[0] is None


def test_unresolved_role_asks_for_authority_classes_and_allows_the_rest():
    for command in ("git push origin b", "git commit -m x", "gh pr merge 5", "git push --delete origin x", "eval 'git push'"):
        decision, reason = guard.decide(classify("Bash", {"command": command}), guard.Caller(False), AUTHORITY, None, False)
        assert decision == guard.ASK and "not resolved" in reason
    assert guard.decide(classify("Bash", {"command": "ls"}), guard.Caller(False), AUTHORITY, None, False) == (None, "")
    edit = classify("Edit", {"file_path": "CLAUDE.md"})
    assert guard.decide(edit, guard.Caller(False), AUTHORITY, None, False)[0] == guard.ASK


# ---- role resolution ----------------------------------------------------------------------------

def _binding(role, session_id, ts="2026-10-05T00:00:00Z"):
    return st.Binding(session_id=session_id, role=role, source="startup", worktree="/w", branch="b",
                      transcript_path="", process=None, manifest_digest="d", ts=ts)


def test_two_concurrent_sessions_never_swap_roles(tmp_path):
    root = tmp_path / "session-roles"
    st.record_start(root, _binding("rpg-implementer", "sess-A"))
    st.record_start(root, _binding("agent-working-implementer", "sess-B"))
    a = guard.resolve_caller({"session_id": "sess-A"}, ROSTER, root)
    b = guard.resolve_caller({"session_id": "sess-B"}, ROSTER, root)
    assert (a.role_id, b.role_id) == ("rpg-implementer", "agent-working-implementer")
    assert not guard.resolve_caller({"session_id": "sess-C"}, ROSTER, root).resolved


def test_second_instance_resolves_to_its_base_role(tmp_path):
    root = tmp_path / "session-roles"
    st.record_start(root, _binding("rpg-implementer-2", "sess-2"))
    caller = guard.resolve_caller({"session_id": "sess-2"}, ROSTER, root)
    assert caller.instance == "rpg-implementer-2" and caller.role_id == "rpg-implementer" and caller.function == "implementer"


def test_agent_type_is_the_fallback_signal(tmp_path):
    caller = guard.resolve_caller({"session_id": "unbound", "agent_type": "session-rpg-planner"}, ROSTER, tmp_path / "none")
    assert caller.resolved and caller.role_id == "rpg-planner" and caller.source == "agent_type"
    assert not guard.resolve_caller({"session_id": "unbound", "agent_type": "session-nope"}, ROSTER, tmp_path / "none").resolved


def test_released_holder_is_not_matched_by_instance_but_its_binding_still_is(tmp_path):
    root = tmp_path / "session-roles"
    st.record_start(root, _binding("rpg-planner", "sess-old"))
    st.release(root, "rpg-planner")
    assert guard.find_session_instance(root, "sess-old") == "rpg-planner"


# ---- fail-closed discipline -----------------------------------------------------------------------

def _run_main(payload, monkeypatch=None, boom=False):
    if boom:
        def _raise(*a, **k):
            raise RuntimeError("forced failure")
        monkeypatch.setattr(guard, "_guard", _raise)
    out, err = io.StringIO(), io.StringIO()
    code = guard.main(io.StringIO(json.dumps(payload)), out, err)
    return code, out.getvalue(), err.getvalue()


def test_forced_exception_on_an_authority_input_exits_2(monkeypatch):
    code, out, err = _run_main({"tool_name": "Bash", "tool_input": {"command": "git push origin x"}}, monkeypatch, boom=True)
    assert code == 2 and "blocked" in err and out == ""
    code, _, _ = _run_main({"tool_name": "Edit", "tool_input": {"file_path": "CLAUDE.md"}}, monkeypatch, boom=True)
    assert code == 2


def test_forced_exception_on_a_non_authority_input_never_blocks(monkeypatch):
    code, out, err = _run_main({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, monkeypatch, boom=True)
    assert code == 0 and out == "" and err == ""
    code, _, _ = _run_main({"tool_name": "Edit", "tool_input": {"file_path": "src/x.py"}}, monkeypatch, boom=True)
    assert code == 0


def test_broken_import_is_a_caught_failure_for_authority_input_not_a_crash(monkeypatch):
    monkeypatch.setattr(guard, "_IMPORT_ERROR", ImportError("simulated"))
    assert _run_main({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})[0] == 2
    assert _run_main({"tool_name": "Bash", "tool_input": {"command": "ls"}})[0] == 0


def test_unparseable_stdin_and_non_object_payloads_pass():
    assert guard.main(io.StringIO("not json"), io.StringIO(), io.StringIO()) == 0
    assert guard.main(io.StringIO("[1, 2]"), io.StringIO(), io.StringIO()) == 0


def test_an_unguarded_traceback_exits_1_which_would_let_the_call_run():
    """Positive control for why the discipline exists (M0n): a bare crash is exit code 1, not 2."""
    result = subprocess.run([sys.executable, "-c", "raise RuntimeError('x')"], capture_output=True, text=True)
    assert result.returncode == 1


def test_script_run_end_to_end_returns_well_formed_json_for_an_unresolved_push(tmp_path):
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin x"}, "session_id": "none", "cwd": str(_REPO_ROOT)}
    result = subprocess.run([sys.executable, str(_GUARD)], input=json.dumps(payload), capture_output=True, text=True, cwd=_REPO_ROOT)
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse" and out["permissionDecision"] == "ask"


def test_script_run_end_to_end_is_silent_for_a_non_authority_call():
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(_REPO_ROOT)}
    result = subprocess.run([sys.executable, str(_GUARD)], input=json.dumps(payload), capture_output=True, text=True, cwd=_REPO_ROOT)
    assert (result.returncode, result.stdout) == (0, "")


# ---- wiring wrapper (the missing-script hazard) ---------------------------------------------------------

def _wired_command():
    settings = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    entries = [e for e in settings["hooks"]["PreToolUse"] if "guard.py" in json.dumps(e)]
    assert len(entries) == 1 and entries[0]["matcher"] == "Bash|Edit|Write|MultiEdit|NotebookEdit"
    assert settings["hooks"]["PreToolUse"][-1] is entries[0] or settings["hooks"]["PreToolUse"][-1] == entries[0]
    return entries[0]["hooks"][0]["command"]


def _git_init(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def _run_wired(cwd, payload="{}"):
    return subprocess.run(["bash", "-c", _wired_command()], input=payload, capture_output=True, text=True, cwd=cwd)


def test_wired_command_passes_outside_a_repo_and_when_the_script_is_missing(tmp_path):
    assert _run_wired(tmp_path).returncode == 0  # not a git repo
    _git_init(tmp_path)
    assert _run_wired(tmp_path).returncode == 0  # repo without tools/sessions/guard.py
    bare = subprocess.run(["bash", "-c", "python3 tools/sessions/guard.py"], input="{}", capture_output=True, text=True, cwd=tmp_path)
    assert bare.returncode == 2  # positive control: an unwrapped missing script exits 2 and would block the call


def test_wired_command_forwards_the_scripts_own_exit_code_from_a_subdirectory(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "tools" / "sessions").mkdir(parents=True)
    (tmp_path / "tools" / "sessions" / "guard.py").write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    assert _run_wired(tmp_path).returncode == 2
    assert _run_wired(tmp_path / "sub").returncode == 2  # the repo root is resolved, so a subdirectory cannot disable the guard


def test_wired_command_runs_the_real_guard_in_this_repo():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(_REPO_ROOT)})
    result = _run_wired(_REPO_ROOT, payload)
    assert (result.returncode, result.stdout) == (0, "")
