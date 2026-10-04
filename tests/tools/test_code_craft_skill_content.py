"""Tests for .claude/skills/code-craft/SKILL.md (TCK-20261004-CODE-CRAFT-SKILL).

The skill cites rule IDs from docs/guidelines/python_code_standard.md and must not drift from it. It must carry
no counts (they go stale at the next exemplar re-pick).
"""
import re
from pathlib import Path

import yaml

from tools.agent_orchestration_codex_adapter.generator import build_codex_skill_md

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "code-craft" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "code-craft" / "SKILL.md"
_STANDARD = _REPO_ROOT / "docs" / "guidelines" / "python_code_standard.md"
_SKILLS_YAML = _REPO_ROOT / "agent-working" / "agent-orchestration" / "skills.yaml"
_IMPLEMENTER = _REPO_ROOT / ".claude" / "agents" / "implementer.md"

_REVIEWER_RULES = ["F1", "F2", "F4", "F5", "N1", "N4", "D2", "D3", "T2", "T3", "E2", "E3"]
_POINTER = (
    "For Python code, follow `docs/guidelines/python_code_standard.md`; "
    "load the `code-craft` skill for the reviewer rules and examples."
)


def _text() -> str:
    return _SKILL_MD.read_text(encoding="utf-8")


def test_frontmatter_and_precise_trigger():
    parts = _text().split("---", 2)
    assert len(parts) == 3 and "name: code-craft" in parts[1] and "source: project" in parts[1]
    description = next(line for line in parts[1].splitlines() if line.startswith("description:"))
    assert "src/ or tools/" in description and "Not for docs, YAML, config or test-only work" in description


def test_every_reviewer_rule_is_present_and_exists_in_the_standard():
    standard = _STANDARD.read_text(encoding="utf-8")
    for rule in _REVIEWER_RULES:
        assert f"**{rule}" in _text(), f"skill is missing reviewer rule {rule}"
    for rule in set(re.findall(r"\*\*([A-Z]\d)[ *]", _text())):
        assert f"| {rule} |" in standard, f"skill cites {rule}, which is not a row of the standard"


def test_cited_repo_paths_exist():
    for path in re.findall(r"`((?:docs|codebase|tools|src)/[\w./-]+?\.(?:md|py|jsonl))`", _text()):
        assert (_REPO_ROOT / path).is_file(), f"skill cites a missing path: {path}"


def test_workflow_markers_and_the_empty_exemplar_rule():
    text = _text()
    for marker in ("package_registry.jsonl", "exemplar_modules", "do_not_imitate", "make code-health",
                   "edit_ratchet_hook", "Section 11", "Important", "Nit", "Pre-existing"):
        assert marker in text, f"missing: {marker}"
    assert "When it is empty, follow the standard" in text


def test_skill_carries_no_counts_that_go_stale():
    assert not re.search(r"\b\d+ of \d+\b|\b\d+ packages\b", _text())


def test_e3_example_does_not_call_handling_a_swallow():
    text = _text()
    assert "except KeyError: return default` is a decision, not a swallow" in text
    assert "`except Exception: return None`, with no log" in text


def test_codex_mirror_is_the_generated_one():
    skills = yaml.safe_load(_SKILLS_YAML.read_text(encoding="utf-8"))["skills"]
    entry = next(s for s in skills if s["id"] == "code-craft")
    assert _MIRROR_MD.read_text(encoding="utf-8") == build_codex_skill_md(_REPO_ROOT, "code-craft", entry["description"])


def test_implementer_points_at_the_standard_once_under_code_quality_rules():
    text = _IMPLEMENTER.read_text(encoding="utf-8")
    assert text.count(_POINTER) == 1
    section = text.split("## Code Quality Rules", 1)[1].split("\n## ", 1)[0]
    assert _POINTER in section


def test_skill_is_listed_in_the_skills_doc():
    assert "`/code-craft`" in (_REPO_ROOT / "docs" / "ai" / "skills.md").read_text(encoding="utf-8")
