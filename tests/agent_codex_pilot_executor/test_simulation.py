from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api.agent_ops_dashboard.ingest import DashboardCache
from tools.agent_codex_pilot_executor.models import PilotSimulationContext
from tools.agent_codex_pilot_executor.simulation import simulate_pilot


TICKET_ID = "TCK-20260731-CODEX-PILOT-EXECUTOR"
EXECUTION_ID = "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400000-deadbeef"


def _payload() -> dict:
    fixture = Path("tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json")
    return json.loads(fixture.read_text(encoding="utf-8"))["raw_stdin_payload"]


def _context(root: Path) -> PilotSimulationContext:
    return PilotSimulationContext(
        scratch_root=root,
        ticket_id=TICKET_ID,
        execution_id=EXECUTION_ID,
        run_id="scratch-codex-pilot-1",
        start_ts="2026-08-01T00:00:00Z",
        end_ts="2026-08-01T00:00:02Z",
        post_tool_payload=_payload(),
        adapter_gate={"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1"},
    )


def _write_request(root: Path) -> None:
    request = root / "pilot_requests" / f"{TICKET_ID}.yaml"
    request.parent.mkdir(exist_ok=True)
    request.write_text(
        f"ticket_id: {TICKET_ID}\nhuman_owner: test\nrollback_plan_summary: delete scratch\n",
        encoding="utf-8",
    )


def test_simulation_writes_coherent_disposable_lifecycle_and_terminalizes_claim(tmp_path: Path):
    _write_request(tmp_path)

    result = simulate_pilot(_context(tmp_path))

    assert result.success is True
    assert result.claim is not None and result.claim.state == "completed"
    runs = [json.loads(line) for line in (tmp_path / "agent-monitoring" / "runs.jsonl").read_text().splitlines()]
    events = [json.loads(line) for line in (tmp_path / "agent-monitoring" / "events.jsonl").read_text().splitlines()]
    tools = [json.loads(line) for line in (tmp_path / "agent-monitoring" / "tools.jsonl").read_text().splitlines()]
    assert len(runs) == 1 and len(events) == 2 and len(tools) == 1
    assert {row["execution_id"] for row in [*runs, *events, *tools]} == {EXECUTION_ID}
    assert tools[0]["seq"] == events[-1]["seq"]
    serialized_tool = json.dumps(tools[0])
    raw = _payload()
    assert raw["tool_response"] not in serialized_tool
    for forbidden in ("transcript_path", "cwd", "model", "permission_mode", "turn_id", "tool_use_id"):
        assert forbidden not in tools[0]


def test_simulation_rejects_unexpected_adapter_suffix_and_marks_claim_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import tools.agent_codex_pilot_executor.simulation as simulation

    _write_request(tmp_path)
    original = simulation.process_post_tool_use

    def append_extra(*args, **kwargs):
        assert original(*args, **kwargs)
        target = kwargs["target_path"]
        target.write_text(target.read_text(encoding="utf-8") + '{"unexpected":true}\n', encoding="utf-8")
        return True

    monkeypatch.setattr(simulation, "process_post_tool_use", append_extra)
    result = simulation.simulate_pilot(_context(tmp_path))
    assert result.success is False
    assert result.boundary == "lifecycle:LifecycleProofError"
    assert result.claim is not None and result.claim.state == "failed"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda lines: lines.__setitem__(0, "{\"changed\":true}\n"),
        lambda lines: lines.pop(0),
        lambda lines: lines.reverse(),
    ],
)
def test_simulation_prefix_gate_rejects_altered_deleted_or_reordered_history(
    tmp_path: Path, mutation, monkeypatch: pytest.MonkeyPatch
):
    import tools.agent_codex_pilot_executor.simulation as simulation

    _write_request(tmp_path)
    original_capture = simulation.capture_pilot_baseline
    calls = 0

    def capture_then_mutate(directory: Path):
        nonlocal calls
        snapshot = original_capture(directory)
        calls += 1
        if calls == 1:
            # Populate a genuine historical prefix only after baseline capture's
            # first invocation would otherwise be empty; the next snapshot must reject it.
            for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
                (directory / filename).write_text('{"historical":true}\n', encoding="utf-8")
            return original_capture(directory)
        if calls == 2:
            for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
                path = directory / filename
                lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
                mutation(lines)
                path.write_text("".join(lines), encoding="utf-8")
            return original_capture(directory)
        return snapshot

    monkeypatch.setattr(simulation, "capture_pilot_baseline", capture_then_mutate)
    result = simulation.simulate_pilot(_context(tmp_path))
    assert result.success is False
    assert result.boundary == "lifecycle:PilotManifestDriftError"


def test_simulation_failure_after_claim_retains_failed_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import tools.agent_codex_pilot_executor.simulation as simulation

    _write_request(tmp_path)
    monkeypatch.setattr(simulation.dependencies, "write_line", lambda *_args: False)
    result = simulation.simulate_pilot(_context(tmp_path))
    assert result.success is False
    assert result.boundary == "lifecycle:LifecycleProofError"
    assert result.claim is not None and result.claim.state == "failed"


def test_dashboard_does_not_treat_an_old_tool_only_row_as_completed_pilot(tmp_path: Path):
    monitoring = tmp_path / "agent-monitoring"
    monitoring.mkdir()
    for filename in ("runs.jsonl", "events.jsonl"):
        (monitoring / filename).touch()
    (monitoring / "tools.jsonl").write_text(
        json.dumps(
            {
                "run_id": "tool-only",
                "provider": "codex",
                "execution_id": EXECUTION_ID,
                "seq": 2,
                "tool": "Bash",
                "ts": "2000-01-01T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cache = DashboardCache(repo_root=tmp_path)
    assert cache.get_run("tool-only") is None
