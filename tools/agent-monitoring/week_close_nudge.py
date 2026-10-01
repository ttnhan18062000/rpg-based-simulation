"""Report-only: which finished ISO weeks still hold per-batch monitoring shards
(TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND). Never blocks; used by `retro_nudge_hook.py` and runnable
on its own (`python3 tools/agent-monitoring/week_close_nudge.py`)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monitoring_shard_paths import per_identifier_shard_paths  # noqa: E402
from week_close import WeekCloseError, is_finished  # noqa: E402

_KINDS = ("runs", "events", "tools", "working_log")


def weeks_needing_close(data_root: Path, today: date | None = None) -> list[tuple[str, int]]:
    """[(week, shard_file_count)] for every finished week under `data_root` that still has shard
    files, oldest first. The current and any unfinished week are never listed."""
    today = today or date.today()
    if not Path(data_root).is_dir():
        return []
    out = []
    for week_dir in sorted(p for p in Path(data_root).iterdir() if p.is_dir()):
        try:
            if not is_finished(week_dir.name, today):
                continue
        except WeekCloseError:
            continue  # not an ISO-week directory
        n = sum(len(per_identifier_shard_paths(week_dir, k)) for k in _KINDS)
        if n:
            out.append((week_dir.name, n))
    return out


def nudge_message(pending: list[tuple[str, int]]) -> str | None:
    if not pending:
        return None
    listing = ", ".join(f"{w} ({n} shard file(s))" for w, n in pending)
    return (
        f"agent-monitoring-close-week: finished week(s) still hold per-batch shards: {listing}. "
        "Report only: when you decide, run `make agent-monitoring-close-week WEEK=<YYYY-Www>` "
        "(one session per week, committed by the implementer)."
    )


if __name__ == "__main__":
    msg = nudge_message(weeks_needing_close(Path("agent-monitoring/data")))
    print(msg or "No finished week has shards.")
