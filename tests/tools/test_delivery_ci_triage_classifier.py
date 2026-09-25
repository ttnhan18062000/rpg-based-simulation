"""Tests for tools/delivery/ci_triage_classifier.py (TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-CI-TRIAGE-
CLASSIFIER/test_plan.md.
"""
import subprocess
from pathlib import Path

import pytest

from tools.delivery import ci_triage_classifier as classifier
from tools.delivery.pr_status import CommandResult


SOFT_MONITOR_POLICY = """\
## 1. What Is a Regression?

prose

## 3. Soft Monitors — Alert Only

| Test Group | Location | Reason |
|---|---|---|
| Live observability | `tests/api/test_live_health_api.py` | flaky |

## 4. Next section
prose
"""

WORKFLOW_YAML = """\
name: Tests
on:
  pull_request: {}
jobs:
  unit_core_world:
    name: "Unit · core / world"
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements.txt
      - name: Run
        run: |
          pytest tests/unit/core tests/unit/kernel
  api_tests:
    name: "API"
    runs-on: ubuntu-latest
    steps:
      - name: Run
        run: pytest tests/api/test_live_health_api.py
"""


class FakeRunner:
    def __init__(self, rules):
        self.rules = rules
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"no rule matched {cmd!r}")


def _diff_rule(changed_files):
    return (lambda cmd: cmd[:2] == ["git", "diff"], CommandResult(0, "\n".join(changed_files) + "\n", ""))


def _write_fixtures(tmp_path, policy_text=SOFT_MONITOR_POLICY, workflow_text=WORKFLOW_YAML):
    policy_path = tmp_path / "regression_policy.md"
    policy_path.write_text(policy_text, encoding="utf-8")
    workflow_path = tmp_path / "test.yml"
    workflow_path.write_text(workflow_text, encoding="utf-8")
    return policy_path, workflow_path


# ---------------------------------------------------------------------------
# AC1 — documented flake
# ---------------------------------------------------------------------------

def test_documented_flake_classification(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "API", "steps": [{"name": "Run", "conclusion": "failure"}]}],
    }
    runner = FakeRunner([_diff_rule([])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result["category"] == classifier.DOCUMENTED_FLAKE
    assert "not code-fix" in result["remedy"]


# ---------------------------------------------------------------------------
# AC2 — real regression
# ---------------------------------------------------------------------------

def test_real_regression_classification(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "Unit · core / world", "steps": []}],
    }
    runner = FakeRunner([_diff_rule(["tests/unit/core/test_something.py"])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result["category"] == classifier.REAL_REGRESSION
    assert "hotfix ticket" in result["remedy"]


# ---------------------------------------------------------------------------
# AC3 — baseline drift
# ---------------------------------------------------------------------------

def test_baseline_drift_classification(tmp_path):
    workflow_text = """\
jobs:
  baseline_job:
    name: "Baseline"
    steps:
      - run: pytest tests/tools/test_parity_index_baseline.py
"""
    policy_path, workflow_path = _write_fixtures(tmp_path, workflow_text=workflow_text)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "Baseline", "steps": []}],
    }
    runner = FakeRunner([_diff_rule([])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result["category"] == classifier.BASELINE_DRIFT
    assert "never a silent edit" in result["remedy"]


# ---------------------------------------------------------------------------
# AC4 — absent + conflicting
# ---------------------------------------------------------------------------

def test_absent_conflicting_classification():
    payload = {"verdict": "ABSENT", "reason": "PR is CONFLICTING and this workflow's 'on:' block..."}
    result = classifier.classify(payload)
    assert result["category"] == classifier.ENVIRONMENT
    assert "resolve the merge conflict" in result["remedy"]
    assert "will NOT help" in result["remedy"]


def test_absent_generic_classification():
    payload = {"verdict": "ABSENT", "reason": "no known cause applies"}
    result = classifier.classify(payload)
    assert result["category"] == classifier.ENVIRONMENT
    assert "Investigate the specific reason" in result["remedy"]


# ---------------------------------------------------------------------------
# AC5 — unclassified
# ---------------------------------------------------------------------------

def test_unclassified_when_no_signal_matches(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "Some Unmapped Job", "steps": []}],
    }
    runner = FakeRunner([_diff_rule(["unrelated/file.py"])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result["category"] == classifier.UNCLASSIFIED


def test_unclassified_when_jobs_disagree(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [
            {"job_name": "API", "steps": []},
            {"job_name": "Unit · core / world", "steps": []},
        ],
    }
    runner = FakeRunner([_diff_rule(["tests/unit/core/test_x.py"])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result["category"] == classifier.UNCLASSIFIED
    assert "do not agree" in result["remedy"]


# ---------------------------------------------------------------------------
# AC6 — reads policy file at runtime
# ---------------------------------------------------------------------------

def test_classification_changes_when_policy_file_changes(tmp_path):
    _, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "API", "steps": []}],
    }
    runner = FakeRunner([_diff_rule(["tests/api/test_live_health_api.py"])])

    policy_with_entry = tmp_path / "policy_with.md"
    policy_with_entry.write_text(SOFT_MONITOR_POLICY, encoding="utf-8")
    result_with = classifier.classify(
        payload, run_command=runner, policy_path=policy_with_entry, workflow_path=workflow_path,
    )
    assert result_with["category"] == classifier.DOCUMENTED_FLAKE

    policy_without_entry = tmp_path / "policy_without.md"
    policy_without_entry.write_text("## 3. Soft Monitors — Alert Only\n\nnothing here\n\n## 4. x\n", encoding="utf-8")
    runner2 = FakeRunner([_diff_rule(["tests/api/test_live_health_api.py"])])
    result_without = classifier.classify(
        payload, run_command=runner2, policy_path=policy_without_entry, workflow_path=workflow_path,
    )
    assert result_without["category"] == classifier.REAL_REGRESSION


# ---------------------------------------------------------------------------
# AC7 — no write side effect
# ---------------------------------------------------------------------------

def test_no_write_side_effect(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {"verdict": "FAILING", "failing_jobs": [{"job_name": "API", "steps": []}]}
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    runner = FakeRunner([_diff_rule([])])
    classifier.classify(payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path)
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert before == after


# ---------------------------------------------------------------------------
# AC8 — exit code zero for every classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", [
    {"verdict": "ABSENT", "reason": "CONFLICTING"},
    {"verdict": "UNKNOWN", "reason": "network error"},
    {"verdict": "GREEN", "reason": "all good"},
])
def test_exit_code_zero_via_cli(payload, tmp_path, monkeypatch, capsys):
    import json as json_module
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json_module.dumps(payload), encoding="utf-8")
    exit_code = classifier.main(["--payload-file", str(payload_file), "--json"])
    assert exit_code == 0


def test_exit_code_nonzero_only_on_internal_error(tmp_path):
    bad_payload_file = tmp_path / "bad.json"
    bad_payload_file.write_text("not json", encoding="utf-8")
    exit_code = classifier.main(["--payload-file", str(bad_payload_file)])
    assert exit_code == 1


# ---------------------------------------------------------------------------
# Regression-prone paths
# ---------------------------------------------------------------------------

def test_unknown_with_tls_reason_is_environment():
    payload = {"verdict": "UNKNOWN", "reason": "looks like a network/TLS block (matched 'certificate')"}
    result = classifier.classify(payload)
    assert result["category"] == classifier.ENVIRONMENT


def test_unknown_without_tls_reason_is_unclassified():
    payload = {"verdict": "UNKNOWN", "reason": "stale SHA, no current-head run found"}
    result = classifier.classify(payload)
    assert result["category"] == classifier.UNCLASSIFIED


def test_parked_slow_regression_job_flagged_not_new(tmp_path):
    policy_path, workflow_path = _write_fixtures(tmp_path)
    payload = {
        "verdict": "FAILING",
        "failing_jobs": [{"job_name": "Slow regression", "steps": []}],
    }
    runner = FakeRunner([_diff_rule([])])
    result = classifier.classify(
        payload, run_command=runner, policy_path=policy_path, workflow_path=workflow_path,
    )
    assert result.get("parked") is True
    assert "not a new finding" in result["note"]
