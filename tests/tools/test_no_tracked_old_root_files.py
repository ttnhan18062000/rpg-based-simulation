"""Guard: nothing is tracked under a pre-move agent-working root.

Origin/main tracks no file at ``tickets/``, ``stored_artifacts/`` ... or the old generated-index folders, so a
tracked file there means a tool or a ``git add -A`` wrote to the pre-move location. Only the leading path
component is matched: ``tools/agent-monitoring/`` and ``docs/agent-monitoring/`` did not move.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List

from tools.agent_working_paths import LEGACY_INDEX_NAMES, LEGACY_ROOT_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
_OLD_ROOTS = frozenset(LEGACY_ROOT_NAMES) | frozenset(LEGACY_INDEX_NAMES)


def tracked_under_old_roots(paths: Iterable[str]) -> List[str]:
    return [p for p in paths if "/" in p and p.split("/", 1)[0] in _OLD_ROOTS]


def _git_ls_files(cwd: Path) -> List[str]:
    out = subprocess.run(["git", "ls-files"], cwd=cwd, check=True, capture_output=True, text=True).stdout
    return out.splitlines()


def test_nothing_tracked_under_an_old_root() -> None:
    assert tracked_under_old_roots(_git_ls_files(REPO_ROOT)) == []


def test_guard_flags_a_seeded_old_root_file_and_spares_moved_neighbours(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    for rel in ("tickets/x.md", "tools/agent-monitoring/a.py", "docs/agent-monitoring/b.md", "agent-working/tickets/y.md"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x")
    git("add", "-A")
    assert tracked_under_old_roots(_git_ls_files(tmp_path)) == ["tickets/x.md"]
