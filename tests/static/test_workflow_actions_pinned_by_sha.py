"""Every `uses:` in testing's workflows is a full commit SHA plus a `# vX.Y.Z` comment.

TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA. A mutable tag lets an action's owner change what runs in
our CI. Dependabot (github-actions, grouped, monthly) keeps the pins current. Local `./` actions are exempt.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    "test.yml",
    "slow-regression.yml",
    "slow-regression-watchdog.yml",
    "rpg-gate-report.yml",
)
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?P<rest>.*)$")
PINNED = re.compile(r"^[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"^\s+#\s*v\d+(?:\.\d+)*\s*$")


def unpinned(text: str) -> list:
    """Return the `uses:` lines that are not `owner/repo@<40-hex> # vX.Y.Z` (local `./` actions excepted)."""
    bad = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = USES.match(line)
        if not match or match["ref"].startswith("./"):
            continue
        if not PINNED.match(match["ref"]) or not VERSION_COMMENT.match(match["rest"]):
            bad.append((number, line.strip()))
    return bad


@pytest.mark.parametrize("name", WORKFLOWS)
def test_every_action_is_pinned_by_sha_with_a_version_comment(name):
    text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
    assert unpinned(text) == []


def test_guard_flags_tags_branches_short_shas_and_missing_comments():
    sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
    snippet = "\n".join(
        [
            "      - uses: actions/checkout@v7",
            "      - uses: actions/checkout@main",
            f"      - uses: actions/checkout@{sha[:7]} # v7.0.1",
            f"      - uses: actions/checkout@{sha}",
            f"        uses: actions/upload-artifact@{sha} # latest",
        ]
    )
    assert len(unpinned(snippet)) == 5


def test_guard_accepts_a_pin_and_local_actions():
    sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
    snippet = f"      - uses: actions/checkout@{sha} # v7.0.1\n      - uses: ./.github/actions/x\n        uses: github/codeql-action/upload-sarif@{sha} # v4.38.3"
    assert unpinned(snippet) == []
