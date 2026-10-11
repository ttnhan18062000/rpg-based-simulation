"""TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW: the gate reused for a second workflow, the rolling issue, the plan, the absent-module banner, shards."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from tools.test_architecture import rpg_gate_harness as harness
from tools.test_architecture import rpg_gate_issue as issue
from tools.test_architecture import rpg_gate_plan as plan
from tools.test_architecture import rpg_gate_report as rep
from tools.test_architecture import slow_regression_gate as gate
from tools.test_architecture.rpg_gate_baseline import GateConfig, load_config

NOW = dt.datetime(2026, 10, 12, 12, tzinfo=dt.timezone.utc)
HEAD = "a" * 40


# ---- the #464 gate, parameterised

def _run(run_id, hours_ago, **kw):
    created = (NOW - dt.timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"databaseId": run_id, "status": "completed", "createdAt": created, "headBranch": "main", "headSha": HEAD, **kw}


def test_collect_looks_at_the_given_workflow_and_suite_job():
    seen = {}

    def list_runs():
        return [_run(1, 3)]

    def view_jobs(run_id):
        return [{"name": "RPG gate report", "conclusion": "success"}, {"name": "Slow regression", "conclusion": "skipped"}]

    runs = gate.collect(HEAD, list_runs, view_jobs, workflow="rpg-gate-report.yml", suite_job="RPG gate report")
    assert runs[0]["tested"] is True
    assert gate.decide(HEAD, runs, NOW)[0] == gate.SKIP  # tested 3 h ago
    default = gate.collect(HEAD, list_runs, view_jobs)  # the slow suite's job is skipped in that run: not tested
    assert default[0]["tested"] is False and gate.decide(HEAD, default, NOW)[0] == gate.RUN
    assert gate.actually_tested(_run(1, 3), [{"name": "X", "conclusion": "failure"}], "X")


def test_collect_passes_the_workflow_file_to_gh(monkeypatch):
    calls = []
    monkeypatch.setattr(gate, "_gh_json", lambda args: calls.append(args) or [])
    gate.collect(HEAD, workflow="rpg-gate-report.yml")
    assert calls[0][calls[0].index("--workflow") + 1] == "rpg-gate-report.yml"
    gate.collect(HEAD)
    assert calls[1][calls[1].index("--workflow") + 1] == "slow-regression.yml"


# ---- the plan

def test_plan_without_a_config_says_so_and_still_gives_a_one_value_matrix(tmp_path):
    result = plan.plan(tmp_path / "missing.yaml")
    assert result["have_config"] is False and "does not exist yet" in result["message"] and json.loads(result["matrix"]) == {"world": ["none"]}


def test_plan_reads_the_worlds_from_the_config_and_reports_an_invalid_one(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("worlds: [a, b]\nseeds: [1, 2, 3]\nticks: 100\nstale_after_days: 30\n")
    result = plan.plan(cfg)
    assert result["have_config"] and json.loads(result["matrix"]) == {"world": ["a", "b"]} and "2 world(s) x 3 seed(s) x 100 ticks" in result["message"]
    cfg.write_text("worlds: [a]\n")
    bad = plan.plan(cfg)
    assert not bad["have_config"] and "invalid" in bad["message"]


def test_plan_cli_prints_github_output_lines(tmp_path, capsys):
    assert plan.main(["--config", str(tmp_path / "none.yaml")]) == 0
    out = capsys.readouterr().out
    assert "have_config=false" in out and "matrix=" in out


# ---- shards

def test_only_world_restricts_the_run_to_that_world(tmp_path, monkeypatch):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("worlds: [a, b]\nseeds: [1]\nticks: 5\nstale_after_days: 30\n")
    seen = {}
    monkeypatch.setattr(harness, "run_matrix", lambda config, *a, **kw: seen.update(worlds=config.worlds) or {"runs": [], "wall_seconds": 0})
    assert harness.main(["--config", str(cfg), "--out", str(tmp_path / "o"), "--only-world", "b", "--sha", "x"]) == 0
    assert seen["worlds"] == ("b",)
    with pytest.raises(SystemExit):
        harness.main(["--config", str(cfg), "--out", str(tmp_path / "o"), "--only-world", "zzz", "--sha", "x"])


# ---- the absent module banner

def _no_module_report():
    config = GateConfig(("w",), (1, 2), 10, 30)
    err = "ModuleNotFoundError: No module named 'src.observability.rpg_gate_metrics'"
    docs = {("w", s): {"schema": "rpg-gate-metrics/v1", "status": "no-data", "reason": "metric_error", "error": err, "metrics": []} for s in (1, 2)}
    docs[("w", None)] = {"schema": "rpg-gate-metrics/v1", "status": "no-data", "reason": "seed_no_data", "error": "no pool", "metrics": []}
    return rep.build_report(config, docs, None, {}, [], dt.date(2026, 10, 12), sha="s" * 40, harness_hash="h")


def test_a_missing_metric_module_is_green_and_the_summary_says_so_plainly():
    report = _no_module_report()
    assert report["verdict"] == "green" and report["module_absent"] is True and report["counts"]["no-data"] == 3
    md = rep.render_markdown(report)
    assert "rpg's metric module is absent" in md and "judges nothing yet" in md
    assert not report["run_errors"]


def test_a_metric_error_that_is_not_a_missing_module_does_not_claim_the_module_is_absent():
    report = _no_module_report()
    for f in report["findings"]:
        f["detail"] = "RuntimeError: boom"
    assert rep.build_report(GateConfig(("w",), (1,), 10, 30), {("w", 1): {"status": "no-data", "reason": "metric_error", "error": "RuntimeError: boom", "metrics": []}}, None, {}, [], dt.date(2026, 10, 12))["module_absent"] is False


# ---- the rolling issue

class FakeClient:
    def __init__(self, issues=()):
        self.issues = list(issues)
        self.calls = []

    def list_issues(self):
        return self.issues

    def create_issue(self, title, body):
        self.calls.append(("create", title))
        self.issues = [{"number": 7, "body": body, "user_login": issue.BOT_LOGIN, "labels": [issue.LABEL]}]

    def update_issue(self, number, title, body):
        self.calls.append(("update", title))
        self.issues[0]["body"] = body

    def comment(self, number, text):
        self.calls.append(("comment", text))

    def close_issue(self, number):
        self.calls.append(("close", number))


def _finding(rid, state, world="w", seed=None, **extra):
    return {"id": rid, "group": "*", "world": world, "scope": "run", "class": "validity", "state": state, "violations": 1 if state == "fail" else 0,
            **({"seed": seed} if seed is not None else {}), **extra}


def _report(findings, module_absent=False):
    return {"verdict": "green", "reasons": [], "counts": {s: 0 for s in rep.STATES}, "references": [], "rerun": {"performed": False}, "run_errors": [],
            "no_data_reasons": {}, "sha": "s" * 40, "harness_hash": "h" * 12, "findings": findings, "module_absent": module_absent}


def test_the_label_is_its_own_not_the_slow_reports():
    assert issue.LABEL == "rpg-gate-report" and issue.LABEL != "slow-regression" and issue.TRACKER_MARKER != "<!-- slow-regression-tracker -->"


def test_first_run_creates_the_issue_then_an_unchanged_set_only_refreshes_then_new_and_resolved_comment_then_empty_closes():
    client = FakeClient()
    assert "nothing to do" in issue.run_issue(client, _report([_finding("V1", "pass")]), "1", "s", "o/r") and not client.calls
    first = issue.run_issue(client, _report([_finding("V1", "fail", seed=1)]), "2", "s", "o/r")
    assert "created" in first and [c[0] for c in client.calls] == ["create"]
    client.calls.clear()
    assert "unchanged" in issue.run_issue(client, _report([_finding("V1", "fail", seed=1)]), "3", "s", "o/r") and [c[0] for c in client.calls] == ["update"]
    client.calls.clear()
    issue.run_issue(client, _report([_finding("V1", "fail", seed=1), _finding("O1", "drift")]), "4", "s", "o/r")
    text = next(c[1] for c in client.calls if c[0] == "comment")
    assert text.startswith("NEW: `O1 [w]` (drift)") and "RESOLVED" not in text
    client.calls.clear()
    issue.run_issue(client, _report([_finding("O1", "drift")]), "5", "s", "o/r")
    assert "RESOLVED: `V1 [w/1]`" in next(c[1] for c in client.calls if c[0] == "comment")
    client.calls.clear()
    assert "closed" in issue.run_issue(client, _report([]), "6", "s", "o/r") and ("close", 7) in client.calls


def test_a_module_absent_report_creates_an_issue_that_says_so_and_a_run_error_is_tracked():
    client = FakeClient()
    issue.run_issue(client, _report([_finding("*", "no-data", reason="metric_error")], module_absent=True), "1", "s", "o/r")
    body = client.issues[0]["body"]
    assert issue.MODULE_ABSENT_ID in issue.parse_state(body) and issue.TRACKER_MARKER in body
    assert issue.tracked(_report([_finding("*", "no-data", reason="run_error", seed=2)])) == {"run_error w/2": "run_error"}


def test_two_marked_issues_are_an_error_and_an_unreadable_state_block_refreshes_without_comments():
    marked = {"number": 1, "body": issue.TRACKER_MARKER, "user_login": issue.BOT_LOGIN, "labels": [issue.LABEL]}
    with pytest.raises(Exception, match="more than one"):
        issue.select_tracker([marked, {**marked, "number": 2}])
    client = FakeClient([marked])
    assert "unreadable" in issue.run_issue(client, _report([_finding("V1", "fail")]), "1", "s", "o/r") and [c[0] for c in client.calls] == ["update"]


def test_main_wires_a_client_and_prints_what_was_done(tmp_path, capsys):
    path = tmp_path / "r.json"
    path.write_text(json.dumps(_report([_finding("V1", "fail")])))
    client = FakeClient()
    assert issue.main(["--report", str(path), "--repo", "o/r", "--run-id", "9", "--sha", "s"], client_factory=lambda repo: client) == 0
    assert "created" in capsys.readouterr().out and client.calls
