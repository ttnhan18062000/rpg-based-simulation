"""Tests for tools/agent-monitoring/epic_staleness_check.py,
TCK-20260710-EPIC-STALENESS-CHECK.

Mirrors test_validate_agent_monitoring.py's import style (sys.path insert into
tools/agent-monitoring, then plain module import — no package boundary).

Per Decision 5 (staging_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/plan.md):
an epic whose children have zero activity ever is never flagged stale — it is
"never started" (informational only). Only an epic with at least one child
showing real activity evidence, followed by silence past the window, is
flagged stale. TCK-20260702-OBSISO-EPIC was originally the repo's real live
proof of the never-started case, but its folder (tickets/todos/obs-isolation)
completed and moved to tickets/done/obs-isolation/ per the standard Finalize
convention — no live repo path is genuinely "zero child activity ever" as of
2026-08-17 (TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP investigation:
the only other tickets/todos/ folder, codex-runtime-activation/, has real,
non-zero child activity and would itself be flagged stale). The never-started
case is therefore proven via a synthetic tmp_path fixture instead.
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from epic_staleness_check import (  # noqa: E402
    DEFAULT_STALENESS_WINDOW_DAYS,
    EpicCandidate,
    compute_stale_epics_report,
    discover_candidate_epics,
    find_stale_epics,
    is_epic_blocked,
    is_epic_never_started,
    is_epic_stale,
    resolve_child_activity,
)

NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)


def _write_ticket(path: Path, ticket_id: str, tier: str, date_str: str, related_tickets: str = "", body_status: str = ""):
    status_section = f"## Status\n{body_status}\n\n" if body_status else ""
    path.write_text(
        f"---\n"
        f"status: active\n"
        f"layer: ai\n"
        f"ticket_id: {ticket_id}\n"
        f"date: {date_str}\n"
        f"---\n\n"
        f"# {ticket_id}\n\n"
        f"{status_section}"
        f"## Tier\n{tier}\n\n"
        f"## Related Tickets\n{related_tickets}\n"
    )


# ---------------------------------------------------------------------------
# 1. Synthetic end-to-end integration — never-started folder epic, not stale
#
# Replaces the original real-repo-backed test_does_not_flag_never_started_
# real_obsiso_epic (TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP): the
# real tickets/todos/obs-isolation fixture completed and moved to
# tickets/done/, so no live repo path is genuinely "zero child activity ever"
# any more. This synthetic tmp_path fixture exercises the same full
# find_stale_epics/compute_stale_epics_report real-file-reading pipeline
# (not just is_epic_stale()/is_epic_never_started() directly, which
# test_does_not_flag_never_started_epic below already covers at the unit
# level) against a controlled folder-mode epic with zero rows for its child
# ID in a synthetic working_log.csv and an empty runs.jsonl.
# ---------------------------------------------------------------------------

def _write_synthetic_never_started_folder_epic(todos_dir: Path) -> Path:
    folder = todos_dir / "synthetic-never-started-epic"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text(
        "Epic: `TCK-20260701-SYNTH-NEVER-STARTED-EPIC`.\n\n"
        "| Order | Ticket |\n|---|---|\n"
        "| 1 | TCK-20260701-SYNTH-NEVER-STARTED-CHILD |\n"
    )
    _write_ticket(
        folder / "TCK-20260701-SYNTH-NEVER-STARTED-EPIC.md",
        "TCK-20260701-SYNTH-NEVER-STARTED-EPIC", "epic", "2026-07-01",
    )
    return folder


def test_does_not_flag_never_started_synthetic_folder_epic(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_synthetic_never_started_folder_epic(todos_dir)
    # Zero rows for the child ID anywhere — real, zero activity ever.
    working_log_path.write_text("timestamp,ticket_id,title,status,summary,artifacts_path\n")
    runs_jsonl_path.write_text("")

    stale = find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" not in [c.epic_id for c in stale]

    report = compute_stale_epics_report(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW
    )
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" not in report.split("Informational:")[0]
    assert "TCK-20260701-SYNTH-NEVER-STARTED-EPIC" in report.split("Informational:")[1]


# ---------------------------------------------------------------------------
# 2. Synthetic non-stale control — recent activity within the window
# ---------------------------------------------------------------------------

def test_does_not_flag_recently_active_epic(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260701-RECENT-EPIC.md",
        "TCK-20260701-RECENT-EPIC",
        "epic",
        "2026-07-01",
        related_tickets="TCK-20260701-RECENT-CHILD",
    )

    candidate = discover_candidate_epics(inprogress_dir, todos_dir)[0]
    working_log_rows = [{"ticket_id": "TCK-20260701-RECENT-CHILD", "timestamp": "2026-07-09T00:00:00Z"}]
    most_recent = resolve_child_activity(candidate.child_ids, working_log_rows, [])

    assert is_epic_stale(candidate, most_recent, NOW) is False


# ---------------------------------------------------------------------------
# 3. Discovery correctly distinguishes epic-tier from regular tickets
# ---------------------------------------------------------------------------

def test_identifies_epic_tickets_vs_regular_tickets(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(inprogress_dir / "TCK-20260701-STD.md", "TCK-20260701-STD", "standard", "2026-07-01")
    _write_ticket(inprogress_dir / "TCK-20260701-HOT.md", "TCK-20260701-HOT", "hotfix", "2026-07-01")
    _write_ticket(
        inprogress_dir / "TCK-20260701-REAL-EPIC.md",
        "TCK-20260701-REAL-EPIC",
        "epic",
        "2026-07-01",
        related_tickets="TCK-20260701-CHILD-A, TCK-20260701-CHILD-B",
    )

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    assert candidates[0].epic_id == "TCK-20260701-REAL-EPIC"
    assert candidates[0].child_ids == ["TCK-20260701-CHILD-A", "TCK-20260701-CHILD-B"]


# ---------------------------------------------------------------------------
# 4. Hybrid folder shape (both SEQUENCE.md and an epic-tier ticket file)
# ---------------------------------------------------------------------------

def test_handles_hybrid_folder_shape(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    folder = todos_dir / "my-hybrid-epic"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text(
        "Epic: `TCK-20260701-HYBRID-EPIC`.\n\n"
        "| Order | Ticket |\n|---|---|\n"
        "| 1 | TCK-20260701-HYBRID-A |\n"
        "| 2 | TCK-20260701-HYBRID-B |\n"
    )
    _write_ticket(folder / "TCK-20260701-HYBRID-EPIC.md", "TCK-20260701-HYBRID-EPIC", "epic", "2026-07-01")
    (folder / "TCK-20260701-HYBRID-A.md").write_text("child ticket A")
    (folder / "TCK-20260701-HYBRID-B.md").write_text("child ticket B")

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.mode == "folder"
    assert candidate.epic_id == "TCK-20260701-HYBRID-EPIC"
    assert candidate.child_ids == ["TCK-20260701-HYBRID-A", "TCK-20260701-HYBRID-B"]


# ---------------------------------------------------------------------------
# 5. Missing/malformed SEQUENCE.md does not crash and is not flagged stale
# ---------------------------------------------------------------------------

def test_handles_missing_or_malformed_sequence_md(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    # Folder with an epic ticket, empty SEQUENCE.md, and no sibling children yet.
    folder = todos_dir / "brand-new-epic"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text("")
    _write_ticket(folder / "TCK-20260701-NEW-EPIC.md", "TCK-20260701-NEW-EPIC", "epic", "2026-07-01")

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.child_ids == []
    assert is_epic_stale(candidate, None, NOW) is False

    # Folder with no SEQUENCE.md and no epic ticket at all — not a candidate.
    non_epic_folder = todos_dir / "not-an-epic"
    non_epic_folder.mkdir()
    (non_epic_folder / "TCK-20260701-REGULAR.md").write_text("some regular ticket, no epic tier")
    candidates_2 = discover_candidate_epics(inprogress_dir, todos_dir)
    assert non_epic_folder.name not in [c.source_path.name for c in candidates_2]


# ---------------------------------------------------------------------------
# 6. All-children-stale — real, but now-old, activity past the window
# ---------------------------------------------------------------------------

def test_epic_with_all_children_stale(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260601-OLD-EPIC.md",
        "TCK-20260601-OLD-EPIC",
        "epic",
        "2026-06-01",
        related_tickets="TCK-20260601-OLD-CHILD",
    )

    candidate = discover_candidate_epics(inprogress_dir, todos_dir)[0]
    # 8-day gap between the child's last activity and NOW, modeled on the real
    # OBSISO folder-date-to-today span (investigation.md).
    working_log_rows = [{"ticket_id": "TCK-20260601-OLD-CHILD", "timestamp": "2026-07-02T00:00:00Z"}]
    most_recent = resolve_child_activity(candidate.child_ids, working_log_rows, [])

    assert most_recent is not None
    assert is_epic_stale(candidate, most_recent, NOW) is True
    assert is_epic_never_started(candidate, most_recent) is False


# ---------------------------------------------------------------------------
# 7. Never-started — zero activity ever, regardless of epic_date's age
# ---------------------------------------------------------------------------

def test_does_not_flag_never_started_epic(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260610-STALE-LOOKING-EPIC.md",
        "TCK-20260610-STALE-LOOKING-EPIC",
        "epic",
        "2026-06-10",  # 30 days before NOW — old age alone must not trigger a flag
        related_tickets="TCK-20260610-NEVER-TOUCHED-CHILD",
    )

    candidate = discover_candidate_epics(inprogress_dir, todos_dir)[0]
    most_recent = resolve_child_activity(candidate.child_ids, [], [])

    assert most_recent is None
    assert is_epic_stale(candidate, most_recent, NOW) is False
    assert is_epic_never_started(candidate, most_recent) is True


# ---------------------------------------------------------------------------
# 8. Advisory-only — never mutates any ticket file's bytes
# ---------------------------------------------------------------------------

def _hash_dir(directory: Path) -> dict:
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir()) if p.is_file()}


def test_advisory_only_no_file_mutation_synthetic(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    folder = _write_synthetic_never_started_folder_epic(todos_dir)
    working_log_path.write_text("timestamp,ticket_id,title,status,summary,artifacts_path\n")
    runs_jsonl_path.write_text("")

    before = _hash_dir(folder)
    compute_stale_epics_report(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    after = _hash_dir(folder)

    assert before == after


def test_advisory_only_never_raises_on_missing_files(tmp_path):
    missing_dir = tmp_path / "does-not-exist"
    report = compute_stale_epics_report(
        missing_dir / "inprogress", missing_dir / "todos",
        missing_dir / "working_log.csv", missing_dir / "runs.jsonl",
    )
    assert isinstance(report, str)
    stale = find_stale_epics(
        missing_dir / "inprogress", missing_dir / "todos",
        missing_dir / "working_log.csv", missing_dir / "runs.jsonl",
    )
    assert stale == []


# ---------------------------------------------------------------------------
# 9. csv.DictReader field-name access, not column-position parsing
# ---------------------------------------------------------------------------

def test_working_log_dictreader_not_column_index():
    child_ids = ["TCK-20260601-DICTREADER-CHILD"]

    # A canonical-shaped row plus a non-canonical row with an extra unescaped
    # comma inflating the raw column count — csv.DictReader still resolves
    # "ticket_id" and "timestamp" by field name regardless of row shape.
    working_log_rows = [
        {
            "timestamp": "2026-06-01T00:00:00Z",
            "ticket_id": "TCK-20260601-DICTREADER-CHILD",
            "title": "some, title, with, extra, commas",
            "status": "DONE",
            "summary": "s",
            "artifacts_path": "none",
        },
        {
            "timestamp": "2026-06-05T00:00:00Z",
            "ticket_id": "TCK-20260601-DICTREADER-CHILD",
            "title": "t",
            "status": "DONE",
            "summary": "s",
            "artifacts_path": "none",
            None: ["extra", "unnamed", "fields", "from", "a", "malformed", "row"],
        },
    ]

    most_recent = resolve_child_activity(child_ids, working_log_rows, [])

    assert most_recent == datetime(2026, 6, 5, 0, 0, 0, tzinfo=timezone.utc)


def test_working_log_row_missing_ticket_id_key_does_not_raise():
    child_ids = ["TCK-20260601-SOME-CHILD"]
    working_log_rows = [{"timestamp": "2026-06-01T00:00:00Z"}]  # no ticket_id key at all

    most_recent = resolve_child_activity(child_ids, working_log_rows, [])

    assert most_recent is None


# ---------------------------------------------------------------------------
# 10. Dual-presence dedupe — same epic_id in both inprogress/ and todos/{folder}/
# ---------------------------------------------------------------------------

def _write_dual_presence_fixture(inprogress_dir: Path, todos_dir: Path, ticket_id: str):
    _write_ticket(
        inprogress_dir / f"{ticket_id}.md",
        ticket_id,
        "epic",
        "2026-07-01",
        related_tickets="TCK-20260701-DUAL-PRESENCE-CHILD",
    )
    folder = todos_dir / "dual-presence-folder"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text(
        f"Epic: `{ticket_id}`.\n\n"
        "| Order | Ticket |\n|---|---|\n"
        "| 1 | TCK-20260701-DUAL-PRESENCE-CHILD |\n"
    )
    _write_ticket(folder / f"{ticket_id}.md", ticket_id, "epic", "2026-07-01")


def test_discover_candidate_epics_dedupes_dual_presence(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()
    ticket_id = "TCK-20260701-DUAL-PRESENCE-EPIC"

    _write_dual_presence_fixture(inprogress_dir, todos_dir, ticket_id)

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    assert candidates[0].epic_id == ticket_id


def test_dual_presence_not_double_reported_in_stale_list(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()
    ticket_id = "TCK-20260701-DUAL-PRESENCE-EPIC"

    _write_dual_presence_fixture(inprogress_dir, todos_dir, ticket_id)

    # 8-day gap between the child's last activity and NOW, past the staleness
    # window, mirroring test_epic_with_all_children_stale's pattern.
    working_log_path.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-02T00:00:00Z,TCK-20260701-DUAL-PRESENCE-CHILD,t,DONE,s,none\n"
    )
    runs_jsonl_path.write_text("")

    stale = find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    assert [c.epic_id for c in stale].count(ticket_id) == 1

    report = compute_stale_epics_report(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    stale_section = report.split("Informational:")[0]
    matching_lines = [line for line in stale_section.splitlines() if ticket_id in line]
    assert len(matching_lines) == 1


def test_dual_presence_prefers_inprogress_candidate(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()
    ticket_id = "TCK-20260701-DUAL-PRESENCE-EPIC"

    _write_dual_presence_fixture(inprogress_dir, todos_dir, ticket_id)

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    survivor = candidates[0]
    assert survivor.mode == "epic_id"
    assert survivor.source_path.parent == inprogress_dir


# ---------------------------------------------------------------------------
# 11. BLOCKED status awareness (TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC)
#
# Modeled on the real false-positive case study, TCK-20260730-CODEX-RUNTIME-
# ACTIVATION-EPIC: an epic ticket whose body `## Status` reads `BLOCKED`,
# with real child activity that has since gone idle past the window. This
# must never reach find_stale_epics()'s return (the hook fire-trigger), and
# must instead surface in compute_stale_epics_report()'s new, separate
# "Informational: BLOCKED epics" section — never silently dropped.
# ---------------------------------------------------------------------------

def test_blocked_epic_with_stale_looking_activity_is_never_in_find_stale_epics(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260601-BLOCKED-EPIC.md",
        "TCK-20260601-BLOCKED-EPIC",
        "epic",
        "2026-06-01",
        related_tickets="TCK-20260601-BLOCKED-CHILD",
        body_status="BLOCKED",
    )
    # Same 8-day-idle shape as test_epic_with_all_children_stale — proves the
    # BLOCKED guard suppresses the flag despite genuinely idle child activity,
    # not because the activity itself is missing or recent.
    working_log_path.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-02T00:00:00Z,TCK-20260601-BLOCKED-CHILD,t,DONE,s,none\n"
    )
    runs_jsonl_path.write_text("")

    stale = find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    assert "TCK-20260601-BLOCKED-EPIC" not in [c.epic_id for c in stale]

    report = compute_stale_epics_report(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW
    )
    stale_section, rest = report.split("Informational: never-started epics")
    assert "TCK-20260601-BLOCKED-EPIC" not in stale_section
    blocked_section = rest.split("Informational: BLOCKED epics")[1]
    assert "TCK-20260601-BLOCKED-EPIC" in blocked_section
    assert "8 days idle" in blocked_section


def test_blocked_epic_does_not_land_in_never_started_bucket(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260601-BLOCKED-NO-ACTIVITY-EPIC.md",
        "TCK-20260601-BLOCKED-NO-ACTIVITY-EPIC",
        "epic",
        "2026-06-01",
        related_tickets="TCK-20260601-BLOCKED-NO-ACTIVITY-CHILD",
        body_status="BLOCKED",
    )
    working_log_path.write_text("timestamp,ticket_id,title,status,summary,artifacts_path\n")
    runs_jsonl_path.write_text("")

    report = compute_stale_epics_report(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW
    )
    never_started_section, blocked_section = report.split("Informational: BLOCKED epics")
    assert "TCK-20260601-BLOCKED-NO-ACTIVITY-EPIC" not in never_started_section
    assert "TCK-20260601-BLOCKED-NO-ACTIVITY-EPIC" in blocked_section
    assert "no child activity recorded" in blocked_section


def test_genuinely_stale_non_blocked_epic_still_flagged_regression_guard(tmp_path):
    """Acceptance-critical: the BLOCKED fix must not weaken real staleness
    detection for epics that are simply idle, not deliberately parked."""
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    _write_ticket(
        inprogress_dir / "TCK-20260601-STILL-STALE-EPIC.md",
        "TCK-20260601-STILL-STALE-EPIC",
        "epic",
        "2026-06-01",
        related_tickets="TCK-20260601-STILL-STALE-CHILD",
        body_status="INPROGRESS",
    )
    working_log_path.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-02T00:00:00Z,TCK-20260601-STILL-STALE-CHILD,t,DONE,s,none\n"
    )
    runs_jsonl_path.write_text("")

    stale = find_stale_epics(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=NOW)
    assert "TCK-20260601-STILL-STALE-EPIC" in [c.epic_id for c in stale]


def test_is_epic_blocked_reads_status_field():
    blocked = EpicCandidate(
        epic_id="TCK-X", source_path=Path("."), mode="epic_id", child_ids=[], status="BLOCKED"
    )
    open_status = EpicCandidate(
        epic_id="TCK-Y", source_path=Path("."), mode="epic_id", child_ids=[], status="OPEN"
    )
    unknown_status = EpicCandidate(
        epic_id="TCK-Z", source_path=Path("."), mode="epic_id", child_ids=[], status=None
    )
    assert is_epic_blocked(blocked) is True
    assert is_epic_blocked(open_status) is False
    assert is_epic_blocked(unknown_status) is False


def test_folder_mode_no_epic_ticket_file_leaves_status_none_not_crash(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    folder = todos_dir / "sequence-only-epic"
    folder.mkdir()
    (folder / "SEQUENCE.md").write_text(
        "Epic: `FOLDER-tickets-todos-sequence-only-epic`.\n\n"
        "| Order | Ticket |\n|---|---|\n"
        "| 1 | TCK-20260701-SEQ-ONLY-CHILD |\n"
    )

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)

    assert len(candidates) == 1
    assert candidates[0].status is None
    assert is_epic_blocked(candidates[0]) is False


def test_real_codex_runtime_activation_epic_is_status_aware(tmp_path):
    """Integration-style confirmation against the real repo ticket that
    motivated this fix, TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC — read-only,
    copies the real file into a synthetic inprogress_dir rather than pointing
    the check at the live tickets/ tree (which would be sensitive to
    unrelated repo state changing over time)."""
    real_ticket_path = (
        Path(__file__).parent.parent.parent
        / "tickets" / "inprogress" / "TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC.md"
    )
    if not real_ticket_path.exists():
        return

    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    working_log_path = tmp_path / "working_log.csv"
    runs_jsonl_path = tmp_path / "runs.jsonl"
    inprogress_dir.mkdir()
    todos_dir.mkdir()

    (inprogress_dir / real_ticket_path.name).write_text(real_ticket_path.read_text())
    # Old activity for one of the epic's real children, past the 5-day window,
    # to reproduce the exact false-positive shape this ticket was filed against.
    working_log_path.write_text(
        "timestamp,ticket_id,title,status,summary,artifacts_path\n"
        "2026-07-31T00:00:00Z,TCK-20260730-CLAUDE-EXECUTION-IDENTITY,t,DONE,s,none\n"
    )
    runs_jsonl_path.write_text("")

    # The real ticket is dated 2026-07-30; use a "now" after both that date
    # and the synthetic child activity above, so the idle gap is genuine
    # rather than an artifact of NOW predating the fixture's own dates.
    integration_now = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)

    candidates = discover_candidate_epics(inprogress_dir, todos_dir)
    epic = next(c for c in candidates if c.epic_id == "TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC")
    assert epic.status == "BLOCKED"
    assert is_epic_blocked(epic) is True

    stale = find_stale_epics(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=integration_now
    )
    assert "TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC" not in [c.epic_id for c in stale]

    report = compute_stale_epics_report(
        inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now=integration_now
    )
    blocked_section = report.split("Informational: BLOCKED epics")[1]
    assert "TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC" in blocked_section
