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


# ---------------------------------------------------------------------------
# Level 1 provider-result cache read/write (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING)
# ---------------------------------------------------------------------------

def _write_row(**overrides) -> None:
    kwargs = dict(
        query_hash="qh-1", normalized_intent="what is x", resolved_entity_ids_json="[]",
        filters_json="{}", budget_class="small", routing_policy_version=1,
        repo_branch_scope="repo::main", provider_name_json='["context_search"]',
        adapter_version_json="{}", result_payload='{"answer": "x"}',
        source_ids_json="[]", source_paths_json="[]", provider_generation="gen-1",
        evidence_fingerprints_json="generation:context_search@gen-1",
        validated_negative_scopes=None, adapter_version_at_validation_json="{}",
        working_tree_overlap_json="[]", provider_generation_at_validation="gen-1",
        redaction_policy_version=1,
    )
    kwargs.update(overrides)
    rc.write_provider_result_cache(**kwargs)


class TestProviderResultCache:
    def test_check_provider_result_cache_creates_table_on_first_real_use(self):
        result = rc.check_provider_result_cache(
            "qh-1", "repo::main", normalized_intent="what is x", filters_json="{}",
            budget_class="small", routing_policy_version=1,
        )
        assert result.status == rc.MISS
        conn = rc._get_connection()
        try:
            table_names = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert "retrieval_provider_result_cache_rows" in table_names

    def test_check_provider_result_cache_miss_on_no_row(self):
        result = rc.check_provider_result_cache(
            "no-such-hash", "repo::main", normalized_intent="x", filters_json="{}",
            budget_class="small", routing_policy_version=1,
        )
        assert result.status == rc.MISS
        assert result.reason_code == "no_cached_row"
        assert result.row is None

    def test_check_provider_result_cache_hit_on_matching_full_identity(self):
        _write_row()
        result = rc.check_provider_result_cache(
            "qh-1", "repo::main", normalized_intent="what is x", filters_json="{}",
            budget_class="small", routing_policy_version=1,
        )
        assert result.status == rc.HIT
        assert result.reason_code is None
        assert result.row["result_payload"] == '{"answer": "x"}'

    def test_check_provider_result_cache_miss_on_filters_mismatch_despite_pk_match(self):
        """DD10 — the primary key (query_hash, repo_branch_scope) is narrower than the full §1
        6-field lookup identity; a filters mismatch on the same PK must be a MISS, never a
        served-wrong-identity HIT."""
        _write_row()
        result = rc.check_provider_result_cache(
            "qh-1", "repo::main", normalized_intent="what is x", filters_json='{"mode": "answer"}',
            budget_class="small", routing_policy_version=1,
        )
        assert result.status == rc.MISS
        assert result.reason_code == "identity_mismatch_on_shared_key"
        assert result.row is None

    def test_check_provider_result_cache_routing_policy_version_type_coercion_is_consistent(self):
        """DD10's non-blocking implementation note: routing_policy_version is stored as TEXT
        (str(int)) by write_provider_result_cache and must be compared consistently by
        check_provider_result_cache, not spuriously mismatched by an int/str type difference."""
        _write_row(routing_policy_version=7)
        matching = rc.check_provider_result_cache(
            "qh-1", "repo::main", normalized_intent="what is x", filters_json="{}",
            budget_class="small", routing_policy_version=7,
        )
        assert matching.status == rc.HIT

        mismatched = rc.check_provider_result_cache(
            "qh-1", "repo::main", normalized_intent="what is x", filters_json="{}",
            budget_class="small", routing_policy_version=8,
        )
        assert mismatched.status == rc.MISS
        assert mismatched.reason_code == "identity_mismatch_on_shared_key"

    def test_lookup_function_never_returns_a_freshness_or_verification_field(self):
        """Non-collapse rule (§3/DD9) — AST-inspects ProviderResultCacheLookup's own fields."""
        field_names = {f.name for f in dataclasses.fields(rc.ProviderResultCacheLookup)}
        assert "freshness" not in field_names
        assert "verification" not in field_names
        assert field_names == {"status", "reason_code", "row"}

    def test_write_provider_result_cache_creates_table_and_inserts_row(self):
        _write_row()
        conn = rc._get_connection()
        try:
            rows = conn.execute(
                "SELECT query_hash, redaction_policy_version FROM retrieval_provider_result_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("qh-1", 1)]

    def test_write_provider_result_cache_insert_or_replace_overwrites_same_pk(self):
        _write_row(result_payload='{"answer": "first"}')
        _write_row(result_payload='{"answer": "second"}')
        conn = rc._get_connection()
        try:
            rows = conn.execute(
                "SELECT result_payload FROM retrieval_provider_result_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [('{"answer": "second"}',)]

    def test_record_provider_result_cache_hit_increments_hit_count_and_stamps_last_hit_at(self):
        _write_row()
        rc.record_provider_result_cache_hit("qh-1", "repo::main")
        conn = rc._get_connection()
        try:
            hit_count, last_hit_at = conn.execute(
                "SELECT hit_count, last_hit_at FROM retrieval_provider_result_cache_rows "
                "WHERE query_hash = 'qh-1'"
            ).fetchone()
        finally:
            conn.close()
        assert hit_count == 1
        assert last_hit_at is not None

    def test_wal_mode_effect_on_real_cache_db_path_is_a_documented_deliberate_choice(self):
        """DD4 — this ticket's Level 1 write functions are the first real callers of
        knowledge_gateway_redaction.open_connection_with_limits() against the real (tmp_path-
        isolated-in-tests) CACHE_DB_PATH. WAL mode is file-persistent; asserting it here is the
        regression guard against a future contributor silently reverting or silently extending
        this deliberately-accepted effect (see tools/retrieval_cache.py::_get_level1_connection's
        own docstring and this ticket's plan.md DD4)."""
        _write_row()
        conn = rc._get_connection()
        try:
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        finally:
            conn.close()
        assert journal_mode.lower() == "wal"

    def test_migration_001_still_never_called_from_the_original_six_check_or_write_functions(self):
        hot_path_functions = [
            rc.check_index_cache, rc.check_query_cache, rc.check_packet_cache,
            rc.write_index_cache, rc.write_query_cache, rc.write_packet_cache,
        ]
        for func in hot_path_functions:
            source = inspect.getsource(func)
            assert "migration_001" not in source


class TestMigration003:
    def test_migration_003_adds_column_to_fresh_database(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)
            columns = [row[1] for row in conn.execute(
                "PRAGMA table_info(retrieval_provider_result_cache_rows)"
            )]
        finally:
            conn.close()
        assert "redaction_policy_version" in columns

    def test_migration_003_is_idempotent_on_already_migrated_database(self):
        conn = rc._get_connection()
        try:
            rc.migration_001_add_level1_tables(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)
            rc.migration_003_add_redaction_policy_version_column(conn)  # must not raise
            columns = [row[1] for row in conn.execute(
                "PRAGMA table_info(retrieval_provider_result_cache_rows)"
            )]
        finally:
            conn.close()
        assert columns.count("redaction_policy_version") == 1

    def test_migration_003_preserves_existing_rows_and_the_20_other_columns(self):
        _write_row(query_hash="qh-preserve", redaction_policy_version=None)
        conn = rc._get_connection()
        try:
            rc.migration_003_add_redaction_policy_version_column(conn)
            row = conn.execute(
                "SELECT query_hash, normalized_intent, result_payload "
                "FROM retrieval_provider_result_cache_rows WHERE query_hash = 'qh-preserve'"
            ).fetchone()
        finally:
            conn.close()
        assert row == ("qh-preserve", "what is x", '{"answer": "x"}')

    def test_migration_002_landed_with_the_reserved_name_not_stubbed_or_renamed(self):
        """Prior to TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS, this test guarded
        ordinal 2 against premature/stubbed reuse by asserting "migration_002" was absent from
        the source entirely. That ticket has now landed the real migration_002_add_level2_tables
        function at the reserved ordinal (see TestLevel2Migrations), fulfilling the reservation
        this guard used to protect -- updated here (not deleted) so the guard still catches a
        stub or a rename, rather than being left asserting a now-false claim."""
        source = Path(rc.__file__).read_text()
        assert "def migration_002_add_level2_tables(" in source
        assert source.count("def migration_002_add_level2_tables(") == 1


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

    def test_check_and_write_functions_now_exist_for_the_new_level2_table(self):
        """TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING inverts this guard's premise: real
        check_context_packet_cache()/write_context_packet_cache() functions now exist. Replaces
        (not deletes) the old test_no_actual_read_write_functions_added_for_the_new_level2_table,
        whose own premise this ticket makes false — still a real, replacement guard against a
        stub/rename, not a coverage regression."""
        assert callable(rc.check_context_packet_cache)
        assert callable(rc.write_context_packet_cache)
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
            "check_provider_result_cache",
            "check_context_packet_cache",
            "write_index_cache",
            "write_query_cache",
            "write_packet_cache",
            "write_provider_result_cache",
            "write_context_packet_cache",
        }

    def test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration(self):
        source = Path(rc.__file__).read_text()
        assert "PRAGMA journal_mode" not in source
        assert "PRAGMA busy_timeout" not in source
        assert "busy_timeout" not in source
        assert "os.chmod" not in source
        assert "chmod" not in source

        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert "os" not in imported_modules


class TestProviderResultCacheStats:
    def test_provider_result_cache_stats_zero_on_fresh_db(self):
        assert rc.provider_result_cache_stats() == {"total_rows": 0, "total_hits": 0}

    def test_provider_result_cache_stats_reflects_real_rows_and_hits(self):
        _write_row(query_hash="qh-a")
        _write_row(query_hash="qh-b")
        rc.record_provider_result_cache_hit("qh-a", "repo::main")
        rc.record_provider_result_cache_hit("qh-a", "repo::main")
        stats = rc.provider_result_cache_stats()
        assert stats == {"total_rows": 2, "total_hits": 2}


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
    rc.write_context_packet_cache(**kwargs)


class TestContextPacketCache:
    def test_check_context_packet_cache_creates_table_on_first_real_use(self):
        result = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=4000,
        )
        assert result.status == rc.MISS
        conn = rc._get_connection()
        try:
            table_names = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
        assert "retrieval_context_packet_cache_rows" in table_names

    def test_fresh_nonexistent_db_gets_migration_001_applied_before_migration_002_on_first_level2_access(
        self,
    ):
        """Deviation 1 (plan.md/investigation.md): _get_level2_connection()/
        _ensure_level2_schema_for_read() must call migration_001_add_level1_tables(conn) before
        migration_002_add_level2_tables(conn), because migration_002 itself assumes
        retrieval_cache_generation (created only by migration_001) already exists. This test
        touches Level 2 *first* on a genuinely non-existent DB file (never calling any Level 1
        function or migration directly) and asserts both migrations' real effects are present --
        not just that no exception was raised, but that migration_001's own tables genuinely
        exist too, proving the ordering fix, not merely tolerating its absence."""
        assert not rc.CACHE_DB_PATH.exists(), "the DB file must be genuinely non-existent first"

        result = rc.check_context_packet_cache(
            "qkh-fresh", normalized_intent="fresh db query", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=4000,
        )
        assert result.status == rc.MISS

        conn = rc._get_connection()
        try:
            table_names = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            generation_row = conn.execute(
                "SELECT retrieval_cache_schema_version FROM retrieval_cache_generation"
            ).fetchone()
        finally:
            conn.close()

        # migration_002's own effects (Level 2 table exists).
        assert "retrieval_context_packet_cache_rows" in table_names
        # migration_001's own effects (Level 1 tables + the generation-metadata row migration_002
        # depends on) must also be present -- this is the real proof migration_001 ran first.
        assert "retrieval_cache_generation" in table_names
        assert generation_row is not None, (
            "retrieval_cache_generation must have a stamped row, proving migration_001 (not just "
            "table creation) genuinely ran before migration_002 on a fresh Level-2-first access"
        )

    def test_check_context_packet_cache_miss_on_no_row(self):
        result = rc.check_context_packet_cache(
            "no-such-hash", normalized_intent="x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=4000,
        )
        assert result.status == rc.MISS
        assert result.reason_code == "no_cached_row"
        assert result.row is None

    def test_check_context_packet_cache_hit_on_matching_full_identity(self):
        _write_level2_row()
        result = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=4000,
        )
        assert result.status == rc.HIT
        assert result.reason_code is None
        assert result.row["answer"] == "an answer"

    def test_check_context_packet_cache_miss_on_identity_mismatch_despite_shared_query_key_hash(
        self,
    ):
        _write_level2_row()
        result = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="feature-x", budget_tokens=4000,
        )
        assert result.status == rc.MISS
        assert result.reason_code == "identity_mismatch_on_shared_key"
        assert result.row is None

    def test_level2_lookup_disambiguates_multiple_rows_sharing_the_same_query_key_hash(self):
        """Directly targets Risk 3 -- query_key_hash is unindexed/non-unique, packet_id is the
        real PK. Seeds two rows sharing the same query_key_hash but different branch, and asserts
        the lookup returns the correct row for the current scope, never the first row an unordered
        fetchall() happens to return."""
        _write_level2_row(packet_id="p-main", branch="main", answer="main answer")
        _write_level2_row(packet_id="p-feature", branch="feature-x", answer="feature answer")

        main_result = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=4000,
        )
        assert main_result.status == rc.HIT
        assert main_result.row["answer"] == "main answer"

        feature_result = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="feature-x", budget_tokens=4000,
        )
        assert feature_result.status == rc.HIT
        assert feature_result.row["answer"] == "feature answer"

    def test_level2_lookup_disambiguates_by_budget_tokens_not_just_budget_class(self):
        """plan.md PD2 -- budget_tokens is part of Level 2's real identity, not budget_class. Two
        rows sharing everything except budget_requested must never collide."""
        _write_level2_row(packet_id="p-small-budget", budget_requested=600, answer="answer-600")
        _write_level2_row(packet_id="p-large-budget", budget_requested=1800, answer="answer-1800")

        result_600 = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=600,
        )
        assert result_600.status == rc.HIT
        assert result_600.row["answer"] == "answer-600"

        result_1800 = rc.check_context_packet_cache(
            "qkh-1", normalized_intent="what is x", entity_ids_json="[]",
            repository_id="repo-a", branch="main", budget_tokens=1800,
        )
        assert result_1800.status == rc.HIT
        assert result_1800.row["answer"] == "answer-1800"

    def test_lookup_function_never_returns_a_freshness_or_verification_field(self):
        field_names = {f.name for f in dataclasses.fields(rc.ContextPacketCacheLookup)}
        assert "freshness" not in field_names
        assert "verification" not in field_names
        assert field_names == {"status", "reason_code", "row"}

    def test_write_context_packet_cache_creates_table_and_inserts_row(self):
        _write_level2_row()
        conn = rc._get_connection()
        try:
            rows = conn.execute(
                "SELECT packet_id, redaction_policy_version "
                "FROM retrieval_context_packet_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("p-1", 1)]

    def test_write_context_packet_cache_insert_or_replace_overwrites_same_pk(self):
        _write_level2_row(answer="first")
        _write_level2_row(answer="second")
        conn = rc._get_connection()
        try:
            rows = conn.execute(
                "SELECT answer FROM retrieval_context_packet_cache_rows"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("second",)]

    def test_level2_write_stamps_redaction_policy_version_column(self):
        _write_level2_row(redaction_policy_version=1)
        conn = rc._get_connection()
        try:
            value = conn.execute(
                "SELECT redaction_policy_version FROM retrieval_context_packet_cache_rows "
                "WHERE packet_id = 'p-1'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert value == 1

    def test_record_context_packet_cache_hit_increments_hit_count_and_stamps_last_validated_at(
        self,
    ):
        _write_level2_row()
        rc.record_context_packet_cache_hit("p-1")
        conn = rc._get_connection()
        try:
            hit_count, last_validated_at = conn.execute(
                "SELECT hit_count, last_validated_at FROM retrieval_context_packet_cache_rows "
                "WHERE packet_id = 'p-1'"
            ).fetchone()
        finally:
            conn.close()
        assert hit_count == 1
        assert last_validated_at is not None


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
        rc.record_context_packet_cache_hit("p-a")
        rc.record_context_packet_cache_hit("p-a")
        stats = rc.context_packet_cache_stats()
        assert stats == {"total_rows": 2, "total_hits": 2}
