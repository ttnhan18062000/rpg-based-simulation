"""Regression tests for TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP.

Static, raw-source-text-parsing tests against
`.claude/skills/implement-ticket/SKILL.md` — follows the established
`Path.read_text()` pattern used in `tests/tools/test_current_run_sidecar_orchestrator.py`
for non-Python source files (no Markdown test runner exists for `.claude/skills/*.md`).

Covers: `SKILL.md`'s Step 0 ("Context search") is a single, upfront, before-Scope-only
`search_docs`/`graphify` call — it does not repeat per phase. Three post-fix violations
(`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`,
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`,
`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`) showed hand-orchestrating
sessions performing Investigate-phase work directly, skipping straight to grep/Read
with zero phase-scoped search_docs/graphify call. The fix adds a self-contained,
phase-scoped search-before-grep callout directly inside step 2's ("Investigate") own
text block, mirroring the fix already applied to `.claude/agents/investigator.md` by
`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`.

These tests bound their assertions to the region between the literal markers
`"2. **Investigate**"` and `"3. **Plan**"` so that a fix landing only in Step 0 (the
explicitly ruled-out failure mode, per investigation.md's Anti-Drift Hazards) cannot
false-pass.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_PATH = _REPO_ROOT / ".claude" / "skills" / "implement-ticket" / "SKILL.md"

_INVESTIGATE_MARKER = "2. **Investigate**"
_PLAN_MARKER = "3. **Plan**"


def _investigate_step_text() -> str:
    text = _SKILL_PATH.read_text()
    start = text.index(_INVESTIGATE_MARKER)
    end = text.index(_PLAN_MARKER, start)
    return text[start:end]


def test_skill_investigate_step_has_search_before_grep_callout():
    region = _investigate_step_text()

    assert "mcp__knowledge-search__search_docs" in region, (
        "SKILL.md step 2 (Investigate) must call out "
        "mcp__knowledge-search__search_docs by its real tool identifier"
    )
    assert "graphify" in region, (
        "SKILL.md step 2 (Investigate) must call out graphify by name"
    )
    assert "does not substitute" in region, (
        "SKILL.md step 2 (Investigate) must explicitly state that Step 0's "
        "upfront search does not substitute for a phase-scoped call here"
    )


def test_skill_investigate_callout_survives_step0_removal_check():
    region = _investigate_step_text()

    assert "search_docs" in region
    assert "graphify" in region
    assert "call" in region.lower(), (
        "the callout must contain an imperative instruction, not a bare "
        "cross-reference like 'see Step 0'"
    )
    assert "see step 0" not in region.lower(), (
        "the callout must be self-contained, not a bare pointer back to Step 0"
    )
    assert len(region) > 200, (
        "the Investigate step's text block should carry a substantive, "
        "self-contained instruction, not a one-line pointer"
    )
