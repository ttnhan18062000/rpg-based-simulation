"""Regression-lock tests for TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE's Gap 2
(multi-provider dedup real-corpus-proof coverage) and the adjacent, newly-found
`canonical_fragment_hash`-vs-`_content_hash()` parity dedup-identity divergence.

Both tests are disclosure-only regression locks, not fixes — see plan.md's own Scope Guards
("do not fix the parity_ledger hash-formula divergence", "does not propose a corpus extension").

Test 1 is a genuine LIVE monitor: it re-runs the real gateway (real `route()`/
`call_providers_for_routing_decision()`/`render_candidates()`/`deduplicate_statements()`, no
monkeypatched `_run_search()`/`match_symbol_name()`) against the real frozen 7-entry corpus
(`tools/agent-monitoring/kgmcp_baseline_corpus.py`) every test run — never a stale snapshot
assertion. If a future change starts producing real duplicate content across providers (or loses
the ability to detect an existing one), this test fails, and the finding must be re-evaluated.

Test 2 is fixture-only (mirrors `build_conflicts()`'s own established fixture-only precedent for
logic no live corpus entry can currently exercise), since no real corpus entry today produces a
`parity_ledger` `found=True` result whose text is byte-identical to a `context_search` excerpt.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from tools import knowledge_gateway_packet_assembly as kpa  # noqa: E402
from kgmcp_baseline_corpus import CORPUS  # noqa: E402

_PARITY_LEDGER_DIR = _REPO_ROOT / "docs" / "parity_ledger"


# ---------------------------------------------------------------------------
# Gap 2 — live, real-corpus dedup coverage (disclosure only, no fix)
# ---------------------------------------------------------------------------

def test_live_corpus_has_zero_cross_provider_content_duplicates_documented_limitation(
    tmp_path, monkeypatch
):
    """LIVE monitor — re-runs the real gateway against the real frozen 7-entry corpus every test
    run (never a stale snapshot). As of this ticket's own investigation, live routing sends 2 of
    7 entries (Q3, Q7) to more than one provider, but zero real duplicate content exists anywhere
    in the corpus today — pre-dedup and post-dedup statement counts are equal for every entry.
    If a future corpus/provider change starts producing (or silently loses the ability to detect)
    a genuine duplicate, this test fails and the documented 0/7 finding must be re-evaluated, not
    silently drift further from reality."""
    kgr_mod = kpa._load_router_module()
    pidx = kgr_mod._load_parity_index_module()
    db_path = tmp_path / "parity.db"
    build_report = pidx.build(ledger_dir=_PARITY_LEDGER_DIR, db_path=db_path)
    assert build_report["status"] == "ok"
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", db_path)

    for entry in CORPUS:
        routing_decision = kgr_mod.route(entry["query_text"])
        provider_results = kpa.call_providers_for_routing_decision(
            routing_decision, entry["query_text"]
        )
        statements, _context_entries, _evidence_entries = kpa.render_candidates(
            provider_results, entry["query_text"]
        )
        deduped = kpa.deduplicate_statements(statements)
        assert len(deduped) == len(statements), (
            f"{entry['id']}: expected zero real cross-provider content duplicates (documented "
            f"limitation), but dedup collapsed {len(statements)} statements into "
            f"{len(deduped)} — a real duplicate now exists; re-evaluate this ticket's Gap 2 "
            f"finding rather than silently accepting the drift."
        )


# ---------------------------------------------------------------------------
# Adjacent, newly-found gap — parity dedup-identity divergence (regression lock, not a fix)
# ---------------------------------------------------------------------------

def test_parity_ledger_evidence_hash_uses_canonical_fragment_hash_not_content_hash():
    """Regression lock, not a fix — "the Parity adapter" is explicitly Out of Scope for this
    ticket. `render_candidates()`'s `parity_ledger` block assigns
    `evidence_hash = record["canonical_fragment_hash"]` — the parity index's own precomputed
    hash — never `_content_hash(text)`, unlike the `context_search`/`graphify` blocks. This locks
    in the real, newly-found divergence: byte-identical text between a parity statement and a
    context_search statement would NOT collapse into one dedup group under `deduplicate_statements()`,
    since their `evidence_hash` key strings differ even though their content is identical. No live
    corpus entry produces this scenario today (investigation.md — Q3's only parity-selecting entry
    returns `found=False`), so this is fixture-only, matching `build_conflicts()`'s own established
    fixture-only precedent for logic untestable against real providers. This test intentionally
    does NOT call `deduplicate_statements()` — the point is the `evidence_hash` divergence itself,
    not a dedup outcome."""
    shared_text = "Identical content shared by parity_ledger and context_search fixtures."

    provider_results = {
        "context_search": [
            {"source_path": "docs/a.md", "heading": "A", "excerpt": shared_text},
        ],
        "graphify": None,
        "parity_ledger": {
            "results": {
                "found": True,
                "record": {
                    "id": "INFRA-999",
                    "shard": "infrastructure.yaml",
                    "text": shared_text,
                    "canonical_fragment_hash": "not-a-real-content-hash-deliberately-distinct",
                },
            },
        },
    }

    statements, _context_entries, _evidence_entries = kpa.render_candidates(
        provider_results, "query text irrelevant here"
    )
    assert len(statements) == 2
    context_search_statement, parity_statement = statements
    assert context_search_statement.text == parity_statement.text == shared_text

    assert context_search_statement.evidence_hash == kpa._content_hash(shared_text)
    assert parity_statement.evidence_hash == "not-a-real-content-hash-deliberately-distinct"
    assert context_search_statement.evidence_hash != parity_statement.evidence_hash
