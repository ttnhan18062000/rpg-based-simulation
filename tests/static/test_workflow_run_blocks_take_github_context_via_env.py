"""Static guard for TCK-20261019-TEST-WORKFLOWS-GITHUB-CONTEXT-VIA-ENV-NOT-RUN.

A `${{ github.* }}` or `${{ inputs.* }}` expression inside a `run:` block is substituted into the shell script text before the shell sees it, so a value an
attacker controls (a head_ref, a title) becomes code. Testing's workflows pass such values to the script through the step's `env:` and use `"${VAR}"` in the
script. Expressions in `name:`, `if:`, `concurrency:`, `with:` and `env:` are not shell and stay. This reads the YAML, so a multi-line `run:` is covered.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOWS = _ROOT / ".github" / "workflows"
FILES = sorted([_WORKFLOWS / "test.yml", *_WORKFLOWS.glob("slow-regression*.yml"), _WORKFLOWS / "rpg-gate-report.yml", _WORKFLOWS / "paired-arms.yml"])
CONTEXT = re.compile(r"\$\{\{\s*(?:github|inputs)\.")


def offending_steps(workflow_text: str) -> list[tuple[str, str]]:
    """``(job, step name)`` of each step whose ``run:`` interpolates a github or inputs expression."""
    jobs = (yaml.safe_load(workflow_text) or {}).get("jobs", {})
    return [(job, step.get("name") or step.get("id") or "?") for job, body in jobs.items() for step in body.get("steps", []) if CONTEXT.search(str(step.get("run", "")))]


def test_the_guarded_workflow_files_exist():
    assert {p.name for p in FILES} >= {"test.yml", "slow-regression.yml", "slow-regression-watchdog.yml", "rpg-gate-report.yml", "paired-arms.yml"}


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_run_block_interpolates_github_or_inputs_context(path):
    assert offending_steps(path.read_text(encoding="utf-8")) == [], f"{path.name}: pass the value through the step's env: and use \"${{VAR}}\" in the script"


def test_the_guard_flags_an_interpolated_run_block_and_accepts_the_env_form():
    bad = "jobs:\n  j:\n    steps:\n      - name: fetch\n        run: |\n          git fetch origin \"${{ github.head_ref }}\"\n"
    assert offending_steps(bad) == [("j", "fetch")]
    inputs = "jobs:\n  j:\n    steps:\n      - name: x\n        run: echo ${{ inputs.ref }}\n"
    assert offending_steps(inputs) == [("j", "x")]
    good = "jobs:\n  j:\n    steps:\n      - name: fetch\n        if: github.event_name == 'pull_request'\n        env:\n          HEAD_REF: ${{ github.head_ref }}\n        run: |\n          git fetch origin \"${HEAD_REF}\"\n"
    assert offending_steps(good) == []
