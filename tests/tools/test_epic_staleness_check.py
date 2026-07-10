"""Tests for tools/agent-monitoring/epic_staleness_check.py,
TCK-20260710-EPIC-STALENESS-CHECK.

Mirrors test_validate_agent_monitoring.py's import style (sys.path insert into
tools/agent-monitoring, then plain module import — no package boundary).

Per Decision 5 (staging_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/plan.md):
an epic whose children have zero activity ever is never flagged stale — it is
"never started" (informational only). Only an epic with at least one child
showing real activity evidence, followed by silence past the window, is
flagged stale. TCK-20260702-OBSISO-EPIC is the repo's real live proof of the
never-started case, not a stale case.
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
    is_epic_never_started,
    is_epic_stale,
    resolve_child_activity,
)

REAL_INPROGRESS_DIR = Path(__file__).parent.parent.parent / "tickets" / "inprogress"
REAL_TODOS_DIR = Path(__file__).parent.parent.parent / "tickets" / "todos"
REAL_WORKING_LOG = Path(__file__).parent.parent.parent / "tickets" / "working_log.csv"
REAL_RUNS_JSONL = Path(__file__).parent.parent.parent / "agent-monitoring" / "runs.jsonl"
REAL_OBSISO_DIR = REAL_TODOS_DIR / "obs-isolation"

NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)


def _write_ticket(path: Path, ticket_id: str, tier: str, date_str: str, related_tickets: str = ""):
    path.write_text(
        f"---\n"
        f"status: active\n"
        f"layer: ai\n"
        f"ticket_id: {ticket_id}\n"
        f"date: {date_str}\n"
        f"---\n\n"
        f"# {ticket_id}\n\n"
        f"## Tier\n{tier}\n\n"
        f"## Related Tickets\n{related_tickets}\n"
    )


# ---------------------------------------------------------------------------
# 1. Real-data integration — TCK-20260702-OBSISO-EPIC never-started, not stale
# ---------------------------------------------------------------------------

def test_does_not_flag_never_started_real_obsiso_epic():
    stale = find_stale_epics(REAL_INPROGRESS_DIR, REAL_TODOS_DIR, REAL_WORKING_LOG, REAL_RUNS_JSONL)
    assert "TCK-20260702-OBSISO-EPIC" not in [c.epic_id for c in stale]

    report = compute_stale_epics_report(REAL_INPROGRESS_DIR, REAL_TODOS_DIR, REAL_WORKING_LOG, REAL_RUNS_JSONL)
    assert "TCK-20260702-OBSISO-EPIC" not in report.split("Informational:")[0]
    assert "TCK-20260702-OBSISO-EPIC" in report.split("Informational:")[1]


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

def test_advisory_only_no_file_mutation():
    def _hash_dir(directory: Path) -> dict:
        return {p.name: p.read_bytes() for p in sorted(directory.iterdir()) if p.is_file()}

    before = _hash_dir(REAL_OBSISO_DIR)
    compute_stale_epics_report(REAL_INPROGRESS_DIR, REAL_TODOS_DIR, REAL_WORKING_LOG, REAL_RUNS_JSONL)
    find_stale_epics(REAL_INPROGRESS_DIR, REAL_TODOS_DIR, REAL_WORKING_LOG, REAL_RUNS_JSONL)
    after = _hash_dir(REAL_OBSISO_DIR)

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
