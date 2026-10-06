#!/usr/bin/env python3
"""The `gate_verdicts` shard family: one row per gate verdict a gate CLI prints
(TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES, child 1 of TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER).

Gate CLIs print PASS/FAIL to stdout and keep nothing, so whether a gate was right can only be
noticed by a person. This module gives them one place to write the verdict, the gate it came from
and what it looked at. Later children add outcomes, adjudication and a precision report on top.

Rows go to `data/<ISO-week>/<batch-identifier>.gate_verdicts.jsonl` through the shared
`writer.py::write_line()` and `monitoring_batch_identifier.resolve_write_target()`, like every other
shard family. Writing never raises and never changes a CLI's exit code or stdout: a failure prints one
warning to stderr.

Opt out per call with `--no-record` (the CLIs map it to `enabled=False`) or per process with
`GATE_VERDICT_NO_RECORD=1`; `tests/conftest.py` sets the env var so no test writes into the real data
root. `GATE_VERDICT_EXECUTION_MODE` labels the row when the caller is not a hand closure (the
native-run backstop and the pipeline set it).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from monitoring_batch_identifier import resolve_write_target  # noqa: E402
from writer import write_line  # noqa: E402

_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))
from tools.agent_working_paths import AGENT_ORCHESTRATION  # noqa: E402

KIND = "gate_verdicts"
EXECUTION_MODES = ("pipeline", "workflow", "hand")
SUB_RESULT_VALUES = ("PASS", "FAIL", "NA")
ENV_NO_RECORD = "GATE_VERDICT_NO_RECORD"
ENV_EXECUTION_MODE = "GATE_VERDICT_EXECUTION_MODE"
ROW_KIND_OUTCOME = "outcome"
ROW_KIND_ADJUDICATION = "adjudication"
OUTCOMES = ("accepted", "fixed_and_rerun", "rerun_no_change", "overridden", "stopped")
ADJUDICATIONS = ("true_block", "false_block", "true_pass", "false_pass", "unknown")
REQUIRED_FIELDS = ("ts", "gate_verdict_id", "execution_mode", "gate_id", "gate_type", "verdict", "blocking", "inputs_ref")

_POLICY_PATH = _REPO_ROOT / AGENT_ORCHESTRATION / "gate-policy.yaml"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def recording_disabled() -> bool:
    return os.environ.get(ENV_NO_RECORD, "").strip().lower() in ("1", "true", "yes")


def resolve_execution_mode(default: str = "hand") -> str:
    mode = os.environ.get(ENV_EXECUTION_MODE, "").strip()
    return mode if mode in EXECUTION_MODES else default


def gate_id_for(module: str, function: str | None = None, policy_path: Path = _POLICY_PATH) -> str:
    """`<phase>:<check_module>.<check_function>` when gate-policy.yaml registers the module (and the
    function, when given); otherwise the stable `cli:<module>` id. gate-policy.yaml is the gate_id
    source, so a gate that is in it keeps the same id wherever it is recorded from."""
    short = module.split(".")[-1]
    try:
        import yaml  # noqa: PLC0415 - only needed when a verdict is recorded
        gates = (yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}).get("gates", [])
        for gate in gates:
            check_module = str(gate.get("check_module", ""))
            if check_module.split(".")[-1] != short:
                continue
            if function is not None and gate.get("check_function") != function:
                continue
            return f"{gate['phase']}:{check_module}.{gate['check_function']}"
    except Exception:  # noqa: BLE001 - a policy read problem must not stop a verdict being recorded
        pass
    return f"cli:{short}"


def head_sha() -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
    except Exception:  # noqa: BLE001
        return None
    return (proc.stdout.strip() or None) if proc.returncode == 0 else None


def build_record(
    *,
    gate_id: str,
    gate_type: str,
    verdict: str,
    blocking: bool,
    inputs_ref: dict,
    phase: str | None = None,
    ticket_id: str | None = None,
    sub_results: dict | None = None,
    execution_mode: str | None = None,
    run_id: str | None = None,
    execution_id: str | None = None,
    session_id: str | None = None,
    now: str | None = None,
) -> dict:
    record = {
        "ts": now or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "gate_verdict_id": f"gv-{uuid.uuid4().hex[:16]}",
        "run_id": run_id,
        "execution_id": execution_id,
        "session_id": session_id if session_id is not None else (os.environ.get("CLAUDE_CODE_SESSION_ID") or None),
        "execution_mode": execution_mode or resolve_execution_mode(),
        "ticket_id": ticket_id,
        "gate_id": gate_id,
        "gate_type": gate_type,
        "phase": phase,
        "verdict": verdict,
        "blocking": bool(blocking),
        "inputs_ref": inputs_ref,
    }
    if sub_results is not None:
        record["sub_results"] = sub_results
    return record


def validate_ledger_row(record: dict) -> list[str]:
    """Problems with an `outcome` or `adjudication` row (TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION)."""
    kind = record["row_kind"]
    if kind == ROW_KIND_OUTCOME:
        value_field, allowed, required = "outcome", OUTCOMES, ("ts", "gate_verdict_id", "outcome")
    elif kind == ROW_KIND_ADJUDICATION:
        value_field, allowed = "adjudication", ADJUDICATIONS
        required = ("ts", "gate_verdict_id", "adjudication", "adjudicated_by", "reason")
    else:
        return [f"row_kind {kind!r} not in {(ROW_KIND_OUTCOME, ROW_KIND_ADJUDICATION)}"]
    problems = [f"missing {f}" for f in required if record.get(f) in (None, "")]
    if record.get(value_field) not in (None, "") and record[value_field] not in allowed:
        problems.append(f"{value_field} {record[value_field]!r} not in {allowed}")
    return problems


def validate_record(record: object) -> list[str]:
    """Problems with one row, empty when it is valid. Never raises."""
    if not isinstance(record, dict):
        return ["row is not an object"]
    if "row_kind" in record:
        return validate_ledger_row(record)
    problems = [f"missing {f}" for f in REQUIRED_FIELDS if record.get(f) in (None, "")]
    if "blocking" in record and not isinstance(record["blocking"], bool):
        problems.append("blocking is not a bool")
    if record.get("execution_mode") not in EXECUTION_MODES and "missing execution_mode" not in problems:
        problems.append(f"execution_mode {record.get('execution_mode')!r} not in {EXECUTION_MODES}")
    if "inputs_ref" in record and not isinstance(record["inputs_ref"], dict):
        problems.append("inputs_ref is not an object")
    sub = record.get("sub_results")
    if sub is not None:
        if not isinstance(sub, dict):
            problems.append("sub_results is not an object")
        else:
            problems.extend(f"sub_results[{k!r}]={v!r} not in {SUB_RESULT_VALUES}" for k, v in sub.items() if v not in SUB_RESULT_VALUES)
    return problems


def record_gate_verdict(*, enabled: bool = True, target: Path | None = None, **fields) -> dict | None:
    """Build, validate and append one row. Returns the row, or None when nothing was written (opted
    out, invalid, or the write failed). Never raises; a failure prints one warning to stderr."""
    if not enabled or recording_disabled():
        return None
    try:
        record = build_record(**fields)
        problems = validate_record(record)
        if problems:
            print(f"WARNING: gate verdict not recorded: {'; '.join(problems)}", file=sys.stderr)
            return None
        week = datetime.now(timezone.utc).strftime("%G-W%V")
        path = target if target is not None else resolve_write_target(KIND, iso_week=week)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not write_line(path, json.dumps(record, separators=(",", ":"))):
            print(f"WARNING: gate verdict not recorded: write to {path} failed", file=sys.stderr)
            return None
        return record
    except Exception as exc:  # noqa: BLE001 - monitoring must never fail a gate
        print(f"WARNING: gate verdict not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
