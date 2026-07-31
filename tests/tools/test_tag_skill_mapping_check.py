"""Tests for tools/tag_skill_mapping_check.py.

TCK-20260720-SKILL-MAPPING-DEDUP retired the 10 tests that previously lived here
(test_extract_pairs_markdown_parses_all_four_tags, test_extract_pairs_js_escaped_parses_all_four_tags,
test_extract_pairs_arrow_list_parses_all_four_tags_including_multiline_debugging,
test_extract_pairs_arrow_list_raises_on_missing_anchor, test_normalize_target_captures_skill_and_carveout_paths,
test_normalize_target_ignores_prose_only_differences,
test_normalize_target_ignores_excluded_path_mentioned_outside_carveout_list,
test_check_tag_skill_mapping_consistency_passes_against_live_repo_files,
test_check_tag_skill_mapping_consistency_detects_injected_divergence,
test_check_tag_skill_mapping_consistency_reports_which_files_disagree) because their premise —
parsing and pairwise-comparing 4 independently-maintained texts — no longer applies: all 4 consumer
files now reference a single live source (`tag_registry.get_skill_mapping()`) instead of embedding a
table, so there is nothing left to parse or compare pairwise. The parser functions
(`extract_pairs_markdown`, `extract_pairs_js_escaped`, `extract_pairs_arrow_list`), `normalize_target`,
and `check_tag_skill_mapping_consistency` were deleted along with them.
"""

import sys
from pathlib import Path

import pytest

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_skill_mapping_check import (  # noqa: E402
    KNOWN_TAGS,
    check_consumers_reference_live_source,
)

_CONSUMER_RELATIVE_PATHS = (
    Path(".claude/agents/ticket-scoper.md"),
    Path("docs/guides/ticket_tagging.md"),
    Path(".claude/workflows/implement-ticket.js"),
    Path(".claude/workflows/create-tickets.js"),
)


def _write_reference_only_fixture(root: Path) -> None:
    for rel_path in _CONSUMER_RELATIVE_PATHS:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "Run `python3 tools/tag_registry.py skill-mapping` and match tags against its keys.\n",
            encoding="utf-8",
        )


def test_known_tags_derived_from_live_get_skill_mapping():
    assert KNOWN_TAGS == {"api-design", "debugging", "performance", "security"}


def test_check_consumers_reference_live_source_passes_against_live_repo_files():
    violations = check_consumers_reference_live_source()

    assert violations == []


def test_check_consumers_reference_live_source_detects_missing_reference(tmp_path):
    _write_reference_only_fixture(tmp_path)
    stripped = tmp_path / ".claude" / "agents" / "ticket-scoper.md"
    stripped.write_text("No live-source reference here at all.\n", encoding="utf-8")

    violations = check_consumers_reference_live_source(root=tmp_path)

    assert any(".claude/agents/ticket-scoper.md" in v for v in violations)


def test_check_consumers_reference_live_source_detects_reintroduced_table(tmp_path):
    _write_reference_only_fixture(tmp_path)
    reintroduced = tmp_path / "docs" / "guides" / "ticket_tagging.md"
    reintroduced.write_text(
        "Run `python3 tools/tag_registry.py skill-mapping` — for reference, it currently returns:\n\n"
        "| Tag | Suggested skill |\n"
        "|---|---|\n"
        "| `api-design` | `/api-design-principles` |\n"
        "| `debugging` | `/debugging-strategies` |\n"
        "| `performance` | `/python-performance-optimization` |\n"
        "| `security` | `/security-review` |\n",
        encoding="utf-8",
    )

    violations = check_consumers_reference_live_source(root=tmp_path)

    assert any("docs/guides/ticket_tagging.md" in v for v in violations)


def test_check_consumers_reference_live_source_tolerates_a_couple_of_tag_mentions(tmp_path):
    _write_reference_only_fixture(tmp_path)
    mentions_two = tmp_path / ".claude" / "workflows" / "create-tickets.js"
    mentions_two.write_text(
        "Run `python3 tools/tag_registry.py skill-mapping`. "
        "For example, `api-design` -> ... or `debugging` -> ... come from that live command, not "
        "from a table maintained here.\n",
        encoding="utf-8",
    )

    violations = check_consumers_reference_live_source(root=tmp_path)

    assert violations == []
