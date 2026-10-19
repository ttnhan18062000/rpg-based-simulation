"""Guard for TCK-20261019-TESTS-HOOKS-IN-TMP-CWD-INSIDE-A-REPO-READ-REAL-STATE.

A tools test that runs a hook with `cwd=tmp_path` must not see a git repository ABOVE its tmp dir, whatever `--basetemp` is.
The autouse `_git_never_looks_above_the_tests_tmp_dir` fixture in tests/tools/conftest.py sets `GIT_CEILING_DIRECTORIES`;
without it, a basetemp inside a repo made the handover hook list that repo's `.claude/handover/*.md`.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
_HOOK_TEST = "tests/tools/test_session_start_handover_hook.py::test_hook_prints_nothing_when_no_handover_notes_exist"


def _scratch_repo_with_a_real_looking_note(root: Path) -> Path:
    repo = root / "scratch-repo"
    (repo / ".claude" / "handover").mkdir(parents=True)
    (repo / ".claude" / "handover" / "fake-role.md").write_text("# Handover — fake-role\nSENTINEL-NOT-TO-BE-LISTED\n")
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "init"]):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=_GIT_ENV)
    return repo


def test_the_handover_hook_test_passes_with_a_basetemp_inside_a_repo_that_has_handover_notes(tmp_path):
    """The failing case from the repro, run for real: pytest with `--basetemp` inside a throwaway repo whose
    `.claude/handover/` holds a note. The hook test asserts it prints nothing; it only passes if git cannot resolve that repo."""
    repo = _scratch_repo_with_a_real_looking_note(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", _HOOK_TEST, "-q", "-p", "no:cacheprovider", f"--basetemp={repo / 'tmp'}"],
        cwd=_REPO_ROOT, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-500:]
    assert "SENTINEL-NOT-TO-BE-LISTED" not in result.stdout


def test_a_repo_the_test_creates_inside_its_own_tmp_dir_is_still_found(tmp_path):
    """The ceiling is the tmp dir's parent: git still resolves a repo the test itself makes under tmp_path."""
    repo = tmp_path / "own-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True, env=_GIT_ENV)
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=repo, capture_output=True, text=True, env=os.environ)
    assert out.returncode == 0 and Path(out.stdout.strip()).resolve() == repo.resolve()
    assert os.environ["GIT_CEILING_DIRECTORIES"].split(os.pathsep)[0] == str(tmp_path.resolve().parent)
