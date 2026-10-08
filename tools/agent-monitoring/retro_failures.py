#!/usr/bin/env python3
"""The retro's `## Failures` section (TCK-20261007-RETRO-FAILURES-SECTION).

Every non-DONE run and every `failed`/`blocked` event of the period with its one-line summary, grouped by
agent and by cause, plus the tests that failed under two or more distinct tickets, so a recurring
pre-existing failure is visible without a throwaway script. Report only: it reads the lists it is given and
changes nothing; the known-failing-test baseline is an owner decision and is not made here.

Sibling module like `gate_ledger` / `path_report`: `generate_retro.py` calls it inside a try/except that
returns None, so it can never fail a retro. The predicates that define "failed run" and "agent" live in
`generate_retro.py`; they are passed in so this module never imports it (a cycle).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

FAILED_STATUSES = ("failed", "blocked")
SUMMARY_CAP = 160
NO_AGENT = "(no agent)"
UNSPECIFIED = "unspecified"
# No structured per-test field exists: names are parsed out of free-text summaries, which is lossy by construction.
_NODE_ID = re.compile(r"[\w./-]+\.py::([A-Za-z_][\w\[\]\-.:]*)")
_BARE_TEST = re.compile(r"\b(test_[A-Za-z0-9_]+)")


def one_line(text, cap: int = SUMMARY_CAP) -> str:
    flat = " ".join(str(text or "").split())
    return flat if len(flat) <= cap else flat[: cap - 1].rstrip() + "…"


def ticket_of(event: dict) -> str | None:
    """The ticket an event belongs to: its `ticket_id`, else its run_id when that is a ticket id."""
    tid = event.get("ticket_id")
    if isinstance(tid, str) and tid.startswith("TCK-"):
        return tid
    run_id = event.get("run_id")
    return run_id if isinstance(run_id, str) and run_id.startswith("TCK-") else None


def test_names(summary: str) -> list:
    """Test function names mentioned in a summary: node ids first (their last segment, parameters cut);
    a bare `test_*` word counts only when the summary has no node id."""
    names = []
    for match in _NODE_ID.finditer(summary or ""):
        names.append(re.split(r"\[", match.group(1).split("::")[-1].rstrip(".,;:)"))[0])
    if not names:
        names = [m.group(1) for m in _BARE_TEST.finditer(summary or "")]
    return sorted(set(n for n in names if n))


def recurring_tests(events: list, min_tickets: int = 2) -> list:
    """[(test name, [ticket ids])] for tests named in failed/blocked events of at least `min_tickets`
    distinct tickets, most tickets first then name."""
    tickets_by_test = defaultdict(set)
    for e in events:
        if e.get("status") not in FAILED_STATUSES:
            continue
        tid = ticket_of(e)
        if tid is None:
            continue
        for name in test_names(e.get("summary") or ""):
            tickets_by_test[name].add(tid)
    rows = [(n, sorted(t)) for n, t in tickets_by_test.items() if len(t) >= min_tickets]
    return sorted(rows, key=lambda row: (-len(row[1]), row[0]))


def render_section(runs: list, events: list, is_failed_run, agent_of, resolve_status=None) -> str:
    """`## Failures`. `runs` must already be the period's deduped latest-per-execution runs."""
    failed_runs = [r for r in runs if is_failed_run(r)]
    failed_events = [e for e in events if e.get("status") in FAILED_STATUSES]
    lines = ["## Failures", "",
             "_Non-DONE runs and failed or blocked events of this period (`tools/agent-monitoring/retro_failures.py`). "
             "Report only: nothing here suppresses a failure or sets a baseline._", ""]
    if not failed_runs and not failed_events:
        return "\n".join(lines + ["_No non-DONE runs and no failed or blocked events in this period._"])

    lines += [f"### Non-DONE runs ({len(failed_runs)})", ""]
    if failed_runs:
        for r in sorted(failed_runs, key=lambda r: (str(r.get("start_ts") or ""), str(r.get("run_id") or ""))):
            status = resolve_status(r) if resolve_status else (r.get("final_status") or r.get("status"))
            lines.append(f"- `{r.get('run_id')}` — {status} ({r.get('workflow') or 'unknown workflow'}, "
                         f"{str(r.get('start_ts') or 'no start')[:10]})")
    else:
        lines.append("_None._")
    lines.append("")

    lines += [f"### Failed and blocked events ({len(failed_events)})", ""]
    groups = defaultdict(lambda: defaultdict(list))
    for e in failed_events:
        groups[agent_of(e) or NO_AGENT][e.get("reason_code") or UNSPECIFIED].append(e)
    if not failed_events:
        lines += ["_None._", ""]
    for agent in sorted(groups, key=lambda a: (-sum(len(v) for v in groups[a].values()), a)):
        lines.append(f"**{agent}** — {sum(len(v) for v in groups[agent].values())}")
        for reason in sorted(groups[agent], key=lambda c: (-len(groups[agent][c]), c)):
            bucket = groups[agent][reason]
            lines.append(f"- `{reason}` × {len(bucket)}")
            for e in sorted(bucket, key=lambda e: (str(e.get("run_id") or ""), e.get("seq") if isinstance(e.get("seq"), int) else 0)):
                lines.append(f"  - {e.get('status')} `{e.get('run_id')}` #{e.get('seq')} {e.get('phase') or ''}: {one_line(e.get('summary'))}")
        lines.append("")

    recurring = recurring_tests(failed_events)
    lines += ["### Tests failing under two or more tickets", "",
              "_Names are parsed from event summaries (no structured field exists), so this can miss a test or merge two "
              "with the same name._", ""]
    if recurring:
        lines += [f"- `{name}` × {len(tickets)}: {', '.join(tickets)}" for name, tickets in recurring]
    else:
        lines.append("_None: no test name appears under two distinct tickets._")
    return "\n".join(lines)
