"""The platform domain (TCK-20261013-PLATFORM-DOMAIN-SEATS): compose and Docker moved from lead."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.sessions.card import CARD_BUDGET_TOKENS, compose_card, estimate_tokens
from tools.sessions.roster import load_authority, load_roster
from tools.sessions.route import route

REPO = Path(__file__).resolve().parents[2]
ROSTER = load_roster(REPO)
AUTHORITY = load_authority(REPO)


@pytest.mark.parametrize("path", ["compose.yaml", "docker/backend.Dockerfile"])
def test_compose_and_docker_resolve_to_platform_not_lead(path):
    result = route(path, ROSTER)
    assert result.domains == ("platform",)
    assert "lead-planner" not in result.seats


def test_lead_keeps_the_other_stack_roots():
    assert route("Makefile", ROSTER).domains == ("lead",)
    assert route("pyproject.toml", ROSTER).domains == ("lead",)


def test_platform_has_a_planner_and_an_implementer_but_no_designer():
    roles = {r.role for r in ROSTER.roles if r.domain == "platform"}
    assert roles == {"platform-planner", "platform-implementer"}


def test_platform_implementer_is_dispatched_by_its_planner_and_the_user():
    role = next(r for r in ROSTER.roles if r.role == "platform-implementer")
    assert set(role.accepts_dispatch_from) == {"user", "platform-planner"}


@pytest.mark.parametrize("name", ["platform-planner", "platform-implementer"])
def test_platform_cards_exist_and_fit_the_budget(name):
    assert (REPO / ".claude" / "agents" / f"session-{name}.md").is_file()
    card = compose_card(name, ROSTER, AUTHORITY, REPO)
    assert "Domain: platform" in card
    assert estimate_tokens(card) <= CARD_BUDGET_TOKENS == 400
