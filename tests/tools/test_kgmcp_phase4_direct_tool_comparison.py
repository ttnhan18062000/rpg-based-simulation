"""Tests for the Knowledge Gateway MCP Phase 4 direct-tool comparison
(TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON).

Mirrors `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`'s SHA-256
content-hash-snapshot and AST-inspection conventions. Most assertions here read (never write) the
committed Phase 4 fixture, produced by a real, live, paired run of
`tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py::main()` against the real
gateway and the real Context Search / Graphify / Parity Ledger direct-tool call paths, followed by
the hand-authored `reviewer_judgment` objects required by Step 6.

The real, honest result recorded by this ticket: the gateway is slower and heavier on tokens than
the direct-tool combination for all 7 corpus entries in this fresh, cold-cache run; 6/7 entries are
judged `direct_equal_or_better` and 1/7 (`Q3_requirement_completeness`, the newly-live Parity
Ledger route) is judged `mixed`. Two of the 7 entries' apparent context_search-half source misses
turned out, on hand inspection, to be normalization-shape false positives (the document was
genuinely retained by the gateway, just under a differently-shaped identifier) rather than real
content loss — this is disclosed explicitly in the reviewer_judgment rationale for those entries,
not silently corrected in the objective proxy (which stays untouched, per Step 5's own Do-Not-Touch
guard).
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_TOOLS_DIR = _REPO_ROOT / "tools"

_RUNNER_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_phase4_direct_tool_comparison_runner.py"
_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase4_direct_tool_comparison_results.json"
)
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION, ROUTING_SHAPES  # noqa: E402

_RUNNER_SOURCE = _RUNNER_MODULE_PATH.read_text()
_RUNNER_AST = ast.parse(_RUNNER_SOURCE)
_FIXTURE = json.loads(_FIXTURE_PATH.read_text())

# Snapshot captured at the start of this ticket's own Implementation (2026-08-16, before this
# ticket's own runner or fixture existed) — mirrors Phase 3's own content-hash-snapshot technique
# (chosen there, and here, because `git diff --stat HEAD` false-positives on sibling-ticket
# concurrent changes in the same working tree).
# knowledge_gateway_mcp.py, knowledge_gateway_packet_assembly.py, and the Phase 3 fixture below
# were all further removed (TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE, 2026-08-16):
# that ticket's own approved plan legitimately edits both files and regenerates the Phase 3 fixture
# in full while widening the budget-cost accounting — same narrowing precedent as this dict's other
# entries, see tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py's own module docstring
# "Post-fix update" note for the full disclosure.
_FROZEN_FILE_HASHES = {
    _TOOLS_DIR / "knowledge_gateway_router.py": (
        "25c71f50d37206d11756d52cd146fac85c6516e0b654ab6156cd1781ba886ae3"
    ),
    _TOOLS_DIR / "knowledge_gateway_cache.py": (
        "4b74cef3615bf5325750c40c7feacac1059820833de893a69c63f7003841d0cc"
    ),
    _TOOLS_DIR / "parity_index.py": (
        "d75ceafb9e3604f1ae4f5951f15978df6f9eb8455b7d80a6b8ab2b2d972a7d54"
    ),
    _TOOLS_DIR / "search_mcp.py": (
        "68da54a3d9df57bb9e776b855e5efec5719827470cb1b561315157373974c336"
    ),
    _MONITORING_TOOLS_DIR / "kgmcp_baseline_corpus.py": (
        "3d1b838a93a12925c8ca3e3347eb8e661a9c0528ad03837496673604d0b10142"
    ),
    _MONITORING_TOOLS_DIR / "kgmcp_baseline_runner.py": (
        "bd77794ab8f763442104dfb2901795a81a26fed2f892e24c2668244f0b92c550"
    ),
    _MONITORING_TOOLS_DIR / "kgmcp_phase1_gateway_runner.py": (
        "b514bfca9df527d70085fead430f28c11829ea801ba5e1826e97e19434fca44d"
    ),
    _MONITORING_TOOLS_DIR / "kgmcp_phase2_gateway_runner.py": (
        "53979bccf22e8f3ee5f4743d3dbfb8a17957899a2f64a7c253448cccaf254153"
    ),
    _MONITORING_TOOLS_DIR / "kgmcp_phase3_gateway_runner.py": (
        "199061bb6d4d088b471d01522712b20109c937286922e6d37c69903c9ab571c9"
    ),
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json": (
        "3ef6fbbe9821fa8f9a36511403bd81396d9ff2546a114836d52a3b6d1b23d9f7"
    ),
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase1_baseline_comparison_results.json": (
        "6eef6ed5ba6e71c29b9acf5662872a79023020001e3cba34aeeadaf5235d3a9f"
    ),
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase2_baseline_recomparison_results.json": (
        "89860b1b17ce47805a220220ee3a5016aeab50a6b3a61f0b94c4c242e353a568"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Frozen-dependency / anti-drift guards
# ---------------------------------------------------------------------------

def test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture():
    for path, expected_hash in _FROZEN_FILE_HASHES.items():
        assert _sha256(path) == expected_hash, (
            f"{path} was modified since this ticket's own Implementation started — this ticket "
            "is measurement-only and must never edit this frozen dependency"
        )


def test_new_runner_imports_not_reimplements_phase0_pure_helpers():
    imported_from_corpus = set()
    imported_from_phase1 = set()
    for node in ast.walk(_RUNNER_AST):
        if isinstance(node, ast.ImportFrom) and node.module == "kgmcp_baseline_corpus":
            imported_from_corpus |= {alias.name for alias in node.names}
        if isinstance(node, ast.ImportFrom) and node.module == "kgmcp_phase1_gateway_runner":
            imported_from_phase1 |= {alias.name for alias in node.names}

    assert {"CORPUS", "CORPUS_VERSION", "kgmcp_char_heuristic_v1_token_count"} <= imported_from_corpus
    assert {"_compute_threshold_4_3", "_normalize_phase1_source_id", "_path_only"} <= imported_from_phase1

    defined_names = {
        node.name for node in ast.walk(_RUNNER_AST) if isinstance(node, ast.FunctionDef)
    }
    assert not (
        {"_compute_threshold_4_3", "_normalize_phase1_source_id", "_path_only"} & defined_names
    )
    assert not (
        {"CORPUS", "CORPUS_VERSION", "kgmcp_char_heuristic_v1_token_count"} & defined_names
    )


def test_never_calls_emit_retrieval_event_or_wrap_functions():
    banned_names = {
        "emit_retrieval_event",
        "wrap_hybrid_retrieval",
        "wrap_retrieval_cache_check",
        "wrap_context_packet_assembly",
    }
    called_names = {
        node.func.id
        for node in ast.walk(_RUNNER_AST)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attrs = {
        node.func.attr
        for node in ast.walk(_RUNNER_AST)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not (called_names & banned_names)
    assert not (called_attrs & banned_names)
    assert "MagicMock" not in _RUNNER_SOURCE
    assert "unittest.mock" not in _RUNNER_SOURCE


def _agent_monitoring_porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


@pytest.mark.extra_slow
def test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner():
    """Exercises the new runner's full live-call path (`run_corpus()`, all 7 corpus entries) — real
    gateway calls plus real direct-tool calls (Context Search, Graphify, and Parity Ledger for Q3)
    — deliberately NOT `main()` (which would also overwrite the committed, hand-annotated fixture).
    Real runtime: ~7 gateway calls + ~15 direct-tool calls, comparable in scale to Phase 3's own
    `extra_slow`-marked equivalent — run with `--resource-budget large`."""
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from kgmcp_phase4_direct_tool_comparison_runner import run_corpus

    pre_porcelain = _agent_monitoring_porcelain_snapshot()
    run_corpus()
    post_porcelain = _agent_monitoring_porcelain_snapshot()

    assert pre_porcelain == post_porcelain, (
        "kgmcp_phase4_direct_tool_comparison_runner.run_corpus() mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )


# ---------------------------------------------------------------------------
# AC1 — every corpus entry run through both real gateway and real direct-tool call(s)
# ---------------------------------------------------------------------------

def test_all_7_corpus_entries_present_with_both_gateway_and_direct_results():
    corpus_ids = {e["id"] for e in CORPUS}
    fixture_ids = {e["id"] for e in _FIXTURE["entries"]}
    assert len(corpus_ids) == 7
    assert fixture_ids == corpus_ids

    for entry in _FIXTURE["entries"]:
        assert "gateway" in entry and "response" in entry["gateway"]
        assert "direct" in entry
        assert "context_search" in entry["direct"]
        assert "graphify" in entry["direct"]


def test_q3_direct_result_includes_a_real_parity_index_entry_call():
    q3 = next(e for e in _FIXTURE["entries"] if e["id"] == "Q3_requirement_completeness")
    assert "parity_ledger" in q3["direct"]
    pl = q3["direct"]["parity_ledger"]
    assert "entry_result" in pl
    assert pl["entry_result"]["entry_id"] == q3["query_text"], (
        "the direct Parity Ledger call must pass query_text itself as entry_id, not a resolved id "
        "— exactly mirroring the gateway's own _run_parity_provider() convention"
    )
    assert "found" in pl["entry_result"]

    for entry in _FIXTURE["entries"]:
        if entry["id"] != "Q3_requirement_completeness":
            assert "parity_ledger" not in entry["direct"]


def test_raw_content_retained_on_both_sides_for_quality_comparison():
    for entry in _FIXTURE["entries"]:
        cs = entry["direct"]["context_search"]
        assert "raw_results" in cs
        gf = entry["direct"]["graphify"]
        assert "raw_stdout" in gf and isinstance(gf["raw_stdout"], str)
        assert "response" in entry["gateway"]
        assert isinstance(entry["gateway"]["response"], dict)
        assert entry["gateway"]["response"], "gateway response must not be an empty stand-in"


def test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing():
    q3 = next(e for e in _FIXTURE["entries"] if e["id"] == "Q3_requirement_completeness")
    assert "parity_ledger" in q3["gateway"]["providers_selected"], (
        "Q3's real, fresh route() call must show the now-live parity_ledger dispatch "
        "(TCK-20260816-KGMCP-P4-PARITY-ADAPTER), not the pre-INFRA-351 dead-end"
    )
    assert "context_search" in q3["gateway"]["providers_selected"]


# ---------------------------------------------------------------------------
# AC2 — results reported per-query-type
# ---------------------------------------------------------------------------

def test_results_grouped_by_query_type_not_only_aggregate():
    assert "by_routing_shape" in _FIXTURE
    assert set(_FIXTURE["by_routing_shape"].keys()) == set(ROUTING_SHAPES)
    entries_by_shape = {e["routing_shape"]: e["id"] for e in _FIXTURE["entries"]}
    for shape, summary in _FIXTURE["by_routing_shape"].items():
        assert summary["entry_id"] == entries_by_shape[shape]


# ---------------------------------------------------------------------------
# AC3 — quality axis: source-completeness proxy (objective) + reviewer_judgment (subjective)
# ---------------------------------------------------------------------------

def test_graphify_half_of_recall_is_no_longer_na():
    statuses = {
        e["quality"]["source_completeness"]["graphify_half"]["graphify_half_status"]
        for e in _FIXTURE["entries"]
    }
    assert "measured" in statuses, (
        "at least one entry must show a real, non-N/A graphify-side source comparison — closing "
        "Design Decision D3's 3-phase-old gap"
    )
    assert "N/A" not in statuses
    for entry in _FIXTURE["entries"]:
        gh = entry["quality"]["source_completeness"]["graphify_half"]
        assert gh["graphify_half_status"] in ("measured", "not_routed_this_entry")
        if gh["graphify_half_status"] == "measured":
            assert "graphify_missing_sources" in gh
            assert "graphify_extra_sources" in gh


def test_context_search_half_derivation_does_not_claim_phase0_fixture_provenance():
    """Provenance-honesty fix (Architecture Review 1st pass): `_compute_threshold_4_3()`'s own
    hardcoded derivation string must be overwritten before persistence — it falsely claims Phase 0
    fixture provenance once fed this ticket's own freshly-run direct_context_search data."""
    for entry in _FIXTURE["entries"]:
        derivation = entry["quality"]["source_completeness"]["context_search_half"]["derivation"]
        assert "Phase 0 fixture" not in derivation
        assert "THIS TICKET" in derivation
        assert "freshly-run" in derivation


def test_quality_signal_is_labeled_judgment_not_scored_metric():
    for entry in _FIXTURE["entries"]:
        rj = entry["quality"]["reviewer_judgment"]
        assert rj is not None, f"{entry['id']}: reviewer_judgment must be populated before commit"
        assert rj["basis"] == "reviewer_judgment_not_a_computed_metric"
        assert rj["verdict"] in ("gateway_equal_or_better", "direct_equal_or_better", "mixed")
        assert rj["rationale"]
        # Structurally distinct sub-objects — never merged into one top-level "quality" number.
        assert "source_completeness" in entry["quality"]
        assert "reviewer_judgment" in entry["quality"]
        assert set(entry["quality"].keys()) == {"source_completeness", "reviewer_judgment"}


def test_reviewer_judgment_verdict_is_never_derived_programmatically_from_source_completeness():
    """Structural guard: the runner module itself must never compute `reviewer_judgment.verdict`
    from `source_completeness`'s numbers — AST-inspected (not a raw substring scan, which would
    false-positive on this module's own prose docstrings describing the field): every dict literal
    in the runner source that has a `"reviewer_judgment"` string key must map that key to a bare
    `None` constant, never a computed expression (Step 6: 'the runner script itself cannot compute
    it — it requires reading content')."""
    found_key = False
    for node in ast.walk(_RUNNER_AST):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value_node in zip(node.keys, node.values):
            if (
                isinstance(key_node, ast.Constant)
                and key_node.value == "reviewer_judgment"
            ):
                found_key = True
                assert isinstance(value_node, ast.Constant) and value_node.value is None, (
                    "runner source assigns reviewer_judgment to something other than a bare None "
                    "placeholder — it must never be computed by the runner itself"
                )
    assert found_key, "expected the runner to leave a reviewer_judgment: None placeholder key"


def test_reviewer_judgment_rationales_are_not_byte_identical_across_entries():
    rationales = [e["quality"]["reviewer_judgment"]["rationale"] for e in _FIXTURE["entries"]]
    assert len(rationales) == 7
    assert len(set(rationales)) == 7, "every entry's rationale must be genuinely distinct text"


def test_reviewer_judgment_cites_a_real_recorded_source_when_source_completeness_shows_a_gap():
    for entry in _FIXTURE["entries"]:
        sc = entry["quality"]["source_completeness"]
        csh = sc["context_search_half"]
        gh = sc["graphify_half"]

        recorded_gap_sources: set[str] = set(csh.get("missing_sources", []))
        if gh.get("graphify_half_status") == "measured":
            recorded_gap_sources |= set(gh.get("graphify_missing_sources", []))
            recorded_gap_sources |= set(gh.get("graphify_extra_sources", []))

        rationale = entry["quality"]["reviewer_judgment"]["rationale"]

        if recorded_gap_sources:
            cited = [s for s in recorded_gap_sources if s in rationale]
            assert cited, (
                f"{entry['id']}: source_completeness recorded a gap "
                f"({sorted(recorded_gap_sources)[:3]}...) but rationale cites none of it verbatim"
            )
        else:
            assert "no source-set difference" in rationale.lower() or "no missing" in rationale.lower(), (
                f"{entry['id']}: no gap recorded, but rationale does not explicitly say so"
            )


# ---------------------------------------------------------------------------
# AC4 — honest reporting: no disadvantage silently excluded or redefined
# ---------------------------------------------------------------------------

def test_no_query_type_disadvantage_is_silently_excluded_or_redefined():
    assert len(_FIXTURE["entries"]) == 7
    assert len(_FIXTURE["by_routing_shape"]) == 7

    for entry in _FIXTURE["entries"]:
        lc = entry["latency_comparison"]
        tc = entry["token_comparison"]
        assert lc["gateway_faster"] == (
            lc["gateway_wall_time_ms"] < lc["direct_combined_wall_time_ms"]
        )
        assert tc["gateway_lighter"] == (
            tc["gateway_tokens"] < tc["direct_combined_tokens_estimate"]
        )

    # The real, committed result: the gateway shows no genuine latency or token advantage over
    # direct tool use for any of the 7 entries in this fresh, cold-cache run — reported plainly,
    # not massaged or excluded.
    assert all(not e["latency_comparison"]["gateway_faster"] for e in _FIXTURE["entries"])
    assert all(not e["token_comparison"]["gateway_lighter"] for e in _FIXTURE["entries"])


def test_real_reviewer_verdicts_include_at_least_one_non_gateway_favoring_result():
    verdicts = {e["id"]: e["quality"]["reviewer_judgment"]["verdict"] for e in _FIXTURE["entries"]}
    assert "direct_equal_or_better" in verdicts.values(), (
        "the real, honest per-entry judgment result must not be uniformly gateway-favoring — this "
        "guards against a future edit silently flipping an unfavorable verdict"
    )


# ---------------------------------------------------------------------------
# Gap-check additions (Test phase, post Architecture-Verify APPROVED):
# these two assertions were previously only true in prose (Implementation Notes / the results doc)
# with no mechanical test backing them.
# ---------------------------------------------------------------------------

def test_fixture_corpus_version_matches_currently_imported_baseline_corpus():
    """Guards against silently running this comparison against a stale/mismatched corpus
    definition: the persisted fixture's own `corpus_version` must equal the live, currently-imported
    `kgmcp_baseline_corpus.CORPUS_VERSION`, not a frozen/stale number left over from an earlier
    corpus revision that happens to still deserialize without error."""
    assert _FIXTURE["corpus_version"] == CORPUS_VERSION


def test_reviewer_judgment_normalization_false_positive_claims_are_mechanically_verified():
    """Step 6's hand-inspection found 2 of the 7 entries' (Q4_historical_rationale,
    Q6_ticket_status) recorded `context_search_half` misses were 'normalization-shape false
    positives, not real loss' — the document was claimed to be genuinely present in the gateway's
    own recorded context, just under a differently-shaped source id (a
    `stored_artifacts/<ticket>/...` path rather than the bare ticket-id `doc_id` shape the direct
    call's raw result carries). Before this test, that specific claim was asserted only in prose
    (the rationale string / the results doc) — a false 'false positive' claim would not have been
    caught mechanically, exactly the kind of thing this ticket's own Gate Integrity bar exists to
    catch. This test re-derives the claim from the fixture's own recorded data: for every entry
    whose rationale invokes a normalization/false-positive claim, every `missing_sources` id it
    cites verbatim must actually appear as a substring of at least one string in that same entry's
    own recorded `gateway_sources` — i.e. the content really is present, just under another id
    shape, not merely asserted to be."""
    checked_any = False
    for entry in _FIXTURE["entries"]:
        rationale = entry["quality"]["reviewer_judgment"]["rationale"]
        if "normalization" not in rationale.lower() or "false positive" not in rationale.lower():
            continue
        checked_any = True

        csh = entry["quality"]["source_completeness"]["context_search_half"]
        missing = csh.get("missing_sources", [])
        gateway_sources = csh.get("gateway_sources", [])

        cited_missing = [m for m in missing if m in rationale]
        assert cited_missing, (
            f"{entry['id']}: rationale claims a normalization-shape false positive but cites no "
            "recorded missing_sources id verbatim"
        )
        for missing_id in cited_missing:
            assert any(missing_id in gs for gs in gateway_sources), (
                f"{entry['id']}: rationale claims {missing_id!r} is a normalization-shape false "
                "positive (genuinely present under a different id shape) but no string in this "
                f"entry's own recorded gateway_sources ({gateway_sources!r}) actually contains it "
                "as a substring — the false-positive claim is not backed by the fixture's own "
                "recorded data"
            )

    assert checked_any, (
        "expected at least one entry (Q4_historical_rationale, Q6_ticket_status per Implementation "
        "Notes) to carry a normalization-shape false-positive claim in its reviewer_judgment "
        "rationale — if this no longer holds, the claim's mechanical backing has nothing to check"
    )
