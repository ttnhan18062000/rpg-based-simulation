"""Tests for the new .claude/skills/systems-economy/SKILL.md (TCK-20260805-SYSTEMS-SKILL),
sourced from docs/mechanics/03_economic_laws.md and docs/systems/buildings_and_economy.md.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "systems-economy" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "systems-economy" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_REAL_PIPELINE_PHASES = {
    "blacksmith": "TOWN-155",
    "quest_rewards": "PROG-084",
    "shop": "TOWN-166",
    "resource_transactions": None,
}


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: systems-economy" in parts[1]
    assert "source: project" in parts[1]


def test_contains_real_reputation_discount_formula():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "clamp(public_reputation, 0.0, 2.0)" in text
    assert "0.20" in text


def test_contains_real_inventory_and_ecology_constants():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "16 slots" in text
    assert "50.0 kg" in text
    assert "ECOLOGY_INTERVAL = 200" in text
    assert "MAX_ACTIVE_QUESTS = 3" in text


def test_contains_all_real_pipeline_phases_and_compliance_ids():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for phase, compliance_id in _REAL_PIPELINE_PHASES.items():
        assert phase in text, f"missing pipeline phase: {phase}"
        if compliance_id:
            assert compliance_id in text, f"missing compliance ID: {compliance_id}"


def test_distinguishes_quest_model_file_from_quest_system_file():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "src/core/quests.py" in text
    assert "src/systems/quest_system.py" in text


def test_discloses_out_of_scope_section():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "What This Skill Does NOT Cover" in text


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/systems-economy" in text
    assert "systems-economy/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
