"""Tests for the new .claude/skills/simq-dev/SKILL.md (TCK-20260805-SIMQ-DEV-SKILL), sourced
from docs/simulation_quality/quality_scoring_contract.md. Must not duplicate simq-audit/SKILL.md's
existing audit/governance content.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "simq-dev" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "simq-dev" / "SKILL.md"
_SIMQ_AUDIT_MD = _REPO_ROOT / ".claude" / "skills" / "simq-audit" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_CORE_DATA_MODEL_CLASSES = ["ScoreRecord", "ScoringContext", "PillarAccumulator"]
_PILLAR_PROTOCOL_MARKERS = [
    "PILLAR_METADATA", "SCORER_REGISTRY", "no numeric literals",
]


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: simq-dev" in parts[1]
    assert "source: project" in parts[1]


def test_contains_core_data_model_classes():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for cls in _CORE_DATA_MODEL_CLASSES:
        assert cls in text, f"missing core data model class: {cls}"


def test_contains_pillar_addition_protocol_markers():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for marker in _PILLAR_PROTOCOL_MARKERS:
        assert marker in text, f"missing pillar-addition protocol marker: {marker}"


def test_discloses_the_economyscorer_divergence():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "EconomyScorer" in text
    assert "paid_info_transaction" in text


def test_does_not_duplicate_simq_audit_content():
    """simq-audit is entirely the audit/governance workflow — this skill covers a different
    lifecycle phase (development/debugging) and must not re-derive simq-audit's own vocabulary."""
    dev_text = _SKILL_MD.read_text(encoding="utf-8")
    audit_text = _SIMQ_AUDIT_MD.read_text(encoding="utf-8")
    assert "Recalibrate" in audit_text  # sanity: confirms this really is simq-audit's vocabulary
    assert "Recalibrate" not in dev_text
    assert "grade anchors" not in dev_text


def test_cross_references_simq_audit_without_duplicating():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "simq-audit" in text


def test_cites_real_test_paths():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for path in (
        "tests/simulation_quality/test_scorer_pillar_binding.py",
        "tests/simulation_quality/test_quality_hub_integration.py",
    ):
        assert path in text
        assert (_REPO_ROOT / path).is_file(), f"cited test path does not actually exist: {path}"


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/simq-dev" in text
    assert "simq-dev/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
