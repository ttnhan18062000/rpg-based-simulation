"""TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS (#620 part 1): five `-u24` roles for the seats that also run on host u24desktop.

Uses the real manifest. Rows refer to the test plan in the ticket's staging artifacts.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.sessions import boundary as bd  # noqa: E402
from tools.sessions import launch as ln  # noqa: E402
from tools.sessions import route as rt  # noqa: E402
from tools.sessions import validate  # noqa: E402
from tools.sessions.card import CARD_BUDGET_TOKENS, compose_card, estimate_tokens  # noqa: E402
from tools.sessions.generate_agents import check_generated  # noqa: E402
from tools.sessions.roster import handover_rel, load_authority, load_roster  # noqa: E402

ROSTER = load_roster(REPO)
AUTH = load_authority(REPO)
TWINS = {
    "platform-planner-u24": ("platform-planner", "platform-planner-u24"),
    "platform-implementer-u24": ("platform-implementer", "platform-u24"),
    "agent-working-designer-u24": ("agent-working-designer", "agent-working-designer-u24"),
    "agent-working-planner-u24": ("agent-working-planner", "agent-working-planner-u24"),
    "agent-working-implementer-u24": ("agent-working-implementer", "agent-working-u24"),
}
_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}


def _git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True, env=_ENV)


def _edit(path):
    return {"tool_name": "Edit", "session_id": "s", "cwd": str(REPO), "tool_input": {"file_path": path}}


def test_row1_the_roster_validates_with_the_five_twins():  # 1
    assert validate.validate(REPO) == []
    for u24 in TWINS:
        assert ROSTER.role(u24) is not None
    names = [r.session_name for r in ROSTER.roles]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("path,seat", [
    ("tools/search_shared.py", "agent-working-planner"),
    (".github/workflows/pr-body-lint.yml", "agent-working-planner"),
    (".github/workflows/publish-images.yml", "platform-planner"),
])
def test_row2_route_keeps_resolving_to_the_plain_seat(path, seat):  # 2
    result = rt.route(path, ROSTER)
    assert result.seats == (seat,)


@pytest.mark.parametrize("u24,twin", [(k, v[0]) for k, v in TWINS.items()])
def test_row3_each_u24_card_has_its_note_and_every_card_is_in_budget(u24, twin):  # 3
    card = compose_card(u24, ROSTER, AUTH)
    assert ROSTER.role(u24).card_note and ROSTER.role(u24).card_note in card
    assert "u24desktop" in ROSTER.role(u24).card_note
    if twin != "agent-working-designer":  # the unstaffed marker on that card already says it; no room for a note
        assert ROSTER.role(twin).card_note and ROSTER.role(twin).card_note in compose_card(twin, ROSTER, AUTH)
    assert estimate_tokens(card) <= CARD_BUDGET_TOKENS and estimate_tokens(compose_card(twin, ROSTER, AUTH)) <= CARD_BUDGET_TOKENS


def test_row3_the_generated_agent_files_are_current():
    assert check_generated(REPO) == []
    for u24 in TWINS:
        assert (REPO / f".claude/agents/session-{u24}.md").is_file()


@pytest.mark.parametrize("u24,logical", [(k, v[1]) for k, v in TWINS.items()])
def test_row4_each_u24_role_has_its_own_logical_worktree_and_handover(u24, logical):  # 4
    role = ROSTER.role(u24)
    twin = ROSTER.role(TWINS[u24][0])
    assert role.worktree == logical != twin.worktree
    assert role.legacy_session_name is None
    assert handover_rel(role) == f".claude/handover/{u24}.md"
    assert ln.default_worktree_path(role, Path("/m")) == Path("/m/.claude/worktrees") / logical


@pytest.fixture
def seats(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    (main / "f").write_text("base\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")
    for rel in ("registries", "docs/guidelines/session_roles", ".claude/agents"):
        shutil.copytree(REPO / rel, main / rel)
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "roster")
    return main


@pytest.mark.parametrize("u24", sorted(TWINS))
def test_row4b_a_reused_plain_named_path_still_launches_the_u24_role(u24, seats, tmp_path, monkeypatch, capsys):  # 4b
    twin, logical = TWINS[u24]
    plain_named = tmp_path / "elsewhere" / ROSTER.role(twin).worktree
    _git(seats, "worktree", "add", "-q", "-b", f"{u24}-b", str(plain_named))
    monkeypatch.setattr(os, "execvpe", lambda *a, **k: pytest.fail("must not exec in a dry run"))
    assert ln.main([u24, "--dry-run", "--worktree", str(plain_named)], root=plain_named) == 0
    out = capsys.readouterr().out
    assert f"handover note: {seats}/.claude/handover/{u24}.md" in out
    assert f"/.claude/handover/{twin}.md" not in out
    resolved = ln.resolve_target(u24, ROSTER)
    assert resolved.role.role == u24 and resolved.instance == u24 and resolved.role.worktree == logical
    slots = {w.name: w.writer for w in ROSTER.worktrees}
    assert slots[logical] == u24 and slots[ROSTER.role(twin).worktree] == twin
    assert logical not in out.replace(u24, "")  # the dry run prints no lease or slot line, so the slot is asserted on the roster above


@pytest.mark.parametrize("u24,twin", [(k, v[0]) for k, v in TWINS.items()])
def test_row5_the_write_grant_equals_the_twins(u24, twin):  # 5
    a, b = ROSTER.role(u24), ROSTER.role(twin)
    assert set(a.may_write) == set(b.may_write)
    for path in ("tools/sessions/launch.py", "docs/plans/agent_infrastructure/x.md", "agent-working/tickets/todos/x.md",
                 "compose.yaml", "src/engine/x.py"):
        fa = bd.check_edit(_edit(path), a, ROSTER)
        fb = bd.check_edit(_edit(path), b, ROSTER)
        assert (fa is None) == (fb is None), path


def test_row6_u24_roles_accept_dispatch_only_from_user_and_same_host_roles():  # 6
    u24 = set(TWINS)
    for name in TWINS:
        sources = set(ROSTER.role(name).accepts_dispatch_from)
        assert sources <= {"user"} | u24, name
    assert ROSTER.role("agent-working-planner-u24").accepts_dispatch_from == ("user", "agent-working-designer-u24")
    assert ROSTER.role("agent-working-implementer-u24").accepts_dispatch_from == (
        "user", "agent-working-designer-u24", "agent-working-planner-u24")
    assert ROSTER.role("platform-implementer-u24").accepts_dispatch_from == ("user", "platform-planner-u24")
    assert ROSTER.role("agent-working-designer-u24").accepts_dispatch_from == ("user",)
    # the plain roles are unchanged (owner 2026-10-18)
    assert ROSTER.role("agent-working-planner").accepts_dispatch_from == ("user", "agent-working-designer")
    assert not any(u in r.accepts_dispatch_from for r in ROSTER.roles if r.role not in u24 for u in u24)


def test_row7_seat_status():  # 7
    for name in TWINS:
        r = ROSTER.role(name)
        assert (r.seat_status, r.interim_holder) == ("staffed", None), name
    planner = ROSTER.role("agent-working-planner")
    assert (planner.seat_status, planner.interim_holder) == ("staffed", None)
    designer = ROSTER.role("agent-working-designer")
    assert designer.seat_status == "unstaffed" and designer.interim_holder
