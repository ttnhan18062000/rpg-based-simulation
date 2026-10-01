#!/usr/bin/env python3
"""Explicit week close: fold a *finished* ISO week's monitoring shards into the three canonical
`runs.jsonl` / `events.jsonl` / `tools.jsonl` files, plus that week's pending working_log shards into
`tickets/working_log.csv` (TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND).

Why it exists: `generate_retro.py` calling `monitoring_consolidation.consolidate_all()` was the only
automatic consolidation trigger. The retro is becoming read-only, so closing a week is now a
deliberate, on-demand step (`make agent-monitoring-close-week WEEK=2026-W40`), made visible by a
report-only nudge (`week_close_nudge.py`) rather than scheduled.

Rules:
- Refuses the current ISO week and any week that has not ended (a week is finished once today is after
  its Sunday), and any malformed week id. Refusal touches nothing and exits 2.
- Deterministic and non-reordering: a kind with no shard file is not touched at all (real canonical
  files are not in ts order, so re-sorting an already-consolidated week would reorder it). Otherwise the
  canonical file's existing lines stay where they are and the new shard lines, exact-line de-duplicated
  against it and each other, are appended ordered by (`ts`, `seq`), unparseable lines last.
- Idempotent: a second close finds no shard and rewrites nothing. The write is tmp-file +
  `os.replace`; shards are deleted only after that succeeds, and a crash between the two is healed by
  the next close because exact duplicates are dropped.
- Late-shard policy: a shard for an already-closed week that arrives later (a branch merging after its
  week ended) is folded by the next close of that week, like any other shard.
- working_log rows go through `working_log_writer.consolidate_pending_rows(week=...)`, the CSV's single
  writer; this module never opens `tickets/working_log.csv` itself.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring_consolidation import DEFAULT_DATA_DIR, JSONL_KINDS, _default_csv_path_for  # noqa: E402
from monitoring_shard_paths import per_identifier_shard_paths  # noqa: E402
from working_log_writer import consolidate_pending_rows  # noqa: E402

_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")


class WeekCloseError(Exception):
    """A refusal (bad id, unfinished week, missing directory). Nothing was written."""


def week_end(week: str) -> date:
    """The Sunday that ends ISO week `week` ("2026-W40")."""
    m = _WEEK_RE.match(week or "")
    if not m:
        raise WeekCloseError(f"not an ISO week id (expected YYYY-Www): {week!r}")
    try:
        monday = date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
    except ValueError as exc:
        raise WeekCloseError(f"not a real ISO week: {week!r} ({exc})") from exc
    return monday + timedelta(days=6)


def is_finished(week: str, today: date) -> bool:
    return today > week_end(week)


def _sort_key(indexed: tuple[int, str]):
    idx, line = indexed
    try:
        rec = json.loads(line)
        ts = rec.get("ts") or rec.get("start_ts") or rec.get("end_ts") or ""
        seq = rec.get("seq")
        return (0, str(ts), seq if isinstance(seq, int) else 0, idx)
    except (ValueError, AttributeError):
        return (1, "", 0, idx)  # unparseable: last, original order


def _fold_kind(week_dir: Path, kind: str) -> dict:
    """Fold this kind's shard files into the canonical file. A kind with no shard file is skipped
    entirely: real canonical files are not in ts order today, so re-sorting an already-consolidated
    week would reorder it. Existing canonical lines keep their existing order; only the new shard
    lines are exact-line de-duplicated (against the canonical file and each other) and appended,
    ordered by (ts, seq)."""
    canonical = week_dir / f"{kind}.jsonl"
    shards = per_identifier_shard_paths(week_dir, kind)
    if not shards:
        return {"shard_files": 0, "lines_in": 0, "lines_out": 0, "duplicates_dropped": 0, "rewrote_canonical": False}
    existing_text = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
    existing = [ln for ln in existing_text.splitlines() if ln.strip()]
    shard_lines = []
    for f in shards:
        shard_lines.extend(ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip())
    seen = set(existing)
    fresh = []
    for ln in shard_lines:
        if ln not in seen:
            seen.add(ln)
            fresh.append(ln)
    appended = [ln for _, ln in sorted(enumerate(fresh), key=_sort_key)]
    new_text = existing_text if existing_text.endswith("\n") or not existing_text else existing_text + "\n"
    new_text += "".join(ln + "\n" for ln in appended)
    changed = new_text != existing_text
    if changed:
        tmp = canonical.with_name(canonical.name + ".closing")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, canonical)
    for f in shards:
        f.unlink()
    return {
        "shard_files": len(shards),
        "lines_in": len(existing) + len(shard_lines),
        "lines_out": len(existing) + len(appended),
        "duplicates_dropped": len(shard_lines) - len(appended),
        "rewrote_canonical": bool(changed),
    }


def close_week(week: str, data_dir: Path = DEFAULT_DATA_DIR, today: date | None = None) -> dict:
    today = today or date.today()
    if not is_finished(week, today):
        raise WeekCloseError(
            f"refusing to close {week}: it ends {week_end(week).isoformat()} and today is "
            f"{today.isoformat()} (only a finished ISO week can be closed)"
        )
    week_dir = Path(data_dir) / week
    if not week_dir.is_dir():
        raise WeekCloseError(f"no such week directory: {week_dir}")
    result = {kind: _fold_kind(week_dir, kind) for kind in JSONL_KINDS}
    result["working_log"] = consolidate_pending_rows(
        data_root=Path(data_dir), csv_path=_default_csv_path_for(Path(data_dir)), week=week
    )
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fold a finished ISO week's monitoring shards into canonical files.")
    ap.add_argument("--week", required=True, help="ISO week id, e.g. 2026-W40")
    ap.add_argument("--data-dir", default=None, help="Override agent-monitoring/data/ (testing).")
    ap.add_argument("--today", default=None, help="Override today's date, YYYY-MM-DD (testing).")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = close_week(
            args.week,
            Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR,
            date.fromisoformat(args.today) if args.today else None,
        )
    except WeekCloseError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for kind in JSONL_KINDS:
            r = result[kind]
            print(f"{args.week} {kind}: {r['shard_files']} shard(s), {r['lines_in']} line(s) in, "
                  f"{r['lines_out']} out, {r['duplicates_dropped']} exact duplicate(s) dropped")
        wl = result["working_log"]
        print(f"{args.week} working_log: folded {wl['shard_files']} shard file(s) ({wl['consolidated_rows']} row(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
