"""Real-corpus calibration tests for tools/open_ticket_overlap.py
(TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER, peer review round 2).

The synthetic-fixture tests in test_open_ticket_overlap.py prove the scoring mechanism works in
isolation; they cannot prove it stays usable against a real, messy open-ticket corpus. Peer review
measured the pre-fix boolean-OR design directly against the real corpus and found it unusable
(average 70.9/81 possible hits per query, shared-term counts up to 15 on pure noise like
"actually"/"confirmed"). This file re-measures the IDF-weighted, ranked, capped replacement the
same way, so the claim "this is now usable" is evidence, not assertion.

**Frozen corpus, not the live tree (peer review round 4)**: the live `tickets/todos/`/
`tickets/inprogress/` tree changes on every merge -- the target ticket these assertions depend on
will eventually close and leave the open corpus, and any new open ticket touching the same code
areas could become a close runner-up and collapse the measured margin, both failing an unrelated
future PR for a reason that has nothing to do with this tool (the same defect class as
TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS: an exact assertion over a corpus that keeps
changing). `tests/fixtures/open_ticket_overlap/corpus/` is a frozen snapshot of the real
`tickets/todos/`+`tickets/inprogress/` trees (82 real tickets, source commit SHA in that
directory's own README.md) -- still a real, messy, non-synthetic corpus, just a stable one.
Deliberately NOT a skip-if-absent/skip-if-target-missing guard: that would silently turn the only
real-quality proof this tool has into a no-op; see the corpus README for the reasoning.

Read-only: never writes to the frozen fixture corpus.
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
_FROZEN_CORPUS_DIR = _FIXTURE_DIR / "corpus"
_TODOS_ROOT = _FROZEN_CORPUS_DIR / "todos"
_INPROGRESS_ROOT = _FROZEN_CORPUS_DIR / "inprogress"
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


# A previous "median hit count <= 5" test here was found vacuous by peer review round 3: with
# top_n=5 and min_score=0.0, `find_overlapping_open_tickets()` caps output at 5 by construction,
# so that assertion could never fail regardless of scoring quality -- it re-proved the cap exists,
# not that the cap is doing anything meaningful. Removed in favor of the margin assertions below,
# which the cap does NOT bound: a real-corpus regression here (e.g. scoring reverting toward the
# old undifferentiated-boolean shape) would show up as the margin collapsing toward 1.0, something
# the vacuous test could never have caught.
_MIN_MARGIN = 1.3  # conservative floor; real measured margins are ~1.9-2x (see docstrings below)


def test_b0_fixture_ranks_the_real_target_ticket_first_with_code_areas():
    hits = find_overlapping_open_tickets(
        query_title=_B0_TITLE,
        query_summary=_B0_SUMMARY,
        query_code_areas=_B0_CODE_AREAS,
        query_ticket_id="TCK-FIXTURE-B0-PERCEPTION-WAVE",
        todos_root=_TODOS_ROOT,
        inprogress_root=_INPROGRESS_ROOT,
    )
    assert len(hits) >= 2, "expected at least 2 hits against the real corpus to measure a margin"
    assert hits[0]["ticket_id"] == _TARGET_TICKET_ID, (
        f"expected {_TARGET_TICKET_ID} ranked #1 against the real corpus, got {hits[0]['ticket_id']} "
        f"(score {hits[0]['score']}) -- full top results: {[(h['ticket_id'], h['score']) for h in hits]}"
    )
    margin = hits[0]["score"] / hits[1]["score"]
    assert margin >= _MIN_MARGIN, (
        f"rank-1 score {hits[0]['score']} is only {margin:.2f}x rank-2 score {hits[1]['score']} "
        f"({hits[1]['ticket_id']}) -- expected a real, not marginal, separation"
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
    assert len(hits) >= 2, "expected at least 2 hits against the real corpus to measure a margin"
    assert hits[0]["ticket_id"] == _TARGET_TICKET_ID, (
        f"expected {_TARGET_TICKET_ID} ranked #1 (title/summary only) against the real corpus, "
        f"got {hits[0]['ticket_id']} (score {hits[0]['score']}) -- "
        f"full top results: {[(h['ticket_id'], h['score']) for h in hits]}"
    )
    margin = hits[0]["score"] / hits[1]["score"]
    assert margin >= _MIN_MARGIN, (
        f"rank-1 score {hits[0]['score']} is only {margin:.2f}x rank-2 score {hits[1]['score']} "
        f"({hits[1]['ticket_id']}) -- expected a real, not marginal, separation"
    )
