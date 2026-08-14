"""Tests for the new .claude/skills/progression-entities/SKILL.md
(TCK-20260805-PROGRESSION-ENTITIES-SKILL), sourced from docs/mechanics/01_entity_anatomy.md and
docs/mechanics/attribute_progression_contract.md.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "progression-entities" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "progression-entities" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_REAL_ATTRIBUTES = ["STR", "AGI", "VIT", "END", "INT", "SPI", "WIS", "PER", "CHA"]
_REAL_PROG_COMPLIANCE_IDS = ["PROG-067", "PROG-068", "PROG-069", "PROG-070"]
_REAL_RECALC_STEPS_IN_ORDER = [
    "Base Attributes", "Equipment Bonuses", "Passive Skill Bonuses",
    "Trait Bonuses", "Movement Cost", "Tactical Role Derivation",
]


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: progression-entities" in parts[1]
    assert "source: project" in parts[1]


def test_contains_all_nine_core_attributes():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for attr in _REAL_ATTRIBUTES:
        assert f"**{attr}**" in text, f"missing core attribute: {attr}"


def test_contains_real_derived_stat_formulas():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "base_hp + (vitality * 2) + int(endurance * 0.5) + gear_hp" in text
    assert "int(100 * (level ** 1.5))" in text


def test_contains_real_xp_threshold_values():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for value in ("100", "283", "520", "8,944", "35,355"):
        assert value in text, f"missing real XP threshold value: {value}"


def test_contains_all_four_prog_compliance_ids():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for compliance_id in _REAL_PROG_COMPLIANCE_IDS:
        assert compliance_id in text, f"missing compliance ID: {compliance_id}"


def test_recalculation_steps_appear_in_correct_order():
    """Getting this order wrong would silently produce incorrect derived stats — tested by
    relative position, not just presence."""
    text = _SKILL_MD.read_text(encoding="utf-8")
    positions = [text.index(step) for step in _REAL_RECALC_STEPS_IN_ORDER]
    assert positions == sorted(positions), (
        "recalculation steps are not in the correct real order"
    )


def test_contains_both_real_pipeline_phases():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "evolution" in text
    assert "progression_conversion" in text


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/progression-entities" in text
    assert "progression-entities/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
