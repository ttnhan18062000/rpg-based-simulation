"""Tests for tools/sessions/boundary.py (TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS).

Advisory `role_boundary` events: an edit outside the caller's domain and a work-assigning message to a role that
does not accept it from the sender each warn once per session and log one event; an edit inside the domain, an
unowned path and a plain finding log nothing; the guard never turns an advisory into a permission decision; a
write failure is swallowed; the event has its own field set and never touches the monitoring `agent` vocabulary.
Also pins the M0b-backed read-only mechanism: a role whose `tools` is an allowlist renders `tools:` into its
generated agent file, and no seat uses one today (owner decision pending).
"""
import io
import json
from pathlib import Path

import pytest

from tools.sessions import boundary as bd
from tools.sessions import guard
from tools.sessions import state as st
from tools.sessions.generate_agents import render_agent_file
from tools.sessions.roster import load_authority
from tools.sessions.roster import load_roster

_REPO_ROOT = Path(__file__).parent.parent.parent
ROSTER = load_roster()


def _caller(role_id):
    role = ROSTER.role(role_id)
    return guard.Caller(True, role_id, role.role, role.function, "binding")


def _edit(path, session="s1", cwd=None):
    return {"tool_name": "Edit", "session_id": session, "cwd": str(cwd or _REPO_ROOT), "tool_input": {"file_path": path}}


def _msg(to, text, session="s1"):
    return {"tool_name": "SendMessage", "session_id": session, "cwd": str(_REPO_ROOT),
            "tool_input": {"to": to, "message": text}}


def _events(data_dir):
    return [json.loads(line) for f in data_dir.glob("*/role_boundary.jsonl") for line in f.read_text().splitlines()]


# ---- pure checks ------------------------------------------------------------------------------

def test_agent_working_implementer_editing_src_is_a_boundary_event():
    found = bd.check_edit(_edit("src/engine/spatial_query.py"), ROSTER.role("agent-working-implementer"), ROSTER)
    kind, key, fields = found
    assert kind == bd.KIND_EDIT and fields["owner_domains"] == ["rpg"] and fields["path"] == "src/engine/spatial_query.py"
    assert key.startswith("rpg:src/engine")


@pytest.mark.parametrize("path", ["tools/sessions/guard.py", "docs/plans/agent_infrastructure/x.md", "registries/session_roles.yaml"])
def test_editing_inside_the_domain_is_not_an_event(path):
    assert bd.check_edit(_edit(path), ROSTER.role("agent-working-implementer"), ROSTER) is None


@pytest.mark.parametrize("path", ["docs/REGISTRY.yaml", ".claude/handover/drafts/x.md", "agent-working/tickets/todos/x.md"])
def test_unowned_paths_are_not_an_event(path):
    assert bd.check_edit(_edit(path), ROSTER.role("agent-working-implementer"), ROSTER) is None


def test_split_path_not_including_the_domain_is_an_event_and_including_it_is_not():
    assert bd.check_edit(_edit("tests/tools/x.py"), ROSTER.role("agent-working-implementer"), ROSTER) is None
    assert bd.check_edit(_edit("tests/tools/x.py"), ROSTER.role("codebase-implementer"), ROSTER) is not None


def test_a_narrow_may_write_grant_exempts_but_the_universal_one_does_not():
    planner = ROSTER.role("agent-working-planner")
    assert "**" not in planner.may_write
    assert bd.check_edit(_edit("agent-working/tickets/todos/x.md"), planner, ROSTER) is None
    assert ROSTER.role("agent-working-implementer").may_write == ("**",)
    assert bd.check_edit(_edit("src/x.py"), ROSTER.role("agent-working-implementer"), ROSTER) is not None


def test_path_outside_the_worktree_is_ignored(tmp_path):
    assert bd.check_edit(_edit("/etc/hosts"), ROSTER.role("agent-working-implementer"), ROSTER) is None


def test_dispatch_to_a_role_that_does_not_accept_the_sender_is_a_mismatch():
    found = bd.check_message(_msg("rpg-implementer", "Dispatch from X: do this"), "agent-working-implementer", ROSTER)
    kind, target, fields = found
    assert kind == bd.KIND_MESSAGE and target == "rpg-implementer" and fields["message_class"] == "dispatch"
    assert "message" not in fields and "Dispatch" not in json.dumps(fields)


def test_dispatch_from_an_accepted_sender_or_a_finding_is_not_a_mismatch():
    assert bd.check_message(_msg("agent-working-implementer", "Dispatch: next batch"), "agent-working-planner", ROSTER) is None
    assert bd.check_message(_msg("agent-working-implementer", "dispatch from design"), "agent-working-designer", ROSTER) is None
    assert bd.check_message(_msg("rpg-implementer", "Finding: x is red on main"), "agent-working-implementer", ROSTER) is None
    assert bd.check_message(_msg("rpg-implementer", "question: who owns y? dispatch is not this"), "agent-working-implementer", ROSTER) is None


def test_second_instance_sender_uses_its_base_role_for_acceptance():
    assert bd.check_message(_msg("rpg-implementer", "Dispatch: x"), "rpg-planner-2", ROSTER) is None


# ---- advise: once per session, event shape, failure handling ----------------------------------

def test_warn_and_log_once_per_path_class_per_session(tmp_path):
    root, data = tmp_path / "roles", tmp_path / "data"
    caller = _caller("agent-working-implementer")
    first = bd.advise(_edit("src/engine/a.py"), caller, ROSTER, root, data)
    second = bd.advise(_edit("src/engine/b.py"), caller, ROSTER, root, data)
    other_class = bd.advise(_edit("src/core/c.py"), caller, ROSTER, root, data)
    other_session = bd.advise(_edit("src/engine/a.py", session="s2"), caller, ROSTER, root, data)
    assert first and "not blocked" in first and second is None and other_class and other_session
    assert len(_events(data)) == 3


def test_event_has_its_own_field_set_and_no_agent_field(tmp_path):
    data = tmp_path / "data"
    bd.advise(_edit("src/engine/a.py"), _caller("agent-working-implementer"), ROSTER, tmp_path / "r", data)
    (event,) = _events(data)
    assert event["event"] == "role_boundary" and event["kind"] == bd.KIND_EDIT
    assert event["session_role"] == "agent-working-implementer" and event["session_id"] == "s1"
    assert "agent" not in event and "phase" not in event and event["ts"].endswith("Z")


def test_role_boundary_file_is_not_an_events_shard_so_the_vocabulary_ratchet_never_sees_it(tmp_path):
    data = tmp_path / "data"
    bd.advise(_edit("src/engine/a.py"), _caller("agent-working-implementer"), ROSTER, tmp_path / "r", data)
    assert not list(data.glob("*/events.jsonl")) and not list(data.glob("*/runs.jsonl"))
    assert [p.name for p in data.glob("*/*.jsonl")] == ["role_boundary.jsonl"]


def test_unresolved_caller_and_unrelated_tools_log_nothing(tmp_path):
    data = tmp_path / "data"
    assert bd.advise(_edit("src/x.py"), guard.Caller(resolved=False), ROSTER, tmp_path / "r", data) is None
    assert bd.advise({"tool_name": "Read", "tool_input": {"file_path": "src/x.py"}}, _caller("agent-working-implementer"),
                     ROSTER, tmp_path / "r", data) is None
    assert not data.exists()


def test_event_write_failure_is_swallowed(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(bd, "write_event", boom)
    assert bd.advise(_edit("src/engine/a.py"), _caller("agent-working-implementer"), ROSTER, tmp_path / "r") is None
    monkeypatch.undo()
    assert bd.write_event({"x": 1}, tmp_path / "ro" / "\0bad") is False


def test_state_write_failure_never_repeats_a_warning(tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("x")
    assert bd.first_time(blocked, "s1", "k") is False


def test_write_event_end_to_end_writes_one_json_line(tmp_path):
    assert bd.write_event({"event": "role_boundary", "kind": "k"}, tmp_path) is True
    (line,) = [json.loads(x) for f in tmp_path.glob("*/role_boundary.jsonl") for x in f.read_text().splitlines()]
    assert line["kind"] == "k"


# ---- through the guard: advisory text only, never a decision ----------------------------------

def _binding(role, session_id):
    return st.Binding(session_id=session_id, role=role, source="startup", worktree="/w", branch="b",
                      transcript_path="", process=None, manifest_digest="d", ts="2026-10-05T00:00:00Z")


def _run_guard(payload, monkeypatch, root, data):
    monkeypatch.setattr(st, "state_root", lambda cwd=".": root)
    real = bd.write_event
    monkeypatch.setattr(bd, "write_event", lambda record, data_dir=None: real(record, data))
    out, err = io.StringIO(), io.StringIO()
    code = guard.main(io.StringIO(json.dumps(payload)), out, err)
    return code, out.getvalue(), err.getvalue()


def test_guard_emits_additional_context_not_a_permission_decision(tmp_path, monkeypatch):
    root = tmp_path / "roles"
    st.record_start(root, _binding("agent-working-implementer", "sess-A"))
    code, out, _ = _run_guard(_edit("src/engine/a.py", session="sess-A"), monkeypatch, root, tmp_path / "data")
    body = json.loads(out)["hookSpecificOutput"]
    assert code == 0 and "additionalContext" in body and "permissionDecision" not in body
    code, out, _ = _run_guard(_edit("src/engine/b.py", session="sess-A"), monkeypatch, root, tmp_path / "data")
    assert code == 0 and out == ""
    assert len(_events(tmp_path / "data")) == 1


def test_guard_edit_inside_owns_is_silent(tmp_path, monkeypatch):
    root = tmp_path / "roles"
    st.record_start(root, _binding("agent-working-implementer", "sess-A"))
    code, out, _ = _run_guard(_edit("tools/sessions/x.py", session="sess-A"), monkeypatch, root, tmp_path / "data")
    assert (code, out) == (0, "") and not (tmp_path / "data").exists()


def test_guard_authority_decision_is_unchanged_and_carries_no_advisory(tmp_path, monkeypatch):
    root = tmp_path / "roles"
    st.record_start(root, _binding("agent-working-implementer", "sess-A"))
    payload = {"tool_name": "Bash", "session_id": "sess-A", "cwd": str(_REPO_ROOT), "tool_input": {"command": "gh pr merge 1"}}
    code, out, _ = _run_guard(payload, monkeypatch, root, tmp_path / "data")
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == guard.ASK
    assert "additionalContext" not in out


def test_guard_advisory_failure_never_changes_the_exit_code(tmp_path, monkeypatch):
    root = tmp_path / "roles"
    st.record_start(root, _binding("agent-working-implementer", "sess-A"))
    monkeypatch.setattr(bd, "advise", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    code, out, err = _run_guard(_edit("src/engine/a.py", session="sess-A"), monkeypatch, root, tmp_path / "data")
    assert (code, out, err) == (0, "", "")


def test_guard_sendmessage_mismatch_warns_when_the_tool_is_wired(tmp_path, monkeypatch):
    root = tmp_path / "roles"
    st.record_start(root, _binding("agent-working-implementer", "sess-A"))
    code, out, _ = _run_guard(_msg("rpg-implementer", "Dispatch from X: go", session="sess-A"), monkeypatch, root, tmp_path / "data")
    assert code == 0 and "accepts dispatch only from" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


# ---- read-only allowlist mechanism (M0b) ------------------------------------------------------

def test_an_allowlist_role_renders_a_tools_line_and_no_seat_has_one_today():
    from dataclasses import replace

    role = ROSTER.role("rpg-designer")
    allow = replace(role, tools=("Read", "Glob", "Grep", "SendMessage"))
    assert "tools: Read, Glob, Grep, SendMessage" in render_agent_file(allow, ROSTER, load_authority())
    assert "tools:" not in render_agent_file(role, ROSTER, load_authority()).split("---")[1]
    assert [r.role for r in ROSTER.roles if r.tools is not None] == []
