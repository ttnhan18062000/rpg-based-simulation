"""Tests for agent-orchestration/skills.yaml (TCK-20260721-ORCHESTRATION-CONTRACT-CORE).

Verifies the skill catalog validates, has stable/unique/identifier-safe ids traceable to
.claude/skills/*/SKILL.md directories, and that its schema stays structurally distinct from
roles/*.yaml's schema (a role-shaped field bleeding into a skill entry would make the downstream
Codex .agents/skills/ traceability ticket ambiguous about which contract file to trace to).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from agent_orchestration.loader import load_contract

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILLS_PATH = _REPO_ROOT / "agent-orchestration" / "skills.yaml"

_ROLE_ONLY_FIELDS = {"role_version", "role_id", "phases", "has_agent_file", "inline_prompt_exception", "obligations", "gates"}


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
