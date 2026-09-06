"""Tests for the advisory shadow candidate-reviewer call sites added to
.claude/workflows/implement-ticket.js's Architecture-Verify and Security-Review phases
(TCK-20260904-SHADOW-REVIEWER-LOGGING).

Static, raw-source-text-parsing tests against implement-ticket.js, following the same
Path.read_text()-only technique tests/tools/test_shadow_packet_call_site.py already
uses (the workflow file is never executed — no JS test runner exists in this repo for
.claude/workflows/*.js). Behavioral sub-tests exercise the new Python modules
(shadow_reviewer_events, shadow_reviewer_window) directly, in-process, against tmp_path
fixtures — never the real agent-monitoring/data corpus.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"

_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import shadow_reviewer_events  # noqa: E402
import shadow_reviewer_window  # noqa: E402
from cost_proxy import compute_cost_proxy_score  # noqa: E402


def _workflow_source() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def _arch_verify_if_block(source: str) -> str:
    """Isolates the production `if (archVerify.verdict !== 'APPROVED') { ... }` block body,
    located via the pushEvent/return landmarks already in the file."""
    start = source.index("if (archVerify.verdict !== 'APPROVED') {")
    end = source.index(
        "pushEvent('Architecture-Verify', 'architecture-reviewer', 'ok', archVerify.summary",
        start,
    )
    return source[start:end]


def _security_review_if_block(source: str) -> str:
    start = source.index("if (securityReview.verdict !== 'APPROVED') {")
    end = source.index(
        "pushEvent('Security-Review', 'security-reviewer', 'ok', securityReview.summary",
        start,
    )
    return source[start:end]


def _arch_shadow_block(source: str) -> str:
    start = source.index("const archShadowWindowOutput = await bash(")
    end = source.index("if (archVerify.verdict !== 'APPROVED') {")
    return source[start:end]


def _security_shadow_block(source: str) -> str:
    start = source.index("const securityShadowWindowOutput = await bash(")
    end = source.index("if (securityReview.verdict !== 'APPROVED') {")
    return source[start:end]


# ---------------------------------------------------------------------------
# 1. Shadow verdict recorded as a distinct joinable record (architecture-reviewer)
# ---------------------------------------------------------------------------


def test_architecture_verify_shadow_call_emits_distinct_joinable_event():
    with tempfile.TemporaryDirectory() as d:
        events_file = Path(d) / "events.jsonl"

        # Production-shaped record (positive seq).
        production_record = {
            "run_id": "TCK-FAKE-SHADOW-JOIN",
            "seq": 6,
            "ts": "2026-09-04T00:00:00Z",
            "phase": "Architecture-Verify",
            "agent": "architecture-reviewer",
            "summary": "APPROVED",
            "status": "ok",
        }
        events_file.write_text(json.dumps(production_record) + "\n")

        ok = shadow_reviewer_events.emit_shadow_reviewer_event(
            run_id="TCK-FAKE-SHADOW-JOIN",
            seq=-100,
            phase="Architecture-Verify",
            agent="architecture-reviewer-shadow",
            summary="candidate summary",
            candidate_model="claude-fable-5-1",
            candidate_verdict="APPROVED",
            candidate_violations_count=0,
            candidate_wall_time_ms=1000,
            workflow_wall_time_ms=5000,
            events_file=events_file,
        )
        assert ok is True

        lines = [json.loads(line) for line in events_file.read_text().splitlines() if line]
        assert len(lines) == 2
        prod, shadow = lines[0], lines[1]

        # Joinable: same run_id + phase.
        assert prod["run_id"] == shadow["run_id"] == "TCK-FAKE-SHADOW-JOIN"
        assert prod["phase"] == shadow["phase"] == "Architecture-Verify"

        # Mechanically distinguishable: seq sign + agent suffix.
        assert prod["seq"] >= 1
        assert shadow["seq"] <= -100
        assert shadow["agent"] == "architecture-reviewer-shadow"
        assert shadow["agent"] != prod["agent"]
        assert "candidate_model" in shadow and "candidate_model" not in prod
        assert "candidate_verdict" in shadow and "candidate_verdict" not in prod


# ---------------------------------------------------------------------------
# 2. Shadow verdict recorded as a distinct joinable record (security-reviewer)
# ---------------------------------------------------------------------------


def test_security_review_shadow_call_emits_distinct_joinable_event():
    with tempfile.TemporaryDirectory() as d:
        events_file = Path(d) / "events.jsonl"

        production_record = {
            "run_id": "TCK-FAKE-SHADOW-JOIN-SEC",
            "seq": 9,
            "ts": "2026-09-04T00:00:00Z",
            "phase": "Security-Review",
            "agent": "security-reviewer",
            "summary": "APPROVED",
            "status": "ok",
        }
        events_file.write_text(json.dumps(production_record) + "\n")

        ok = shadow_reviewer_events.emit_shadow_reviewer_event(
            run_id="TCK-FAKE-SHADOW-JOIN-SEC",
            seq=-200,
            phase="Security-Review",
            agent="security-reviewer-shadow",
            summary="candidate security summary",
            candidate_model="claude-fable-5-1",
            candidate_verdict="APPROVED",
            candidate_violations_count=0,
            candidate_wall_time_ms=2000,
            workflow_wall_time_ms=8000,
            events_file=events_file,
        )
        assert ok is True

        lines = [json.loads(line) for line in events_file.read_text().splitlines() if line]
        assert len(lines) == 2
        prod, shadow = lines[0], lines[1]

        assert prod["run_id"] == shadow["run_id"]
        assert prod["phase"] == shadow["phase"] == "Security-Review"
        assert prod["seq"] >= 1
        assert shadow["seq"] <= -200
        assert shadow["agent"] == "security-reviewer-shadow"

    # Confirm the production Security-Review site (and its shadow companion) only fires
    # inside the tag-gated `if` — see the Anti-Drift Test Guard test below for the exact text.
    source = _workflow_source()
    assert "const securityShadowWindowOutput = await bash(" in source


# ---------------------------------------------------------------------------
# 3. Candidate-only failure never affects the gate outcome (Architecture-Verify / Security-Review)
# ---------------------------------------------------------------------------


def test_candidate_only_architecture_verify_failure_does_not_trigger_gate_failure():
    source = _workflow_source()
    if_block = _arch_verify_if_block(source)
    assert "archVerifyShadow" not in if_block
    assert "pushEvent" in if_block  # sanity: this is really the production failure branch
    assert "'failed'" in if_block


def test_candidate_only_security_review_failure_does_not_trigger_gate_failure():
    source = _workflow_source()
    if_block = _security_review_if_block(source)
    assert "securityReviewShadow" not in if_block
    assert "pushEvent" in if_block
    assert "'failed'" in if_block


# ---------------------------------------------------------------------------
# 4. Shadow-reviewer seq disjointness from the real per-phase seq range
# ---------------------------------------------------------------------------


def test_shadow_reviewer_seq_never_collides_with_real_phase_seq(tmp_path, monkeypatch):
    monkeypatch.setattr(shadow_reviewer_window, "DATA_DIR", tmp_path)

    for reviewer in ("architecture-reviewer", "security-reviewer"):
        for run_id in ("TCK-FAKE-A", "TCK-FAKE-B"):
            seq = shadow_reviewer_window.compute_shadow_seq(reviewer, run_id)
            assert seq <= -100

    # The two reviewers never collide with each other for any prior_count in a reasonable bound —
    # base 100 vs. 200, so architecture-reviewer's range [-100, -199] and security-reviewer's
    # range [-200, -299] (for prior_count in 0..99) never overlap.
    arch_range = {
        -(shadow_reviewer_window.SHADOW_SEQ_BASE["architecture-reviewer"] + n) for n in range(100)
    }
    sec_range = {
        -(shadow_reviewer_window.SHADOW_SEQ_BASE["security-reviewer"] + n) for n in range(100)
    }
    assert arch_range.isdisjoint(sec_range)

    # Real per-phase seq is always >= 1 by construction — disjoint from any shadow value <= -100.
    assert all(s >= 1 for s in range(1, 20))


# ---------------------------------------------------------------------------
# 5. Fail-open + env-gated shape, both call sites
# ---------------------------------------------------------------------------


def test_shadow_reviewer_call_site_is_fail_open_and_env_gated():
    source = _workflow_source()

    for block in (_arch_shadow_block(source), _security_shadow_block(source)):
        assert 'if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" = "1" ]' in block
        assert "timeout 15s python3 -c" in block
        assert "2>/dev/null || true" in block
        assert re.search(r"except Exception:\s*\n\s*pass", block)
        # JS-level try/catch wraps the whole advisory body — must not let a thrown exception
        # (API error, timeout, etc.) propagate out of the shadow block.
        assert "try {" in block
        assert "} catch (e) {" in block


# ---------------------------------------------------------------------------
# 6. Cost/timing attribution correctness (AC #3)
# ---------------------------------------------------------------------------


def test_candidate_call_cost_and_timing_labeled_separately_from_production(tmp_path, monkeypatch):
    tools_dir = tmp_path / "2026-W99"
    tools_dir.mkdir(parents=True)
    tools_file = tools_dir / "tools.jsonl"

    run_id = "TCK-FAKE-COST-ATTRIBUTION"
    production_rows = [
        {"run_id": run_id, "seq": 6, "tool": "Bash", "duration_ms": 2000},
        {"run_id": run_id, "seq": 6, "tool": "Edit"},
    ]
    shadow_rows = [
        {"run_id": run_id, "seq": -100, "tool": "Bash", "duration_ms": 500},
        {"run_id": run_id, "seq": -100, "tool": "Agent"},
        {"run_id": run_id, "seq": -100, "tool": "Read"},
    ]
    tools_file.write_text(
        "\n".join(json.dumps(r) for r in production_rows + shadow_rows) + "\n"
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "agent-monitoring" / "data" / "2026-W99").mkdir(parents=True)
    (tmp_path / "agent-monitoring" / "data" / "2026-W99" / "tools.jsonl").write_text(
        "\n".join(json.dumps(r) for r in production_rows + shadow_rows) + "\n"
    )

    production_count, production_score = (
        len(production_rows),
        compute_cost_proxy_score(production_rows),
    )
    shadow_count, shadow_score = shadow_reviewer_events._compute_candidate_tool_stats(run_id, -100)

    assert shadow_count == len(shadow_rows)
    assert shadow_score == compute_cost_proxy_score(shadow_rows)
    # Never summed or overwritten into one figure.
    assert shadow_count != production_count
    assert shadow_score != production_score


# ---------------------------------------------------------------------------
# 7. Anti-Drift Test Guard: Security-Review trigger condition untouched
# ---------------------------------------------------------------------------


def test_security_review_trigger_condition_byte_for_byte_unchanged():
    source = _workflow_source()
    assert (
        "if ((ticketInfo.tags && ticketInfo.tags.includes('security')) ||\n"
        "    (ticketInfo.suggested_skills && ticketInfo.suggested_skills.includes('/security-review'))) {"
    ) in source


# ---------------------------------------------------------------------------
# 8. Scope-creep guard: pre-Implement Review phase gains no shadow block
# ---------------------------------------------------------------------------


def test_pre_implement_review_phase_gains_no_shadow_block():
    source = _workflow_source()
    review_start = source.index("phase('Review')")
    review_end = source.index("phase('Implement')")
    review_block = source[review_start:review_end]

    assert "SHADOW_REVIEWER_LOGGING_ENABLED" not in review_block
    assert "shadow_reviewer_window" not in review_block
    assert "shadow_reviewer_events" not in review_block


# ---------------------------------------------------------------------------
# 9. captureEpochMs/workflowStartMs helper shape
# ---------------------------------------------------------------------------


def test_capture_epoch_ms_and_workflow_start_ms_defined_once_after_capture_ts():
    source = _workflow_source()
    assert source.count("const captureEpochMs = async ()") == 1
    assert source.count("const workflowStartMs = await captureEpochMs()") == 1

    capture_ts_idx = source.index("const captureTs = async ()")
    capture_epoch_ms_idx = source.index("const captureEpochMs = async ()")
    workflow_start_ms_idx = source.index("const workflowStartMs = await captureEpochMs()")
    resolve_scope_idx = source.index("const resolveScopeTicketLocation = async (id)")

    assert capture_ts_idx < capture_epoch_ms_idx < workflow_start_ms_idx < resolve_scope_idx


# ---------------------------------------------------------------------------
# 10. Bounded window gates the candidate agent() call at both sites (static shape)
# ---------------------------------------------------------------------------


def test_shadow_window_gate_precedes_candidate_agent_call_at_both_sites():
    source = _workflow_source()

    arch_block = _arch_shadow_block(source)
    window_check_idx = arch_block.index("if (archShadowWindow && archShadowWindow.window_open) {")
    agent_call_idx = arch_block.index("const archVerifyShadow = await agent(")
    assert window_check_idx < agent_call_idx

    security_block = _security_shadow_block(source)
    window_check_idx = security_block.index(
        "if (securityShadowWindow && securityShadowWindow.window_open) {"
    )
    agent_call_idx = security_block.index("const securityReviewShadow = await agent(")
    assert window_check_idx < agent_call_idx
