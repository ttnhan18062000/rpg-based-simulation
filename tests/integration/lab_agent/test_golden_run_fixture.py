"""
Golden run fixture tests.

Verifies that RegisterSimulationResultWorkflow can consume real engine-produced
artifact structure (represented by the golden fixture in
tests/fixtures/lab_runs/minimal_completed_run/).

Unlike the synthetic hand-written tests in test_register_simulation_result_workflow.py,
these tests validate schema compatibility between the fixture and LabRunManifest.
"""
import json
import shutil
import pytest
from pathlib import Path

from src.lab.request import WorkflowRequest
from src.lab.schema import LabRunManifest
from src.lab.session import LabSessionStore
from src.lab.workflows import RegisterSimulationResultWorkflow

pytestmark = [pytest.mark.integration, pytest.mark.e2e_golden]

_FIXTURE_SRC = Path("tests/fixtures/lab_runs/minimal_completed_run")
_FIXTURE_RUN_ID = "minimal-completed-run"


@pytest.fixture
def golden_run_workspace(tmp_path: Path) -> Path:
    """Copy the golden fixture into a fully wired workspace and patch artifact_root."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)

    run_dst = tmp_path / "data" / "lab_runs" / _FIXTURE_RUN_ID
    shutil.copytree(_FIXTURE_SRC, run_dst)

    manifest_path = run_dst / "lab_run_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["artifact_root"] = str(run_dst)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    store.create_session("session_golden_01")
    return tmp_path


def test_golden_fixture_registers_successfully(golden_run_workspace: Path):
    """RegisterSimulationResultWorkflow must accept the golden fixture without error."""
    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": f"data/lab_runs/{_FIXTURE_RUN_ID}"},
    )
    workflow = RegisterSimulationResultWorkflow(workspace_root=golden_run_workspace)
    res = workflow.run("session_golden_01", request)

    assert res["status"] == "READY", f"Expected READY, got: {res}"
    assert res["classification"] == "COMPLETE"
    assert res["lab_run_id"] == _FIXTURE_RUN_ID

    reg_dir = (
        golden_run_workspace / "data" / "lab_sessions" / "session_golden_01" / "registration"
    )
    assert (reg_dir / "artifact_index.json").is_file()
    assert (reg_dir / "result_integrity_report.json").is_file()
    assert (reg_dir / "actual_lab_run_path.txt").is_file()

    # Verify completed_run_count in registration report matches fixture
    with open(reg_dir / "result_integrity_report.json", encoding="utf-8") as f:
        report = json.load(f)
    assert report["completed_run_count"] == 1
    assert report["failed_run_count"] == 0


def test_golden_fixture_manifest_matches_schema():
    """Golden fixture lab_run_manifest.json must parse cleanly via LabRunManifest."""
    with open(_FIXTURE_SRC / "lab_run_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    # Patch sentinel so the model validator passes
    data["artifact_root"] = "/tmp/fixture_schema_check"
    manifest = LabRunManifest(**data)
    assert manifest.lab_run_id == _FIXTURE_RUN_ID
    assert manifest.status == "COMPLETED"
    assert manifest.run_count == manifest.completed_run_count


def test_missing_fixture_blocks_registration(tmp_path: Path):
    """Missing run directory must block registration with status BLOCKED."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    store.create_session("session_missing_01")

    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": "data/lab_runs/nonexistent-run"},
    )
    workflow = RegisterSimulationResultWorkflow(workspace_root=tmp_path)
    res = workflow.run("session_missing_01", request)

    assert res["status"] == "BLOCKED"
    assert "MISSING" in res.get("reason", "") or "does not exist" in res.get("reason", "").lower()


def test_corrupt_manifest_blocks_registration(tmp_path: Path):
    """Corrupt lab_run_manifest.json must block registration with status BLOCKED."""
    (tmp_path / "data" / "lab_sessions").mkdir(parents=True)
    store = LabSessionStore(tmp_path / "data" / "lab_sessions")
    store.create_session("session_corrupt_01")

    run_dst = tmp_path / "data" / "lab_runs" / _FIXTURE_RUN_ID
    shutil.copytree(_FIXTURE_SRC, run_dst)
    (run_dst / "lab_run_manifest.json").write_text("{ invalid json <<<", encoding="utf-8")

    request = WorkflowRequest(
        workflow="RegisterSimulationResult",
        mode="specific",
        specific_inputs={"lab_run_path": f"data/lab_runs/{_FIXTURE_RUN_ID}"},
    )
    workflow = RegisterSimulationResultWorkflow(workspace_root=tmp_path)
    res = workflow.run("session_corrupt_01", request)

    assert res["status"] == "BLOCKED"
