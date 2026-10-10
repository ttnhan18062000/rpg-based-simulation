"""Guard: no file under ``visual_assets/`` or ``tests/visual_assets/`` is hidden by a gitignore rule.

A broad rule such as ``build/`` once swallowed the whole ``visual_assets/store/build/`` package: it passed every local
run (the files existed on disk) and failed CI (they were never committed). Anything git ignores here, code or data, is
a file a clean checkout will not have, so the only ignored paths allowed are bytecode caches and the two local-only
catalog folders.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOTS = ("visual_assets", "tests/visual_assets")
ALLOWED_PREFIXES = (
    "visual_assets/catalog/.quarantine/", "visual_assets/catalog/.review/",
    # ADR D24 local state: the store lock and the gc deletion log with its archives
    "visual_assets/catalog/.store.lock", "visual_assets/catalog/.deletions",
)


def unexpected_ignored(paths: Iterable[str]) -> List[str]:
    return [
        p
        for p in paths
        if "__pycache__/" not in p and not p.endswith(".pyc") and not p.startswith(ALLOWED_PREFIXES)
    ]


def _ignored_files(cwd: Path, roots: Iterable[str]) -> List[str]:
    out = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", *roots],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return out.splitlines()


def test_nothing_under_visual_assets_is_gitignored() -> None:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    assert unexpected_ignored(_ignored_files(REPO_ROOT, ROOTS)) == []


def test_guard_flags_a_planted_ignored_file_and_spares_the_allowed_ones(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("build/\n__pycache__/\n.quarantine/\n.review/\n")
    for rel in (
        "visual_assets/store/build/exporter.py",
        "visual_assets/store/build/data.json",
        "visual_assets/store/__pycache__/a.pyc",
        "visual_assets/catalog/.quarantine/in-0/x.bin",
        "visual_assets/catalog/.review/y.png",
        "visual_assets/store/ok.py",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x")
    assert unexpected_ignored(_ignored_files(tmp_path, ROOTS)) == [
        "visual_assets/store/build/data.json",
        "visual_assets/store/build/exporter.py",
    ]
