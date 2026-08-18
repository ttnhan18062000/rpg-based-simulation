"""
Anti-drift guard for docs/guidelines/design_patterns.md.
Ensures the doc does not present V1 GoalEvaluator/GOAL_REGISTRY as still-current. `GoalScorer` and
`src/ai/goals/` were archived as V1-only when this guard was authored
(TCK-20260626-FIX-DESIGN-PATTERNS) but were deliberately revived as the current V2 tier-5 extension
point in TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (see design_patterns.md's own primary-section
prose) — they are intentionally excluded from `v1_symbols` below, not an oversight.
"""
import re

DOC_PATH = "docs/guidelines/design_patterns.md"
LEGACY_SECTION_HEADER = "Legacy Patterns"  # Expected header for the V1 archive section


def _load() -> str:
    with open(DOC_PATH, "r") as f:
        return f.read()


def test_v1_symbols_not_in_primary_sections():
    """
    GoalEvaluator and GOAL_REGISTRY must not appear in any primary (H2) section
    outside the legacy archive section.

    Strategy: split on the legacy section header; check that V1 symbols do not
    appear in the content BEFORE the legacy section header.
    """
    content = _load()
    v1_symbols = ["GoalEvaluator", "GOAL_REGISTRY"]

    # Find where the legacy section starts
    legacy_idx = content.find(LEGACY_SECTION_HEADER)
    assert legacy_idx != -1, (
        f"{DOC_PATH} must contain a '## {LEGACY_SECTION_HEADER}' (or similar) section "
        "to archive V1 patterns. Found no such header."
    )

    # Check that V1 symbols are NOT in the primary (pre-legacy) content
    primary_content = content[:legacy_idx]
    for symbol in v1_symbols:
        assert symbol not in primary_content, (
            f"V1 symbol '{symbol}' found in primary (non-legacy) section of {DOC_PATH}. "
            "This symbol must only appear under the Legacy Patterns archive section."
        )


def test_v2_extension_patterns_documented():
    """
    The doc must document at least 3 V2 extension patterns by name.
    """
    content = _load()
    required_patterns = [
        "Domain Phase",         # Pattern A — XPhase class with apply()/execute()
        "StateUpdate",          # Pattern B — typed update records
        "StatePresenter",       # Pattern C — presenter/read-model layer
    ]
    for pattern in required_patterns:
        assert pattern in content, (
            f"V2 pattern term '{pattern}' not found in {DOC_PATH}. "
            "The doc must document V2 extension points."
        )


def test_v2_file_paths_cited():
    """
    The doc must reference the authoritative V2 source files, not only V1 paths.
    """
    content = _load()
    required_paths = [
        "src/domains/",         # Domain phases live here
        "src/core/updates.py",  # Typed update records
        "src/api/presenters/",  # Presenter layer
    ]
    for path in required_paths:
        assert path in content, (
            f"V2 path '{path}' not cited in {DOC_PATH}. "
            "The doc must reference real V2 source locations."
        )


def test_legacy_section_clearly_marked():
    """
    The V1 archive section must be present and marked as not-for-new-code.
    """
    content = _load()
    assert LEGACY_SECTION_HEADER in content, (
        f"{DOC_PATH} must contain a section header with '{LEGACY_SECTION_HEADER}' "
        "to clearly mark V1 patterns as historical."
    )
    # The section header must also contain "(V1" to make the legacy framing explicit
    assert "(V1" in content[content.find(LEGACY_SECTION_HEADER):content.find(LEGACY_SECTION_HEADER) + 100], (
        f"Legacy section header in {DOC_PATH} must include '(V1' to be clearly marked. "
        "Expected a header like '## Legacy Patterns (V1 — do not use in new code)'."
    )
    # The section must contain at least one of the V1 symbols (confirming it's the archive)
    legacy_idx = content.find(LEGACY_SECTION_HEADER)
    legacy_content = content[legacy_idx:]
    assert any(sym in legacy_content for sym in ["GoalScorer", "src/ai/goals/"]), (
        f"Legacy section in {DOC_PATH} does not mention V1 symbols. "
        "Expected GoalScorer or src/ai/goals/ to appear in the archive section."
    )


def test_no_broken_src_links_in_doc():
    """
    All 'src/' paths cited in the doc (as inline code) must exist on disk.
    Catches regressions where file paths are invented or have moved.
    """
    import os
    content = _load()
    # Match backtick-quoted src/ paths: `src/foo/bar.py`
    cited_paths = re.findall(r"`(src/[^`]+\.py)`", content)
    for rel_path in set(cited_paths):
        assert os.path.exists(rel_path), (
            f"{DOC_PATH} cites '{rel_path}' but the file does not exist. "
            "Update the doc to reflect the current source layout."
        )
