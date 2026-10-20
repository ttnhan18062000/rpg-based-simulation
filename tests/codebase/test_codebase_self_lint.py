"""Pin: ``codebase/`` meets the Python code standard it enforces on everyone else (TCK-20261018-CODEBASE-SELF-LINT)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _ruff() -> str:
    beside = Path(sys.executable).parent / "ruff"
    if beside.exists():
        return str(beside)
    pytest.fail("ruff is not installed: run `uv sync` (it is in the `lint` dependency group)")


def test_codebase_package_has_no_ruff_findings() -> None:
    """`ruff check codebase` is clean under the repo's own configuration; the findings are printed on failure."""
    done = subprocess.run(
        [_ruff(), "check", "codebase", "--output-format", "concise", "--no-cache"],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert done.returncode == 0, f"ruff findings in codebase/:\n{done.stdout}{done.stderr}"
