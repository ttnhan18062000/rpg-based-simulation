"""tools/agent-monitoring/batch_latency.py: the batch-latency triplet, derived with no batch registry
(TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT; plan section 11: "never PR green = done").

  implementation latency = dispatch -> PR green
  finalization latency   = PR green -> finalized
  batch cycle time       = dispatch -> finalized

Timestamps come from existing artifacts only, and each one that is not available is `unknown`, NEVER zero:
  dispatch   `--dispatch-ts` if given (the planner's message time, owner supplied), else the first commit of the
             batch on its PR (a proxy: the dispatch message itself leaves no repo artifact)
  PR green   the latest completion time among the PR head's checks, only when every examined check finished and
             none failed (SUCCESS/SKIPPED/NEUTRAL); otherwise unknown
  finalized  the PR's `mergedAt` (the ticket reaches `agent-working/tickets/done/` on the default branch only
             then; closing the ticket inside the PR is not finalization). A PR not yet merged is unknown.
Negative spans are reported as `unknown`: a clock or artifact mix-up must not read as a latency.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime

UNKNOWN = "unknown"
_OK_CONCLUSIONS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


def _parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def pr_green_ts(checks: list[dict]) -> str | None:
    """The latest check completion if the rollup is non-empty, finished and green, else None."""
    if not checks:
        return None
    stamps = []
    for c in checks:
        done = c.get("completedAt") or ""
        state = c.get("conclusion") or c.get("state") or ""
        if not done or done.startswith("0001") or str(state).upper() not in _OK_CONCLUSIONS:
            return None
        stamps.append(done)
    return max(stamps, key=lambda s: _parse(s))


def _span(start, end) -> str | float:
    a, b = _parse(start), _parse(end)
    if a is None or b is None or b < a:
        return UNKNOWN
    return (b - a).total_seconds()


def latencies(dispatch_ts, green_ts, finalized_ts) -> dict:
    """Seconds for each of the three measures, or `unknown`."""
    return {
        "dispatch_ts": dispatch_ts or UNKNOWN, "pr_green_ts": green_ts or UNKNOWN, "finalized_ts": finalized_ts or UNKNOWN,
        "implementation_s": _span(dispatch_ts, green_ts),
        "finalization_s": _span(green_ts, finalized_ts),
        "cycle_s": _span(dispatch_ts, finalized_ts),
    }


def from_pr(pr: dict, dispatch_ts: str | None = None) -> dict:
    """The triplet from a `gh pr view --json commits,mergedAt,statusCheckRollup` object."""
    commits = pr.get("commits") or []
    first = min((c.get("committedDate") for c in commits if c.get("committedDate")), key=_parse, default=None)
    out = latencies(dispatch_ts or first, pr_green_ts(pr.get("statusCheckRollup") or []), pr.get("mergedAt"))
    out["dispatch_source"] = "given" if dispatch_ts else ("first_commit" if first else UNKNOWN)
    return out


def fetch_pr(number: int, repo: str | None = None) -> dict:
    cmd = ["gh", "pr", "view", str(number), "--json", "commits,mergedAt,statusCheckRollup,headRefName"]
    if repo:
        cmd += ["--repo", repo]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout)


def fmt(seconds) -> str:
    if seconds == UNKNOWN:
        return UNKNOWN
    s = int(seconds)
    return f"{s // 3600}h{(s % 3600) // 60:02d}m{s % 60:02d}s"


def render_row(label: str, result: dict) -> str:
    return (f"| {label} | {fmt(result['implementation_s'])} | {fmt(result['finalization_s'])} | "
            f"{fmt(result['cycle_s'])} | {result['dispatch_source']} |")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Batch latency triplet for merged PRs (derived; no batch registry)")
    parser.add_argument("prs", nargs="+", type=int)
    parser.add_argument("--dispatch-ts", help="ISO timestamp of the dispatch (applies to every PR given)")
    parser.add_argument("--repo")
    args = parser.parse_args(argv)
    print("| batch | implementation | finalization | cycle | dispatch from |\n|---|---|---|---|---|")
    for n in args.prs:
        try:
            print(render_row(f"#{n}", from_pr(fetch_pr(n, args.repo), args.dispatch_ts)))
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            print(f"| #{n} | unknown | unknown | unknown | unavailable: {type(exc).__name__} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
