#!/usr/bin/env python3
"""Per-tier reading of how tickets took their path and which planned phases they carry
(TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO, child 2 of TCK-20261006-EPIC-TICKET-PATH-RECORD).

A phase that was never logged cannot be told from one that never ran, so a run now records `path_reason` and
`phases_omitted` and a skipped event records `skip_reason` (TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD). This reads
them back, per tier and `execution_mode`: the `path_reason` mix, and for every planned phase how many runs ran it, skipped it,
omitted it, or never had it because it is conditional. Report only: nothing here routes a ticket or changes a tier.

A run from before the fields existed is counted under "predates the fields" and never as `unstated`, so old rows cannot
pass for a habit of not saying why. The routing line names a phase only when the reading is firm enough to act on:
skipped or omitted in at least 80% of the runs that carry the fields, at least 10 such runs, and an `unstated` `path_reason`
share of at most 25%. Otherwise it says why not. The three thresholds are starting values, to be changed at a retro.

    python3 tools/agent-monitoring/path_report.py [--week YYYY-Www]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import path_record  # noqa: E402

SKIPPED_OR_OMITTED_SHARE = 0.80
MIN_RUNS = 10
MAX_UNSTATED_SHARE = 0.25
WORKFLOW = "implement-ticket"
UNLABELLED = "unlabelled"


def has_path_fields(run: dict) -> bool:
    return "path_reason" in run or "phases_omitted" in run


def planned_phases(tier: str, plan_path: Path = path_record.WORKFLOW_PLAN_PATH) -> list[tuple[str, str]]:
    """(phase, tier_behavior) for each phase the plan lists for `tier` (`full`, `conditional` or `skipped_event`)."""
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    return [(p["name"], p["tiers"][tier]) for p in plan.get("phases", []) if (p.get("tiers") or {}).get(tier)]


def _events_by_run(events: list[dict]) -> dict:
    by_run = defaultdict(list)
    for e in events:
        by_run[(e.get("run_id"), e.get("execution_id"))].append(e)
        by_run[(e.get("run_id"), None)].append(e)  # a record that carries no execution_id
    return by_run


def _share(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def analyze(runs: list[dict], events: list[dict], plan_path: Path = path_record.WORKFLOW_PLAN_PATH) -> list[dict]:
    """One group per (tier, execution_mode) over the implement-ticket runs, in a stable order."""
    by_run = _events_by_run(events)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for run in runs:
        if run.get("workflow") != WORKFLOW:
            continue
        buckets[(run.get("tier") or "unknown", run.get("execution_mode") or UNLABELLED)].append(run)
    groups = []
    for (tier, mode), group_runs in sorted(buckets.items()):
        with_fields = [r for r in group_runs if has_path_fields(r)]
        try:
            plan = planned_phases(tier, plan_path)
        except (OSError, ValueError, KeyError, yaml.YAMLError):
            plan = []
        phases = {name: {"behavior": behavior, "ran": 0, "skipped": 0, "omitted": 0, "conditional_absent": 0, "skip_reasons": Counter()}
                  for name, behavior in plan}
        for run in with_fields:
            run_events = by_run.get((run.get("run_id"), run.get("execution_id"))) or by_run.get((run.get("run_id"), None)) or []
            omitted = set(run.get("phases_omitted") or [])
            for name, row in phases.items():
                phase_events = [e for e in run_events if e.get("phase") == name]
                if any(e.get("status") != "skipped" for e in phase_events):
                    row["ran"] += 1
                elif phase_events:
                    row["skipped"] += 1
                    row["skip_reasons"].update(e.get("skip_reason") or "unstated" for e in phase_events if e.get("status") == "skipped")
                elif name in omitted:
                    row["omitted"] += 1
                elif row["behavior"] == "conditional":
                    row["conditional_absent"] += 1
        groups.append({
            "tier": tier, "execution_mode": mode, "runs": len(group_runs), "predates": len(group_runs) - len(with_fields),
            "with_fields": len(with_fields),
            "path_reasons": Counter(r.get("path_reason") or "unstated" for r in with_fields),
            "phases": phases,
        })
    return groups


def routing(group: dict) -> tuple[list[str], list[str]]:
    """(candidate phases, one reason line per phase held back). A phase is held back when it is skipped or omitted in enough
    runs but the sample is too small or too much of it is `unstated`; a phase below the share is not mentioned."""
    n = group["with_fields"]
    unstated = _share(group["path_reasons"].get("unstated", 0), n)
    candidates, held = [], []
    for name, row in group["phases"].items():
        absent = row["skipped"] + row["omitted"]
        if not n or _share(absent, n) < SKIPPED_OR_OMITTED_SHARE:
            continue
        if n < MIN_RUNS:
            held.append(f"`{name}`: skipped or omitted in {absent} of {n} runs, but fewer than {MIN_RUNS} runs carry the fields")
        elif unstated > MAX_UNSTATED_SHARE:
            held.append(f"`{name}`: skipped or omitted in {absent} of {n} runs, but `unstated` is {round(100 * unstated)}% of "
                        f"`path_reason` (above {round(100 * MAX_UNSTATED_SHARE)}%)")
        else:
            candidates.append(name)
    return candidates, held


def _mix(counter: Counter) -> str:
    return ", ".join(f"{k} {v}" for k, v in counter.most_common()) or "-"


def render_section(runs: list[dict], events: list[dict], total_field_runs: int | None = None) -> str:
    """The retro's `## Paths` section. `total_field_runs` is the count of runs in any week that carry the fields: 0 means
    the instrument is not running (zeros would mean nothing); rows without them in this period read as "predates"."""
    lines = ["## Paths", "",
             "_How implement-ticket runs took their path, from `path_reason`, `phases_omitted` and `skip_reason` "
             "(`tools/agent-monitoring/path_report.py`). Report only: nothing here routes a ticket or changes a tier. "
             "A run from before the fields is counted as \"predates\", never as `unstated`._", ""]
    groups = analyze(runs, events)
    if total_field_runs == 0:
        lines += ["_Instrument not running: no run in any week carries `path_reason` or `phases_omitted`. "
                  "Zeros below would be meaningless, so the phase tables are omitted._", ""]
        if groups:
            lines += ["| tier | execution_mode | runs | predate the fields |", "|---|---|---|---|"]
            lines += [f"| {g['tier']} | {g['execution_mode']} | {g['runs']} | {g['predates']} |" for g in groups]
            lines += ["", "No routing candidate: no run carries the fields yet.", ""]
        return "\n".join(lines)
    if not groups:
        outside = f" ({total_field_runs} runs outside this period carry the fields)" if total_field_runs else ""
        return "\n".join(lines + [f"_No implement-ticket runs this period{outside}._", ""])
    for g in groups:
        lines += [f"### {g['tier']} · {g['execution_mode']}", "",
                  f"{g['runs']} runs; {g['predates']} predate the fields; {g['with_fields']} carry them. "
                  f"`path_reason`: {_mix(g['path_reasons'])}.", ""]
        if g["with_fields"]:
            lines += ["| phase | plan | ran | skipped | omitted | conditional absent | skip_reason |", "|---|---|---|---|---|---|---|"]
            for name, row in g["phases"].items():
                lines.append(f"| {name} | {row['behavior']} | {row['ran']} | {row['skipped']} | {row['omitted']} | "
                             f"{row['conditional_absent']} | {_mix(row['skip_reasons'])} |")
            lines.append("")
        candidates, held = routing(g)
        if candidates:
            lines.append("Routing candidates: " + ", ".join(f"`{c}`" for c in candidates) + ".")
        elif held:
            lines.append("No routing candidate.")
        else:
            lines.append(f"No routing candidate: no phase is skipped or omitted in {round(100 * SKIPPED_OR_OMITTED_SHARE)}% "
                         f"of the {g['with_fields']} run(s) that carry the fields." if g["with_fields"]
                         else "No routing candidate: no run in this group carries the fields yet.")
        lines += [f"- {h}" for h in held] + [""]
    return "\n".join(lines + [f"_Routing needs {round(100 * SKIPPED_OR_OMITTED_SHARE)}% of runs, at least {MIN_RUNS} runs "
                              f"carrying the fields, and `unstated` at most {round(100 * MAX_UNSTATED_SHARE)}% of `path_reason`._", ""])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--week", help="ISO week YYYY-Www of the run start; default all weeks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    import generate_retro  # noqa: PLC0415 - heavy import, only the CLI needs it
    from run_dedup import dedupe_to_latest_per_execution  # noqa: PLC0415

    all_runs, all_events = generate_retro._load_runs_and_events()
    all_runs = dedupe_to_latest_per_execution(all_runs)
    runs = [r for r in all_runs if not args.week or generate_retro.iso_week(r.get("start_ts", "")) == args.week]
    run_ids = {r.get("run_id") for r in runs}
    events = [e for e in all_events if e.get("run_id") in run_ids]
    print(render_section(runs, events, sum(1 for r in all_runs if has_path_fields(r))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
