"""TCK-20261020-PR-BODY-LINT-PIN-CHECKOUT-BY-SHA: every `uses:` in pr-body-lint.yml (agent-working's workflow) is a full
commit SHA plus a `# vX.Y.Z` comment. testing's guard (tests/static/test_workflow_actions_pinned_by_sha.py, #675) covers
only testing's four workflows, so this one is guarded here.

The two regexes and `unpinned()` are copied from that file (testing owns it; importing from tests/static would couple two
suites); keep them in step with it. Local `./` actions are exempt."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-body-lint.yml"
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?P<rest>.*)$")
PINNED = re.compile(r"^[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"^\s+#\s*v\d+(?:\.\d+)*\s*$")
SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"


def unpinned(text: str) -> list:
    bad = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = USES.match(line)
        if not match or match["ref"].startswith("./"):
            continue
        if not PINNED.match(match["ref"]) or not VERSION_COMMENT.match(match["rest"]):
            bad.append((number, line.strip()))
    return bad


def test_pr_body_lint_pins_every_action_by_sha_with_a_version_comment():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "uses:" in text
    assert unpinned(text) == []


def test_the_guard_flags_a_mutable_tag_and_a_missing_comment_and_accepts_a_pin():
    assert unpinned("      - uses: actions/checkout@v7") == [(1, "- uses: actions/checkout@v7")]
    assert len(unpinned(f"      - uses: actions/checkout@{SHA}")) == 1
    assert unpinned(f"      - uses: actions/checkout@{SHA} # v7.0.1\n      - uses: ./.github/actions/x") == []
