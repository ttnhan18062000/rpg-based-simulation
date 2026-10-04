"""D10 guard (ADR D10, docs/assets/aseprite_licence_review.md): Aseprite never runs on a hosted runner.

Fails if a workflow line other than a comment or the two allowed summary lines names Aseprite (install, download,
build, cache, `uses:` and cache keys all name it), or if a tracked file is an Aseprite executable or package
(`*.deb`, `*.AppImage`, an ELF named `aseprite*`). The checkers are pure functions over text/paths so the same code
that guards the real tree is proven against planted violations. No Aseprite needed; runs in CI.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"

# The only non-comment workflow lines allowed to name the editor: the skip-summary step (ADR D10).
ALLOWED_LINES = (
    re.compile(r'- name: "Note: needs_aseprite skips \(ADR D10\)"'),
    re.compile(r'run: python3 tools/ci_aseprite_skip_line\.py \S+ >> "\$GITHUB_STEP_SUMMARY"'),
)
PACKAGE_SUFFIXES = (".deb", ".appimage")
ELF_MAGIC = b"\x7fELF"


def workflow_violations(name: str, text: str) -> list[str]:
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or "aseprite" not in stripped.lower():
            continue
        if any(rule.fullmatch(stripped) for rule in ALLOWED_LINES):
            continue
        found.append(f"{name}:{number}: {stripped}")
    return found


def tracked_file_violations(path: str, head: bytes) -> list[str]:
    lower = path.lower()
    base = lower.rsplit("/", 1)[-1]
    if lower.endswith(PACKAGE_SUFFIXES):
        return [f"{path}: an Aseprite-style package"]
    if base.startswith("aseprite") and head.startswith(ELF_MAGIC):
        return [f"{path}: an Aseprite executable"]
    return []


def test_no_workflow_installs_downloads_builds_or_caches_aseprite():
    found = []
    for workflow in sorted(WORKFLOWS.glob("*.y*ml")):
        found += workflow_violations(workflow.name, workflow.read_text())
    assert not found, "Aseprite named in a workflow (ADR D10):\n" + "\n".join(found)


def test_no_tracked_file_is_an_aseprite_executable_or_package():
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True).stdout.decode()
    found = []
    for path in filter(None, tracked.split("\0")):
        file = REPO / path
        if not file.is_file() or file.is_symlink():
            continue
        lower = path.lower()
        needs_head = lower.rsplit("/", 1)[-1].startswith("aseprite")
        head = file.read_bytes()[:4] if needs_head else b""
        found += tracked_file_violations(path, head)
    assert not found, "\n".join(found)


def test_planted_install_lines_are_caught():
    for line in (
        "run: sudo apt-get install -y aseprite",
        "uses: someone/setup-aseprite@v1",
        "key: aseprite-${{ runner.os }}",
        "run: wget https://example.org/Aseprite-v1.3.AppImage",
        'run: python3 tools/ci_aseprite_skip_line.py x >> "$GITHUB_STEP_SUMMARY" && apt install aseprite',
        "run: apt install aseprite # tools/ci_aseprite_skip_line.py",
    ):
        assert workflow_violations("w.yml", f"steps:\n  - {line}\n"), line


def test_comments_and_the_skip_summary_lines_are_allowed():
    text = "\n".join(
        [
            "      # the real-Aseprite tests skip here (ADR D10)",
            '      - name: "Note: needs_aseprite skips (ADR D10)"',
            '        run: python3 tools/ci_aseprite_skip_line.py reports/junit/x.xml >> "$GITHUB_STEP_SUMMARY"',
        ]
    )
    assert workflow_violations("w.yml", text) == []


def test_planted_binaries_and_packages_are_caught():
    assert tracked_file_violations("tools/aseprite_1.3.deb", b"")
    assert tracked_file_violations("x/Aseprite.AppImage", b"")
    assert tracked_file_violations("bin/aseprite", b"\x7fELF")
    assert not tracked_file_violations("bin/aseprite", b"#!/b")  # a script, not the editor
    assert not tracked_file_violations("visual_assets/store/intake/aseprite.py", b"")
