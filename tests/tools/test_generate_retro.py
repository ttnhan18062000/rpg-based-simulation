"""Targeted tests for tools/agent-monitoring/generate_retro.py's reason-code section
(TCK-20260706-MONITORING-REASON-CODE, extended by TCK-20260706-SCOPE-TAG-REGISTRY-CHECK and
TCK-20260706-CREATE-TICKETS-TAG-CHECK), its Subsystem/Topic + Process/Skill-signal tag
breakdown sections (TCK-20260708-RETRO-TAG-BREAKDOWN), and (TCK-20260718-RETRO-STATS-REFACTOR)
the extracted compute_retro_metrics() computation function. Not full coverage of the pre-existing
script (which had no test file before the first of these tickets) — scoped to the behavior these
tickets changed.
"""

import sys
from datetime import date
from pathlib import Path

import pytest

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import generate_retro  # noqa: E402
from generate_retro import (  # noqa: E402
    build_raw_investigation_count_section,
    build_search_count_section,
    build_skill_usage_section,
    compute_kgmcp_cache_efficiency_metrics,
    compute_parity_index_readpath_call_count,
    compute_retro_metrics,
    compute_retrieval_metrics,
    compute_search_investigation_trend,
    compute_shadow_baseline_comparison,
    compute_tool_safety_metrics,
    compute_zero_invocation_skill_flags,
    generate,
    _is_parity_index_readpath_call,
    _record_since_cutoff,
    _resolve_status,
    _is_legacy_event,
    _is_gate_fail,
)
from tests.tools.skill_staleness_assertions import SkillStalenessWarning, skill_staleness_check


@pytest.fixture(autouse=True)
def _isolate_monitoring_index(monkeypatch, tmp_path):
    """Every test in this file drives generate_retro through compute_retro_metrics()/generate()
    directly (never through the index) except the tests that explicitly exercise
    _load_runs_and_events()/main() below — but main() now sources its data via
    DEFAULT_DB_PATH-backed _load_runs_and_events(). Without this monkeypatch, any test reaching
    that path would read (or worse, on-demand build) the real repo's
    agent-monitoring-index/monitoring.db, corrupting durable state for other consumers
    (query.py/validate.py). tmp_path is function-scoped, so this points every test's index at its
    own private, nonexistent-by-default location."""
    monkeypatch.setattr(generate_retro, "DEFAULT_DB_PATH", tmp_path / "monitoring.db")


_BASE_RUN = {
    "run_id": "TCK-FAKE",
    "start_ts": "2026-07-06T00:00:00Z",
    "end_ts": "2026-07-06T01:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DOD_BLOCKED",
    "agent_count": 9,
    "duration_s": 3600,
}


# --- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE: direct predicate-level tests for the three
# legacy-shape helpers, added before the data-loading migration to pin their current behavior. ---

def test_resolve_status_prefers_final_status_over_status():
    assert _resolve_status({"final_status": "DONE", "status": "old"}) == "DONE"


def test_resolve_status_falls_back_to_status_when_final_status_absent():
    # Literal spelling preserved, NOT normalized to "DONE" — _resolve_status's documented
    # non-normalizing contract.
    assert _resolve_status({"status": "complete"}) == "complete"


def test_resolve_status_returns_none_when_both_absent():
    assert _resolve_status({}) is None


def test_is_legacy_event_true_when_agent_missing():
    assert _is_legacy_event({"event": "did a thing"}) is True


def test_is_legacy_event_false_when_agent_present():
    assert _is_legacy_event({"agent": "implementer"}) is False


def test_is_gate_fail_true_for_non_terminal_status():
    assert _is_gate_fail({"final_status": "DOD_BLOCKED"}) is True


def test_is_gate_fail_false_for_done_epic_scoped_in_progress():
    assert _is_gate_fail({"final_status": "DONE"}) is False
    assert _is_gate_fail({"final_status": "EPIC_SCOPED"}) is False
    assert _is_gate_fail({"final_status": "IN_PROGRESS"}) is False


def test_resolve_status_function_still_importable_from_generate_retro():
    # Guards against a future edit literally deleting _resolve_status()'s definition —
    # build_index.py imports it directly (`from generate_retro import _resolve_status`).
    from generate_retro import _resolve_status as reimported

    assert callable(reimported)
    assert reimported({"status": "legacy-spelling"}) == "legacy-spelling"


def test_gate_fail_tuple_literal_unchanged():
    # Pins the exact terminal-state tuple _is_gate_fail() compares against.
    for terminal in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"):
        assert _is_gate_fail({"final_status": terminal}) is False
    assert _is_gate_fail({"final_status": "SOMETHING_ELSE"}) is True


def test_reason_code_section_omitted_when_no_reason_codes_present():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" not in report


def test_reason_code_section_tallies_present_codes():
    runs = [_BASE_RUN, dict(_BASE_RUN, run_id="TCK-FAKE-2")]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "TCK-FAKE-2", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "TCK-FAKE-2", "seq": 2, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" in report
    assert "| tag_registry_rejection | 2 |" in report


def test_reason_code_section_ignores_null_and_missing_fields():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": None},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" not in report


def _write_ticket(root, subdir, ticket_id, tags, date="20260710"):
    """Write a minimal ticket markdown file with a parseable frontmatter block under
    root/tickets/{subdir}/{ticket_id}.md. `date` controls the embedded ticket_id date used by
    _ticket_id_effective_date; defaults to a post-taxonomy date."""
    tickets_dir = root / "tickets" / subdir
    tickets_dir.mkdir(parents=True, exist_ok=True)
    tags_inline = "[" + ", ".join(tags) + "]"
    (tickets_dir / f"{ticket_id}.md").write_text(
        f"---\n"
        f"status: active\n"
        f"layer: observability\n"
        f"authority: P1\n"
        f"audience: agent\n"
        f"ticket_id: {ticket_id}\n"
        f"phase: open\n"
        f"date: {date[:4]}-{date[4:6]}-{date[6:]}\n"
        f"tags: {tags_inline}\n"
        f"---\n\n"
        f"# {ticket_id}\n"
    )


def _write_registry(root, entries):
    """Write a fixture registries/tag_registry.jsonl under root with `entries`, a list of
    (tag, category) tuples."""
    import json as _json

    registry_dir = root / "registries"
    registry_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        _json.dumps({"tag": tag, "category": category, "added_date": "2026-07-06", "note": "fixture"})
        for tag, category in entries
    ]
    (registry_dir / "tag_registry.jsonl").write_text("\n".join(lines) + "\n")


def test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve(tmp_path):
    _write_registry(tmp_path, [("observability", "subsystem-topic")])
    _write_ticket(tmp_path, "done", "TCK-20260710-FAKE-DONE", ["observability"])
    _write_ticket(tmp_path, "inprogress", "TCK-20260710-FAKE-INPROG", ["observability"])

    runs = [
        dict(_BASE_RUN, run_id="TCK-20260710-FAKE-DONE", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-FAKE-INPROG", final_status="DOD_BLOCKED"),
    ]
    # status-without-final_status regression case: a legacy-shaped record whose DONE-ness can
    # only be read via the `status` fallback (_resolve_status), not `final_status` directly —
    # guards against reintroducing the exact bug TCK-20260705-RETRO-METRIC-ACCURACY fixed.
    runs[0].pop("final_status")
    runs[0]["status"] = "DONE"
    events = []

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Subsystem/Topic" in report
    assert "| observability | 2 | 50% | 1 |" in report


def test_tag_breakdown_process_skill_signal_security_cross_reference(tmp_path):
    _write_registry(tmp_path, [("security", "process-skill-signal")])
    _write_ticket(tmp_path, "done", "TCK-20260710-SEC-PHASE-HIT", ["security"])
    _write_ticket(tmp_path, "done", "TCK-20260710-SEC-NO-HIT", ["security"])
    _write_ticket(tmp_path, "done", "TCK-20260710-SEC-STATUS-HIT", ["security"])

    runs = [
        dict(_BASE_RUN, run_id="TCK-20260710-SEC-PHASE-HIT", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-SEC-NO-HIT", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-SEC-STATUS-HIT", final_status="SECURITY_BLOCKED"),
    ]
    events = [
        # Case-insensitive match (Decision 3): lowercase "security-review" must still count.
        {"run_id": "TCK-20260710-SEC-PHASE-HIT", "seq": 1, "phase": "security-review",
         "agent": "security-reviewer", "status": "ok", "summary": "reviewed"},
        {"run_id": "TCK-20260710-SEC-NO-HIT", "seq": 1, "phase": "Verify",
         "agent": "done-checker", "status": "ok", "summary": "no security review"},
    ]

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Process/Skill-signal" in report
    assert "| security | 3 | 2 |" in report


def test_tag_breakdown_process_skill_signal_non_security_tags_have_no_gate_column(tmp_path):
    _write_registry(tmp_path, [("performance", "process-skill-signal")])
    _write_ticket(tmp_path, "done", "TCK-20260710-PERF-ONE", ["performance"])

    runs = [dict(_BASE_RUN, run_id="TCK-20260710-PERF-ONE", final_status="DONE")]
    events = []

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Process/Skill-signal" in report
    assert "| performance | 1 | N/A — no gate implemented |" in report


def test_tag_breakdown_section_omitted_when_no_run_id_resolves(tmp_path):
    _write_registry(tmp_path, [("observability", "subsystem-topic"), ("security", "process-skill-signal")])
    # No ticket files written — every run_id below is unresolvable against this empty tree.
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker",
         "status": "failed", "summary": "blocked"},
    ]

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Subsystem/Topic" not in report
    assert "## Tag Breakdown — Process/Skill-signal" not in report


def test_tag_breakdown_excludes_epic_folder_and_unresolvable_run_ids(tmp_path):
    _write_registry(tmp_path, [("observability", "subsystem-topic")])
    _write_ticket(tmp_path, "done", "TCK-20260710-RESOLVABLE", ["observability"])

    runs = [
        dict(_BASE_RUN, run_id="EPIC-some-epic", final_status="EPIC_SCOPED"),
        dict(_BASE_RUN, run_id="FOLDER-simq", final_status="EPIC_SCOPED"),
        dict(_BASE_RUN, run_id="CREATE-TICKETS-some-source", final_status="DONE"),
        dict(_BASE_RUN, run_id="E41D-20260621-001", final_status="DONE"),
        dict(_BASE_RUN, run_id="427cbe47-6093-481c-8abc-1234567890ab", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-RESOLVABLE", final_status="DONE"),
    ]
    events = []

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Subsystem/Topic" in report
    assert "| observability | 1 | 100% | 0 |" in report


def test_tag_breakdown_excludes_pre_taxonomy_and_untagged_tickets(tmp_path):
    _write_registry(tmp_path, [("observability", "subsystem-topic")])
    # Pre-taxonomy ticket_id date (before 2026-07-04) — excluded even though the file exists and
    # is readable.
    _write_ticket(tmp_path, "done", "TCK-20260601-OLD-TICKET", ["observability"], date="20260601")
    # Post-taxonomy ticket with no tags — excluded, must not crash.
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done" / "TCK-20260710-NO-TAGS.md").write_text(
        "---\n"
        "status: active\n"
        "layer: observability\n"
        "authority: P1\n"
        "audience: agent\n"
        "ticket_id: TCK-20260710-NO-TAGS\n"
        "phase: open\n"
        "date: 2026-07-10\n"
        "tags: []\n"
        "---\n\n"
        "# TCK-20260710-NO-TAGS\n"
    )

    runs = [
        dict(_BASE_RUN, run_id="TCK-20260601-OLD-TICKET", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-NO-TAGS", final_status="DONE"),
    ]
    events = []

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Subsystem/Topic" not in report
    assert "## Tag Breakdown — Process/Skill-signal" not in report


def test_tag_breakdown_uses_registry_categorize_tag_not_reimplemented_lookup(tmp_path):
    """Proves generate() actually calls the real load_registry/categorize_tag against the
    injected tickets_root, rather than reimplementing tag-category lookup locally — an unused
    import wouldn't be caught by a grep, but a distinct fixture-only category assignment would
    only classify correctly if the real functions were invoked against the fixture registry."""
    _write_registry(tmp_path, [
        ("fixture-only-subsystem-tag", "subsystem-topic"),
        ("fixture-only-skill-tag", "process-skill-signal"),
    ])
    _write_ticket(
        tmp_path, "done", "TCK-20260710-FIXTURE-REGISTRY",
        ["fixture-only-subsystem-tag", "fixture-only-skill-tag"],
    )

    runs = [dict(_BASE_RUN, run_id="TCK-20260710-FIXTURE-REGISTRY", final_status="DONE")]
    events = []

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "| fixture-only-subsystem-tag | 1 | 100% | 0 |" in report
    assert "| fixture-only-skill-tag | 1 | N/A — no gate implemented |" in report


def test_retro_spend_by_phase_breakdown_renders_with_fixture_events():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "found stuff", "cost_proxy_score": 10.0},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "more stuff", "cost_proxy_score": 30.0},
        {"run_id": "TCK-FAKE", "seq": 3, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "ran tests", "cost_proxy_score": 5.0},
    ]

    report = generate(runs, events, "test-label")

    assert "## Spend Proxy — By Phase" in report
    assert "| Investigate | 2 | 40.0 | 20.0 |" in report
    assert "| Test | 1 | 5.0 | 5.0 |" in report


def test_retro_spend_by_agent_breakdown_renders_with_fixture_events():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "found stuff", "cost_proxy_score": 10.0},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "more stuff", "cost_proxy_score": 30.0},
        {"run_id": "TCK-FAKE", "seq": 3, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "ran tests", "cost_proxy_score": 5.0},
    ]

    report = generate(runs, events, "test-label")

    assert "## Spend Proxy — By Agent" in report
    assert "| investigator | 2 | 40.0 | 20.0 |" in report
    assert "| test-scoper | 1 | 5.0 | 5.0 |" in report


def test_retro_spend_breakdown_omitted_or_zero_safe_when_no_events_have_cost_proxy_score():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed", "cost_proxy_score": None},
    ]

    report = generate(runs, events, "test-label")

    assert "## Spend Proxy — By Phase" not in report
    assert "## Spend Proxy — By Agent" not in report


def test_retro_spend_breakdown_placement_does_not_disturb_tag_breakdown_sections(tmp_path):
    _write_registry(tmp_path, [("observability", "subsystem-topic"), ("security", "process-skill-signal")])
    _write_ticket(tmp_path, "done", "TCK-20260710-FAKE-DONE", ["observability"])
    _write_ticket(tmp_path, "done", "TCK-20260710-SEC-ONE", ["security"])

    runs = [
        dict(_BASE_RUN, run_id="TCK-20260710-FAKE-DONE", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-SEC-ONE", final_status="DONE"),
    ]
    events = [
        {"run_id": "TCK-20260710-FAKE-DONE", "seq": 1, "phase": "Investigate", "agent": "investigator", "status": "ok", "summary": "found stuff", "cost_proxy_score": 12.0},
    ]

    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert "## Tag Breakdown — Subsystem/Topic" in report
    assert "## Tag Breakdown — Process/Skill-signal" in report
    assert "## Spend Proxy — By Phase" in report
    assert "## Spend Proxy — By Agent" in report

    tag_subsystem_idx = report.index("## Tag Breakdown — Subsystem/Topic")
    tag_skill_idx = report.index("## Tag Breakdown — Process/Skill-signal")
    agent_status_idx = report.index("## Agent Status Distribution")
    spend_phase_idx = report.index("## Spend Proxy — By Phase")
    spend_agent_idx = report.index("## Spend Proxy — By Agent")
    summary_quality_idx = report.index("## Summary Quality")

    assert tag_subsystem_idx < tag_skill_idx < agent_status_idx < spend_phase_idx < spend_agent_idx < summary_quality_idx


def test_reason_code_aggregation_is_workflow_agnostic():
    """Confirms TCK-20260706-CREATE-TICKETS-TAG-CHECK's claim: no code change was needed for
    generate_retro.py to also tally reason_code values from create-tickets.js's events, since the
    aggregation already iterates every event regardless of which workflow wrote it."""
    runs = [
        dict(_BASE_RUN, workflow="implement-ticket", final_status="TAGS_NOT_REGISTERED"),
        dict(_BASE_RUN, run_id="CREATE-TICKETS-FAKE", workflow="create-tickets", tier="n/a", final_status="DONE"),
    ]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Scope", "agent": "ticket-scoper", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "CREATE-TICKETS-FAKE", "seq": 1, "phase": "Structure", "agent": "create-tickets", "status": "blocked", "summary": "1 task skipped", "reason_code": "tag_registry_rejection"},
    ]

    report = generate(runs, events, "test-label")

    assert "| tag_registry_rejection | 2 |" in report


# --- TCK-20260718-RETRO-STATS-REFACTOR: compute_retro_metrics() direct tests ---
# generate() itself stays covered by every test above (unchanged signature/behavior, proven via
# this ticket's own byte-identical CLI-output comparison in plan.md Step 3). These tests exercise
# the newly-extracted computation function directly, so a future JSON API consumer
# (TCK-20260718-AGENTOPS-STATS-API) has direct coverage of the data shape it will import and call.

def test_compute_retro_metrics_returns_all_documented_keys():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
    ]

    metrics = compute_retro_metrics(runs, events)

    assert set(metrics.keys()) == {
        "run_summary", "gate_failure_breakdown", "reason_code_breakdown",
        "tag_breakdown_subsystem", "tag_breakdown_skill", "tier_distribution",
        "agent_status_distribution", "phase_status_distribution", "spend_proxy_by_phase",
        "spend_proxy_by_agent", "summary_quality", "slow_runs", "outliers",
        # Added by TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD —
        # both always present (computed over an empty list, not omitted) when `tools`/
        # `kgmcp_access_log` are omitted, keeping this function's own additive-only contract.
        "skill_usage", "kgmcp_cache_efficiency",
    }


def test_compute_retro_metrics_run_summary_matches_fixture():
    runs = [_BASE_RUN, dict(_BASE_RUN, run_id="TCK-FAKE-2", final_status="DONE", duration_s=1800, agent_count=3)]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
        {"run_id": "TCK-FAKE-2", "seq": 1, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
    ]

    metrics = compute_retro_metrics(runs, events)
    rs = metrics["run_summary"]

    assert rs["total"] == 2
    assert rs["done_count"] == 1
    assert rs["gate_fail_count"] == 1
    assert rs["total_agent_calls"] == 2
    # avg of 3600s and 1800s = 2700s = 45 min
    assert rs["avg_duration_min"] == 45
    # avg of 9 and 3 = 6.0
    assert rs["avg_agents"] == 6.0


def test_compute_retro_metrics_is_a_pure_read_only_function(tmp_path):
    """No file writes, no printing — mirrors this project's read-only-logic architecture test
    convention. Calling it twice with the same inputs must be side-effect-free and idempotent."""
    runs = [_BASE_RUN]
    events = []

    before = set(tmp_path.iterdir()) if tmp_path.exists() else set()
    metrics_1 = compute_retro_metrics(runs, events, tickets_root=tmp_path)
    metrics_2 = compute_retro_metrics(runs, events, tickets_root=tmp_path)
    after = set(tmp_path.iterdir()) if tmp_path.exists() else set()

    assert metrics_1 == metrics_2
    assert before == after


def test_compute_retro_metrics_tag_breakdown_matches_generate_output(tmp_path):
    """Cross-checks compute_retro_metrics()'s tag_breakdown_subsystem shape directly against
    generate()'s rendered table row for the same fixture — proves the renderer's fmt_pct(row['done'],
    row['runs']) call is fed the same raw counts the old inline computation produced."""
    _write_registry(tmp_path, [("observability", "subsystem-topic")])
    _write_ticket(tmp_path, "done", "TCK-20260710-FAKE-DONE", ["observability"])
    _write_ticket(tmp_path, "inprogress", "TCK-20260710-FAKE-INPROG", ["observability"])

    runs = [
        dict(_BASE_RUN, run_id="TCK-20260710-FAKE-DONE", final_status="DONE"),
        dict(_BASE_RUN, run_id="TCK-20260710-FAKE-INPROG", final_status="DOD_BLOCKED"),
    ]
    events = []

    metrics = compute_retro_metrics(runs, events, tickets_root=tmp_path)
    report = generate(runs, events, "test-label", tickets_root=tmp_path)

    assert metrics["tag_breakdown_subsystem"]["observability"] == {"runs": 2, "done": 1, "gate_fails": 1}
    assert "| observability | 2 | 50% | 1 |" in report


def test_compute_retro_metrics_skill_tag_gate_hits_none_when_no_gate_implemented(tmp_path):
    _write_registry(tmp_path, [("performance", "process-skill-signal")])
    _write_ticket(tmp_path, "done", "TCK-20260710-PERF-ONE", ["performance"])

    runs = [dict(_BASE_RUN, run_id="TCK-20260710-PERF-ONE", final_status="DONE")]
    events = []

    metrics = compute_retro_metrics(runs, events, tickets_root=tmp_path)

    assert metrics["tag_breakdown_skill"]["performance"] == {"runs": 1, "gate_hits": None}


# --- TCK-20260719-PHASE-AGENT-CASE-FOLD: phase/agent casing normalization ---

def test_phase_status_distribution_merges_casing_variants_review_failure_rate():
    # Fragmented input across 3 casing variants of the same logical phase — the exact shape
    # confirmed in real agent-monitoring/events.jsonl data (Finalize/finalize/FINALIZE,
    # Implement/implement/IMPLEMENT, Review/review, etc). 41 failed + 184 ok = 225 total,
    # 41/225 = 18.2% (rounded to 1 decimal) — the ticket's own motivating real-data example.
    runs = [_BASE_RUN]
    events = (
        [{"run_id": "TCK-FAKE", "seq": i, "phase": "Review", "agent": "architecture-reviewer",
          "status": "failed", "summary": "needs changes"} for i in range(20)]
        + [{"run_id": "TCK-FAKE", "seq": 100 + i, "phase": "review", "agent": "architecture-reviewer",
            "status": "failed", "summary": "needs changes"} for i in range(15)]
        + [{"run_id": "TCK-FAKE", "seq": 200 + i, "phase": "REVIEW", "agent": "architecture-reviewer",
            "status": "failed", "summary": "needs changes"} for i in range(6)]
        + [{"run_id": "TCK-FAKE", "seq": 300 + i, "phase": "Review", "agent": "architecture-reviewer",
            "status": "ok", "summary": "approved"} for i in range(100)]
        + [{"run_id": "TCK-FAKE", "seq": 400 + i, "phase": "review", "agent": "architecture-reviewer",
            "status": "ok", "summary": "approved"} for i in range(60)]
        + [{"run_id": "TCK-FAKE", "seq": 500 + i, "phase": "REVIEW", "agent": "architecture-reviewer",
            "status": "ok", "summary": "approved"} for i in range(24)]
    )

    metrics = compute_retro_metrics(runs, events)

    # Merged into exactly one "Review" key — casing variants no longer fragment the count.
    assert set(metrics["phase_status_distribution"].keys()) == {"Review"}
    merged = metrics["phase_status_distribution"]["Review"]
    assert merged == {"failed": 41, "ok": 184}

    failure_rate = round(100 * merged["failed"] / (merged["failed"] + merged["ok"]), 1)
    assert failure_rate == 18.2

    # Naive (unmerged) reads would have shown 3 separate, individually-smaller-looking phases —
    # this proves the fragmentation was real and would have undercounted the true rate: e.g. the
    # "Review" literal-only bucket alone is 20 failed / 120 total = 16.7%, not 18.2%.
    naive_review_only_rate = round(100 * 20 / 120, 1)
    assert naive_review_only_rate != failure_rate


def test_phase_status_distribution_rendered_in_report():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "verify", "agent": "done-checker", "status": "ok", "summary": "passed"},
    ]

    metrics = compute_retro_metrics(runs, events)
    report = generate(runs, events, "test-label")

    assert metrics["phase_status_distribution"]["Verify"] == {"failed": 1, "ok": 1}
    assert "## Phase Status Distribution" in report
    assert "| Verify | 2 | 1 | 1 | 0 | 0 |" in report


def test_agent_status_distribution_still_merges_casing_variants_if_ever_present():
    # Real production data (checked directly) shows zero agent-name casing drift today — every
    # implement-ticket agent literal is already lowercase-consistent. This test proves the
    # normalization mechanism works for agent too (not just phase), so it's not a latent gap if
    # drift is ever introduced later.
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Test", "agent": "Test-Scoper", "status": "ok", "summary": "passed"},
    ]

    metrics = compute_retro_metrics(runs, events)

    assert set(metrics["agent_status_distribution"].keys()) == {"test-scoper"}
    assert metrics["agent_status_distribution"]["test-scoper"] == {"ok": 2}


def test_spend_proxy_by_phase_merges_casing_variants():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Implement", "agent": "implementer", "status": "ok", "summary": "done", "cost_proxy_score": 10.0},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "implement", "agent": "implementer", "status": "ok", "summary": "done", "cost_proxy_score": 20.0},
        {"run_id": "TCK-FAKE", "seq": 3, "phase": "IMPLEMENT", "agent": "implementer", "status": "ok", "summary": "done", "cost_proxy_score": 30.0},
    ]

    metrics = compute_retro_metrics(runs, events)

    assert set(metrics["spend_proxy_by_phase"].keys()) == {"Implement"}
    assert metrics["spend_proxy_by_phase"]["Implement"] == {"events_scored": 3, "total": 60.0, "avg": 20.0}


def test_normalization_leaves_unknown_workflow_and_unrecognized_phase_untouched():
    # A run_id matching no known workflow prefix (infer_workflow returns None) must pass phase/
    # agent through completely unchanged — never crash, never merge into a fabricated canonical
    # spelling for a vocabulary that doesn't exist for that workflow.
    runs = [dict(_BASE_RUN, run_id="UNKNOWN-PREFIX-123")]
    events = [
        {"run_id": "UNKNOWN-PREFIX-123", "seq": 1, "phase": "SomeWeirdPhase", "agent": "someone", "status": "ok", "summary": "did a thing"},
    ]

    metrics = compute_retro_metrics(runs, events)

    assert metrics["phase_status_distribution"] == {"SomeWeirdPhase": {"ok": 1}}
    assert metrics["agent_status_distribution"] == {"someone": {"ok": 1}}


def test_create_tickets_prefix_family_agent_not_merged_into_a_literal():
    # create-tickets' dynamic `investigate:C1`/`investigate:C2` agents are a prefix-family, not a
    # fixed literal in WORKFLOW_AGENTS — must never be force-merged into a single canonical
    # literal (there isn't one), and must not collide with each other.
    runs = [dict(_BASE_RUN, run_id="CREATE-TICKETS-fake-source", workflow="create-tickets", tier="n/a")]
    events = [
        {"run_id": "CREATE-TICKETS-fake-source", "seq": 1, "phase": "Investigate", "agent": "investigate:C1", "status": "ok", "summary": "found stuff"},
        {"run_id": "CREATE-TICKETS-fake-source", "seq": 2, "phase": "Investigate", "agent": "investigate:C2", "status": "ok", "summary": "found other stuff"},
    ]

    metrics = compute_retro_metrics(runs, events)

    assert set(metrics["agent_status_distribution"].keys()) == {"investigate:C1", "investigate:C2"}


# --- TCK-20260719-RETRO-OUTLIER-FLAGS: duration_s/cost_proxy_score outlier detection ---

def test_duration_outlier_flagged_relative_to_tier_median_not_global():
    # 5 standard-tier runs around 1000s (median), 1 wildly longer standard-tier run (>3x median)
    # must be flagged; a 1000s epic-tier run (which would look "high" against the standard-tier
    # median) must NOT be flagged since epic has its own separate group and too few members
    # (below _OUTLIER_MIN_GROUP_SIZE) to compute a median at all.
    runs = [
        dict(_BASE_RUN, run_id=f"TCK-STD-{i}", tier="standard", duration_s=1000)
        for i in range(5)
    ] + [
        dict(_BASE_RUN, run_id="TCK-STD-OUTLIER", tier="standard", duration_s=5000),
        dict(_BASE_RUN, run_id="TCK-EPIC-ONE", tier="epic", duration_s=1000),
    ]
    events = []

    metrics = compute_retro_metrics(runs, events)

    outlier_run_ids = {o["run_id"] for o in metrics["outliers"]["duration_s"]}
    assert outlier_run_ids == {"TCK-STD-OUTLIER"}
    flagged = metrics["outliers"]["duration_s"][0]
    assert flagged["tier"] == "standard"
    assert flagged["duration_s"] == 5000
    assert flagged["median"] == 1000.0
    assert flagged["ratio"] == 5.0


def test_duration_outlier_excludes_null_from_flagging_and_median():
    # A run with duration_s=None (in-progress, no end_ts yet) must not be flagged, and must not
    # be counted toward the group's median.
    runs = [
        dict(_BASE_RUN, run_id=f"TCK-STD-{i}", tier="standard", duration_s=1000)
        for i in range(3)
    ] + [dict(_BASE_RUN, run_id="TCK-STD-INPROGRESS", tier="standard", duration_s=None)]
    events = []

    metrics = compute_retro_metrics(runs, events)

    assert metrics["outliers"]["duration_s"] == []


def test_duration_outlier_skips_group_below_minimum_size():
    # Only 2 runs in the "hotfix" tier — below _OUTLIER_MIN_GROUP_SIZE (3) — even though one is
    # numerically 10x the other, no outlier is flagged (a 2-point median is not a meaningful
    # baseline).
    runs = [
        dict(_BASE_RUN, run_id="TCK-HOTFIX-1", tier="hotfix", duration_s=100),
        dict(_BASE_RUN, run_id="TCK-HOTFIX-2", tier="hotfix", duration_s=1000),
    ]
    events = []

    metrics = compute_retro_metrics(runs, events)

    assert metrics["outliers"]["duration_s"] == []


def test_cost_proxy_outlier_flagged_relative_to_normalized_phase_median():
    # cost_proxy_score outliers group by *normalized* phase — 'Investigate'/'investigate' must
    # merge into one group (not fragment into two too-small groups), reusing
    # TCK-20260719-PHASE-AGENT-CASE-FOLD's _normalize_phase.
    runs = [_BASE_RUN]
    events = (
        [{"run_id": "TCK-FAKE", "seq": i, "phase": "Investigate", "agent": "investigator",
          "status": "ok", "summary": "found stuff", "cost_proxy_score": 100.0} for i in range(3)]
        + [{"run_id": "TCK-FAKE", "seq": 100, "phase": "investigate", "agent": "investigator",
            "status": "ok", "summary": "found stuff", "cost_proxy_score": 1000.0}]
    )

    metrics = compute_retro_metrics(runs, events)

    outliers = metrics["outliers"]["cost_proxy_score"]
    assert len(outliers) == 1
    assert outliers[0]["phase"] == "Investigate"
    assert outliers[0]["cost_proxy_score"] == 1000.0
    assert outliers[0]["seq"] == 100


def test_cost_proxy_outlier_excludes_events_with_no_score():
    # An event with no cost_proxy_score at all (pre-TCK-20260708-AGENT-COST-OBSERVABILITY
    # historical record) must not be counted in the group or ever flagged.
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": i, "phase": "Test", "agent": "test-scoper",
         "status": "ok", "summary": "passed", "cost_proxy_score": 10.0} for i in range(3)
    ] + [
        {"run_id": "TCK-FAKE", "seq": 100, "phase": "Test", "agent": "test-scoper",
         "status": "ok", "summary": "passed"},  # no cost_proxy_score key at all
    ]

    metrics = compute_retro_metrics(runs, events)

    assert metrics["outliers"]["cost_proxy_score"] == []


def test_outliers_section_omitted_when_none_flagged():
    runs = [_BASE_RUN]
    events = []

    report = generate(runs, events, "test-label")

    assert "## Outliers" not in report


def test_outliers_section_rendered_when_flagged():
    runs = [
        dict(_BASE_RUN, run_id=f"TCK-STD-{i}", tier="standard", duration_s=1000)
        for i in range(4)
    ] + [dict(_BASE_RUN, run_id="TCK-STD-OUTLIER", tier="standard", duration_s=9000)]
    events = []

    report = generate(runs, events, "test-label")

    assert "## Outliers" in report
    assert "### Duration outliers (by tier)" in report
    assert "TCK-STD-OUTLIER" in report
    assert "9.0x" in report


def test_record_since_cutoff_true_for_iso_string_at_or_after_cutoff():
    cutoff = "2026-07-01T00:00:00Z"
    assert _record_since_cutoff("2026-07-15T00:00:00Z", cutoff) is True
    assert _record_since_cutoff("2026-07-01T00:00:00Z", cutoff) is True


def test_record_since_cutoff_false_for_iso_string_before_cutoff():
    cutoff = "2026-07-01T00:00:00Z"
    assert _record_since_cutoff("2026-06-01T00:00:00Z", cutoff) is False


def test_record_since_cutoff_excludes_non_string_start_ts_instead_of_raising():
    # TCK-... (2026-07-20 orchestration audit): --days crashed on legacy runs.jsonl records
    # whose start_ts is a non-string (e.g. a float from an older schema generation) — verify the
    # >= comparison no longer runs against a non-string value at all.
    cutoff = "2026-07-01T00:00:00Z"
    assert _record_since_cutoff(1720000000.0, cutoff) is False
    assert _record_since_cutoff(None, cutoff) is False
    assert _record_since_cutoff("", cutoff) is False


def test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts(tmp_path, monkeypatch):
    import generate_retro

    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    runs_file.write_text(
        '{"run_id":"TCK-LEGACY","start_ts":1720000000.0,"workflow":"implement-ticket","tier":"standard","final_status":"DONE","agent_count":1}\n'
        '{"run_id":"TCK-RECENT","start_ts":"2026-07-19T00:00:00Z","end_ts":"2026-07-19T01:00:00Z","workflow":"implement-ticket","tier":"standard","final_status":"DONE","agent_count":1}\n'
    )
    events_file.write_text("")
    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)
    monkeypatch.setattr(generate_retro, "RETRO_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_retro.py", "--days", "30"])

    generate_retro.main()  # must not raise

    assert (tmp_path / "RETRO-LAST30D.md").exists()


# --- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE: build-on-demand / fallback / no-hard-exit ---

def test_generate_retro_builds_index_on_demand_when_missing(tmp_path, monkeypatch):
    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    tools_file = tmp_path / "tools.jsonl"
    runs_file.write_text(
        '{"run_id":"TCK-ONDEMAND","start_ts":"2026-07-20T00:00:00Z","end_ts":"2026-07-20T00:10:00Z",'
        '"workflow":"implement-ticket","tier":"standard","final_status":"DONE","agent_count":1}\n'
    )
    events_file.write_text(
        '{"run_id":"TCK-ONDEMAND","seq":1,"phase":"Implement","agent":"implementer","status":"ok","summary":"done"}\n'
    )
    tools_file.write_text("")

    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)
    monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tools_file)

    assert not generate_retro.DEFAULT_DB_PATH.exists()

    runs, events = generate_retro._load_runs_and_events()

    assert generate_retro.DEFAULT_DB_PATH.exists()
    assert [r["run_id"] for r in runs] == ["TCK-ONDEMAND"]
    assert [e["run_id"] for e in events] == ["TCK-ONDEMAND"]


def test_generate_retro_rebuilds_stale_index_not_just_missing_index(tmp_path, monkeypatch):
    # TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS: a present-but-outdated index was
    # previously read silently forever (old code only checked DEFAULT_DB_PATH.exists()) —
    # under-reporting retro numbers with no warning. This proves a source JSONL write that
    # postdates the index's mtime triggers a rebuild before read, not just a missing DB file.
    import os
    import time

    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    tools_file = tmp_path / "tools.jsonl"
    runs_file.write_text(
        '{"run_id":"TCK-STALE-BEFORE","start_ts":"2026-08-10T00:00:00Z",'
        '"end_ts":"2026-08-10T00:10:00Z","workflow":"implement-ticket","tier":"standard",'
        '"final_status":"DONE","agent_count":1}\n'
    )
    events_file.write_text(
        '{"run_id":"TCK-STALE-BEFORE","seq":1,"phase":"Implement","agent":"implementer",'
        '"status":"ok","summary":"done"}\n'
    )
    tools_file.write_text("")

    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)
    monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tools_file)

    # First load builds the index (missing-DB path) and reflects only the "before" row.
    runs, events = generate_retro._load_runs_and_events()
    assert [r["run_id"] for r in runs] == ["TCK-STALE-BEFORE"]
    assert generate_retro.DEFAULT_DB_PATH.exists()

    # Write a new record that postdates the index's own mtime (not just the source file's
    # existing mtime — sleep briefly to guarantee a strictly later mtime on filesystems with
    # coarse mtime resolution).
    time.sleep(0.05)
    with runs_file.open("a") as f:
        f.write(
            '{"run_id":"TCK-STALE-AFTER","start_ts":"2026-08-11T00:00:00Z",'
            '"end_ts":"2026-08-11T00:10:00Z","workflow":"implement-ticket","tier":"standard",'
            '"final_status":"DONE","agent_count":1}\n'
        )
    os.utime(runs_file, None)  # force mtime update even on filesystems with 1s resolution

    assert generate_retro._index_is_stale(generate_retro.DEFAULT_DB_PATH) is True

    runs, events = generate_retro._load_runs_and_events()

    assert {r["run_id"] for r in runs} == {"TCK-STALE-BEFORE", "TCK-STALE-AFTER"}


def test_index_is_stale_false_when_index_newer_than_all_sources(tmp_path, monkeypatch):
    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    tools_file = tmp_path / "tools.jsonl"
    runs_file.write_text("")
    events_file.write_text("")
    tools_file.write_text("")

    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)
    monkeypatch.setattr(generate_retro, "DEFAULT_TOOLS_FILE", tools_file)

    generate_retro._load_runs_and_events()  # builds the index fresh, now newer than all sources

    assert generate_retro._index_is_stale(generate_retro.DEFAULT_DB_PATH) is False


def test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails(
    tmp_path, monkeypatch, capsys
):
    import build_index

    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    runs_file.write_text(
        '{"run_id":"TCK-FALLBACK","start_ts":"2026-07-20T00:00:00Z","end_ts":"2026-07-20T00:05:00Z",'
        '"workflow":"implement-ticket","tier":"standard","final_status":"DONE","agent_count":1}\n'
    )
    events_file.write_text("")

    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)

    def _raise(*_args, **_kwargs):
        raise RuntimeError("simulated on-demand build failure")

    monkeypatch.setattr(build_index, "build", _raise)

    runs, events = generate_retro._load_runs_and_events()

    assert runs == generate_retro.load_jsonl(runs_file)
    assert events == generate_retro.load_jsonl(events_file)
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "agent-monitoring index unavailable" in captured.err


def test_no_sys_exit_1_on_missing_index_in_generate_retro(tmp_path, monkeypatch):
    # Direct opposite of query.py/validate.py's open_index() precedent (sys.exit(1) on a missing
    # index) — this ticket's Scope explicitly requires the index never becomes a hard gating
    # dependency for a retro report.
    runs_file = tmp_path / "runs.jsonl"
    events_file = tmp_path / "events.jsonl"
    runs_file.write_text("")
    events_file.write_text("")

    monkeypatch.setattr(generate_retro, "RUNS_FILE", runs_file)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", events_file)

    try:
        runs, events = generate_retro._load_runs_and_events()
    except SystemExit:
        pytest.fail("_load_runs_and_events() must never sys.exit on a missing/unbuildable index")

    assert runs == []
    assert events == []


def test_generate_retro_never_writes_to_agent_monitoring_index_db():
    # Architecture guard: the only legitimate write path to monitoring.db is the delegated
    # build_index.build() call — no bespoke INSERT/UPDATE/sqlite3-write logic may exist here.
    source = Path(generate_retro.__file__).read_text()
    assert "INSERT INTO" not in source
    assert "UPDATE " not in source
    assert '.execute("INSERT' not in source


# --- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE: migration-completeness / output-parity guards ---

def test_main_loads_via_index_not_direct_jsonl_scan():
    import inspect

    source = inspect.getsource(generate_retro.main)
    assert "load_jsonl(RUNS_FILE)" not in source
    assert "load_jsonl(EVENTS_FILE)" not in source
    assert "_load_runs_and_events" in source


def test_update_index_signature_change_is_deliberate_and_documented():
    """Replaces test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope
    (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING, Design Decision 2): _update_index gained
    an additional, optional `all_tools` parameter to thread per-week search/read trend data into
    index.md — a deliberate, disclosed arity change, not a silent regression. The original test's
    real property — _update_index never bypasses its passed-in data by reading RUNS_FILE directly
    — is preserved and re-asserted below; only the arity pin itself is consciously updated."""
    import inspect

    source = inspect.getsource(generate_retro._update_index)
    assert "load_jsonl(RUNS_FILE)" not in source

    sig = inspect.signature(generate_retro._update_index)
    assert list(sig.parameters) == ["all_runs", "all_tools"]
    assert sig.parameters["all_tools"].default is None


_FIXED_CORPUS_RUNS = [
    {
        "run_id": "TCK-FIXED-DONE", "start_ts": "2026-07-01T00:00:00Z",
        "end_ts": "2026-07-01T00:30:00Z", "workflow": "implement-ticket", "tier": "standard",
        "final_status": "DONE", "agent_count": 5, "duration_s": 1800,
    },
    {
        "run_id": "TCK-FIXED-GATEFAIL", "start_ts": "2026-07-01T01:00:00Z",
        "end_ts": "2026-07-01T01:20:00Z", "workflow": "implement-ticket", "tier": "hotfix",
        "final_status": "DOD_BLOCKED", "agent_count": 3, "duration_s": 1200,
    },
    {
        # Legacy-shaped record: status only, no final_status — exercises _resolve_status's
        # fallback path with a non-normalized literal spelling ("complete", not "DONE").
        "run_id": "TCK-FIXED-LEGACY", "start_ts": "2026-07-01T02:00:00Z",
        "end_ts": "2026-07-01T02:10:00Z", "workflow": "implement-ticket", "tier": "standard",
        "status": "complete", "agent_count": 2, "duration_s": 600,
    },
]
_FIXED_CORPUS_EVENTS = [
    {"run_id": "TCK-FIXED-DONE", "seq": 1, "phase": "Implement", "agent": "implementer",
     "status": "ok", "summary": "did work"},
    {"run_id": "TCK-FIXED-GATEFAIL", "seq": 1, "phase": "Verify", "agent": "done-checker",
     "status": "failed", "summary": "blocked"},
]

# Hand-copied frozen output — captured from generate() before this ticket's data-loading
# migration landed (mirrors the QUERY-INDEX-MIGRATE convention: a frozen literal in the test
# file, not sourced from git history). compute_retro_metrics()/generate() are untouched by this
# migration, so this should trivially pass — its value is pinning the guarantee explicitly.
_FIXED_CORPUS_EXPECTED_REPORT = (
    "# Agent Monitoring Retro — fixed-label\n"
    "\n"
    "---\n"
    "\n"
    "## Run Summary\n"
    "\n"
    "| Metric | Value |\n"
    "|---|---|\n"
    "| Total runs | 3 |\n"
    "| Completed (DONE) | 1 (33%) |\n"
    "| Gate failures | 2 |\n"
    "| Avg duration | 20 min |\n"
    "| Avg agents per run | 3.3 |\n"
    "| Total agent calls | 2 |\n"
    "\n"
    "## Gate Failure Breakdown\n"
    "\n"
    "| Gate | Count | % of runs |\n"
    "|---|---|---|\n"
    "| DOD_BLOCKED | 1 | 33% |\n"
    "| complete | 1 | 33% |\n"
    "\n"
    "## Tier Distribution\n"
    "\n"
    "| Tier | Count | Scoped | DONE count | DONE rate |\n"
    "|---|---|---|---|---|\n"
    "| hotfix | 1 | 0 | 0 | 0% |\n"
    "| standard | 2 | 0 | 1 | 50% |\n"
    "\n"
    "## Agent Status Distribution\n"
    "\n"
    "| Agent | Calls | ok | failed | blocked | skipped |\n"
    "|---|---|---|---|---|---|\n"
    "| done-checker | 1 | 0 | 1 | 0 | 0 |\n"
    "| implementer | 1 | 1 | 0 | 0 | 0 |\n"
    "\n"
    "## Phase Status Distribution\n"
    "\n"
    "| Phase | Calls | ok | failed | blocked | skipped |\n"
    "|---|---|---|---|---|---|\n"
    "| Implement | 1 | 1 | 0 | 0 | 0 |\n"
    "| Verify | 1 | 0 | 1 | 0 | 0 |\n"
    "\n"
    "## Summary Quality\n"
    "\n"
    "| Issue | Count |\n"
    "|---|---|\n"
    "| Empty summary (current schema) | 0 |\n"
    "| Legacy-format records (summary field not applicable) | 0 |\n"
    "| Truncated (>200 chars) | 0 |\n"
    "\n"
    "## Slow Runs (> 30 min)\n"
    "\n"
    "_No slow runs this period._\n"
    "\n"
    "## Parity Index Read-Path Usage\n"
    "\n"
    "**`entry`/`impact`/`health` call count:** 0/0 Bash rows scanned\n"
    "\n"
    "_Counts tools.jsonl rows where tool == \"Bash\" and input_summary matches parity_index.py "
    "followed immediately by entry, impact, or health (path-anchored, so a filename mention alone "
    "— e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' "
    "tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row "
    "population this detector ran against (the section's own 'N' denominator). Confirmed 0 real "
    "call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet "
    "wired into any real workflow call site) — this is the expected, correct value until a future "
    "ticket adds a real entry/impact/health call site, not a bug._\n"
    "\n"
    "## KGMCP Cache Efficiency\n"
    "\n"
    "_Reflects the full retrieval_cache_access_log corpus regardless of this report's "
    "--days/--week/--all period selection — these rows are logged against "
    "`.claude/current_run` sidecar attribution at call time, not `runs.jsonl` timestamps._\n"
    "\n"
    "_A low coverage rate is architectural, not a fixable cache inefficiency: only "
    "`knowledge_gateway_mcp.py`'s `knowledge_context`/`knowledge_status` tools are wired "
    "into this cache; the hard-rule-mandated `mcp__knowledge-search__search_docs` is served "
    "by a completely separate, uninstrumented implementation (`knowledge_search.py`) that "
    "never touches this cache path at all._\n"
    "\n"
    "**Cache Efficiency: NO DATA** — No KGMCP cache activity and no search/graphify tool "
    "calls recorded in this corpus — nothing to evaluate yet.\n"
    "\n"
    "| Metric | Value |\n"
    "|---|---|\n"
    "| Total hits | 0 |\n"
    "| Total writes | 0 |\n"
    "| Overall reuse rate | n/a |\n"
    "| Dead writes (never hit) | 0 |\n"
    "| Repeated refetches (within 300s) | 0 |\n"
    "| Real search/graphify calls (coverage denominator) | 0 |\n"
    "| Coverage rate (cache events / search calls) | n/a |\n"
    "\n"
    "_Derived from tools/retrieval_cache.py::read_cache_access_log()'s real "
    "retrieval_cache_access_log rows (Level 1 provider-result + Level 2 context-packet "
    "cache hit/write events only — 'invalidate' is a schema-supported but never-emitted "
    "event_type today) plus tools.jsonl's real search_docs/graphify/ToolSearch call "
    "volume (via build_search_count_section(), for `coverage` only). reuse_rate = hit / "
    "(hit + write) per ticket/agent/overall — the fraction of real access events served "
    "from cache rather than re-fetched. repeated_refetches flags a 'write' event for the "
    "same real cache row (same cache_level + query_hash/repo_branch_scope, or same "
    "cache_level + packet_id) following any prior event for that row within 300s — "
    "content re-fetched instead of reused. dead_writes flags a 'write' never followed by "
    "a 'hit' before the next write to that same row (or the end of the observed log) — a "
    "wasted write, as of what this function can currently see (a row that is still live "
    "may yet be hit later; this is not a permanent-deadness claim past the observed "
    "data). coverage compares total cache events against real search/graphify tool-call "
    "volume — a period with substantial search activity but few/zero cache events means "
    "retrieval work is bypassing the cache path, a real, distinct finding from a low "
    "reuse_rate. `ticket_id`/`agent` absent on a row (ad-hoc calls or a stale sidecar) "
    "are grouped under the literal 'unattributed' key, mirroring "
    "build_search_count_section()'s run_id=None convention. `stale_attribution_count` "
    "counts rows whose `.claude/current_run` sidecar pointed at an already-closed ticket "
    "at log time (tools/retrieval_cache.py::_sidecar_run_is_stale()) — a real, disclosed "
    "known limitation of sidecar-based attribution "
    "(TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD Scope item "
    "6), not a fixed one; these rows are still counted in hit/write/reuse-rate totals "
    "above, just flagged rather than silently trusted or dropped. "
    "`verdict`/`verdict_explanation` are a rule-based summary of the four signals above "
    "(reuse rate, repeated refetches, dead writes, coverage) — every clause is a literal "
    "readout of an already-computed number, never a fabricated score._\n"
    "\n"
    "## Notes\n"
    "\n"
    "_Fill in after reviewing the report above. What patterns stand out? What to improve?_\n"
)


def test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus(tmp_path):
    report = generate(_FIXED_CORPUS_RUNS, _FIXED_CORPUS_EVENTS, "fixed-label", tickets_root=tmp_path)

    assert report == _FIXED_CORPUS_EXPECTED_REPORT


# Hashes captured from generate_retro.py before this ticket's data-loading migration landed —
# proves these six functions (the three legacy-shape helpers plus the phase/agent normalization
# quartet) are byte-identical pre/post migration, not "also cleaned up" as unrequested scope creep.
_PRE_MIGRATION_SOURCE_HASHES = {
    "_resolve_status": "3af78b8f4068e490c572c4a74a4aa644e4c5a8e6c818209ed806408d7ccf70aa",
    "_is_legacy_event": "b63e60eb4a26afa9212f1fc3af7f9e63e7526cb450b8a91ef778a422c4f03c2a",
    "_is_gate_fail": "463d5c42d8c9094f865c7837bdc73f083a70005dbe034209f0a1eadd3deaf13e",
    "_normalize_phase": "b333ea95446d509fc9b3a188dd8dfdc2635ac429595353a1fd2b2475df31e1f1",
    "_normalize_agent": "aeb21df5446b1369edb9e0307218f325af919e7123db5b113529786607600115",
    "_canonicalize": "ce578ddee86f27ef1143f325a4ac012ad0676a13adb50d69e95ed33c91331cd6",
    "_flag_outliers": "4721cd694fe16bf98d52935c1bf0b888097d988ef9a6104e6afa55ce7c683ca0",
}


def test_normalize_phase_agent_and_flag_outliers_untouched():
    import hashlib
    import inspect

    for name, expected_hash in _PRE_MIGRATION_SOURCE_HASHES.items():
        source = inspect.getsource(getattr(generate_retro, name))
        actual_hash = hashlib.sha256(source.encode()).hexdigest()
        assert actual_hash == expected_hash, f"{name}'s source changed unexpectedly"


# ---------------------------------------------------------------------------
# TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT — AC7 proof-of-queryability
# ---------------------------------------------------------------------------

_ORDINARY_WORKFLOW_EVENT = {
    "run_id": "TCK-FAKE",
    "seq": 1,
    "ts": "2026-07-29T00:00:00Z",
    "phase": "Implement",
    "agent": "implementer",
    "summary": "ordinary workflow event, no retrieval fields",
    "status": "ok",
}


def _retrieval_event(**overrides):
    base = {
        "run_id": "RETRIEVAL-EVENT-test",
        "seq": 1,
        "ts": "2026-07-29T00:00:00Z",
        "phase": "Retrieval",
        "agent": "retrieval-cache-wrapper",
        "summary": "fixture retrieval event",
        "status": "ok",
        "retrieval_event_schema_version": 1,
    }
    base.update(overrides)
    return base


class TestComputeRetrievalMetrics:
    def test_non_retrieval_events_are_skipped_not_crashed_on(self):
        metrics = compute_retrieval_metrics([_ORDINARY_WORKFLOW_EVENT])
        assert metrics["retrieval_event_count"] == 0
        assert metrics["cache_rates"] == {}
        assert metrics["candidate_to_selected_ratios"] == []
        assert metrics["selected_to_cited_ratios"] == []

    def test_mixed_fixture_only_counts_retrieval_shaped_events(self):
        events = [
            _ORDINARY_WORKFLOW_EVENT,
            _retrieval_event(cache_level="retrieval_query_cache", cache_status="hit"),
            _ORDINARY_WORKFLOW_EVENT,
        ]
        metrics = compute_retrieval_metrics(events)
        assert metrics["retrieval_event_count"] == 1

    def test_cache_hit_miss_stale_rejected_rates_grouped_by_cache_level(self):
        events = [
            _retrieval_event(cache_level="retrieval_query_cache", cache_status="hit"),
            _retrieval_event(cache_level="retrieval_query_cache", cache_status="hit"),
            _retrieval_event(cache_level="retrieval_query_cache", cache_status="miss"),
            _retrieval_event(cache_level="retrieval_index_cache", cache_status="stale-rejected"),
        ]
        metrics = compute_retrieval_metrics(events)

        query_rates = metrics["cache_rates"]["retrieval_query_cache"]
        assert query_rates["counts"] == {"hit": 2, "miss": 1}
        assert query_rates["total"] == 3
        assert query_rates["rates"]["hit"] == pytest.approx(2 / 3)
        assert query_rates["rates"]["miss"] == pytest.approx(1 / 3)

        index_rates = metrics["cache_rates"]["retrieval_index_cache"]
        assert index_rates["counts"] == {"stale-rejected": 1}
        assert index_rates["total"] == 1

    def test_candidate_to_selected_ratio_computed_correctly(self):
        events = [_retrieval_event(candidate_count=10, selected_count=4)]
        metrics = compute_retrieval_metrics(events)
        assert metrics["candidate_to_selected_ratios"] == [
            {"run_id": "RETRIEVAL-EVENT-test", "seq": 1, "ratio": pytest.approx(0.4)}
        ]

    def test_candidate_to_selected_ratio_guards_zero_candidate_count(self):
        events = [_retrieval_event(candidate_count=0, selected_count=0)]
        metrics = compute_retrieval_metrics(events)
        assert metrics["candidate_to_selected_ratios"] == [
            {"run_id": "RETRIEVAL-EVENT-test", "seq": 1, "ratio": None}
        ]

    def test_selected_to_cited_ratio_computed_correctly(self):
        events = [_retrieval_event(selected_count=4, cited_source_hashes=["a" * 64, "b" * 64])]
        metrics = compute_retrieval_metrics(events)
        assert metrics["selected_to_cited_ratios"] == [
            {"run_id": "RETRIEVAL-EVENT-test", "seq": 1, "ratio": pytest.approx(0.5)}
        ]

    def test_selected_to_cited_ratio_guards_zero_selected_count(self):
        events = [_retrieval_event(selected_count=0, cited_source_hashes=[])]
        metrics = compute_retrieval_metrics(events)
        assert metrics["selected_to_cited_ratios"] == [
            {"run_id": "RETRIEVAL-EVENT-test", "seq": 1, "ratio": None}
        ]

    def test_cache_rates_already_covers_hit_miss_stale_rejected_by_level(self):
        from retrieval_cache import (
            HIT, MISS, STALE_REJECTED,
            INDEX_CACHE_CATEGORY, QUERY_CACHE_CATEGORY, PACKET_CACHE_CATEGORY,
        )

        events = [
            _retrieval_event(cache_level=INDEX_CACHE_CATEGORY, cache_status=HIT),
            _retrieval_event(cache_level=INDEX_CACHE_CATEGORY, cache_status=MISS),
            _retrieval_event(cache_level=INDEX_CACHE_CATEGORY, cache_status=STALE_REJECTED),
            _retrieval_event(cache_level=QUERY_CACHE_CATEGORY, cache_status=HIT),
            _retrieval_event(cache_level=QUERY_CACHE_CATEGORY, cache_status=HIT),
            _retrieval_event(cache_level=PACKET_CACHE_CATEGORY, cache_status=STALE_REJECTED),
        ]
        metrics = compute_retrieval_metrics(events)
        rates = metrics["cache_rates"]

        assert rates[INDEX_CACHE_CATEGORY]["counts"] == {HIT: 1, MISS: 1, STALE_REJECTED: 1}
        assert rates[INDEX_CACHE_CATEGORY]["total"] == 3
        assert rates[QUERY_CACHE_CATEGORY]["counts"] == {HIT: 2}
        assert rates[QUERY_CACHE_CATEGORY]["rates"][HIT] == pytest.approx(1.0)
        assert rates[PACKET_CACHE_CATEGORY]["counts"] == {STALE_REJECTED: 1}

    def test_function_is_read_only_no_write_call_or_file_open_in_write_mode(self):
        import inspect

        source = inspect.getsource(compute_retrieval_metrics)
        assert "write_lines(" not in source
        assert "write_line(" not in source
        assert '"w")' not in source and "'w')" not in source
        assert '"a")' not in source and "'a')" not in source
        assert "EVENTS_FILE" not in source
        assert "RUNS_FILE" not in source
        assert "load_jsonl" not in source
        assert "DEFAULT_DB_PATH" not in source

    def test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants(self):
        import inspect

        source = inspect.getsource(compute_retrieval_metrics)
        for literal in (
            '"hit"', "'hit'",
            '"miss"', "'miss'",
            '"stale-rejected"', "'stale-rejected'",
            '"retrieval_index_cache"', "'retrieval_index_cache'",
            '"retrieval_query_cache"', "'retrieval_query_cache'",
            '"retrieval_packet_cache"', "'retrieval_packet_cache'",
        ):
            assert literal not in source, f"{literal} re-literaled in compute_retrieval_metrics"

        module_source = inspect.getsource(generate_retro)
        assert "from retrieval_cache import" in module_source
        for name in (
            "HIT", "MISS", "STALE_REJECTED",
            "INDEX_CACHE_CATEGORY", "QUERY_CACHE_CATEGORY", "PACKET_CACHE_CATEGORY",
        ):
            assert name in module_source
        assert "from hybrid_retrieval import UNRATED" in module_source

    def test_candidate_to_selected_and_selected_to_cited_aggregate_ratio(self):
        events = [
            _retrieval_event(candidate_count=10, selected_count=4, seq=1),
            _retrieval_event(candidate_count=0, selected_count=0, seq=2),
            _retrieval_event(selected_count=4, cited_source_hashes=["a" * 64, "b" * 64], seq=3),
            _retrieval_event(selected_count=0, cited_source_hashes=[], seq=4),
        ]
        metrics = compute_retrieval_metrics(events)

        cts = metrics["candidate_to_selected_aggregate"]
        assert cts["total_candidates"] == 10
        assert cts["total_selected"] == 4
        assert cts["ratio"] == pytest.approx(0.4)

        stc = metrics["selected_to_cited_aggregate"]
        assert stc["total_selected"] == 4
        assert stc["total_cited"] == 2
        assert stc["ratio"] == pytest.approx(0.5)

    def test_candidate_to_selected_aggregate_ratio_is_none_when_all_candidate_counts_zero(self):
        events = [
            _retrieval_event(candidate_count=0, selected_count=0, seq=1),
            _retrieval_event(candidate_count=0, selected_count=0, seq=2),
        ]
        metrics = compute_retrieval_metrics(events)

        assert metrics["candidate_to_selected_aggregate"] == {
            "total_candidates": 0, "total_selected": 0, "ratio": None,
        }
        assert metrics["selected_to_cited_aggregate"] == {
            "total_selected": 0, "total_cited": 0, "ratio": None,
        }

    def test_freshness_authority_distribution_includes_unrated_sentinel_bucket(self):
        from hybrid_retrieval import UNRATED

        events = [
            _retrieval_event(
                authority_counts={"authoritative": 3, UNRATED: 2},
                freshness_counts={"fresh": 1, UNRATED: 4},
            ),
            _retrieval_event(
                authority_counts={"authoritative": 1, UNRATED: 1},
                freshness_counts={"fresh": 2},
            ),
        ]
        metrics = compute_retrieval_metrics(events)

        assert metrics["authority_distribution"] == {"authoritative": 4, UNRATED: 3}
        assert metrics["freshness_distribution"] == {"fresh": 3, UNRATED: 4}

    def test_freshness_authority_distribution_empty_when_no_counts_present(self):
        events = [_retrieval_event(cache_level="retrieval_query_cache", cache_status="hit")]
        metrics = compute_retrieval_metrics(events)

        assert metrics["authority_distribution"] == {}
        assert metrics["freshness_distribution"] == {}

    def test_expansion_rate_computed_from_adequacy_verdict_and_expansion_fields(self):
        # Formula is UNCONDITIONAL (plan.md Resolved Decision 1): fraction of events carrying
        # expansion_reason/expansion_count at all, regardless of adequacy_verdict. Of 4 events,
        # 2 carry an expansion field -> 0.5.
        events = [
            _retrieval_event(seq=1, adequacy_verdict="sufficient"),
            _retrieval_event(seq=2, adequacy_verdict="insufficient", expansion_reason="low_recall"),
            _retrieval_event(seq=3, adequacy_verdict="noisy", expansion_count=2),
            _retrieval_event(seq=4, adequacy_verdict="noisy"),
        ]
        metrics = compute_retrieval_metrics(events)

        assert metrics["expansion_rate"] == pytest.approx(0.5)

    def test_expansion_rate_zero_when_no_events_carry_expansion_fields(self):
        events = [
            _retrieval_event(seq=1, adequacy_verdict="sufficient"),
            _retrieval_event(seq=2, adequacy_verdict="insufficient"),
        ]
        metrics = compute_retrieval_metrics(events)

        assert metrics["expansion_rate"] == 0.0

    def test_expansion_rate_zero_when_no_retrieval_events_at_all(self):
        metrics = compute_retrieval_metrics([_ORDINARY_WORKFLOW_EVENT])
        assert metrics["expansion_rate"] == 0.0

    def test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger(self):
        # TCK-20260804-EXPANSION-RATE-WIRING: none of the 3 wrap_*() producers in
        # tools/retrieval_events.py is called by any real (non-test) caller yet, so no event in
        # the live corpus can carry expansion_reason/expansion_count. This is the honest, disclosed
        # current state (Open Decisions 5/6 remain deferred), not a bug -- and this test is a
        # regression guard against a future accidental fabrication silently making this non-zero.
        real_events = generate_retro.load_jsonl(generate_retro.EVENTS_FILE)
        metrics = compute_retrieval_metrics(real_events)
        assert metrics["expansion_rate"] == 0.0


# ---------------------------------------------------------------------------
# TCK-20260729-RETRIEVAL-RETRO-VIEWS — "## Retrieval Quality" rendered section
# ---------------------------------------------------------------------------

def test_retrieval_quality_section_omitted_when_no_retrieval_events():
    runs = [_BASE_RUN]
    events = [_ORDINARY_WORKFLOW_EVENT]

    report = generate(runs, events, "test-label")

    assert "## Retrieval Quality" not in report


def test_retrieval_quality_section_rendered_with_fixture_retrieval_events():
    from retrieval_cache import HIT, QUERY_CACHE_CATEGORY
    from hybrid_retrieval import UNRATED

    runs = [_BASE_RUN]
    events = [
        _ORDINARY_WORKFLOW_EVENT,
        _retrieval_event(
            cache_level=QUERY_CACHE_CATEGORY,
            cache_status=HIT,
            candidate_count=10,
            selected_count=4,
            cited_source_hashes=["a" * 64],
            authority_counts={"authoritative": 1, UNRATED: 1},
            freshness_counts={"fresh": 1},
            adequacy_verdict="sufficient",
        ),
    ]

    report = generate(runs, events, "test-label")

    assert "## Retrieval Quality" in report
    assert "--all" in report
    assert "### Cache Rates by Level" in report
    assert QUERY_CACHE_CATEGORY in report
    assert "### Noise Indicators" in report
    assert "### Freshness / Authority Distribution" in report
    assert UNRATED in report
    assert "### Expansion Rate" in report
    assert "0.0%" in report


def test_retrieval_quality_section_placement_does_not_disturb_existing_sections():
    runs = [
        dict(_BASE_RUN, run_id=f"TCK-STD-{i}", tier="standard", duration_s=1000)
        for i in range(4)
    ] + [dict(_BASE_RUN, run_id="TCK-STD-OUTLIER", tier="standard", duration_s=9000)]
    events = [_retrieval_event()]

    report = generate(runs, events, "test-label")

    assert "## Outliers" in report
    assert "## Retrieval Quality" in report
    assert "## Notes" in report

    outliers_idx = report.index("## Outliers")
    retrieval_idx = report.index("## Retrieval Quality")
    notes_idx = report.index("## Notes")

    assert outliers_idx < retrieval_idx < notes_idx


def test_no_new_frontend_ui_file_introduced_by_this_ticket():
    import inspect

    for fn in (compute_retrieval_metrics, generate):
        source = inspect.getsource(fn)
        assert "dashboard-frontend/src/" not in source
        assert "experiments/agent_ops_dashboard/" not in source
        assert "import react" not in source.lower()
        assert ".tsx" not in source
        assert ".jsx" not in source


# ---------------------------------------------------------------------------
# TCK-20260729-SHADOW-BASELINE-COMPARISON — "## Shadow vs. Baseline Retrieval
# Comparison" partition + rendered section
# ---------------------------------------------------------------------------

def test_shadow_comparison_partitions_real_vs_synthetic_run_id():
    import inspect

    source = inspect.getsource(compute_shadow_baseline_comparison)
    assert "infer_workflow(" in source
    assert "is not None" in source
    assert '"TCK-"' not in source
    assert "'TCK-'" not in source
    assert '"RETRIEVAL-EVENT-"' not in source
    assert "'RETRIEVAL-EVENT-'" not in source

    events = [
        _retrieval_event(run_id="TCK-REAL-1", agent="context-packet-wrapper", seq=-1),
        _retrieval_event(run_id="RETRIEVAL-EVENT-test", seq=1),
        _retrieval_event(run_id="RETRIEVAL-EVENT-hybrid-retrieval", seq=2),
        _ORDINARY_WORKFLOW_EVENT,  # run_id "TCK-FAKE" -> shadow cohort by run_id, but not
                                   # retrieval-shaped, so filtered out of the retrieval count too
    ]

    comparison = compute_shadow_baseline_comparison(events)

    assert comparison["shadow"]["retrieval_event_count"] == 1
    assert comparison["baseline"]["retrieval_event_count"] == 2


def test_shadow_comparison_computes_same_measurement_domain_as_compute_retrieval_metrics():
    shadow_event = _retrieval_event(
        run_id="TCK-REAL-2", agent="context-packet-wrapper", seq=-1,
        cache_level="retrieval_query_cache", cache_status="hit",
        candidate_count=10, selected_count=5,
    )
    baseline_event = _retrieval_event(
        run_id="RETRIEVAL-EVENT-test", seq=1,
        cache_level="retrieval_query_cache", cache_status="miss",
        candidate_count=4, selected_count=1,
    )
    events = [shadow_event, baseline_event]

    comparison = compute_shadow_baseline_comparison(events)

    assert comparison["shadow"] == compute_retrieval_metrics([shadow_event])
    assert comparison["baseline"] == compute_retrieval_metrics([baseline_event])


def test_shadow_comparison_reuses_compute_retrieval_metrics_not_reimplemented():
    import inspect

    source = inspect.getsource(compute_shadow_baseline_comparison)
    assert "compute_retrieval_metrics(" in source
    for literal in (
        '"hit"', "'hit'",
        '"miss"', "'miss'",
        '"stale-rejected"', "'stale-rejected'",
        '"retrieval_index_cache"', "'retrieval_index_cache'",
        '"retrieval_query_cache"', "'retrieval_query_cache'",
        '"retrieval_packet_cache"', "'retrieval_packet_cache'",
    ):
        assert literal not in source, (
            f"{literal} re-literaled in compute_shadow_baseline_comparison"
        )


def test_shadow_comparison_section_omitted_when_zero_shadow_events():
    runs = [_BASE_RUN]

    synthetic_only_events = [_retrieval_event(run_id="RETRIEVAL-EVENT-test")]
    report = generate(runs, synthetic_only_events, "test-label")
    assert "## Shadow vs. Baseline Retrieval Comparison" not in report

    no_retrieval_events = [_ORDINARY_WORKFLOW_EVENT]
    report_zero = generate(runs, no_retrieval_events, "test-label")
    assert "## Shadow vs. Baseline Retrieval Comparison" not in report_zero


def test_shadow_comparison_section_rendered_when_shadow_events_nonzero():
    from retrieval_cache import HIT, QUERY_CACHE_CATEGORY

    runs = [_BASE_RUN]
    events = [
        _retrieval_event(
            run_id="TCK-REAL-3", agent="context-packet-wrapper", seq=-1,
            cache_level=QUERY_CACHE_CATEGORY, cache_status=HIT,
            candidate_count=10, selected_count=5,
        ),
        _retrieval_event(run_id="RETRIEVAL-EVENT-test", seq=1),
    ]

    report = generate(runs, events, "test-label")

    assert "## Shadow vs. Baseline Retrieval Comparison" in report
    assert "| Retrieval event count | 1 | 1 |" in report


def test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture(tmp_path):
    report = generate(_FIXED_CORPUS_RUNS, _FIXED_CORPUS_EVENTS, "fixed-label", tickets_root=tmp_path)

    assert report == _FIXED_CORPUS_EXPECTED_REPORT
    assert "## Shadow vs. Baseline Retrieval Comparison" not in report


def test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase():
    from retrieval_cache import HIT, QUERY_CACHE_CATEGORY

    runs = [_BASE_RUN]
    events = [
        _retrieval_event(
            run_id="TCK-REAL-4", agent="context-packet-wrapper", seq=-1,
            cache_level=QUERY_CACHE_CATEGORY, cache_status=HIT,
            candidate_count=10, selected_count=5,
        ),
        _retrieval_event(run_id="RETRIEVAL-EVENT-test", seq=1),
    ]

    report = generate(runs, events, "test-label")
    assert "## Shadow vs. Baseline Retrieval Comparison" in report

    report_lower = report.lower()
    for phrase in (
        "authoritative-source recall",
        "missed contracts",
        "review rework",
        "context tokens",
        "cache correctness",
        "provider parity",
        "privacy boundary",
        "approval gate",
        "promotion",
    ):
        assert phrase not in report_lower, f"forbidden phrase {phrase!r} found in report"


def test_shadow_comparison_new_tests_are_fixture_only_no_live_data_read():
    import inspect

    new_test_functions = [
        test_shadow_comparison_partitions_real_vs_synthetic_run_id,
        test_shadow_comparison_computes_same_measurement_domain_as_compute_retrieval_metrics,
        test_shadow_comparison_reuses_compute_retrieval_metrics_not_reimplemented,
        test_shadow_comparison_section_omitted_when_zero_shadow_events,
        test_shadow_comparison_section_rendered_when_shadow_events_nonzero,
        test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture,
        test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase,
    ]
    for fn in new_test_functions:
        source = inspect.getsource(fn)
        assert "EVENTS_FILE" not in source
        assert "RUNS_FILE" not in source
        assert "DEFAULT_DB_PATH" not in source
        assert "_load_runs_and_events" not in source


# ---------------------------------------------------------------------------
# TCK-20260803-RETRO-TOOL-SAFETY-AUDIT — compute_tool_safety_metrics() and the
# "## Tool Safety Audit" rendered section
# ---------------------------------------------------------------------------

def _investigate_event(**overrides):
    base = {
        "run_id": "TCK-SAFETY-TEST",
        "seq": 1,
        "ts": "2026-08-03T00:00:00Z",
        "phase": "Investigate",
        "agent": "investigator",
        "summary": "investigate fixture event",
        "status": "ok",
    }
    base.update(overrides)
    return base


def _tool_row(**overrides):
    base = {
        "run_id": "TCK-SAFETY-TEST",
        "seq": 1,
        "tool": "Read",
        "input_summary": "some file",
    }
    base.update(overrides)
    return base


def test_search_before_grep_compliance_true_when_search_docs_precedes_grep():
    events = [_investigate_event()]
    tools = [
        _tool_row(tool="mcp__knowledge-search__search_docs", input_summary="query: foo"),
        _tool_row(tool="Grep", input_summary="pattern foo"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["investigate_pair_count"] == 1
    assert sbg["compliant_count"] == 1
    assert sbg["compliance_rate"] == pytest.approx(1.0)
    assert sbg["per_pair_compliance"]["TCK-SAFETY-TEST::1"] is True


def test_search_before_grep_compliance_true_when_graphify_bash_call_precedes_grep():
    events = [_investigate_event()]
    tools = [
        _tool_row(tool="Bash", input_summary="graphify query \"foo\""),
        _tool_row(tool="Bash", input_summary="grep -rn foo ."),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["compliant_count"] == 1
    assert sbg["per_pair_compliance"]["TCK-SAFETY-TEST::1"] is True


def test_search_before_grep_compliance_false_when_grep_tool_precedes_search_docs():
    events = [_investigate_event()]
    tools = [
        _tool_row(tool="Grep", input_summary="pattern foo"),
        _tool_row(tool="mcp__knowledge-search__search_docs", input_summary="query: foo"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["compliant_count"] == 0
    assert sbg["compliance_rate"] == pytest.approx(0.0)
    assert sbg["per_pair_compliance"]["TCK-SAFETY-TEST::1"] is False


def test_search_before_grep_compliance_false_when_bash_grep_precedes_search_docs():
    events = [_investigate_event()]
    tools = [
        _tool_row(tool="Bash", input_summary="grep -rn foo ."),
        _tool_row(tool="mcp__knowledge-search__search_docs", input_summary="query: foo"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["compliant_count"] == 0
    assert sbg["per_pair_compliance"]["TCK-SAFETY-TEST::1"] is False


def test_search_before_grep_compliance_rate_aggregated_across_multiple_investigate_pairs():
    events = [
        _investigate_event(run_id="TCK-A", seq=1),
        _investigate_event(run_id="TCK-B", seq=1),
        _investigate_event(run_id="TCK-C", seq=1),
    ]
    tools = [
        # TCK-A: compliant (search before grep)
        _tool_row(run_id="TCK-A", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-A", seq=1, tool="Grep", input_summary="p"),
        # TCK-B: compliant (never greps at all)
        _tool_row(run_id="TCK-B", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f"),
        # TCK-C: non-compliant (grep before search)
        _tool_row(run_id="TCK-C", seq=1, tool="Grep", input_summary="p"),
        _tool_row(run_id="TCK-C", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["investigate_pair_count"] == 3
    assert sbg["compliant_count"] == 2
    assert sbg["compliance_rate"] == pytest.approx(2 / 3)


def test_search_before_grep_ignores_non_investigate_phase_tool_calls():
    events = [
        {"run_id": "TCK-IMPL", "seq": 1, "phase": "Implement", "agent": "implementer",
         "status": "ok", "summary": "not investigate"},
    ]
    tools = [
        _tool_row(run_id="TCK-IMPL", seq=1, tool="Grep", input_summary="p"),
        _tool_row(run_id="TCK-IMPL", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    assert sbg["investigate_pair_count"] == 0
    assert sbg["per_pair_compliance"] == {}


def test_parity_write_safety_zero_violations_on_clean_fixture():
    tools = [
        _tool_row(tool="Edit", input_summary="src/engine/kernel.py"),
        _tool_row(tool="Write", input_summary="tests/tools/test_generate_retro.py"),
        _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py build --db-path /tmp/pi_smoke2/parity.db"),
    ]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 0
    assert pws["unsafe_parity_build_count"] == 0
    assert pws["parity_ledger_yaml_write_examples"] == []
    assert pws["unsafe_parity_build_examples"] == []


def test_parity_write_safety_detects_edit_cooccurring_with_same_run_build_call():
    violating_row = _tool_row(tool="Edit", input_summary="docs/parity_ledger/combat_movement.yaml")
    build_row = _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py build --db-path /tmp/pi/parity.db")
    tools = [
        _tool_row(tool="Edit", input_summary="src/engine/kernel.py"),
        violating_row,
        build_row,
    ]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 1
    assert pws["parity_ledger_yaml_write_examples"] == [violating_row]


def test_parity_write_safety_lone_yaml_edit_no_longer_counts():
    lone_edit = _tool_row(tool="Edit", input_summary="docs/parity_ledger/combat_movement.yaml")
    tools = [
        _tool_row(tool="Edit", input_summary="src/engine/kernel.py"),
        lone_edit,
    ]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 0
    assert pws["parity_ledger_yaml_write_examples"] == []


def test_parity_write_safety_yaml_edit_and_build_different_run_ids_not_flagged():
    edit_row = _tool_row(run_id="TCK-A", tool="Edit", input_summary="docs/parity_ledger/combat_movement.yaml")
    build_row = _tool_row(run_id="TCK-B", tool="Bash", input_summary="python3 tools/parity_index.py build")
    tools = [edit_row, build_row]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 0
    assert pws["parity_ledger_yaml_write_examples"] == []


def test_parity_write_safety_help_call_does_not_count_as_build():
    edit_row = _tool_row(tool="Edit", input_summary="docs/parity_ledger/combat_movement.yaml")
    help_row = _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py --help")
    tools = [edit_row, help_row]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 0
    assert pws["parity_ledger_yaml_write_examples"] == []


def test_parity_write_safety_detects_build_targeting_real_repo_path():
    no_override_row = _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py build")
    real_path_row = _tool_row(
        tool="Bash",
        input_summary="python3 tools/parity_index.py build --db-path parity-index/parity.db",
    )
    scratch_row = _tool_row(
        tool="Bash",
        input_summary="python3 tools/parity_index.py build --db-path /tmp/pi_smoke2/parity.db",
    )
    tools = [no_override_row, real_path_row, scratch_row]
    metrics = compute_tool_safety_metrics([], tools)
    pws = metrics["parity_write_safety"]
    assert pws["unsafe_parity_build_count"] == 2
    assert no_override_row in pws["unsafe_parity_build_examples"]
    assert real_path_row in pws["unsafe_parity_build_examples"]
    assert scratch_row not in pws["unsafe_parity_build_examples"]


def test_tool_safety_function_never_crashes_on_malformed_rows():
    events = [_investigate_event(run_id="TCK-SAFETY-TEST", seq=1)]
    tools = [
        {"run_id": "TCK-SAFETY-TEST", "seq": 1, "tool": "Grep"},  # missing input_summary
        {"run_id": "TCK-SAFETY-TEST", "seq": None, "tool": "Grep", "input_summary": "p"},  # seq null
        {"run_id": "TCK-OTHER", "seq": 1, "tool": "Grep", "input_summary": "p"},  # no matching pair
        {"run_id": "TCK-SAFETY-TEST", "seq": -1, "tool": "Grep", "input_summary": "p"},  # shadow packet
        {"run_id": None, "seq": None, "tool": "Bash", "input_summary": None},  # fully null
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    sbg = metrics["search_before_grep"]
    # Only the row with matching (run_id, seq) == ("TCK-SAFETY-TEST", 1) is attributed to the
    # Investigate pair; the malformed input_summary does not raise.
    assert sbg["investigate_pair_count"] == 1
    assert sbg["per_pair_compliance"]["TCK-SAFETY-TEST::1"] is False  # grep with no preceding search
    pws = metrics["parity_write_safety"]
    assert pws["parity_ledger_yaml_write_count"] == 0
    assert pws["unsafe_parity_build_count"] == 0


def test_tool_safety_function_is_pure_no_file_io():
    import inspect

    source = inspect.getsource(compute_tool_safety_metrics)
    assert "write_lines(" not in source
    assert "write_line(" not in source
    assert '"w")' not in source and "'w')" not in source
    assert '"a")' not in source and "'a')" not in source
    assert "EVENTS_FILE" not in source
    assert "RUNS_FILE" not in source
    assert "DEFAULT_TOOLS_FILE" not in source
    assert "load_jsonl" not in source
    assert "DEFAULT_DB_PATH" not in source


def test_new_section_rendered_in_generate_output_when_investigate_tool_data_present():
    runs = [_BASE_RUN]
    events = [_investigate_event()]
    tools = [
        _tool_row(tool="mcp__knowledge-search__search_docs", input_summary="query: foo"),
        _tool_row(tool="Grep", input_summary="pattern foo"),
    ]

    report = generate(runs, events, "test-label", tools=tools)

    assert "## Tool Safety Audit" in report
    assert "### Search-Before-Grep Compliance (Investigate Phase)" in report
    assert "**Compliance rate:** 100.0% (1/1 Investigate-phase calls)" in report
    assert "### Parity Ledger Write-Safety" in report
    assert "`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 0" in report
    assert "Unsafe `parity_index.py build` invocations (real repo path):** 0" in report

    notes_idx = report.index("## Notes")
    tool_safety_idx = report.index("## Tool Safety Audit")
    assert tool_safety_idx < notes_idx


def test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data():
    runs = [_BASE_RUN]
    events = [_ORDINARY_WORKFLOW_EVENT]

    report_no_tools = generate(runs, events, "test-label")
    assert "## Tool Safety Audit" not in report_no_tools

    report_empty_tools = generate(runs, events, "test-label", tools=[])
    assert "## Tool Safety Audit" not in report_empty_tools


# ---------------------------------------------------------------------------
# TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
# ## Search & Investigation Effort (AC1) — trended search/raw-investigation section
# ---------------------------------------------------------------------------

def test_search_read_investigation_section_wired_into_generate_output():
    runs = [_BASE_RUN]
    events = [_ORDINARY_WORKFLOW_EVENT]
    tools = [
        _tool_row(tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(tool="Read", input_summary="f1"),
        _tool_row(tool="Read", input_summary="f2"),
    ]

    report = generate(runs, events, "test-label", tools=tools)

    assert "## Search & Investigation Effort" in report
    assert "### Search Calls (Follow-Up Search Tooling)" in report
    assert "**Total:** 1" in report
    assert "### Raw Investigation (Read) Calls" in report
    assert "**Total:** 2" in report
    assert "**Read-to-search ratio:** 2.0" in report


def test_search_read_investigation_section_never_silent_has_derivation():
    tools = [_tool_row(tool="mcp__knowledge-search__search_docs", input_summary="q")]
    sit = compute_search_investigation_trend(tools)
    assert sit["search_count"]["derivation"]
    assert sit["raw_investigation_count"]["derivation"]


def test_search_read_investigation_section_reuses_retrieval_baseline_metrics_not_reimplemented():
    import ast
    import inspect

    source = inspect.getsource(compute_search_investigation_trend)
    tree = ast.parse(source)
    call_names = {
        n.func.id for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "build_search_count_section" in call_names
    assert "build_raw_investigation_count_section" in call_names
    assert "for record in tools" not in source
    assert "SEARCH_TOOL_NAMES" not in source


# ---------------------------------------------------------------------------
# ## Agent Monitoring Retro Index — Search Calls / Read Calls trend columns (AC1)
# ---------------------------------------------------------------------------

def test_index_md_trends_search_and_read_investigation_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_retro, "RETRO_DIR", tmp_path)
    (tmp_path / "RETRO-2026-W01.md").write_text("placeholder")
    (tmp_path / "RETRO-2026-W02.md").write_text("placeholder")

    all_runs = [
        {"run_id": "TCK-W1", "start_ts": "2026-01-01T00:00:00Z", "final_status": "DONE"},
        {"run_id": "TCK-W2", "start_ts": "2026-01-08T00:00:00Z", "final_status": "DONE"},
    ]
    all_tools = [
        _tool_row(run_id="TCK-W1", tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-W1", tool="Read", input_summary="f"),
        _tool_row(run_id="TCK-W1", tool="Read", input_summary="f2"),
        _tool_row(run_id="TCK-W1", tool="Skill", input_summary="{'skill': 'graphify'}"),
        _tool_row(run_id="TCK-W2", tool="Read", input_summary="f"),
    ]

    generate_retro._update_index(all_runs, all_tools)

    index_text = (tmp_path / "index.md").read_text()
    assert (
        "| Report | Runs | DONE | Gate failures | Search Calls | Read Calls | "
        "Skill Invocations |" in index_text
    )

    week1_line = next(l for l in index_text.splitlines() if "2026-W01" in l)
    week2_line = next(l for l in index_text.splitlines() if "2026-W02" in l)
    assert week1_line.split("|") == [
        "", " [2026-W01](RETRO-2026-W01.md) ", " 1 ", " 1 ", " 0 ", " 1 ", " 2 ", " 1 ", "",
    ]
    assert week2_line.split("|") == [
        "", " [2026-W02](RETRO-2026-W02.md) ", " 1 ", " 1 ", " 0 ", " 0 ", " 1 ", " 0 ", "",
    ]


def test_index_md_all_tools_default_never_crashes_on_none(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_retro, "RETRO_DIR", tmp_path)
    (tmp_path / "RETRO-ALL.md").write_text("placeholder")
    generate_retro._update_index([{"run_id": "TCK-A", "start_ts": "2026-01-01T00:00:00Z"}])  # all_tools omitted
    index_text = (tmp_path / "index.md").read_text()
    assert "| [ALL]" in index_text


# ---------------------------------------------------------------------------
# ## Tool Safety Audit — Read-Count Correlation subsection (AC2)
# ---------------------------------------------------------------------------

def test_correlation_computes_read_count_per_investigate_pair():
    events = [
        _investigate_event(run_id="TCK-A", seq=1),
        _investigate_event(run_id="TCK-B", seq=1),
    ]
    tools = [
        # TCK-A: compliant, 2 Read calls
        _tool_row(run_id="TCK-A", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-A", seq=1, tool="Read", input_summary="f1"),
        _tool_row(run_id="TCK-A", seq=1, tool="Read", input_summary="f2"),
        # TCK-B: non-compliant, 5 Read calls
        _tool_row(run_id="TCK-B", seq=1, tool="Grep", input_summary="p"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f1"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f2"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f3"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f4"),
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary="f5"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    rcc = metrics["read_count_correlation"]
    assert rcc["compliant_group"]["count"] == 1
    assert rcc["compliant_group"]["median"] == 2
    assert rcc["compliant_group"]["average"] == 2
    assert rcc["non_compliant_group"]["count"] == 1
    assert rcc["non_compliant_group"]["median"] == 5
    assert rcc["non_compliant_group"]["average"] == 5


def test_correlation_median_average_split_by_compliance():
    events = [
        _investigate_event(run_id="TCK-A", seq=1),
        _investigate_event(run_id="TCK-B", seq=1),
        _investigate_event(run_id="TCK-C", seq=1),
    ]
    tools = [
        # TCK-A: compliant, 1 Read
        _tool_row(run_id="TCK-A", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-A", seq=1, tool="Read", input_summary="f1"),
        # TCK-B: compliant, 9 Reads
        _tool_row(run_id="TCK-B", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
    ] + [
        _tool_row(run_id="TCK-B", seq=1, tool="Read", input_summary=f"f{i}") for i in range(9)
    ] + [
        # TCK-C: non-compliant, 3 Reads
        _tool_row(run_id="TCK-C", seq=1, tool="Grep", input_summary="p"),
        _tool_row(run_id="TCK-C", seq=1, tool="Read", input_summary="f1"),
        _tool_row(run_id="TCK-C", seq=1, tool="Read", input_summary="f2"),
        _tool_row(run_id="TCK-C", seq=1, tool="Read", input_summary="f3"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    rcc = metrics["read_count_correlation"]
    assert rcc["compliant_group"]["count"] == 2
    assert rcc["compliant_group"]["median"] == 5  # median of [1, 9]
    assert rcc["compliant_group"]["average"] == 5  # average of [1, 9]
    assert rcc["non_compliant_group"]["count"] == 1
    assert rcc["non_compliant_group"]["median"] == 3
    assert rcc["non_compliant_group"]["average"] == 3


def test_correlation_reuses_per_pair_compliance_not_a_second_pass():
    import inspect

    source = inspect.getsource(compute_tool_safety_metrics)
    # The correlation logic must read pair_tool_rows/per_pair_compliance as already computed,
    # not re-derive Investigate-pair attribution a second time inside the same function.
    assert source.count("investigate_pairs = {") == 1
    assert source.count("pair_tool_rows = defaultdict") == 1
    assert "for row in tools" in source  # the one, original pair_tool_rows population loop
    assert source.count("for row in tools") == 1


def test_correlation_section_omitted_when_no_investigate_pairs():
    runs = [_BASE_RUN]
    events = [_ORDINARY_WORKFLOW_EVENT]
    report = generate(runs, events, "test-label", tools=[])
    assert "### Read-Count Correlation" not in report


def test_correlation_handles_single_group_empty_gracefully():
    events = [_investigate_event(run_id="TCK-A", seq=1)]
    tools = [
        _tool_row(run_id="TCK-A", seq=1, tool="mcp__knowledge-search__search_docs", input_summary="q"),
        _tool_row(run_id="TCK-A", seq=1, tool="Read", input_summary="f1"),
    ]
    metrics = compute_tool_safety_metrics(events, tools)
    rcc = metrics["read_count_correlation"]
    assert rcc["compliant_group"]["count"] == 1
    assert rcc["non_compliant_group"]["count"] == 0
    assert rcc["non_compliant_group"]["median"] is None
    assert rcc["non_compliant_group"]["average"] is None

    report = generate([_BASE_RUN], events, "test-label", tools=tools)
    assert "### Read-Count Correlation" in report
    assert "| Non-compliant | 0 | n/a | n/a |" in report


def test_correlation_real_corpus_produces_a_real_number():
    real_events = generate_retro.load_jsonl(generate_retro.EVENTS_FILE)
    real_tools = generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    metrics = compute_tool_safety_metrics(real_events, real_tools)
    rcc = metrics["read_count_correlation"]
    assert rcc["compliant_group"]["count"] > 0
    assert rcc["non_compliant_group"]["count"] > 0


# ---------------------------------------------------------------------------
# ## Parity Index Read-Path Usage (AC3)
# ---------------------------------------------------------------------------

def test_parity_index_readpath_call_count_matches_real_corpus_state():
    # Was pinned at 0 (TCK-20260731-PARITY-READPATH-GATE's Gate A review: reviewed GO but not yet
    # wired into any real call site). compute_parity_index_readpath_call_count()'s own docstring
    # already anticipated this changing -- "a future real call site needs zero code change here to
    # start reporting a nonzero number" -- and that happened: TCK-20260819-STANDARD-PARITY-LEDGER-
    # HYGIENE-SWEEP's implementer and done-checker agents legitimately ran
    # `tools/parity_index.py health` 3 times via Bash during Implement/Verify (that ticket's whole
    # subject was the parity-ledger health checker), recording 3 real rows into the committed
    # agent-monitoring/tools.jsonl corpus this test reads. This is expected drift, not a bug -- see
    # TCK-20260820-HOTFIX-PARITY-READPATH-BASELINE-DRIFT. It then drifted a 2nd time (3 -> 4) when
    # TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION's parity-updater phase legitimately ran
    # `tools/parity_index.py entry INFRA-366` (2026-08-21T02:30:02Z), recording a 4th real row --
    # again expected drift, not a bug -- see TCK-20260821-HOTFIX-PARITY-READPATH-BASELINE-DRIFT-2.
    real_tools = generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    result = compute_parity_index_readpath_call_count(real_tools)
    assert result["count"] == 4
    assert result["derivation"]


def test_parity_index_readpath_detection_matches_real_call_when_present():
    tools = [
        _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py entry INFRA-292"),
        _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py impact --changed-path src/foo.py"),
        _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py health --subsystem combat"),
    ]
    result = compute_parity_index_readpath_call_count(tools)
    assert result["count"] == 3
    assert len(result["examples"]) == 3
    assert result["bash_rows_scanned"] == 3


def test_parity_index_readpath_detection_false_positive_guards():
    tools = [
        _tool_row(tool="Bash", input_summary="python3 tools/parity_index.py --help"),
        _tool_row(tool="Bash", input_summary="git log -- docs/foo tools/parity_index.py"),
        _tool_row(tool="Bash", input_summary="pytest tests/tools/test_parity_index.py -k impact"),
        _tool_row(tool="Bash", input_summary="sed -n '1,60p' tools/parity_index.py"),
    ]
    result = compute_parity_index_readpath_call_count(tools)
    assert result["count"] == 0
    assert result["examples"] == []


def test_parity_index_readpath_section_never_silent_has_derivation():
    result = compute_parity_index_readpath_call_count([])
    assert result["derivation"]
    assert len(result["derivation"]) > 20  # prose, not a bare number or empty marker
    assert isinstance(result["count"], int)

    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=[])
    assert "## Parity Index Read-Path Usage" in report
    assert "0/0 Bash rows scanned" in report


# ---------------------------------------------------------------------------
# Cross-cutting (AC4/AC5)
# ---------------------------------------------------------------------------

def test_all_new_sections_have_derivation_key(tmp_path):
    sit = compute_search_investigation_trend([])
    assert "derivation" in sit["search_count"]
    assert "derivation" in sit["raw_investigation_count"]

    tool_safety = compute_tool_safety_metrics([_investigate_event()], [_tool_row()])
    assert "derivation" in tool_safety["read_count_correlation"]

    pircc = compute_parity_index_readpath_call_count([])
    assert "derivation" in pircc

    assert "derivation" in build_skill_usage_section([])
    assert "derivation" in compute_zero_invocation_skill_flags([], skills_dir=tmp_path)


def test_new_sections_never_write_any_file():
    import inspect

    for func in (
        compute_search_investigation_trend,
        compute_tool_safety_metrics,
        compute_parity_index_readpath_call_count,
        build_skill_usage_section,
        compute_zero_invocation_skill_flags,
    ):
        source = inspect.getsource(func)
        assert "write_lines(" not in source
        assert "write_line(" not in source
        assert '"w")' not in source and "'w')" not in source
        assert '"a")' not in source and "'a')" not in source
        assert "EVENTS_FILE" not in source
        assert "RUNS_FILE" not in source
        assert "DEFAULT_TOOLS_FILE" not in source
        assert "load_jsonl" not in source


# ---------------------------------------------------------------------------
# ## Skill Usage (AC1/AC2/AC3/AC4) — TCK-20260810-SKILL-USAGE-RETRO-TRACKING
# ---------------------------------------------------------------------------

def test_generate_retro_imports_build_skill_usage_section_not_a_reimplementation():
    """AST guard: skill_usage_metric.py now re-imports build_skill_usage_section from
    generate_retro.py rather than defining it locally (Step 1's relocation)."""
    import ast

    module_path = _MONITORING_TOOLS_DIR / "skill_usage_metric.py"
    tree = ast.parse(module_path.read_text())

    imported_names = set()
    defined_func_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.name)
        if isinstance(node, ast.FunctionDef):
            defined_func_names.add(node.name)

    assert "build_skill_usage_section" in imported_names
    assert "build_skill_usage_section" not in defined_func_names

    generate_retro_path = _MONITORING_TOOLS_DIR / "generate_retro.py"
    generate_retro_tree = ast.parse(generate_retro_path.read_text())
    generate_retro_func_names = {
        n.name for n in ast.walk(generate_retro_tree) if isinstance(n, ast.FunctionDef)
    }
    assert "build_skill_usage_section" in generate_retro_func_names


def test_skill_usage_section_present_in_generated_report():
    tools = [
        _tool_row(run_id="TCK-A", tool="Skill", input_summary="{'skill': 'graphify'}"),
        _tool_row(run_id="TCK-A", tool="Skill", input_summary="{'skill': 'graphify'}"),
    ]
    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=tools)
    assert "## Skill Usage" in report
    assert "### Per-Skill Invocation Counts (This Period)" in report
    assert "graphify" in report
    assert "### Zero-Invocation Flags" not in report


def test_skill_usage_section_matches_real_corpus_counts():
    real_tools = generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    expected = build_skill_usage_section(real_tools)
    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=real_tools)
    if expected["total_skill_invocations"] > 0:
        assert "## Skill Usage" in report
        assert f"**Total:** {expected['total_skill_invocations']}" in report
        for skill, count in expected["per_skill"].items():
            assert f"| {skill} | {count} |" in report


def test_skill_usage_section_has_derivation():
    tools = [_tool_row(run_id="TCK-A", tool="Skill", input_summary="{'skill': 'graphify'}")]
    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=tools)
    su = build_skill_usage_section(tools)
    assert su["derivation"] in report


def test_skill_usage_section_omitted_when_no_skill_calls_and_no_all_tools():
    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=[_tool_row()])
    assert "## Skill Usage" not in report


def test_skill_usage_trend_column_in_retro_index(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_retro, "RETRO_DIR", tmp_path)
    (tmp_path / "RETRO-2026-W03.md").write_text("placeholder")

    all_runs = [{"run_id": "TCK-W3", "start_ts": "2026-01-15T00:00:00Z", "final_status": "DONE"}]
    all_tools = [
        _tool_row(run_id="TCK-W3", tool="Skill", input_summary="{'skill': 'graphify'}"),
        _tool_row(run_id="TCK-W3", tool="Skill", input_summary="{'skill': 'graphify'}"),
        _tool_row(run_id="TCK-W3", tool="Skill", input_summary="{'skill': 'implement-ticket'}"),
    ]
    generate_retro._update_index(all_runs, all_tools)

    index_text = (tmp_path / "index.md").read_text()
    assert "Skill Invocations" in index_text
    week3_line = next(l for l in index_text.splitlines() if "2026-W03" in l)
    assert week3_line.strip().endswith("| 3 |")


# --- compute_zero_invocation_skill_flags (Step 3) ---

def _write_skill(skills_dir, name, date_added=None, frontmatter_extra=""):
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    fm_lines = ["---"]
    if date_added is not None:
        fm_lines.append(f'date_added: "{date_added}"')
    if frontmatter_extra:
        fm_lines.append(frontmatter_extra)
    fm_lines.append("---")
    fm_lines.append(f"# {name}")
    (skill_dir / "SKILL.md").write_text("\n".join(fm_lines) + "\n")
    return skill_dir


def test_zero_invocation_flag_excludes_skill_within_grace_period(tmp_path):
    _write_skill(tmp_path, "fresh-skill", date_added="2026-08-05")
    result = compute_zero_invocation_skill_flags(
        [], skills_dir=tmp_path, today=date(2026, 8, 15)
    )
    assert "fresh-skill" not in result["flagged_stale"]
    assert "fresh-skill" not in result["flagged_unknown_age"]


def test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations(tmp_path):
    _write_skill(tmp_path, "old-skill", date_added="2026-07-01")
    result = compute_zero_invocation_skill_flags(
        [], skills_dir=tmp_path, today=date(2026, 8, 15)
    )
    assert "old-skill" in result["flagged_stale"]
    assert "old-skill" not in result["flagged_unknown_age"]


def test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age(tmp_path):
    _write_skill(tmp_path, "old-but-used", date_added="2026-01-01")
    tools = [_tool_row(run_id="TCK-A", tool="Skill", input_summary="{'skill': 'old-but-used'}")]
    result = compute_zero_invocation_skill_flags(tools, skills_dir=tmp_path, today=date(2026, 8, 15))
    assert "old-but-used" not in result["flagged_stale"]
    assert "old-but-used" not in result["flagged_unknown_age"]


def test_backend_testing_pre_fix_state_would_have_been_flagged(tmp_path):
    """Sanity check per AC2: backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-
    UNDISCLOSED state had no date_added/source field at all — reconstructed here as a synthetic
    fixture (no date_added) with zero invocations."""
    _write_skill(tmp_path, "backend-testing", date_added=None)
    result = compute_zero_invocation_skill_flags([], skills_dir=tmp_path, today=date(2026, 8, 15))
    assert "backend-testing" in result["flagged_unknown_age"]
    assert "backend-testing" not in result["flagged_stale"]


def test_backend_testing_post_fix_state_not_currently_flagged():
    """Real-corpus check: the actual, current .claude/skills/backend-testing/SKILL.md has a
    real date_added (2026-08-05, post-fix) — as of this ticket it is within the grace period, so
    it must not appear in flagged_stale on the real catalog today. Soft-checked (TCK-20260819-
    SKILL-STALENESS-SOFT-WARNING): grace-period expiry is calendar-driven, not code-driven, so a
    miss here warns rather than hard-fails CI — see tests/tools/skill_staleness_assertions.py."""
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    skill_staleness_check(
        "backend-testing" not in result["flagged_stale"],
        f"skill 'backend-testing' flagged stale (zero invocations past "
        f"{result['grace_period_days']}-day grace period): "
        f"flagged_stale={result['flagged_stale']!r}",
    )


def test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md(tmp_path):
    skill_dir = tmp_path / "broken-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nthis line has no colon at all\n---\nbody\n")
    result = compute_zero_invocation_skill_flags([], skills_dir=tmp_path, today=date(2026, 8, 15))
    assert "broken-skill" in result["flagged_unknown_age"]
    assert "broken-skill" in result["catalog_parse_errors"]


def test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation(tmp_path):
    _write_skill(tmp_path, "some-skill", date_added="2026-01-01")
    before = (tmp_path / "some-skill" / "SKILL.md").read_text()
    compute_zero_invocation_skill_flags([], skills_dir=tmp_path, today=date(2026, 8, 15))
    after = (tmp_path / "some-skill" / "SKILL.md").read_text()
    assert before == after


def test_grace_period_missing_date_added_policy_is_explicit_not_accidental(tmp_path):
    result = compute_zero_invocation_skill_flags([], skills_dir=tmp_path)
    assert "flagged_unknown_age" in result["derivation"]
    assert "flagged_stale" in result["derivation"]
    assert "backend-testing" in result["derivation"]


def test_flagged_skills_list_never_auto_triggers_downstream_action():
    import inspect

    source = inspect.getsource(compute_zero_invocation_skill_flags)
    for forbidden in ("deprecat", "auto_invoke", "write_text(", "unlink(", "rmtree("):
        assert forbidden not in source


def test_six_domain_skills_verdict_not_reopened(tmp_path):
    """Guard against re-litigating TCK-20260705-SIX-SKILLS-INVESTIGATION's settled verdicts —
    the derivation string must never claim to prove or disprove those verdicts."""
    result = compute_zero_invocation_skill_flags([], skills_dir=tmp_path)
    for forbidden in ("correctly redundant", "SIX-SKILLS-INVESTIGATION", "proves"):
        assert forbidden not in result["derivation"]


def test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus():
    """Real-corpus check (AC2): the 6 domain skills authored by
    TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC must never appear in flagged_stale today —
    either because they now have >=1 real invocation, or because they are still within the grace
    period. Never hardcodes "all 6 show zero" (that snapshot has already drifted). Soft-checked
    (TCK-20260819-SKILL-STALENESS-SOFT-WARNING): see tests/tools/skill_staleness_assertions.py."""
    domain_skills = {
        "observability", "simq-dev", "systems-economy",
        "combat-mechanics", "cognition-strategy", "progression-entities",
    }
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    stale_domain_skills = domain_skills.intersection(set(result["flagged_stale"]))
    skill_staleness_check(
        not stale_domain_skills,
        f"domain skill(s) flagged stale (zero invocations past "
        f"{result['grace_period_days']}-day grace period): {sorted(stale_domain_skills)!r} "
        f"(full flagged_stale={result['flagged_stale']!r})",
    )


def test_skill_staleness_check_ok_returns_true_no_warning(recwarn):
    assert skill_staleness_check(True, "unused message") is True
    assert len(recwarn) == 0


def test_skill_staleness_check_warns_not_raises_by_default():
    with pytest.warns(SkillStalenessWarning, match="some-skill flagged stale"):
        result = skill_staleness_check(False, "some-skill flagged stale: detail")
    assert result is False


def test_skill_staleness_check_hard_true_raises():
    with pytest.raises(AssertionError, match="some-skill flagged stale"):
        skill_staleness_check(False, "some-skill flagged stale: detail", hard=True)


def test_zero_invocation_flag_has_derivation(tmp_path):
    result = compute_zero_invocation_skill_flags([], skills_dir=tmp_path)
    assert result["derivation"]
    assert len(result["derivation"]) > 20


def test_generate_without_all_tools_never_computes_zero_invocation_flags(monkeypatch):
    """Direct regression guard for the architecture-review fix (2026-08-15): generate() must
    never reach compute_zero_invocation_skill_flags unless the caller explicitly passed
    all_tools — mirrors the calling convention of the 121+ pre-existing test_generate_retro.py
    calls that pass only tools=/nothing at all."""

    def _boom(*args, **kwargs):
        raise AssertionError("compute_zero_invocation_skill_flags must not be called without all_tools")

    monkeypatch.setattr(generate_retro, "compute_zero_invocation_skill_flags", _boom)

    tools = [_tool_row(run_id="TCK-A", tool="Skill", input_summary="{'skill': 'graphify'}")]
    report = generate([_BASE_RUN], [_ORDINARY_WORKFLOW_EVENT], "test-label", tools=tools)
    assert "### Zero-Invocation Flags" not in report


# ---------------------------------------------------------------------------
# ## KGMCP Cache Efficiency — TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-
# DASHBOARD
# ---------------------------------------------------------------------------

def _kgmcp_row(**overrides):
    row = {
        "cache_level": "level1_provider_result",
        "event_type": "hit",
        "query_hash": "qh1",
        "repo_branch_scope": "repo@main",
        "packet_id": None,
        "run_id": "TCK-KGMCP-FAKE",
        "seq": 1,
        "phase": "Investigate",
        "agent": "investigator",
        "execution_id": "e1",
        "provider": "anthropic",
        "ticket_id": "TCK-KGMCP-FAKE",
        "sidecar_stale": 0,
        "ts": 1000.0,
    }
    row.update(overrides)
    return row


def test_compute_kgmcp_cache_efficiency_metrics_empty_input_returns_no_data_verdict():
    result = compute_kgmcp_cache_efficiency_metrics([], tools=[])
    assert result["total_hits"] == 0
    assert result["total_writes"] == 0
    assert result["overall_reuse_rate"] is None
    assert result["per_ticket"] == {}
    assert result["per_agent"] == {}
    assert result["repeated_refetches"] == []
    assert result["dead_writes"] == []
    assert result["dead_write_count"] == 0
    assert result["coverage"] == {
        "search_calls_total": 0, "cache_events_total": 0, "coverage_rate": None,
    }
    assert result["verdict"] == "NO DATA"


def test_compute_kgmcp_cache_efficiency_metrics_not_in_use_when_search_activity_but_no_cache_events():
    tools = [_tool_row(run_id="TCK-A", tool="mcp__knowledge-search__search_docs")]
    result = compute_kgmcp_cache_efficiency_metrics([], tools=tools)
    assert result["verdict"] == "NOT IN USE"
    assert "1 real" in result["verdict_explanation"]
    assert result["coverage"]["search_calls_total"] == 1
    assert result["coverage"]["cache_events_total"] == 0


def test_compute_kgmcp_cache_efficiency_metrics_computes_hit_write_and_reuse_rate():
    rows = [
        _kgmcp_row(event_type="write", ts=1000.0),
        _kgmcp_row(event_type="hit", ts=1010.0),
        _kgmcp_row(event_type="hit", ts=1020.0),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert result["total_hits"] == 2
    assert result["total_writes"] == 1
    assert result["overall_reuse_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert result["per_ticket"]["TCK-KGMCP-FAKE"] == {
        "hit": 2, "write": 1, "reuse_rate": pytest.approx(2 / 3, abs=1e-4),
    }
    assert result["per_agent"]["investigator"] == {
        "hit": 2, "write": 1, "reuse_rate": pytest.approx(2 / 3, abs=1e-4),
    }
    assert result["verdict"] == "EFFECTIVE"


def test_compute_kgmcp_cache_efficiency_metrics_detects_repeated_refetch_within_window():
    rows = [
        _kgmcp_row(event_type="write", run_id="TCK-A", ticket_id="TCK-A", ts=1000.0),
        _kgmcp_row(event_type="write", run_id="TCK-B", ticket_id="TCK-B", ts=1100.0),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert len(result["repeated_refetches"]) == 1
    rf = result["repeated_refetches"][0]
    assert rf["run_id"] == "TCK-B"
    assert rf["prior_run_id"] == "TCK-A"
    assert rf["gap_s"] == pytest.approx(100.0)


def test_compute_kgmcp_cache_efficiency_metrics_no_repeated_refetch_outside_window():
    rows = [
        _kgmcp_row(event_type="write", run_id="TCK-A", ts=1000.0),
        _kgmcp_row(event_type="write", run_id="TCK-B", ts=1000.0 + generate_retro.KGMCP_REFETCH_WINDOW_SECONDS + 1),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert result["repeated_refetches"] == []


def test_compute_kgmcp_cache_efficiency_metrics_detects_dead_write():
    # A write with no hit before the next write to the same row is a dead write. Both writes here
    # qualify: the first has no hit before the second write, and the second (the row's most recent
    # write) has no hit before the end of the observed log either — see the function's own
    # docstring on why a still-live row's most recent write is flagged too (not a permanent-
    # deadness claim, just "no payoff observed yet").
    rows = [
        _kgmcp_row(event_type="write", run_id="TCK-A", ts=1000.0),
        _kgmcp_row(event_type="write", run_id="TCK-B", ts=5000.0),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert result["dead_write_count"] == 2
    assert {dw["run_id"] for dw in result["dead_writes"]} == {"TCK-A", "TCK-B"}


def test_compute_kgmcp_cache_efficiency_metrics_write_followed_by_hit_is_not_dead():
    rows = [
        _kgmcp_row(event_type="write", run_id="TCK-A", ts=1000.0),
        _kgmcp_row(event_type="hit", run_id="TCK-A", ts=1010.0),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert result["dead_write_count"] == 0


def test_compute_kgmcp_cache_efficiency_metrics_unattributed_bucket_for_missing_ticket_and_agent():
    rows = [_kgmcp_row(event_type="hit", ticket_id=None, agent=None)]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert "unattributed" in result["per_ticket"]
    assert "unattributed" in result["per_agent"]


def test_compute_kgmcp_cache_efficiency_metrics_counts_stale_attribution():
    rows = [
        _kgmcp_row(event_type="hit", sidecar_stale=1),
        _kgmcp_row(event_type="hit", sidecar_stale=0),
    ]
    result = compute_kgmcp_cache_efficiency_metrics(rows, tools=[])
    assert result["stale_attribution_count"] == 1


def test_compute_kgmcp_cache_efficiency_metrics_has_derivation():
    result = compute_kgmcp_cache_efficiency_metrics([], tools=[])
    assert "derivation" in result
    assert len(result["derivation"]) > 20


def test_compute_kgmcp_cache_efficiency_metrics_never_writes_any_file():
    import inspect

    source = inspect.getsource(compute_kgmcp_cache_efficiency_metrics)
    assert "write_lines(" not in source
    assert "write_line(" not in source
    assert '"w")' not in source and "'w')" not in source
    assert "CACHE_DB_PATH" not in source
    assert "_get_connection(" not in source
    assert "_get_access_log_connection(" not in source


def test_compute_retro_metrics_includes_skill_usage_and_kgmcp_when_supplied(tmp_path):
    tools = [_tool_row(run_id="TCK-FAKE", tool="Skill", input_summary="{'skill': 'graphify'}")]
    access_log = [_kgmcp_row(event_type="hit")]
    metrics = compute_retro_metrics(
        [_BASE_RUN], [], tickets_root=tmp_path, tools=tools, kgmcp_access_log=access_log
    )
    assert metrics["skill_usage"]["total_skill_invocations"] == 1
    assert metrics["kgmcp_cache_efficiency"]["total_hits"] == 1


def test_generate_uses_compute_retro_metrics_skill_usage_not_a_second_call(monkeypatch, tmp_path):
    """generate()'s `su` must be read from compute_retro_metrics()'s own `skill_usage` key, not
    computed via a second, independent build_skill_usage_section() call — the property this
    ticket's own Scope item 3 requires ('CLI Markdown report and JSON API stay logically
    consistent'). Verified by making build_skill_usage_section() raise if called a second time
    after compute_retro_metrics() has already computed it."""
    call_count = {"n": 0}
    real = generate_retro.build_skill_usage_section

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(generate_retro, "build_skill_usage_section", _counting)
    tools = [_tool_row(run_id="TCK-FAKE", tool="Skill", input_summary="{'skill': 'graphify'}")]
    generate([_BASE_RUN], [], "test-label", tickets_root=tmp_path, tools=tools)
    assert call_count["n"] == 1


def test_generate_kgmcp_section_always_renders_even_when_empty(tmp_path):
    report = generate([_BASE_RUN], [], "test-label", tickets_root=tmp_path, tools=[], kgmcp_access_log=[])
    assert "## KGMCP Cache Efficiency" in report
    assert "Cache Efficiency: NO DATA" in report


def test_generate_kgmcp_section_renders_real_verdict_and_table(tmp_path):
    access_log = [
        _kgmcp_row(event_type="write", ts=1000.0),
        _kgmcp_row(event_type="hit", ts=1010.0),
    ]
    report = generate(
        [_BASE_RUN], [], "test-label", tickets_root=tmp_path, tools=[], kgmcp_access_log=access_log
    )
    assert "## KGMCP Cache Efficiency" in report
    assert "Cache Efficiency: EFFECTIVE" in report
    assert "| Total hits | 1 |" in report
    assert "| Total writes | 1 |" in report
