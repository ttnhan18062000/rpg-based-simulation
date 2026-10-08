"""The tracked top level of the repository equals the allowlist in docs/guidelines/repo_tooling_layout.md
(TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD). Only first path components count: a new file under src/, tools/ or a
domain root never trips it; a new root file or directory does, and needs an owner decision."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_GUIDELINE = "docs/guidelines/repo_tooling_layout.md"
_BEGIN = "<!-- repo-root-allowlist:begin -->"
_END = "<!-- repo-root-allowlist:end -->"


def root_entries(tracked_paths: list[str]) -> set[str]:
    """First path component of every tracked path: root files and root directories."""
    return {path.split("/", 1)[0] for path in tracked_paths if path}


def parse_allowlist(guideline_text: str) -> set[str]:
    start, end = guideline_text.index(_BEGIN), guideline_text.index(_END)
    return set(re.findall(r"`([^`]+)`", guideline_text[start + len(_BEGIN):end]))


def diff_message(tracked: set[str], allowed: set[str]) -> str:
    unexpected, missing = sorted(tracked - allowed), sorted(allowed - tracked)
    lines = [f"the tracked repo-root entries differ from the allowlist in {_GUIDELINE} (section 'Repo root')."]
    if unexpected:
        lines.append(f"Not on the allowlist (a new root entry needs an owner decision; put it under tools/, docker/, config/ or a domain root): {unexpected}")
    if missing:
        lines.append(f"On the allowlist but no longer tracked (remove it from the guideline in the same PR): {missing}")
    return "\n".join(lines)


def _tracked_root_entries() -> set[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True).stdout
    return root_entries(out.split("\0"))


def test_tracked_root_equals_the_allowlist():
    allowed = parse_allowlist((_REPO_ROOT / _GUIDELINE).read_text(encoding="utf-8"))
    tracked = _tracked_root_entries()
    assert tracked == allowed, diff_message(tracked, allowed)


def test_allowlist_parse_is_not_vacuous():
    allowed = parse_allowlist((_REPO_ROOT / _GUIDELINE).read_text(encoding="utf-8"))
    assert {"src", "tools", "docker", "compose.yaml", "pyproject.toml", "perf_baselines.json", "skills-lock.json"} <= allowed
    assert not {"requirements.txt", "make.bat", "package.json", "backend.Dockerfile", "grafana", "scripts"} & allowed


def test_new_files_under_src_or_a_domain_root_do_not_change_the_root_entries():
    base = ["Makefile", "src/a.py", "codebase/health/x.py", "tools/gate_checks/y.py", "docs/guidelines/z.md", "agent-working/tickets/todos/a.md"]
    extended = base + ["src/new/package/mod.py", "codebase/new_check.py", "tools/new_tool.py", "agent-working/tickets/done/T.md"]
    assert root_entries(extended) == root_entries(base)


def test_a_new_root_file_or_directory_is_caught_and_the_message_names_the_guideline():
    allowed = {"Makefile", "src"}
    for extra in ("notes.txt", "scratch_dir/a.py"):
        tracked = root_entries(["Makefile", "src/a.py", extra])
        assert tracked != allowed
        message = diff_message(tracked, allowed)
        assert _GUIDELINE in message and "Repo root" in message and extra.split("/")[0] in message
    removed = diff_message(root_entries(["Makefile"]), allowed)
    assert "src" in removed and "no longer tracked" in removed
