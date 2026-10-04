"""The advisory mypy gate: report only the mypy errors that are not in the committed baseline.

    python3 -m codebase.gates.mypy_gate [--summary-out PATH] [--annotate] [--mypy-output FILE]

It runs the repository's mypy command, pipes the output through `mypy-baseline filter` (configured in
`[tool.mypy_baseline]` in pyproject.toml; the baseline is `codebase/baselines/mypy_baseline.txt`), prints the errors
that are new, and returns the filter's exit code: 0 for none, 1 for at least one new error. On every run it
appends one Markdown summary to `--summary-out` ($GITHUB_STEP_SUMMARY in CI) that states the new-error count
and the current baseline size, so the trend stays visible without a snapshot metric. With `--annotate` a
failure also prints one GitHub `::warning::` line.

If mypy or the filter cannot run (a crash, a missing tool, a missing baseline) it still writes a "could not
run" summary line and warning and returns 2, so a broken tool never looks like a clean pass in the
`continue-on-error` CI step (the same rule as `codebase.health check`).

Advisory for the roadmap M4 soak: nothing blocks on the result yet.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Sequence

from codebase.health import registry

MYPY_COMMAND = ("-m", "mypy", "src/", "--config-file", "pyproject.toml", "--no-error-summary")
FILTER_COMMAND = ("-m", "mypy_baseline", "filter")
DEFAULT_BASELINE = "codebase/baselines/mypy_baseline.txt"
LIST_LIMIT = 25


class GateCannotRun(Exception):
    """mypy or mypy-baseline could not produce a usable result."""


def baseline_path(root: Path) -> Path:
    """The baseline file named by `[tool.mypy_baseline] baseline_path`, default `codebase/baselines/mypy_baseline.txt`."""
    with (root / "pyproject.toml").open("rb") as handle:
        table = tomllib.load(handle).get("tool", {}).get("mypy_baseline", {})
    return root / str(table.get("baseline_path", DEFAULT_BASELINE))


def baseline_entries(root: Path) -> int:
    """The number of entries (non-empty lines) in the baseline file."""
    path = baseline_path(root)
    if not path.is_file():
        raise GateCannotRun(f"baseline {path.relative_to(root)} does not exist (run `make typecheck-baseline-sync` on main)")
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def new_error_lines(filtered: str) -> list[str]:
    """The `error:` lines of the filter's output (notes and blank lines are not counted)."""
    return [line for line in filtered.splitlines() if ": error:" in line]


def _run(command: Sequence[str], root: Path, ok_codes: Sequence[int], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        done = subprocess.run(command, cwd=root, input=stdin, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise GateCannotRun(f"{command[0]}: {exc}") from exc
    if done.returncode not in ok_codes:
        detail = (done.stderr or done.stdout).strip()
        raise GateCannotRun(f"{' '.join(command[1:3])} exited {done.returncode}: {detail}")
    return done


def format_summary(new: Sequence[str], entries: int) -> str:
    """The job summary: one line when nothing is new, otherwise the count and the first errors."""
    size = f"baseline holds {entries} entries"
    if not new:
        return f"**mypy (advisory):** 0 new errors ({size})."
    shown = list(new[:LIST_LIMIT])
    more = [f"... and {len(new) - LIST_LIMIT} more"] if len(new) > LIST_LIMIT else []
    body = "\n".join([*shown, *more])
    return f"**mypy (advisory):** {len(new)} new errors ({size}).\n\n```\n{body}\n```"


def _append(path: Path | None, text: str) -> None:
    if path is not None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def run(root: Path, summary_out: Path | None = None, annotate: bool = False, mypy_output: Path | None = None) -> int:
    """Run the gate; returns 0 (nothing new), 1 (new errors) or 2 (could not run)."""
    try:
        entries = baseline_entries(root)
        if mypy_output is not None:
            raw = mypy_output.read_text(encoding="utf-8")
        else:
            raw = _run([sys.executable, *MYPY_COMMAND], root, (0, 1)).stdout
        filtered = _run([sys.executable, *FILTER_COMMAND], root, (0, 1), stdin=raw)
    except (GateCannotRun, OSError, tomllib.TOMLDecodeError) as exc:
        reason = " ".join(f"{exc}".split())[:300] or type(exc).__name__
        _append(summary_out, f"**mypy (advisory):** could not run: {reason}")
        if annotate:
            print(f"::warning::mypy-baseline could not run (advisory): {reason}")
        print(f"error: {reason}", file=sys.stderr)
        return 2
    new = new_error_lines(filtered.stdout)
    if filtered.stdout.strip():
        print(filtered.stdout.rstrip())
    _append(summary_out, format_summary(new, entries))
    if new and annotate:
        print(f"::warning::mypy-baseline: {len(new)} new errors (advisory); see job summary")
    return filtered.returncode


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.gates.mypy_gate", description=__doc__)
    parser.add_argument("--root", type=Path, default=registry.REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--summary-out", type=Path, help="append a Markdown summary here ($GITHUB_STEP_SUMMARY)")
    parser.add_argument("--annotate", action="store_true", help="print a GitHub ::warning:: line on a failure")
    parser.add_argument("--mypy-output", type=Path, help="filter this saved mypy output instead of running mypy")
    args = parser.parse_args(argv)
    return run(args.root, args.summary_out, args.annotate, args.mypy_output)


if __name__ == "__main__":
    sys.exit(main())
