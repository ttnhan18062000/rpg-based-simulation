"""Tests for tools/knowledge_gateway_cache.py — the Level 1 provider-result cache orchestration
module (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING).

Full end-to-end integration coverage (a genuine cache hit skipping `_run_search()`, branch
partitioning, real corpus_generation invalidation, the redaction write-path gate, and
`knowledge_status`'s real cache-domain fields) lives in `tests/tools/test_knowledge_gateway_mcp.py`,
which already exercises the real `_run_knowledge_context()`/`_run_knowledge_status()` entry points.
This file covers this module's own pure-function/orchestration units in isolation, plus the
structural architecture guards this ticket's plan requires.

SYMBOL/FILE-kind evidence-fingerprint revalidation cannot be exercised against real live provider
data today — both real `provider_capabilities_*.json` descriptors report
`fine_grained_fingerprints: false` (confirmed directly below). The two tests covering that path are
explicitly fixture-based and labeled as such, mirroring
`tests/tools/test_evidence_cache_identity_contract.py`'s own Phase 0 fixture-based pattern and
`tools/knowledge_gateway_packet_assembly.py`'s own "Honesty notes" disclosure precedent — never
presented as an end-to-end real-provider test.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_CACHE_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_cache.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_cache_module():
    spec = importlib.util.spec_from_file_location("knowledge_gateway_cache_test", _CACHE_MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_gateway_cache_test"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_cache_module()


@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    from tools import retrieval_cache as rc

    monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")
    monkeypatch.setattr(rc, "_MANIFEST_PATH", tmp_path / "manifest.json")
    yield


# ---------------------------------------------------------------------------
# Step 1 — module docstring + budget-class boundaries
# ---------------------------------------------------------------------------

def test_module_docstring_states_non_collapse_and_orchestration_role():
    normalized = " ".join(_mod.__doc__.split())
    assert "orchestrat" in normalized.lower()
    assert "genuinely separate" in normalized or "separate steps" in normalized


def test_compute_budget_class_small_medium_large_boundaries():
    assert _mod.compute_budget_class(1) == "small"
    assert _mod.compute_budget_class(500) == "small"
    assert _mod.compute_budget_class(501) == "medium"
    assert _mod.compute_budget_class(2000) == "medium"
    assert _mod.compute_budget_class(2001) == "large"
    assert _mod.compute_budget_class(100000) == "large"


# ---------------------------------------------------------------------------
# Step 5 — lookup identity (§1)
# ---------------------------------------------------------------------------

def test_compute_resolved_entity_ids_maps_all_five_closed_forms():
    cases = [
        ("ticket_id", "TCK-1", "ticket:TCK-1"),
        ("parity_id", "COMBAT-1", "parity:COMBAT-1"),
        ("registered_doc_path", "docs/foo.md", "doc:docs/foo.md"),
        ("subsystem_id", "combat", "subsystem:combat"),
        ("symbol_name", "some_symbol", "symbol:some_symbol"),
    ]
    for category, value, expected in cases:
        decision = SimpleNamespace(matched_identifier=SimpleNamespace(category=category, value=value))
        assert _mod.compute_resolved_entity_ids(decision) == [expected]


def test_compute_resolved_entity_ids_empty_for_source_path_match():
    """DD6 — source_path has no closed form in evidence_cache_identity_contract.md §1; this is a
    real, frozen-contract limitation, not an oversight to patch with an invented 6th form."""
    decision = SimpleNamespace(
        matched_identifier=SimpleNamespace(category="source_path", value="tools/foo.py")
    )
    assert _mod.compute_resolved_entity_ids(decision) == []


def test_compute_resolved_entity_ids_empty_for_ambiguous_fallback():
    decision = SimpleNamespace(matched_identifier=None)
    assert _mod.compute_resolved_entity_ids(decision) == []


def test_compute_lookup_identity_filters_excludes_budget_tokens_and_changed_paths():
    """DD8 — budget_tokens maps only to budget_class; changed_paths is a separate identity axis
    (§5), neither ever leaks into the filters field."""
    request = {
        "query": "what is X",
        "mode": "answer",
        "budget_tokens": 999,
        "changed_paths": ["tools/foo.py"],
        "include_history": True,
        "evidence_detail": "summary",
    }
    decision = SimpleNamespace(matched_identifier=None)
    identity = _mod.compute_lookup_identity(request, decision, 4000)
    filters = json.loads(identity["filters_json"])
    assert filters == {"mode": "answer", "include_history": True, "evidence_detail": "summary"}
    assert "budget_tokens" not in identity["filters_json"]
    assert "changed_paths" not in identity["filters_json"]


def test_compute_lookup_identity_query_hash_matches_retrieval_cache_normalization():
    from tools import retrieval_cache as rc

    request = {"query": "  What IS   the Damage Formula  "}
    decision = SimpleNamespace(matched_identifier=None)
    identity = _mod.compute_lookup_identity(request, decision, 4000)
    expected_hash = rc._hash_text(rc._normalize_query(request["query"]))
    assert identity["query_hash"] == expected_hash
    assert identity["normalized_intent"] == rc._normalize_query(request["query"])


def test_compute_lookup_identity_repo_branch_scope_is_a_real_git_read():
    request = {"query": "some query"}
    decision = SimpleNamespace(matched_identifier=None)
    identity = _mod.compute_lookup_identity(request, decision, 4000)
    assert "::" in identity["repo_branch_scope"]
    assert identity["routing_policy_version"] == _mod.ROUTING_POLICY_VERSION


# ---------------------------------------------------------------------------
# Step 6 — §4 provider-generation fallback rule (AC3)
# ---------------------------------------------------------------------------

def test_provider_generation_fallback_used_for_both_real_providers_today():
    context_search_caps = json.loads(
        (_CONTRACTS_DIR / "provider_capabilities_context_search.json").read_text()
    )
    graphify_caps = json.loads((_CONTRACTS_DIR / "provider_capabilities_graphify.json").read_text())

    assert context_search_caps["fine_grained_fingerprints"] is False
    assert graphify_caps["fine_grained_fingerprints"] is False

    assert _mod.select_validation_basis(context_search_caps) == "PROVIDER_GENERATION"
    assert _mod.select_validation_basis(graphify_caps) == "PROVIDER_GENERATION"


def test_finer_fingerprint_preferred_over_provider_generation_when_capability_advertises_it():
    """Fixture-based: neither real provider descriptor advertises fine_grained_fingerprints today
    (confirmed above), so this asserts the *other* half of AC3 (never the default path when finer
    evidence IS available) against a constructed descriptor, mirroring
    tests/tools/test_knowledge_gateway_packet_assembly.py's own monkeypatched-capability
    precedent."""
    descriptor = {"fine_grained_fingerprints": True}
    assert _mod.select_validation_basis(descriptor) == "FINER"


def test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture():
    """Fixture-based (investigation.md Risks item 2) — no real live provider capability descriptor
    advertises fine_grained_fingerprints today, so this directly constructs a SYMBOL-backed row and
    revalidates it with a capability descriptor that DOES advertise finer fingerprints, proving
    rejection is driven by the fingerprint mismatch alone, never a generation comparison."""
    row = {
        "working_tree_overlap": "[]",
        "evidence_fingerprints": "symbol:some_module.some_func@hash-a",
        "provider_generation_at_validation": "gen-1",
    }
    valid = _mod.revalidate_cache_row(
        row, capability_descriptor={"fine_grained_fingerprints": True},
        current_provider_generation="gen-1",
        current_evidence_fingerprint="symbol:some_module.some_func@hash-b",
        changed_paths=[],
    )
    assert valid is False


def test_symbol_backed_cache_row_survives_unrelated_generation_bump_fixture():
    """Fixture-based (investigation.md Risks item 2) — the §4 hard rule: a SYMBOL/FILE-backed row
    must never be invalidated by a bare PROVIDER_GENERATION bump alone. This is the real path
    exercisable today (both real providers only ever report PROVIDER_GENERATION-basis), so this
    asserts the row survives purely because its evidence_fingerprints kind is protected."""
    row = {
        "working_tree_overlap": "[]",
        "evidence_fingerprints": "symbol:some_module.some_func@hash-a",
        "provider_generation_at_validation": "gen-1",
    }
    valid = _mod.revalidate_cache_row(
        row, capability_descriptor={"fine_grained_fingerprints": False},
        current_provider_generation="gen-2",  # bumped, unrelated to the symbol's own fingerprint
        current_evidence_fingerprint=None,
        changed_paths=[],
    )
    assert valid is True


def test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash():
    assert _mod.working_tree_overlap_forces_revalidation(
        json.dumps(["docs/foo.md", "docs/bar.md"]), ["src/unrelated.py"]
    ) is False
    assert _mod.working_tree_overlap_forces_revalidation(
        json.dumps(["docs/foo.md", "docs/bar.md"]), ["docs/foo.md"]
    ) is True


def test_is_branch_compatible_hard_partition():
    assert _mod.is_branch_compatible("repo::main", "repo::main") is True
    assert _mod.is_branch_compatible("repo::feature-x", "repo::main") is False


# ---------------------------------------------------------------------------
# Step 2/Step 7 — Non-collapse rule structural guard (§3/DD9)
# ---------------------------------------------------------------------------

def test_lookup_function_never_returns_a_freshness_or_verification_field():
    from tools import retrieval_cache as rc
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(rc.ProviderResultCacheLookup)}
    assert "freshness" not in field_names
    assert "verification" not in field_names


# ---------------------------------------------------------------------------
# Architecture guards
# ---------------------------------------------------------------------------

def test_module_does_not_import_knowledge_gateway_router_or_packet_assembly():
    """AST-based (not a blind substring ban) — this module's own docstring legitimately *names*
    `tools/knowledge_gateway_router.py`/`tools/knowledge_gateway_packet_assembly.py` in prose to
    explain they are untouched Out-of-Scope dependencies; only a real `import`/`from ... import`
    statement naming either module would be a violation."""
    source = _CACHE_MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert "tools.knowledge_gateway_router" not in imported_modules
    assert "tools.knowledge_gateway_packet_assembly" not in imported_modules
    assert "knowledge_gateway_router" not in imported_modules
    assert "knowledge_gateway_packet_assembly" not in imported_modules


def test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module():
    """AC5's 'no raw/unredacted write path exists anywhere' guard, adapted for DD2's call-site
    split (the literal INSERT SQL text lives in tools/retrieval_cache.py, not in this module —
    plan.md Step 8's own documented refinement). Statically confirms:
    1. tools/knowledge_gateway_cache.py itself contains no literal SQL INSERT text of its own.
    2. rc.write_provider_result_cache() is called from exactly one place across tools/*.py:
       perform_cache_write() in tools/knowledge_gateway_cache.py.
    3. Inside perform_cache_write(), the call to evaluate_write_candidate() precedes the call to
       write_provider_result_cache() in source order, with an intervening ALLOW-gated early return
       — never an unconditional write.
    """
    cache_source = _CACHE_MODULE_PATH.read_text()
    # Not a blind "INSERT" substring ban — this module's own docstring legitimately discusses
    # `INSERT OR REPLACE`/`SELECT`/`UPDATE` in prose to explain where the real SQL lives (DD2).
    # The real guarantee: this module never calls sqlite3 or .execute(...) directly at all.
    assert ".execute(" not in cache_source
    assert "sqlite3" not in cache_source

    call_sites = []
    for py_file in sorted(_TOOLS_DIR.glob("*.py")):
        text = py_file.read_text()
        if "write_provider_result_cache(" in text:
            call_sites.append(py_file.name)
    assert call_sites == ["knowledge_gateway_cache.py", "retrieval_cache.py"], (
        f"write_provider_result_cache must be defined in retrieval_cache.py and called only from "
        f"knowledge_gateway_cache.py's perform_cache_write(); found: {call_sites}"
    )

    tree = ast.parse(cache_source)
    perform_cache_write_node = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "perform_cache_write"
    )
    func_source = ast.get_source_segment(cache_source, perform_cache_write_node)
    eval_index = func_source.index("evaluate_write_candidate(")
    write_index = func_source.index("write_provider_result_cache(")
    assert eval_index < write_index, (
        "evaluate_write_candidate() must be called before write_provider_result_cache()"
    )
    between = func_source[eval_index:write_index]
    assert "decision.verdict" in between and "return" in between, (
        "there must be a decision.verdict-gated early return between the redaction check and the "
        "real write — never an unconditional call"
    )


def test_migration_001_still_never_called_from_the_original_six_check_or_write_functions():
    import inspect
    from tools import retrieval_cache as rc

    hot_path_functions = [
        rc.check_index_cache, rc.check_query_cache, rc.check_packet_cache,
        rc.write_index_cache, rc.write_query_cache, rc.write_packet_cache,
    ]
    for func in hot_path_functions:
        assert "migration_001" not in inspect.getsource(func)


# ---------------------------------------------------------------------------
# Step 8 — perform_cache_write() integration coverage
#
# Architecture-Verify gap fix (post-Implement): plan.md's own Step 8 Verify list names both tests
# below, but the original Implement pass only exercised the two write-path gates
# (acquire_write_guard/check_db_size_within_limit) indirectly, or as bare-primitive unit tests in
# tests/tools/test_knowledge_gateway_redaction.py. Both tests here call the real orchestrator,
# perform_cache_write() itself, per plan.md's explicit instruction ("re-run against the real
# orchestrator, not just knowledge_gateway_redaction.py's own unit test of the guard primitive").
# ---------------------------------------------------------------------------

def _perform_cache_write_fixture_args():
    """Shared request/routing_decision/response shape for both tests below — a plain, ALLOW-eligible
    response (no secrets, no never-cache-category content, well under the 8 KB size cap) so the only
    variable under test is the stampede guard / size-cap gate itself, not evaluate_write_candidate's
    own verdict."""
    request = {"query": "perform_cache_write integration fixture query"}
    routing_decision = SimpleNamespace(matched_identifier=None)
    response = {
        "status": "OK",
        "providers_consulted_this_call": ["graphify"],
        "context": [],
        "answer": "perform_cache_write integration fixture answer",
    }
    return request, routing_decision, response


def test_per_key_stampede_guard_prevents_concurrent_duplicate_write():
    """Calls the real perform_cache_write() orchestrator from two threads for the exact same cache
    key. The first call is deliberately held inside its write step (via a blocking mock on
    rc.write_provider_result_cache, entered only after the real acquire_write_guard() succeeded
    inside perform_cache_write()); the second call is started only once we know the first is inside
    the critical section, so its own rk.acquire_write_guard() call inside perform_cache_write() must
    genuinely observe the lock as held and return without ever reaching
    rc.write_provider_result_cache() — proving the guard is enforced by the real orchestrator, not
    just the bare acquire_write_guard/release_write_guard primitives in isolation."""
    import threading

    from tools import retrieval_cache as rc

    write_calls = []
    entered_write = threading.Event()
    release_write = threading.Event()

    def _blocking_write(**kwargs):
        write_calls.append(kwargs)
        entered_write.set()
        release_write.wait(timeout=5)

    original_write = rc.write_provider_result_cache
    rc.write_provider_result_cache = _blocking_write
    try:
        request, routing_decision, response = _perform_cache_write_fixture_args()

        def _call():
            _mod.perform_cache_write(request, routing_decision, dict(response), 4000)

        first = threading.Thread(target=_call)
        first.start()
        assert entered_write.wait(timeout=5), "first call never reached the real write step"

        second = threading.Thread(target=_call)
        second.start()
        second.join(timeout=5)
        assert not second.is_alive(), "second call did not return promptly — guard did not skip it"

        release_write.set()
        first.join(timeout=5)

        assert len(write_calls) == 1, (
            "the per-key stampede guard must prevent a second concurrent perform_cache_write() call "
            "for the same cache key from ever reaching the real write"
        )
    finally:
        rc.write_provider_result_cache = original_write


def test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling():
    """Directly exercises the `if not rk.check_db_size_within_limit(rc.CACHE_DB_PATH): return`
    branch inside perform_cache_write() (tools/knowledge_gateway_cache.py:289-290) — the branch had
    no test anywhere prior to this fix. Mocks rk.check_db_size_within_limit (the real boundary
    perform_cache_write() calls through) to return False, rather than actually growing a real DB
    file to the 256 MB SQLITE_MAX_DB_SIZE_BYTES ceiling. Confirms the write is skipped cleanly (no
    raise, no call to the real write function) while still allowing the live result to have already
    been returned to the caller — this gate only skips the cache write, never the response."""
    from tools import knowledge_gateway_redaction as rk
    from tools import retrieval_cache as rc

    write_calls = []
    original_write = rc.write_provider_result_cache
    original_check = rk.check_db_size_within_limit
    rc.write_provider_result_cache = lambda **kwargs: write_calls.append(kwargs)
    rk.check_db_size_within_limit = lambda db_path: False
    try:
        request, routing_decision, response = _perform_cache_write_fixture_args()

        result = _mod.perform_cache_write(request, routing_decision, response, 4000)

        assert result is None
        assert write_calls == [], (
            "write_provider_result_cache must never be called once check_db_size_within_limit "
            "reports the DB is over the ceiling"
        )
    finally:
        rc.write_provider_result_cache = original_write
        rk.check_db_size_within_limit = original_check
