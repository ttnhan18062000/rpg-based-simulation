"""Tests for tools/open_ticket_overlap.py (TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER).

Mirrors tests/tools/test_epic_folder_status.py's fixture-directory-per-test style: real
tickets/todos/tickets/inprogress-shaped subtrees under tmp_path, no mocking of the parser.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from open_ticket_overlap import find_overlapping_open_tickets  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "open_ticket_overlap"
_REAL_TARGET_TICKET = (
    _REPO_ROOT / "tickets" / "todos" / "TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED.md"
)


def _write_ticket(
    path: Path,
    ticket_id: str,
    title: str,
    summary: str,
    code_areas: list,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    areas_text = "\n".join(f"- `{a}`" for a in code_areas) or "None."
    path.write_text(
        f"---\nstatus: active\nlayer: ai\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-01-01\ntags: []\n---\n\n"
        f"# {ticket_id}\n\n"
        f"## Title\n{title}\n\n"
        f"## Status\nOPEN\n\n"
        f"## Tier\nhotfix\n\n"
        f"## Request Summary\n{summary}\n\n"
        f"## Related Code Areas\n{areas_text}\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# AC1 -- real missed pair, via fixture
# ---------------------------------------------------------------------------


def test_finds_overlap_with_real_target_ticket_via_fixture(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    todos.mkdir(parents=True)
    (todos / _REAL_TARGET_TICKET.name).write_text(
        _REAL_TARGET_TICKET.read_text(encoding="utf-8"), encoding="utf-8"
    )

    fixture_text = (_FIXTURE_DIR / "B0-PERCEPTION-UPDATE-WAVE-FIXTURE.md").read_text(encoding="utf-8")
    fixture_path = todos / "B0-PERCEPTION-UPDATE-WAVE-FIXTURE.md"
    fixture_path.write_text(fixture_text, encoding="utf-8")

    hits = find_overlapping_open_tickets(
        query_title="Wave B0: wire the perception pipeline into strategic cognition so goal "
                    "selection reads a real perceived-entity model instead of a raw spatial query",
        query_summary=(
            "Reconstructs the real miss: rpg-feature-planning's hand-authored roadmap wave "
            "ticket concerns wiring the perception pipeline into strategic cognition."
        ),
        query_code_areas=[
            "src/domains/perception/phase.py",
            "src/systems/strategic_systems/intelligence.py",
            "src/engine/pipeline.py",
        ],
        query_ticket_id="TCK-FIXTURE-B0-PERCEPTION-WAVE",
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )

    hit_ids = {h["ticket_id"] for h in hits}
    assert "TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED" in hit_ids
    target_hit = next(h for h in hits if h["ticket_id"] == "TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED")
    assert target_hit["matched_code_areas"], "expected at least one matched code area"


# ---------------------------------------------------------------------------
# AC2 -- negative controls
# ---------------------------------------------------------------------------


def test_unrelated_ticket_gets_no_hits(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "TCK-COMBAT-UNRELATED.md",
        "TCK-COMBAT-UNRELATED",
        "Combat durability decay formula rounds down instead of to nearest",
        "Tactical combat resolution durability decay uses floor division.",
        ["src/domains/combat_engagement/resolution.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap in strategic cognition.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id="TCK-QUERY-EXAMPLE",
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert hits == []


def test_ticket_never_matches_itself(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "TCK-SELF.md",
        "TCK-SELF",
        "Perception pipeline never instantiated",
        "PerceptionUpdatePhase wiring gap in strategic cognition.",
        ["src/domains/perception/phase.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap in strategic cognition.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id="TCK-SELF",
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert hits == []


# ---------------------------------------------------------------------------
# AC3 -- no index/staleness dependency
# ---------------------------------------------------------------------------


def test_sees_a_ticket_created_during_the_test(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    hits_before = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert hits_before == []

    _write_ticket(
        todos / "TCK-JUST-WRITTEN.md",
        "TCK-JUST-WRITTEN",
        "Perception pipeline never instantiated",
        "PerceptionUpdatePhase wiring gap.",
        ["src/domains/perception/phase.py"],
    )

    hits_after = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert {h["ticket_id"] for h in hits_after} == {"TCK-JUST-WRITTEN"}


# ---------------------------------------------------------------------------
# Signal-isolation tests
# ---------------------------------------------------------------------------


def test_code_area_signal_alone_triggers_a_hit(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "TCK-CODEAREA-ONLY.md",
        "TCK-CODEAREA-ONLY",
        "Totally different subject about crafting recipes",
        "Nothing to do with the query's own wording at all, distinct domain entirely.",
        ["src/domains/perception/phase.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Unrelated title wording here",
        query_summary="Also unrelated wording, no shared vocabulary intended.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert {h["ticket_id"] for h in hits} == {"TCK-CODEAREA-ONLY"}


def test_term_overlap_signal_alone_triggers_a_hit(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "TCK-TERMS-ONLY.md",
        "TCK-TERMS-ONLY",
        "Perception pipeline strategic cognition wiring gap",
        "Concerns perception and strategic cognition wiring.",
        ["src/completely/unrelated/path.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline strategic cognition investigation",
        query_summary="Also about perception and strategic cognition.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert {h["ticket_id"] for h in hits} == {"TCK-TERMS-ONLY"}


def test_single_shared_term_is_not_enough(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "TCK-ONE-TERM.md",
        "TCK-ONE-TERM",
        "Combat durability decay formula wrong",
        "Rounds down instead of nearest during combat resolution.",
        ["src/domains/combat_engagement/resolution.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap during combat.",  # shares only "combat"
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert hits == []


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


def test_recurses_into_todos_subfolders(tmp_path):
    todos = tmp_path / "tickets" / "todos"
    _write_ticket(
        todos / "myepic" / "TCK-NESTED.md",
        "TCK-NESTED",
        "Perception pipeline never instantiated",
        "PerceptionUpdatePhase wiring gap.",
        ["src/domains/perception/phase.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=todos,
        inprogress_root=tmp_path / "tickets" / "inprogress",
    )
    assert {h["ticket_id"] for h in hits} == {"TCK-NESTED"}


def test_scans_inprogress_too(tmp_path):
    inprogress = tmp_path / "tickets" / "inprogress"
    _write_ticket(
        inprogress / "TCK-INPROGRESS.md",
        "TCK-INPROGRESS",
        "Perception pipeline never instantiated",
        "PerceptionUpdatePhase wiring gap.",
        ["src/domains/perception/phase.py"],
    )

    hits = find_overlapping_open_tickets(
        query_title="Perception pipeline never instantiated",
        query_summary="PerceptionUpdatePhase wiring gap.",
        query_code_areas=["src/domains/perception/phase.py"],
        query_ticket_id=None,
        todos_root=tmp_path / "tickets" / "todos",
        inprogress_root=inprogress,
    )
    assert {h["ticket_id"] for h in hits} == {"TCK-INPROGRESS"}
