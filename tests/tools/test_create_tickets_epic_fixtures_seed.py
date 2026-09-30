"""create-tickets seeds the shared-fixtures subsection on epic-tier tickets (as implement-epic does)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED = "### Shared test fixtures and patterns"


def test_create_tickets_write_prompt_seeds_fixtures_subsection_for_epics():
    text = (REPO_ROOT / ".claude/workflows/create-tickets.js").read_text(encoding="utf-8")
    assert SEED in text and "task.tier is epic" in text


def test_seeded_heading_matches_what_investigator_and_implement_epic_use():
    for rel in (".claude/workflows/implement-epic.js", ".claude/agents/investigator.md"):
        assert SEED in (REPO_ROOT / rel).read_text(encoding="utf-8")
