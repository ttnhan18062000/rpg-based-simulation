"""Tests for TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED's bespoke replacement of
backend-testing/SKILL.md and light adaptation of python-testing-patterns,
python-performance-optimization, and debugging-strategies, plus the corresponding
.agents/ Codex-mirror regeneration.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SKILLS_DIR = _REPO_ROOT / ".claude" / "skills"
_MIRROR_DIR = _REPO_ROOT / ".agents" / "skills"

_BACKEND_TESTING_MD = _SKILLS_DIR / "backend-testing" / "SKILL.md"
_PYTHON_TESTING_MD = _SKILLS_DIR / "python-testing-patterns" / "SKILL.md"
_PYTHON_PERF_MD = _SKILLS_DIR / "python-performance-optimization" / "SKILL.md"
_DEBUGGING_MD = _SKILLS_DIR / "debugging-strategies" / "SKILL.md"

_ADAPTED_SKILLS_MIN_LINES = {
    "python-testing-patterns": 1028,
    "python-performance-optimization": 851,
    "debugging-strategies": 527,
}


def _body(text: str) -> str:
    parts = text.split("---", 2)
    assert len(parts) == 3
    return parts[2]


# ---------------------------------------------------------------------------
# backend-testing — bespoke replacement
# ---------------------------------------------------------------------------

def test_backend_testing_has_no_node_express_jest_fingerprint():
    """'Prisma'/'bcrypt' are deliberately excluded from this banned list — the replacement's own
    opening paragraph honestly names them once, in prose describing what was replaced and why.
    These 3 strings are ones that could only appear in actual copy-pasted Node.js test code, not
    in that explanatory sentence."""
    text = _BACKEND_TESTING_MD.read_text(encoding="utf-8")
    for banned in ("jest.config", "Supertest", "supertest", "db.user.findUnique"):
        assert banned not in text, f"stale Node/Express/Jest content still present: {banned!r}"


def test_backend_testing_has_no_dangling_sibling_refs():
    text = _BACKEND_TESTING_MD.read_text(encoding="utf-8")
    assert "../api-design/SKILL.md" not in text
    assert "../authentication/SKILL.md" not in text


def test_backend_testing_cites_real_repo_pattern():
    text = _BACKEND_TESTING_MD.read_text(encoding="utf-8")
    assert "subprocess" in text
    assert "requests" in text
    assert "tests/api/test_rest_parity.py" in text
    assert "ReadModelCache" in text
    assert "test_api_read_model_guard.py" in text


def test_backend_testing_frontmatter_discloses_project_source():
    text = _BACKEND_TESTING_MD.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert "source: project" in frontmatter


# ---------------------------------------------------------------------------
# python-testing-patterns / python-performance-optimization / debugging-strategies — adapt only
# ---------------------------------------------------------------------------

def test_python_testing_patterns_has_in_this_repo_section():
    text = _PYTHON_TESTING_MD.read_text(encoding="utf-8")
    assert "## In This Repo" in text
    assert "test-scoper" in text


def test_python_performance_optimization_has_in_this_repo_section():
    text = _PYTHON_PERF_MD.read_text(encoding="utf-8")
    assert "## In This Repo" in text
    assert "PerfRegressionGate" in text
    assert "DirtySet" in text


def test_debugging_strategies_has_in_this_repo_section():
    text = _DEBUGGING_MD.read_text(encoding="utf-8")
    assert "## In This Repo" in text
    assert "world-debugger" in text


def test_adapted_skills_content_only_grew_not_shrank():
    for skill_id, min_lines in _ADAPTED_SKILLS_MIN_LINES.items():
        path = _SKILLS_DIR / skill_id / "SKILL.md"
        actual_lines = len(path.read_text(encoding="utf-8").splitlines())
        assert actual_lines >= min_lines, (
            f"{skill_id}/SKILL.md shrank from {min_lines} to {actual_lines} lines — "
            "adaptation should be additive only"
        )


# ---------------------------------------------------------------------------
# .agents/ mirror regeneration
# ---------------------------------------------------------------------------

def test_agents_mirror_body_matches_claude_source_for_all_four():
    for skill_id in (
        "backend-testing", "python-testing-patterns",
        "python-performance-optimization", "debugging-strategies",
    ):
        source = _SKILLS_DIR / skill_id / "SKILL.md"
        mirror = _MIRROR_DIR / skill_id / "SKILL.md"
        source_body = _body(source.read_text(encoding="utf-8"))
        mirror_body = _body(mirror.read_text(encoding="utf-8"))
        assert mirror_body == source_body, f"{mirror} drifted from {source}"
