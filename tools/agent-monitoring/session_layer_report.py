"""tools/agent-monitoring/session_layer_report.py: the session-layer measures added to the existing retro report
(TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT; no new report). Pure rendering over already-collected
records, so it is testable without a data tree.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from batch_latency import render_row
from manual_actions import CATEGORIES, count_by_category
from session_role import UNRESOLVED

_LABELS = {
    "role_reminder": "role reminder", "routing_correction": "routing correction", "manual_wake": "manual wake",
    "worktree_correction": "worktree correction", "boundary_reminder": "boundary reminder",
    "handover_recovery": "handover recovery",
}


def load_family(data_dir: Path, filename: str) -> list[dict]:
    """Every record of one new file family (`manual_actions.jsonl`, `role_boundary.jsonl`) across the week folders."""
    out: list[dict] = []
    for path in sorted(Path(data_dir).glob(f"*/{filename}")):
        for line in path.read_text().splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    return out


def in_period(records: list[dict], week_str: str | None = None, cutoff: str | None = None) -> list[dict]:
    from datetime import datetime

    def keep(rec: dict) -> bool:
        ts = rec.get("ts")
        if not isinstance(ts, str):
            return False
        if week_str is not None:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%G-W%V") == week_str
            except ValueError:
                return False
        return cutoff is None or ts >= cutoff

    return [r for r in records if keep(r)]


def _dark(family: str, total: int | None, in_period_n: int) -> str | None:
    """The line for a family that cannot be read as zeros, or None when its zeros are real.

    `total` is every record of the family in any week; None means the caller did not count (old behaviour).
    """
    if total is None or total > 0 and in_period_n:
        return None
    if total == 0:
        return (f"_Instrument not running: no {family} records exist in any week. "
                "Zeros below would be meaningless, so the table is omitted._")
    return f"_(instrument active; {total - in_period_n} records outside this period)_"


def _manual_lines(manual: list[dict], total: int | None) -> list[str]:
    lines = ["### Manual orchestration actions", ""]
    note = _dark("manual_actions", total, len(manual))
    if total == 0:
        return lines + [note, ""]
    counts = count_by_category(manual)
    lines += ["| category | sample | tally |", "|---|---|---|"]
    for cat in CATEGORIES:
        lines.append(f"| {_LABELS[cat]} | {counts[cat]['sample']} | {counts[cat]['tally']} |")
    count = sum(v["sample"] + v["tally"] for v in counts.values())
    lines += ["", f"Total: {count}. Per-batch: tally with `manual_actions.py tally <category> --batch <id>`."]
    return lines + ([note] if note else []) + [""]


def render(manual: list[dict], runs: list[dict], boundary: list[dict], latency_rows: list[tuple[str, dict]] | None = None,
           manual_total: int | None = None, boundary_total: int | None = None) -> str:
    lines = ["## Session-Layer Measures", "",
             "_Headline metric and batch latency from `docs/plans/agent_infrastructure/session_layer_working_process.md` "
             "section 11. Counts are repeated instructions, never decisions, design feedback or requirements. "
             "`sample` is the conservative prompt tagger (under-counts); `tally` is the owner's own line per batch._", ""]
    lines += _manual_lines(manual, manual_total)
    roles = Counter(str(r.get("session_role") or UNRESOLVED) for r in runs)
    lines += ["### Runs by session role", ""]
    if roles:
        lines += ["| session_role | runs |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(roles.items())]
    else:
        lines.append("No runs in this period.")
    if roles and set(roles) == {UNRESOLVED}:
        lines += ["", "_No run in this period had a resolved role, so role binding was not active._"]
    lines += ["", "_`unresolved` = no binding names the session (plain session) or the record predates `session_role`._", ""]
    kinds = Counter(str(b.get("kind") or "unknown") for b in boundary)
    lines += ["### `role_boundary` warnings (advisory)", ""]
    note = _dark("role_boundary", boundary_total, len(boundary))
    if boundary_total == 0:
        lines.append(note)
    else:
        lines.append(", ".join(f"{k}: {v}" for k, v in sorted(kinds.items())) if kinds else "None in this period.")
        if note:
            lines.append(note)
    lines += ["", "### Batch latency", ""]
    if latency_rows:
        lines += ["| batch | implementation | finalization | cycle | dispatch from |", "|---|---|---|---|---|"]
        lines += [render_row(label, result) for label, result in latency_rows]
        lines.append("")
        lines.append("_Dispatch defaults to the batch's first commit (the dispatch message leaves no repo artifact); "
                     "`unknown` means a timestamp was unavailable, never zero._")
    else:
        lines.append("Not computed for this report. Pass `--latency-prs <N> ...` to derive implementation, finalization "
                     "and cycle time from merged PRs (`unknown` when a timestamp is unavailable, never zero).")
    lines.append("")
    return "\n".join(lines)
