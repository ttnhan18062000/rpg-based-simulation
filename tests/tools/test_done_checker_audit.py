"""Smoke tests for tools/gate_checks/done_checker_audit.py (TCK-20260705-GATE-DET-DONE-CHECKER Part C).

Per the ticket's explicit, permanent scope guard: legacy tickets with no parseable `## Tier` field
must be skipped/warned, never classified or crashed on, and must never appear in the missing/
incomplete counts. This file only asserts "does not crash, does not appear in gap counts" for that
class — not "correctly classifies" (there is nothing to classify; the field doesn't exist).
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.done_checker_audit import (  # noqa: E402
    audit_stored_artifacts_migration,
    scan_done_tickets,
)

ARTIFACT_FM = """---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: {ticket_id}
artifact_type: {artifact_type}
tags: []
---

Some content.
"""


def _write_ticket_with_tier(path: Path, ticket_id: str, tier: str) -> None:
    path.write_text(
        f"""---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: {ticket_id}
phase: done
date: 2026-07-05
tags: []
---

# {ticket_id}

## Title
Fixture ticket

## Tier
{tier}
""",
        encoding="utf-8",
    )


def _write_legacy_ticket_no_tier(path: Path, ticket_id: str) -> None:
    # Pre-frontmatter-era legacy ticket shape: no frontmatter, no ## Tier section at all.
    path.write_text(f"# {ticket_id}\n\nSome legacy prose with no structured fields.\n", encoding="utf-8")


def _write_complete_stored_artifacts(stored_base: Path, ticket_id: str) -> None:
    directory = stored_base / ticket_id
    directory.mkdir(parents=True)
    for name, artifact_type in (("plan.md", "plan"), ("investigation.md", "investigation"), ("test_plan.md", "test_plan")):
        (directory / name).write_text(ARTIFACT_FM.format(ticket_id=ticket_id, artifact_type=artifact_type), encoding="utf-8")


def _scaffold(tmp_path):
    done_dir = tmp_path / "tickets" / "done"
    done_dir.mkdir(parents=True)
    stored_base = tmp_path / "stored_artifacts"

    _write_ticket_with_tier(done_dir / "TCK-OK.md", "TCK-OK", "standard")
    _write_complete_stored_artifacts(stored_base, "TCK-OK")

    _write_ticket_with_tier(done_dir / "TCK-INCOMPLETE.md", "TCK-INCOMPLETE", "standard")
    incomplete_dir = stored_base / "TCK-INCOMPLETE"
    incomplete_dir.mkdir(parents=True)
    (incomplete_dir / "investigation.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-INCOMPLETE", artifact_type="investigation"), encoding="utf-8"
    )
    (incomplete_dir / "test_plan.md").write_text(
        ARTIFACT_FM.format(ticket_id="TCK-INCOMPLETE", artifact_type="test_plan"), encoding="utf-8"
    )
    # plan.md intentionally missing

    _write_ticket_with_tier(done_dir / "TCK-MISSING.md", "TCK-MISSING", "standard")
    # no stored_artifacts/TCK-MISSING/ at all

    _write_ticket_with_tier(done_dir / "TCK-HOTFIX.md", "TCK-HOTFIX", "hotfix")
    # no stored_artifacts/TCK-HOTFIX/ — correct, not expected

    _write_legacy_ticket_no_tier(done_dir / "METRICS-01.md", "METRICS-01")

    return done_dir, stored_base


def test_scan_done_tickets_extracts_tier_and_marks_legacy_none(tmp_path):
    done_dir, _ = _scaffold(tmp_path)

    entries = scan_done_tickets(done_dir)
    by_id = {e["ticket_id"]: e for e in entries}

    assert by_id["TCK-OK"]["tier"] == "standard"
    assert by_id["TCK-HOTFIX"]["tier"] == "hotfix"
    assert by_id["METRICS-01"]["tier"] is None


def test_scan_done_tickets_excludes_readme_and_sequence(tmp_path):
    done_dir, _ = _scaffold(tmp_path)
    (done_dir / "README.md").write_text("# readme", encoding="utf-8")
    (done_dir / "SEQUENCE.md").write_text("# sequence", encoding="utf-8")

    entries = scan_done_tickets(done_dir)
    ids = {e["ticket_id"] for e in entries}
    assert "README" not in ids
    assert "SEQUENCE" not in ids


def test_audit_classifies_ok_missing_incomplete_correctly(tmp_path):
    done_dir, stored_base = _scaffold(tmp_path)

    summary = audit_stored_artifacts_migration(done_dir=done_dir, stored_base=stored_base)

    assert "TCK-OK" in summary["ok"]
    assert "TCK-MISSING" in summary["missing"]
    assert "TCK-INCOMPLETE" in summary["incomplete"]
    assert "plan.md" in summary["incomplete"]["TCK-INCOMPLETE"]


def test_audit_skips_hotfix_not_counted_as_gap(tmp_path):
    done_dir, stored_base = _scaffold(tmp_path)

    summary = audit_stored_artifacts_migration(done_dir=done_dir, stored_base=stored_base)

    assert "TCK-HOTFIX" not in summary["missing"]
    assert "TCK-HOTFIX" not in summary["incomplete"]
    assert summary["hotfix_skipped"] == 1


def test_audit_skips_legacy_ticket_warns_and_never_appears_in_gap_counts(tmp_path, capsys):
    done_dir, stored_base = _scaffold(tmp_path)

    summary = audit_stored_artifacts_migration(done_dir=done_dir, stored_base=stored_base)

    assert "METRICS-01" not in summary["missing"]
    assert "METRICS-01" not in summary["incomplete"]
    assert "METRICS-01" not in summary["ok"]
    assert summary["legacy_skipped"] == 1

    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "METRICS-01" in captured.out


def test_audit_does_not_raise_on_legacy_ticket(tmp_path):
    done_dir, stored_base = _scaffold(tmp_path)

    # Must not raise — this is the core "does not crash" requirement for legacy tickets.
    audit_stored_artifacts_migration(done_dir=done_dir, stored_base=stored_base)
