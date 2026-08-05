"""Tests for the new .claude/skills/cognition-strategy/SKILL.md
(TCK-20260805-COGNITION-STRATEGY-SKILL), sourced from docs/cognition/README.md,
docs/mechanics/04_strategic_cognition.md, docs/strategy/bounded_cognition_decision_flow.md, and
docs/engine/authoritative_pipeline.md.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "cognition-strategy" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "cognition-strategy" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_REAL_NOT_STATEMENTS = [
    "Not strategy", "Not domain decision logic", "Not AI personality", "Not social or intelligence",
]
_REAL_SCORING_FORMULAS = [
    "0.30*p + 0.20*u + 0.15*s + 0.25*a + 0.10*resume_reliability",
    "0.25*p + 0.40*u + 0.25*s + 0.10*(1.0 - resistance)",
    "0.40*sev + 0.30*cp_score + 0.15*budget + 0.15*patience",
]
_REAL_PIPELINE_PHASES = {
    "self_model": "ENABLE_SELF_MODEL_COGNITION",
    "information_belief": "ENABLE_BELIEF_ASSIMILATION",
    "information_intent_execution": "ENABLE_INFORMATION_INTENT_EXECUTION",
    "strategic_intelligence": "STRAT-002",
}


def _body_sections(text: str) -> list:
    """Returns the ordered list of ## section headings in the file body (after frontmatter)."""
    body = text.split("---", 2)[2]
    return re.findall(r"^## (.+)$", body, flags=re.MULTILINE)


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: cognition-strategy" in parts[1]
    assert "source: project" in parts[1]


def test_boundary_section_is_structurally_first():
    """Not just present somewhere — the ticket's own Scope explicitly requires this to be
    foregrounded, not buried, so this checks position, not just substring presence."""
    text = _SKILL_MD.read_text(encoding="utf-8")
    sections = _body_sections(text)
    assert sections, "no ## sections found in skill body"
    assert "boundary" in sections[0].lower()


def test_contains_all_four_not_statements():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for statement in _REAL_NOT_STATEMENTS:
        assert statement in text, f"missing NOT-statement: {statement}"


def test_contains_interruption_resistance_formula_and_not_hardcoded_caveat():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "Interruption_Margin = Profile_Resistance * resistance_multiplier" in text
    assert "not a hardcoded 30.0" in text


def test_contains_all_three_real_scoring_formulas():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for formula in _REAL_SCORING_FORMULAS:
        assert formula in text, f"missing scoring formula: {formula}"


def test_contains_all_real_pipeline_phases_and_flags():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for phase, flag in _REAL_PIPELINE_PHASES.items():
        assert phase in text, f"missing pipeline phase: {phase}"
        assert flag in text, f"missing flag/compliance ID: {flag}"


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/cognition-strategy" in text
    assert "cognition-strategy/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
