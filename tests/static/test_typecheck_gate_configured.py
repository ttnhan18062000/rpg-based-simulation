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


def test_typecheck_job_gets_mypy_from_the_lockfile_not_a_separate_pip_install():
    # mypy is in the `dev` dependency group (TCK-20261002-UV-DECLARE-AND-LOCK), so the uv sync
    # step already installs it (TCK-20261002-UV-REMAINING-CI-JOBS removed `pip install mypy`).
    text = (_REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "pip install mypy" not in text
    assert re.search(r'^\s*"mypy",?\s*$', (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE)


# ── TCK-20261003-MYPY-BASELINE-ADVISORY: existing errors live in a baseline, only new ones are reported ──


def test_pyproject_configures_mypy_baseline_with_the_committed_baseline_and_tolerant_syncing():
    import tomllib

    data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    table = data["tool"]["mypy_baseline"]
    assert table["baseline_path"] == "registries/mypy_baseline.txt"
    assert table["allow_unsynced"] is True, "a fixed-but-unsynced error must not fail the gate"
    assert "note" in table["ignore_categories"], "a reworded note alone must not count as a new error"
    assert "mypy-baseline==0.7.4" in data["dependency-groups"]["dev"]
    assert table["sort_baseline"] is True, "a sorted baseline keeps re-sync diffs minimal and byte-comparable"
    baseline = (_REPO_ROOT / table["baseline_path"]).read_text(encoding="utf-8").splitlines()
    assert baseline and all(": error:" in line and ":0:" in line for line in baseline), (
        "entries are errors only, with the line number normalised to 0"
    )
    assert baseline == sorted(baseline), "the committed baseline is sorted (sort_baseline = true)"


def test_makefile_typecheck_py_filters_through_the_baseline_and_stays_advisory():
    text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^typecheck-py:.*\n(\t.*\n)+", text, re.MULTILINE)
    assert match is not None
    assert "mypy_baseline filter" in match.group(0) and match.group(0).rstrip().endswith("|| true")
    sync = re.search(r"^typecheck-baseline-sync:.*\n(\t.*\n)+", text, re.MULTILINE)
    assert sync is not None and "mypy_baseline sync" in sync.group(0)
    assert "Codebase domain only" in sync.group(0).splitlines()[0]


def test_ci_mypy_step_runs_the_advisory_gate_and_is_not_blocking():
    import yaml

    steps = yaml.safe_load((_REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8"))["jobs"]["typecheck"]["steps"]
    step = next(s for s in steps if s.get("name") == "mypy")
    assert "tools.code_health.mypy_gate" in step["run"] and "--annotate" in step["run"]
    assert step["continue-on-error"] is True, "advisory until TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING"
