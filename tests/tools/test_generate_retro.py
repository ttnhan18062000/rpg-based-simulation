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

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from generate_retro import compute_retro_metrics, generate  # noqa: E402

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
    """Write a fixture docs/guidelines/tag_registry.jsonl under root with `entries`, a list of
    (tag, category) tuples."""
    import json as _json

    registry_dir = root / "docs" / "guidelines"
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
        "agent_status_distribution", "spend_proxy_by_phase", "spend_proxy_by_agent",
        "summary_quality", "slow_runs",
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
