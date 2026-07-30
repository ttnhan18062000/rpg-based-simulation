"""Targeted tests for tools/agent-monitoring/generate_retro.py's reason-code section
(TCK-20260706-MONITORING-REASON-CODE, extended by TCK-20260706-SCOPE-TAG-REGISTRY-CHECK and
TCK-20260706-CREATE-TICKETS-TAG-CHECK), its Subsystem/Topic + Process/Skill-signal tag
breakdown sections (TCK-20260708-RETRO-TAG-BREAKDOWN), and (TCK-20260718-RETRO-STATS-REFACTOR)
the extracted compute_retro_metrics() computation function. Not full coverage of the pre-existing
script (which had no test file before the first of these tickets) — scoped to the behavior these
tickets changed.
"""

import sys
from pathlib import Path

import pytest

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import generate_retro  # noqa: E402
from generate_retro import (  # noqa: E402
    compute_retro_metrics,
    compute_retrieval_metrics,
    compute_shadow_baseline_comparison,
    generate,
    _record_since_cutoff,
    _resolve_status,
    _is_legacy_event,
    _is_gate_fail,
)


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


def test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope():
    import inspect

    source = inspect.getsource(generate_retro._update_index)
    assert "load_jsonl(RUNS_FILE)" not in source

    sig = inspect.signature(generate_retro._update_index)
    assert list(sig.parameters) == ["all_runs"]


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
