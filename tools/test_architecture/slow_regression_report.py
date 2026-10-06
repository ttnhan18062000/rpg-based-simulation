"""Keep one rolling GitHub issue for the `Slow regression` workflow's failing set.

Built for TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (Reporting-Path Design, P2).
Reads the JUnit XML the three slow steps write, computes the failing set, compares it with the set
recorded in the open `slow-regression` issue (a fenced JSON block in the body), and comments ONLY
when the set changes: `NEW: ...` / `FIXED: ...`. Known reds are not suppressed, they are just not
new; `slow_known_reds.yaml` maps test ids to the tickets that own them so an unmapped red shows as
UNOWNED. Recommendation/reporting only: it never fails the workflow on a red test.

Rules:
- A test is red when its JUnit testcase has a `<failure>` or `<error>` child. A strict XPASS is
  recorded by pytest as a failure, so it counts. `<skipped>` (skip and xfail) is not red.
- First run (no open issue): create the issue with the full current set and post NO per-test
  comments.
- A step that produced no JUnit file is "missing": its previously recorded failures are carried
  over (not reported FIXED) and the issue is not closed, because an empty set would be unproven.
- An id in the known-reds mapping that is not failing is listed as a "stale mapping" in the body.

GitHub access goes through a small client object (`GhClient` shells out to the `gh` CLI), so the
logic is tested with a fake client.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import yaml

LABEL = "slow-regression"
STEP_BY_FILE_PREFIX = (
    ("corpus_", "corpus diversity"),
    ("slow_tests", "slow tests"),
    ("legacy_regression", "legacy regression"),
)
EXPECTED_STEPS = tuple(step for _, step in STEP_BY_FILE_PREFIX)
_STATE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def step_for_file(name: str) -> Optional[str]:
    for prefix, step in STEP_BY_FILE_PREFIX:
        if name.startswith(prefix):
            return step
    return None


def parse_junit_dir(junit_dir: Path) -> Tuple[Dict[str, str], Set[str]]:
    """Return ({test id: step} for every red test, steps that produced at least one file)."""
    failing: Dict[str, str] = {}
    seen: Set[str] = set()
    for path in sorted(Path(junit_dir).glob("*.xml")):
        step = step_for_file(path.name)
        if step is None:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue  # a truncated file proves nothing: the step stays "missing"
        seen.add(step)
        for case in root.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                failing[f"{case.get('classname', '')}::{case.get('name', '')}"] = step
    return failing, seen


def load_known_reds(path: Optional[Path]) -> List[dict]:
    if path is None or not Path(path).exists():
        return []
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return list(data.get("known_reds", []))


def owner_of(test_id: str, known: Sequence[dict]) -> Optional[dict]:
    for entry in known:
        if fnmatch.fnmatchcase(test_id, entry["match"]):
            return entry
    return None


def stale_mappings(failing: Dict[str, str], known: Sequence[dict]) -> List[dict]:
    return [e for e in known if not any(fnmatch.fnmatchcase(t, e["match"]) for t in failing)]


def render_body(
    failing: Dict[str, str], known: Sequence[dict], repo: str, run_id: str, sha: str
) -> str:
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    lines = [f"Failing set of the `Slow regression` workflow, as of run [{run_id}]({run_url}) at `{sha[:12]}`.", ""]
    for step in EXPECTED_STEPS:
        ids = sorted(t for t, s in failing.items() if s == step)
        if not ids:
            continue
        lines.append(f"### {step} ({len(ids)})")
        for test_id in ids:
            entry = owner_of(test_id, known)
            owner = f"`{entry['ticket']}`" if entry else "**UNOWNED**"
            lines.append(f"- [{test_id}]({run_url}) — {owner}")
        lines.append("")
    stale = stale_mappings(failing, known)
    if stale:
        lines.append("### Stale mappings (mapped to a ticket but not failing; consider cleaning up)")
        lines.extend(f"- `{e['match']}` — `{e['ticket']}`" for e in stale)
        lines.append("")
    lines.append(f"Last seen: run [{run_id}]({run_url}) at `{sha[:12]}`.")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({"failing": dict(sorted(failing.items()))}, indent=1, sort_keys=True))
    lines.append("```")
    return "\n".join(lines)


def parse_state(body: str) -> Optional[Dict[str, str]]:
    match = _STATE_RE.search(body or "")
    if not match:
        return None
    try:
        return dict(json.loads(match.group(1)).get("failing", {}))
    except (ValueError, AttributeError):
        return None


def title_for(count: int) -> str:
    return f"Slow regression: {count} failing on main"


def run_report(
    client,
    failing: Dict[str, str],
    seen_steps: Set[str],
    known: Sequence[dict],
    repo: str,
    run_id: str,
    sha: str,
) -> str:
    """Apply one run's result to the rolling issue. Returns a one-line description of what was done."""
    issue = client.find_open_issue()
    missing = [s for s in EXPECTED_STEPS if s not in seen_steps]
    previous = parse_state(issue["body"]) if issue else None

    if previous is not None and missing:
        # Carry over what we cannot re-measure this run.
        for test_id, step in previous.items():
            if step in missing:
                failing = {**failing, test_id: step}

    if issue is None:
        if not failing:
            return "no open issue and nothing failing: nothing to do"
        client.create_issue(title_for(len(failing)), render_body(failing, known, repo, run_id, sha))
        return f"first run: created the issue with {len(failing)} failing, no per-test comments"

    body = render_body(failing, known, repo, run_id, sha)
    if previous is None:
        client.update_issue(issue["number"], title_for(len(failing)), body)
        return "issue state block unreadable: refreshed the body, no comments"

    new = sorted(set(failing) - set(previous))
    fixed = sorted(set(previous) - set(failing))
    comment_lines = []
    if new:
        comment_lines.append("NEW: " + ", ".join(f"`{t}` ({failing[t]})" for t in new))
    if fixed:
        comment_lines.append("FIXED: " + ", ".join(f"`{t}`" for t in fixed))
    if missing:
        comment_lines.append("Steps with no result this run: " + ", ".join(missing))
    changed = bool(new or fixed)
    if changed:
        comment_lines.append(f"Run {run_id}, head `{sha}`.")
        client.comment(issue["number"], "\n".join(comment_lines))

    if not failing and not missing:
        client.update_issue(issue["number"], title_for(0), body)
        client.close_issue(issue["number"])
        return "failing set is empty: closed the issue"
    client.update_issue(issue["number"], title_for(len(failing)), body)
    return "set changed: commented and refreshed" if changed else "set unchanged: refreshed 'last seen' only"


class GhClient:
    """The `gh` CLI as a client. Needs GH_TOKEN in the environment and `issues: write`."""

    def __init__(self, repo: str) -> None:
        self.repo = repo

    def _gh(self, *args: str) -> str:
        return subprocess.run(
            ["gh", *args, "--repo", self.repo], check=True, capture_output=True, text=True
        ).stdout

    def find_open_issue(self) -> Optional[dict]:
        self._gh("label", "create", LABEL, "--force", "--description", "Slow regression failing set")
        out = self._gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number,body", "--limit", "1")
        rows = json.loads(out or "[]")
        return rows[0] if rows else None

    def create_issue(self, title: str, body: str) -> None:
        self._gh("issue", "create", "--title", title, "--body", body, "--label", LABEL)

    def update_issue(self, number: int, title: str, body: str) -> None:
        self._gh("issue", "edit", str(number), "--title", title, "--body", body)

    def comment(self, number: int, text: str) -> None:
        self._gh("issue", "comment", str(number), "--body", text)

    def close_issue(self, number: int) -> None:
        self._gh("issue", "close", str(number), "--comment", "Failing set is empty.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--junit-dir", required=True, type=Path)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--known-reds", type=Path, default=None)
    args = ap.parse_args(argv)

    failing, seen = parse_junit_dir(args.junit_dir)
    known = load_known_reds(args.known_reds)
    try:
        message = run_report(GhClient(args.repo), failing, seen, known, args.repo, args.run_id, args.sha)
    except (subprocess.CalledProcessError, OSError) as exc:
        # Reporting is informational: a GitHub failure must not turn the run's own result into a different one.
        print(f"slow_regression_report: could not update the issue: {exc}", file=sys.stderr)
        return 0
    print(f"slow_regression_report: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
