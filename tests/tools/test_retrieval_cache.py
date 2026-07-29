"""Tests for tools/retrieval_cache.py — 3-level SQLite retrieval cache.

Built for TCK-20260729-RETRIEVAL-CACHE-LEVELS. No live ML dependencies required — cache
read/write/invalidation logic has no ML dependency itself, following the dependency-free-by-
default pattern established by tests/tools/test_hybrid_retrieval.py.

Duration-is-not-behavior guard: no test in this file may assert that a row is evicted strictly
because 30/7/14 days elapsed. Every invalidation test (AC1-AC3) constructs its stale condition via
a hash/version mismatch only. The three `test_prune_*` tests are the sole exception permitted by
this ticket's plan (Resolved Decision 5) — they seed an explicit past `created_at` value on a row
and assert a count before/after, with no clock mocking and no elapsed-day precision assertion
against the primary hash/version-mismatch invalidation path.
"""

from __future__ import annotations

import ast
import inspect
import json
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import retrieval_cache as rc  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")
    monkeypatch.setattr(rc, "_MANIFEST_PATH", tmp_path / "manifest.json")
    yield


def _write_manifest(tmp_path: Path, built_at: str) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"version": 1, "built_at": built_at, "paths": {}})
    )


# ---------------------------------------------------------------------------
# AC1 — Embedding/index cache
# ---------------------------------------------------------------------------

class TestIndexCache:
    def test_hit_on_unchanged_content_hash_and_chunking_version(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        result = rc.check_index_cache("hash-a", "emb-v1", "chunk-v1")
        assert result.status == rc.HIT

    def test_recompute_on_content_hash_change(self):
        # A changed content_hash is a different composite key entirely (the hash *is* the
        # content's identity) -- recompute is proven by the new key missing. Stale-row eviction
        # (per the plan's Step 2) is scoped to same-content_hash-different-version, exercised by
        # test_recompute_on_chunking_version_change below; the old hash's row legitimately
        # remains a valid cache entry for that old content under its own key.
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        result = rc.check_index_cache("hash-b", "emb-v1", "chunk-v1")
        assert result.status == rc.MISS

        rc.write_index_cache("hash-b", "emb-v1", "chunk-v1", source_id="doc-1")
        result = rc.check_index_cache("hash-b", "emb-v1", "chunk-v1")
        assert result.status == rc.HIT

    def test_recompute_on_chunking_version_change(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        result = rc.check_index_cache("hash-a", "emb-v1", "chunk-v2")
        assert result.status == rc.MISS

        rc.write_index_cache("hash-a", "emb-v1", "chunk-v2", source_id="doc-1")
        conn = rc._get_connection()
        try:
            rows = conn.execute(
                "SELECT chunking_version FROM retrieval_index_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("chunk-v2",)]

    def test_category_name_is_retrieval_index_cache(self):
        assert rc.INDEX_CACHE_CATEGORY == "retrieval_index_cache"


# ---------------------------------------------------------------------------
# AC2 — Query-result cache
# ---------------------------------------------------------------------------

class TestQueryCache:
    def test_hit_on_identical_query_filters_and_versions(self):
        rc.write_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1, score=0.9)
        result = rc.check_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1)
        assert result.status == rc.HIT

    def test_stale_reject_on_corpus_generation_change(self):
        rc.write_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1, score=0.9)
        result = rc.check_query_cache("player fatigue", {"top_k": 5}, "gen-2", 1)
        assert result.status == rc.STALE_REJECTED
        assert result.reason_code == "corpus_generation_mismatch"

    def test_stale_reject_on_retrieval_version_change(self):
        rc.write_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1, score=0.9)
        result = rc.check_query_cache("player fatigue", {"top_k": 5}, "gen-1", 2)
        assert result.status == rc.STALE_REJECTED
        assert result.reason_code == "retrieval_version_mismatch"

    def test_miss_reason_code_distinct_from_stale_reject_reason_code(self):
        rc.write_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1, score=0.9)

        miss_result = rc.check_query_cache("never seen before", {"top_k": 5}, "gen-1", 1)
        stale_result = rc.check_query_cache("player fatigue", {"top_k": 5}, "gen-2", 1)

        assert miss_result.status == rc.MISS
        assert stale_result.status == rc.STALE_REJECTED
        assert miss_result.reason_code != stale_result.reason_code

    def test_category_name_is_retrieval_query_cache(self):
        assert rc.QUERY_CACHE_CATEGORY == "retrieval_query_cache"


# ---------------------------------------------------------------------------
# AC3 — Context-packet cache
# ---------------------------------------------------------------------------

class TestPacketCache:
    def test_hit_when_all_cited_hashes_and_versions_match(self):
        rc.write_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-1")
        result = rc.check_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-1")
        assert result.status == rc.HIT

    def test_invalidated_on_single_cited_source_hash_mismatch(self):
        rc.write_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-1")
        result = rc.check_packet_cache("packet-1", ["h1", "h2", "h3-changed"], "gen-1", "policy-1")
        assert result.status == rc.STALE_REJECTED
        assert result.reason_code == "cited_hash_mismatch"

    def test_invalidated_on_corpus_generation_change(self):
        rc.write_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-1")
        result = rc.check_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-2", "policy-1")
        assert result.status == rc.STALE_REJECTED
        assert result.reason_code == "corpus_generation_mismatch"

    def test_invalidated_on_policy_version_change(self):
        rc.write_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-1")
        result = rc.check_packet_cache("packet-1", ["h1", "h2", "h3"], "gen-1", "policy-2")
        assert result.status == rc.STALE_REJECTED
        assert result.reason_code == "policy_version_mismatch"

    def test_category_name_is_retrieval_packet_cache(self):
        assert rc.PACKET_CACHE_CATEGORY == "retrieval_packet_cache"


# ---------------------------------------------------------------------------
# AC4 — MAY-list only, no raw text, ever
# ---------------------------------------------------------------------------

class TestMayListEnforcement:
    def test_all_three_cache_tables_expose_only_may_list_columns(self):
        conn = rc._get_connection()
        try:
            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                columns = {
                    row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")
                }
                assert columns <= rc.MAY_LIST_COLUMNS, (
                    f"{table_name} exposes column(s) outside MAY_LIST_COLUMNS: "
                    f"{columns - rc.MAY_LIST_COLUMNS}"
                )
        finally:
            conn.close()

    def test_no_stored_row_contains_raw_prompt_or_chunk_text(self):
        raw_prompt = (
            "This is a long excerpt of retrieved chunk text that must never be persisted "
            "verbatim into any retrieval cache row, only referenced by its hash."
        )
        rc.write_query_cache(raw_prompt, {"top_k": 5}, "gen-1", 1, score=0.9)
        rc.write_packet_cache("packet-1", [rc._hash_text(raw_prompt)], "gen-1", "policy-1")
        rc.write_index_cache(
            rc._hash_text(raw_prompt), "emb-v1", "chunk-v1", source_id="doc-1"
        )

        conn = rc._get_connection()
        try:
            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                for row in conn.execute(f"SELECT * FROM {table_name}"):
                    for value in row:
                        if isinstance(value, str):
                            assert raw_prompt not in value
        finally:
            conn.close()

    def test_write_path_rejects_a_prohibited_field_if_offered(self):
        with pytest.raises(ValueError):
            rc.write_index_cache(
                "hash-a", "emb-v1", "chunk-v1", raw_text="prohibited content"
            )
        with pytest.raises(ValueError):
            rc.write_query_cache(
                "some query", {"top_k": 5}, "gen-1", 1, prompt="prohibited content"
            )
        with pytest.raises(ValueError):
            rc.write_packet_cache(
                "packet-1", ["h1"], "gen-1", "policy-1", chunk_text="prohibited content"
            )


# ---------------------------------------------------------------------------
# Naming-collision and import-isolation static guards
# ---------------------------------------------------------------------------

class TestStaticGuards:
    def test_no_class_named_cache_invalidation_policy_defined(self):
        source = Path(rc.__file__).read_text()
        tree = ast.parse(source)
        class_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }
        assert "CacheInvalidationPolicy" not in class_names

    def test_no_import_from_out_of_scope_modules(self):
        source = Path(rc.__file__).read_text()
        tree = ast.parse(source)
        banned_modules = {
            "src.observability.reporting.retention",
            "src.core.retention",
            "src.engine.world_index",
        }
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not (imported_modules & banned_modules)

    def test_cache_db_path_never_equals_knowledge_search_db_path(self):
        import tools.knowledge_search as ks

        assert rc.CACHE_DB_PATH != ks._DEFAULT_DB


# ---------------------------------------------------------------------------
# Lifecycle backstop — manual prune (Durable State Rule / Decision C)
# ---------------------------------------------------------------------------

class TestPrune:
    def test_prune_deletes_rows_older_than_threshold_across_all_three_tables(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        rc.write_query_cache("some query", {"top_k": 5}, "gen-1", 1, score=0.9)
        rc.write_packet_cache("packet-1", ["h1"], "gen-1", "policy-1")

        old_timestamp = time.time() - (40 * 86400)
        conn = rc._get_connection()
        try:
            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                conn.execute(
                    f"UPDATE {table_name} SET created_at = ?", (old_timestamp,)
                )
            conn.commit()
        finally:
            conn.close()

        deleted_by_table = rc.prune(older_than_days=30, table="all")

        assert all(count == 1 for count in deleted_by_table.values())
        conn = rc._get_connection()
        try:
            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                assert count == 0
        finally:
            conn.close()

    def test_prune_leaves_rows_newer_than_threshold_untouched(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")

        deleted_by_table = rc.prune(older_than_days=30, table="index")

        assert deleted_by_table["retrieval_index_cache_rows"] == 0
        result = rc.check_index_cache("hash-a", "emb-v1", "chunk-v1")
        assert result.status == rc.HIT

    def test_prune_is_not_invoked_by_any_check_or_write_function(self):
        hot_path_functions = [
            rc.check_index_cache,
            rc.check_query_cache,
            rc.check_packet_cache,
            rc.write_index_cache,
            rc.write_query_cache,
            rc.write_packet_cache,
        ]
        for func in hot_path_functions:
            source = inspect.getsource(func)
            assert "prune(" not in source
            assert "rc.prune" not in source


# ---------------------------------------------------------------------------
# RETRIEVAL_VERSION sentinel plumbing
# ---------------------------------------------------------------------------

class TestRetrievalVersionAndManifest:
    def test_corpus_generation_returns_no_manifest_sentinel_when_manifest_absent(self):
        assert rc._corpus_generation() == rc._NO_MANIFEST

    def test_corpus_generation_reads_built_at_from_manifest(self, tmp_path):
        _write_manifest(tmp_path, "2026-07-29T00:00:00Z")
        assert rc._corpus_generation() == "2026-07-29T00:00:00Z"
