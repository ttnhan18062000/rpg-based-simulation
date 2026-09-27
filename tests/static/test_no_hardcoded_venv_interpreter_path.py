"""Guards against the exact defect class fixed twice now: a test/tool subprocess call hardcoding
one specific dev machine's absolute venv interpreter path instead of `sys.executable`.

This project has (at least) two dev machines with different venv locations -- `u24desktop` at
`.venv/bin/python3`, `vboxuser` at `/home/vboxuser/Work/venv/bin/python3` -- plus CI, which has
neither. A path that works for whoever wrote the test is broken for the other two environments,
and fails there with a plain `FileNotFoundError`, not a test assertion failure -- deterministic on
CI, never reproducible on the machine where the path happens to be valid (see
TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH,
TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS).

Deliberately narrow: only flags a venv-interpreter-path string literal used as the first element
of a subprocess command list (`[<path>, ...]`) -- the exact shape both real bugs had. A broad
"no absolute /home/... path anywhere" rule would be wrong; this repo has legitimate machine-
specific path literals used as pure string *data* (e.g. `tests/tools/test_cd_prefix_advisory_hook.py`
passes one to a path-parsing function under test) or inside documentation strings/comments
(e.g. `tools/perf/live_map_ws_payload_measure.py`'s CLI usage example) -- neither is ever executed
as an interpreter, so neither is a bug of this class.
"""
import re
from pathlib import Path

_VENV_INTERPRETER_AS_SUBPROCESS_ARG_RE = re.compile(
    r"""\[\s*["'][^"']*\.?venv/bin/python\d*["']"""
)

# This module's own docstring/pattern text must not flag itself.
_SELF = Path(__file__).name


def _find_violations(scan_dirs: list[Path], root_dir: Path) -> list[str]:
    violations = []
    for scan_dir in scan_dirs:
        for py_file in sorted(scan_dir.rglob("*.py")):
            if py_file.name == _SELF or "__pycache__" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8")
            for line_num, line in enumerate(text.splitlines(), 1):
                if _VENV_INTERPRETER_AS_SUBPROCESS_ARG_RE.search(line):
                    violations.append(f"{py_file.relative_to(root_dir)}:{line_num} -> {line.strip()}")
    return violations


def test_no_hardcoded_venv_interpreter_path_as_subprocess_arg():
    root_dir = Path(__file__).resolve().parent.parent.parent
    violations = _find_violations([root_dir / "tests", root_dir / "tools"], root_dir)

    assert not violations, (
        "Found a hardcoded venv interpreter path used as a subprocess command argument -- use "
        "sys.executable instead, which resolves correctly on every machine and in CI:\n"
        + "\n".join(violations)
    )


def test_detects_planted_violation_matching_the_real_bug_shape(tmp_path):
    # Deliberately-planted bad file, same shape as the real bug: a hardcoded venv path as the
    # first element of a subprocess command list. Proves detection works, not just clean
    # reporting on an already-fixed corpus.
    bad_file = tmp_path / "test_planted_bad_subprocess_call.py"
    bad_file.write_text(
        'result = subprocess.run(\n'
        '    ["/home/someone/Work/repo/.venv/bin/python3", "-m", "pytest"],\n'
        ')\n',
        encoding="utf-8",
    )
    violations = _find_violations([tmp_path], tmp_path)
    assert len(violations) == 1
    assert "test_planted_bad_subprocess_call.py:2" in violations[0]


def test_does_not_flag_path_as_pure_string_data():
    # Mirrors tests/tools/test_cd_prefix_advisory_hook.py's real, legitimate usage: a
    # machine-specific path passed as data to a non-subprocess call, never as a subprocess arg.
    text = (
        'vboxuser_pos = text.index("/home/vboxuser/Work/venv/bin/python3")\n'
    )
    assert not _VENV_INTERPRETER_AS_SUBPROCESS_ARG_RE.search(text)
