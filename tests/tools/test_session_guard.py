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


def _decide(command, role_id, lease_role=None, lease_found=True, tool="Bash", tool_input=None, on_default=False):
    c = classify(tool, tool_input if tool_input is not None else {"command": command})
    return guard.decide(c, _caller(role_id), AUTHORITY, lease_role, lease_found, on_default, command if tool == "Bash" else "")


# ---- decision table ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_id", ["rpg-designer", "agent-working-planner", "testing-planner"])
@pytest.mark.parametrize("command", ["git commit -m x", "git push origin b", "gh pr create --title t"])
def test_designers_and_planners_may_commit_push_and_open_pr_with_no_lease_or_their_own(role_id, command):
    """Owner, 2026-10-07: nothing is forbidden by function; only the writer lease and the critical asks remain."""
    assert _decide(command, role_id, lease_found=False)[0] is None
    assert _decide(command, role_id, lease_role=role_id, lease_found=True)[0] is None


@pytest.mark.parametrize("role_id", ["rpg-designer", "agent-working-planner", "testing-planner"])
@pytest.mark.parametrize("command", ["git commit -m x", "git push origin b", "gh pr create --title t"])
def test_designers_and_planners_are_still_denied_by_another_roles_writer_lease(role_id, command):
    decision, reason = _decide(command, role_id, lease_role="rpg-implementer")
    assert decision == guard.DENY and "writer is rpg-implementer" in reason


def test_a_function_forbidden_action_is_still_denied_when_the_data_lists_one():
    fa = AUTHORITY.for_function("planner")
    forbidden = type(fa)(**{**fa.__dict__, "forbidden": ("commit",)}) if hasattr(fa, "__dict__") else None
    if forbidden is None:
        pytest.skip("function authority is not a plain dataclass")
    class _Auth:
        def for_function(self, _f): return forbidden
        def grants_for(self, _r): return []
    c = classify("Bash", {"command": "git commit -m x"})
    decision, reason = guard.decide(c, _caller("agent-working-planner"), _Auth(), None, False, False, "git commit -m x")
    assert decision == guard.DENY and "must not commit" in reason


def test_non_writer_implementer_is_denied():
    decision, reason = _decide("git push origin b", "rpg-implementer", lease_role="rpg-implementer-2")
    assert decision == guard.DENY and "writer is rpg-implementer-2" in reason


def test_writer_implementer_with_a_grant_pushes_without_asking():
    assert _decide("git push origin b", "agent-working-implementer", lease_role="agent-working-implementer")[0] is None
    assert _decide("gh pr create --title t", "agent-working-implementer", lease_role="agent-working-implementer")[0] is None


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-implementer", "testing-implementer"])
@pytest.mark.parametrize("lease", [None, "self"])
@pytest.mark.parametrize("command", [
    "git commit -m x", "git push", "git push -u origin feature-x", "git push --force-with-lease",
    "git push --force origin feature-x", "git merge origin/main", "gh pr create --title t",
])
def test_own_branch_actions_are_allowed_with_or_without_a_lease(role_id, lease, command):
    """TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED: every action on a non-default branch, lease or not, grant or not."""
    decision, _ = _decide(command, role_id, lease_role=role_id if lease else None, lease_found=bool(lease), on_default=False)
    assert decision is None


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-implementer"])
@pytest.mark.parametrize("lease", [None, "self"])
@pytest.mark.parametrize("command,on_default", [
    ("gh pr merge 1", False),
    ("git push origin HEAD:main", False),
    ("git push origin main", False),
    ("git push", True),
    ("git push origin", True),
])
def test_landing_on_the_default_branch_asks_for_every_role(role_id, lease, command, on_default):
    decision, _ = _decide(command, role_id, lease_role=role_id if lease else None, lease_found=bool(lease), on_default=on_default)
    assert decision == guard.ASK


@pytest.mark.parametrize("command", [
    "git push --force origin main", "git push -f origin main", "git push --force-with-lease origin main",
    "git push --force origin HEAD:main",
])
def test_force_push_to_the_default_branch_asks_now_that_the_static_ask_list_no_longer_does(command):
    """TCK-20261006-SETTINGS-OWN-BRANCH-PERMISSION-PROMPTS: the protection lives in the guard, not in settings.json."""
    decision, _ = _decide(command, "rpg-implementer", lease_role="rpg-implementer", on_default=False)
    assert decision == guard.ASK


def test_settings_json_allows_pr_create_and_has_no_force_push_ask_patterns():
    perms = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text())["permissions"]
    assert "Bash(gh pr create *)" in perms["allow"]
    assert not [p for p in perms["ask"] if p.startswith("Bash(git push") and ("force" in p or "-f" in p)]
    assert "Bash(gh pr merge *)" in perms["ask"] and "Bash(gh pr merge*--admin*)" in perms["deny"]


def test_an_implicit_push_with_an_unknown_branch_asks_but_a_commit_does_not():
    decision, reason = _decide("git push", "rpg-implementer", lease_found=False, on_default=None)
    assert decision == guard.ASK and "could not be determined" in reason
    assert _decide("git commit -m x", "rpg-implementer", lease_found=False, on_default=None)[0] is None


def test_critical_only_policy_a_commit_on_main_and_an_uncertain_commit_are_allowed():
    """Owner, 2026-10-07 ("Drop all but critical"): only merge, push to default, remote delete, data delete, workflow."""
    assert _decide("git commit -m x", "rpg-implementer", lease_role="rpg-implementer", on_default=True)[0] is None
    assert _decide('bash -c "git commit -m x"', "rpg-implementer", lease_role="rpg-implementer")[0] is None
    assert _decide("git push origin main", "rpg-implementer", lease_role="rpg-implementer")[0] == guard.ASK
    assert _decide("gh pr merge 1", "rpg-implementer", lease_role="rpg-implementer")[0] == guard.ASK
    assert _decide("git commit -m x", "rpg-planner", lease_role="rpg-implementer")[0] == guard.DENY  # the lease


@pytest.mark.parametrize("command,expected", [
    ('bash -c "git push origin main"', guard.ASK),
    ('eval "gh pr merge 1"', guard.ASK),
    ('bash -c "git push --delete origin x"', guard.ASK),
    ('bash -c "git commit -m x"', None),
    ('bash -c "pytest"', None),
    ('eval "echo CLAUDE.md"', None),
])
def test_an_uncertain_command_asks_only_when_its_raw_text_names_a_critical_operation(command, expected):
    assert _decide(command, "rpg-implementer", lease_role="rpg-implementer")[0] == expected


def test_another_roles_lease_still_denies_on_a_feature_branch():
    for command in ("git commit -m x", "git push -u origin feature-x", "gh pr create --title t"):
        decision, reason = _decide(command, "rpg-implementer", lease_role="rpg-implementer-2", on_default=False)
        assert decision == guard.DENY and "writer is rpg-implementer-2" in reason


def test_unchanged_rules_still_hold_on_a_feature_branch():
    assert _decide("git commit -m x", "rpg-designer", lease_role="rpg-implementer")[0] == guard.DENY  # the lease
    assert _decide("git push origin --delete old", "rpg-implementer", lease_found=False)[0] == guard.ASK
    assert _decide("bash -c 'git push'", "rpg-implementer", lease_found=False)[0] == guard.ASK
    assert _decide("", "rpg-implementer", tool="Edit", tool_input={"file_path": ".claude/settings.json"})[0] is None


def test_default_branch_helpers_read_git(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "feature-x", str(tmp_path)], check=True)
    assert guard.current_branch(str(tmp_path)) == "feature-x"
    assert guard.default_branches(str(tmp_path)) == ("main",)
    subprocess.run(["git", "-C", str(tmp_path), "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"], check=True)
    assert guard.default_branches(str(tmp_path)) == ("main", "trunk")


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-implementer"])
@pytest.mark.parametrize("command", ["gh pr merge 5", "git push origin --delete old", "gh api -X DELETE repos/o/r/git/refs/heads/x"])
def test_merge_and_remote_deletion_ask_even_for_a_granted_writer(role_id, command):
    decision, _ = _decide(command, role_id, lease_role=role_id)
    assert decision == guard.ASK


@pytest.mark.parametrize("role_id", ["agent-working-implementer", "rpg-planner", "testing-designer"])
def test_governing_and_authority_file_edits_are_allowed_for_every_role(role_id):
    """Owner, 2026-10-07: governing files are protected by review and PR merge, not by a guard prompt."""
    for path in ("CLAUDE.md", ".claude/settings.json", "registries/session_authority.yaml"):
        for tool in ("Edit", "Write", "MultiEdit"):
            decision, _ = _decide("", role_id, tool=tool, tool_input={"file_path": path})
            assert decision is None, (role_id, tool, path)


def test_uncertain_command_asks_for_a_role_that_could_otherwise_proceed():
    command = "bash -c 'git push origin x'"
    decision, reason = _decide(command, "agent-working-implementer", lease_role="agent-working-implementer")
    assert decision == guard.ASK and "uncertain" in reason


def test_non_authority_call_is_allowed_for_everyone():
    for role_id in ("rpg-designer", "rpg-implementer"):
        assert _decide("ls -la", role_id)[0] is None
        assert _decide("", role_id, tool="Edit", tool_input={"file_path": "src/x.py"})[0] is None


def test_unresolved_role_asks_for_critical_actions_and_allows_the_rest():
    for command in ("git push origin main", "gh pr merge 5", "git push --delete origin x", "eval 'git push'"):
        decision, reason = guard.decide(classify("Bash", {"command": command}), guard.Caller(False), AUTHORITY, None, False,
                                        False, command)
        assert decision == guard.ASK and "not resolved" in reason
    for command in ("git push origin b", "git commit -m x"):
        assert guard.decide(classify("Bash", {"command": command}), guard.Caller(False), AUTHORITY, None, False)[0] is None
    assert guard.decide(classify("Bash", {"command": "ls"}), guard.Caller(False), AUTHORITY, None, False) == (None, "")
    edit = classify("Edit", {"file_path": "CLAUDE.md"})
    assert guard.decide(edit, guard.Caller(False), AUTHORITY, None, False)[0] is None


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
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}, "session_id": "none", "cwd": str(_REPO_ROOT)}
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
    assert len(entries) == 1 and entries[0]["matcher"] == "Bash|Edit|Write|MultiEdit|NotebookEdit|SendMessage"
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


@pytest.mark.parametrize("branch,command,expected", [
    ("feature-x", "git commit -m x", None),
    ("feature-x", "git push", None),
    ("feature-x", "git push --force-with-lease", None),
    ("feature-x", "git push origin HEAD:main", "ask"),
    ("feature-x", "gh pr merge 1", "ask"),
    ("main", "git commit -m x", None),
    ("main", "git push", "ask"),
    ("main", "git push origin", "ask"),
])
def test_end_to_end_in_a_real_repo_with_no_lease(tmp_path, branch, command, expected):
    """The cwd's real branch decides a commit and a bare push; an implementer with no lease and no grant."""
    subprocess.run(["git", "init", "-q", "-b", branch, str(tmp_path)], check=True)
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(tmp_path),
               "session_id": "unbound", "agent_type": "session-rpg-implementer"}
    code, out, _ = _run_main(payload)
    assert code == 0
    if expected is None:
        assert out == ""
    else:
        assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == expected


def _git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def two_worktrees(tmp_path):
    """`repo` has main checked out; `wt` is a linked worktree on feature-x."""
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git("commit", "--allow-empty", "-m", "i", cwd=repo)
    _git("worktree", "add", "-q", "-b", "feature-x", str(tmp_path / "wt"), cwd=repo)
    return tmp_path


def _decision_in(cwd, command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd),
               "session_id": "unbound", "agent_type": "session-rpg-implementer"}
    code, out, _ = _run_main(payload)
    assert code == 0
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


@pytest.mark.parametrize("session_cwd,command,expected", [
    # session on a feature branch, command moves to the worktree that has main: the cd target's branch decides
    ("wt", "cd ../repo && git push", "ask"),
    ("wt", "cd ../repo && git commit -m x", None),
    ("wt", "cd ../repo && git push origin", "ask"),
    ("wt", "pushd ../repo && git push", "ask"),
    ("wt", "git commit -m x && cd ../repo && git push", "ask"),
    ("wt", "cd ../wt && git commit -m x", None),
    ("wt", "cd . && git push", None),
    # session on main, command moves to the feature worktree: allowed, the target is not main
    ("repo", "cd ../wt && git push", None),
    ("repo", "cd ../wt && git commit -m x", None),
    ("repo", "git push", "ask"),
    # not resolvable: ask
    ("wt", "cd ../does-not-exist && git push", "ask"),
    ("wt", "cd $SOMEWHERE && git push", "ask"),
])
def test_cd_before_a_commit_or_push_is_checked_against_the_directory_it_moves_to(two_worktrees, session_cwd, command, expected):
    assert _decision_in(two_worktrees / session_cwd, command) == expected


def test_effective_cwd_applies_relative_and_absolute_targets_in_order(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert guard.effective_cwd(str(tmp_path), ("a", "b")) == str(tmp_path / "a" / "b")
    assert guard.effective_cwd(str(tmp_path / "a"), ("..", "a")) == str(tmp_path / "a")
    assert guard.effective_cwd(str(tmp_path), (str(tmp_path / "a"),)) == str(tmp_path / "a")
    assert guard.effective_cwd(str(tmp_path), ("missing",)) is None


def test_critical_text_pattern_is_narrow():
    for text in ("git push", "gh pr merge 1", "gh api x -X DELETE", "gh api --method DELETE x", "git worktree remove w",
                 "git branch --delete x", "gh repo merge", "gh x merge"):
        assert guard.critical_text(text), text
    for text in ("git commit -m x", "cat CLAUDE.md", "git merge origin/main", "pytest -k merge", "echo settings.json"):
        assert not guard.critical_text(text), text
