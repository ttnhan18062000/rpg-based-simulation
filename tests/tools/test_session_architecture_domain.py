"""The advisory architecture domain (TCK-20261022-ARCHITECTURE-PLANNER-U24-SEAT): one planner seat, docs/plans/architecture/** only."""

from __future__ import annotations

from pathlib import Path

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


def test_the_seat_is_a_lone_main_checkout_planner_dispatched_by_the_user():
    roles = [r for r in ROSTER.roles if r.domain == "architecture"]
    assert [r.role for r in roles] == ["architecture-planner-u24"]
    assert set(roles[0].accepts_dispatch_from) == {"user"}
    assert roles[0].function == "planner"
