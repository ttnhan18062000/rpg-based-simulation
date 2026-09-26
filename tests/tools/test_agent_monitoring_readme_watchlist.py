"""Tests for TCK-20260925-RETRO-WATCHLIST-TABLE: docs/agent-monitoring/README.md's
`## Measurement Watchlist` table and the retro skill's procedure step that reads it.

Light checks per the ticket's own instruction ("light — not a schema validator"): heading exists,
table has rows, the removed KGMCP stub is gone, durable sections are untouched, and the retro
skill's numbered procedure (not its `## Related` footer) names the file.
"""
from pathlib import Path

README_PATH = Path("docs/agent-monitoring/README.md")
SKILL_PATH = Path(".claude/skills/agent-monitoring-retro/SKILL.md")

DURABLE_SECTION_HEADINGS = [
    "## Baseline Metrics Snapshot (one-off)",
    "## Security Gate Firing Check",
    "## Skill Usage Metric",
    "## Done-Ticket Monitoring Coverage Audit",
    "## Agent Tool-Usage Baseline",
    "## Bash Command Mix Baseline",
]


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_watchlist_heading_and_nonempty_table_exist():
    text = _readme_text()
    assert "## Measurement Watchlist" in text
    section = text.split("## Measurement Watchlist", 1)[1].split("\n## ", 1)[0]
    table_lines = [l for l in section.splitlines() if l.strip().startswith("|")]
    # header row + separator row + at least one data row
    assert len(table_lines) >= 3


def test_kgmcp_stub_removed():
    text = _readme_text()
    assert "Knowledge Gateway MCP Phase 0 Measurement Baseline" not in text


def test_seeded_row_carries_ref_and_no_after_caveat():
    text = _readme_text()
    section = text.split("## Measurement Watchlist", 1)[1].split("\n## ", 1)[0]
    assert "16.04" in section
    assert "0e0ff8f2" in section
    assert "not" in section.lower() and "implementation batch" in section.lower()


def test_durable_sections_untouched():
    text = _readme_text()
    for heading in DURABLE_SECTION_HEADINGS:
        assert heading in text, f"missing durable section: {heading}"


def test_removal_rule_stated_in_preamble():
    text = _readme_text()
    section = text.split("## Measurement Watchlist", 1)[1].split("\n## ", 1)[0]
    assert "deleted" in section.lower() or "delete" in section.lower()


def test_retro_skill_names_readme_path_in_procedure():
    """AC4/AC5: the path must appear in the numbered procedure itself, not only as a `## Related`
    footer pointer."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    what_this_does = text.split("## What This Skill Does", 1)[1].split("\n## ", 1)[0]
    assert "docs/agent-monitoring/README.md" in what_this_does
