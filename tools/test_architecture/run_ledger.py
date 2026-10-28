"""The run ledger: one typed row per paired or gate invocation, so the step-cycle cost can be stated instead of remembered.

TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (T1 of ``docs/plans/architecture/faster_feature_testing_draft_tickets.md``). Nothing recorded how many
paired or gate runs a measured step took, how many were reruns, or why (STOP, refusal, ordering change, host kill). This module is the record.
Testing owns the module, its schema and the summary; ``rpg_gate_harness.run_matrix`` writes the gate rows; rpg's ``tools/rpg_measure/paired.py`` writes
the paired rows to this schema (``RunLedgerRow`` is the only way to build one). The ledger is evidence, never a gate: nothing reads it to pass or fail
a run, and a write failure warns on stderr and never changes an invocation's exit code.

File: append-only JSONL, default ``data/ledgers/run_ledger.jsonl`` (git-ignored like ``data/runs/``), override with ``RUN_LEDGER_PATH``. One line per
row, written with a single ``O_APPEND`` write, so two invocations never interleave a line. Schema ``run-ledger/v1``, every field required, the nullable
ones marked::

    {"schema": "run-ledger/v1", "invocation_id": uuid4, "tool": "paired" | "gate", "step": str,
     "mode": "step" | "neutral" | "report_only" (paired) | "gate" (gate), "workers": int >= 1 (the --jobs parallelism),
     "base_sha": str | null (null for gate), "new_sha": str, "worlds": [str], "seeds": [int], "ticks": int,
     "started_at": ISO tz-aware, "ended_at": ISO tz-aware | null,
     "outcome": "PASS" | "STOP" | "REFUSED" | "KILLED" | "ERROR" | null, "outcome_detail": str | null,
     "rerun_of": invocation_id | null (given by the caller, never guessed),
     "runs": [{"arm": "base" | "new" | "self" | "gate", "world": str, "seed": int, "wall_seconds": float,
               "peak_rss_mb": float | null, "cached": bool}],
     "host": {"name", "nproc", "mem_total_mb", "python", "platform"}}

``mode`` says what a ``PASS`` means (added at rpg-planner's request, 2026-10-26): a paired ``step`` gives PASS/STOP; ``neutral`` gives IDENTICAL (PASS) or DIFFERENT (STOP, the
differing keys in ``outcome_detail``) at the neutral tick count; ``report_only`` suppresses STOP, so its PASS is not a real pass. ``workers`` is the parallelism the per-arm
``wall_seconds`` depend on, so a rerun at a different ``--jobs`` is comparable.

``cached`` is true when the result came from the cache and was not executed. A killed invocation: it writes a *started* row first (``outcome`` and
``ended_at`` null, the same ``invocation_id``) and an end row when it finishes; the summary reads a started row with no end row as ``KILLED``.
:meth:`RunLedgerRow.from_json` rejects an unknown or missing field, and a wrong type, naming the field.

Summary (``python -m tools.test_architecture.run_ledger summary [--step S] [--since DATE] [--json] [--path FILE]``): per step, the invocations, runs
executed, runs cached, reruns (invocations with a ``rerun_of``), total and per-arm wall time of the executed runs, the max peak RSS and the outcomes by kind, and the invocations by mode (a ``report_only`` PASS is not a real pass).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import platform
import socket
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "run-ledger/v1"
TOOLS = ("paired", "gate")
OUTCOMES = ("PASS", "STOP", "REFUSED", "KILLED", "ERROR")
ARMS = ("base", "new", "self", "gate")
MODES = {"paired": ("step", "neutral", "report_only"), "gate": ("gate",)}
ENV_PATH = "RUN_LEDGER_PATH"
DEFAULT_RELATIVE_PATH = Path("data") / "ledgers" / "run_ledger.jsonl"
SUMMARY_SCHEMA = "run-ledger-summary/v1"


class LedgerRowError(ValueError):
    """A row that does not follow ``run-ledger/v1``; the message names the field."""


def _fail(field: str, why: str) -> "LedgerRowError":
    return LedgerRowError(f"{field}: {why}")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_keys(field: str, data: Any, expected: Sequence[str]) -> None:
    if not isinstance(data, dict):
        raise _fail(field, f"must be an object, got {type(data).__name__}")
    for name in expected:
        if name not in data:
            raise _fail(f"{field}.{name}" if field != "row" else name, "is required but missing")
    for name in data:
        if name not in expected:
            raise _fail(f"{field}.{name}" if field != "row" else name, "is not a field of run-ledger/v1")


def _aware_time(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(field, f"must be an ISO time string, got {value!r}")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise _fail(field, f"is not an ISO time: {value!r}") from None
    if parsed.tzinfo is None:
        raise _fail(field, f"must be timezone-aware: {value!r}")
    return value


def _uuid(field: str, value: Any) -> str:
    try:
        return str(uuid.UUID(str(value))) if isinstance(value, str) else (_ for _ in ()).throw(ValueError())
    except ValueError:
        raise _fail(field, f"must be a uuid string, got {value!r}") from None


def _str(field: str, value: Any, *, nullable: bool = False) -> Optional[str]:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise _fail(field, f"must be a non-empty string{' or null' if nullable else ''}, got {value!r}")
    return value


@dataclass(frozen=True)
class RunEntry:
    """One arm run: ``cached`` true when the result came from the cache and was not executed."""

    arm: str
    world: str
    seed: int
    wall_seconds: float
    peak_rss_mb: Optional[float]
    cached: bool

    @classmethod
    def from_dict(cls, data: Any, field: str = "runs[]") -> "RunEntry":
        _check_keys(field, data, ("arm", "world", "seed", "wall_seconds", "peak_rss_mb", "cached"))
        if data["arm"] not in ARMS:
            raise _fail(f"{field}.arm", f"must be one of {ARMS}, got {data['arm']!r}")
        _str(f"{field}.world", data["world"])
        if not _is_int(data["seed"]):
            raise _fail(f"{field}.seed", f"must be an integer, got {data['seed']!r}")
        if not _is_number(data["wall_seconds"]) or data["wall_seconds"] < 0:
            raise _fail(f"{field}.wall_seconds", f"must be a number >= 0, got {data['wall_seconds']!r}")
        if data["peak_rss_mb"] is not None and (not _is_number(data["peak_rss_mb"]) or data["peak_rss_mb"] < 0):
            raise _fail(f"{field}.peak_rss_mb", f"must be a number >= 0 or null, got {data['peak_rss_mb']!r}")
        if not isinstance(data["cached"], bool):
            raise _fail(f"{field}.cached", f"must be a boolean, got {data['cached']!r}")
        return cls(data["arm"], data["world"], data["seed"], data["wall_seconds"], data["peak_rss_mb"], data["cached"])


@dataclass(frozen=True)
class Host:
    name: str
    nproc: int
    mem_total_mb: Optional[int]
    python: str
    platform: str

    @classmethod
    def from_dict(cls, data: Any) -> "Host":
        _check_keys("host", data, ("name", "nproc", "mem_total_mb", "python", "platform"))
        _str("host.name", data["name"])
        if not _is_int(data["nproc"]) or data["nproc"] < 1:
            raise _fail("host.nproc", f"must be an integer >= 1, got {data['nproc']!r}")
        if data["mem_total_mb"] is not None and (not _is_int(data["mem_total_mb"]) or data["mem_total_mb"] < 0):
            raise _fail("host.mem_total_mb", f"must be an integer >= 0 or null, got {data['mem_total_mb']!r}")
        _str("host.python", data["python"])
        _str("host.platform", data["platform"])
        return cls(data["name"], data["nproc"], data["mem_total_mb"], data["python"], data["platform"])


def _mem_total_mb() -> Optional[int]:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def host_info() -> Host:
    return Host(socket.gethostname() or "unknown", os.cpu_count() or 1, _mem_total_mb(), platform.python_version(), platform.platform())


_FIELDS = ("schema", "invocation_id", "tool", "step", "mode", "workers", "base_sha", "new_sha", "worlds", "seeds", "ticks", "started_at", "ended_at",
           "outcome", "outcome_detail", "rerun_of", "runs", "host")


@dataclass(frozen=True)
class RunLedgerRow:
    schema: str
    invocation_id: str
    tool: str
    step: str
    mode: str
    workers: int
    base_sha: Optional[str]
    new_sha: str
    worlds: Tuple[str, ...]
    seeds: Tuple[int, ...]
    ticks: int
    started_at: str
    ended_at: Optional[str]
    outcome: Optional[str]
    outcome_detail: Optional[str]
    rerun_of: Optional[str]
    runs: Tuple[RunEntry, ...]
    host: Host

    @property
    def is_started_row(self) -> bool:
        """A row written before the invocation finished: no outcome and no end time."""
        return self.outcome is None

    def to_dict(self) -> Dict[str, Any]:
        data = dataclasses.asdict(self)
        data["worlds"], data["seeds"] = list(self.worlds), list(self.seeds)
        data["runs"] = [dataclasses.asdict(r) for r in self.runs]
        return data

    def to_json(self) -> str:
        """One line (sorted keys, no newline)."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, source: "str | Mapping[str, Any]") -> "RunLedgerRow":
        try:
            data = json.loads(source) if isinstance(source, str) else dict(source)
        except json.JSONDecodeError as exc:
            raise LedgerRowError(f"row: not JSON ({exc})") from None
        _check_keys("row", data, _FIELDS)
        if data["schema"] != SCHEMA:
            raise _fail("schema", f"must be {SCHEMA!r}, got {data['schema']!r}")
        _uuid("invocation_id", data["invocation_id"])
        if data["tool"] not in TOOLS:
            raise _fail("tool", f"must be one of {TOOLS}, got {data['tool']!r}")
        _str("step", data["step"])
        if data["mode"] not in MODES[data["tool"]]:
            raise _fail("mode", f"must be one of {MODES[data['tool']]} for tool {data['tool']!r}, got {data['mode']!r}")
        if not _is_int(data["workers"]) or data["workers"] < 1:
            raise _fail("workers", f"must be an integer >= 1, got {data['workers']!r}")
        _str("base_sha", data["base_sha"], nullable=True)
        _str("new_sha", data["new_sha"])
        if not isinstance(data["worlds"], list) or not data["worlds"] or not all(isinstance(w, str) and w for w in data["worlds"]):
            raise _fail("worlds", f"must be a non-empty list of strings, got {data['worlds']!r}")
        if not isinstance(data["seeds"], list) or not data["seeds"] or not all(_is_int(s) for s in data["seeds"]):
            raise _fail("seeds", f"must be a non-empty list of integers, got {data['seeds']!r}")
        if not _is_int(data["ticks"]) or data["ticks"] < 1:
            raise _fail("ticks", f"must be an integer >= 1, got {data['ticks']!r}")
        _aware_time("started_at", data["started_at"])
        if data["ended_at"] is not None:
            _aware_time("ended_at", data["ended_at"])
        if data["outcome"] is not None and data["outcome"] not in OUTCOMES:
            raise _fail("outcome", f"must be one of {OUTCOMES} or null, got {data['outcome']!r}")
        if (data["outcome"] is None) != (data["ended_at"] is None):
            raise _fail("ended_at", "must be null exactly when outcome is null (a started row)")
        _str("outcome_detail", data["outcome_detail"], nullable=True)
        if data["rerun_of"] is not None:
            _uuid("rerun_of", data["rerun_of"])
            if data["rerun_of"] == data["invocation_id"]:
                raise _fail("rerun_of", "must name an earlier invocation, not this one")
        if not isinstance(data["runs"], list):
            raise _fail("runs", f"must be a list, got {type(data['runs']).__name__}")
        runs = tuple(RunEntry.from_dict(r, f"runs[{i}]") for i, r in enumerate(data["runs"]))
        return cls(
            data["schema"], data["invocation_id"], data["tool"], data["step"], data["mode"], data["workers"], data["base_sha"], data["new_sha"],
            tuple(data["worlds"]), tuple(data["seeds"]), data["ticks"], data["started_at"], data["ended_at"],
            data["outcome"], data["outcome_detail"], data["rerun_of"], runs, Host.from_dict(data["host"]),
        )


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def ledger_path() -> Path:
    """``RUN_LEDGER_PATH`` or ``data/ledgers/run_ledger.jsonl`` under the repository root."""
    override = os.environ.get(ENV_PATH)
    return Path(override) if override else Path(__file__).resolve().parents[2] / DEFAULT_RELATIVE_PATH


def append_row(path: Optional[Path], row: RunLedgerRow) -> bool:
    """Append ``row`` as one line; return whether it was written. A failure warns on stderr and never raises: a ledger is evidence, not a gate."""
    try:
        target = Path(path) if path is not None else ledger_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        line = (row.to_json() + "\n").encode("utf-8")
        fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line)  # one write on an O_APPEND descriptor: two writers never interleave a line
        finally:
            os.close(fd)
        return True
    except Exception as exc:  # noqa: BLE001 - the monitoring rule: never fail the invocation
        print(f"warning: run ledger not written ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return False


def begin(*, tool: str, step: str, mode: str, workers: int, base_sha: Optional[str], new_sha: str, worlds: Sequence[str], seeds: Sequence[int], ticks: int,
          rerun_of: Optional[str] = None, path: Optional[Path] = None) -> Optional[RunLedgerRow]:
    """Write the *started* row and return it (``None`` if it could not even be built; the invocation goes on). Pass it to :func:`finish`."""
    try:
        row = RunLedgerRow(SCHEMA, str(uuid.uuid4()), tool, step, mode, workers, base_sha, new_sha, tuple(worlds), tuple(seeds), ticks, now_iso(), None, None, None,
                           rerun_of, (), host_info())
        RunLedgerRow.from_json(row.to_json())  # the caller's values are checked at the start, with the field named
    except Exception as exc:  # noqa: BLE001
        print(f"warning: run ledger row not built ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return None
    append_row(path, row)
    return row


def finish(started: Optional[RunLedgerRow], outcome: str, *, detail: Optional[str] = None, runs: Iterable[RunEntry] = (), path: Optional[Path] = None) -> None:
    """Write the end row for ``started`` (same ``invocation_id``). A no-op when ``started`` is ``None``."""
    if started is None:
        return
    try:
        row = dataclasses.replace(started, ended_at=now_iso(), outcome=outcome, outcome_detail=detail, runs=tuple(runs))
        RunLedgerRow.from_json(row.to_json())
    except Exception as exc:  # noqa: BLE001
        print(f"warning: run ledger end row not built ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return
    append_row(path, row)


def read_rows(path: Path) -> Tuple[List[RunLedgerRow], int]:
    """Every valid row of ``path`` in file order, and the number of lines that were not valid rows (a missing file has none)."""
    rows: List[RunLedgerRow] = []
    bad = 0
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return rows, 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            rows.append(RunLedgerRow.from_json(line))
        except LedgerRowError:
            bad += 1
    return rows, bad


def _final_rows(rows: Sequence[RunLedgerRow]) -> List[RunLedgerRow]:
    """One row per invocation: its end row, or its started row read as ``KILLED`` when no end row exists."""
    by_id: Dict[str, RunLedgerRow] = {}
    for row in rows:
        if row.invocation_id not in by_id or by_id[row.invocation_id].is_started_row:
            by_id[row.invocation_id] = row
    out = []
    for row in by_id.values():
        out.append(dataclasses.replace(row, outcome="KILLED", outcome_detail=row.outcome_detail or "started row with no end row") if row.is_started_row else row)
    return out


def summarize(rows: Sequence[RunLedgerRow], *, step: Optional[str] = None, since: Optional[dt.date] = None) -> Dict[str, Any]:
    """``{"schema", "steps": {step: {invocations, runs_executed, runs_cached, reruns, wall_seconds_total, wall_seconds_by_arm, max_peak_rss_mb, outcomes}}}``."""
    steps: Dict[str, Dict[str, Any]] = {}
    for row in sorted(_final_rows(rows), key=lambda r: r.started_at):
        if step is not None and row.step != step:
            continue
        if since is not None and dt.datetime.fromisoformat(row.started_at.replace("Z", "+00:00")).date() < since:
            continue
        s = steps.setdefault(row.step, {"invocations": 0, "runs_executed": 0, "runs_cached": 0, "reruns": 0, "wall_seconds_total": 0.0,
                                        "wall_seconds_by_arm": {}, "max_peak_rss_mb": None, "outcomes": Counter(), "modes": Counter()})
        s["invocations"] += 1
        s["reruns"] += 1 if row.rerun_of else 0
        s["outcomes"][row.outcome] += 1
        s["modes"][row.mode] += 1
        for run in row.runs:
            if run.cached:
                s["runs_cached"] += 1
                continue
            s["runs_executed"] += 1
            s["wall_seconds_total"] += run.wall_seconds
            s["wall_seconds_by_arm"][run.arm] = round(s["wall_seconds_by_arm"].get(run.arm, 0.0) + run.wall_seconds, 3)
            if run.peak_rss_mb is not None and (s["max_peak_rss_mb"] is None or run.peak_rss_mb > s["max_peak_rss_mb"]):
                s["max_peak_rss_mb"] = run.peak_rss_mb
    for s in steps.values():
        s["wall_seconds_total"] = round(s["wall_seconds_total"], 3)
        s["wall_seconds_by_arm"] = dict(sorted(s["wall_seconds_by_arm"].items()))
        s["outcomes"] = dict(sorted(s["outcomes"].items()))
        s["modes"] = dict(sorted(s["modes"].items()))
    return {"schema": SUMMARY_SCHEMA, "steps": dict(sorted(steps.items()))}


def render_summary(summary: Mapping[str, Any]) -> str:
    if not summary["steps"]:
        return "no ledger rows\n"
    lines = []
    for name, s in summary["steps"].items():
        arms = ", ".join(f"{arm} {sec:g}s" for arm, sec in s["wall_seconds_by_arm"].items()) or "none"
        outcomes = ", ".join(f"{k} {v}" for k, v in s["outcomes"].items())
        rss = "n/a" if s["max_peak_rss_mb"] is None else f"{s['max_peak_rss_mb']:g} MB"
        lines.append(f"{name}: {s['invocations']} invocation(s), {s['reruns']} rerun(s); runs {s['runs_executed']} executed, {s['runs_cached']} cached; "
                     f"wall {s['wall_seconds_total']:g}s ({arms}); max peak RSS {rss}; outcomes: {outcomes}; modes: "
                     + ", ".join(f"{k} {v}" for k, v in s["modes"].items()))
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    summary = sub.add_parser("summary", help="runs, reruns and wall time per measured step")
    summary.add_argument("--step")
    summary.add_argument("--since", type=dt.date.fromisoformat, metavar="YYYY-MM-DD")
    summary.add_argument("--json", action="store_true")
    summary.add_argument("--path", type=Path, help=f"the ledger file (default: ${ENV_PATH} or {DEFAULT_RELATIVE_PATH})")
    args = parser.parse_args(argv)
    rows, bad = read_rows(args.path or ledger_path())
    result = summarize(rows, step=args.step, since=args.since)
    if args.json:
        print(json.dumps({**result, "invalid_lines": bad}, sort_keys=True, indent=2))
    else:
        sys.stdout.write(render_summary(result))
        if bad:
            print(f"({bad} line(s) in the ledger were not valid run-ledger/v1 rows and are not counted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
