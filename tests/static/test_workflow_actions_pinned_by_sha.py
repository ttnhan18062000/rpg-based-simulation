"""Every `uses:` in every workflow under .github/workflows is a full commit SHA plus a `# vX.Y.Z` comment.

TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA, widened by TCK-20261020-WORKFLOW-PIN-GUARD-COVERS-EVERY-WORKFLOW
from testing's four files to a glob of the directory. A mutable tag lets an action's owner change what runs in
our CI. Dependabot (github-actions, grouped, monthly) keeps the pins current. Local `./` actions are exempt.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
WORKFLOWS = tuple(sorted(p.name for p in WORKFLOW_DIR.glob("*.y*ml")))
TESTING_WORKFLOWS = ("test.yml", "slow-regression.yml", "slow-regression-watchdog.yml", "rpg-gate-report.yml", "paired-arms.yml")
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


def _uses_in(node) -> list:
    """Every `uses` value in a parsed workflow, wherever it sits (block or flow style)."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_uses_in(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_uses_in(item))
    return found


def test_the_glob_finds_the_testing_workflows():
    """An empty or shrunken glob must not pass: the parametrized test below would then check nothing."""
    assert set(TESTING_WORKFLOWS) <= set(WORKFLOWS)


@pytest.mark.parametrize("name", WORKFLOWS)
def test_every_action_is_pinned_by_sha_with_a_version_comment(name):
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    assert unpinned(text) == []


@pytest.mark.parametrize("name", WORKFLOWS)
def test_the_line_scan_sees_every_uses_key_the_yaml_parser_sees(name):
    """Closes the flow-style gap: a `uses` the line regex cannot see (e.g. `{uses: x@v1}`) is a count mismatch."""
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    parsed = _uses_in(yaml.safe_load(text))
    scanned = [line for line in text.splitlines() if USES.match(line)]
    assert len(parsed) == len(scanned)


def test_the_count_check_notices_a_flow_style_uses():
    text = "jobs:\n  a:\n    steps:\n      - {uses: actions/checkout@v7}\n"
    assert len(_uses_in(yaml.safe_load(text))) == 1
    assert [line for line in text.splitlines() if USES.match(line)] == []


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
