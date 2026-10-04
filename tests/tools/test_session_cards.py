"""Session role cards: composition and budget (session-layer M1b)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools.sessions.card import CARD_BUDGET_TOKENS, TEMPLATE_DIR, compose_card, estimate_tokens
from tools.sessions.roster import FUNCTIONS, load_authority, load_roster

ROOT = Path(__file__).resolve().parents[2]
ROSTER = load_roster(ROOT)
AUTHORITY = load_authority(ROOT)


def test_every_function_and_domain_has_a_template_with_a_card_section():
    for function in FUNCTIONS:
        assert "## Card" in (ROOT / TEMPLATE_DIR / "functions" / f"{function}.md").read_text(encoding="utf-8")
    for domain in ROSTER.domains:
        assert "## Card" in (ROOT / TEMPLATE_DIR / "domains" / f"{domain.name}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("role_id", [r.role for r in ROSTER.roles])
def test_composed_card_is_within_the_token_budget(role_id):
    card = compose_card(role_id, ROSTER, AUTHORITY, ROOT)
    assert estimate_tokens(card) <= CARD_BUDGET_TOKENS, f"{role_id}: {estimate_tokens(card)} tokens"


def test_budget_estimate_is_conservative_for_a_known_string():
    # 35 characters at 3.5 chars/token: exactly 10 tokens; the estimator rounds up.
    assert estimate_tokens("x" * 35) == 10
    assert estimate_tokens("x" * 36) == 11


@pytest.mark.parametrize("role", ROSTER.roles, ids=lambda r: r.role)
def test_card_authority_matches_session_authority_file(role):
    card = compose_card(role.role, ROSTER, AUTHORITY, ROOT)
    base = AUTHORITY.for_function(role.function)
    assert f"Needs the user: {', '.join(base.needs_user)}." in card
    if base.forbidden:
        assert f"Never: {', '.join(base.forbidden)}." in card
    for grant in AUTHORITY.grants_for(role.role):
        assert "/".join(grant.actions) in card and grant.date in card


def test_card_carries_role_ownership_routes_and_handover():
    role = ROSTER.role("agent-working-implementer")
    card = compose_card(role.role, ROSTER, AUTHORITY, ROOT)
    assert "`agent-working-implementer`" in card
    assert role.handover in card
    assert "rpg-planner" in card  # a route target
    assert "tools/{agent-monitoring,delivery," in card  # shared parents are named once


def test_unstaffed_seat_names_its_holder_on_the_card():
    card = compose_card("agent-working-planner", ROSTER, AUTHORITY, ROOT)
    assert "unstaffed, held by agent-working-designer" in card


def test_only_the_card_section_is_injected(tmp_path):
    for sub in ("functions", "domains"):
        (tmp_path / TEMPLATE_DIR / sub).mkdir(parents=True)
    for function in FUNCTIONS:
        (tmp_path / TEMPLATE_DIR / "functions" / f"{function}.md").write_text(f"# t\n\nRATIONALE-{function}\n\n## Card\nCARD-{function}\n\n## Notes\nNOTES\n", encoding="utf-8")
    for domain in ROSTER.domains:
        (tmp_path / TEMPLATE_DIR / "domains" / f"{domain.name}.md").write_text("## Card\nCARD-DOMAIN\n", encoding="utf-8")
    card = compose_card("rpg-planner", ROSTER, AUTHORITY, tmp_path)
    assert "CARD-planner" in card and "CARD-DOMAIN" in card
    assert "RATIONALE" not in card and "NOTES" not in card


def test_template_without_card_section_is_an_error(tmp_path):
    for sub in ("functions", "domains"):
        (tmp_path / TEMPLATE_DIR / sub).mkdir(parents=True)
    (tmp_path / TEMPLATE_DIR / "functions" / "planner.md").write_text("# no card here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Card"):
        compose_card("rpg-planner", ROSTER, AUTHORITY, tmp_path)


def test_define_once_templates_do_not_restate_authority_classes():
    # Authority classes are generated from session_authority.yaml; a template that lists them would be a second copy.
    classes = {c for _, fa in AUTHORITY.function_defaults for c in (*fa.needs_user, *fa.forbidden)}
    for path in (ROOT / TEMPLATE_DIR).rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for cls in classes:
            assert not re.search(rf"\b{re.escape(cls)}\b", text),  f"{path.name} restates authority class {cls!r}"
