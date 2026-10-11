"""The rpg gate report's rolling GitHub issue, kept the way the slow report keeps #390.

TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW (child 5 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). One open issue carries the label
``rpg-gate-report`` (separate from #390's ``slow-regression``) and a marker. Only the scheduled run on main calls this module; a dispatch run on a branch writes
the step summary and artifacts, never the issue.

What is tracked: every ``fail``, ``drift`` and ``unstable`` finding, every ``run_error`` (an rpg defect), and one synthetic entry ``rpg-metric-module-absent`` while
rpg's metric module cannot be imported (so the issue exists and says so plainly during the phase before rpg's module lands). A run that changes the tracked set
comments ``NEW: ...`` / ``RESOLVED: ...``; an unchanged set only refreshes the body ("last seen"); an empty set closes the issue; the first run creates it with no
comments. The issue is advisory: this module never decides the job's verdict (the report's verdict does).

CLI::

    python -m tools.test_architecture.rpg_gate_issue --report FILE --repo OWNER/NAME --run-id ID --sha SHA
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from tools.test_architecture.rpg_gate_report import metric_test_id, render_markdown
from tools.test_architecture.slow_regression_report import BOT_LOGIN, GhClient, TrackerError

LABEL = "rpg-gate-report"
TRACKER_MARKER = "<!-- rpg-gate-report-tracker -->"
MODULE_ABSENT_ID = "rpg-metric-module-absent"
_STATE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)
TRACKED_STATES = ("fail", "drift", "unstable")


def finding_label(f: Mapping[str, Any]) -> str:
    where = f"{f['world']}/{f['seed']}" if f.get("seed") is not None else f["world"]
    return f"{metric_test_id(f)} [{where}]"


def tracked(report: Mapping[str, Any]) -> Dict[str, str]:
    """``label -> state`` of everything the issue follows for this report."""
    out = {finding_label(f): f["state"] for f in report["findings"] if f["state"] in TRACKED_STATES}
    for f in report["findings"]:
        if f.get("reason") == "run_error":
            out[f"run_error {f['world']}/{f.get('seed')}"] = "run_error"
    if report.get("module_absent"):
        out[MODULE_ABSENT_ID] = "module-absent"
    return out


def render_body(report: Mapping[str, Any], run_id: str, sha: str, repo: str) -> str:
    state = {"tracked": tracked(report)}
    return "\n".join([
        TRACKER_MARKER,
        f"Latest scheduled run: [{run_id}](https://github.com/{repo}/actions/runs/{run_id}), head `{sha}`. Advisory: this report is not a required check.",
        "",
        render_markdown(report),
        "```json",
        json.dumps(state, sort_keys=True, indent=2),
        "```",
    ])


def parse_state(body: str) -> Optional[Dict[str, str]]:
    match = _STATE_RE.search(body or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except ValueError:
        return None
    return dict(data["tracked"]) if isinstance(data, dict) and isinstance(data.get("tracked"), dict) else None


def title_for(count: int) -> str:
    return f"rpg gate report: {count} item(s) to look at on main"


def select_tracker(issues: Sequence[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    marked = [i for i in issues if i.get("user_login") == BOT_LOGIN and LABEL in (i.get("labels") or []) and TRACKER_MARKER in (i.get("body") or "")]
    if len(marked) > 1:
        raise TrackerError("more than one open rpg gate tracker issue carries the marker: " + ", ".join(f"#{i['number']}" for i in marked))
    return marked[0] if marked else None


def run_issue(client, report: Mapping[str, Any], run_id: str, sha: str, repo: str) -> str:
    """Apply one scheduled run's report to the rolling issue and say what was done."""
    now_tracked = tracked(report)
    body = render_body(report, run_id, sha, repo)
    issue = select_tracker(client.list_issues())
    if issue is None:
        if not now_tracked:
            return "no open tracker issue and nothing to track: nothing to do"
        client.create_issue(title_for(len(now_tracked)), body)
        return f"first run: created the issue with {len(now_tracked)} tracked item(s), no comments"
    previous = parse_state(issue["body"])
    if previous is None:
        client.update_issue(issue["number"], title_for(len(now_tracked)), body)
        return "issue state block unreadable: refreshed the body, no comments"
    new = sorted(set(now_tracked) - set(previous))
    resolved = sorted(set(previous) - set(now_tracked))
    lines: List[str] = []
    if new:
        lines.append("NEW: " + ", ".join(f"`{t}` ({now_tracked[t]})" for t in new))
    if resolved:
        lines.append("RESOLVED: " + ", ".join(f"`{t}`" for t in resolved))
    if lines:
        lines.append(f"Run {run_id}, head `{sha}`.")
        client.comment(issue["number"], "\n".join(lines))
    if not now_tracked:
        client.update_issue(issue["number"], title_for(0), body)
        client.close_issue(issue["number"])
        return "nothing to track: closed the issue"
    client.update_issue(issue["number"], title_for(len(now_tracked)), body)
    return "set changed: commented and refreshed" if lines else "set unchanged: refreshed 'last seen' only"


def main(argv: Optional[Sequence[str]] = None, client_factory=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args(argv)
    client = (client_factory or (lambda repo: GhClient(repo, LABEL, "rpg gate report: items to look at")))(args.repo)
    print(run_issue(client, json.loads(args.report.read_text(encoding="utf-8")), args.run_id, args.sha, args.repo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
