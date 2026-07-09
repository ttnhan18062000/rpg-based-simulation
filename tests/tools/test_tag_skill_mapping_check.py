"""Tests for tools/tag_skill_mapping_check.py."""

import sys
from pathlib import Path

import pytest

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_skill_mapping_check import (  # noqa: E402
    KNOWN_TAGS,
    check_tag_skill_mapping_consistency,
    extract_pairs_arrow_list,
    extract_pairs_js_escaped,
    extract_pairs_markdown,
    normalize_target,
)

_DEBUGGING_TARGET = (
    "`/debugging-strategies` — unless `Related Code Areas` includes a path under "
    "`src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or "
    "`src/core/registries.py`, in which case suggest `Agent(subagent_type: \"world-debugger\")` "
    "instead"
)

# ---------------------------------------------------------------------------
# extract_pairs_markdown (Format A)
# ---------------------------------------------------------------------------


def test_extract_pairs_markdown_parses_all_four_tags():
    text = (
        "| Tag | Suggested skill |\n"
        "|---|---|\n"
        "| `api-design` | `/api-design-principles` |\n"
        f"| `debugging` | {_DEBUGGING_TARGET} |\n"
        "| `performance` | `/python-performance-optimization` |\n"
        "| `security` | `/security-review` (first codification of this mapping) |\n"
    )

    pairs = extract_pairs_markdown(text)

    assert set(pairs) == KNOWN_TAGS
    assert pairs["api-design"] == "`/api-design-principles`"
    assert pairs["performance"] == "`/python-performance-optimization`"
    assert "world-debugger" in pairs["debugging"]


# ---------------------------------------------------------------------------
# extract_pairs_js_escaped (Format B)
# ---------------------------------------------------------------------------


def test_extract_pairs_js_escaped_parses_all_four_tags():
    debugging_target_escaped = _DEBUGGING_TARGET.replace("`", "\\`")
    text = (
        "  | Tag | Suggested skill |\n"
        "  |---|---|\n"
        "  | \\`api-design\\` | \\`/api-design-principles\\` |\n"
        f"  | \\`debugging\\` | {debugging_target_escaped} |\n"
        "  | \\`performance\\` | \\`/python-performance-optimization\\` |\n"
        "  | \\`security\\` | \\`/security-review\\` |\n"
    )

    pairs = extract_pairs_js_escaped(text)

    assert set(pairs) == KNOWN_TAGS
    assert pairs["api-design"] == "\\`/api-design-principles\\`"
    assert "world-debugger" in pairs["debugging"]


# ---------------------------------------------------------------------------
# extract_pairs_arrow_list (Format C)
# ---------------------------------------------------------------------------


def _arrow_list_fixture() -> str:
    return (
        "  suggested_skills:\n"
        "  - Map each assigned tag against this table; empty array if nothing matches:\n"
        "      api-design  -> /api-design-principles\n"
        "      debugging   -> /debugging-strategies (or Agent(subagent_type: \"world-debugger\") if\n"
        "                     related_code_areas includes a path under src/worldassembly/,\n"
        "                     src/worldbuilding/, src/worldmodules/, src/content/, or\n"
        "                     src/core/registries.py)\n"
        "      performance -> /python-performance-optimization\n"
        "      security    -> /security-review\n"
        "  - Do not invent mappings for tags outside this 4-entry table\n"
    )


def test_extract_pairs_arrow_list_parses_all_four_tags_including_multiline_debugging():
    pairs = extract_pairs_arrow_list(_arrow_list_fixture())

    assert set(pairs) == KNOWN_TAGS
    assert pairs["api-design"] == "/api-design-principles"
    assert "src/worldassembly/" in pairs["debugging"]
    assert "src/worldbuilding/" in pairs["debugging"]
    assert "src/worldmodules/" in pairs["debugging"]
    assert "src/content/" in pairs["debugging"]
    assert "src/core/registries.py" in pairs["debugging"]


def test_extract_pairs_arrow_list_raises_on_missing_anchor():
    text = _arrow_list_fixture().replace(
        "Do not invent mappings for tags outside this 4-entry table", "some other closing line"
    )

    with pytest.raises(ValueError, match="could not locate arrow-list mapping block"):
        extract_pairs_arrow_list(text)


# ---------------------------------------------------------------------------
# normalize_target
# ---------------------------------------------------------------------------


def test_normalize_target_captures_skill_and_carveout_paths():
    worded_one = (
        "`/debugging-strategies` unless a path under `src/worldassembly/`, "
        "`src/worldbuilding/`, `src/worldmodules/`, `src/content/`, or `src/core/registries.py` "
        "is touched, in which case use world-debugger instead"
    )
    worded_two = (
        "/debugging-strategies (or Agent(subagent_type: \"world-debugger\") if "
        "related_code_areas includes a path under src/worldassembly/, src/worldbuilding/, "
        "src/worldmodules/, src/content/, or src/core/registries.py)"
    )

    normalized_one = normalize_target(worded_one)
    normalized_two = normalize_target(worded_two)

    assert normalized_one == normalized_two
    assert normalized_one == (
        "/debugging-strategies",
        "world-debugger",
        (
            "src/content/",
            "src/core/registries.py",
            "src/worldassembly/",
            "src/worldbuilding/",
            "src/worldmodules/",
        ),
    )


def test_normalize_target_ignores_prose_only_differences():
    verbose = "`/security-review` (first codification of this mapping in the repo — no existing CLAUDE.md auto-invoke row for it yet)"
    terse = "`/security-review`"

    assert normalize_target(verbose) == normalize_target(terse)


def test_normalize_target_ignores_excluded_path_mentioned_outside_carveout_list():
    # Mirrors ticket-scoper.md's debugging row: a trailing parenthetical explicitly says
    # `src/worldgeneration/` is EXCLUDED from the carve-out — it must not be read as a 6th path.
    with_excluded_mention = _DEBUGGING_TARGET + (
        " (mirrors CLAUDE.md's existing debugging carve-out; note `src/worldgeneration/` is "
        "intentionally excluded — that path only appears in `world-debugger.md`'s own broader "
        "scope list, not CLAUDE.md's, and this mapping follows CLAUDE.md)"
    )

    assert normalize_target(with_excluded_mention) == normalize_target(_DEBUGGING_TARGET)
    assert "src/worldgeneration/" not in normalize_target(with_excluded_mention)[2]


# ---------------------------------------------------------------------------
# check_tag_skill_mapping_consistency
# ---------------------------------------------------------------------------


def test_check_tag_skill_mapping_consistency_passes_against_live_repo_files():
    mismatches = check_tag_skill_mapping_consistency()

    assert mismatches == []


def _write_consistent_fixture(root: Path, *, security_target: str = "/security-review") -> None:
    ticket_scoper = root / ".claude" / "agents" / "ticket-scoper.md"
    ticket_tagging = root / "docs" / "guides" / "ticket_tagging.md"
    implement_ticket = root / ".claude" / "workflows" / "implement-ticket.js"
    create_tickets = root / ".claude" / "workflows" / "create-tickets.js"

    for path in (ticket_scoper, ticket_tagging, implement_ticket, create_tickets):
        path.parent.mkdir(parents=True, exist_ok=True)

    markdown_table = (
        "| Tag | Suggested skill |\n"
        "|---|---|\n"
        "| `api-design` | `/api-design-principles` |\n"
        f"| `debugging` | {_DEBUGGING_TARGET} |\n"
        "| `performance` | `/python-performance-optimization` |\n"
        f"| `security` | `{security_target}` |\n"
    )
    ticket_scoper.write_text(markdown_table, encoding="utf-8")
    ticket_tagging.write_text(markdown_table, encoding="utf-8")

    debugging_target_escaped = _DEBUGGING_TARGET.replace("`", "\\`")
    js_table = (
        "  | Tag | Suggested skill |\n"
        "  |---|---|\n"
        "  | \\`api-design\\` | \\`/api-design-principles\\` |\n"
        f"  | \\`debugging\\` | {debugging_target_escaped} |\n"
        "  | \\`performance\\` | \\`/python-performance-optimization\\` |\n"
        f"  | \\`security\\` | \\`{security_target}\\` |\n"
    )
    implement_ticket.write_text(js_table, encoding="utf-8")

    create_tickets.write_text(
        "  suggested_skills:\n"
        "  - Map each assigned tag against this table; empty array if nothing matches:\n"
        "      api-design  -> /api-design-principles\n"
        "      debugging   -> /debugging-strategies (or Agent(subagent_type: \"world-debugger\") if\n"
        "                     related_code_areas includes a path under src/worldassembly/,\n"
        "                     src/worldbuilding/, src/worldmodules/, src/content/, or\n"
        "                     src/core/registries.py)\n"
        "      performance -> /python-performance-optimization\n"
        f"      security    -> {security_target}\n"
        "  - Do not invent mappings for tags outside this 4-entry table\n",
        encoding="utf-8",
    )


def test_check_tag_skill_mapping_consistency_detects_injected_divergence(tmp_path):
    _write_consistent_fixture(tmp_path)
    # Diverge implement-ticket.js's security target to a genuinely different skill path — not a
    # whitespace/formatting change — so the mismatch is a real semantic divergence.
    implement_ticket = tmp_path / ".claude" / "workflows" / "implement-ticket.js"
    text = implement_ticket.read_text(encoding="utf-8")
    implement_ticket.write_text(
        text.replace("\\`/security-review\\`", "\\`/some-other-skill\\`"), encoding="utf-8"
    )

    mismatches = check_tag_skill_mapping_consistency(root=tmp_path)

    tags_mismatched = {m["tag"] for m in mismatches}
    assert "security" in tags_mismatched


def test_check_tag_skill_mapping_consistency_reports_which_files_disagree(tmp_path):
    _write_consistent_fixture(tmp_path)
    implement_ticket = tmp_path / ".claude" / "workflows" / "implement-ticket.js"
    text = implement_ticket.read_text(encoding="utf-8")
    implement_ticket.write_text(
        text.replace("\\`/security-review\\`", "\\`/some-other-skill\\`"), encoding="utf-8"
    )

    mismatches = check_tag_skill_mapping_consistency(root=tmp_path)

    security_mismatch = next(m for m in mismatches if m["tag"] == "security")
    values = security_mismatch["values"]
    assert str(Path(".claude/workflows/implement-ticket.js")) in values
    diverging_value = values[str(Path(".claude/workflows/implement-ticket.js"))]
    other_value = values[str(Path(".claude/agents/ticket-scoper.md"))]
    assert diverging_value != other_value
    assert diverging_value[0] == "/some-other-skill"
