#!/usr/bin/env python3
"""What followed a gate verdict, and whether the verdict was right
(TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION, child 3 of TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER).

Two append-only row kinds share the `gate_verdicts` shard family with the verdict rows
`gate_verdicts.py` writes, keyed by `gate_verdict_id`; nothing is edited in place:

  outcome       what happened next: accepted | fixed_and_rerun | rerun_no_change | overridden | stopped
  adjudication  whether the verdict was right: true_block | false_block | true_pass | false_pass | unknown

Outcomes are also derived on read, so a session need not enter the common cases by hand: a blocking verdict
followed on the same ticket and gate by a passing one is `fixed_and_rerun`; followed by a blocking one with the
same `inputs_ref` it is `rerun_no_change`. Anything else has no derived outcome and shows in `list --unresolved`.
An explicit outcome always wins over a derived one. For adjudication, the latest row for a verdict wins and the
earlier rows are kept.

The one automatic adjudication is `backstop_adjudicate()`: when `post_native_run_check.py` fails a gate that a
native run attested as PASS for the same ticket, the native verdict is a `false_pass`
(agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md names that
backstop as the authoritative re-run). `true_pass` is only ever recorded by someone who checked a pass on
purpose; an unchecked pass is not assumed true.

CLI: `gate_ledger.py outcome|adjudicate|list`. An unknown `gate_verdict_id` is refused with exit 2.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import gate_verdicts  # noqa: E402
from monitoring_batch_identifier import resolve_write_target  # noqa: E402
from monitoring_shard_paths import shard_paths  # noqa: E402
from writer import write_line  # noqa: E402

DEFAULT_DATA_ROOT = Path("agent-working/agent-monitoring/data")
BACKSTOP_ACTOR = "orchestrator-backstop"
# Backstop check -> the attested native gate ids it re-derives (design.md: the orchestrator re-runs
# done_checker_static after the run returns). Other native gates have no backstop counterpart.
BACKSTOP_COVERS = {"done_checker_static": ("finalize_selfcheck",)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_rows(data_root: Path = DEFAULT_DATA_ROOT) -> list[dict]:
    """Every row of the family in read order (shards sorted, lines in file order). Bad lines are skipped."""
    rows = []
    for shard in shard_paths(data_root, gate_verdicts.KIND):
        try:
            lines = shard.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _split(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    verdicts = [r for r in rows if "row_kind" not in r]
    outcomes = [r for r in rows if r.get("row_kind") == gate_verdicts.ROW_KIND_OUTCOME]
    adjudications = [r for r in rows if r.get("row_kind") == gate_verdicts.ROW_KIND_ADJUDICATION]
    return verdicts, outcomes, adjudications


def _latest_by_verdict(rows: list[dict]) -> dict[str, dict]:
    """Latest row per gate_verdict_id by (ts, read order); the earlier rows stay on disk."""
    ordered = sorted(enumerate(rows), key=lambda pair: (str(pair[1].get("ts", "")), pair[0]))
    return {r["gate_verdict_id"]: r for _, r in ordered if r.get("gate_verdict_id")}


def derive_outcomes(verdicts: list[dict]) -> dict[str, dict]:
    """`{gate_verdict_id: {"outcome", "followup_verdict_id"}}` for a blocking verdict whose next verdict on the
    same (ticket, gate) is a pass (`fixed_and_rerun`) or a block with the same inputs (`rerun_no_change`)."""
    groups: dict[tuple, list[tuple[int, dict]]] = {}
    for index, row in enumerate(verdicts):
        if row.get("ticket_id") and row.get("gate_id"):
            groups.setdefault((row["ticket_id"], row["gate_id"]), []).append((index, row))
    derived: dict[str, dict] = {}
    for members in groups.values():
        members.sort(key=lambda pair: (str(pair[1].get("ts", "")), pair[0]))
        for (_, current), (_, following) in zip(members, members[1:]):
            if not current.get("blocking"):
                continue
            if not following.get("blocking"):
                outcome = "fixed_and_rerun"
            elif following.get("inputs_ref") == current.get("inputs_ref"):
                outcome = "rerun_no_change"
            else:
                continue
            derived[current["gate_verdict_id"]] = {"outcome": outcome, "followup_verdict_id": following["gate_verdict_id"]}
    return derived


def resolved_view(rows: list[dict]) -> list[dict]:
    """Each verdict row with its `outcome` (explicit beats derived; `outcome_source` says which) and its latest
    `adjudication`, `None` when there is none."""
    verdicts, outcomes, adjudications = _split(rows)
    explicit = _latest_by_verdict(outcomes)
    derived = derive_outcomes(verdicts)
    adjudicated = _latest_by_verdict(adjudications)
    view = []
    for verdict in verdicts:
        vid = verdict.get("gate_verdict_id")
        entry = dict(verdict)
        if vid in explicit:
            entry["outcome"], entry["outcome_source"] = explicit[vid]["outcome"], "explicit"
            entry["followup_verdict_id"] = explicit[vid].get("followup_verdict_id")
        elif vid in derived:
            entry["outcome"], entry["outcome_source"] = derived[vid]["outcome"], "derived"
            entry["followup_verdict_id"] = derived[vid]["followup_verdict_id"]
        else:
            entry["outcome"], entry["outcome_source"], entry["followup_verdict_id"] = None, None, None
        entry["adjudication"] = adjudicated[vid]["adjudication"] if vid in adjudicated else None
        entry["adjudicated_by"] = adjudicated[vid]["adjudicated_by"] if vid in adjudicated else None
        view.append(entry)
    return view


def unresolved(view: list[dict]) -> list[dict]:
    """Blocking verdicts with neither an explicit nor a derived outcome."""
    return [v for v in view if v.get("blocking") and v["outcome"] is None]


def _known_verdict_ids(data_root: Path) -> set[str]:
    return {r["gate_verdict_id"] for r in _split(load_rows(data_root))[0] if r.get("gate_verdict_id")}


def _append(row: dict, data_root: Path, target: Path | None) -> bool:
    problems = gate_verdicts.validate_record(row)
    if problems:
        raise ValueError("; ".join(problems))
    path = target or (resolve_write_target(gate_verdicts.KIND) if data_root == DEFAULT_DATA_ROOT
                      else data_root / datetime.now(timezone.utc).strftime("%G-W%V") / f"ledger.{gate_verdicts.KIND}.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    return write_line(path, json.dumps(row, separators=(",", ":")))


def record_outcome(gate_verdict_id: str, outcome: str, followup_verdict_id: str | None = None, note: str | None = None,
                   data_root: Path = DEFAULT_DATA_ROOT, target: Path | None = None) -> dict:
    """Append an `outcome` row. Raises KeyError for an unknown verdict id, ValueError for an invalid row."""
    if gate_verdict_id not in _known_verdict_ids(data_root):
        raise KeyError(gate_verdict_id)
    row = {"ts": _now(), "row_kind": gate_verdicts.ROW_KIND_OUTCOME, "gate_verdict_id": gate_verdict_id,
           "outcome": outcome, "followup_verdict_id": followup_verdict_id, "note": note}
    if not _append(row, data_root, target):
        raise OSError("gate_verdicts write failed")
    return row


def record_adjudication(gate_verdict_id: str, adjudication: str, adjudicated_by: str, reason: str,
                        data_root: Path = DEFAULT_DATA_ROOT, target: Path | None = None) -> dict:
    """Append an `adjudication` row. Raises KeyError for an unknown verdict id, ValueError for an invalid row."""
    if gate_verdict_id not in _known_verdict_ids(data_root):
        raise KeyError(gate_verdict_id)
    row = {"ts": _now(), "row_kind": gate_verdicts.ROW_KIND_ADJUDICATION, "gate_verdict_id": gate_verdict_id,
           "adjudication": adjudication, "adjudicated_by": adjudicated_by, "reason": reason}
    if not _append(row, data_root, target):
        raise OSError("gate_verdicts write failed")
    return row


def backstop_adjudicate(ticket_id: str, backstop_check: str, data_root: Path = DEFAULT_DATA_ROOT,
                        target: Path | None = None) -> list[dict]:
    """The backstop failed `backstop_check` for `ticket_id`: mark each native PASS it contradicts as a
    `false_pass`. At most one adjudication per native verdict (a repeat run adds nothing). Never raises."""
    if gate_verdicts.recording_disabled():
        return []
    try:
        verdicts, _, adjudications = _split(load_rows(data_root))
        already = {a["gate_verdict_id"] for a in adjudications if a.get("adjudicated_by") == BACKSTOP_ACTOR}
        covered = BACKSTOP_COVERS.get(backstop_check, ())
        written = []
        for row in verdicts:
            if (row.get("ticket_id") == ticket_id and row.get("execution_mode") == "workflow"
                    and row.get("gate_id") in covered and not row.get("blocking")
                    and row["gate_verdict_id"] not in already):
                written.append(record_adjudication(
                    row["gate_verdict_id"], "false_pass", BACKSTOP_ACTOR,
                    f"native run attested {row['gate_id']} PASS; the orchestrator re-run of {backstop_check} failed",
                    data_root=data_root, target=target))
        return written
    except Exception as exc:  # noqa: BLE001 - monitoring must never fail the backstop
        print(f"WARNING: backstop adjudication not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
        return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    out = sub.add_parser("outcome", help="record what followed a gate verdict")
    out.add_argument("--gate-verdict-id", required=True)
    out.add_argument("--outcome", required=True, choices=gate_verdicts.OUTCOMES)
    out.add_argument("--followup-verdict-id")
    out.add_argument("--note")
    adj = sub.add_parser("adjudicate", help="record whether a gate verdict was right")
    adj.add_argument("--gate-verdict-id", required=True)
    adj.add_argument("--adjudication", required=True, choices=gate_verdicts.ADJUDICATIONS)
    adj.add_argument("--by", required=True, help="a role, or `owner`")
    adj.add_argument("--reason", required=True)
    lst = sub.add_parser("list", help="show verdicts with their resolved outcome and adjudication")
    lst.add_argument("--unresolved", action="store_true", help="only blocking verdicts with no outcome")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_root = Path(args.data_root)
    try:
        if args.command == "outcome":
            row = record_outcome(args.gate_verdict_id, args.outcome, args.followup_verdict_id, args.note, data_root)
            print(f"recorded outcome {row['outcome']} for {row['gate_verdict_id']}")
        elif args.command == "adjudicate":
            row = record_adjudication(args.gate_verdict_id, args.adjudication, args.by, args.reason, data_root)
            print(f"recorded adjudication {row['adjudication']} for {row['gate_verdict_id']}")
        else:
            view = resolved_view(load_rows(data_root))
            for v in (unresolved(view) if args.unresolved else view):
                print(f"{v['gate_verdict_id']}  {v.get('ticket_id') or '-'}  {v['gate_id']}  {v['verdict']}  "
                      f"outcome={v['outcome'] or '-'}  adjudication={v['adjudication'] or '-'}")
    except KeyError as exc:
        print(f"ERROR: unknown gate_verdict_id {exc.args[0]!r}", file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
