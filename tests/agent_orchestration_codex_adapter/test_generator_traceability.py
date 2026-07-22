from pathlib import Path

from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
from tools.agent_orchestration.loader import load_contract

ROOT = Path(__file__).parent.parent.parent

def test_generated_skill_frontmatter_traces_to_contract(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    for skill in load_contract(ROOT).skills["skills"]:
        text = (tmp_path / ".agents" / "skills" / skill["id"] / "SKILL.md").read_text()
        assert f"name: {skill['id']}" in text
        assert f"description: {skill['description']!r}" in text

def test_generated_skill_body_is_byte_identical_to_claude_source(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    for skill_id in ("brainstorming", "test-driven-development"):
        generated = (tmp_path / ".agents" / "skills" / skill_id / "SKILL.md").read_text()
        source = (ROOT / ".claude" / "skills" / skill_id / "SKILL.md").read_text()
        assert generated.split("---", 2)[2] == source.split("---", 2)[2]


def test_generated_skill_body_matches_full_content_for_frontmatter_less_sources(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    for skill_id in ("create-tickets", "implement-epic", "implement-ticket", "simq-audit"):
        generated = (tmp_path / ".agents" / "skills" / skill_id / "SKILL.md").read_text()
        source = (ROOT / ".claude" / "skills" / skill_id / "SKILL.md").read_text()
        assert generated.split("---", 2)[2] == "\n" + source
        assert "---\n#" in generated


def test_skills_yaml_sixteen_entry_set_is_not_expanded(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    ids = {path.parent.name for path in (tmp_path / ".agents" / "skills").glob("*/SKILL.md")}
    assert len(load_contract(ROOT).skills["skills"]) == 16
    assert not ids.intersection({"clean-code", "codebase-search", "code-review", "create-skill", "receiving-code-review", "requesting-code-review"})
