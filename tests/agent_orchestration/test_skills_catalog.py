"""Tests for agent-orchestration/skills.yaml (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

Verifies the skill catalog validates, has stable/unique/identifier-safe ids traceable to
.claude/skills/*/SKILL.md directories, and that its schema stays structurally distinct from
roles/*.yaml's schema (a role-shaped field bleeding into a skill entry would make the downstream
Codex .agents/skills/ traceability ticket ambiguous about which contract file to trace to).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from agent_orchestration.errors import ContractValidationError
from agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILLS_PATH = _REPO_ROOT / "agent-orchestration" / "skills.yaml"

_ROLE_ONLY_FIELDS = {"role_version", "role_id", "phases", "has_agent_file", "inline_prompt_exception", "obligations", "gates"}

_FOUR_CONFIRMED_SKILLS_COMPANION_ASSETS = {
    "api-design-principles": [
        "assets/api-design-checklist.md",
        "assets/rest-api-template.py",
        "references/graphql-schema-design.md",
        "references/rest-best-practices.md",
        "resources/implementation-playbook.md",
    ],
    "architecture": [
        "context-discovery.md",
        "examples.md",
        "pattern-selection.md",
        "patterns-reference.md",
        "trade-off-analysis.md",
    ],
    "brainstorming": [
        "spec-document-reviewer-prompt.md",
        "visual-companion.md",
        "scripts/frame-template.html",
        "scripts/helper.js",
        "scripts/server.cjs",
        "scripts/start-server.sh",
        "scripts/stop-server.sh",
    ],
    "test-driven-development": ["testing-anti-patterns.md"],
}


def _copy_contract_to(tmp_path: Path) -> Path:
    dest = tmp_path / "agent-orchestration"
    shutil.copytree(_REPO_ROOT / "agent-orchestration", dest)
    return dest


def test_skills_yaml_validates_and_has_stable_ids():
    bundle = load_contract(_REPO_ROOT)
    skills = bundle.skills["skills"]
    assert len(skills) > 0

    ids = [entry["id"] for entry in skills]
    assert len(ids) == len(set(ids)), "skills.yaml has duplicate ids"

    for skill_id in ids:
        assert skill_id.isidentifier() or skill_id.replace("-", "_").isidentifier(), (
            f"skill id {skill_id!r} is not Python-identifier-safe (after hyphen->underscore normalization)"
        )

    skill_dirs = {p.parent.name for p in (_REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    for skill_id in ids:
        assert skill_id in skill_dirs, f"skill id {skill_id!r} has no matching .claude/skills/{skill_id}/SKILL.md"


def test_skills_yaml_does_not_duplicate_role_fields():
    raw = yaml.safe_load(_SKILLS_PATH.read_text(encoding="utf-8"))
    for entry in raw["skills"]:
        overlapping = _ROLE_ONLY_FIELDS & set(entry.keys())
        assert not overlapping, f"skill entry {entry.get('id')!r} has role-shaped field(s): {overlapping}"


def test_companion_assets_field_defaults_to_empty_list_when_omitted(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    skills_path = contract_dir / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text(encoding="utf-8"))
    del data["skills"][0]["companion_assets"]
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    bundle = load_contract(tmp_path)
    assert bundle.skills["skills"][0]["companion_assets"] == []


def test_companion_assets_field_rejects_non_list_value(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    skills_path = contract_dir / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text(encoding="utf-8"))
    data["skills"][0]["companion_assets"] = "not-a-list.md"
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    assert str(skills_path) in str(excinfo.value)
    assert "companion_assets" in str(excinfo.value)


def test_companion_assets_field_rejects_non_string_list_element(tmp_path):
    contract_dir = _copy_contract_to(tmp_path)
    skills_path = contract_dir / "skills.yaml"
    data = yaml.safe_load(skills_path.read_text(encoding="utf-8"))
    data["skills"][0]["companion_assets"] = [1, "ok.md"]
    skills_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        load_contract(tmp_path)
    assert str(skills_path) in str(excinfo.value)
    assert "companion_assets" in str(excinfo.value)


def test_companion_assets_populated_for_the_four_confirmed_skills():
    bundle = load_contract(_REPO_ROOT)
    by_id = {entry["id"]: entry["companion_assets"] for entry in bundle.skills["skills"]}
    for skill_id, expected in _FOUR_CONFIRMED_SKILLS_COMPANION_ASSETS.items():
        assert by_id[skill_id] == expected


def test_companion_assets_empty_for_the_twelve_unaffected_skills():
    bundle = load_contract(_REPO_ROOT)
    for entry in bundle.skills["skills"]:
        if entry["id"] not in _FOUR_CONFIRMED_SKILLS_COMPANION_ASSETS:
            assert entry["companion_assets"] == [], f"{entry['id']!r} should have no companion assets"
