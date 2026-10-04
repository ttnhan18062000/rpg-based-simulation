"""The pre-commit check: ruff on the staged `src` Python files, compared with the code-health registry.

    python3 -m codebase.gates.staged_ratchet FILE...

prek passes the staged files. Only existing, safe `src/**/*.py` paths are used (the same rule as the SARIF
module). ruff runs on them, and the findings are compared with the registry rows of those files by the
ratchet's own `compare` (a (file, rule) group within its row's ceiling passes), so a commit that touches only
grandfathered code passes and a new or worse violation is rejected with the ratchet's NEW / WORSE report.

Exit 1 only for a real NEW or WORSE result. The hook is installed into the machine-shared `.git/hooks`, so it
also runs in worktrees that have no project environment; whenever the check cannot run (ruff not installed, no
registry, a registry or ruff output that cannot be read) it prints one visible
"code-health hook skipped: <reason>" line and exits 0. CI stays the real gate.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from codebase.health import adapters, ratchet, registry
from codebase.gates.sarif_feedback import changed_python_files

HOW_TO = (
    "Fix the new violation. If it is genuinely owner-approved debt, `git commit --no-verify` is the bypass; "
    "see 'Git hooks (opt-in)' in docs/guidelines/agent_working_environment.md."
)


class HookSkipped(Exception):
    """The check cannot run here; the commit must not be blocked for that reason."""


def _skip(reason: str) -> int:
    print(f"code-health hook skipped: {reason}")
    return 0


def _ruff_json(paths: Sequence[str], root: Path) -> list[dict]:
    if importlib.util.find_spec("ruff") is None:
        raise HookSkipped("ruff is not installed for this Python (environment not synced: uv sync)")
    done = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *paths, "--output-format", "json"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if done.returncode not in (0, 1):
        raise HookSkipped(f"ruff exited {done.returncode}: {' '.join(done.stderr.split())[:200]}")
    try:
        records = json.loads(done.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise HookSkipped(f"ruff output was not JSON ({exc})") from exc
    if not isinstance(records, list):
        raise HookSkipped("ruff output was not a list")
    return records


def check(root: Path, files: Sequence[str], registry_file: Path | None = None) -> ratchet.RatchetResult | None:
    """The ratchet result for the staged files, or None when none of them is a checkable `src` file."""
    paths = changed_python_files(files, root)
    if not paths:
        return None
    path = registry_file or registry.registry_path(root)
    if not path.is_file():
        raise HookSkipped(f"no code-health registry at {path.name} (an older checkout?)")
    try:
        rows = [row for row in registry.load_rows(path, root, check_files=False) if row.file in set(paths)]
        findings = adapters.adapt_ruff(_ruff_json(paths, root), str(root))
    except registry.RegistryError as exc:
        raise HookSkipped(f"the code-health registry is unusable ({exc})") from exc
    return ratchet.compare(findings, rows)


def run(root: Path, files: Sequence[str], registry_file: Path | None = None) -> int:
    """Run the check; returns 1 for a new or worse violation, otherwise 0."""
    try:
        result = check(root, files, registry_file)
    except HookSkipped as exc:
        return _skip(str(exc))
    if result is None or not result.failed:
        return 0
    print(ratchet.format_report(ratchet.RatchetResult(new=result.new, worse=result.worse)))
    print(HOW_TO)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point: the staged file names are the arguments."""
    return run(registry.REPO_ROOT, list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    sys.exit(main())
