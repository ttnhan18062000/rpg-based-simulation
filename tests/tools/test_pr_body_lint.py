"""Tests for tools/delivery/pr_body_lint.py and its wiring (TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED)."""
import json
from pathlib import Path

import yaml

from tools.delivery import pr_body_lint, pr_render
from tools.delivery.pr_status import CommandResult
from tests.tools.test_delivery_pr_render import (
    FakeRunner, _git_diff_rule, _git_log_rule, _rendered_and_hand_filled_live,
)

_ROOT = Path(__file__).resolve().parents[2]
_GENERATED = "\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)"
_SESSION = "https://claude.ai/code/session_01R6qK28EjtCtUQmohUDgC2a"


def test_generated_with_line_is_found():
    assert pr_body_lint.find_attribution(f"## Review notes\nok\n\n{_GENERATED}\n") == [_GENERATED]


def test_session_link_only_is_found():
    assert pr_body_lint.find_attribution(f"body\n\n{_SESSION}") == [_SESSION]


def test_co_authored_by_line_is_found_case_insensitively():
    assert pr_body_lint.find_attribution("x\nco-authored-by: A <a@b.c>") == ["co-authored-by: A <a@b.c>"]


def test_clean_body_is_clean_and_prose_about_the_rule_is_not_a_hit():
    assert pr_body_lint.find_attribution("Clean.\nCloses: TCK-1") == []
    assert pr_body_lint.find_attribution("The rule: no Generated with line, no session link, no Co-Authored-By.") == []
    assert pr_body_lint.find_attribution(None) == []


def test_prose_that_quotes_the_trailer_mid_sentence_is_not_a_hit():
    """This ticket's own Request Summary reaches the PR body through `## What landed`."""
    quoted = (
        'no "\U0001F916 Generated with [Claude Code](...)" line, no\n'
        "`https://claude.ai/code/session_...` link, and no `Co-Authored-By`. It still happens. #369 merged with the\n"
        'the "Generated with" line, and #372 carries both lines.'
    )
    assert pr_body_lint.find_attribution(quoted) == []


def test_main_exit_codes_and_message(capsys):
    assert pr_body_lint.main(environ={"PR_BODY": "clean"}) == 0
    assert pr_body_lint.main(environ={"PR_BODY": f"x\n{_GENERATED}"}) == 1
    assert "attribution trailer in PR body" in capsys.readouterr().out
    assert pr_body_lint.main(environ={}) == 0


def _check(tmp_path, trailer):
    rules = [_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(["agent-working/tickets/TCK-20260924-A.md"])]
    tickets_root, rendered, live_body = _rendered_and_hand_filled_live(tmp_path, rules)
    if trailer:
        live_body += "\n\n" + trailer
    runner = FakeRunner([
        (lambda cmd: cmd[:2] == ["gh", "pr"],
         CommandResult(0, json.dumps({"title": rendered["title"], "body": live_body}), "")),
        *rules,
    ])
    return pr_render.check_against_live(run_command=runner, tickets_root=tickets_root)


def test_check_reports_a_generated_with_trailer_and_fails_the_match(tmp_path):
    result = _check(tmp_path, _GENERATED)
    assert result["matches"] is False
    assert result["attribution_found"] == [_GENERATED]
    assert result["differing_sections"] == []


def test_check_reports_a_session_link_only_trailer(tmp_path):
    result = _check(tmp_path, _SESSION)
    assert result["matches"] is False and result["attribution_found"] == [_SESSION]


def test_check_on_a_clean_body_is_unchanged(tmp_path):
    result = _check(tmp_path, None)
    assert result["matches"] is True and result["attribution_found"] == []


def test_workflow_runs_the_lint_on_the_pr_body_events():
    workflow = yaml.safe_load((_ROOT / ".github/workflows/pr-body-lint.yml").read_text(encoding="utf-8"))
    triggers = workflow.get("on") or workflow.get(True)
    assert triggers["pull_request"]["types"] == ["opened", "edited", "synchronize"]
    steps = workflow["jobs"]["pr-body-lint"]["steps"]
    lint = next(step for step in steps if "pr_body_lint.py" in step.get("run", ""))
    assert lint["env"]["PR_BODY"] == "${{ github.event.pull_request.body }}"
    assert "${{" not in lint["run"]  # the body reaches the script through env, never shell text
