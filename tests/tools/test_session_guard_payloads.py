"""The four forms the guard used to pass as "no action" now ask, and ordinary commands stay allowed.

TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION. Plan P-1: `env git push`, `python3 -c`, `gh api -X PUT .../merge` and
`gh pr close --delete-branch`. The guard is mistake reduction, not a boundary (plan section 10): it reads payload text, so a
payload that builds the words by string arithmetic is out of reach, and the tests do not claim otherwise.
"""
import io
import json
from pathlib import Path

import pytest

from tools.sessions import guard
from tools.sessions.classify import classify

BASH = "Bash"
_REPO_ROOT = Path(__file__).resolve().parents[2]  # the guard needs a git work tree for a caller it cannot resolve


def _classify(command):
    return classify(BASH, {"command": command})


def _guard_says(command, _unused=None):
    """The guard's decision for an unresolved session (a plain `claude`): 'ask' on a critical operation, else None."""
    out = io.StringIO()
    payload = {"tool_name": BASH, "tool_input": {"command": command}, "cwd": str(_REPO_ROOT), "session_id": "no-such-session"}
    rc = guard.main(stdin=io.StringIO(json.dumps(payload)), stdout=out, stderr=io.StringIO())
    assert rc == 0
    text = out.getvalue().strip()
    return json.loads(text)["hookSpecificOutput"]["permissionDecision"] if text else None


# --- form 1: a wrapper before the real command ---------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "env git push origin main",
    "env GIT_TRACE=1 git push origin main",
    "env -i git push origin main",
    "env -u HOME git push origin main",
    "command git push origin main",
    "nohup git push origin main",
    "time git push origin main",
    "timeout 60 git push origin main",
    "nice -n 5 git push origin main",
    "exec git push origin main",
    "/usr/bin/env git push origin main",
])
def test_a_wrapped_push_to_the_default_branch_is_a_push_to_the_default_branch(command, tmp_path):
    assert {"push", "push_default_branch"} <= set(_classify(command).actions)
    assert _guard_says(command, tmp_path) == "ask"


def test_a_wrapped_push_to_an_own_branch_stays_a_plain_push():
    assert set(_classify("env -i git push origin my-branch").actions) == {"push"}


@pytest.mark.parametrize("command", ["command -v git", "env", "env FOO=1 python3 tools/x.py", "time ls", "nohup python3 run.py"])
def test_a_wrapper_that_runs_nothing_authoritative_is_not_an_authority_call(command):
    assert not _classify(command).is_authority


# --- form 2: an interpreter payload ----------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "python3 -c \"import subprocess; subprocess.run(['git','push','origin','main'])\"",
    "python3 -c 'import os; os.system(\"git push origin main\")'",
    "node -e \"require('child_process').execSync('git push origin main')\"",
    "perl -e 'system(\"git push origin main\")'",
    "env python3 -c \"import os; os.system('gh pr merge 5')\"",
    "python3 -c \"import os; os.system('gh pr close 5 --delete-branch')\"",
])
def test_an_interpreter_payload_that_names_a_push_a_merge_or_a_delete_asks(command, tmp_path):
    result = _classify(command)
    assert result.is_authority and result.uncertain and "interpreter payload" in result.detail
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "python3 -c 'print(1)'",
    "python3 -c \"import json; print(json.dumps({'a': 1}))\"",
    "python3 -c \"import yaml, sys; print(len(yaml.safe_load(open('registries/session_roles.yaml'))))\"",
    "python3 -c \"print('commit message text')\"",
    "python3 -c 'import sys; print(sys.version)'",
    "node -e \"console.log(JSON.stringify({a: 1}))\"",
    "python3 tools/delivery/pr_status.py --pr 1",
    "python3 -m pytest tests/tools -q",
])
def test_ordinary_interpreter_calls_stay_allowed(command, tmp_path):
    assert _guard_says(command, tmp_path) is None


def test_a_later_own_branch_push_is_not_made_uncertain_by_an_earlier_harmless_payload(tmp_path):
    command = "python3 -c 'x = 1' && git push origin my-branch"
    assert set(_classify(command).actions) == {"push"} and not _classify(command).uncertain
    assert _guard_says(command, tmp_path) is None


# --- form 3: gh api PUT ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "gh api -X PUT repos/o/r/pulls/1/merge",
    "gh api --method PUT repos/o/r/pulls/1/merge",
    "gh api repos/o/r/pulls/1/merge -XPUT",
    "gh api --method=PUT repos/o/r/rulesets/1 --input body.json",
    "gh api -X put repos/o/r/pulls/1/merge",
])
def test_gh_api_put_asks(command, tmp_path):
    assert "merge" in _classify(command).actions
    assert "PUT" in _classify(command).detail
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "gh api repos/o/r/pulls/1",
    "gh api repos/o/r/pulls/1/merge",
    "gh api -X GET repos/o/r/rulesets",
    "gh api -X PATCH repos/o/r/pulls/796 --input body.json",
    "gh api -X POST repos/o/r/issues/715/comments -f body=hello",
    "gh api repos/o/r/issues/715/comments -f body=hello",
    "gh pr view 796 --json state",
    "gh pr checks 796",
    "gh pr list --head my-branch",
    "gh run list --limit 3",
])
def test_gh_reads_and_ordinary_writes_stay_allowed(command, tmp_path):
    assert not _classify(command).is_authority
    assert _guard_says(command, tmp_path) is None


# --- other routes to the same actions: a merge, a delete or a moved ref by another API call --------------------

@pytest.mark.parametrize("command,action", [
    ("gh api -X POST repos/o/r/merges -f base=main -f head=x", "merge"),
    ("gh api repos/o/r/merges -f base=main -f head=x", "merge"),  # -f implies POST
    ("gh api graphql -f query='mutation { mergePullRequest(input: {pullRequestId: \"X\"}) { clientMutationId } }'", "merge"),
    ("gh api graphql -f query='mutation { enablePullRequestAutoMerge(input: {}) { clientMutationId } }'", "merge"),
    ("gh api graphql -f query='mutation { deleteRef(input: {refId: \"X\"}) { clientMutationId } }'", "delete_remote_branch"),
    ("gh api -X DELETE repos/o/r/git/refs/heads/x", "delete_remote_branch"),
    ("gh api -XDELETE repos/o/r/git/refs/heads/x", "delete_remote_branch"),
    ("gh api --method=DELETE repos/o/r/issues/comments/1", "delete_remote_branch"),  # DELETE generally
    ("gh api -X PATCH repos/o/r/git/refs/heads/main -f sha=abc", "push_default_branch"),
])
def test_other_routes_to_a_merge_a_delete_or_a_moved_main_ask(command, action, tmp_path):
    assert action in _classify(command).actions
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "gh api -X POST repos/o/r/git/refs -f ref=refs/heads/x -f sha=abc",
    "gh api repos/o/r/git/refs -f ref=refs/heads/x -f sha=abc",  # -f implies POST
    "gh api -X PATCH repos/o/r/git/refs/heads/feature -f sha=abc",
    "gh api graphql -f query='mutation { updateRef(input: {}) { clientMutationId } }'",
    "gh api graphql -f query='mutation { createRef(input: {}) { clientMutationId } }'",
])
def test_a_ref_written_through_the_api_asks_because_its_target_cannot_be_told(command, tmp_path):
    result = _classify(command)
    assert "push" in result.actions and result.uncertain
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "gh api -X PATCH repos/o/r/pulls/796 -f title=x",
    "gh api -X PATCH repos/o/r/pulls/796 --input body.json",
    "gh api -X POST repos/o/r/issues/715/comments -f body=hello",
    "gh api repos/o/r/issues/715/comments -f body=hello",
    "gh api repos/o/r/git/refs/heads/main",  # a GET of a ref
    "gh api repos/o/r/rulesets/14220945",
    "gh api graphql -f query='query { viewer { login } }'",
    "gh api graphql -f query='mutation { addComment(input: {}) { clientMutationId } }'",
    "gh api repos/o/r/actions/runs?per_page=100 --jq .total_count",
    "echo 'gh api -X PUT repos/o/r/pulls/1/merge'",  # a string, not a call
    "git commit -m 'document gh api -X PUT'",
])
def test_pr_edits_comments_reads_and_text_that_merely_mentions_an_api_call_stay_allowed(command, tmp_path):
    assert not (set(_classify(command).actions) & {"merge", "delete_remote_branch", "push", "push_default_branch"}), command
    assert _guard_says(command, tmp_path) is None


def test_an_api_call_inside_a_compound_command_is_still_seen(tmp_path):
    command = "gh api repos/o/r/pulls/1 && gh api -X PUT repos/o/r/pulls/1/merge"
    assert "merge" in _classify(command).actions and _guard_says(command, tmp_path) == "ask"
    command = "env gh api -X PUT repos/o/r/pulls/1/merge"
    assert "merge" in _classify(command).actions


# --- form 4: --delete-branch ------------------------------------------------------------------------------------

@pytest.mark.parametrize("command", ["gh pr close 5 --delete-branch", "gh pr close 5 -d", "gh pr close --delete-branch 5",
                                     "gh pr close 5 --delete-branch=true", "gh pr merge 5 --squash --delete-branch"])
def test_a_branch_delete_on_a_pr_command_asks(command, tmp_path):
    assert "delete_remote_branch" in _classify(command).actions
    assert _guard_says(command, tmp_path) == "ask"


def test_closing_a_pr_without_deleting_its_branch_is_not_an_authority_call():
    assert not _classify("gh pr close 5").is_authority
    assert not _classify("gh pr close 5 --comment 'superseded'").is_authority


def test_the_old_cases_still_classify_as_before():
    assert set(_classify("git push origin main").actions) == {"push", "push_default_branch"}
    assert set(_classify("gh pr merge 5 --squash").actions) == {"merge"}
    assert set(_classify("gh api -X DELETE repos/o/r/git/refs/heads/x").actions) == {"delete_remote_branch"}
    assert set(_classify("git push origin my-branch").actions) == {"push"}


# --- more wrappers, grouping, and `gh` repo flags (planner review) ---------------------------------------------

@pytest.mark.parametrize("command", [
    "sudo git push origin main",
    "sudo -u bob git push origin main",
    "sudo -E git push origin main",
    "stdbuf -oL git push origin main",
    "stdbuf -o L git push origin main",
    "watch git push origin main",
    "watch -n 5 git push origin main",
])
def test_sudo_stdbuf_and_watch_wrap_a_push_like_the_other_wrappers(command, tmp_path):
    assert {"push", "push_default_branch"} <= set(_classify(command).actions)
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "(git push origin main)",
    "( git push origin main )",
    "(cd x && git push origin main)",
    "{ git push origin main; }",
    "{ cd x; git push origin main; }",
    "echo start && (git push origin main)",
    "((git push origin main))",
])
def test_a_push_inside_a_subshell_or_a_brace_group_is_still_a_push(command, tmp_path):
    assert {"push", "push_default_branch"} <= set(_classify(command).actions)
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", [
    "(cd x && ls)", "(ls -la)", "{ echo hi; }", "(git status)", "echo ${HOME}", "(git log --oneline | head)",
    "sudo ls", "sudo -u bob ls /tmp", "stdbuf -oL ls", "watch -n 2 ls", "watch -n 2 git status",
])
def test_an_ordinary_subshell_group_or_wrapper_stays_allowed(command, tmp_path):
    assert not _classify(command).is_authority
    assert _guard_says(command, tmp_path) is None


@pytest.mark.parametrize("command", [
    "gh pr -R o/r merge 5",
    "gh pr --repo o/r merge 5",
    "gh --repo o/r pr merge 5",
    "gh pr merge -R o/r 5",
    "gh pr merge 5 --repo o/r",
])
def test_the_value_of_a_gh_repo_flag_is_skipped_so_a_merge_is_still_seen(command, tmp_path):
    assert "merge" in _classify(command).actions
    assert _guard_says(command, tmp_path) == "ask"


@pytest.mark.parametrize("command", ["gh pr -R o/r view 5", "gh pr --repo o/r list", "gh --repo o/r pr view 5", "gh pr view 5 -R o/r"])
def test_a_gh_repo_flag_on_a_read_stays_allowed(command, tmp_path):
    assert not _classify(command).is_authority
    assert _guard_says(command, tmp_path) is None
