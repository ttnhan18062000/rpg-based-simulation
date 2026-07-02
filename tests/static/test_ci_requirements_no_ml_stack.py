from pathlib import Path

# torch's CPU-only wheel (`torch==...+cpu`) is not resolvable from public PyPI without
# an extra index URL, and .github/workflows/test.yml installs requirements.txt with plain
# `pip install -r requirements.txt`. If any of these packages reappear in requirements.txt,
# every CI job fails at the install step before any test runs (see TCK-20260702-CI-REQUIREMENTS-SPLIT).
FORBIDDEN_PACKAGES = ["torch", "sentence-transformers", "sqlite-vec", "rank-bm25"]


def test_requirements_txt_excludes_knowledge_search_stack():
    root_dir = Path(__file__).resolve().parent.parent.parent
    requirements_path = root_dir / "requirements.txt"

    lines = requirements_path.read_text(encoding="utf-8").splitlines()
    violations = []
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        package_name = stripped.split("==")[0].strip().lower()
        if package_name in FORBIDDEN_PACKAGES:
            violations.append(f"requirements.txt:{line_num} -> '{stripped}'")

    assert not violations, (
        "requirements.txt must not contain the knowledge-search ML stack "
        "(it belongs in requirements-knowledge.txt, local agent tooling only):\n"
        + "\n".join(violations)
    )


def test_requirements_knowledge_txt_exists_and_has_the_stack():
    root_dir = Path(__file__).resolve().parent.parent.parent
    requirements_knowledge_path = root_dir / "requirements-knowledge.txt"

    assert requirements_knowledge_path.exists(), (
        "requirements-knowledge.txt should hold the knowledge-search ML stack "
        "(torch, sentence-transformers, sqlite-vec, rank-bm25)"
    )

    content = requirements_knowledge_path.read_text(encoding="utf-8").lower()
    for package in FORBIDDEN_PACKAGES:
        assert package in content, f"requirements-knowledge.txt is missing '{package}'"
