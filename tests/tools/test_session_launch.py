"""tools/sessions/launch.py (TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL).

Real git repositories, real child processes and a real `kill -9`; only the `claude` binary is never run
(`--dry-run` prints the exact command)."""
from __future__ import annotations

import dataclasses
import shutil
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]
if str(REAL_ROOT) not in sys.path:
    sys.path.insert(0, str(REAL_ROOT))

from tools.sessions import launch as ln  # noqa: E402
from tools.sessions import state as st  # noqa: E402
from tools.sessions.roster import load_roster  # noqa: E402

ROSTER = load_roster(REAL_ROOT)
ROLE = "agent-working-implementer"
TARGET = ln.Target(ROSTER.role(ROLE), ROLE)
ROLE_HANDOVER = Path(ROSTER.role(ROLE).handover)
_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}


def git(cwd, *a, check=True):
    return subprocess.run(["git", *a], cwd=cwd, check=check, capture_output=True, text=True, env=_ENV)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "main"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "f").write_text("base\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r


def _binding(repo, sid="old-sess", process=None, branch="work"):
    return st.Binding(sid, ROLE, "startup", str(repo), branch, "", process, "d", "2026-10-04T00:00:00Z")


def _plan(repo, tmp_path, **kw):
    sroot = st.state_root(repo)
    args = dict(target=TARGET, root=REAL_ROOT, state_root=sroot, worktree=repo, pdir=tmp_path / "projects",
                action=None, session_id=None, interactive=False, resume_flag=False)
    args.update(kw)
    return ln.plan_launch(**args)


def _orphan(repo):
    p = subprocess.Popen(["sleep", "60"])
    st.record_start(st.state_root(repo), _binding(repo, process=st.process_identity(p.pid)))
    return p


def _kill(p):
    os.kill(p.pid, signal.SIGKILL)
    p.wait()


# ---- AC1: the exact command --------------------------------------------------------------------

def test_build_command_forms():
    cmd, env = ln.build_command(TARGET)
    assert cmd == ["claude", "--name", ROLE, "--agent", f"session-{ROLE}"] and env == {"SESSION_ROLE": ROLE}
    cmd, env = ln.build_command(TARGET, "abc-123")
    assert cmd[:3] == ["claude", "--resume", "abc-123"] and "--name" in cmd and "--agent" in cmd
    second = ln.Target(TARGET.role, f"{ROLE}-2")
    assert ln.build_command(second)[1] == {"SESSION_ROLE": f"{ROLE}-2"} and ln.build_command(second)[0][2] == f"{ROLE}-2"


def test_every_roster_role_has_the_generated_agent_file_the_launcher_names():
    for r in ROSTER.roles:
        assert ln.agent_file_exists(r, REAL_ROOT), r.role
        text = (REAL_ROOT / ".claude" / "agents" / f"{ln.agent_name(r)}.md").read_text()
        assert "never spawn" in text.lower()  # M1c: launcher-only


def test_dry_run_prints_the_command_without_executing(repo, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(st, "state_root", lambda *_: tmp_path / "sr")
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: pytest.fail("must not exec in a dry run"))
    assert ln.main([ROLE, "--dry-run", "--worktree", str(repo)], root=REAL_ROOT) == 0
    out = capsys.readouterr().out
    assert f"SESSION_ROLE={ROLE} claude --name {ROLE} --agent session-{ROLE}" in out and "DRY RUN" in out


def test_unknown_role_lists_the_roster_and_exits_2(capsys):
    assert ln.main(["no-such-role"], root=REAL_ROOT) == 2
    assert ROLE in capsys.readouterr().err


def test_instance_names_follow_max_sessions():
    two = dataclasses.replace(TARGET.role, max_sessions=2)
    roster = dataclasses.replace(ROSTER, roles=tuple(two if r.role == ROLE else r for r in ROSTER.roles))
    assert ln.resolve_target(f"{ROLE}-2", roster).instance == f"{ROLE}-2"
    assert ln.resolve_target(f"{ROLE}-2", ROSTER) is None and ln.resolve_target(f"{ROLE}-3", roster) is None


# ---- AC2: live refused, killed -> recovery, released -> fresh ----------------------------------

def test_a_live_instance_is_refused(repo, tmp_path):
    p = _orphan(repo)
    try:
        code, lines, sid = _plan(repo, tmp_path)
        assert code == ln.EXIT_REFUSED and "LIVE" in lines[0] and sid is None
    finally:
        p.kill(); p.wait()


def test_a_killed_instance_takes_the_recovery_path_and_a_released_one_starts_fresh(repo, tmp_path):
    p = _orphan(repo)
    _kill(p)  # positive control from M2a: it was live a moment ago
    code, lines, _ = _plan(repo, tmp_path)
    assert code == ln.EXIT_NEEDS_CHOICE and "ORPHANED" in lines[0]
    st.release(st.state_root(repo), ROLE)
    assert _plan(repo, tmp_path)[0] == 0
    assert _plan(repo, tmp_path)[2] is None


def test_no_instance_starts_fresh(repo, tmp_path):
    assert _plan(repo, tmp_path)[:1] == (0,)


# ---- AC3: git operation left in progress -------------------------------------------------------

def test_mid_rebase_is_reported_as_a_never_boundary_state(repo, tmp_path):
    git(repo, "checkout", "-q", "-b", "work")
    (repo / "f").write_text("work\n"); git(repo, "commit", "-q", "-am", "w")
    git(repo, "checkout", "-q", "main")
    (repo / "f").write_text("main\n"); git(repo, "commit", "-q", "-am", "m")
    git(repo, "checkout", "-q", "work")
    assert git(repo, "rebase", "main", check=False).returncode != 0  # stopped on the conflict
    assert ln.git_operation_in_progress(repo) == ["a rebase"]
    p = _orphan(repo)
    _kill(p)
    _, lines, _ = _plan(repo, tmp_path)
    assert any("GIT OPERATION LEFT IN PROGRESS" in l and "NEVER-boundary" in l for l in lines)


def test_a_clean_repo_reports_no_operation_in_progress(repo):
    assert ln.git_operation_in_progress(repo) == []


# ---- AC4: worktree self-heal -------------------------------------------------------------------

def test_a_removed_worktree_is_recreated_from_its_branch_and_loss_is_stated(repo, tmp_path):
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "-b", "work", str(wt))
    (wt / "g").write_text("committed\n"); git(wt, "add", "-A"); git(wt, "commit", "-q", "-m", "c")
    git(repo, "worktree", "remove", "--force", str(wt))
    notes = ln.ensure_worktree(wt, "work", repo)
    assert (wt / "g").read_text() == "committed\n"
    assert any("UNCOMMITTED" in n for n in notes) and any("recreated" in n for n in notes)
    assert ln.ensure_worktree(wt, "work", repo) == []  # healthy: nothing to say


def test_a_directory_deleted_behind_gits_back_is_prunable_and_recreated(repo, tmp_path):
    import shutil
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "-b", "work", str(wt))
    shutil.rmtree(wt)
    assert any("recreated" in n for n in ln.ensure_worktree(wt, "work", repo))
    assert wt.is_dir()


def test_a_missing_branch_or_no_recorded_branch_is_reported_not_invented(repo, tmp_path):
    wt = tmp_path / "wt"
    assert any("no longer exists" in n for n in ln.ensure_worktree(wt, "gone-branch", repo))
    assert any("no branch is recorded" in n for n in ln.ensure_worktree(wt, None, repo))
    assert not wt.exists()


def test_dry_run_self_heal_changes_nothing(repo, tmp_path):
    git(repo, "branch", "work")
    wt = tmp_path / "wt"
    assert any("would run" in n for n in ln.ensure_worktree(wt, "work", repo, apply=False))
    assert not wt.exists()


# ---- AC5: candidate transcripts ----------------------------------------------------------------

def _transcript(pdir, project, sid, title, age=0):
    d = pdir / project
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{sid}.jsonl"
    f.write_text(json.dumps({"type": "custom-title", "customTitle": title}) + "\n" + json.dumps({"type": "user"}) + "\n")
    t = time.time() - age
    os.utime(f, (t, t))
    return f


def test_candidates_are_found_by_custom_title_across_project_dirs_newest_first(tmp_path):
    pdir = tmp_path / "projects"
    _transcript(pdir, "-proj-a", "s-old", ROLE, age=5000)
    _transcript(pdir, "-proj-b-other-cwd", "s-new", ROLE, age=10)  # resumed from another cwd
    _transcript(pdir, "-proj-a", "s-else", "someone-else", age=1)
    got = ln.find_transcripts(ROLE, pdir)
    assert [t.session_id for t in got] == ["s-new", "s-old"]
    assert ln.find_transcript("s-new", pdir).path.parent.name == "-proj-b-other-cwd"
    assert ln.find_transcript("nope", pdir) is None


def test_replace_never_deletes_a_transcript_and_resume_is_by_session_id(repo, tmp_path):
    pdir = tmp_path / "projects"
    f = _transcript(pdir, "-proj-a", "s-new", ROLE, age=10)
    p = _orphan(repo); _kill(p)
    code, _, sid = _plan(repo, tmp_path, action="replace")
    assert code == 0 and sid is None and f.exists()
    code, lines, sid = _plan(repo, tmp_path, action="resume")  # the holder ("old-sess") has no transcript
    assert code == ln.EXIT_NEEDS_CHOICE and sid is None and any("never wrote a transcript" in l for l in lines)
    _transcript(pdir, "-proj-a", "old-sess", ROLE, age=20)
    code, lines, sid = _plan(repo, tmp_path, action="resume")
    assert code == 0 and sid == "old-sess" and any("by id, never by name" in l for l in lines)
    code, _, sid = _plan(repo, tmp_path, action="resume", session_id="explicit-id")
    assert sid == "explicit-id"


def test_default_action_resumes_only_the_holders_own_newer_transcript():
    own = ln.Transcript("s", Path("x"), 1000.0)
    assert ln.default_action(own, 500.0) == "resume" and ln.default_action(own, None) == "resume"
    assert ln.default_action(own, 2000.0) == "replace"
    assert ln.default_action(None, None) == "replace" and ln.default_action(None, 5.0) == "replace"


def test_the_newest_transcript_of_the_role_is_never_the_default_when_it_is_not_the_holders(repo, tmp_path):
    """Regression from the live rehearsal: another (live) session of the same role had the newest transcript."""
    pdir = tmp_path / "projects"
    _transcript(pdir, "-proj-a", "someone-elses-live-session", ROLE, age=1)
    p = _orphan(repo); _kill(p)
    code, lines, sid = _plan(repo, tmp_path, interactive=True, input_fn=lambda _: "")
    assert sid is None  # empty answer took the suggestion, which is replace, not that session
    assert "someone-elses-live-session" not in " ".join(lines[-1:])


# ---- AC6: non-interactive never chooses --------------------------------------------------------

def test_non_interactive_prints_evidence_and_exits_nonzero_asking_for_a_flag(repo, tmp_path):
    p = _orphan(repo); _kill(p)
    code, lines, sid = _plan(repo, tmp_path, interactive=False)
    assert code == ln.EXIT_NEEDS_CHOICE and sid is None
    assert any("--action resume|replace|inspect" in l for l in lines)


def test_interactive_choice_is_the_owners_and_empty_answer_takes_the_suggestion(repo, tmp_path):
    pdir = tmp_path / "projects"
    _transcript(pdir, "-p", "old-sess", ROLE, age=10)  # the holder's own transcript
    p = _orphan(repo); _kill(p)
    assert _plan(repo, tmp_path, interactive=True, input_fn=lambda _: "")[2] == "old-sess"   # suggestion: resume
    assert _plan(repo, tmp_path, interactive=True, input_fn=lambda _: "replace")[2] is None
    assert _plan(repo, tmp_path, interactive=True, input_fn=lambda _: "inspect")[0] == ln.EXIT_NEEDS_CHOICE
    assert _plan(repo, tmp_path, interactive=True, input_fn=lambda _: "bogus")[0] == ln.EXIT_USAGE


def test_handover_summary_reads_the_awaiting_line(tmp_path):
    h = tmp_path / "h.md"
    h.write_text("# H\n\n## Awaiting\n- the owner's go on the push\n\n## Next\n- x\n")
    assert ln.handover_summary(h)[1] == "- the owner's go on the push"
    assert ln.handover_summary(tmp_path / "none.md") == (None, "no handover note")


# ---- TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT ------------------------------------

@pytest.fixture
def seat_worktree(repo, tmp_path):
    for rel in ("registries", "docs/guidelines/session_roles", ".claude/agents"):
        shutil.copytree(REAL_ROOT / rel, repo / rel)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "roster")
    wt = tmp_path / "seat"
    git(repo, "worktree", "add", "-q", "-b", "seat", str(wt))
    return wt


def test_dry_run_from_a_secondary_worktree_sees_the_main_checkout_note(repo, seat_worktree, tmp_path, monkeypatch, capsys):
    note = repo / ROLE_HANDOVER
    note.parent.mkdir(parents=True)
    note.write_text("# Handover\n")
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: pytest.fail("must not exec in a dry run"))
    assert ln.main([ROLE, "--dry-run", "--worktree", str(seat_worktree)], root=seat_worktree) == 0
    assert "no handover note yet" not in capsys.readouterr().out
    assert not (seat_worktree / ".claude" / "handover").exists()


def test_real_launch_from_a_secondary_worktree_writes_no_stub_there(repo, seat_worktree, monkeypatch):
    note = repo / ROLE_HANDOVER
    note.parent.mkdir(parents=True)
    note.write_text("# Handover\n")
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: None)
    monkeypatch.setattr(os, "chdir", lambda *_: None)
    ln.main([ROLE, "--worktree", str(seat_worktree)], root=seat_worktree)
    assert not (seat_worktree / ".claude" / "handover").exists()
    assert note.read_text() == "# Handover\n"


def test_plan_launch_reports_a_missing_note_against_the_main_checkout(repo, seat_worktree, tmp_path):
    code, lines, _ = _plan(repo, tmp_path, root=seat_worktree)
    assert code == 0 and lines == ["no handover note yet: a stub will be created"]
    note = repo / ROLE_HANDOVER
    note.parent.mkdir(parents=True)
    note.write_text("# Handover\n")
    assert _plan(repo, tmp_path, root=seat_worktree)[1] == []
