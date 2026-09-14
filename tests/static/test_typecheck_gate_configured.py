"""Static config assertions backing parity ledger entry INFRA-TYPE-001
(TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL): the mypy type-checking gate.

INFRA-TYPE-001's real evidence is a build/lint gate configuration (pyproject.toml's [tool.mypy]
section, a Makefile target, a CI step), not a pytest citation at all -- the parity ledger schema
has no field for "this claim's evidence is a non-pytest gate check". Confirmed via a corpus-wide
grep (docs/parity_ledger/*.yaml) that this shape is a genuine one-off, not shared by any other
entry -- so a real schema/parser change would be disproportionate infrastructure for one entry.
This small static test file gives the entry a real, citable pytest node-id instead, pinning the
three facts its `text`/`v2_evidence` fields already claim.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_pyproject_declares_tool_mypy_section():
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.mypy]" in text


def test_makefile_typecheck_py_target_runs_mypy_on_src():
    text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^typecheck-py:.*\n(\t.*\n)+", text, re.MULTILINE)
    assert match is not None, "typecheck-py target not found in Makefile"
    assert "mypy src/" in match.group(0)
    assert "pyproject.toml" in match.group(0)


def test_ci_workflow_has_a_mypy_step():
    text = (_REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert re.search(r"name:\s*mypy", text) is not None
    assert "mypy src/" in text
