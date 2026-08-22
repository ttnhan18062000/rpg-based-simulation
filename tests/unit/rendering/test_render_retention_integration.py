"""Documents and tests the REAL, unmodified retention.py behavior toward a
data/runs/{run_id}/renders/ subdirectory.

TCK-20260821-WORLD-RENDER-CORE, resolving investigation.md's Risk #1: AC #4
("render output ... is correctly aged/pruned by the existing RetentionPolicy with
zero changes made to retention.py") is NOT literally true of RetentionManager's
current normal-expiry path — RetentionManager.generate_cleanup_plan() builds a
hardcoded per-run "files" list (13 specific telemetry filenames) that does not
include a renders/ subdirectory, and execute_cleanup()'s normal-expiry branch only
ever os.remove()s files named in that literal list. A renders/ subdirectory is
therefore left untouched by ordinary per-file expiry.

The only path that removes an entire run directory (renders/ included) is
execute_cleanup()'s `"full directory" in details["reason"] or
details["reason"].startswith("Evaluation error")` check. Confirmed by direct
execution against the real, unmodified code that this check is met ONLY by the
`except Exception` / evaluation-error branch of generate_cleanup_plan() (reason
literally starts with "Evaluation error: ...") -- NOT by the merely-missing-
run_manifest.json branch, whose reason string ("Corrupted or missing
run_manifest.json") does not contain "full directory" (only its sibling `"files"`
list does, which execute_cleanup's condition does not check). A run with a
missing manifest is therefore flagged eligible but its directory is never actually
removed by today's code -- execute_cleanup falls through to the per-file loop,
tries to os.remove() a literal file named "* (full directory)" that never exists,
and leaves the run (renders/ included) on disk indefinitely. This is a real,
pre-existing quirk of retention.py's reason-string/files-list mismatch, not
something this ticket introduces or may fix (zero edits to retention.py).

This test proves the real, current behavior against the real, unmodified
RetentionManager.execute_cleanup() -- it does not assert the AC's more
optimistic literal wording, and it must not be "fixed" by adding renders/-related
entries to retention.py's hardcoded file list (see plan.md's Scope Guards — zero
edits to retention.py).
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.retention import RetentionManager


def _write_manifest(run_dir: str, run_id: str, started_at: str) -> dict:
    m_data = {
        "run_id": run_id,
        "scenario_name": "scen",
        "scenario_type": "comb",
        "seed": 42,
        "observability_mode": "LIGHT",
        "started_at": started_at,
        "ticks_requested": 10,
        "ticks_completed": 10,
        "status": "COMPLETED",
        "artifact_schema_version": "observability_artifact_v1",
    }
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m_data, f)
    return m_data


def _make_renders_dir(run_dir: str) -> str:
    renders_dir = os.path.join(run_dir, "renders")
    os.makedirs(renders_dir)
    with open(os.path.join(renders_dir, "tick_0000.png"), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    return renders_dir


def test_renders_directory_not_pruned_by_normal_expiry(tmp_path):
    run_dir = os.path.join(str(tmp_path), "run-normal")
    os.makedirs(run_dir)
    renders_dir = _make_renders_dir(run_dir)
    m_data = _write_manifest(run_dir, "run-normal", "2020-05-20T00:00:00Z")  # extremely old, must expire

    events_file = os.path.join(run_dir, "simulation_events.jsonl")
    with open(events_file, "w") as f:
        f.write("{}\n")

    with patch("src.observability.reporting.retention.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        mock_repo.read_manifest.return_value = RunManifest.model_validate(m_data)
        mock_repo_class.return_value = mock_repo

        manager = RetentionManager(repo=mock_repo)
        manager.execute_cleanup()

    # Existing, unchanged behavior: hardcoded telemetry files get pruned.
    assert not os.path.exists(events_file)
    # renders/ is not in retention.py's hardcoded file list -- normal per-file
    # expiry leaves it untouched.
    assert os.path.exists(renders_dir)
    assert os.path.exists(os.path.join(renders_dir, "tick_0000.png"))


def test_renders_directory_removed_with_full_run_purge_on_evaluation_error(tmp_path):
    # A run whose manifest file exists on disk (bypassing the "missing manifest"
    # branch, which does not actually purge -- see module docstring) but raises
    # during RunArtifactRepository.read_manifest -- the one path that reaches
    # execute_cleanup()'s shutil.rmtree(run_dir) branch.
    run_dir = os.path.join(str(tmp_path), "run-eval-error")
    os.makedirs(run_dir)
    renders_dir = _make_renders_dir(run_dir)
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        f.write("not valid json")

    with patch("src.observability.reporting.retention.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        mock_repo.read_manifest.side_effect = ValueError("corrupted manifest content")
        mock_repo_class.return_value = mock_repo

        manager = RetentionManager(repo=mock_repo)
        manager.execute_cleanup()

    assert not os.path.exists(run_dir)
    assert not os.path.exists(renders_dir)


def test_renders_directory_survives_missing_manifest_run_today(tmp_path):
    # Documents the real (surprising) current behavior: a run with a genuinely
    # missing run_manifest.json is flagged eligible by generate_cleanup_plan(),
    # but execute_cleanup() never actually removes it -- its reason string
    # ("Corrupted or missing run_manifest.json") does not satisfy the
    # "full directory" / "Evaluation error" check, so the directory (renders/
    # included) is left on disk. Not something this ticket may fix (zero edits
    # to retention.py) -- documented here so a future retention.py change does
    # not silently invalidate this ticket's AC #4 resolution without review.
    run_dir = os.path.join(str(tmp_path), "run-missing-manifest")
    renders_dir = _make_renders_dir(run_dir)

    with patch("src.observability.reporting.retention.RunArtifactRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.base_dir = str(tmp_path)
        mock_repo_class.return_value = mock_repo

        manager = RetentionManager(repo=mock_repo)
        manager.execute_cleanup()

    assert os.path.exists(run_dir)
    assert os.path.exists(renders_dir)
