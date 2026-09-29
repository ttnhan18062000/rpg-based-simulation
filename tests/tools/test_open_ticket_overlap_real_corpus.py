"""Real-corpus calibration tests for tools/open_ticket_overlap.py
(TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER, peer review round 2).

The synthetic-fixture tests in test_open_ticket_overlap.py prove the scoring mechanism works in
isolation; they cannot prove it stays usable against the real, messy ~82-ticket open corpus. Peer
review measured the pre-fix boolean-OR design directly against that corpus and found it unusable
(average 70.9/81 possible hits per query, shared-term counts up to 15 on pure noise like
"actually"/"confirmed"). This file re-measures the IDF-weighted, ranked, capped replacement the
same way, against the same real tree, so the claim "this is now usable" is evidence, not assertion.

Read-only: never writes to tickets/todos/ or tickets/inprogress/.
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from open_ticket_overlap import _load_ticket, find_overlapping_open_tickets  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_TODOS_ROOT = _REPO_ROOT / "tickets" / "todos"
_INPROGRESS_ROOT = _REPO_ROOT / "tickets" / "inprogress"
_FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "open_ticket_overlap"
_TARGET_TICKET_ID = "TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED"

_B0_TITLE = (
    "Wave B0: wire the perception pipeline into strategic cognition so goal selection reads a "
    "real perceived-entity model instead of a raw spatial query"
)
_B0_SUMMARY = (
    "Reconstructs the real miss: rpg-feature-planning's hand-authored roadmap wave ticket "
    "concerns wiring the perception pipeline into strategic cognition."
)
_B0_CODE_AREAS = [
    "src/domains/perception/phase.py",
    "src/systems/strategic_systems/intelligence.py",
    "src/engine/pipeline.py",
]


def _real_open_ticket_paths() -> list:
    paths = []
    for root in (_TODOS_ROOT, _INPROGRESS_ROOT):
        if root.exists():
            paths.extend(sorted(root.rglob("TCK-*.md")))
    return paths


def test_b0_fixture_ranks_the_real_target_ticket_first_with_code_areas():
    hits = find_overlapping_open_tickets(
        query_title=_B0_TITLE,
        query_summary=_B0_SUMMARY,
        query_code_areas=_B0_CODE_AREAS,
        query_ticket_id="TCK-FIXTURE-B0-PERCEPTION-WAVE",
        todos_root=_TODOS_ROOT,
        inprogress_root=_INPROGRESS_ROOT,
    )
    assert hits, "expected at least one hit against the real corpus"
    assert hits[0]["ticket_id"] == _TARGET_TICKET_ID, (
        f"expected {_TARGET_TICKET_ID} ranked #1 against the real corpus, got {hits[0]['ticket_id']} "
        f"(score {hits[0]['score']}) -- full top results: {[(h['ticket_id'], h['score']) for h in hits]}"
    )


def test_b0_fixture_ranks_the_real_target_ticket_first_title_summary_only():
    """The concern-investigator call shape: no code areas at all, title+summary only. This is the
    harder case (peer review's own point: this path gets signal (b) alone) -- if the target isn't
    found here, the exact real miss this ticket exists to fix (a hand-authored wave ticket, no
    Related Code Areas section yet at concern stage) still slips through."""
    hits = find_overlapping_open_tickets(
        query_title=_B0_TITLE,
        query_summary=_B0_SUMMARY,
        query_code_areas=[],
        query_ticket_id="TCK-FIXTURE-B0-PERCEPTION-WAVE",
        todos_root=_TODOS_ROOT,
        inprogress_root=_INPROGRESS_ROOT,
    )
    assert hits, "expected at least one hit against the real corpus (title/summary only)"
    assert hits[0]["ticket_id"] == _TARGET_TICKET_ID, (
        f"expected {_TARGET_TICKET_ID} ranked #1 (title/summary only) against the real corpus, "
        f"got {hits[0]['ticket_id']} (score {hits[0]['score']}) -- "
        f"full top results: {[(h['ticket_id'], h['score']) for h in hits]}"
    )


def test_median_hit_count_per_real_ticket_stays_small():
    """Each real open ticket, queried against every OTHER real open ticket, must not flood the
    output. Pre-fix (peer measurement): average 70.9/81 possible hits, zero tickets with zero
    hits -- an advisory nobody reads. Post-fix: capped at top_n (5 by default), so this is really
    asserting the cap works end-to-end, not a new empirical claim -- but it's the AC the peer
    review asked for, and it's cheap to prove directly rather than trust the cap in isolation."""
    real_tickets = []
    for path in _real_open_ticket_paths():
        loaded = _load_ticket(path)
        if loaded is not None:
            real_tickets.append(loaded)

    assert len(real_tickets) >= 10, "expected a real, non-trivial open-ticket corpus to measure against"

    hit_counts = []
    for query in real_tickets:
        hits = find_overlapping_open_tickets(
            query_title=query["title"],
            query_summary=query["summary"],
            query_code_areas=query["code_areas"],
            query_ticket_id=query["ticket_id"],
            todos_root=_TODOS_ROOT,
            inprogress_root=_INPROGRESS_ROOT,
        )
        hit_counts.append(len(hits))

    median = statistics.median(hit_counts)
    assert median <= 5, f"median hit count per real ticket is {median}, expected <= 5 (counts: {hit_counts})"
