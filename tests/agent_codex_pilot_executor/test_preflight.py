from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_codex_pilot_executor.models import PilotSimulationContext
from tools.agent_codex_pilot_executor.preflight import preflight
from tools.agent_codex_pilot_executor.simulation import simulate_pilot


TICKET_ID = "TCK-20260731-CODEX-PILOT-EXECUTOR"
EXECUTION_ID = "codex-TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400000-deadbeef"


def _context(root: Path, **overrides) -> PilotSimulationContext:
    values = dict(
        scratch_root=root,
        ticket_id=TICKET_ID,
        execution_id=EXECUTION_ID,
        run_id="scratch-codex-pilot-1",
        start_ts="2026-08-01T00:00:00Z",
        end_ts="2026-08-01T00:00:02Z",
        post_tool_payload={},
        adapter_gate={"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1"},
    )
    values.update(overrides)
    return PilotSimulationContext(**values)


def test_traversal_ticket_refuses_before_creating_scratch_paths(tmp_path: Path):
    context = _context(
        tmp_path,
        ticket_id="../TCK-20260731-CODEX-PILOT-EXECUTOR",
        execution_id="codex-../TCK-20260731-CODEX-PILOT-EXECUTOR-1722470400000-deadbeef",
    )
    with pytest.raises(Exception):
        preflight(context)
    assert not (tmp_path / "claims").exists()
    assert not (tmp_path / "agent-monitoring").exists()


def test_repository_root_is_not_a_valid_scratch_root():
    repo = Path(__file__).resolve().parents[2]
    with pytest.raises(Exception):
        preflight(_context(repo))


@pytest.mark.parametrize(
    ("request_text", "expected_reason"),
    [
        (None, "request_missing_or_malformed"),
        (f"ticket_id: {TICKET_ID}\nrollback_plan_summary: x\n", "request_missing_human_owner"),
        (f"ticket_id: {TICKET_ID}\nhuman_owner: x\n", "request_missing_rollback_plan"),
        (f"ticket_id: TCK-20260101-OTHER\nhuman_owner: x\nrollback_plan_summary: x\n", "request_ticket_mismatch"),
    ],
)
def test_preflight_reports_gate_specific_request_refusal_without_side_effects(
    tmp_path: Path, request_text: str | None, expected_reason: str
):
    if request_text is not None:
        request = tmp_path / "pilot_requests" / f"{TICKET_ID}.yaml"
        request.parent.mkdir()
        request.write_text(request_text, encoding="utf-8")
    result = simulate_pilot(_context(tmp_path))
    assert result.success is False
    assert result.boundary == f"preflight:{expected_reason}"
    assert not (tmp_path / "claims").exists()
    assert not (tmp_path / "agent-monitoring").exists()


def test_preflight_identity_and_surface_refusals_are_specific_and_do_not_call_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import tools.agent_codex_pilot_executor.preflight as preflight_module

    calls: list[str] = []
    original_select = preflight_module.select_pilot_candidate
    monkeypatch.setattr(
        preflight_module,
        "select_pilot_candidate",
        lambda *_args: calls.append("request") or (_ for _ in ()).throw(AssertionError("unexpected request call")),
    )
    invalid = _context(
        tmp_path,
        ticket_id="../bad",
        execution_id="codex-../bad-1722470400000-deadbeef",
    )
    result = simulate_pilot(invalid)
    assert result.boundary == "preflight:identity_invalid"
    assert calls == []
    monkeypatch.setattr(preflight_module, "select_pilot_candidate", original_select)

    request = tmp_path / "pilot_requests" / f"{TICKET_ID}.yaml"
    request.parent.mkdir()
    request.write_text(
        f"ticket_id: {TICKET_ID}\nhuman_owner: x\nrollback_plan_summary: x\n", encoding="utf-8"
    )
    surface = _context(tmp_path, enabled_hook_events=frozenset({"PreToolUse"}))
    result = simulate_pilot(surface)
    assert result.boundary == "preflight:surface_not_evidenced"
    assert not (tmp_path / "claims").exists()
    assert not (tmp_path / "agent-monitoring").exists()


def test_symlinked_scratch_root_is_refused_before_request_or_claim_io(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(target, target_is_directory=True)
    # A symlink to the repository is specifically an unsafe injected root.
    repo_link = tmp_path / "repo-link"
    repo_link.symlink_to(Path(__file__).resolve().parents[2], target_is_directory=True)
    result = simulate_pilot(_context(repo_link))
    assert result.boundary == "preflight:scratch_path_unsafe"
    assert not (target / "claims").exists()
