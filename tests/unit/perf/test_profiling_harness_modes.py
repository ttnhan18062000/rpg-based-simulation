from __future__ import annotations

import os
from pathlib import Path
import pytest

from scripts.profile_engine import ProfilingHarness
from src.config.profiles import PROD_SMALL


def test_profiling_pure_mode_sets_clean_compute_flags(tmp_path: Path) -> None:
    """
    Verify that pure mode sets no_replay=True, no_frame_pacing=True, audit_mode=False
    and generates correctly named output files.
    """
    harness = ProfilingHarness(tmp_path)
    harness.run_scenario("idle", entity_count=10, ticks=2, profile=PROD_SMALL, mode="pure")

    kernel = harness.last_kernel
    assert kernel is not None
    assert kernel._no_replay is True
    assert kernel._no_frame_pacing is True
    assert kernel._audit_mode is False

    prof_file = tmp_path / "idle_10_pure.prof"
    txt_file = tmp_path / "idle_10_pure.txt"
    assert prof_file.exists()
    assert txt_file.exists()


def test_profiling_runtime_mode_allows_replay_and_frame_pacing(tmp_path: Path) -> None:
    """
    Verify that runtime mode allows replay and frame pacing by setting no_replay=False,
    no_frame_pacing=False, audit_mode=False.
    """
    harness = ProfilingHarness(tmp_path)
    harness.run_scenario("idle", entity_count=10, ticks=2, profile=PROD_SMALL, mode="runtime")

    kernel = harness.last_kernel
    assert kernel is not None
    assert kernel._no_replay is False
    assert kernel._no_frame_pacing is False
    assert kernel._audit_mode is False

    prof_file = tmp_path / "idle_10_runtime.prof"
    txt_file = tmp_path / "idle_10_runtime.txt"
    assert prof_file.exists()
    assert txt_file.exists()


def test_profiling_audit_mode_enables_audit_without_frame_pacing(tmp_path: Path) -> None:
    """
    Verify that audit mode enables audit_mode=True and disables frame pacing (no_frame_pacing=True).
    """
    harness = ProfilingHarness(tmp_path)
    harness.run_scenario("idle", entity_count=10, ticks=2, profile=PROD_SMALL, mode="audit")

    kernel = harness.last_kernel
    assert kernel is not None
    assert kernel._no_replay is False
    assert kernel._no_frame_pacing is True
    assert kernel._audit_mode is True

    prof_file = tmp_path / "idle_10_audit.prof"
    txt_file = tmp_path / "idle_10_audit.txt"
    assert prof_file.exists()
    assert txt_file.exists()


def test_profile_output_includes_mode_and_flags(tmp_path: Path) -> None:
    """
    Verify that both report.md and the text profile summary explicitly record the mode and flags used.
    """
    harness = ProfilingHarness(tmp_path)
    harness.run_scenario("idle", entity_count=15, ticks=2, profile=PROD_SMALL, mode="pure")

    txt_file = tmp_path / "idle_15_pure.txt"
    report_file = tmp_path / "report.md"

    txt_content = txt_file.read_text(encoding="utf-8")
    assert "Mode: pure" in txt_content
    assert "'no_replay': True" in txt_content
    assert "'no_frame_pacing': True" in txt_content
    assert "'audit_mode': False" in txt_content

    report_content = report_file.read_text(encoding="utf-8")
    assert "- **Mode**: pure" in report_content
    assert "- **Flags**: `{'no_replay': True, 'no_frame_pacing': True, 'audit_mode': False}`" in report_content


def test_profile_report_does_not_claim_gc_resilience_without_gc_metrics(tmp_path: Path) -> None:
    """
    Verify that the profiling report explicitly states that GC resilience and memory non-fragmentation
    cannot be claimed without active GC/RSS metrics.
    """
    harness = ProfilingHarness(tmp_path)
    harness.run_scenario("idle", entity_count=15, ticks=2, profile=PROD_SMALL, mode="runtime")

    report_file = tmp_path / "report.md"
    report_content = report_file.read_text(encoding="utf-8")

    assert "no claims regarding GC resilience, lack of memory leaks, or absence of heap fragmentation can be made from this report** without explicit GC and RSS telemetry verification" in report_content
