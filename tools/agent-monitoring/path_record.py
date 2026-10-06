#!/usr/bin/env python3
"""Which phases a tier plans but a run's record does not contain (run field `phases_omitted`).

TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD. A phase that was never logged cannot be told from one that never
ran, so the writers derive the omitted list at write time from the workflow's own per-tier plan
(`agent-working/agent-orchestration/workflows/implement-ticket.yaml`), never from a hard-coded copy. Only phases the
plan marks `full` for the tier count: `conditional` phases, `skipped_event` phases and tiers the file does not list
(epic, n/a) are never omitted.

CLI (used by implement-ticket.js's run write):
    python3 tools/agent-monitoring/path_record.py --tier standard --phases Scope,Implement,Test
prints the JSON list, e.g. ["Investigate", ...]. A missing or unreadable plan prints [] and exits 0 (fail-open).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))
from tools.agent_working_paths import AGENT_ORCHESTRATION  # noqa: E402

WORKFLOW_PLAN_PATH = _REPO_ROOT / AGENT_ORCHESTRATION / "workflows" / "implement-ticket.yaml"
FULL = "full"


def full_phases(tier: str, plan_path: Path = WORKFLOW_PLAN_PATH) -> list[str]:
    """Phases the plan marks `full` for `tier`, in plan order; [] for a tier the plan does not list."""
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    return [p["name"] for p in plan.get("phases", []) if (p.get("tiers") or {}).get(tier) == FULL]


def phases_omitted(tier: str, recorded_phases, plan_path: Path = WORKFLOW_PLAN_PATH) -> list[str] | None:
    """`full` phases of `tier` with no event in `recorded_phases`. None when the plan cannot be read, so a caller
    leaves the field off rather than writing a false `[]`."""
    try:
        planned = full_phases(tier, plan_path)
    except (OSError, ValueError, KeyError, AttributeError, yaml.YAMLError):
        return None
    seen = set(recorded_phases)
    return [phase for phase in planned if phase not in seen]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tier", required=True)
    parser.add_argument("--phases", default="", help="comma-separated phases that have an event")
    args = parser.parse_args()
    omitted = phases_omitted(args.tier, [p for p in args.phases.split(",") if p])
    print(json.dumps(omitted if omitted is not None else []))


if __name__ == "__main__":
    main()
