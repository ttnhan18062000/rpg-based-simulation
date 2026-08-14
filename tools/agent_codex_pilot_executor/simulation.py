"""Compose an entirely disposable, provider-attributed lifecycle fixture."""
from __future__ import annotations

import json
from pathlib import Path

from src.api.agent_ops_dashboard.ingest import DashboardCache
from tools.agent_codex_pilot_guardrails.baseline_manifest_gate import (
    assert_pilot_baseline_preserved,
    capture_pilot_baseline,
)
from tools.agent_codex_posttool_adapter.adapter import process_post_tool_use
from tools.agent_codex_posttool_adapter.input_model import parse_payload
from tools.agent_codex_posttool_adapter.record_builder import build_record

from . import dependencies
from .claims import acquire_claim, terminalize_claim
from .errors import LifecycleProofError, PilotExecutorError, PreflightRefusedError
from .models import PilotSimulationContext, SimulationResult
from .preflight import preflight

_MONITORING_FILES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


def _seed_monitoring(monitoring_dir: Path) -> None:
    monitoring_dir.mkdir(parents=True, exist_ok=True)
    for filename in _MONITORING_FILES:
        (monitoring_dir / filename).touch(exist_ok=True)


def _lines(records: list[dict]) -> list[str]:
    return [json.dumps(record, separators=(",", ":")) + "\n" for record in records]


def _assert_exact_suffix(pre: dict[str, list[str]], post: dict[str, list[str]], expected: dict[str, list[dict]]) -> None:
    for filename, records in expected.items():
        actual = post[filename][len(pre[filename]) :]
        if actual != _lines(records):
            raise LifecycleProofError(f"{filename}: unexpected scratch lifecycle suffix")


def _dashboard_proof(context: PilotSimulationContext, event_records: list[dict]) -> None:
    cache = DashboardCache(repo_root=context.scratch_root)
    runs = cache.get_runs(provider="codex", execution_id=context.execution_id)
    if len([run for run in runs if run.run_id == context.run_id]) != 1:
        raise LifecycleProofError("dashboard did not expose the synthetic Codex run")
    detail = cache.get_run(context.run_id)
    timeline = cache.get_timeline(context.run_id)
    if detail is None or timeline is None or len(timeline.entries) != len(event_records):
        raise LifecycleProofError("dashboard lifecycle/timeline proof failed")
    post_seq = event_records[-1]["seq"]
    if not timeline.entries[-1].tool_calls or timeline.entries[-1].seq != post_seq:
        raise LifecycleProofError("dashboard did not attach PostToolUse tool row")


def _declared_adapter_tool_record(context: PilotSimulationContext) -> dict:
    """Build the one allowed adapter append *before* asking the adapter to write.

    This deliberately reuses the adapter's parser and record builder instead of
    treating the row read back from disk as its own specification.  The later
    suffix proof can therefore reject an unexpected, redacted-differently, or
    additional adapter write.
    """
    payload = parse_payload(context.post_tool_payload)
    return build_record(
        payload,
        execution_id=context.execution_id,
        provider="codex",
        ticket_id=context.ticket_id,
        run_id=context.run_id,
        seq=2,
        phase="PostToolUse",
        agent="executor",
        now=context.end_ts,
    )


def simulate_pilot(context: PilotSimulationContext) -> SimulationResult:
    """Run a scratch-only synthetic lifecycle and retain a terminal claim marker.

    A refusal before a claim has no durable scratch monitoring effect.  Once an
    active claim exists, every write/proof failure terminalizes it as failed.
    """
    try:
        paths = preflight(context)
    except PilotExecutorError as exc:
        reason = exc.reason if isinstance(exc, PreflightRefusedError) else type(exc).__name__
        return SimulationResult(False, f"preflight:{reason}", None)

    try:
        claim = acquire_claim(context.scratch_root, context.ticket_id, context.execution_id)
    except PilotExecutorError as exc:
        return SimulationResult(False, f"claim:{type(exc).__name__}", None)

    try:
        _seed_monitoring(paths.monitoring_dir)
        baseline = capture_pilot_baseline(paths.monitoring_dir)
        run = {
            "run_id": context.run_id,
            "start_ts": context.start_ts,
            "end_ts": context.end_ts,
            "workflow": "codex-pilot-simulation",
            "tier": "standard",
            "final_status": "DONE",
            "agent_count": 1,
            "ticket_id": context.ticket_id,
            "provider": "codex",
            "execution_id": context.execution_id,
        }
        run["duration_s"] = dependencies.record_run.compute_duration_s(run)
        events = [
            {
                "run_id": context.run_id,
                "seq": 1,
                "ts": context.start_ts,
                "phase": "Scope",
                "agent": "executor",
                "summary": "scratch preflight completed",
                "status": "ok",
                "ticket_id": context.ticket_id,
                "provider": "codex",
                "execution_id": context.execution_id,
            },
            {
                "run_id": context.run_id,
                "seq": 2,
                "ts": context.end_ts,
                "phase": "PostToolUse",
                "agent": "executor",
                "summary": "synthetic PostToolUse captured",
                "status": "ok",
                "ticket_id": context.ticket_id,
                "provider": "codex",
                "execution_id": context.execution_id,
            },
        ]
        expected_tool = _declared_adapter_tool_record(context)
        if dependencies.record_run.validate_record(run):
            raise LifecycleProofError("shared run validator refused synthetic record")
        if any(dependencies.record_events.validate_record(event) for event in events):
            raise LifecycleProofError("shared event validator refused synthetic record")
        if not dependencies.write_line(paths.monitoring_dir / "runs.jsonl", json.dumps(run, separators=(",", ":"))):
            raise LifecycleProofError("shared run writer failed")
        if not dependencies.write_lines(
            paths.monitoring_dir / "events.jsonl", [line.rstrip("\n") for line in _lines(events)]
        ):
            raise LifecycleProofError("shared event writer failed")
        if not process_post_tool_use(
            context.post_tool_payload,
            target_path=paths.monitoring_dir / "tools.jsonl",
            execution_id=context.execution_id,
            ticket_id=context.ticket_id,
            run_id=context.run_id,
            seq=2,
            phase="PostToolUse",
            agent="executor",
            env=context.adapter_gate,
            now=context.end_ts,
        ):
            raise LifecycleProofError("adapter tool writer failed")
        post = capture_pilot_baseline(paths.monitoring_dir)
        assert_pilot_baseline_preserved(baseline, post)
        _assert_exact_suffix(
            baseline,
            post,
            {"runs.jsonl": [run], "events.jsonl": events, "tools.jsonl": [expected_tool]},
        )
        _dashboard_proof(context, events)
        terminal = terminalize_claim(context.scratch_root, context.ticket_id, context.execution_id, "completed")
        return SimulationResult(True, "completed", terminal)
    except Exception as exc:
        try:
            terminal = terminalize_claim(context.scratch_root, context.ticket_id, context.execution_id, "failed")
        except Exception:
            terminal = claim
        return SimulationResult(False, f"lifecycle:{type(exc).__name__}", terminal)
