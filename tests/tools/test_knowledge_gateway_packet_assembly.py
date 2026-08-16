"""Tests for tools/knowledge_gateway_packet_assembly.py — extractive/template packet assembly
for the Knowledge Gateway MCP Phase 1 (TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY).

No live ML dependency, no live sqlite/vector index reads, no live `graphify` subprocess calls —
`tools/search_mcp.py::_run_search()` and `tools/knowledge_gateway_router.py::match_symbol_name()`
are monkeypatched at the module boundary this ticket's own module loads them through
(`kpa._load_search_mcp_module()` / `kpa._load_router_module()`), following
`tests/tools/test_context_packet_assembler.py`'s and `tests/tools/test_knowledge_gateway_router.py`'s
established conventions: small hand-built fixtures matching each real function's confirmed return
shape, `tmp_path`/`monkeypatch` isolation for capability-descriptor state.

Honesty note mirrored from the module under test: `test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support`
is the ONLY test that reaches `VERIFIED`/`SUPPORTED` negative-knowledge verification, and it does
so only via a monkeypatched/temp-copy capability descriptor — no real provider today declares
`negative_knowledge_support != "NONE"`, so this branch has zero real trigger path in Phase 1.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import knowledge_gateway_packet_assembly as kpa  # noqa: E402

_MODULE_PATH = _REPO_ROOT / "tools" / "knowledge_gateway_packet_assembly.py"


# ---------------------------------------------------------------------------
# Fixture builders — real _run_search()/match_symbol_name() return shapes
# ---------------------------------------------------------------------------

def _cs_result(
    *,
    source_path: str = "docs/plans/knowledge-gateway-mcp-proposal.md",
    heading: str = "15. Token-Budgeted Assembly",
    excerpt: str = "Budgeting must measure the content actually returned.",
    doc_id: str = "chunk-1",
    score: float = 0.9,
    **extra,
) -> dict:
    result = {
        "doc_id": doc_id,
        "title": "Some Title",
        "heading": heading,
        "source_path": source_path,
        "section": "",
        "score": score,
        "semantic_score": score,
        "keyword_score": score,
        "excerpt": excerpt,
    }
    result.update(extra)
    return result


def _graphify_result(
    *,
    symbol: str = "kgmcp_char_heuristic_v1",
    returncode: int = 0,
    stdout: str = "def kgmcp_char_heuristic_v1(text): ...",
) -> dict:
    return {"symbol": symbol, "returncode": returncode, "stdout": stdout}


def _routing_decision(providers_selected: list[str]):
    return SimpleNamespace(providers_selected=providers_selected)


def _assemble(
    monkeypatch,
    *,
    providers_selected: list[str],
    cs_results: list[dict] | None = None,
    graphify_result: dict | None = None,
    budget_requested: int = 10_000,
    query_text: str = "test query",
) -> "kpa.PacketAssembly":
    sm_mod = kpa._load_search_mcp_module()
    monkeypatch.setattr(sm_mod, "_run_search", lambda q: cs_results if cs_results is not None else [])

    kgr_mod = kpa._load_router_module()

    def _fake_match_symbol_name(q):
        if graphify_result is not None:
            return graphify_result
        return {"symbol": q, "returncode": 1, "stdout": ""}

    monkeypatch.setattr(kgr_mod, "match_symbol_name", _fake_match_symbol_name)

    return kpa.assemble_packet(
        _routing_decision(providers_selected), query_text, budget_requested
    )


# ---------------------------------------------------------------------------
# Step 1 — kgmcp_char_heuristic_v1
# ---------------------------------------------------------------------------

def test_kgmcp_char_heuristic_v1_matches_frozen_formula():
    assert kpa.kgmcp_char_heuristic_v1("") == 0
    assert kpa.kgmcp_char_heuristic_v1("abcd") == 1
    assert kpa.kgmcp_char_heuristic_v1("abcde") == 2
    multibyte = "café résumé"  # multi-byte UTF-8 case
    assert kpa.kgmcp_char_heuristic_v1(multibyte) == math.ceil(
        len(multibyte.encode("utf-8")) / 4
    )


# ---------------------------------------------------------------------------
# AC1 — structural linters: every answer/context sentence traces to real evidence
# ---------------------------------------------------------------------------

def _assert_answer_traces_to_statement_evidence(packet: "kpa.PacketAssembly") -> None:
    """The automated linter AC1 requires: `answer` is exactly the join of included statement
    texts, and every statement has a non-empty evidence_ids list that resolves to a real
    packet.evidence entry."""
    assert packet.answer == " ".join(s.text for s in packet.statements)
    evidence_ids = {e.evidence_id for e in packet.evidence}
    for statement in packet.statements:
        assert statement.evidence_ids, f"{statement.statement_id} has no evidence_ids"
        for evidence_id in statement.evidence_ids:
            assert evidence_id in evidence_ids, f"{evidence_id} missing from packet.evidence"


def test_every_answer_sentence_traces_to_a_real_statement_evidence_id(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search", "graphify"],
        cs_results=[_cs_result(excerpt="Deduplication should occur before truncation.")],
        graphify_result=_graphify_result(stdout="graphify traversal output line"),
    )
    assert packet.statements
    _assert_answer_traces_to_statement_evidence(packet)


def test_context_summary_sentences_also_trace_to_statements(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="UNIQUE_CTX_MARKER real retrieved excerpt text")],
    )
    statement_texts = {s.text for s in packet.statements}
    evidence_ids = {eid for s in packet.statements for eid in s.evidence_ids}
    assert packet.context
    for entry in packet.context:
        assert entry.summary in statement_texts
        assert entry.source_id in evidence_ids


# ---------------------------------------------------------------------------
# Extractive-only guard
# ---------------------------------------------------------------------------

def test_statement_text_is_a_verbatim_rendering_of_provider_excerpt_not_new_prose(monkeypatch):
    excerpt = "  The damage formula subtracts DEF from ATK, per the combat laws chapter.  "
    packet = _assemble(
        monkeypatch, providers_selected=["context_search"], cs_results=[_cs_result(excerpt=excerpt)]
    )
    assert len(packet.statements) == 1
    assert packet.statements[0].text == excerpt.strip()
    assert packet.answer == excerpt.strip()


def test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements(monkeypatch):
    packet = _assemble(
        monkeypatch, providers_selected=["context_search"], cs_results=[_cs_result()]
    )
    field_names = {f.name for f in dataclasses.fields(packet)}
    assert "raw_provider_results" not in field_names
    assert "raw" not in field_names
    for statement_field in dataclasses.fields(kpa.Statement):
        assert statement_field.name not in {"raw", "raw_result", "provider_result"}
    for context_field in dataclasses.fields(kpa.ContextEntry):
        assert context_field.name not in {"raw", "raw_result", "provider_result"}


# ---------------------------------------------------------------------------
# AC2 — NegativeClaimSupport, honestly-scoped
# ---------------------------------------------------------------------------

def test_negative_claim_rejected_when_provider_lacks_negative_knowledge_support():
    """Exercised against the REAL, frozen provider_capabilities_*.json descriptor files — both
    declare negative_knowledge_support: NONE today."""
    result = kpa.build_negative_claim_support(
        statement="Kafka is not currently used by runtime code",
        subject_ids=["kafka"],
        provider_ids=["context_search", "graphify"],
        validated_scopes=["runtime_imports", "dependency_manifests"],
    )
    assert result.verification == "UNVERIFIED"
    assert result.exclusions_or_blind_spots
    assert result.checked_at


def test_negative_claim_accepted_only_with_monkeypatched_scoped_or_complete_support(
    tmp_path, monkeypatch
):
    """No real provider today declares negative_knowledge_support != NONE (both real
    provider_capabilities_*.json files declare NONE, confirmed by the test above). This is the
    ONLY way to reach a non-UNVERIFIED verification: a monkeypatched/temp-copy descriptor. This
    branch has zero real trigger path against live provider data in Phase 1."""
    fake_path = tmp_path / "provider_capabilities_context_search.json"
    fake_path.write_text(json.dumps({
        "schema_version": 1,
        "provider_id": "context_search",
        "adapter_version": None,
        "negative_knowledge_support": "COMPLETE",
    }))
    monkeypatch.setitem(kpa._PROVIDER_CAPS_PATHS, "context_search", fake_path)

    result = kpa.build_negative_claim_support(
        statement="X is not used anywhere in this repository",
        subject_ids=["x"],
        provider_ids=["context_search"],
        validated_scopes=["runtime_imports"],
    )
    assert result.verification == "VERIFIED"


def test_negative_claim_downgrades_to_unverified_when_validated_scopes_incomplete(
    tmp_path, monkeypatch
):
    fake_path = tmp_path / "provider_capabilities_context_search.json"
    fake_path.write_text(json.dumps({
        "schema_version": 1,
        "provider_id": "context_search",
        "adapter_version": None,
        "negative_knowledge_support": "SCOPED",
    }))
    monkeypatch.setitem(kpa._PROVIDER_CAPS_PATHS, "context_search", fake_path)

    result = kpa.build_negative_claim_support(
        statement="X is not used anywhere in this repository",
        subject_ids=["x"],
        provider_ids=["context_search"],
        validated_scopes=[],
    )
    assert result.verification == "UNVERIFIED"


def test_negative_claim_carries_exclusions_or_blind_spots_and_checked_at():
    result = kpa.build_negative_claim_support(
        statement="s", subject_ids=[], provider_ids=["context_search", "graphify"]
    )
    assert result.exclusions_or_blind_spots is not None
    assert result.checked_at


# ---------------------------------------------------------------------------
# AC3 — token-budgeted assembly
# ---------------------------------------------------------------------------

def test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate():
    short = kpa.Statement("stmt-001", "short text", "FACT", ["file:a"], priority_tier=2)
    long = kpa.Statement(
        "stmt-002", "a much longer piece of text than the short statement above", "FACT",
        ["file:b"], priority_tier=2,
    )

    _, returned_short = kpa.assemble_within_budget([short], budget_requested=1000)
    _, returned_long = kpa.assemble_within_budget([long], budget_requested=1000)

    assert returned_short == kpa.kgmcp_char_heuristic_v1(short.text)
    assert returned_long == kpa.kgmcp_char_heuristic_v1(long.text)
    assert returned_long > returned_short


def test_budget_returned_never_exceeds_budget_requested():
    statements = [
        kpa.Statement(f"stmt-{i:03d}", "x" * 50, "FACT", [f"file:f{i}"], priority_tier=2)
        for i in range(5)
    ]
    _, returned = kpa.assemble_within_budget(statements, budget_requested=77)
    assert returned <= 77


def test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids(monkeypatch):
    shared_text = "Damage equals ATK minus DEF."
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search", "graphify"],
        cs_results=[_cs_result(
            source_path="docs/mechanics/02_combat_laws.md",
            heading="Damage Formula",
            excerpt=shared_text,
        )],
        graphify_result=_graphify_result(stdout=shared_text),
    )
    assert len(packet.statements) == 1
    assert len(packet.statements[0].evidence_ids) == 2


def test_deduplication_occurs_before_truncation_not_after():
    dup_a = kpa.Statement("stmt-001", "SAME TEXT", "FACT", ["file:a"], priority_tier=2)
    dup_b = kpa.Statement("stmt-002", "SAME TEXT", "FACT", ["file:b"], priority_tier=2)
    statements = [dup_a, dup_b]

    cost = kpa.kgmcp_char_heuristic_v1("SAME TEXT")
    budget = cost + max(cost // 2, 1)  # room for exactly one item's worth of cost, not two

    # Correct order: dedup first, then truncate.
    deduped = kpa.deduplicate_statements(statements)
    included_correct, _ = kpa.assemble_within_budget(deduped, budget)
    assert len(included_correct) == 1
    assert included_correct[0].evidence_ids == ["file:a", "file:b"]

    # Wrong order: truncate first (over the undeduplicated set), dedup after — this drops the
    # second evidence_id because dup_b never survives truncation to be merged.
    included_wrong_order, _ = kpa.assemble_within_budget(statements, budget)
    included_wrong_order_deduped = kpa.deduplicate_statements(included_wrong_order)
    assert included_wrong_order_deduped[0].evidence_ids == ["file:a"]

    assert included_correct[0].evidence_ids != included_wrong_order_deduped[0].evidence_ids


def _tier_statement(tier: int, n: int) -> "kpa.Statement":
    return kpa.Statement(f"stmt-{n:03d}", "X" * 20, "FACT", [f"file:{n}"], priority_tier=tier)


def test_priority_order_invariants_before_facts_before_tests_before_history():
    # Deliberately reversed input order (tier 5 first) — the sort must not depend on input order.
    statements = [_tier_statement(tier, n) for n, tier in enumerate([5, 4, 3, 2, 1], start=1)]
    cost_each = kpa.kgmcp_char_heuristic_v1("X" * 20)
    budget = cost_each * 2  # room for exactly 2 of the 5 tiers

    included, _ = kpa.assemble_within_budget(statements, budget)
    assert [s.priority_tier for s in included] == [1, 2]


# ---------------------------------------------------------------------------
# AC4 — §16 budget-assembly-failure fallback
# ---------------------------------------------------------------------------

def test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="a" * 500)],
        budget_requested=1,
    )
    assert packet.statements == []
    assert packet.status == "PARTIAL"
    assert packet.evidence
    for entry in packet.evidence:
        assert entry.evidence_id


def test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output(monkeypatch):
    excerpt = "UNIQUE_FAILURE_MARKER " + "b" * 400
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt=excerpt, source_path="docs/a.md")],
        budget_requested=1,
    )
    assert packet.answer == ""
    assert packet.context == []
    expected_hash = hashlib.sha256(excerpt.strip().encode("utf-8")).hexdigest()
    for entry in packet.evidence:
        assert entry.evidence_hash == expected_hash
        assert entry.path == "docs/a.md"


# ---------------------------------------------------------------------------
# AC5 — structural-only conflicts
# ---------------------------------------------------------------------------

def test_conflict_only_surfaces_real_supersession_metadata(monkeypatch):
    old = _cs_result(
        source_path="docs/a.md", heading="X", excerpt="old value",
        superseded_by="docs/b.md",
    )
    new = _cs_result(
        source_path="docs/b.md", heading="Y", excerpt="new value",
        supersedes="docs/a.md",
    )
    packet = _assemble(monkeypatch, providers_selected=["context_search"], cs_results=[old, new])
    assert len(packet.conflicts) == 1
    assert packet.conflicts[0].subject == "docs/a.md vs docs/b.md"
    assert {c.source_id for c in packet.conflicts[0].claims} == {"docs/a.md", "docs/b.md"}


def test_conflicts_never_populated_from_bare_topical_similarity(monkeypatch):
    a = _cs_result(source_path="docs/a.md", heading="X", excerpt="Damage uses ATK and DEF")
    b = _cs_result(source_path="docs/b.md", heading="Y", excerpt="Damage also uses ATK and DEF")
    packet = _assemble(monkeypatch, providers_selected=["context_search"], cs_results=[a, b])
    assert packet.conflicts == []


# ---------------------------------------------------------------------------
# §13 ephemeral-only classification / no durable persistence
# ---------------------------------------------------------------------------

def test_statement_classification_is_ephemeral_not_persisted(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="ephemeral classification marker text")],
    )
    assert packet.statements[0].classification in {"FACT", "INFERENCE", "DECISION"}

    tree = ast.parse(_MODULE_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            for arg in list(node.args)[1:] + [kw.value for kw in node.keywords if kw.arg == "mode"]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    assert "w" not in arg.value, "found a write-mode open() in the packet-assembly module"

    source = _MODULE_PATH.read_text()
    for forbidden in ("yaml.safe_dump", "yaml.dump(", ".write_text(", "json.dump("):
        assert forbidden not in source, f"found durable-write call `{forbidden}` in packet-assembly module"


# ---------------------------------------------------------------------------
# Evidence-identity-kind reuse guard
# ---------------------------------------------------------------------------

_CLOSED_EVIDENCE_ID_PREFIXES = (
    "doc:", "file:", "symbol:", "ticket:", "parity:", "registry:", "generation:",
)


def test_evidence_id_uses_closed_evidence_identity_kind_form(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search", "graphify"],
        cs_results=[_cs_result(source_path="docs/plans/knowledge-gateway-mcp-proposal.md")],
        graphify_result=_graphify_result(),
    )
    assert packet.evidence
    for entry in packet.evidence:
        assert entry.evidence_id.startswith(_CLOSED_EVIDENCE_ID_PREFIXES), entry.evidence_id


def test_evidence_id_disambiguates_duplicate_anchor_within_same_document(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="Overview", excerpt="first excerpt", doc_id="d1"),
            _cs_result(source_path="docs/a.md", heading="Overview", excerpt="second excerpt", doc_id="d2"),
        ],
    )
    evidence_ids = [s.evidence_ids[0] for s in packet.statements]
    assert evidence_ids[0] == "doc:docs/a.md#overview"
    assert evidence_ids[1] == "doc:docs/a.md#overview-2"


def test_evidence_id_for_ticket_source_path_uses_ticket_kind(monkeypatch):
    real_ticket = next(iter((_REPO_ROOT / "tickets" / "done").glob("TCK-*.md")))
    ticket_relpath = f"tickets/done/{real_ticket.name}"
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(source_path=ticket_relpath, heading="")],
    )
    assert packet.statements[0].evidence_ids[0] == f"ticket:{real_ticket.stem}"


def test_evidence_id_for_non_doc_non_ticket_path_uses_file_kind(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(source_path="tools/search_mcp.py", heading="")],
    )
    assert packet.statements[0].evidence_ids[0] == "file:tools/search_mcp.py"


# ---------------------------------------------------------------------------
# Out-of-scope architecture guards
# ---------------------------------------------------------------------------

def test_module_not_referenced_by_any_claude_workflows_file():
    workflows_dir = _REPO_ROOT / ".claude" / "workflows"
    js_files = list(workflows_dir.glob("*.js"))
    assert js_files, "expected at least one .claude/workflows/*.js file to scan"
    for js_file in js_files:
        assert "knowledge_gateway_packet_assembly" not in js_file.read_text()


def test_module_introduces_zero_mcp_server_code():
    """`.mcp.json` now legitimately carries a `knowledge-gateway` entry
    (TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE) — updated in the same change per that ticket's own
    Regression Surface note. This packet-assembly module itself must still never define the live
    `knowledge_context`/`knowledge_status` tool functions — that half of the guard is unchanged."""
    source = _MODULE_PATH.read_text()
    assert "def knowledge_context(" not in source
    assert "def knowledge_status(" not in source
    assert "FastMCP" not in source
    assert "server.tool()" not in source

    mcp_config = json.loads((_REPO_ROOT / ".mcp.json").read_text())
    assert set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github", "knowledge-gateway"}


def test_module_does_not_modify_or_import_retrieval_cache():
    source = _MODULE_PATH.read_text()
    assert "retrieval_cache" not in source
    assert "sqlite3" not in source


# ---------------------------------------------------------------------------
# TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT — Gap 1: content-hash dedup identity
# ---------------------------------------------------------------------------

def test_dedup_identity_uses_content_hash_not_casefold_normalization(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="X", excerpt="Damage Equals ATK Minus DEF."),
            _cs_result(source_path="docs/b.md", heading="Y", excerpt="damage equals atk minus def."),
        ],
    )
    # A regression to the old casefold key would collapse these two into one statement.
    assert len(packet.statements) == 2


def test_dedup_collapses_only_on_exact_content_hash_match_across_providers(monkeypatch):
    shared_text = "Damage equals ATK minus DEF."
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search", "graphify"],
        cs_results=[_cs_result(
            source_path="docs/mechanics/02_combat_laws.md",
            heading="Damage Formula",
            excerpt=shared_text,
        )],
        graphify_result=_graphify_result(stdout=shared_text),
    )
    assert len(packet.statements) == 1
    assert len(packet.statements[0].evidence_ids) == 2
    assert kpa._dedup_key(packet.statements[0]) == hashlib.sha256(
        shared_text.strip().encode("utf-8")
    ).hexdigest()


def test_dedup_key_is_stricter_than_semantic_similarity_no_fuzzy_merge(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="X", excerpt="Damage equals ATK minus DEF."),
            _cs_result(
                source_path="docs/b.md", heading="Y",
                excerpt="Damage equals ATK minus DEF plus bonus.",
            ),
        ],
    )
    assert len(packet.statements) == 2


def test_no_semantic_or_embedding_dependency_introduced():
    """Mirrors test_statement_classification_is_ephemeral_not_persisted's AST-walk pattern —
    catches silent Phase-5-scope creep (semantic/fuzzy dedup) into this Phase-3 ticket. Walks
    only real import statements (not docstrings, which already legitimately discuss the
    embedding/similarity boundary in prose)."""
    tree = ast.parse(_MODULE_PATH.read_text())
    forbidden_modules = {
        "sentence_transformers", "sklearn", "tiktoken", "difflib", "numpy", "scipy",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & forbidden_modules), imported & forbidden_modules


def test_evidence_hash_and_dedup_key_share_single_content_hash_helper(monkeypatch):
    stub_calls: list[str] = []

    def _stub_content_hash(text: str) -> str:
        stub_calls.append(text)
        return f"STUBBED::{text.strip()}"

    monkeypatch.setattr(kpa, "_content_hash", _stub_content_hash)

    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="single source of truth marker text")],
    )
    assert packet.evidence[0].evidence_hash == "STUBBED::single source of truth marker text"

    directly_constructed = kpa.Statement(
        "stmt-999", "single source of truth marker text", "FACT", ["file:x"],
        priority_tier=2, evidence_hash=None,
    )
    assert kpa._dedup_key(directly_constructed) == "STUBBED::single source of truth marker text"
    assert stub_calls, "expected _content_hash() to actually be called by both code paths"


# ---------------------------------------------------------------------------
# TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT — Gap 2/AC4: dedup-vs-conflict guard
# ---------------------------------------------------------------------------

def test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text(monkeypatch):
    shared_text = "identical restated sentence"
    old = _cs_result(
        source_path="docs/a.md", heading="X", excerpt=shared_text,
        superseded_by="docs/b.md",
    )
    new = _cs_result(
        source_path="docs/b.md", heading="Y", excerpt=shared_text,
        supersedes="docs/a.md",
    )
    packet = _assemble(monkeypatch, providers_selected=["context_search"], cs_results=[old, new])

    assert len(packet.statements) == 2
    assert len(packet.conflicts) == 1
    assert packet.status == "CONFLICTED"


def test_conflicting_claims_with_different_text_still_never_merge_and_pass_through_dedup(monkeypatch):
    old = _cs_result(
        source_path="docs/a.md", heading="X", excerpt="old value",
        superseded_by="docs/b.md",
    )
    new = _cs_result(
        source_path="docs/b.md", heading="Y", excerpt="new value",
        supersedes="docs/a.md",
    )
    packet = _assemble(monkeypatch, providers_selected=["context_search"], cs_results=[old, new])

    assert len(packet.statements) == 2
    assert len(packet.conflicts) == 1


def test_conflict_index_pairs_correspondence_invariant_raises_on_desync(monkeypatch):
    """Deliberately desyncs render_candidates()'s statement cardinality from provider_results so
    the Step 4 cardinality assertion in assemble_packet() must raise, proving the desync fails
    loudly rather than silently letting AC4's conflict-vs-dedup exclusion misfire."""
    real_render_candidates = kpa.render_candidates

    def _desynced_render_candidates(provider_results, query_text):
        statements, context_entries, evidence_entries = real_render_candidates(
            provider_results, query_text
        )
        extra = dataclasses.replace(
            statements[0], statement_id="stmt-extra", text="not backed by any provider result"
        )
        return [*statements, extra], context_entries, evidence_entries

    monkeypatch.setattr(kpa, "render_candidates", _desynced_render_candidates)

    with pytest.raises(AssertionError):
        _assemble(
            monkeypatch,
            providers_selected=["context_search"],
            cs_results=[_cs_result(excerpt="real single provider result")],
        )


# ---------------------------------------------------------------------------
# TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT — Gap 3/AC2/AC3: budget-truncation marker
# ---------------------------------------------------------------------------

def test_budget_truncation_produces_visible_marker_when_content_is_dropped(monkeypatch):
    text_a = "first statement text that costs some real budget"
    text_b = "second statement text that costs additional real budget beyond the first"
    cost_a = kpa.kgmcp_char_heuristic_v1(text_a.strip())
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="A", excerpt=text_a),
            _cs_result(source_path="docs/b.md", heading="B", excerpt=text_b),
        ],
        budget_requested=cost_a,
    )
    assert packet.budget_truncated is True
    assert packet.omitted_statement_count == 1


def test_no_budget_truncation_marker_is_false_and_present_when_everything_fits(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="small statement that fits comfortably in the budget")],
        budget_requested=10_000,
    )
    assert packet.budget_truncated is False
    assert packet.omitted_statement_count == 0


def test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(excerpt="a" * 500)],
        budget_requested=1,
    )
    assert packet.statements == []
    assert packet.budget_truncated is True
    assert packet.omitted_statement_count == 1


# ---------------------------------------------------------------------------
# evidence_dependencies (TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION, plan.md DD1)
# ---------------------------------------------------------------------------

def test_evidence_dependencies_aggregated_from_packet_evidence_paths(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="A", excerpt="statement about a"),
            _cs_result(source_path="docs/b.md", heading="B", excerpt="statement about b"),
        ],
    )
    assert packet.evidence_dependencies == ["docs/a.md", "docs/b.md"]


def test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements(monkeypatch):
    text_a = "first statement text that costs some real budget"
    text_b = "second statement text that costs additional real budget beyond the first"
    cost_a = kpa.kgmcp_char_heuristic_v1(text_a.strip())
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[
            _cs_result(source_path="docs/a.md", heading="A", excerpt=text_a),
            _cs_result(source_path="docs/b.md", heading="B", excerpt=text_b),
        ],
        budget_requested=cost_a,
    )
    assert packet.budget_truncated is True
    assert packet.evidence_dependencies == ["docs/a.md"]
    assert "docs/b.md" not in packet.evidence_dependencies


def test_evidence_dependencies_omits_graphify_symbol_evidence_with_no_path(monkeypatch):
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search", "graphify"],
        cs_results=[_cs_result(source_path="docs/a.md", heading="A", excerpt="statement about a")],
        graphify_result=_graphify_result(),
    )
    assert any(entry.path is None for entry in packet.evidence)
    assert packet.evidence_dependencies == ["docs/a.md"]
    assert None not in packet.evidence_dependencies
    assert "None" not in packet.evidence_dependencies


def test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_evidence(
    monkeypatch,
):
    """DD1's own correction test — the section-16 budget-assembly-failure branch leaves
    `final_evidence` (packet.evidence) as the full, unfiltered evidence_entries list, but
    `final_context` (and therefore evidence_dependencies) must be empty in that branch, matching
    the packet's own empty answer/statements. Asserting evidence_dependencies == [] here, while
    packet.evidence is non-empty, is the direct proof that evidence_dependencies is aggregated
    from final_context and not final_evidence."""
    packet = _assemble(
        monkeypatch,
        providers_selected=["context_search"],
        cs_results=[_cs_result(source_path="docs/a.md", excerpt="a" * 500)],
        budget_requested=1,
    )
    assert packet.statements == []
    assert packet.context == []
    assert packet.evidence  # final_evidence deliberately left unfiltered on this branch
    assert packet.evidence_dependencies == []


# ---------------------------------------------------------------------------
# TCK-20260816-KGMCP-P4-PARITY-ADAPTER: real end-to-end parity_ledger provider dispatch
# ---------------------------------------------------------------------------

_PARITY_LEDGER_DIR = _REPO_ROOT / "docs" / "parity_ledger"


def test_parity_id_query_reaches_real_entry_lookup_end_to_end(tmp_path, monkeypatch):
    """Resolves investigation.md Risk 1: drives call_providers_for_routing_decision() -- the real
    per-call provider-dispatch layer every live _run_knowledge_context() call goes through --
    directly against a real, freshly-built parity index. Never monkeypatches tools.parity_index's
    entry()/check_staleness() themselves, only the module-level DEFAULT_DB_PATH constant so the
    real build()/entry() code runs against test-isolated state instead of a developer's real
    parity-index/parity.db.
    """
    kgr_mod = kpa._load_router_module()
    pidx = kgr_mod._load_parity_index_module()
    db_path = tmp_path / "parity.db"
    build_report = pidx.build(ledger_dir=_PARITY_LEDGER_DIR, db_path=db_path)
    assert build_report["status"] == "ok"
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", db_path)

    decision = SimpleNamespace(providers_selected=["parity_ledger"])
    results = kpa.call_providers_for_routing_decision(decision, "INFRA-349")

    assert results["parity_ledger"] is not None
    assert results["parity_ledger"]["results"]["found"] is True
    assert results["parity_ledger"]["results"]["record"]["id"] == "INFRA-349"
    assert results["failures"] == []


def test_missing_parity_index_fails_open_not_crash(tmp_path, monkeypatch):
    kgr_mod = kpa._load_router_module()
    pidx = kgr_mod._load_parity_index_module()
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", tmp_path / "does_not_exist" / "parity.db")

    decision = SimpleNamespace(providers_selected=["parity_ledger"])
    results = kpa.call_providers_for_routing_decision(decision, "INFRA-349")

    assert results["parity_ledger"] is None
    assert results["failures"]
    assert "parity_ledger: index not built" in results["failures"][0]


def test_free_text_requirement_completeness_query_uses_context_search_and_does_not_error_on_parity(
    tmp_path, monkeypatch
):
    """Gap-check (Architecture-Verify follow-up): `ROUTING_TABLE["requirement_completeness_verification"]`
    has BOTH `context_search` and `parity_ledger` as primary providers, so a free-text (non-parity-ID
    -shaped) query classified into this row -- e.g. the real corpus query text for
    `Q3_requirement_completeness` in `tools/agent-monitoring/kgmcp_baseline_corpus.py` -- still
    dispatches to `parity_ledger`. This proves that co-primary dispatch: (1) context_search still
    returns its own real results untouched, (2) the parity adapter receives the raw free-text query
    as the literal entry_id (per `_run_parity_provider()`'s own documented Design Decision D1),
    genuinely calls the real `tools/parity_index.py::entry()` against a real, freshly-built index,
    and returns `found: False` for the whole sentence -- and (3) this is real provider behavior, not
    an error: it must never land in `results["failures"]`."""
    kgr_mod = kpa._load_router_module()
    pidx = kgr_mod._load_parity_index_module()
    db_path = tmp_path / "parity.db"
    build_report = pidx.build(ledger_dir=_PARITY_LEDGER_DIR, db_path=db_path)
    assert build_report["status"] == "ok"
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", db_path)

    sm_mod = kpa._load_search_mcp_module()
    real_cs_results = [_cs_result(excerpt="Q3 free-text requirement-completeness real result")]
    monkeypatch.setattr(sm_mod, "_run_search", lambda q: real_cs_results)

    free_text_query = "Is the read_count_correlation feature fully implemented?"
    decision = SimpleNamespace(providers_selected=["context_search", "parity_ledger"])
    results = kpa.call_providers_for_routing_decision(decision, free_text_query)

    assert results["failures"] == [], (
        "a free-text query genuinely not existing as a parity entry ID is real provider "
        "behavior (found: False), never a failure"
    )
    assert results["context_search"] == real_cs_results

    assert results["parity_ledger"] is not None
    assert results["parity_ledger"]["results"]["found"] is False
    assert results["parity_ledger"]["results"]["entry_id"] == free_text_query


def test_module_does_not_edit_knowledge_gateway_router():
    """`tools/knowledge_gateway_router.py` is untracked in this working tree (its own ticket has
    not yet been committed), so a `git diff HEAD` check would be a silent no-op regardless of
    whether this ticket edited it. Per plan.md's own documented alternative, the robust signal is
    that the router's real test suite still passes unmodified."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/tools/test_knowledge_gateway_router.py", "-q"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
