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

import argparse
import ast
import dataclasses
import inspect
import json
import os
import sqlite3
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
    # TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD: every
    # write_provider_result_cache()/record_provider_result_cache_hit()/write_context_packet_cache()/
    # record_context_packet_cache_hit() call now also calls log_cache_access() internally, which
    # reads `.claude/current_run` and checks `tickets/{inprogress,done}/` for staleness — pointed
    # at a nonexistent tmp_path location by default so every pre-existing test in this file (which
    # never touches the access log at all) stays fully hermetic, never depending on this real
    # repo's actual sidecar file or ticket corpus.
    monkeypatch.setattr(rc, "_CURRENT_RUN_SIDECAR_PATH", tmp_path / "current_run")
    monkeypatch.setattr(rc, "_REPO_ROOT", tmp_path)
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

    def test_retrieval_cache_imports_open_connection_with_limits_from_new_location(self):
        """TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE moved open_connection_with_limits() out of
        the (now-archived) tools/knowledge_gateway_redaction.py into tools/write_path_guard.py."""
        source = Path(rc.__file__).read_text()
        assert "from tools import knowledge_gateway_redaction" not in source
        assert "from tools import write_path_guard" in source


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
# Migrations (Level 1 provider-result cache, TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS)
# ---------------------------------------------------------------------------

class TestMigrations:
    def test_migration_applies_cleanly_to_a_fresh_database(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            table_names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert table_names >= {
            "retrieval_index_cache_rows",
            "retrieval_query_cache_rows",
            "retrieval_packet_cache_rows",
            "retrieval_provider_result_cache_rows",
            "retrieval_cache_generation",
        }

    def test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        rc.write_query_cache("some query", {"top_k": 5}, "gen-1", 1, score=0.9)
        rc.write_packet_cache("packet-1", ["h1"], "gen-1", "policy-1")

        conn = rc._get_connection()
        try:
            before = {
                table_name: conn.execute(f"SELECT * FROM {table_name}").fetchall()
                for table_name in rc._TABLE_NAME_BY_ALIAS.values()
            }

            rc.migration_001_add_level1_tables(conn)

            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                after = conn.execute(f"SELECT * FROM {table_name}").fetchall()
                assert after == before[table_name]

            new_table_rows = conn.execute(
                "SELECT * FROM retrieval_provider_result_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert new_table_rows == []

    def test_new_table_column_set_matches_proposal_section_10_2_row_shape(self):
        # Updated by TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DD3, Architecture
        # Review-confirmed): LEVEL1_CACHE_COLUMNS gained a 22nd entry, redaction_policy_version,
        # added by migration_003_add_redaction_policy_version_column — a real, in-scope schema
        # widening this ticket performs, not a stale-assertion routed around. migration_003 must
        # now run alongside migration_001 for the live table shape to match the full documented
        # column set; migration_001 alone (this test's original scope) is a strict subset by
        # design (DD3's whole point is that migration_001 stays frozen/untouched).
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(retrieval_provider_result_cache_rows)"
                )
            }
        finally:
            conn.close()
        assert columns == rc.LEVEL1_CACHE_COLUMNS

    def test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rows = conn.execute(
                "SELECT retrieval_cache_schema_version, migrated_at FROM retrieval_cache_generation"
            ).fetchall()
        finally:
            conn.close()
        assert len(rows) == 1
        schema_version, migrated_at = rows[0]
        assert schema_version == 1
        assert abs(migrated_at - time.time()) < 5

    def test_migration_is_idempotent_when_run_twice(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            schema_before = list(
                conn.execute("PRAGMA table_info(retrieval_provider_result_cache_rows)")
            )
            conn.execute(
                "INSERT INTO retrieval_provider_result_cache_rows "
                "(query_hash, normalized_intent, resolved_entity_ids, filters, "
                "routing_policy_version, repo_branch_scope, provider_name, adapter_version, "
                "result_payload, source_ids, source_paths, provider_generation, "
                "evidence_fingerprints, created_at, hit_count) "
                "VALUES ('h1','intent','[]','{}', 'rp-v1', 'repo:main', 'prov', 'av1', "
                "'payload', '[]', '[]', 'gen-1', '[]', ?, 0)",
                (time.time(),),
            )
            conn.commit()

            rc.migration_001_add_level1_tables(conn)

            schema_after = list(
                conn.execute("PRAGMA table_info(retrieval_provider_result_cache_rows)")
            )
            generation_rows = conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchall()
            payload_rows = conn.execute(
                "SELECT query_hash FROM retrieval_provider_result_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert schema_after == schema_before
        assert generation_rows == [(1,)]
        assert payload_rows == [("h1",)]

    def test_migration_does_not_alter_existing_marker_only_table_column_sets(self):
        conn = rc._get_connection()
        try:
            before = {
                table_name: list(conn.execute(f"PRAGMA table_info({table_name})"))
                for table_name in rc._TABLE_NAME_BY_ALIAS.values()
            }

            rc.migration_001_add_level1_tables(conn)

            after = {
                table_name: list(conn.execute(f"PRAGMA table_info({table_name})"))
                for table_name in rc._TABLE_NAME_BY_ALIAS.values()
            }
        finally:
            conn.close()
        assert after == before

    def test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes(
        self,
    ):
        source = Path(rc.__file__).read_text()
        tree = ast.parse(source)
        module_level_names = set()
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                module_level_names.add(node.target.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_level_names.add(target.id)
        assert "RETRIEVAL_VERSION" in module_level_names
        assert "retrieval_cache_schema_version" in module_level_names

        import tools.retrieval_events as re_mod

        assert re_mod.retrieval_event_schema_version == 1

    def test_migration_001_function_is_never_called_from_any_check_or_write_function(self):
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
            assert "migration_001" not in source

    def test_no_migrate_or_rebuild_subcommand_added_to_cli(self):
        assert "migrate" not in rc._COMMAND_DISPATCH
        assert "rebuild" not in rc._COMMAND_DISPATCH

        parser = rc._build_parser()
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        subcommand_names = set()
        for action in subparsers_actions:
            subcommand_names.update(action.choices.keys())
        assert "migrate" not in subcommand_names
        assert "rebuild" not in subcommand_names

    def test_new_table_and_generation_table_absent_from_prune_table_alias_map(self):
        assert "retrieval_cache_generation" not in rc._TABLE_NAME_BY_ALIAS.values()
        assert "retrieval_provider_result_cache_rows" not in rc._TABLE_NAME_BY_ALIAS.values()


# ---------------------------------------------------------------------------
# RETRIEVAL_VERSION sentinel plumbing
# ---------------------------------------------------------------------------

class TestRetrievalVersionAndManifest:
    def test_corpus_generation_returns_no_manifest_sentinel_when_manifest_absent(self):
        assert rc._corpus_generation() == rc._NO_MANIFEST

    def test_corpus_generation_reads_built_at_from_manifest(self, tmp_path):
        _write_manifest(tmp_path, "2026-07-29T00:00:00Z")
        assert rc._corpus_generation() == "2026-07-29T00:00:00Z"


# ---------------------------------------------------------------------------
# Crash recovery — today's marker-only schema only
# (TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY)
# ---------------------------------------------------------------------------

class TestCrashRecovery:
    def test_deleted_cache_db_rebuilds_clean_marker_only_schema(self, tmp_path):
        """This test verifies rebuild of the schema that exists today (three marker-only
        tables: retrieval_index_cache_rows, retrieval_query_cache_rows,
        retrieval_packet_cache_rows). It does not and cannot test payload-row recovery,
        because no payload column exists yet (cache_migration_plan.md confirms Level 1/2
        payload tables are unimplemented Phase 2/3 work). A future ticket that adds payload
        tables must extend this test, not treat it as already covering that case.
        """
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        rc.write_query_cache("some query", {"top_k": 5}, "gen-1", 1, score=0.9)
        rc.write_packet_cache("packet-1", ["h1"], "gen-1", "policy-1")

        rc.CACHE_DB_PATH.unlink()

        result = rc.check_index_cache("hash-a", "emb-v1", "chunk-v1")
        assert result.status == rc.MISS

        conn = rc._get_connection()
        try:
            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                assert count == 0
        finally:
            conn.close()

        touched_outside_cache_dir = [
            path
            for path in tmp_path.rglob("*")
            if path.is_file() and path != rc.CACHE_DB_PATH
        ]
        assert touched_outside_cache_dir == []

    def test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_rows(
        self, tmp_path
    ):
        """Per plan.md DD6: migration_001_add_level1_tables is never called from _get_connection()/
        _init_schema(), so after a raw file delete, reconnecting via _get_connection() brings back
        only the 3 marker-only tables (today's existing behavior) — the Level 1 table stays absent
        until migration_001_add_level1_tables is explicitly re-run. This is the decided, correct
        behavior, not an oversight: cache_migration_plan.md §5 defers any auto-apply-on-connect
        ('migrate') policy to a future ticket.
        """
        conn = rc._get_connection()
        rc.migration_001_add_level1_tables(conn)
        conn.execute(
            "INSERT INTO retrieval_provider_result_cache_rows "
            "(query_hash, normalized_intent, resolved_entity_ids, filters, routing_policy_version, "
            "repo_branch_scope, provider_name, adapter_version, result_payload, source_ids, "
            "source_paths, provider_generation, evidence_fingerprints, created_at, hit_count) "
            "VALUES ('h1','intent','[]','{}', 'rp-v1', 'repo:main', 'prov', 'av1', 'payload', '[]', "
            "'[]', 'gen-1', '[]', ?, 0)",
            (time.time(),),
        )
        conn.commit()
        conn.close()

        rc.CACHE_DB_PATH.unlink()

        conn = rc._get_connection()
        try:
            table_names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()

        assert "retrieval_provider_result_cache_rows" not in table_names
        assert "retrieval_cache_generation" not in table_names


def _insert_level2_row(conn: sqlite3.Connection, *, packet_id: str = "p1",
                        evidence_dependencies: str = "[]") -> None:
    conn.execute(
        "INSERT INTO retrieval_context_packet_cache_rows "
        "(packet_id, normalized_intent, query_key_hash, entity_ids, statements, "
        "context_items, evidence, conflicts, evidence_dependencies, provenance_providers, "
        "providers_consulted_this_call, repository_id, branch, provider_generations, "
        "policy_version, response_schema_version, status, freshness, verification, "
        "created_at, hit_count) "
        "VALUES (?, 'intent', 'qkh-1', '[]', '[]', '[]', '[]', '[]', ?, '[]', '[]', "
        "'repo-a', 'main', '{}', 'policy-1', 1, 'ok', 'fresh', 'verified', ?, 0)",
        (packet_id, evidence_dependencies, time.time()),
    )
    conn.commit()


class TestLevel2Migrations:
    """TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS — migration_002_add_level2_tables and
    LEVEL2_CACHE_COLUMNS (plan.md Step 5). migration_002 assumes retrieval_cache_generation already
    exists (created only by migration_001) -- an explicit, deliberate design documented in plan.md
    Step 2/DD2's "Ordering assumption" (migration_002 is never auto-applied and never itself
    verifies migration_001 ran first; calling it on a connection where migration_001 has never run
    raises sqlite3.OperationalError by design, mirroring migration_001's own "explicit invocation
    only" pattern). Every test below therefore applies migration_001 before migration_002,
    consistent with that documented ordering assumption and with the real chain this module's own
    production caller uses today (migration_001 -> migration_003 -> migration_002).
    """

    def test_migration_002_function_exists_with_reserved_name_and_ordinal(self):
        assert callable(rc.migration_002_add_level2_tables)
        params = list(inspect.signature(rc.migration_002_add_level2_tables).parameters.values())
        assert len(params) == 1
        assert params[0].name == "conn"
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

        source = Path(rc.__file__).read_text()
        tree = ast.parse(source)
        def_lines = {
            node.name: node.lineno
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {
                "migration_001_add_level1_tables",
                "migration_002_add_level2_tables",
                "migration_003_add_redaction_policy_version_column",
            }
        }
        assert (
            def_lines["migration_001_add_level1_tables"]
            < def_lines["migration_002_add_level2_tables"]
            < def_lines["migration_003_add_redaction_policy_version_column"]
        )

    def test_migration_002_never_creates_a_second_database_file(self, tmp_path):
        """AC6 (Test-phase-flagged gap): migration_002_add_level2_tables takes a connection, not a
        path (confirmed structurally by test_migration_002_function_exists_with_reserved_name_and_
        ordinal's signature assertion above), so it cannot open a second file on its own -- but
        that's an implementation-shape argument, not an independent end-to-end check. This test
        proves it behaviorally: after running migration_001 then migration_002 against the isolated
        tmp_path CACHE_DB_PATH, the only file(s) present are the single cache DB (plus any SQLite
        journal/WAL/SHM sidecar of that *same* file) -- never a second, distinct database file."""
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
        finally:
            conn.close()

        db_stem = rc.CACHE_DB_PATH.stem
        other_files = [
            path
            for path in tmp_path.rglob("*")
            if path.is_file() and path.stem != db_stem
        ]
        assert other_files == [], (
            f"expected only sidecar files of {rc.CACHE_DB_PATH.name}, found: {other_files}"
        )

    def test_migration_002_applies_cleanly_to_a_fresh_database(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            table_names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert table_names >= {
            "retrieval_index_cache_rows",
            "retrieval_query_cache_rows",
            "retrieval_packet_cache_rows",
            "retrieval_provider_result_cache_rows",
            "retrieval_cache_generation",
            "retrieval_context_packet_cache_rows",
        }

    def test_migration_002_applies_cleanly_on_top_of_legacy_only_schema_with_zero_data_loss(self):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        rc.write_query_cache("some query", {"top_k": 5}, "gen-1", 1, score=0.9)
        rc.write_packet_cache("packet-1", ["h1"], "gen-1", "policy-1")

        conn = rc._get_connection()
        try:
            before = {
                table_name: conn.execute(f"SELECT * FROM {table_name}").fetchall()
                for table_name in rc._TABLE_NAME_BY_ALIAS.values()
            }

            # migration_001 required first -- see class docstring.
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)

            for table_name in rc._TABLE_NAME_BY_ALIAS.values():
                after = conn.execute(f"SELECT * FROM {table_name}").fetchall()
                assert after == before[table_name]

            new_table_rows = conn.execute(
                "SELECT * FROM retrieval_context_packet_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert new_table_rows == []

    def test_migration_002_applies_cleanly_on_top_of_level1_already_migrated_schema_with_zero_data_loss(
        self,
    ):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)

            conn.execute(
                "INSERT INTO retrieval_provider_result_cache_rows "
                "(query_hash, normalized_intent, resolved_entity_ids, filters, "
                "routing_policy_version, repo_branch_scope, provider_name, adapter_version, "
                "result_payload, source_ids, source_paths, provider_generation, "
                "evidence_fingerprints, created_at, hit_count) "
                "VALUES ('h1','intent','[]','{}', 'rp-v1', 'repo:main', 'prov', 'av1', "
                "'payload', '[]', '[]', 'gen-1', '[]', ?, 0)",
                (time.time(),),
            )
            conn.commit()

            before = conn.execute(
                "SELECT * FROM retrieval_provider_result_cache_rows"
            ).fetchall()

            rc.migration_002_add_level2_tables(conn)

            after = conn.execute(
                "SELECT * FROM retrieval_provider_result_cache_rows"
            ).fetchall()
            columns_after = [
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(retrieval_provider_result_cache_rows)"
                )
            ]
            table_names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert after == before
        assert "redaction_policy_version" in columns_after
        assert "retrieval_context_packet_cache_rows" in table_names

    def test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list(
        self,
    ):
        # Updated by TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING (plan.md PD4): mirrors
        # test_new_table_column_set_matches_proposal_section_10_2_row_shape's own precedent —
        # LEVEL2_CACHE_COLUMNS gained 4 entries (redaction_policy_version/budget_truncated/
        # omitted_statement_count/provider_failures) added by
        # migration_004_add_level2_write_path_columns, a real, in-scope schema widening this
        # ticket performs. migration_004 must now run alongside migration_001/migration_002 for
        # the live table shape to match the full documented column set; migration_002 alone (this
        # test's original scope) is a strict subset by design.
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            rc.migration_004_add_level2_write_path_columns(conn)
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(retrieval_context_packet_cache_rows)"
                )
            }
        finally:
            conn.close()
        assert columns == rc.LEVEL2_CACHE_COLUMNS

    def test_migration_002_is_idempotent_when_run_twice(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            schema_before = list(
                conn.execute("PRAGMA table_info(retrieval_context_packet_cache_rows)")
            )
            _insert_level2_row(conn, packet_id="p1")

            rc.migration_002_add_level2_tables(conn)

            schema_after = list(
                conn.execute("PRAGMA table_info(retrieval_context_packet_cache_rows)")
            )
            generation_rows = conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchall()
            payload_rows = conn.execute(
                "SELECT packet_id FROM retrieval_context_packet_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert schema_after == schema_before
        assert generation_rows == [(2,)]
        assert payload_rows == [("p1",)]

    def test_migration_002_does_not_alter_existing_marker_only_or_level1_table_column_sets(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)

            tables = list(rc._TABLE_NAME_BY_ALIAS.values()) + [
                "retrieval_provider_result_cache_rows"
            ]
            before = {
                table_name: list(conn.execute(f"PRAGMA table_info({table_name})"))
                for table_name in tables
            }

            rc.migration_002_add_level2_tables(conn)

            after = {
                table_name: list(conn.execute(f"PRAGMA table_info({table_name})"))
                for table_name in tables
            }
        finally:
            conn.close()
        assert after == before

    def test_retrieval_cache_schema_version_correctly_reflects_new_schema_state_after_migration_002(
        self,
    ):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)
            rc.migration_002_add_level2_tables(conn)
            full_chain_rows = conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchall()
        finally:
            conn.close()
        assert full_chain_rows == [(2,)]

        # Regression guard for investigation.md Risk 1 / plan.md DD2: migration_001 run alone, in
        # true isolation on a separate connection, must still stamp exactly 1 -- unaffected by
        # migration_002 having ever existed or run elsewhere.
        isolated_conn = sqlite3.connect(":memory:")
        try:
            rc.migration_001_add_level1_tables(isolated_conn)
            migration_001_alone_rows = isolated_conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchall()
        finally:
            isolated_conn.close()
        assert migration_001_alone_rows == [(1,)]

    def test_evidence_dependencies_column_is_json_text_and_supports_set_intersection_like_the_existing_marker_only_packet_table(
        self,
    ):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            deps = ["path/a.py", "path/b.py"]
            _insert_level2_row(conn, packet_id="p1", evidence_dependencies=json.dumps(deps))

            stored_deps_json = conn.execute(
                "SELECT evidence_dependencies FROM retrieval_context_packet_cache_rows "
                "WHERE packet_id = 'p1'"
            ).fetchone()[0]
        finally:
            conn.close()
        current_changed_paths = ["path/a.py", "path/b.py"]
        assert set(current_changed_paths) == set(json.loads(stored_deps_json))

        different_changed_paths = ["path/a.py", "path/c.py"]
        assert set(different_changed_paths) != set(json.loads(stored_deps_json))

    def test_new_level2_table_name_does_not_collide_with_existing_marker_only_packet_table(self):
        rc.write_packet_cache("packet-1", ["h1"], "gen-1", "policy-1")

        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            _insert_level2_row(conn, packet_id="p1")

            table_names = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            marker_rows = conn.execute(
                "SELECT packet_key_hash FROM retrieval_packet_cache_rows"
            ).fetchall()
            level2_rows = conn.execute(
                "SELECT packet_id FROM retrieval_context_packet_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert "retrieval_packet_cache_rows" != "retrieval_context_packet_cache_rows"
        assert {"retrieval_packet_cache_rows", "retrieval_context_packet_cache_rows"} <= table_names
        assert marker_rows == [("packet-1",)]
        assert level2_rows == [("p1",)]

    def test_check_and_write_functions_no_longer_exist_for_the_removed_level2_table(self):
        """TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING once added real
        check_context_packet_cache()/write_context_packet_cache() functions here (see this test's
        prior docstring, before TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL). That ticket
        removed both again, along with the Level 1 pair, once their only production caller (the
        deleted KGMCP gateway) was gone. Restored to its pre-P3 premise -- guarding against the
        opposite drift (a stub/rename reintroducing them) -- rather than deleted outright, since the
        module's public check_*/write_* surface remains a real invariant worth guarding regardless
        of which direction it last changed."""
        assert not hasattr(rc, "check_context_packet_cache")
        assert not hasattr(rc, "write_context_packet_cache")
        module_public_names = {name for name in dir(rc) if not name.startswith("_")}
        read_write_style_names = {
            name
            for name in module_public_names
            if name.startswith("check_") or name.startswith("write_")
        }
        assert read_write_style_names == {
            "check_index_cache",
            "check_query_cache",
            "check_packet_cache",
            "write_index_cache",
            "write_query_cache",
            "write_packet_cache",
        }

    def test_no_pragma_busy_timeout_or_chmod_introduced_by_level2_migration(self):
        # TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY: narrowed from
        # test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration. That name
        # additionally banned importing `os` anywhere in this file at all, as a blanket proxy for
        # "no os.chmod-based permission hacks" -- but the two chmod-specific string checks below
        # already test that real concern precisely and remain fully enforced unchanged. The
        # blanket `os` import ban was an overly broad proxy that this ticket's own legitimate,
        # unrelated need (os.environ.get("CLAUDE_CODE_SESSION_ID") in read_current_run_sidecar())
        # ran into; narrowing this one redundant clause is not a weakening of the real, still-
        # enforced invariant (no chmod, no busy_timeout PRAGMA tricks in the migration code).
        source = Path(rc.__file__).read_text()
        assert "PRAGMA journal_mode" not in source
        assert "PRAGMA busy_timeout" not in source
        assert "busy_timeout" not in source
        assert "os.chmod" not in source
        assert "chmod" not in source


# ---------------------------------------------------------------------------
# migration_004 — Level 2 write-path columns
# (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING, plan.md Step 1/PD4)
# ---------------------------------------------------------------------------

class TestMigration004:
    _NEW_COLUMNS = (
        "redaction_policy_version", "budget_truncated", "omitted_statement_count",
        "provider_failures",
    )

    def test_migration_004_adds_redaction_policy_version_budget_truncated_omitted_statement_count_provider_failures_columns_idempotently(
        self,
    ):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            rc.migration_004_add_level2_write_path_columns(conn)
            rc.migration_004_add_level2_write_path_columns(conn)  # must not raise
            columns = [row[1] for row in conn.execute(
                "PRAGMA table_info(retrieval_context_packet_cache_rows)"
            )]
        finally:
            conn.close()
        for name in self._NEW_COLUMNS:
            assert columns.count(name) == 1, f"{name} must be added exactly once, idempotently"

    def test_migration_004_preserves_existing_rows_and_column_set_matches_updated_constant(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_002_add_level2_tables(conn)
            _insert_level2_row(conn, packet_id="p-preserve")
            rc.migration_004_add_level2_write_path_columns(conn)
            row = conn.execute(
                "SELECT packet_id, normalized_intent FROM retrieval_context_packet_cache_rows "
                "WHERE packet_id = 'p-preserve'"
            ).fetchone()
            columns = {c[1] for c in conn.execute(
                "PRAGMA table_info(retrieval_context_packet_cache_rows)"
            )}
        finally:
            conn.close()
        assert row == ("p-preserve", "intent")
        assert columns == rc.LEVEL2_CACHE_COLUMNS


# ---------------------------------------------------------------------------
# Level 2 context-packet cache — read/write orchestration
# (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING, plan.md Step 2)
# ---------------------------------------------------------------------------

def _write_level2_row(**overrides) -> None:
    kwargs = dict(
        packet_id="p-1", normalized_intent="what is x", query_key_hash="qkh-1",
        entity_ids_json="[]", answer="an answer", statements_json="[]",
        context_items_json="[]", evidence_json="[]", conflicts_json="[]",
        evidence_dependencies_json="[]", provenance_providers_json="[]",
        providers_consulted_this_call_json='["context_search"]',
        repository_id="repo-a", branch="main", head_commit=None,
        working_tree_fingerprint=None, provider_generations_json='{"context_search": "gen-1"}',
        policy_version="1", response_schema_version=1, budget_requested=4000,
        budget_returned=100, status="OK", freshness="UNKNOWN", verification="SUPPORTED",
        lifecycle=None, redaction_policy_version=1, budget_truncated=False,
        omitted_statement_count=0, provider_failures_json=None,
    )
    kwargs.update(overrides)
    # write_context_packet_cache() was removed by TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-
    # REMOVAL along with its only production caller; this helper now performs the same INSERT OR
    # REPLACE directly so TestContextPacketCacheStats (left standing -- see that ticket's own
    # Unresolved Question #1 resolution) still has real, non-trivial rows to aggregate over.
    conn = rc._get_level2_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO retrieval_context_packet_cache_rows "
            "(packet_id, normalized_intent, query_key_hash, entity_ids, answer, statements, "
            " context_items, evidence, conflicts, evidence_dependencies, provenance_providers, "
            " providers_consulted_this_call, repository_id, branch, head_commit, "
            " working_tree_fingerprint, provider_generations, policy_version, "
            " response_schema_version, budget_requested, budget_returned, status, freshness, "
            " verification, lifecycle, redaction_policy_version, budget_truncated, "
            " omitted_statement_count, provider_failures, created_at, last_validated_at, "
            " hit_count)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            " ?, ?, ?, ?, ?, NULL, 0)",
            (
                kwargs["packet_id"], kwargs["normalized_intent"], kwargs["query_key_hash"],
                kwargs["entity_ids_json"], kwargs["answer"], kwargs["statements_json"],
                kwargs["context_items_json"], kwargs["evidence_json"], kwargs["conflicts_json"],
                kwargs["evidence_dependencies_json"], kwargs["provenance_providers_json"],
                kwargs["providers_consulted_this_call_json"], kwargs["repository_id"],
                kwargs["branch"], kwargs["head_commit"], kwargs["working_tree_fingerprint"],
                kwargs["provider_generations_json"], kwargs["policy_version"],
                kwargs["response_schema_version"], kwargs["budget_requested"],
                kwargs["budget_returned"], kwargs["status"], kwargs["freshness"],
                kwargs["verification"], kwargs["lifecycle"], kwargs["redaction_policy_version"],
                int(kwargs["budget_truncated"]) if kwargs["budget_truncated"] is not None else None,
                kwargs["omitted_statement_count"], kwargs["provider_failures_json"], time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


class TestContextPacketCacheStats:
    def test_context_packet_cache_stats_zero_on_fresh_db(self):
        assert rc.context_packet_cache_stats() == {"total_rows": 0, "total_hits": 0}

    def test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db(self):
        # No write has ever happened -- the table may not exist yet; must return zeros, never
        # raise, mirroring provider_result_cache_stats()'s own fresh/never-migrated DB contract.
        assert rc.context_packet_cache_stats() == {"total_rows": 0, "total_hits": 0}

    def test_context_packet_cache_stats_reflects_real_rows_and_hits(self):
        _write_level2_row(packet_id="p-a")
        _write_level2_row(packet_id="p-b")
        # record_context_packet_cache_hit() was removed by TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-
        # CHAIN-REMOVAL along with its only production caller; increment hit_count directly so this
        # test's own real-row/real-hit assertion stays meaningful.
        conn = rc._get_connection()
        try:
            conn.execute(
                "UPDATE retrieval_context_packet_cache_rows SET hit_count = hit_count + 1 "
                "WHERE packet_id = 'p-a'"
            )
            conn.execute(
                "UPDATE retrieval_context_packet_cache_rows SET hit_count = hit_count + 1 "
                "WHERE packet_id = 'p-a'"
            )
            conn.commit()
        finally:
            conn.close()
        stats = rc.context_packet_cache_stats()
        assert stats == {"total_rows": 2, "total_hits": 2}


# ---------------------------------------------------------------------------
# KGMCP cache-access-log — TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
# ---------------------------------------------------------------------------

def _write_sidecar(tmp_path: Path, **fields) -> None:
    (tmp_path / "current_run").write_text(json.dumps(fields))


def _make_inprogress_ticket(tmp_path: Path, ticket_id: str) -> None:
    d = tmp_path / "tickets" / "inprogress"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{ticket_id}.md").write_text("# fake ticket\n")


def _make_done_ticket(tmp_path: Path, ticket_id: str) -> None:
    d = tmp_path / "tickets" / "done"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{ticket_id}.md").write_text("# fake ticket\n")


class TestMigration005CacheAccessLog:
    def test_migration_applies_cleanly_to_a_fresh_database(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_005_add_cache_access_log_table(conn)
            table_names = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert "retrieval_cache_access_log" in table_names

    def test_migration_is_idempotent_when_run_twice(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_005_add_cache_access_log_table(conn)
            rc.migration_005_add_cache_access_log_table(conn)  # must not raise
            count = conn.execute("SELECT COUNT(*) FROM retrieval_cache_generation").fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_migration_stamps_generation_table_with_version_3(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_005_add_cache_access_log_table(conn)
            version = conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchone()[0]
        finally:
            conn.close()
        assert version == 3

    def test_migration_does_not_touch_existing_marker_only_or_level1_tables(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            before = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            rc.migration_005_add_cache_access_log_table(conn)
            after = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert before <= after
        # sqlite_sequence is SQLite's own internal bookkeeping table, auto-created the first time
        # any table uses AUTOINCREMENT (retrieval_cache_access_log's `id` column) -- not a table
        # this migration defines itself, but a real, expected SQLite side effect.
        assert after - before == {"retrieval_cache_access_log", "sqlite_sequence"}

    def test_access_log_column_set_matches_documented_shape(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_005_add_cache_access_log_table(conn)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(retrieval_cache_access_log)")}
        finally:
            conn.close()
        assert columns == {
            "id", "cache_level", "event_type", "query_hash", "repo_branch_scope", "packet_id",
            "run_id", "seq", "phase", "agent", "execution_id", "provider", "ticket_id",
            "sidecar_stale", "ts",
        }

class TestReadCurrentRunSidecar:
    def test_returns_all_none_and_not_stale_when_sidecar_file_absent(self):
        result = rc.read_current_run_sidecar()
        assert result == {
            "run_id": None, "seq": None, "phase": None, "agent": None, "execution_id": None,
            "provider": None, "ticket_id": None, "sidecar_stale": False,
        }

    def test_reads_real_sidecar_fields(self, tmp_path):
        _write_sidecar(
            tmp_path, run_id="TCK-A", seq=2, phase="Implement", agent="implementer",
            execution_id="x1", provider="anthropic",
        )
        result = rc.read_current_run_sidecar()
        assert result["run_id"] == "TCK-A"
        assert result["seq"] == 2
        assert result["phase"] == "Implement"
        assert result["agent"] == "implementer"
        assert result["execution_id"] == "x1"
        assert result["provider"] == "anthropic"

    def test_malformed_sidecar_json_fails_silently_to_all_none(self, tmp_path):
        (tmp_path / "current_run").write_text("{not valid json")
        result = rc.read_current_run_sidecar()
        assert result["run_id"] is None
        assert result["sidecar_stale"] is False

    def test_sidecar_stale_true_when_run_id_ticket_is_already_done_not_inprogress(self, tmp_path):
        """Reproduces the exact live failure mode this ticket's own Scope item 6 documents:
        .claude/current_run points at a ticket that has already moved to tickets/done/."""
        _make_done_ticket(tmp_path, "TCK-20260101-FAKE-CLOSED")
        _write_sidecar(tmp_path, run_id="TCK-20260101-FAKE-CLOSED", seq=1, phase="Verify", agent="done-checker")
        result = rc.read_current_run_sidecar()
        assert result["sidecar_stale"] is True

    def test_sidecar_not_stale_when_ticket_is_genuinely_inprogress(self, tmp_path):
        _make_inprogress_ticket(tmp_path, "TCK-20260101-FAKE-OPEN")
        _write_sidecar(tmp_path, run_id="TCK-20260101-FAKE-OPEN", seq=1, phase="Implement", agent="implementer")
        result = rc.read_current_run_sidecar()
        assert result["sidecar_stale"] is False

    def test_sidecar_not_stale_when_no_ticket_id_at_all_ad_hoc_work(self, tmp_path):
        # No run_id starting with TCK- and no explicit ticket_id -- ad-hoc, non-ticket work. This
        # is honestly "unattributed", not "stale" -- a real, distinct signal (see
        # compute_kgmcp_cache_efficiency_metrics's own "unattributed" bucket).
        _write_sidecar(tmp_path, run_id="ad-hoc-session", seq=1, phase="Investigate", agent="claude")
        result = rc.read_current_run_sidecar()
        assert result["sidecar_stale"] is False

    def test_run_id_only_sidecar_reports_effective_ticket_id_not_none(self, tmp_path):
        """TCK-20260826-KGMCP-CACHE-TICKET-ATTRIBUTION: the real shape every sidecar writer
        produces (run_id only, no explicit ticket_id key) must resolve 'ticket_id' to the run_id
        fallback, not raw None — this is exactly why per-ticket cache-efficiency breakdown was
        100% 'unattributed' before this fix."""
        _write_sidecar(
            tmp_path, run_id="TCK-20260101-REAL-WORK", seq=1, phase="Implement", agent="implementer",
        )
        result = rc.read_current_run_sidecar()
        assert result["ticket_id"] == "TCK-20260101-REAL-WORK"

    def test_explicit_ticket_id_field_used_over_run_id_when_both_present(self, tmp_path):
        _make_done_ticket(tmp_path, "TCK-20260101-CHILD-CLOSED")
        _write_sidecar(
            tmp_path, run_id="EPIC-20260101-PARENT", ticket_id="TCK-20260101-CHILD-CLOSED",
            seq=1, phase="Implement", agent="implementer",
        )
        result = rc.read_current_run_sidecar()
        assert result["ticket_id"] == "TCK-20260101-CHILD-CLOSED"
        assert result["sidecar_stale"] is True

    def test_scoped_sidecar_wins_over_stale_unscoped_when_both_exist(self, tmp_path, monkeypatch):
        # TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY: mirrors post_tool_hook.py's own
        # scoped-file preference (TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE).
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-real")
        _write_sidecar(
            tmp_path, run_id="TCK-STALE-FOREIGN", seq=99, phase="Finalize", agent="implementer",
        )
        (tmp_path / "current_run.sess-real").write_text(
            json.dumps({"run_id": "TCK-REAL", "seq": 3, "phase": "Implement", "agent": "implementer"})
        )
        result = rc.read_current_run_sidecar()
        assert result["run_id"] == "TCK-REAL"
        assert result["seq"] == 3
        assert result["phase"] == "Implement"

    def test_no_scoped_file_falls_back_to_unscoped_and_deletes_nothing(self, tmp_path, monkeypatch):
        # TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY: deliberately does NOT adopt
        # post_tool_hook.py's null-sentinel-on-absence write side effect (see
        # read_current_run_sidecar()'s own docstring for the reasoning) — falls back to the
        # unscoped file, same as pre-TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION, and never
        # deletes any file (no pruning logic of its own, per this ticket's Out of Scope).
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-no-scoped-file")
        _write_sidecar(tmp_path, run_id="TCK-UNSCOPED", seq=1, phase="Scope", agent="ticket-scoper")
        stale_other_scoped = tmp_path / "current_run.sess-other"
        stale_other_scoped.write_text(json.dumps({"run_id": "TCK-OTHER", "seq": 9}))
        old_time = time.time() - (25 * 3600)
        os.utime(stale_other_scoped, (old_time, old_time))

        result = rc.read_current_run_sidecar()
        assert result["run_id"] == "TCK-UNSCOPED"
        assert result["phase"] == "Scope"
        # No new file-deletion side effect: the unrelated, genuinely stale scoped file for a
        # DIFFERENT session is untouched — pruning stays solely owned by post_tool_hook.py.
        assert stale_other_scoped.exists()
