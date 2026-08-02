import shutil
from pathlib import Path

import pytest
import yaml

from tools.agent_orchestration_codex_adapter.errors import CodexAdapterMissingCompanionAssetError
from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
from tools.agent_orchestration.loader import load_contract

ROOT = Path(__file__).parent.parent.parent

def test_generated_skill_frontmatter_traces_to_contract(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    for skill in load_contract(ROOT).skills["skills"]:
        text = (tmp_path / ".agents" / "skills" / skill["id"] / "SKILL.md").read_text()
        assert f"name: {skill['id']}" in text
        assert f"description: {skill['description']!r}" in text


def test_generated_guidance_renders_validated_continuation_policy(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    text = (tmp_path / "AGENTS.md").read_text()
    assert "## Workflow Continuation" in text
    assert "current ticket invocation" in text
    assert "EPIC_SCOPED" in text
    assert "never pre-write a completion row before the ticket move" in text

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


def test_render_codex_guidance_copies_declared_companion_assets_byte_identical(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    for skill in load_contract(ROOT).skills["skills"]:
        for rel in skill["companion_assets"]:
            generated = (tmp_path / ".agents" / "skills" / skill["id"] / rel).read_bytes()
            source = (ROOT / ".claude" / "skills" / skill["id"] / rel).read_bytes()
            assert generated == source


def test_missing_companion_asset_source_raises_named_error(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(ROOT / "agent-orchestration", source / "agent-orchestration")
    skills_path = source / "agent-orchestration" / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text())
    data["skills"][0]["companion_assets"] = ["does-not-exist.md"]
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False))
    target = tmp_path / "target"
    with pytest.raises(CodexAdapterMissingCompanionAssetError):
        render_codex_guidance(source, target, allow_outside_contract=True)
    assert not target.exists()
