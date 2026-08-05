"""Tests for the new .claude/skills/combat-mechanics/SKILL.md (TCK-20260805-COMBAT-SKILL),
sourced from docs/mechanics/02_combat_laws.md and
docs/simulation/domains/combat_engagement_contract.md.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "combat-mechanics" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "combat-mechanics" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_REAL_TACTICAL_MODIFIERS = [
    "High Ground", "Flanking", "Surrounded", "Cover", "Shatter", "Exhaustion", "Bond Synergy",
]
_REAL_COMBAT_POSTURES = [
    "IGNORE", "WATCH", "AVOID", "PROBE", "THREATEN",
    "ENGAGE", "SKIRMISH", "CALL_HELP", "RETREAT", "PANIC_FLEE",
]


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: combat-mechanics" in parts[1]
    assert "source: project" in parts[1]


def test_contains_real_damage_formula():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "Atk * (Atk / (Atk + Def * 2.0 + 1.0))" in text


def test_contains_all_seven_tactical_modifiers():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for modifier in _REAL_TACTICAL_MODIFIERS:
        assert modifier in text, f"missing tactical modifier: {modifier}"


def test_contains_all_ten_combat_postures():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for posture in _REAL_COMBAT_POSTURES:
        assert posture in text, f"missing CombatPosture: {posture}"


def test_states_not_authoritative_framing_prominently():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "NOT authoritative" in text
    # Must appear early — this is the single easiest thing to get backwards.
    not_authoritative_idx = text.index("NOT authoritative")
    damage_formula_idx = text.index("Atk * (Atk")
    assert not_authoritative_idx < damage_formula_idx


def test_contains_sliding_state_rule_with_real_phase_and_compliance_id():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "Sliding State" in text
    assert "action_routing" in text
    assert "TOWN-149" in text
    assert "cannot receive a kill reward" in text


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/combat-mechanics" in text
    assert "combat-mechanics/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
