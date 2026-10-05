"""Tests for tools/test_architecture/registry_resync_skip.py (fail-open skip decision on a re-sync push)."""

import subprocess
from pathlib import Path
from typing import Dict, List

import pytest

from tools.test_architecture import registry_resync_skip as rrs

SLUG = "owner/repo"
PR_FILE = "src/feature.py"
BODY = "".join(f"line {i}\n" for i in range(1, 41))


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def commit(repo: Path, files: Dict[str, str], message: str) -> str:
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


class Scenario:
    """A repo with main (M0) and a PR branch (BEFORE) that edits PR_FILE near the top of the file."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        git(repo, "init", "-b", "main")
        self.m0 = commit(repo, {PR_FILE: BODY, rrs.REGISTRY_PATH: "registry v0\n"}, "main 0")
        git(repo, "checkout", "-b", "pr")
        self.before = commit(repo, {PR_FILE: BODY.replace("line 3\n", "line 3 PR\n")}, "pr change")
        git(repo, "checkout", "main")
        self.m1 = commit(repo, {rrs.REGISTRY_PATH: "registry v1\n", "docs/other.md": "x\n"}, "main 1")
        git(repo, "checkout", "pr")

    def resync(self, files: Dict[str, str] = None, *merge_args: str) -> str:
        """Merge main into the PR branch, then apply extra file changes as a following commit."""
        git(self.repo, "merge", "--no-edit", *merge_args, "main")
        if files:
            commit(self.repo, files, "extra change on the PR branch")
        return git(self.repo, "rev-parse", "HEAD")


def fetcher(runs: List[Dict[str, object]], jobs: Dict[int, List[Dict[str, object]]], fail: bool = False):
    def fetch(path: str) -> Dict[str, object]:
        if fail:
            raise OSError("api down")
        if "/jobs" in path:
            run_id = int(path.split("/runs/")[1].split("/")[0])
            return {"total_count": len(jobs[run_id]), "jobs": jobs[run_id]}
        return {"workflow_runs": runs}

    return fetch


def green_fetch():
    return fetcher(
        [{"id": 1, "name": "Tests", "status": "completed", "conclusion": "success"}],
        {1: [{"name": "a", "conclusion": "success"}, {"name": "b", "conclusion": "skipped"}]},
    )


def run_decide(s: Scenario, after: str, fetch, before: str = None, event="pull_request", action="synchronize"):
    return rrs.decide(
        str(s.repo), SLUG, event, action, s.m1, before if before is not None else s.before, after, fetch
    )


@pytest.fixture
def s(tmp_path: Path) -> Scenario:
    return Scenario(tmp_path)


def test_registry_only_resync_after_green_run_is_true(s):
    after = s.resync()
    d = run_decide(s, after, green_fetch())
    assert d.unchanged, d.rule
    assert d.before == s.before


def test_identical_patch_with_registry_change_in_the_pr_is_true(s):
    git(s.repo, "checkout", "pr")
    before = commit(s.repo, {rrs.REGISTRY_PATH: "registry pr edit\n"}, "pr registry only")
    after = s.resync(None, "-X", "theirs")
    assert run_decide(s, after, green_fetch(), before=before).unchanged


def test_code_change_is_false(s):
    after = s.resync({PR_FILE: BODY.replace("line 3\n", "line 3 PR\n").replace("line 30\n", "line 30 NEW\n")})
    d = run_decide(s, after, green_fetch())
    assert not d.unchanged
    assert "patch" in d.rule


def test_context_shift_caused_by_main_is_false(s):
    git(s.repo, "checkout", "main")
    s.m1 = commit(s.repo, {PR_FILE: BODY.replace("line 6\n", "line 6 MAIN\n")}, "main edits next to the PR")
    git(s.repo, "checkout", "pr")
    after = s.resync()
    d = run_decide(s, after, green_fetch())
    assert not d.unchanged
    assert "patch" in d.rule


@pytest.mark.parametrize(
    "run,jobs",
    [
        ({"status": "completed", "conclusion": "failure"}, [{"name": "a", "conclusion": "failure"}]),
        ({"status": "completed", "conclusion": "cancelled"}, [{"name": "a", "conclusion": "cancelled"}]),
        ({"status": "completed", "conclusion": "failure"}, [{"name": "a", "conclusion": "timed_out"}]),
        ({"status": "in_progress", "conclusion": None}, [{"name": "a", "conclusion": None}]),
        ({"status": "completed", "conclusion": "success"}, [{"name": "a", "conclusion": "success"}, {"name": "b", "conclusion": "cancelled"}]),
        ({"status": "completed", "conclusion": "success"}, []),
    ],
    ids=["red", "cancelled", "timed_out", "in_progress", "one_bad_job", "no_jobs"],
)
def test_previous_run_not_green_is_false(s, run, jobs):
    after = s.resync()
    fetch = fetcher([{"id": 1, "name": "Tests", **run}], {1: jobs})
    d = run_decide(s, after, fetch)
    assert not d.unchanged
    assert "not green" in d.rule


def test_no_tests_run_on_before_is_false(s):
    after = s.resync()
    fetch = fetcher([{"id": 9, "name": "Other", "status": "completed"}], {9: []})
    assert not run_decide(s, after, fetch).unchanged


def test_api_error_is_false(s):
    after = s.resync()
    d = run_decide(s, after, fetcher([], {}, fail=True))
    assert not d.unchanged
    assert "errored" in d.rule


def test_missing_before_is_false(s):
    after = s.resync()
    assert not run_decide(s, after, green_fetch(), before="1" * 40).unchanged
    assert not run_decide(s, after, green_fetch(), before="0" * 40).unchanged
    assert not run_decide(s, after, green_fetch(), before="").unchanged


@pytest.mark.parametrize("event,action", [("push", "synchronize"), ("pull_request", "opened"), ("schedule", "")])
def test_other_events_are_false(s, event, action):
    after = s.resync()
    assert not run_decide(s, after, green_fetch(), event=event, action=action).unchanged


def test_render_first_line_is_the_flag_and_summary_names_rule_and_before(s):
    after = s.resync()
    lines = rrs.render(run_decide(s, after, green_fetch()))
    assert lines[0] == "pr_content_unchanged=true"
    text = "\n".join(lines)
    assert s.before in text
    assert "Rule that decided" in text
    off = rrs.render(rrs.Decision(False, "why", ""))
    assert off[0] == "pr_content_unchanged=false"


def test_main_never_raises_and_fails_open(monkeypatch, capsys):
    for var in ("EVENT_NAME", "EVENT_ACTION", "BASE_SHA", "BEFORE_SHA", "AFTER_SHA", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    assert rrs.main() == 0
    assert capsys.readouterr().out.splitlines()[0] == "pr_content_unchanged=false"
