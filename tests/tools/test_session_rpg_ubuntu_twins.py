"""TCK-20261025-RPG-UBUNTU-SEATS: three host-ubuntu rpg twins (`-ubuntu`); the plain u24desktop rpg seats keep every route."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.sessions import validate
from tools.sessions.card import CARD_BUDGET_TOKENS, compose_card, estimate_tokens
from tools.sessions.roster import handover_rel, load_authority, load_roster
from tools.sessions.route import route

REPO = Path(__file__).resolve().parents[2]
ROSTER = load_roster(REPO)
AUTHORITY = load_authority(REPO)
TWINS = {
    "rpg-designer-ubuntu": ("rpg-designer", "rpg-designer-ubuntu", ["user"]),
    "rpg-planner-ubuntu": ("rpg-planner", "rpg-planner-ubuntu", ["user", "rpg-designer-ubuntu"]),
    "rpg-implementer-ubuntu": ("rpg-implementer", "rpg-ubuntu", ["user", "rpg-planner-ubuntu"]),
}


def test_the_roster_validates_with_the_three_twins():
    assert validate.validate(REPO) == []
    for role in TWINS:
        assert ROSTER.role(role) is not None


@pytest.mark.parametrize("twin,spec", TWINS.items())
def test_a_twin_copies_its_plain_role_and_takes_dispatch_only_from_user_and_its_own_host(twin, spec):
    plain_name, worktree, dispatch = spec
    plain, t = ROSTER.role(plain_name), ROSTER.role(twin)
    assert list(t.accepts_dispatch_from) == dispatch
    assert all(src == "user" or src.endswith("-ubuntu") for src in t.accepts_dispatch_from)
    assert (t.domain, t.function, t.max_sessions, t.owns) == (plain.domain, plain.function, plain.max_sessions, plain.owns)
    assert t.worktree == worktree and t.worktree != plain.worktree
    assert handover_rel(t, twin) == f".claude/handover/{twin}.md"
    assert t.seat_status == "staffed"


def test_the_plain_roles_dispatch_is_unchanged_and_never_names_a_twin():
    assert list(ROSTER.role("rpg-designer").accepts_dispatch_from) == ["user"]
    assert list(ROSTER.role("rpg-planner").accepts_dispatch_from) == ["user", "rpg-designer"]
    assert list(ROSTER.role("rpg-implementer").accepts_dispatch_from) == ["user", "rpg-planner"]


@pytest.mark.parametrize("path", ["src/core/x.py", "docs/mechanics/01_entity_anatomy.md", "registries/mechanisms.yaml"])
def test_route_still_names_the_plain_rpg_planner(path):
    result = route(path, ROSTER)
    assert result.seats == ("rpg-planner",)


def test_the_worktree_writer_slots_are_distinct():
    slots = {w.name: w.writer for w in ROSTER.worktrees if w.name.startswith("rpg")}
    assert slots["rpg-ubuntu"] == "rpg-implementer-ubuntu" and slots["rpg"] == "rpg-implementer"
    assert slots["rpg-designer-ubuntu"] == "rpg-designer-ubuntu" and slots["rpg-planner-ubuntu"] == "rpg-planner-ubuntu"


@pytest.mark.parametrize("role", ["rpg-designer", "rpg-planner", "rpg-implementer", *TWINS])
def test_every_rpg_card_exists_names_its_host_and_fits_the_budget(role):
    assert (REPO / ".claude" / "agents" / f"session-{role}.md").is_file()
    card = compose_card(role, ROSTER, AUTHORITY, REPO)
    assert ("Host ubuntu." if role in TWINS else "Host u24desktop; twin `-ubuntu`.") in card
    assert estimate_tokens(card) <= CARD_BUDGET_TOKENS
