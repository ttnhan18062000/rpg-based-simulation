"""Tests for tools/ticket_stats_report.py (TCK-20260718-TICKET-CORPUS-REPORT).

Mirrors tools/tag_report.py's own test conventions where applicable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from ticket_stats_report import (  # noqa: E402
    collect_done_tickets,
    compute_artifact_completeness,
    compute_distribution,
    compute_velocity,
    build_json_report,
)


def _write_ticket(root: Path, ticket_id: str, *, layer="engine", tier="standard",
                   ticket_type="feature", priority="P1", date="2026-07-10") -> Path:
    tickets_dir = root / "tickets" / "done"
    tickets_dir.mkdir(parents=True, exist_ok=True)
    p = tickets_dir / f"{ticket_id}.md"
    p.write_text(
        f"---\nstatus: historical\nlayer: {layer}\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: done\ndate: {date}\ntags: []\n---\n\n"
        f"# {ticket_id}\n\n## Tier\n{tier}\n\n## Type\n{ticket_type}\n\n"
        f"## Priority\n{priority}\n\n## Status\nDONE\n",
        encoding="utf-8",
    )
    return p


def test_collect_done_tickets_extracts_layer_tier_type_priority(tmp_path):
    _write_ticket(tmp_path, "TCK-20260710-FAKE-ONE", layer="economy", tier="hotfix", priority="P0")

    included, skip_reasons = collect_done_tickets(tmp_path)

    assert len(included) == 1
    row = included[0]
    assert row["layer"] == "economy"
    assert row["tier"] == "hotfix"
    assert row["priority"] == "P0"


def test_collect_done_tickets_skips_sequence_md(tmp_path):
    _write_ticket(tmp_path, "TCK-20260710-FAKE-ONE")
    (tmp_path / "tickets" / "done" / "SEQUENCE.md").write_text("# Sequence\n", encoding="utf-8")

    included, skip_reasons = collect_done_tickets(tmp_path)

    assert len(included) == 1
    assert skip_reasons["sequence_index_file"] == 1


def test_compute_velocity_groups_by_day_and_week(tmp_path):
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    log = tmp_path / "tickets" / "working_log.csv"
    log.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-06T00:00:00Z,TCK-A,A,DONE,x,none\n"
        "2026-07-06T01:00:00Z,TCK-B,B,DONE,x,none\n"
        "2026-07-07T00:00:00Z,TCK-C,C,DONE,x,none\n",
        encoding="utf-8",
    )

    velocity = compute_velocity(tmp_path)

    assert velocity["by_day"]["2026-07-06"] == 2
    assert velocity["by_day"]["2026-07-07"] == 1
    assert velocity["unparseable_rows"] == 0


def test_compute_velocity_counts_unparseable_rows_without_crashing(tmp_path):
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    log = tmp_path / "tickets" / "working_log.csv"
    log.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        ",TCK-A,A,DONE,x,none\n"
        "not-a-timestamp,TCK-B,B,DONE,x,none\n",
        encoding="utf-8",
    )

    velocity = compute_velocity(tmp_path)

    assert velocity["unparseable_rows"] == 2
    assert velocity["by_day"] == {}


def test_compute_distribution_counts_unknown_for_missing_fields(tmp_path):
    included = [
        {"ticket_id": "A", "layer": "engine", "tier": "standard", "ticket_type": "feature", "priority": "P1", "date": "2026-07-10"},
        {"ticket_id": "B", "layer": None, "tier": None, "ticket_type": None, "priority": None, "date": "2026-07-10"},
    ]

    dist = compute_distribution(included)

    assert dist["tier"] == {"standard": 1, "unknown": 1}
    assert dist["layer"] == {"engine": 1, "unknown": 1}
    assert dist["layer_by_tier"]["engine"]["standard"] == 1


def test_compute_artifact_completeness_detects_missing_files(tmp_path):
    included = [
        {"ticket_id": "TCK-COMPLETE", "layer": "engine", "tier": "standard", "ticket_type": "feature", "priority": "P1", "date": "2026-07-10"},
        {"ticket_id": "TCK-INCOMPLETE", "layer": "engine", "tier": "standard", "ticket_type": "feature", "priority": "P1", "date": "2026-07-10"},
        {"ticket_id": "TCK-HOTFIX", "layer": "engine", "tier": "hotfix", "ticket_type": "bug", "priority": "P1", "date": "2026-07-10"},
    ]
    complete_dir = tmp_path / "stored_artifacts" / "TCK-COMPLETE"
    complete_dir.mkdir(parents=True)
    for fname in ("investigation.md", "plan.md", "test_plan.md"):
        (complete_dir / fname).write_text("content", encoding="utf-8")

    incomplete_dir = tmp_path / "stored_artifacts" / "TCK-INCOMPLETE"
    incomplete_dir.mkdir(parents=True)
    (incomplete_dir / "investigation.md").write_text("content", encoding="utf-8")
    # plan.md, test_plan.md missing entirely

    result = compute_artifact_completeness(included, tmp_path)

    assert result["complete_count"] == 1
    assert result["incomplete_count"] == 1
    # hotfix ticket excluded from the check entirely
    assert result["total_checked"] == 2
    assert result["incomplete"][0]["ticket_id"] == "TCK-INCOMPLETE"
    assert set(result["incomplete"][0]["missing"]) == {"plan.md", "test_plan.md"}


def test_build_json_report_is_json_serializable(tmp_path):
    _write_ticket(tmp_path, "TCK-20260710-FAKE-ONE")
    included, skip_reasons = collect_done_tickets(tmp_path)
    velocity = compute_velocity(tmp_path)
    distribution = compute_distribution(included)
    artifact_completeness = compute_artifact_completeness(included, tmp_path)

    report = build_json_report(included, skip_reasons, velocity, distribution, artifact_completeness)

    # Must not raise — proves no Counter/set/other non-JSON-native type leaked into the report.
    json.dumps(report)


def test_uses_canonical_enums_not_reimplemented():
    """Source-text anti-drift guard: must import TIER_VALUES/PRIORITY_VALUES/layer_values,
    never redefine its own copy."""
    source = Path("tools/ticket_stats_report.py").read_text(encoding="utf-8")
    assert "from ticket_field_values import TIER_VALUES, PRIORITY_VALUES" in source
    assert "from layer_registry import layer_values" in source
