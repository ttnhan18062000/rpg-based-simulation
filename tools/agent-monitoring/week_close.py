#!/usr/bin/env python3
"""Explicit week close: fold a *finished* ISO week's monitoring shards into the three canonical
`runs.jsonl` / `events.jsonl` / `tools.jsonl` files, plus that week's pending working_log shards into
`agent-working/tickets/working_log.csv` (TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND).

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
- Main-checkout tools rows: a session launched in the main checkout writes `main.tools.jsonl`, which no PR carries. A close run
  from a worktree reads that file (read-only) from the main checkout, found through `git rev-parse --git-common-dir`, and appends
  the week's rows missing from the canonical `tools.jsonl` (full-row identity dedup). A close run in the main checkout itself
  folds it as an ordinary shard. Host u24desktop's main checkout is another host and is not swept.
- working_log rows go through `working_log_writer.consolidate_pending_rows(week=...)`, the CSV's single
  writer; this module never opens `agent-working/tickets/working_log.csv` itself.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import hand_closure_time as hct  # noqa: E402
from monitoring_consolidation import DEFAULT_DATA_DIR, JSONL_KINDS, _default_csv_path_for  # noqa: E402

#: What a week close folds: the three canonical kinds plus the gate-verdict ledger, so a closed week leaves no per-batch shard
#: of any family that has them (TCK-20261015-WEEK-CLOSE-ALL-SHARD-KINDS-AND-VOID-ROW). `manual_actions.jsonl` and
#: `role_boundary.jsonl` are bare per-week files with no per-batch shards, so there is nothing of theirs to fold.
CLOSE_KINDS = (*JSONL_KINDS, "gate_verdicts")
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


#: The branch key the hook gives a session launched in the main checkout (`main.tools.jsonl`). No PR branch carries that file, so
#: a worktree's week close pulls it in (TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH).
MAIN_CHECKOUT_TOOLS_SHARD = "main.tools.jsonl"
_UNSET = object()


def find_main_checkout(data_dir: Path) -> Path | None:
    """The main worktree, one level above `git rev-parse --git-common-dir`, when `data_dir` belongs to a different checkout; else None."""
    cwd = Path(data_dir).resolve().parent
    try:
        out = []
        for flag in ("--git-common-dir", "--show-toplevel"):
            proc = subprocess.run(["git", "rev-parse", flag], cwd=cwd, capture_output=True, text=True, timeout=10)
            if proc.returncode != 0 or not proc.stdout.strip():
                return None
            out.append(proc.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return None
    common = Path(out[0]) if Path(out[0]).is_absolute() else (cwd / out[0])
    main = common.resolve().parent
    return main if main != Path(out[1]).resolve() and main.is_dir() else None


def _identity(line: str) -> str | None:
    """Full-row identity: the parsed row re-serialised with sorted keys, so spacing or key order never hides a duplicate."""
    try:
        rec = json.loads(line)
    except ValueError:
        return None
    return json.dumps(rec, sort_keys=True, separators=(",", ":")) if isinstance(rec, dict) else None


def sweep_main_checkout_tools(week: str, week_dir: Path, main_checkout: object = _UNSET) -> dict:
    """Append the main checkout's `main.tools.jsonl` rows for `week` to this checkout's canonical `tools.jsonl`.

    Strictly read-only on the main checkout (never truncated, rewritten or staged). Only the week being closed. Rows already in the
    canonical file (or repeated in the sweep) are dropped by full-row identity; a torn line is skipped. Idempotent. Never raises.
    """
    result = {"swept": 0, "duplicates_dropped": 0, "skipped": None}
    try:
        main = find_main_checkout(Path(week_dir).parent) if main_checkout is _UNSET else main_checkout
        if main is None:
            result["skipped"] = "no separate main checkout (this is the main checkout, or git cannot say)"
            return result
        src = Path(main) / "agent-working" / "agent-monitoring" / "data" / week / MAIN_CHECKOUT_TOOLS_SHARD
        if not src.is_file():
            result["skipped"] = f"no {MAIN_CHECKOUT_TOOLS_SHARD} for {week} in the main checkout"
            return result
        canonical = Path(week_dir) / "tools.jsonl"
        existing_text = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
        seen = {i for i in (_identity(ln) for ln in existing_text.splitlines() if ln.strip()) if i}
        fresh = []
        for ln in src.read_text(encoding="utf-8", errors="replace").splitlines():
            ident = _identity(ln) if ln.strip() else None
            if ident is None:
                continue  # blank or torn
            if ident in seen:
                result["duplicates_dropped"] += 1
                continue
            seen.add(ident)
            fresh.append(ln.strip())
        if not fresh:
            return result
        appended = [ln for _, ln in sorted(enumerate(fresh), key=_sort_key)]
        new_text = existing_text if existing_text.endswith("\n") or not existing_text else existing_text + "\n"
        new_text += "".join(ln + "\n" for ln in appended)
        tmp = canonical.with_name(canonical.name + ".closing")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, canonical)
        result["swept"] = len(appended)
    except Exception as exc:  # noqa: BLE001 - a sweep problem never fails a week close
        result["skipped"] = f"sweep failed: {type(exc).__name__}: {exc}"
    return result


def _previous_week(week: str) -> str:
    year, number = (int(x) for x in _WEEK_RE.match(week).groups())
    iso = (date.fromisocalendar(year, number, 1) - timedelta(days=7)).isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _week_rows(data_dir: Path, week: str, suffix: str) -> list[dict]:
    folder = Path(data_dir) / week
    return [r for path in sorted(folder.glob(f"*{suffix}")) for r in hct._read_jsonl(path)] if folder.is_dir() else []


def rederive_week_durations(week: str, week_dir: Path) -> dict:
    """Re-derive the `unknown` durations of this week's hand closures from the tool rows present now
    (TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE).

    Replays `hand_closure_time.resolve()` for each hand run row with `duration_source: unknown` and a session id, oldest closure first, with
    the session's unattributed rows of this and the previous week and the session's earlier hand closures. A run that now resolves
    `tool_activity` is rewritten in place (`start_ts`, `end_ts`, `duration_s`, `duration_source`, `claim_peers`, `closed_ts` when anchored)
    and marked `duration_rederived: "week_close"`; `declared` and `tool_activity` rows are never touched, and cost fields are not
    re-derived. Because the rewrite changes `start_ts`, an old `unknown` row for the same `(run_id, execution_id)` (a late shard folded
    in by a re-close) would count as a second run under `run_dedup`: it is dropped, and only that row. When one execution holds several
    unknown rows (a checkpoint line and the final line), the latest closure that resolves is re-derived and its unknown siblings are
    dropped, so one execution ends as one run row. Idempotent; never raises.
    """
    result = {"rederived": 0, "stale_dropped": 0, "skipped": None}
    try:
        canonical = Path(week_dir) / "runs.jsonl"
        if not canonical.is_file():
            return result
        data_dir = Path(week_dir).parent
        lines = canonical.read_text(encoding="utf-8").splitlines()
        parsed = []
        for ln in lines:
            try:
                rec = json.loads(ln)
            except ValueError:
                rec = None
            parsed.append(rec if isinstance(rec, dict) else None)
        rederived_ids = {(r.get("run_id"), r.get("execution_id")) for r in parsed if r and r.get("duration_rederived")}
        tool_rows = [r for w in (_previous_week(week), week) for r in _week_rows(data_dir, w, "tools.jsonl")]
        all_hand_runs = [r for w in (_previous_week(week), week) for r in _week_rows(data_dir, w, "runs.jsonl")
                         if r.get("execution_mode") == "hand" and r.get("session_id")]
        by_session: dict[str, list[dict]] = {}
        for r in tool_rows:
            if r.get("run_id") is None and r.get("session_id") and hct._parse(r.get("ts")):
                by_session.setdefault(r["session_id"], []).append(r)
        for rows in by_session.values():
            rows.sort(key=lambda r: r["ts"])
        ends_by_session: dict[str, list[tuple[str, tuple]]] = {}  # session -> (end_ts, (run_id, execution_id)) of its hand closures
        for r in all_hand_runs:
            if hct._parse(r.get("end_ts")):
                ends_by_session.setdefault(r["session_id"], []).append((r["end_ts"], (r.get("run_id"), r.get("execution_id"))))

        def closure_of(rec: dict) -> str:
            return rec.get("closed_ts") or rec.get("end_ts") or ""

        candidates = sorted(
            (i for i, r in enumerate(parsed) if r and r.get("execution_mode") == "hand" and r.get("duration_source") == "unknown"
             and r.get("session_id") and (r.get("run_id"), r.get("execution_id")) not in rederived_ids and hct._parse(closure_of(r))),
            key=lambda i: hct._parse(closure_of(parsed[i])))
        drop = set()
        for i, r in enumerate(parsed):
            if r and r.get("duration_source") == "unknown" and (r.get("run_id"), r.get("execution_id")) in rederived_ids:
                drop.add(i)
        # One execution can hold several unknown rows (a checkpoint line and the final line). Re-derive the LATEST closure's row, the one
        # that carries the final state, and drop its unknown siblings only when that succeeds; a sibling's own end never counts as a
        # prior closure of the same execution.
        groups: dict[tuple, list[int]] = {}
        for i in candidates:
            groups.setdefault((parsed[i].get("run_id"), parsed[i].get("execution_id")), []).append(i)
        done_ids: dict[tuple, int] = {}
        for key, members in sorted(groups.items(), key=lambda kv: hct._parse(closure_of(parsed[kv[1][-1]]))):
            for i in reversed(members):  # latest closure first; the first row that resolves is the survivor
                rec = parsed[i]
                sid, closure = rec["session_id"], closure_of(rec)
                prior = [e for e, k in ends_by_session.get(sid, []) if k != key and hct._parse(e) < hct._parse(closure)]
                res = hct.resolve(closure, None, None, sid, by_session.get(sid, []), prior)
                if res.duration_source != hct.TOOL_ACTIVITY:
                    continue
                rec.update({"start_ts": res.start_ts, "end_ts": res.end_ts, "duration_source": hct.TOOL_ACTIVITY,
                            "claim_peers": res.claim_peers, "duration_rederived": "week_close"})
                rec["duration_s"] = int((hct._parse(res.end_ts) - hct._parse(res.start_ts)).total_seconds())
                if res.closed_ts:
                    rec["closed_ts"] = res.closed_ts
                ends_by_session[sid] = [(e, k) for e, k in ends_by_session.get(sid, []) if k != key] + [(res.end_ts, key)]
                done_ids[key] = i
                drop.update(m for m in members if m != i)
                break
        result["rederived"] = len([i for i in done_ids.values() if i not in drop])
        if not result["rederived"] and not drop:
            return result
        out = []
        for i, ln in enumerate(lines):
            if i in drop:
                result["stale_dropped"] += 1
                continue
            out.append(json.dumps(parsed[i], separators=(",", ":")) if i in candidates and parsed[i].get("duration_rederived") else ln)
        tmp = canonical.with_name(canonical.name + ".closing")
        tmp.write_text("".join(x + "\n" for x in out), encoding="utf-8")
        os.replace(tmp, canonical)
    except Exception as exc:  # noqa: BLE001 - a re-derivation problem never fails a week close
        result["skipped"] = f"re-derivation failed: {type(exc).__name__}: {exc}"
    return result


def close_week(week: str, data_dir: Path = DEFAULT_DATA_DIR, today: date | None = None, main_checkout: object = _UNSET) -> dict:
    today = today or date.today()
    if not is_finished(week, today):
        raise WeekCloseError(
            f"refusing to close {week}: it ends {week_end(week).isoformat()} and today is "
            f"{today.isoformat()} (only a finished ISO week can be closed)"
        )
    week_dir = Path(data_dir) / week
    if not week_dir.is_dir():
        raise WeekCloseError(f"no such week directory: {week_dir}")
    result = {kind: _fold_kind(week_dir, kind) for kind in CLOSE_KINDS}
    result["main_checkout_tools"] = sweep_main_checkout_tools(week, week_dir, main_checkout)
    result["durations"] = rederive_week_durations(week, week_dir)
    result["working_log"] = consolidate_pending_rows(
        data_root=Path(data_dir), csv_path=_default_csv_path_for(Path(data_dir)), week=week
    )
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fold a finished ISO week's monitoring shards into canonical files.")
    ap.add_argument("--week", required=True, help="ISO week id, e.g. 2026-W40")
    ap.add_argument("--data-dir", default=None, help="Override agent-working/agent-monitoring/data/ (testing).")
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
        for kind in CLOSE_KINDS:
            r = result[kind]
            print(f"{args.week} {kind}: {r['shard_files']} shard(s), {r['lines_in']} line(s) in, "
                  f"{r['lines_out']} out, {r['duplicates_dropped']} exact duplicate(s) dropped")
        sw = result["main_checkout_tools"]
        print(f"{args.week} main-checkout tools rows: swept {sw['swept']} ({sw['duplicates_dropped']} duplicate(s) dropped)"
              + (f"; {sw['skipped']}" if sw["skipped"] else ""))
        rd = result["durations"]
        print(f"{args.week} hand-closure durations: re-derived {rd['rederived']} unknown, dropped {rd['stale_dropped']} stale unknown row(s)"
              + (f"; {rd['skipped']}" if rd["skipped"] else ""))
        wl = result["working_log"]
        print(f"{args.week} working_log: folded {wl['shard_files']} shard file(s) ({wl['consolidated_rows']} row(s)"
              + (f", {wl['voided_rows']} voided, recorded in working_log_voids.jsonl" if wl.get("voided_rows") else "") + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
