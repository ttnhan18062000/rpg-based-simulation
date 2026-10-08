import tomllib
from pathlib import Path

# torch's CPU-only wheel (`torch==...+cpu`) is not resolvable from public PyPI without an extra index URL,
# and every CI job runs `uv sync --locked`. If any of these packages reached the *default* install (the
# project's runtime dependencies plus the default dependency groups), every CI job would fail at the install
# step before any test runs (see TCK-20260702-CI-REQUIREMENTS-SPLIT). They are allowed in `uv.lock` only
# behind an opt-in extra (`knowledge`, `search-mcp`) or group. This used to assert on `requirements.txt`, a
# `uv export` of the lock that was removed by TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT; it now walks the
# lock's dependency graph from the same roots a plain `uv sync` installs.
FORBIDDEN_PACKAGES = ["torch", "sentence-transformers", "sqlite-vec", "rank-bm25"]

_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT = "rpg-based-simulation"


def _default_install_closure() -> set[str]:
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((_ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = {pkg["name"]: pkg for pkg in lock["package"]}
    root = packages[_PROJECT]
    default_groups = pyproject["tool"]["uv"]["default-groups"]
    pending = [dep["name"] for dep in root.get("dependencies", [])]
    for group in default_groups:
        pending += [dep["name"] for dep in root.get("dev-dependencies", {}).get(group, [])]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending += [dep["name"] for dep in packages.get(name, {}).get("dependencies", [])]
    return seen


def test_default_install_excludes_knowledge_search_stack():
    closure = _default_install_closure()
    assert closure, "the default install closure is empty: the lock walk found no root dependencies"
    violations = sorted(set(FORBIDDEN_PACKAGES) & closure)
    assert not violations, (
        "the default `uv sync` (runtime dependencies + default dependency groups) must not pull in the "
        "knowledge-search ML stack (it belongs behind the opt-in `knowledge` extra and "
        f"requirements-knowledge.txt, local agent tooling only): {violations}"
    )


def test_requirements_knowledge_txt_exists_and_has_the_stack():
    requirements_knowledge_path = _ROOT / "requirements-knowledge.txt"

    assert requirements_knowledge_path.exists(), (
        "requirements-knowledge.txt should hold the knowledge-search ML stack "
        "(torch, sentence-transformers, sqlite-vec, rank-bm25)"
    )

    content = requirements_knowledge_path.read_text(encoding="utf-8").lower()
    for package in FORBIDDEN_PACKAGES:
        assert package in content, f"requirements-knowledge.txt is missing '{package}'"
