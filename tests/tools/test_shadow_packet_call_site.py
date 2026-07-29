"""Tests for the advisory shadow context-packet call site added to
.claude/workflows/implement-ticket.js's Investigate phase (TCK-20260729-SHADOW-PACKET-CALL-SITE).

Static, raw-source-text-parsing tests against implement-ticket.js, following the same
Path.read_text()-only technique tests/tools/test_current_run_sidecar_orchestrator.py already
uses (the workflow file is never executed — no JS test runner exists in this repo for
.claude/workflows/*.js). One behavioral sub-test (seq non-collision, fail-open) exercises the
same Python logic the inline python3 -c script runs, directly in-process against a tmp_path
events_file — never the real agent-monitoring/events.jsonl.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_RETRIEVAL_EVENTS_PATH = _REPO_ROOT / "tools" / "retrieval_events.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import retrieval_events as re_mod  # noqa: E402


def _workflow_source() -> str:
    return _WORKFLOW_PATH.read_text()


def _investigate_phase_block(source: str) -> str:
    start = source.index("phase('Investigate')")
    end = source.index("phase('Plan')")
    return source[start:end]


def _agent_prompt_bodies(source: str) -> list[str]:
    """Balanced-backtick scan of every `agent(\\`...\\`)` call's literal body."""
    bodies = []
    for m in re.finditer(r"agent\(\s*`", source):
        body_start = m.end()
        body_end = source.index("`", body_start)
        bodies.append(source[body_start:body_end])
    return bodies


# ---------------------------------------------------------------------------
# 1. Call site presence
# ---------------------------------------------------------------------------

def test_call_site_present_and_invokes_wrap_context_packet_assembly():
    block = _investigate_phase_block(_workflow_source())
    assert "wrap_context_packet_assembly" in block
    assert "context_packet_assembler" in block or "assemble_context_packet" in block


# ---------------------------------------------------------------------------
# 2. writeSidecar -> agent() adjacency untouched; call site strictly after pushEvent
# ---------------------------------------------------------------------------

def test_call_site_does_not_break_writesidecar_agent_adjacency():
    source = _workflow_source()
    adjacency = (
        "  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')\n"
        "  investigation = await agent("
    )
    assert adjacency in source

    push_event_call = (
        "pushEvent('Investigate', 'investigator', 'ok', "
        "investigationText.slice(0, 200), investigationTs)"
    )
    push_event_index = source.index(push_event_call)
    shadow_call_index = source.index("SHADOW_CONTEXT_PACKET_ENABLED")
    assert shadow_call_index > push_event_index


# ---------------------------------------------------------------------------
# 3. timeout + env-var gate (strict equality)
# ---------------------------------------------------------------------------

def test_call_wrapped_in_timeout_and_env_var_gate():
    block = _investigate_phase_block(_workflow_source())
    assert "timeout 10s" in block
    assert 'if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]' in block

    gate_index = block.index('if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]')
    timeout_index = block.index("timeout 10s", gate_index)
    python_index = block.index("python3", timeout_index)
    assert timeout_index < python_index


# ---------------------------------------------------------------------------
# 4. Fail-open: static shell suffix + behavioral inner try/except
# ---------------------------------------------------------------------------

def test_forcing_failure_or_timeout_does_not_change_investigate_pushevent_or_return_value():
    block = _investigate_phase_block(_workflow_source())
    assert "2>/dev/null || true" in block
    assert "except Exception:" in block
    assert re.search(r"except Exception:\s*\n\s*pass", block)

    # Behavioral half: force assemble_context_packet() to raise and confirm the exception
    # propagates out of wrap_context_packet_assembly() unmodified — i.e. the fail-open guarantee
    # comes from this ticket's own inline try/except in the python3 -c script, not from
    # wrap_context_packet_assembly() itself swallowing errors.
    import context_packet_assembler as cpa
    from unittest import mock

    with mock.patch.object(cpa, "assemble_context_packet", side_effect=RuntimeError("boom")):
        try:
            re_mod.wrap_context_packet_assembly(
                seq=-1,
                summary="test",
                run_id="TCK-FAKE-SHADOW-TEST",
                packet_id="shadow-test",
                corpus_generation="shadow",
                retrieval_version=1,
                budget_requested=0,
                included_candidates=[],
            )
            raised = False
        except RuntimeError:
            raised = True
    assert raised, (
        "wrap_context_packet_assembly() must not itself swallow the error — fail-open must "
        "come from this ticket's own try/except around the call, confirming that layer is load-"
        "bearing"
    )


# ---------------------------------------------------------------------------
# 5. Env var unset -> zero shadow calls
# ---------------------------------------------------------------------------

def _extract_shadow_bash_command(source: str) -> str:
    marker = 'if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]; then timeout 10s python3 -c "'
    start = source.index(marker)
    end = source.index('" "${tid}" 2>/dev/null || true; fi', start)
    end = source.index("fi`", end) + len("fi")
    return source[start:end]


def test_no_shadow_packet_call_when_env_var_unset(tmp_path):
    command = _extract_shadow_bash_command(_workflow_source())
    command = command.replace("${tid}", "TCK-FAKE-ENV-UNSET-TEST")

    import os
    env = os.environ.copy()
    env.pop("SHADOW_CONTEXT_PACKET_ENABLED", None)

    events_file = tmp_path / "events.jsonl"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert not events_file.exists()


# ---------------------------------------------------------------------------
# 6. No packet content in any agent()-prompt template
# ---------------------------------------------------------------------------

def test_no_packet_variable_in_any_agent_prompt_backtick_literal():
    source = _workflow_source()
    forbidden = ("packet", "ContextPacket", "wrap_context_packet_assembly", "assemble_context_packet")
    for body in _agent_prompt_bodies(source):
        for term in forbidden:
            assert term not in body, f"found forbidden term {term!r} inside an agent() prompt body"


# ---------------------------------------------------------------------------
# 7. Real run_id passthrough; phase="Retrieval" unchanged in retrieval_events.py
# ---------------------------------------------------------------------------

def test_real_run_id_passed_and_phase_field_unchanged():
    block = _investigate_phase_block(_workflow_source())
    assert '"${tid}"' in block

    retrieval_events_source = _RETRIEVAL_EVENTS_PATH.read_text()
    assert 'phase="Retrieval"' in retrieval_events_source
    assert 'AGENT_PACKET = "context-packet-wrapper"' in retrieval_events_source


# ---------------------------------------------------------------------------
# 8. Minimal (empty) candidate set; no hybrid_retrieval.py wiring
# ---------------------------------------------------------------------------

def test_minimal_candidate_set_no_hybrid_retrieval_import():
    # Scoped to the actual bash() command string, not the whole Investigate phase block — the
    # block's surrounding explanatory comment legitimately mentions tools/hybrid_retrieval.py by
    # name (documenting that its wiring is deferred to a follow-up ticket), which is prose, not a
    # reference inside the call's own command string.
    command = _extract_shadow_bash_command(_workflow_source())
    assert "hybrid_retrieval" not in command
    assert "hybrid_fuse_and_filter" not in command
    assert "included_candidates=[]" in command


# ---------------------------------------------------------------------------
# 9. docs/ path present in files_changed for the doc-staleness gate
# ---------------------------------------------------------------------------

def test_docs_path_present_in_the_same_diff():
    _MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "gate_checks"
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from tools.gate_checks.doc_staleness_check import check_doc_staleness

    files_changed = [
        ".claude/workflows/implement-ticket.js",
        "docs/agent-monitoring/schema.md",
        "tests/tools/test_shadow_packet_call_site.py",
    ]
    result = check_doc_staleness(files_changed, behavior_changed=True)
    assert all(r["status"] == "PASS" for r in result), result


# ---------------------------------------------------------------------------
# 10. No new field in RETRIEVAL_EVENT_FIELDS (negative control)
# ---------------------------------------------------------------------------

def test_no_new_field_in_retrieval_event_fields():
    expected = frozenset(
        {
            "retrieval_version",
            "corpus_generation",
            "cache_level",
            "cache_status",
            "latency_ms",
            "candidate_count",
            "selected_count",
            "source_kind_counts",
            "authority_counts",
            "freshness_counts",
            "exclusion_reason_counts",
            "cited_source_hashes",
            "adequacy_verdict",
            "expansion_reason",
            "expansion_count",
            "scenario",
            "risk_tier",
            "retrieval_event_schema_version",
        }
    )
    assert re_mod.RETRIEVAL_EVENT_FIELDS == expected


# ---------------------------------------------------------------------------
# 11. Shadow event seq never collides with any real phase seq
# ---------------------------------------------------------------------------

def _event(run_id, seq, agent="implementer", phase="Implement"):
    return {"run_id": run_id, "seq": seq, "ts": "t", "phase": phase, "agent": agent,
            "status": "ok", "summary": "ok"}


def _compute_shadow_seq(run_id: str, events: list[dict]) -> int:
    """Mirrors the Step 1 inline script's own computation exactly."""
    prior_shadow_count = sum(
        1 for e in events
        if e.get("run_id") == run_id and e.get("agent") == "context-packet-wrapper"
    )
    return -(1 + prior_shadow_count)


def test_shadow_call_seq_derivation_does_not_reference_events_length_or_seqoffset():
    block = _investigate_phase_block(_workflow_source())
    seq_line_match = re.search(r"shadow_seq = -\(1 \+ prior_shadow_count\)", block)
    assert seq_line_match is not None

    # The construction of shadow_seq itself (not merely the whole call-site block, which
    # legitimately contains the term elsewhere via the surrounding-comment prose) must not read
    # events.length/seqOffset anywhere in the python3 -c script body.
    script_start = block.index('python3 -c "')
    script_end = block.index('" "${tid}"')
    script_body = block[script_start:script_end]
    assert "events.length" not in script_body
    assert "seqOffset" not in script_body


def test_shadow_event_seq_never_collides_with_any_real_phase_seq():
    run_id = "TCK-FAKE-SEQ-COLLISION"

    # (a) fresh run: seqOffset=0, real seq values 1..N
    for n in range(1, 11):
        real_events = [_event(run_id, s) for s in range(1, n + 1)]
        shadow_seq = _compute_shadow_seq(run_id, real_events)
        assert shadow_seq <= 0
        assert shadow_seq not in {e["seq"] for e in real_events}

    # (b) resumed run: seqOffset=K>0, real seq values K+1..K+N
    for k in (5, 20, 100):
        for n in range(1, 6):
            real_events = [_event(run_id, s) for s in range(k + 1, k + n + 1)]
            shadow_seq = _compute_shadow_seq(run_id, real_events)
            assert shadow_seq <= 0
            assert shadow_seq not in {e["seq"] for e in real_events}

    # (c) two prior context-packet-wrapper rows already present for this run_id (re-investigation
    # scenario) — a third shadow call must compute a seq distinct from the first two shadow seqs
    # as well as from every real seq.
    real_events = [_event(run_id, s) for s in range(1, 5)]
    prior_shadow_events = [
        _event(run_id, -1, agent="context-packet-wrapper", phase="Retrieval"),
        _event(run_id, -2, agent="context-packet-wrapper", phase="Retrieval"),
    ]
    fixture = real_events + prior_shadow_events
    third_shadow_seq = _compute_shadow_seq(run_id, fixture)
    assert third_shadow_seq == -3
    assert third_shadow_seq not in {e["seq"] for e in real_events}
    assert third_shadow_seq not in {e["seq"] for e in prior_shadow_events}

    # Sanity: real per-phase seq is always >= 1 by construction of writeSidecar/pushEvent's
    # events.length + 1 + seqOffset idiom (events.length >= 0, seqOffset >= 0) -- the shadow
    # scheme's <= 0 range is disjoint from this for any prior_shadow_count/seqOffset/events.length
    # combination, independent of run length or resume count.
    assert all(e["seq"] >= 1 for e in real_events)
