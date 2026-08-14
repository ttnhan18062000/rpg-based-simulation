"""Tests for TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED's adaptation of
api-design-principles and architecture SKILL.md files, and the corresponding
.agents/ Codex-mirror regeneration.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_API_DESIGN_MD = _REPO_ROOT / ".claude" / "skills" / "api-design-principles" / "SKILL.md"
_ARCHITECTURE_MD = _REPO_ROOT / ".claude" / "skills" / "architecture" / "SKILL.md"
_API_DESIGN_MIRROR = _REPO_ROOT / ".agents" / "skills" / "api-design-principles" / "SKILL.md"
_ARCHITECTURE_MIRROR = _REPO_ROOT / ".agents" / "skills" / "architecture" / "SKILL.md"


def _body(text: str) -> str:
    parts = text.split("---", 2)
    assert len(parts) == 3, "expected frontmatter-delimited SKILL.md"
    return parts[2]


def test_api_design_principles_has_in_this_repo_section():
    text = _API_DESIGN_MD.read_text(encoding="utf-8")
    assert "## In This Repo" in text
    assert "test_api_read_model_guard.py" in text
    assert "presenters" in text


def test_architecture_has_no_dangling_skill_references():
    text = _ARCHITECTURE_MD.read_text(encoding="utf-8")
    assert "@[skills/database-design]" not in text
    assert "@[skills/api-patterns]" not in text
    assert "@[skills/deployment-procedures]" not in text


def test_architecture_related_skills_names_real_in_repo_pointers():
    text = _ARCHITECTURE_MD.read_text(encoding="utf-8")
    assert "architecture-reviewer" in text
    assert "docs/architecture/" in text


def test_disclosure_frontmatter_unchanged_on_both_skills():
    for path in (_API_DESIGN_MD, _ARCHITECTURE_MD):
        text = path.read_text(encoding="utf-8")
        assert 'risk: unknown' in text
        assert 'source: community' in text
        assert 'date_added: "2026-02-27"' in text


def test_agents_mirror_body_matches_claude_source_body_for_both_skills():
    for source_path, mirror_path in (
        (_API_DESIGN_MD, _API_DESIGN_MIRROR),
        (_ARCHITECTURE_MD, _ARCHITECTURE_MIRROR),
    ):
        source_body = _body(source_path.read_text(encoding="utf-8"))
        mirror_body = _body(mirror_path.read_text(encoding="utf-8"))
        assert mirror_body == source_body, (
            f"{mirror_path} body has drifted from {source_path} — "
            "re-run render_codex_guidance() to regenerate"
        )


def test_agents_mirror_frontmatter_stays_minimal_by_design():
    """.agents/ mirrors intentionally do NOT carry risk/source/date_added — that's a Claude-only
    disclosure field, not part of the Codex contract's frontmatter schema. This test guards
    against someone "fixing" the mirror to add them by hand later, which the generator would
    immediately overwrite anyway."""
    for mirror_path in (_API_DESIGN_MIRROR, _ARCHITECTURE_MIRROR):
        frontmatter = mirror_path.read_text(encoding="utf-8").split("---", 2)[1]
        assert "risk:" not in frontmatter
        assert "source:" not in frontmatter
