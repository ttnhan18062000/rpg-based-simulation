"""Role resolution, manifest diff and the role-aware SessionStart hook
(TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING).

The hook runs against a tmp copy of the real manifest and card templates, so what is asserted is the real
resolution and card composition; state goes to a tmp git repo's common dir."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REAL_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(REAL_ROOT), str(REAL_ROOT / "tools" / "agent-monitoring")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.sessions import manifest_diff as md  # noqa: E402
from tools.sessions import session_start_hook as hook  # noqa: E402
from tools.sessions import state as st  # noqa: E402
from tools.sessions.resolve import DISAGREE, RESOLVED, UNRESOLVED, Signals, resolve  # noqa: E402
from tools.sessions.roster import load_authority, load_roster  # noqa: E402

ROSTER = load_roster(REAL_ROOT)
WRITER = "agent-working-implementer"
OTHER = "rpg-designer"
_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}


# ---- AC1: the resolution table -----------------------------------------------------------------

@pytest.mark.parametrize("signals, status, role", [
    (Signals("startup", agent_type=f"session-{WRITER}", session_title=WRITER, env_role=WRITER), RESOLVED, WRITER),
    (Signals("startup", agent_type=f"session-{WRITER}"), RESOLVED, WRITER),
    (Signals("startup", env_role=WRITER), RESOLVED, WRITER),
    (Signals("resume", session_title=WRITER), RESOLVED, WRITER),                       # resume: title only
    (Signals("resume", agent_type=f"session-{WRITER}", env_role=WRITER), UNRESOLVED, None),  # untrusted on resume
    (Signals("startup", agent_type=f"session-{WRITER}", session_title=WRITER), RESOLVED, WRITER),  # fork: duplicate title, new id
    (Signals("clear", env_role=WRITER, session_title=WRITER), RESOLVED, WRITER),
    (Signals("compact", agent_type=f"session-{WRITER}"), RESOLVED, WRITER),
    (Signals("startup"), UNRESOLVED, None),                                             # plain claude
    (Signals("startup", session_title="my own name"), UNRESOLVED, None),                # unknown title is ignored
    (Signals("startup", agent_type=f"session-{WRITER}", env_role=OTHER), DISAGREE, None),
    (Signals("resume", session_title=OTHER, agent_type=f"session-{WRITER}"), RESOLVED, OTHER),
])
def test_resolution_table(signals, status, role):
    res = resolve(signals, ROSTER)
    assert (res.status, res.role) == (status, role), res.reason


def test_disagreement_names_both_signals_and_resolves_nothing():
    res = resolve(Signals("startup", agent_type=f"session-{WRITER}", env_role=OTHER), ROSTER)
    assert res.status == DISAGREE and res.role is None
    assert ("agent_type", WRITER) in res.used and ("env_role", OTHER) in res.used


# ---- manifest digest diff ----------------------------------------------------------------------

def _snap(**kw):
    base = dict(owns=("a/**",), routes=(), forbidden=("x",), needs_user=("y",), grants=("push@all",), max_sessions=1)
    base.update(kw)
    return md.Snapshot(**base)


def test_diff_reports_changes_and_flags_only_authority_reductions():
    assert md.diff(_snap(), _snap()).lines == ()
    widened = md.diff(_snap(), _snap(grants=("push@all", "merge@all"), owns=("a/**", "b/**")))
    assert widened.lines and not widened.authority_reduced
    for reduced in (_snap(forbidden=("x", "z")), _snap(needs_user=("y", "z")), _snap(grants=())):
        c = md.diff(_snap(), reduced)
        assert c.authority_reduced and c.lines
    assert "max_sessions: 1 -> 2" in md.diff(_snap(), _snap(max_sessions=2)).lines


def test_snapshot_round_trips_and_rejects_a_malformed_dict():
    s = md.snapshot(WRITER, ROSTER, load_authority(REAL_ROOT))
    assert md.Snapshot.from_json(json.loads(json.dumps(s.to_json()))) == s
    with pytest.raises(ValueError):
        md.Snapshot.from_json({"owns": []})


# ---- the hook ----------------------------------------------------------------------------------

@pytest.fixture
def world(tmp_path):
    root = tmp_path / "root"
    shutil.copytree(REAL_ROOT / "registries", root / "registries",
                    ignore=shutil.ignore_patterns("*.jsonl"))
    shutil.copytree(REAL_ROOT / "docs" / "guidelines" / "session_roles", root / "docs" / "guidelines" / "session_roles")
    (root / ".claude" / "handover").mkdir(parents=True)
    (root / ".claude" / "handover" / f"{WRITER}.md").write_text(f"# Handover {WRITER}\nSECRET-WRITER-NOTE\n")
    (root / ".claude" / "handover" / f"{OTHER}.md").write_text(f"# Handover {OTHER}\nSECRET-OTHER-NOTE\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True, env=_ENV)
    (repo / "f").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=_ENV)
    subprocess.run(["git", "commit", "-q", "-m", "i"], cwd=repo, check=True, capture_output=True, env=_ENV)
    return root, repo, st.state_root(repo)


def _payload(repo, **kw):
    return {"session_id": "sess-1", "source": "startup", "cwd": str(repo), "transcript_path": "/somewhere/t.jsonl",
            "agent_type": f"session-{WRITER}", **kw}


def _ctx(world, payload, env=None):
    root, repo, state_root = world
    return hook.build_context(payload, env or {}, root, state_root)


def test_resolved_role_gets_its_card_and_only_its_own_handover(world):
    out = _ctx(world, _payload(world[1]))
    assert f"You are `{WRITER}`" in out and "SECRET-WRITER-NOTE" in out
    assert "SECRET-OTHER-NOTE" not in out and f"Handover {OTHER}" not in out


def test_unresolved_gets_the_fallback_listing_and_one_launch_hint_and_nothing_privileged(world):
    root, repo, state_root = world
    out = _ctx(world, _payload(repo, agent_type=None, source="clear"))
    assert out.count("session-roles: no role resolved") == 1
    assert "existing handover notes found" in out  # the old hook, kept as the fallback
    assert "You are `" not in out and "SECRET" not in out
    assert not (state_root / WRITER).exists()  # nothing bound
    startup = _ctx(world, _payload(repo, agent_type=None))
    assert startup.count("session-roles: no role resolved") == 1 and "existing handover notes" not in startup


def test_each_start_appends_a_binding_and_updates_the_instance(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo, session_id="a"))
    _ctx(world, _payload(repo, session_id="b", source="clear"))
    bindings = st.read_bindings(state_root, WRITER)
    assert [b.session_id for b in bindings] == ["a", "b"]
    assert bindings[0].manifest_digest == md.manifest_digest(root)
    assert bindings[1].source == "clear" and bindings[0].worktree == str(repo.resolve())
    assert st.read_instance(state_root, WRITER).holder.session_id == "b"


def test_the_writer_role_takes_the_lease_and_another_role_cannot_take_a_held_one(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo))
    assert st.read_lease(state_root, repo).role == WRITER
    _ctx(world, _payload(repo, agent_type=f"session-{OTHER}", session_id="d"))
    assert st.read_lease(state_root, repo).role == WRITER  # the designer did not take it


@pytest.mark.parametrize("role_id", ["rpg-designer", "agent-working-planner", "testing-planner", "codebase-designer"])
def test_a_designer_or_planner_takes_the_lease_in_its_own_worktree(world, role_id):
    """TCK-20261007-SESSION-PER-ROLE-WORKTREES: each designer/planner is the writer of its own worktree."""
    root, repo, state_root = world
    out = _ctx(world, _payload(repo, agent_type=f"session-{role_id}"))
    assert "WRITER LEASE NOT TAKEN" not in out and st.read_lease(state_root, repo).role == role_id


def test_a_planners_second_instance_does_not_take_the_planners_lease(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo, agent_type="session-agent-working-planner"))
    out = _ctx(world, _payload(repo, agent_type="session-agent-working-planner", session_id="s2"),
               env={"SESSION_ROLE": "agent-working-planner-2"})
    assert "WRITER LEASE NOT TAKEN" not in out and st.read_lease(state_root, repo).role == "agent-working-planner"


def test_another_roles_lease_is_reported_not_stolen(world):
    root, repo, state_root = world
    st.take_lease(state_root, repo, "someone-else", "s0", None)
    out = _ctx(world, _payload(repo))
    assert "WRITER LEASE NOT TAKEN" in out and "someone-else" in out
    assert st.read_lease(state_root, repo).role == "someone-else"
    assert f"You are `{WRITER}`" in out  # still bound and carded


def test_a_changed_manifest_is_reported_on_resume_and_an_authority_reduction_is_flagged(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo, session_id="a"))
    path = root / "registries" / "session_authority.yaml"
    data = yaml.safe_load(path.read_text())
    fn = data["function_defaults"][ROSTER.role(WRITER).function]
    fn["forbidden"] = list(fn["forbidden"]) + ["a brand new prohibition"]
    path.write_text(yaml.safe_dump(data))
    out = _ctx(world, _payload(repo, session_id="b", source="resume", agent_type=None, session_title=WRITER))
    assert "the manifest changed since your last binding" in out and "a brand new prohibition" in out
    assert "AUTHORITY WAS REDUCED" in out


def test_a_manifest_change_that_does_not_touch_this_role_is_silent(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo, session_id="a"))
    path = root / "registries" / "session_authority.yaml"
    data = yaml.safe_load(path.read_text())
    mine = ROSTER.role(WRITER).function
    other = next(f for f in data["function_defaults"] if f != mine)
    data["function_defaults"][other]["forbidden"] = list(data["function_defaults"][other]["forbidden"]) + ["zzz"]
    path.write_text(yaml.safe_dump(data))
    out = _ctx(world, _payload(repo, session_id="b", source="clear"))
    assert "manifest changed" not in out and "AUTHORITY WAS REDUCED" not in out


def test_an_unchanged_manifest_adds_no_digest_message(world):
    root, repo, state_root = world
    _ctx(world, _payload(repo, session_id="a"))
    out = _ctx(world, _payload(repo, session_id="b", source="clear"))
    assert "manifest changed" not in out


def test_resume_from_a_different_cwd_stores_the_transcript_path_as_a_hint_only(world, tmp_path):
    root, repo, state_root = world
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pl = _payload(repo, source="resume", agent_type=None, session_title=WRITER,
                  transcript_path="/new/cwd/project/dir/t.jsonl")
    out = _ctx(world, pl)
    assert f"You are `{WRITER}`" in out
    assert st.read_bindings(state_root, WRITER)[0].transcript_path == "/new/cwd/project/dir/t.jsonl"
    # no file at that path exists, and resolution/binding did not need it
    assert not Path("/new/cwd/project/dir/t.jsonl").exists()


def test_a_second_live_holder_is_flagged(world):
    root, repo, state_root = world
    live = subprocess.Popen(["sleep", "30"])
    try:
        ident = st.process_identity(live.pid)
        st.record_start(state_root, st.Binding("other-sess", WRITER, "startup", str(repo), "b", "", ident, "d", "2026-10-04T00:00:00Z"))
        assert "another LIVE instance already holds role" in _ctx(world, _payload(repo, session_id="new"))
    finally:
        live.kill(); live.wait()


def _holder(state_root, repo, session_id, process):
    st.record_start(state_root, st.Binding(session_id, WRITER, "startup", str(repo), "b", "", process, "d", "2026-10-04T00:00:00Z"))


def test_clear_in_the_same_process_does_not_warn_about_the_superseded_session(world):
    """TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING (a): same ProcessId, new session id -> no warning."""
    root, repo, state_root = world
    live = subprocess.Popen(["sleep", "30"])
    try:
        _holder(state_root, repo, "before-clear", st.process_identity(live.pid))
        out = _ctx(world, _payload(repo, session_id="after-clear", source="clear"), {"CLAUDE_PID": str(live.pid)})
        assert "another LIVE instance" not in out and f"You are `{WRITER}`" in out
        assert st.read_instance(state_root, WRITER).holder.session_id == "after-clear"  # supersession still recorded
    finally:
        live.kill(); live.wait()


def test_a_different_live_process_still_warns_even_when_a_process_is_known(world):
    """(b): the prior holder is another live process; the current session has its own, different process."""
    root, repo, state_root = world
    prior, mine = subprocess.Popen(["sleep", "30"]), subprocess.Popen(["sleep", "30"])
    try:
        _holder(state_root, repo, "other-sess", st.process_identity(prior.pid))
        out = _ctx(world, _payload(repo, session_id="new", source="startup"), {"CLAUDE_PID": str(mine.pid)})
        assert "another LIVE instance already holds role" in out and "other-sess" in out
    finally:
        for p in (prior, mine):
            p.kill(); p.wait()


def test_a_dead_prior_process_does_not_warn(world):
    """(c): an orphaned prior holder is not a live second writer (existing behaviour)."""
    root, repo, state_root = world
    dead = subprocess.Popen(["sleep", "30"])
    ident = st.process_identity(dead.pid)
    dead.kill(); dead.wait()
    _holder(state_root, repo, "dead-sess", ident)
    assert "another LIVE instance" not in _ctx(world, _payload(repo, session_id="new"))


def test_replaying_the_recorded_rpg_implementer_clear_binding_yields_no_warning():
    """AC2: 2026-10-06T02:26:56Z `clear`, pid 2366257 holding prior session af245d7d: the predicate sees the same process."""
    recorded = st.ProcessId(pid=2366257, start="257703023", cmdline="claude --name rpg-implementer --agent session-rpg-implementer")
    current = st.ProcessId(pid=2366257, start="257703023", cmdline="claude --name rpg-implementer --agent session-rpg-implementer")
    assert hook._same_process(recorded, current)
    assert not hook._same_process(recorded, st.ProcessId(pid=2366257, start="999", cmdline=recorded.cmdline))  # pid reuse
    assert not hook._same_process(recorded, None) and not hook._same_process(None, current)


# ---- AC3: fail open ----------------------------------------------------------------------------

def _run_main(stdin, cwd):
    return subprocess.run([sys.executable, str(REAL_ROOT / "tools" / "sessions" / "session_start_hook.py")],
                          input=stdin, capture_output=True, text=True, cwd=str(cwd), timeout=20)


@pytest.mark.parametrize("stdin", ["", "not json", "[]", json.dumps({"source": "mystery"}), json.dumps({"source": "startup"})])
def test_main_fails_open_on_bad_payloads(tmp_path, stdin):
    r = _run_main(stdin, tmp_path)  # tmp_path is not a git repo either
    assert r.returncode == 0
    assert r.stdout == "" or "hookSpecificOutput" in r.stdout


def test_unreadable_manifest_injects_nothing_and_exits_zero(world, monkeypatch):
    root, repo, state_root = world
    (root / "registries" / "session_roles.yaml").write_text(": : not yaml : [")
    with pytest.raises(Exception):
        hook.build_context(_payload(repo), {}, root, state_root)  # the library raises ...
    monkeypatch.setattr(hook, "_REPO_ROOT", root)
    monkeypatch.setattr(hook, "build_context", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(json.dumps(_payload(repo))))
    assert hook.main() == 0  # ... and main() swallows it


def test_find_claude_pid_uses_claude_pid_when_it_names_a_real_process():
    assert hook.find_claude_pid({"CLAUDE_PID": str(os.getpid())}) == os.getpid()
    assert hook.find_claude_pid({"CLAUDE_PID": "999999999"}) in (None, *range(1, 2**22))


# ---- instance ids: a role with max_sessions > 1 (owner decision 2026-10-04: second holder is <role>-N) ----

def _roster_with_two(role_id):
    import dataclasses
    roles = tuple(dataclasses.replace(r, max_sessions=2) if r.role == role_id else r for r in ROSTER.roles)
    return dataclasses.replace(ROSTER, roles=roles)


def test_second_instance_resolves_to_the_same_role_with_its_own_instance_id():
    two = _roster_with_two(WRITER)
    res = resolve(Signals("startup", agent_type=f"session-{WRITER}", env_role=f"{WRITER}-2", session_title=f"{WRITER}-2"), two)
    assert (res.status, res.role, res.instance) == (RESOLVED, WRITER, f"{WRITER}-2")
    first = resolve(Signals("startup", agent_type=f"session-{WRITER}", session_title=WRITER), two)
    assert (first.role, first.instance) == (WRITER, WRITER)
    assert resolve(Signals("resume", session_title=f"{WRITER}-2"), two).instance == f"{WRITER}-2"


def test_an_instance_id_beyond_max_sessions_is_unknown_and_two_different_instances_disagree():
    assert resolve(Signals("startup", session_title=f"{WRITER}-2"), ROSTER).status == UNRESOLVED  # max_sessions is 1
    two = _roster_with_two(WRITER)
    assert resolve(Signals("startup", session_title=f"{WRITER}-2", env_role=WRITER), two).instance == f"{WRITER}-2"
    three = _roster_with_two(WRITER)
    import dataclasses
    three = dataclasses.replace(three, roles=tuple(dataclasses.replace(r, max_sessions=3) if r.role == WRITER else r for r in three.roles))
    assert resolve(Signals("startup", session_title=f"{WRITER}-2", env_role=f"{WRITER}-3"), three).status == DISAGREE


def test_a_second_instance_neither_takes_nor_complains_about_the_writer_lease(world):
    """Launcher fix D: `<role>-2` has a different id from the lease holder; it skips the lease silently."""
    root, repo, state_root = world
    first = _ctx(world, _payload(repo, agent_type="session-rpg-implementer"), {"SESSION_ROLE": "rpg-implementer"})
    assert "WRITER LEASE NOT TAKEN" not in first and st.read_lease(state_root, repo).role == "rpg-implementer"
    second = _ctx(world, _payload(repo, agent_type="session-rpg-implementer", session_id="sess-2"),
                  {"SESSION_ROLE": "rpg-implementer-2"})
    assert "WRITER LEASE NOT TAKEN" not in second
    assert st.read_lease(state_root, repo).role == "rpg-implementer"
