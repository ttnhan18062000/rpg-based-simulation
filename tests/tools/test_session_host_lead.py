"""TCK-20261013-HOST-LEAD-PLANNER-U24: a second lead seat for host u24desktop; neither lead can write the other's file.

Uses the real manifest. `boundary.check_edit` is advisory (it returns the crossing, the hook warns), so "may not write" here
means: the edit is reported as crossing into the sibling seat's claim.
"""
from pathlib import Path

from tools.sessions import boundary as bd
from tools.sessions import launch as ln
from tools.sessions import validate
from tools.sessions.card import CARD_BUDGET_TOKENS, compose_card, estimate_tokens
from tools.sessions.generate_agents import check_generated
from tools.sessions.roster import load_authority, load_roster

REPO = Path(__file__).parent.parent.parent
ROSTER = load_roster()
AUTH = load_authority()
U24 = ROSTER.role("lead-planner-u24")
LEAD = ROSTER.role("lead-planner")
PAGE = "agent-working/lead/hosts/u24desktop.md"


def _edit(path):
    return {"tool_name": "Edit", "session_id": "s", "cwd": str(REPO), "tool_input": {"file_path": path}}


def test_the_validator_reports_no_findings_for_the_whole_roster():
    assert validate.validate(REPO) == []
    assert len(ROSTER.roles) == 26  # +1 architecture-planner-u24 (#715)


def test_the_u24_seat_is_a_main_checkout_planner_that_nobody_dispatches_to():
    assert (U24.domain, U24.function, U24.launch, U24.worktree) == ("lead", "planner", "main-checkout", "")
    assert U24.accepts_dispatch_from == ("user",)
    assert all("lead-planner-u24" not in r.accepts_dispatch_from for r in ROSTER.roles)


def test_the_u24_seat_writes_exactly_its_page_and_the_shared_bookkeeping():
    assert U24.owns == (PAGE,)
    assert set(U24.may_write) == {".claude/handover/drafts/**", "agent-working/agent-monitoring/**", "docs/REGISTRY.yaml"}
    assert "owns" in U24.overrides


def test_the_u24_seat_may_write_its_page_and_not_board_makefile_or_mcp_json():
    assert bd.check_edit(_edit(PAGE), U24, ROSTER) is None
    for path in ("agent-working/lead/board.md", "Makefile", ".mcp.json", "agent-working/lead/stack_seed_review.md"):
        found = bd.check_edit(_edit(path), U24, ROSTER)
        assert found is not None, path
        assert found[2]["owner_seats"] == ["lead-planner"], path


def test_lead_planner_may_write_the_board_and_not_the_u24_page():
    assert bd.check_edit(_edit("agent-working/lead/board.md"), LEAD, ROSTER) is None
    assert bd.check_edit(_edit("Makefile"), LEAD, ROSTER) is None
    found = bd.check_edit(_edit(PAGE), LEAD, ROSTER)
    assert found is not None and found[2]["owner_seats"] == ["lead-planner-u24"]


def test_a_role_that_narrows_nothing_keeps_the_domain_wide_exemption():
    """Only a role-level owns/owns_not override opts into sibling checks: other seats are unchanged."""
    planner = ROSTER.role("agent-working-planner")
    assert not {"owns", "owns_not"} & set(planner.overrides)
    assert bd.check_edit(_edit("tools/sessions/boundary.py"), planner, ROSTER) is None


def test_the_u24_card_carries_its_note_and_every_card_stays_in_budget():
    card = compose_card("lead-planner-u24", ROSTER, AUTH)
    assert "Host lead for u24desktop" in card and "Never edits `board.md`" in card
    assert "comment only" in card
    assert PAGE in compose_card("lead-planner", ROSTER, AUTH)
    for role in ROSTER.roles:
        assert estimate_tokens(compose_card(role.role, ROSTER, AUTH)) <= CARD_BUDGET_TOKENS, role.role


def test_the_generated_agent_files_are_current_and_the_u24_file_exists():
    assert check_generated(REPO) == []
    assert (REPO / ".claude/agents/session-lead-planner-u24.md").is_file()


def test_launching_the_u24_seat_resolves_to_the_main_checkout_with_no_worktree(tmp_path):
    assert ln.default_worktree_path(U24, tmp_path) == tmp_path


def test_the_host_page_has_frontmatter_and_the_two_sections():
    text = (REPO / PAGE).read_text()
    assert text.startswith("---\n") and "## Sessions on u24desktop" in text and "## Overlap and conflicts" in text


def test_a_non_string_card_note_is_rejected(tmp_path):
    import shutil
    import pytest
    from tools.sessions.roster import RosterError

    (tmp_path / "registries").mkdir()
    for name in ("session_roles.yaml", "session_authority.yaml"):
        shutil.copy(REPO / "registries" / name, tmp_path / "registries" / name)
    path = tmp_path / "registries" / "session_roles.yaml"
    path.write_text(path.read_text().replace('card_note: "Folds', "card_note: [Folds", 1).replace('never edits that page."', 'never edits that page."]', 1))
    with pytest.raises(RosterError):
        load_roster(tmp_path)
