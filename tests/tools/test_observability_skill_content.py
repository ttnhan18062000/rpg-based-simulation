"""Tests for the new .claude/skills/observability/SKILL.md (TCK-20260805-OBSERVABILITY-SKILL),
sourced from docs/observability/hard_law_monitor.md and
docs/architecture/observability_hot_path_safety_contract.md.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILL_MD = _REPO_ROOT / ".claude" / "skills" / "observability" / "SKILL.md"
_MIRROR_MD = _REPO_ROOT / ".agents" / "skills" / "observability" / "SKILL.md"
_SKILLS_DOC = _REPO_ROOT / "docs" / "ai" / "skills.md"

_REAL_LAW_IDS = [
    "LAW-HP-NONNEGATIVE", "LAW-READINESS-NONNEGATIVE", "LAW-GOLD-NONNEGATIVE",
    "LAW-STAMINA-NONNEGATIVE", "LAW-POSITION-FINITE", "LAW-OCCUPANCY-COLLISION",
    "LAW-SPAWN-OCCUPANCY",
]
_REAL_OBSERVABILITY_MODES = ["OFF", "LIGHT", "DEBUG", "CERTIFICATION", "LONG_RUN"]
_REAL_BACKPRESSURE_MODES = ["NORMAL", "PRESSURE", "DEGRADED", "SURVIVAL"]


def test_skill_file_exists_with_valid_frontmatter():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    parts = text.split("---", 2)
    assert len(parts) == 3
    assert "name: observability" in parts[1]


def test_contains_all_seven_real_hard_laws():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for law_id in _REAL_LAW_IDS:
        assert law_id in text, f"missing real Law ID: {law_id}"


def test_contains_all_observability_modes_including_the_long_run_gap():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for mode in _REAL_OBSERVABILITY_MODES:
        assert mode in text, f"missing ObservabilityMode: {mode}"
    # The LONG_RUN fall-through gap must be disclosed, not silently omitted.
    assert "falls through" in text or "fall-through" in text or "fall through" in text


def test_contains_all_backpressure_modes():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for mode in _REAL_BACKPRESSURE_MODES:
        assert mode in text, f"missing backpressure mode: {mode}"


def test_cites_kernel_and_dirtyset_docs():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "docs/engine/kernel.md" in text
    assert "docs/core/dirty_state_and_dependency.md" in text


def test_cites_real_test_paths():
    text = _SKILL_MD.read_text(encoding="utf-8")
    for path in (
        "tests/engine/test_hard_law_monitor.py",
        "tests/perf/test_hard_law_monitor_overhead.py",
    ):
        assert path in text
        assert (_REPO_ROOT / path).is_file(), f"cited test path does not actually exist: {path}"


def test_docs_ai_skills_md_lists_the_new_skill():
    text = _SKILLS_DOC.read_text(encoding="utf-8")
    assert "/observability" in text
    assert "observability/SKILL.md" in text


def test_agents_mirror_body_matches_claude_source():
    source_body = _SKILL_MD.read_text(encoding="utf-8").split("---", 2)[2]
    mirror_body = _MIRROR_MD.read_text(encoding="utf-8").split("---", 2)[2]
    assert mirror_body == source_body
