"""Tests for tools/agent_replay/pilot_isolation.py (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #4).

Runs against the REAL repository tree, mirroring tests/agent_replay/test_no_mutation_snapshot.py's
own precedent (a tmp_path copy would make the assertion vacuously true).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import load_fixture  # noqa: E402
from agent_replay.pilot_isolation import (  # noqa: E402
    IsolationSnapshot,
    _UNSCOPED_SIDECAR_RELPATH,
    assert_isolation_held,
    capture,
    run_pilot_isolated,
)
from agent_replay_codex.errors import ContainmentViolationError  # noqa: E402

_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)


def test_isolation_produces_zero_diff_across_agent_monitoring_shards():
    fixture = load_fixture(_REAL_FIXTURE_PATH)

    run1_outcomes, run2_outcomes, timing, evidence = run_pilot_isolated([fixture], _REPO_ROOT)

    assert len(run1_outcomes) == 1
    assert len(run2_outcomes) == 1
    assert run1_outcomes[0].final_status == run2_outcomes[0].final_status == "ok"
    assert evidence.held is True, evidence.violation
    assert "run1_wall_clock_s" in timing and "run2_wall_clock_s" in timing


def test_isolation_watch_set_actually_detects_a_deliberate_mutation():
    """Regression guard mirroring test_no_mutation_snapshot.py's own precedent — proves the
    watch set actually fires on a real mutation under the sharded agent-monitoring/data/ layout,
    not merely that the snapshot helpers run without error (the exact vacuous-pass failure mode
    a naive 'assert no diff' implementation could silently have)."""
    probe_path = (
        _REPO_ROOT / "agent-monitoring" / "data" / "unknown-week" / "_pilot_isolation_probe.jsonl"
    )
    assert not probe_path.exists(), "stale probe file from a previous failed run — clean it up first"

    pre = capture(_REPO_ROOT)
    try:
        probe_path.parent.mkdir(parents=True, exist_ok=True)
        probe_path.write_text('{"run_id": "not-the-pilot", "probe": true}\n', encoding="utf-8")

        post = capture(_REPO_ROOT)

        assert pre.content_hash != post.content_hash or pre.porcelain != post.porcelain, (
            "watch set did not detect a deliberate mutation under agent-monitoring/data/"
        )
        # a mutation NOT attributed to the pilot's own run_id must not raise
        assert_isolation_held(pre, post, pilot_run_id="TCK-20260907-FILTERED-REPLAY-EVAL-PILOT")
    finally:
        probe_path.unlink(missing_ok=True)


def test_isolation_detects_a_pilot_attributed_line_as_a_violation():
    """The isolation check must positively distinguish ambient concurrent-session growth from a
    genuine containment violation — a new agent-monitoring line carrying the pilot's own run_id
    must be treated as a hard failure, not tolerated as ambient noise.

    Uses a dedicated new shard directory (never a real, currently-shared shard file) so this test
    never risks clobbering a concurrent session's own in-flight append."""
    pilot_run_id = "TCK-20260907-FILTERED-REPLAY-EVAL-PILOT"
    probe_week_dir = _REPO_ROOT / "agent-monitoring" / "data" / "_pilot_isolation_test_week"
    probe_path = probe_week_dir / "runs.jsonl"
    assert not probe_week_dir.exists(), "stale probe shard from a previous failed run — clean it up first"

    pre = capture(_REPO_ROOT)
    try:
        probe_week_dir.mkdir(parents=True)
        probe_path.write_text(f'{{"run_id": "{pilot_run_id}", "final_status": "ok"}}\n', encoding="utf-8")

        post = capture(_REPO_ROOT)

        try:
            assert_isolation_held(pre, post, pilot_run_id=pilot_run_id)
            raised = False
        except ContainmentViolationError:
            raised = True
        assert raised, "a new line carrying the pilot's own run_id must raise ContainmentViolationError"
    finally:
        probe_path.unlink(missing_ok=True)
        try:
            probe_week_dir.rmdir()
        except OSError:
            pass


def test_isolation_uses_session_scoped_sidecar_path_exclusively():
    sidecar_path = _REPO_ROOT / _UNSCOPED_SIDECAR_RELPATH
    pre_exists = sidecar_path.exists()
    pre_mtime = sidecar_path.stat().st_mtime if pre_exists else None
    pre_content = sidecar_path.read_text(encoding="utf-8") if pre_exists else None

    fixture = load_fixture(_REAL_FIXTURE_PATH)
    run_pilot_isolated([fixture], _REPO_ROOT)

    post_exists = sidecar_path.exists()
    post_mtime = sidecar_path.stat().st_mtime if post_exists else None
    post_content = sidecar_path.read_text(encoding="utf-8") if post_exists else None

    assert pre_exists == post_exists
    assert pre_mtime == post_mtime
    assert pre_content == post_content
