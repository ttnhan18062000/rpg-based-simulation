"""The advisory architecture domain (TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT): one planner seat, docs/plans/architecture/** only."""

from __future__ import annotations

from pathlib import Path

from tools.sessions import boundary as bd
from tools.sessions.card import CARD_BUDGET_TOKENS, compose_card, estimate_tokens
from tools.sessions.roster import load_authority, load_roster
from tools.sessions.route import route

REPO = Path(__file__).resolve().parents[2]
ROSTER = load_roster(REPO)
AUTHORITY = load_authority(REPO)


def test_architecture_card_exists_and_fits_the_budget():
    assert (REPO / ".claude" / "agents" / "session-architecture-planner-u24.md").is_file()
    card = compose_card("architecture-planner-u24", ROSTER, AUTHORITY, REPO)
    assert "Domain: architecture" in card
    assert estimate_tokens(card) <= CARD_BUDGET_TOKENS


def test_plans_architecture_routes_to_architecture():
    for path in ("docs/plans/architecture/x.md", "docs/plans/architecture/README.md"):
        assert route(path, ROSTER).domains == ("architecture",)
    assert (REPO / "docs/plans/architecture/README.md").is_file()


def test_adrs_still_route_to_lead():
    assert route("docs/architecture/system_overview.md", ROSTER).domains == ("lead",)


def test_two_planners_and_two_implementers_taking_dispatch_from_the_user_and_their_own_hosts_planner():
    roles = {r.role: r for r in ROSTER.roles if r.domain == "architecture"}
    assert set(roles) == {"architecture-planner", "architecture-planner-u24",
                          "architecture-implementer", "architecture-implementer-u24"}
    assert {n for n, r in roles.items() if r.function == "planner"} == {"architecture-planner", "architecture-planner-u24"}
    for planner in ("architecture-planner", "architecture-planner-u24"):
        assert set(roles[planner].accepts_dispatch_from) == {"user"}
    assert set(roles["architecture-implementer"].accepts_dispatch_from) == {"user", "architecture-planner"}
    assert set(roles["architecture-implementer-u24"].accepts_dispatch_from) == {"user", "architecture-planner-u24"}


def test_the_implementers_have_distinct_worktree_writer_slots():
    slots = {w.name: w.writer for w in ROSTER.worktrees if w.name.startswith("architecture")}
    assert slots == {"architecture": "architecture-implementer", "architecture-u24": "architecture-implementer-u24"}


def test_all_four_cards_exist_and_fit_the_budget():
    for name in ("architecture-planner", "architecture-planner-u24", "architecture-implementer", "architecture-implementer-u24"):
        assert (REPO / ".claude" / "agents" / f"session-{name}.md").is_file()
        card = compose_card(name, ROSTER, AUTHORITY, REPO)
        assert "Domain: architecture" in card and estimate_tokens(card) <= CARD_BUDGET_TOKENS


def test_owns_stay_proposals_only():
    domain = next(d for d in ROSTER.domains if d.name == "architecture")
    assert domain.owns == ("docs/plans/architecture/**",)


def _edit(path):
    return {"tool_input": {"file_path": str(REPO / path)}, "cwd": str(REPO)}


def test_an_architecture_implementer_is_flagged_for_src_but_not_for_its_own_docs():
    for name in ("architecture-implementer", "architecture-implementer-u24"):
        role = ROSTER.role(name)
        assert "**" not in role.may_write
        found = bd.check_edit(_edit("src/x.py"), role, ROSTER)
        assert found is not None and found[0] == "edit_outside_owns"
        assert bd.check_edit(_edit("docs/plans/architecture/x.md"), role, ROSTER) is None
