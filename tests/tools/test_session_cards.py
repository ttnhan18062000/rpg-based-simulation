"""Session role cards: composition and budget (session-layer M1b)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools.sessions.card import _IMPLIED_BY, CARD_BUDGET_TOKENS, TEMPLATE_DIR, compose_card, estimate_tokens
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
    # an action whose parent the role never does (push_default_branch when push is forbidden) is not repeated
    shown = [a for a in base.needs_user if _IMPLIED_BY.get(a) not in base.forbidden]
    assert f"Needs the user: {', '.join(shown)}." in card
    assert set(base.needs_user) - set(shown) <= set(_IMPLIED_BY), "only the declared implied actions may be elided"
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
    card = compose_card("agent-working-designer", ROSTER, AUTHORITY, ROOT)
    assert "unstaffed, held by agent-working-planner" in card


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


def test_compact_globs_names_a_shared_first_segment_once_for_multi_segment_leaves():
    from tools.sessions.card import _compact_globs

    globs = ["docs/agent-monitoring/**", "docs/plans/agent_infrastructure/**", "docs/guidelines/session_roles/**"]
    assert _compact_globs(globs) == "docs/{agent-monitoring,plans/agent_infrastructure,guidelines/session_roles}/**"


@pytest.mark.parametrize(
    "globs",
    [
        ["docs/plans/a/**", "docs/plans/b/**", "docs/plans/c/**"],
        ["docs/a/**", "docs/b/**"],
        ["src/x/**", "docs/plans/a/**", "docs/plans/b/**", "tools/y.py"],
        ["docs/a/**"],
    ],
)
def test_compact_globs_is_never_longer_than_the_full_parent_grouping(globs):
    from tools.sessions.card import _DIR_GLOB, _compact_globs, _group_globs

    assert len(_compact_globs(globs)) <= len(_group_globs(globs, _DIR_GLOB))


def test_designer_and_planner_cards_list_a_push_to_main_under_needs_the_user_now_that_nothing_is_forbidden():
    """Owner, 2026-10-07: no function is forbidden commit/push/open_pr, so there is no `Never:` line and the push to
    the default branch is listed like the implementer's."""
    for role_id in ("rpg-designer", "agent-working-planner"):
        card = compose_card(role_id, ROSTER, AUTHORITY, ROOT)
        assert "Never:" not in card and "push_default_branch" in card
    assert "push_default_branch" in compose_card("rpg-implementer", ROSTER, AUTHORITY, ROOT)


def test_adjacent_sibling_files_with_a_shared_stem_prefix_share_one_brace_entry():
    """TCK-20261010-...: `tools/graphify_link.py, tools/graphify_prune.py` -> `tools/graphify_{link,prune}.py`."""
    from tools.sessions.card import _compact_globs

    assert _compact_globs(["a/**", "tools/graphify_link.py", "tools/graphify_prune.py", "b.md"]) == \
        "a/**, tools/graphify_{link,prune}.py, b.md"
    # different directory, extension, or no shared `_`/`-` prefix: left alone
    assert _compact_globs(["x/a_one.py", "y/a_two.py"]) == "x/a_one.py, y/a_two.py"
    assert _compact_globs(["x/a_one.py"]) == "x/a_one.py"


def test_same_directory_file_globs_fold_into_one_brace_group_when_shorter():
    """Owner-planner decision, 2026-10-14: `tools/graphify_{link,prune}.py, tools/search_*.py, tools/start_*_mcp.sh`
    -> `tools/{graphify_{link,prune}.py,search_*.py,start_*_mcp.sh}`."""
    from tools.sessions.card import _compact_globs

    assert _compact_globs(["a/**", "tools/graphify_link.py", "tools/graphify_prune.py", "tools/search_*.py",
                           "tools/start_*_mcp.sh", "tests/x/**"]) == \
        "a/**, tools/{graphify_{link,prune}.py,search_*.py,start_*_mcp.sh}, tests/x/**"
    assert _compact_globs(["x/a_one.py", "x/a_two.md"]) == "x/{a_one.py,a_two.md}"
    # a lone file, files in different directories, and directory globs are left alone
    assert _compact_globs(["x/one.py", "y/two.py"]) == "x/one.py, y/two.py"
    assert _compact_globs(["x/one.py", "z/**"]) == "x/one.py, z/**"


def test_search_mcp_files_route_to_agent_working_and_every_card_stays_in_budget():
    from tools.sessions.route import OWNED, route

    for path in ("tools/search_mcp.py", "tools/search_server.py", "tools/search_shared.py",
                 "tools/start_search_mcp.sh", "tools/start_headroom_mcp.sh"):
        result = route(path, ROSTER)
        assert result.status == OWNED and result.domains == ("agent-working",), path
    for role in ROSTER.roles:
        card = compose_card(role.role, ROSTER, AUTHORITY, ROOT)
        assert estimate_tokens(card) <= CARD_BUDGET_TOKENS, f"{role.role}: {estimate_tokens(card)} tokens"


# --- scattered single files in a directory the role does not own as a whole -> `dir/ (N files)` ---

from tools.sessions.card import COUNT_NOTE, _count_scattered_files, _role_line  # noqa: E402


def test_two_scattered_files_in_an_unowned_dir_become_a_count():
    out = _count_scattered_files(["a/**", "docs/observability/x_policy.md", "b/**", "docs/observability/y_contract.md"])
    assert out == ["a/**", "docs/observability/ (2 files)", "b/**"]


def test_a_single_file_in_its_dir_is_unchanged():
    globs = ["a/**", ".github/workflows/pr-body-lint.yml", "docs/guides/cross_session_messages.md"]
    assert _count_scattered_files(globs) == globs


def test_files_in_an_owned_dir_are_unchanged():
    globs = ["docs/observability/**", "docs/observability/a_policy_file.md", "docs/observability/b_policy_file.md"]
    assert _count_scattered_files(globs) == globs
    assert _count_scattered_files(["docs/**", "docs/guides/aaaa_long_name.md", "docs/guides/bbbb_long_name.md"]) == [
        "docs/**", "docs/guides/aaaa_long_name.md", "docs/guides/bbbb_long_name.md"]


def test_a_brace_form_that_is_already_shorter_is_unchanged():
    globs = ["x/a.b", "x/c.d"]  # `x/{a.b,c.d}` (11) is shorter than `x/ (2 files)` (12)
    assert _count_scattered_files(globs) == globs


def test_wildcards_are_not_counted_as_files():
    globs = ["tools/search_*.py", "tools/*_search.py"]
    assert _count_scattered_files(globs) == globs


def test_the_note_appears_only_when_it_pays_for_itself():
    counted = [r for r in ROSTER.roles if "(N files" not in compose_card(r.role, ROSTER, AUTHORITY, ROOT)
               and COUNT_NOTE in compose_card(r.role, ROSTER, AUTHORITY, ROOT)]
    assert counted == []
    implementer = compose_card("agent-working-implementer", ROSTER, AUTHORITY, ROOT)
    assert "docs/observability/ (2 files)" in implementer and COUNT_NOTE in implementer
    assert _role_line(ROSTER.role("agent-working-implementer"), ROSTER).count(COUNT_NOTE) == 1
    # a role with nothing to count carries no note
    assert COUNT_NOTE not in compose_card("lead-planner", ROSTER, AUTHORITY, ROOT)
