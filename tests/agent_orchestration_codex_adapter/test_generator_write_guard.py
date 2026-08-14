from pathlib import Path
import pytest
import shutil
import yaml
from tools.agent_orchestration_codex_adapter.errors import CodexAdapterWriteGuardError
from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
ROOT=Path(__file__).parent.parent.parent

def test_refuses_external_target_without_flag(tmp_path):
    with pytest.raises(CodexAdapterWriteGuardError): render_codex_guidance(ROOT, tmp_path)
    assert not (tmp_path / "AGENTS.md").exists()

def test_allows_external_target_with_flag(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)
    assert (tmp_path / "AGENTS.md").is_file()

def test_never_targets_dot_claude_or_dot_codex():
    for target in (ROOT / ".claude" / "x", ROOT / ".codex" / "x"):
        with pytest.raises(CodexAdapterWriteGuardError): render_codex_guidance(ROOT, target, allow_outside_contract=True)


def test_rejects_path_traversal_skill_id_before_writing(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(ROOT / "agent-orchestration", source / "agent-orchestration")
    skills_path = source / "agent-orchestration" / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text())
    data["skills"][0]["id"] = "../../etc"
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False))
    target = tmp_path / "target"
    with pytest.raises(CodexAdapterWriteGuardError):
        render_codex_guidance(source, target, allow_outside_contract=True)
    assert not target.exists()


def test_companion_asset_copy_respects_write_guard_and_refuses_traversal(tmp_path):
    # repo_root == target_repo_root here (matching the real regeneration invocation shape,
    # `render_codex_guidance(repo_root, repo_root)`) so a `../`-relative companion_assets entry
    # actually resolves back through the shared root, exercising _assert_write_allowed's
    # resolve-based containment check rather than the unrelated `id`-format regex.
    source = tmp_path / "source"
    shutil.copytree(ROOT / "agent-orchestration", source / "agent-orchestration")
    skills_path = source / "agent-orchestration" / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text())
    data["skills"][0]["companion_assets"] = ["../../../etc/passwd"]
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False))
    with pytest.raises(CodexAdapterWriteGuardError):
        render_codex_guidance(source, source)
    assert not (source / "AGENTS.md").exists()
    assert not (source / ".agents").exists()


def test_companion_asset_copy_refuses_traversal_into_dot_claude(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(ROOT / "agent-orchestration", source / "agent-orchestration")
    skills_path = source / "agent-orchestration" / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text())
    data["skills"][0]["companion_assets"] = ["../../../.claude/skills/agent-monitoring-retro/SKILL.md"]
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False))
    with pytest.raises(CodexAdapterWriteGuardError):
        render_codex_guidance(source, source)
    assert not (source / "AGENTS.md").exists()
    assert not (source / ".agents").exists()
