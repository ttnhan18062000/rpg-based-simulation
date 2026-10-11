"""TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE: the slow report's output on a recorded JUnit fixture is byte-identical.

The expected file was captured from `slow_regression_report` BEFORE the known-reds schema, matcher and lint moved to
`known_reds.py`. A refactor that changes any title, body, comment, update or close for these inputs fails here. Regenerate the
expected file only for a deliberate change of the report's output, never to make a refactor pass:
`REGEN_SLOW_REPORT_GOLDEN=1 pytest tests/unit/tools/test_slow_regression_report_golden.py`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from tools.test_architecture import slow_regression_report as srr

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures" / "slow_report_golden"
EXPECTED = GOLDEN / "expected.json"
NOW = dt.datetime(2026, 10, 9, 12, 0, tzinfo=dt.timezone.utc)
TODAY = NOW.date()
KW = dict(repo="o/r", run_id="111", sha="a" * 40, today=TODAY, now=NOW)


class RecordingClient:
    def __init__(self, issues=None, comment_bodies=None):
        self.issues = issues or []
        self.comment_bodies = comment_bodies or []
        self.calls: list = []

    def list_issues(self):
        return self.issues

    def list_comment_bodies(self, number):
        return self.comment_bodies

    def create_issue(self, title, body):
        self.calls.append(["create_issue", title, body])

    def update_issue(self, number, title, body):
        self.calls.append(["update_issue", number, title, body])

    def comment(self, number, text):
        self.calls.append(["comment", number, text])

    def close_issue(self, number):
        self.calls.append(["close_issue", number])


def _tracker(body, number=7):
    return {"number": number, "body": body, "user_login": srr.BOT_LOGIN, "labels": [srr.LABEL], "created_at": "2026-10-01T01:00:00+00:00"}


def _scenario(client):
    failing, seen, measured = srr.parse_junit_dir(GOLDEN / "junit")
    known = srr.load_known_reds(GOLDEN / "known_reds.yaml")
    lint = srr.lint_known_reds(known)
    result = srr.run_report(client, failing, seen, known, unmeasured=set(), **KW)
    return {
        "failing": dict(sorted(failing.items())),
        "seen": sorted(seen),
        "measured": sorted(measured),
        "lint": lint,
        "message": result.message,
        "reasons": result.reasons,
        "warnings": result.warnings,
        "exit_code": result.exit_code,
        "calls": client.calls,
    }


def _run_all() -> dict:
    out = {"first_run_no_tracker": _scenario(RecordingClient())}
    # Take the tracker body the first run wrote, then replay it with the same set and with a changed set.
    first_body = out["first_run_no_tracker"]["calls"][0][2]
    out["unchanged_set_digest_not_yet_posted"] = _scenario(RecordingClient(issues=[_tracker(first_body)], comment_bodies=[]))
    prior = srr.parse_state(first_body)
    prior["failing"]["tests.regression.test_gone::test_fixed"] = "slow tests"  # FIXED this run
    prior["failing"].pop("tests.unknown.test_new::test_c")  # NEW this run
    stale_body = srr.render_body(prior["failing"], srr.load_known_reds(GOLDEN / "known_reds.yaml"), "o/r", "100", "b" * 40, prior["first_seen"], TODAY)
    out["new_and_fixed_and_digest"] = _scenario(RecordingClient(issues=[_tracker(stale_body)], comment_bodies=[]))
    out["unchanged_set_digest_already_posted"] = _scenario(
        RecordingClient(issues=[_tracker(first_body)], comment_bodies=[srr.DIGEST_MARKER_FMT.format(week=srr._week_key(TODAY))])
    )
    return out


def test_slow_report_output_on_the_recorded_junit_fixture_is_byte_identical():
    actual = json.dumps(_run_all(), indent=1, sort_keys=True) + "\n"
    if os.environ.get("REGEN_SLOW_REPORT_GOLDEN"):
        EXPECTED.write_text(actual, encoding="utf-8")
    assert EXPECTED.exists(), "golden file missing"
    assert actual == EXPECTED.read_text(encoding="utf-8")


def test_the_fixture_covers_the_interesting_verdicts():
    scenario = _run_all()["first_run_no_tracker"]
    assert scenario["exit_code"] == 1  # UNOWNED and EXPIRED reds
    assert any("UNOWNED" in r for r in scenario["reasons"]) and any("EXPIRED" in r for r in scenario["reasons"])
    assert "legacy regression" not in "".join(scenario["reasons"])
