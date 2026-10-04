"""Layout guards for the codebase domain root (TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE).

`codebase/` owns the Python code-craft tooling (docs/plans/codebase_health/codebase_domain_root.md). These
tests keep the move from being undone by accident and keep the dependency direction one-way:
codebase -> tools is allowed, tools -> codebase is not.
"""

import ast
import importlib
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_MOVED_FLAT_FILES = (
    "tools/codebase_health_baseline.py",
    "tools/codebase_health_snapshot.py",
    "tools/code_health_impact.py",
    "tools/pr_impact_report.py",
    "tools/audit_unreachable_code.py",
)
_MOVED_HOOKS = (
    "tools/hooks/code_health_pre_commit.sh",
    "tools/hooks/uv_lock_pre_commit.sh",
    "tools/hooks/install_git_hooks.py",
)
_MOVED_BASELINES = ("registries/code_health_exceptions.jsonl", "registries/mypy_baseline.txt", ".jscpd.json")
_PACKAGES = ("codebase", "codebase.health", "codebase.gates", "codebase.hooks", "codebase.reports")
_MODULES = (
    "codebase.health.scan", "codebase.health.registry", "codebase.health.ratchet", "codebase.health.metrics",
    "codebase.health.line_count", "codebase.health.adapters", "codebase.health.findings",
    "codebase.gates.mypy_gate", "codebase.gates.sarif_feedback", "codebase.gates.staged_ratchet",
    "codebase.hooks.install_git_hooks",
    "codebase.reports.codebase_health_baseline", "codebase.reports.codebase_health_snapshot",
    "codebase.reports.code_health_impact", "codebase.reports.pr_impact_report",
    "codebase.reports.audit_unreachable_code",
)


def _tracked() -> list[str]:
    done = subprocess.run(["git", "ls-files"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True)
    return done.stdout.splitlines()


def test_the_old_tool_locations_do_not_reappear():
    tracked = _tracked()
    reappeared = [p for p in tracked if p.startswith("tools/code_health/")]
    reappeared += [p for p in (*_MOVED_FLAT_FILES, *_MOVED_HOOKS, *_MOVED_BASELINES) if p in tracked]
    assert not reappeared, f"these belong under codebase/ now (see codebase/README.md): {reappeared}"
    on_disk = [p for p in ("tools/code_health", *_MOVED_FLAT_FILES, *_MOVED_HOOKS) if (_REPO_ROOT / p).is_file()]
    assert not on_disk


def test_codebase_resolves_to_this_repository_and_is_not_shadowed():
    package = importlib.import_module("codebase")
    assert Path(package.__file__).resolve() == _REPO_ROOT / "codebase" / "__init__.py"


@pytest.mark.parametrize("name", _PACKAGES + _MODULES)
def test_every_moved_module_imports_under_its_new_name(name):
    importlib.import_module(name)


def test_the_domain_readme_and_baselines_exist():
    for rel in ("codebase/README.md", "codebase/baselines/code_health_exceptions.jsonl",
                "codebase/baselines/mypy_baseline.txt", "codebase/config/.jscpd.json"):
        assert (_REPO_ROOT / rel).is_file(), rel


def test_nothing_under_tools_imports_codebase():
    """The direction rule as a check: tools/ never depends on the codebase domain root."""
    offenders = []
    for rel in (p for p in _tracked() if p.startswith("tools/") and p.endswith(".py")):
        try:
            tree = ast.parse((_REPO_ROOT / rel).read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module]
            if any(m == "codebase" or m.startswith("codebase.") for m in modules):
                offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, f"tools/ must not import codebase/ (codebase -> tools only): {offenders}"
