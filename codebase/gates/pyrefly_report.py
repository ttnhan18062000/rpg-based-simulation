"""The Pyrefly advisory report: show the Pyrefly errors that are not in the committed baseline. Never a gate.

    python3 -m codebase.gates.pyrefly_report [--summary-out PATH] [--pyrefly-output FILE]
    python3 -m codebase.gates.pyrefly_report --update-baseline

Pyrefly is an advisory second type-checker opinion next to mypy (`TCK-20261021-PYREFLY-ADVISORY-REPORT`; the
recommendation of `docs/plans/codebase_health/python_code_craft_type_checker_trial.md`). mypy + mypy-baseline stays the
blocking checker (`codebase.gates.mypy_gate`); this module never blocks. It runs `pyrefly check` with its own
`--baseline codebase/baselines/pyrefly_baseline.json` (configured in `[tool.pyrefly]` in pyproject.toml), prints the
errors that are new, and appends one Markdown summary to `--summary-out` ($GITHUB_STEP_SUMMARY in CI): the Pyrefly
version, the count of new errors, the baseline size, and the first few new errors with file:line and the error kind.

Exit codes: 0 whether or not there are new errors (report-only), 2 only when the report cannot be produced (Pyrefly
is missing or crashed, its output is not JSON, or the baseline is missing, empty or unparseable). A broken tool is
therefore loud in the log and in the summary and never reads as "0 new". There is no `--annotate`: inline annotations
would make an advisory tool look like a failure.

The baseline is written by `make typecheck-pyrefly-baseline-sync` (Pyrefly's own `--update-baseline`, which edits no
source file; `pyrefly suppress` is forbidden because it writes comments into `src/`). Pyrefly keys baseline entries by
file, error kind, column and message and not by line number, so an unrelated edit does not churn it.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from codebase.health import registry

# The interpreter that runs this module is the one whose site-packages Pyrefly resolves imports against (as for mypy), so the
# result does not depend on which `python` happens to be first on PATH.
PYREFLY_ARGS = ("check", "--output-format", "json", "--python-interpreter-path", sys.executable)
DEFAULT_BASELINE = "codebase/baselines/pyrefly_baseline.json"
# `pyrefly check` exits 0 for no errors and 1 for errors; anything else (crash, bad config) is "could not run".
OK_EXIT_CODES = (0, 1)
LIST_LIMIT = 25
SUMMARY_HEADING = "Pyrefly (advisory, never blocks)"


class ReportCannotRunError(Exception):
    """Pyrefly could not produce a usable result."""


def find_pyrefly() -> str:
    """The `pyrefly` executable: next to the running interpreter (the uv environment), else on PATH."""
    beside = Path(sys.executable).parent / "pyrefly"
    if beside.is_file() and os.access(beside, os.X_OK):
        return str(beside)
    found = shutil.which("pyrefly")
    if found is None:
        raise ReportCannotRunError("pyrefly is not installed (uv sync --group lint)")
    return found


def parse_errors(text: str, what: str) -> list[dict[str, Any]]:
    """The `errors` list of a Pyrefly JSON document; anything else is `ReportCannotRunError`."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReportCannotRunError(f"{what} is not JSON: {exc}") from exc
    errors = document.get("errors") if isinstance(document, dict) else None
    if not isinstance(errors, list):
        raise ReportCannotRunError(f"{what} has no `errors` list")
    return [entry for entry in errors if isinstance(entry, dict)]


def baseline_entries(root: Path, baseline: str = DEFAULT_BASELINE) -> int:
    """The number of errors in the baseline file; a missing, unparseable or empty baseline cannot run."""
    path = root / baseline
    if not path.is_file():
        raise ReportCannotRunError(f"baseline {baseline} does not exist (run `make typecheck-pyrefly-baseline-sync` on main)")
    entries = len(parse_errors(path.read_text(encoding="utf-8"), baseline))
    if entries == 0:
        raise ReportCannotRunError(f"baseline {baseline} holds no errors (run `make typecheck-pyrefly-baseline-sync` on main)")
    return entries


def _run(command: Sequence[str], root: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYREFLY_COLOR": "never"}
    try:
        return subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, env=env)
    except OSError as exc:
        raise ReportCannotRunError(f"{command[0]}: {exc}") from exc


def pyrefly_version(executable: str, root: Path) -> str:
    """`pyrefly --version` without the program name, or `unknown` if it cannot be read."""
    done = _run([executable, "--version"], root)
    words = done.stdout.split()
    return words[-1] if done.returncode == 0 and words else "unknown"


def describe(error: dict[str, Any]) -> str:
    """One line for a new error: `path:line:column [kind] first line of the message`."""
    message = str(error.get("concise_description") or error.get("description") or "").splitlines()
    first = message[0] if message else ""
    return f"{error.get('path', '?')}:{error.get('line', '?')}:{error.get('column', '?')} [{error.get('name', '?')}] {first}"


def format_summary(new: Sequence[dict[str, Any]], entries: int, version: str) -> str:
    """The job summary: one line when nothing is new, otherwise the count and the first errors."""
    head = f"### {SUMMARY_HEADING}\n\nPyrefly {version}:"
    size = f"baseline holds {entries} errors"
    if not new:
        return f"{head} 0 new errors ({size})."
    shown = [describe(error) for error in new[:LIST_LIMIT]]
    more = [f"... and {len(new) - LIST_LIMIT} more"] if len(new) > LIST_LIMIT else []
    return f"{head} {len(new)} new errors ({size}).\n\n```\n" + "\n".join([*shown, *more]) + "\n```"


def _append(path: Path | None, text: str) -> None:
    if path is not None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def run(root: Path, summary_out: Path | None = None, pyrefly_output: Path | None = None, executable: str | None = None) -> int:
    """Produce the report; returns 0 (report written, new errors or not) or 2 (could not run)."""
    try:
        entries = baseline_entries(root)
        if pyrefly_output is not None:
            raw, version = pyrefly_output.read_text(encoding="utf-8"), "unknown"
        else:
            binary = executable or find_pyrefly()
            version = pyrefly_version(binary, root)
            done = _run([binary, *PYREFLY_ARGS, "--baseline", DEFAULT_BASELINE], root)
            if done.returncode not in OK_EXIT_CODES:
                detail = (done.stderr or done.stdout).strip()
                raise ReportCannotRunError(f"pyrefly exited {done.returncode}: {detail}")
            raw = done.stdout
        new = parse_errors(raw, "pyrefly output")
    except (ReportCannotRunError, OSError) as exc:
        reason = " ".join(f"{exc}".split())[:300] or type(exc).__name__
        _append(summary_out, f"### {SUMMARY_HEADING}\n\nCould not run: {reason}")
        print(f"error: {reason}", file=sys.stderr)
        return 2
    for error in new:
        print(describe(error))
    _append(summary_out, format_summary(new, entries, version))
    print(format_summary(new, entries, version).splitlines()[2])
    return 0


def update_baseline(root: Path, executable: str | None = None) -> int:
    """Rewrite the baseline from a fresh Pyrefly run (Pyrefly's own `--update-baseline`; no source file is edited)."""
    try:
        binary = executable or find_pyrefly()
        done = _run([binary, *PYREFLY_ARGS, "--baseline", DEFAULT_BASELINE, "--update-baseline"], root)
        if done.returncode not in OK_EXIT_CODES:
            raise ReportCannotRunError(f"pyrefly exited {done.returncode}: {(done.stderr or done.stdout).strip()}")
        entries = baseline_entries(root)
    except (ReportCannotRunError, OSError) as exc:
        print(f"error: {' '.join(f'{exc}'.split())[:300]}", file=sys.stderr)
        return 2
    print(f"{DEFAULT_BASELINE} rewritten: {entries} errors")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.gates.pyrefly_report", description=__doc__)
    parser.add_argument("--root", type=Path, default=registry.REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--summary-out", type=Path, help="append a Markdown summary here ($GITHUB_STEP_SUMMARY)")
    parser.add_argument("--pyrefly-output", type=Path, help="read this saved Pyrefly JSON instead of running Pyrefly")
    parser.add_argument("--update-baseline", action="store_true", help="rewrite the baseline from a fresh Pyrefly run")
    args = parser.parse_args(argv)
    if args.update_baseline:
        return update_baseline(args.root)
    return run(args.root, args.summary_out, args.pyrefly_output)


if __name__ == "__main__":
    sys.exit(main())
