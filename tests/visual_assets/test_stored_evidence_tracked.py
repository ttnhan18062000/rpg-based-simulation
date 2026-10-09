"""Guard: evidence stored for a visual-asset ticket must be in git, not only on one machine (`TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT`).

`.gitignore` (line 241) ignores `agent-working/stored_artifacts/**/*.json`, so blind-check answers, rule results and browser captures that tickets stored as `.json` were never committed: the merged PR #418
(and the earlier M5 work) pointed at files that existed on one disk only. The repo's own convention is a `.txt` twin (`art_prototype_rule_check.py.txt`). This guard fails when a file under
`agent-working/stored_artifacts/TCK-*VISUAL-ASSETS*/` is git-ignored and has no TRACKED `<name>.txt` twin. On a clean checkout there are no ignored files, so it passes trivially there; it bites on the machine
that produced the evidence. The shared `.gitignore` rule is codebase-wide and deliberately not changed here.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GLOB = "agent-working/stored_artifacts/TCK-*VISUAL-ASSETS*/*"


def _git(repo: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout
    return [line for line in out.split("\n") if line]


def ignored_evidence(repo: Path) -> list[str]:
    """Git-ignored files (untracked, matched by an ignore rule) under a visual-asset ticket's stored artifacts, as repo-relative paths."""
    found = _git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "--", "agent-working/stored_artifacts")
    return sorted(f for f in found if fnmatch.fnmatch(f, GLOB))


def missing_twins(repo: Path) -> list[str]:
    """Ignored evidence files that have no tracked `<name>.txt` twin."""
    tracked = set(_git(repo, "ls-files"))
    return [f for f in ignored_evidence(repo) if f + ".txt" not in tracked]


def test_every_ignored_evidence_file_of_a_visual_asset_ticket_has_a_tracked_txt_twin():
    assert missing_twins(REPO) == [], "commit a `<name>.txt` copy beside each of these (never edit or move the original)"


def test_each_twin_is_byte_identical_to_the_original_it_copies():
    for original in ignored_evidence(REPO):
        assert (REPO / (original + ".txt")).read_bytes() == (REPO / original).read_bytes(), original


# ---- the guard itself, on a scratch repository (a planted ignored .json must fail it) -------------------------------------------------------------

def scratch(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".gitignore").write_text("agent-working/stored_artifacts/**/*.json\n")
    return repo


def put(repo: Path, rel: str, text: str = "{}") -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def add(repo: Path, *rels: str) -> None:
    subprocess.run(["git", "add", "-f", *rels], cwd=repo, check=True)


def test_a_planted_ignored_json_without_a_twin_fails_the_guard(tmp_path):
    repo = scratch(tmp_path)
    put(repo, "agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/blind_check/answers.json")
    assert missing_twins(repo) == ["agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/blind_check/answers.json"]


def test_a_tracked_twin_satisfies_the_guard_and_an_untracked_twin_does_not(tmp_path):
    repo = scratch(tmp_path)
    original = "agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/result.json"
    put(repo, original)
    put(repo, original + ".txt")
    assert missing_twins(repo) == [original]  # the twin exists but is not tracked
    add(repo, original + ".txt")
    assert missing_twins(repo) == []


def test_files_of_other_tickets_and_files_that_are_not_ignored_are_out_of_scope(tmp_path):
    repo = scratch(tmp_path)
    put(repo, "agent-working/stored_artifacts/TCK-20261009-SOMETHING-ELSE/result.json")  # another subsystem: not ours to police
    put(repo, "agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/notes.md", "# ok")  # not ignored
    put(repo, "agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/result.json.txt")  # a twin without an original
    assert ignored_evidence(repo) == [] and missing_twins(repo) == []


def test_an_ignored_file_in_a_nested_folder_is_found(tmp_path):
    repo = scratch(tmp_path)
    nested = "agent-working/stored_artifacts/TCK-20261009-VISUAL-ASSETS-X/captures/chrome-dpr1/evidence.json"
    put(repo, nested)
    assert missing_twins(repo) == [nested]
