"""Path routing for the dedicated CI scenario lane (roadmap D-R2).

A changed path is one of: `trigger` (src/**, a known scenario dependency, or the scenario tests
themselves), `irrelevant` (listed explicitly, with evidence in the ticket's investigation.md), or
`unknown` (anything else). Unknown paths fail open: they run the lane and are named in the summary.

Limits of the irrelevant list: it is a rule over path prefixes, not a record of what scenarios read. A
new file inside an excluded prefix (for example a new `tools/` module) is irrelevant by rule, not
unknown, so it never fails open. `tests/unit/tools/test_scenario_lane_exclusions.py` guards that
assumption: scenario-reachable code (src/, tests/mechanic_scenarios/, tests/helpers/, tests/conftest.py)
must not import top-level `tools` or name a path under an irrelevant prefix. If a dependency appears, move
that prefix out of the irrelevant list instead of extending the test's allowlist.

The summary reports routing only ("routed to ..."); whether a job ran, and its outcome, is that job's result.

The lane runs when any path is a trigger or unknown, and also when the path list is empty or this
script errors (fail open, same shape as the existing changed-files step).

Run: `python3 -m tools.test_architecture.scenario_lane_paths [--perf-covers true|false]` with the
changed paths on stdin, one per line. Prints `run_scenario_lane=<bool>` on the first line and a
markdown summary after it; the workflow splits them.
"""

import argparse
import re
import sys
from typing import Dict, Iterable, List

TRIGGER_RE = re.compile(
    r"^(src/"
    r"|tests/mechanic_scenarios/"
    r"|tests/helpers/"
    r"|tests/tools/"
    r"|tests/conftest\.py$"
    r"|tests/__init__\.py$"
    r"|tests/integration/kernel/test_determinism_suite\.py$"
    r"|data/content/"
    r"|data/worlds/"
    r"|config/simulation_quality/"
    r"|requirements\.txt$|pyproject\.toml$|uv\.lock$|Makefile$"
    r"|\.github/workflows/test\.yml$)"
)

IRRELEVANT_RE = re.compile(
    r"^(docs/|tickets/|agent-monitoring/|agent-orchestration/|stored_artifacts/|staging_artifacts/"
    r"|frontend/|dashboard-frontend/|website/|grafana/|reviews/|experiments/|registries/|tools/"
    r"|pilot_requests/|skills-lock\.json$|[^/]+\.md$)"
)


def classify(paths: Iterable[str]) -> Dict[str, object]:
    matched: List[str] = []
    unknown: List[str] = []
    irrelevant: List[str] = []
    for raw in paths:
        p = raw.strip()
        if not p:
            continue
        if TRIGGER_RE.match(p):
            matched.append(p)
        elif IRRELEVANT_RE.match(p):
            irrelevant.append(p)
        else:
            unknown.append(p)
    run = bool(matched or unknown)
    return {"run": run, "matched": matched, "unknown": unknown, "irrelevant": irrelevant}


def render_summary(result: Dict[str, object], perf_covers: bool) -> str:
    if result["run"]:
        # A routing statement, not an execution record: whether the job ran, and its outcome, is that job's own result.
        state = (
            "routed to perf-cert-arena; scenario execution is that job's result"
            if perf_covers
            else "routed to the scenario-lane job; scenario execution is that job's result"
        )
    else:
        state = "skipped: no changed path is a scenario trigger or unknown"
    out = [f"### Scenario lane: {state}", ""]
    for key, title in (("matched", "Matched trigger paths"), ("unknown", "Unknown paths (fail open)"),
                       ("irrelevant", "Known-irrelevant paths")):
        items = result[key]
        out.append(f"- {title}: {len(items)}")  # type: ignore[arg-type]
        out.extend(f"  - `{p}`" for p in list(items)[:20])  # type: ignore[call-overload]
        if len(items) > 20:  # type: ignore[arg-type]
            out.append(f"  - ... and {len(items) - 20} more")  # type: ignore[arg-type]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perf-covers", default="false", choices=["true", "false"])
    args = ap.parse_args(argv)
    try:
        result = classify(sys.stdin.read().splitlines())
        # An empty list (e.g. an empty diff) has no evidence either way: fail open.
        if not (result["matched"] or result["unknown"] or result["irrelevant"]):
            result["run"] = True
        print(f"run_scenario_lane={'true' if result['run'] else 'false'}")
        print(render_summary(result, args.perf_covers == "true"))
    except Exception as exc:  # fail open: the lane runs if classification errors
        print("run_scenario_lane=true")
        print(f"### Scenario lane: classifier error, failing open ({exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
