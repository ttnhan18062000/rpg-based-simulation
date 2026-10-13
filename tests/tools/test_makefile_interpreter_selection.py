"""Live-behavior test for TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT: proves
Makefile's PYTHON3/PYTHON_KNOWLEDGE selection actually falls through past a candidate that exists
but fails its capability probe, instead of picking it (and every downstream target silently or
loudly breaking on it) or picking nothing.

Extracts the real shell command from inside each variable's `$(shell ...)` block (never a
hand-copied reimplementation, so this test can't drift from the real Makefile logic), swaps only
the candidate path list for two fake `python3` executables, and runs the result via `bash -c` --
same shell, same probe expression, same fallthrough semantics as `make` itself uses to compute
these variables.
"""
from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path

import pytest

_MAKEFILE = Path("Makefile")

# Both shims intercept the probe's `-c` invocation directly (exit 0 / exit 1) rather than
# delegating to a real python3 for it -- the probed module (pydantic / sentence_transformers) may
# or may not actually be installed for whatever bare `python3` resolves to in the sandbox running
# this test, and the point of this test is the selection loop's fallthrough logic, not a real
# capability check. Non-probe invocations still delegate to a real interpreter.
_WORKING_SHIM = '#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\nexec python3 "$@"\n'
_BROKEN_SHIM = '#!/bin/sh\nif [ "$1" = "-c" ]; then exit 1; fi\nexec python3 "$@"\n'


def _extract_shell_command(text: str, var_name: str) -> str:
    """Pull the raw command out of `<var_name> := $(shell <command>)`, converting Make's `$$`
    escaping back to a literal `$` for direct execution by bash."""
    match = re.search(rf"^{re.escape(var_name)} := \$\(shell (.+)\)$", text, re.MULTILINE)
    assert match is not None, f"{var_name} := $(shell ...) line not found in Makefile"
    return match.group(1).replace("$$", "$")


def _write_shim(path: Path, contents: str) -> None:
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_selection(command: str, candidates: list[str]) -> str:
    """Replace the `for py in ...; do` candidate list with `candidates`, keeping the rest of the
    extracted probe/selection command verbatim, and run it."""
    new_command = re.sub(
        r"^for py in .*?; do", f"for py in {' '.join(candidates)}; do", command
    )
    result = subprocess.run(
        ["bash", "-c", new_command], capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()


@pytest.fixture(params=["PYTHON3", "PYTHON_KNOWLEDGE"])
def selection_command(request) -> str:
    text = _MAKEFILE.read_text(encoding="utf-8")
    return _extract_shell_command(text, request.param)


def test_falls_through_broken_candidate_to_working_one(tmp_path, selection_command):
    broken_dir = tmp_path / "broken" / "bin"
    working_dir = tmp_path / "working" / "bin"
    broken_dir.mkdir(parents=True)
    working_dir.mkdir(parents=True)
    _write_shim(broken_dir / "python3", _BROKEN_SHIM)
    _write_shim(working_dir / "python3", _WORKING_SHIM)

    selected = _run_selection(
        selection_command, [str(broken_dir / "python3"), str(working_dir / "python3")]
    )

    assert selected == str(working_dir / "python3"), (
        "selection must fall through the existing-but-capability-failing candidate to the next "
        "one that actually passes the probe, not pick the broken one or stop early"
    )


def test_picking_broken_candidate_first_does_not_silently_resolve_it(tmp_path, selection_command):
    """Sanity check for the fixture above: confirms the broken shim genuinely fails the probe on
    its own (would resolve if listed alone), so the fallthrough test isn't passing by accident."""
    broken_dir = tmp_path / "broken" / "bin"
    broken_dir.mkdir(parents=True)
    _write_shim(broken_dir / "python3", _BROKEN_SHIM)

    selected = _run_selection(selection_command, [str(broken_dir / "python3")])

    assert selected == "", "the broken shim must fail the probe when it is the only candidate"


def test_all_broken_candidates_resolve_to_empty(tmp_path, selection_command):
    """No working candidate anywhere -> empty result, same as the pre-existing bare-`python3`
    fallback failing today; matches PYTHON's own documented empty-on-CI failure mode, not a new
    behavior this ticket introduces."""
    broken_dir = tmp_path / "broken" / "bin"
    broken_dir.mkdir(parents=True)
    _write_shim(broken_dir / "python3", _BROKEN_SHIM)

    selected = _run_selection(
        selection_command, [str(broken_dir / "python3"), str(broken_dir / "python3")]
    )

    assert selected == ""


def test_python3_candidate_list_names_the_main_root_not_a_host_path():
    text = _MAKEFILE.read_text(encoding="utf-8")
    match = re.search(r"^PYTHON3 := \$\(shell for py in (.+?); do", text, re.MULTILINE)
    assert match is not None
    assert match.group(1).split() == [
        ".venv/bin/python3",
        '"$(KNOWLEDGE_MAIN_ROOT)/.venv/bin/python3"',
        "python3",
    ]


def test_python3_resolves_to_the_main_checkout_venv_from_a_worktree(tmp_path):
    """TCK-20261012-HOST-PATH-LITERALS-MAKEFILE-AND-MCP-LAUNCHERS: a worktree has no `.venv`; the
    main checkout's is found through the git common dir, on any host."""
    import os
    import shutil

    if shutil.which("make") is None or shutil.which("git") is None:
        pytest.skip("make and git are required")
    main = tmp_path / "main"
    main.mkdir()
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
    }

    def git(*args: str, cwd: Path = main) -> None:
        subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "init")
    (main / ".venv" / "bin").mkdir(parents=True)
    _write_shim(main / ".venv" / "bin" / "python3", _WORKING_SHIM)
    worktree = tmp_path / "wt"
    git("worktree", "add", "-q", str(worktree))

    result = subprocess.run(
        ["make", "-f", str(_MAKEFILE.resolve()), "-pn"],
        cwd=worktree, env=env, capture_output=True, text=True, timeout=60,
    )
    line = next((l for l in result.stdout.splitlines() if l.startswith("PYTHON3 :=")), "")
    assert line.split(":=", 1)[1].strip() == os.path.realpath(main) + "/.venv/bin/python3"
