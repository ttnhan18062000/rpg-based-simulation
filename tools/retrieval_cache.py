"""
tools/retrieval_cache.py — 3-level SQLite retrieval cache: embedding/index, query-result, and
context-packet, per the idea doc's Cache design table and
docs/observability/retrieval_retention_redaction_policy.md's Decision C category names and
MAY-Contain/PROHIBITED field list.

What this is: three independently-invalidatable SQLite tables
(retrieval_index_cache_rows / retrieval_query_cache_rows / retrieval_packet_cache_rows), each with
a narrow MAY-list-only write path (tools/retrieval_cache.py::_validate_may_list_kwargs — raises
ValueError on any field not in MAY_LIST_COLUMNS, never stores raw prompt/chunk/source text) and a
check(...) function returning hit / miss / stale-rejected plus a reason code.

What this is not: no lightweight re-ranker (that boundary belongs to the already-closed
TCK-20260729-HYBRID-RETRIEVAL-FUSION), no external vector/graph DB (SQLite only), no relationship
to src/observability/reporting/retention.py or src/core/retention.py (both out of scope for this
subsystem — this module is genuinely new code, not an extension of either), no relationship to
src/engine/world_index.py::CacheInvalidationPolicy (an unrelated, tick-scoped, in-memory spatial
index class — this module deliberately never reuses that name), no .claude/workflows/*.js wiring,
no new agent-monitoring/*.jsonl event type.

Owns its own SQLite file, knowledge-index/retrieval_cache.db, distinct from
knowledge-index/knowledge.db: tools/knowledge_search.py's cmd_build() and
cmd_build_incremental() unconditionally db_path.unlink() and rewrite knowledge.db on every
rebuild — sharing that file would silently destroy every cached row on every index rebuild. This
module never opens, imports, or references knowledge.db.

Source ticket: TCK-20260729-RETRIEVAL-CACHE-LEVELS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Imported for Level 1 provider-result-cache writes only (DD2/DD4,
# TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING) — open_connection_with_limits() applies its own
# §9 connection-tuning defaults to the real CACHE_DB_PATH, per _get_level1_connection() below. The
# 3 legacy marker-only tables' own 8 _get_connection() call sites are untouched (DD4) and never call
# this module. One-directional dependency only: knowledge_gateway_redaction.py imports nothing from
# this module (verified by direct read), so no import cycle is created.
from tools import knowledge_gateway_redaction as _kgr_redaction  # noqa: E402

# Manually bumped on breaking changes to this module's own key-derivation or invalidation logic —
# no existing "version of retrieval logic" concept exists anywhere in the repo to derive this from.
RETRIEVAL_VERSION: int = 1

# DDL/table-shape version for this module's migrations (cache_migration_plan.md §1) — distinct
# from RETRIEVAL_VERSION above (cache-key-derivation logic) and from
# tools/retrieval_events.py::retrieval_event_schema_version (event-field shape). Bumped once per
# new *table-creating* migration function added (migration_001 -> 1, migration_002 -> 2,
# migration_005_add_cache_access_log_table -> 3) — matching the real established pattern:
# migration_003/004 (ALTER TABLE ADD COLUMN against an existing table) never bumped this constant
# or stamped retrieval_cache_generation, only migration_001/002 (CREATE TABLE of a wholly new
# table) did. Never aliased to either sibling constant.
retrieval_cache_schema_version: int = 3

# Sentinel-over-fabrication precedent: tools/hybrid_retrieval.py::UNRATED,
# tools/code_test_index.py's DOCSTRING_GAP/ASSOCIATED_TESTS_GAP. If manifest.json does not exist
# (index never built), corpus_generation resolves to this explicit sentinel — never a fabricated
# timestamp.
_NO_MANIFEST = "no_manifest"

CACHE_DB_PATH: Path = Path("knowledge-index/retrieval_cache.db")
_MANIFEST_PATH: Path = Path("knowledge-index/manifest.json")

INDEX_CACHE_CATEGORY = "retrieval_index_cache"
QUERY_CACHE_CATEGORY = "retrieval_query_cache"
PACKET_CACHE_CATEGORY = "retrieval_packet_cache"

HIT = "hit"
MISS = "miss"
STALE_REJECTED = "stale-rejected"

# The load-bearing MAY-list contract with
# docs/observability/retrieval_retention_redaction_policy.md — exactly the columns the three
# tables below actually carry, restricted to hashes, IDs, counts, reason codes, scores, latency,
# version numbers, cache status, and created_at (an ordinary management column, same footing as
# reason_code/cache_status). No column named anything resembling text/prompt/chunk/payload/content
# (as opposed to *_hash/*_hashes_json).
MAY_LIST_COLUMNS: frozenset[str] = frozenset(
    {
        "content_hash",
        "embedding_version",
        "chunking_version",
        "source_id",
        "query_hash",
        "filters_hash",
        "corpus_generation",
        "retrieval_version",
        "score",
        "latency_ms",
        "packet_key_hash",
        "cited_hashes_json",
        "policy_version",
        "cache_status",
        "reason_code",
        "created_at",
    }
)

# Column set for the new Level 1 provider-result cache table (retrieval_provider_result_cache_rows),
# mapped 1:1 onto docs/plans/knowledge-gateway-mcp-proposal.md §10.2's Level 1 row-shape bullets and
# evidence_cache_identity_contract.md §1/§2's literal field names — see plan.md DD5 for the full
# per-column provenance table. NOT a write-path validation allowlist (unlike MAY_LIST_COLUMNS) —
# this ticket ships no write function for this table; this constant exists so the structural test
# below and the later read-write-wiring ticket have one documented source of truth for the column
# set, not two.
LEVEL1_CACHE_COLUMNS: frozenset[str] = frozenset(
    {
        "query_hash",
        "normalized_intent",
        "resolved_entity_ids",
        "filters",
        "budget_class",
        "routing_policy_version",
        "repo_branch_scope",
        "provider_name",
        "adapter_version",
        "result_payload",
        "source_ids",
        "source_paths",
        "provider_generation",
        "evidence_fingerprints",
        "validated_negative_scopes",
        "adapter_version_at_validation",
        "working_tree_overlap",
        "provider_generation_at_validation",
        "created_at",
        "last_hit_at",
        "hit_count",
        # 22nd column, added by migration_003_add_redaction_policy_version_column (DD3, confirmed
        # by Architecture Review) — TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING.
        "redaction_policy_version",
    }
)

# Column set for the new Level 2 assembled-context-packet cache table
# (retrieval_context_packet_cache_rows), mapped 1:1 onto
# docs/plans/knowledge-gateway-mcp-proposal.md §10.2's Level 2 row-shape bullets and §10.3's
# CachedPacket field list — see plan.md DD5 for the full per-column provenance table. One field is
# renamed from §10.3's literal `schema_version`: `response_schema_version` (DD3), to avoid colliding
# with this module's own retrieval_cache_schema_version DDL-version constant
# (cache_migration_plan.md §1). NOT a write-path validation allowlist (unlike MAY_LIST_COLUMNS) —
# this ticket ships no write function for this table; this constant exists so the structural test
# below and the later read-write-wiring ticket have one documented source of truth for the column
# set, not two.
LEVEL2_CACHE_COLUMNS: frozenset[str] = frozenset(
    {
        "packet_id",
        "normalized_intent",
        "query_key_hash",
        "entity_ids",
        "answer",
        "statements",
        "context_items",
        "evidence",
        "conflicts",
        "evidence_dependencies",
        "provenance_providers",
        "providers_consulted_this_call",
        "repository_id",
        "branch",
        "head_commit",
        "working_tree_fingerprint",
        "provider_generations",
        "policy_version",
        "response_schema_version",
        "budget_requested",
        "budget_returned",
        "status",
        "freshness",
        "verification",
        "lifecycle",
        "created_at",
        "last_validated_at",
        "hit_count",
        # 4 columns added by migration_004_add_level2_write_path_columns
        # (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING, plan.md PD4) — close the
        # redaction_policy_version persistence gap and the 3 write-fidelity gaps needed to
        # faithfully reconstruct a hit response (budget_truncated/omitted_statement_count/
        # provider_failures all exist on the live response dict but had no Level 2 column before).
        "redaction_policy_version",
        "budget_truncated",
        "omitted_statement_count",
        "provider_failures",
    }
)


# ---------------------------------------------------------------------------
# Schema / connection
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """Open CACHE_DB_PATH, creating the parent dir if needed. Never deletes/unlinks any existing
    file — unlike knowledge_search.py's rebuild functions, this module only removes rows via
    explicit per-row eviction (write_index_cache's stale-row DELETE) or the manual `prune`
    subcommand, never a whole-file rewrite.
    """
    CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB_PATH))
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_index_cache_rows (
            content_hash TEXT NOT NULL,
            embedding_version TEXT NOT NULL,
            chunking_version TEXT NOT NULL,
            source_id TEXT,
            cache_status TEXT NOT NULL,
            reason_code TEXT,
            created_at REAL NOT NULL,
            PRIMARY KEY (content_hash, embedding_version, chunking_version)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_query_cache_rows (
            query_hash TEXT NOT NULL,
            filters_hash TEXT NOT NULL,
            corpus_generation TEXT NOT NULL,
            retrieval_version INTEGER NOT NULL,
            cache_status TEXT NOT NULL,
            reason_code TEXT,
            score REAL,
            latency_ms REAL,
            created_at REAL NOT NULL,
            PRIMARY KEY (query_hash, filters_hash, corpus_generation, retrieval_version)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_packet_cache_rows (
            packet_key_hash TEXT NOT NULL PRIMARY KEY,
            cited_hashes_json TEXT NOT NULL,
            corpus_generation TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            cache_status TEXT NOT NULL,
            reason_code TEXT,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Migrations (Level 1 provider-result cache, TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS)
# ---------------------------------------------------------------------------

def migration_001_add_level1_tables(conn: sqlite3.Connection) -> None:
    """Adds the Level 1 provider-result cache table plus the retrieval_cache_generation metadata
    table, per cache_migration_plan.md §1/§2. CREATE TABLE IF NOT EXISTS only — additive, never
    touches the three existing marker-only tables. Idempotent: safe to call again on a database
    that already has this migration applied. Not called by _get_connection(), _init_schema(), or
    any check_*_cache()/write_*_cache()/prune() function (see plan.md DD6) — must be invoked
    directly.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_cache_generation (
            retrieval_cache_schema_version INTEGER NOT NULL,
            migrated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_provider_result_cache_rows (
            query_hash TEXT NOT NULL,
            normalized_intent TEXT NOT NULL,
            resolved_entity_ids TEXT NOT NULL,
            filters TEXT NOT NULL,
            budget_class TEXT,
            routing_policy_version TEXT NOT NULL,
            repo_branch_scope TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            adapter_version TEXT NOT NULL,
            result_payload TEXT NOT NULL,
            source_ids TEXT NOT NULL,
            source_paths TEXT NOT NULL,
            provider_generation TEXT NOT NULL,
            evidence_fingerprints TEXT NOT NULL,
            validated_negative_scopes TEXT,
            adapter_version_at_validation TEXT,
            working_tree_overlap TEXT,
            provider_generation_at_validation TEXT,
            created_at REAL NOT NULL,
            last_hit_at REAL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (query_hash, repo_branch_scope)
        )
        """
    )
    conn.execute("DELETE FROM retrieval_cache_generation")
    # Plan DD2 (Architecture-Review-corrected mechanism): hardcoded literal, not the live module
    # constant — decouples this migration's on-disk stamp from a constant other migrations bump.
    conn.execute(
        "INSERT INTO retrieval_cache_generation "
        "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
        (1, time.time()),
    )
    conn.commit()


def migration_002_add_level2_tables(conn: sqlite3.Connection) -> None:
    """Adds the Level 2 assembled-context-packet cache table, per cache_migration_plan.md §2 and
    proposal §10.2/§10.3. CREATE TABLE IF NOT EXISTS only — additive, never touches the 3 legacy
    marker-only tables or the Level 1 retrieval_provider_result_cache_rows table. Idempotent: safe
    to call again on a database that already has this migration applied. Not called by
    _get_connection(), _init_schema(), or _get_level1_connection() (see plan.md DD6/Out of Scope) —
    must be invoked directly. Per plan.md DD2 (Architecture-Review-corrected mechanism): stamps
    retrieval_cache_generation with its own hardcoded literal target version (2), scoped to this
    migration's own INSERT only. Neither this function nor migration_001 reads the live
    retrieval_cache_schema_version module constant when stamping retrieval_cache_generation --
    migration_001's own INSERT independently hardcodes its own literal (1), so the module constant
    (bumped to 2) can be updated freely for introspection purposes without risk of retroactively
    changing either migration's stamped output.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_context_packet_cache_rows (
            packet_id TEXT NOT NULL PRIMARY KEY,
            normalized_intent TEXT NOT NULL,
            query_key_hash TEXT NOT NULL,
            entity_ids TEXT NOT NULL,
            answer TEXT,
            statements TEXT NOT NULL,
            context_items TEXT NOT NULL,
            evidence TEXT NOT NULL,
            conflicts TEXT NOT NULL,
            evidence_dependencies TEXT NOT NULL,
            provenance_providers TEXT NOT NULL,
            providers_consulted_this_call TEXT NOT NULL,
            repository_id TEXT NOT NULL,
            branch TEXT NOT NULL,
            head_commit TEXT,
            working_tree_fingerprint TEXT,
            provider_generations TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            response_schema_version INTEGER NOT NULL,
            budget_requested INTEGER,
            budget_returned INTEGER,
            status TEXT NOT NULL,
            freshness TEXT NOT NULL,
            verification TEXT NOT NULL,
            lifecycle TEXT,
            created_at REAL NOT NULL,
            last_validated_at REAL,
            hit_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute("DELETE FROM retrieval_cache_generation")
    conn.execute(
        "INSERT INTO retrieval_cache_generation "
        "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
        (2, time.time()),
    )
    conn.commit()


def migration_003_add_redaction_policy_version_column(conn: sqlite3.Connection) -> None:
    """Adds redaction_policy_version to retrieval_provider_result_cache_rows (DD3, Architecture
    Review-confirmed, TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING). Never called from
    _get_connection()/_init_schema() or any of the original 6 check/write functions — invoked only
    from _get_level1_connection() below. Idempotent via an explicit table_info existence check
    (SQLite has no ALTER TABLE ... ADD COLUMN IF NOT EXISTS). Ordinal 3, never 2 — the
    ordinal immediately after this one is reserved for Level 2/Phase 3 tables by
    TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS's own Anti-Drift Notes and must never be reused
    or stubbed here.
    """
    columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(retrieval_provider_result_cache_rows)"
    ).fetchall()]
    if "redaction_policy_version" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_provider_result_cache_rows "
            "ADD COLUMN redaction_policy_version INTEGER"
        )
        conn.commit()


def migration_004_add_level2_write_path_columns(conn: sqlite3.Connection) -> None:
    """Adds redaction_policy_version, budget_truncated, omitted_statement_count, and
    provider_failures to retrieval_context_packet_cache_rows (plan.md PD4,
    TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING). Never called from
    _get_connection()/_init_schema() or any of the original 6 check/write functions — invoked only
    from _get_level2_connection() below. Idempotent via an explicit table_info existence check per
    column (SQLite has no ALTER TABLE ... ADD COLUMN IF NOT EXISTS), mirroring
    migration_003_add_redaction_policy_version_column's exact pattern. Ordinal 4, the next open
    ordinal after migration_003 (no migration_004_* exists anywhere in this file before this
    ticket).
    """
    columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(retrieval_context_packet_cache_rows)"
    ).fetchall()]
    added = False
    if "redaction_policy_version" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_context_packet_cache_rows "
            "ADD COLUMN redaction_policy_version INTEGER"
        )
        added = True
    if "budget_truncated" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_context_packet_cache_rows ADD COLUMN budget_truncated INTEGER"
        )
        added = True
    if "omitted_statement_count" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_context_packet_cache_rows "
            "ADD COLUMN omitted_statement_count INTEGER"
        )
        added = True
    if "provider_failures" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_context_packet_cache_rows ADD COLUMN provider_failures TEXT"
        )
        added = True
    if added:
        conn.commit()


def migration_005_add_cache_access_log_table(conn: sqlite3.Connection) -> None:
    """Adds retrieval_cache_access_log — a per-event work-attribution log for the Level 1/Level 2
    caches (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD, Scope item 1).
    Neither Level 1's retrieval_provider_result_cache_rows nor Level 2's
    retrieval_context_packet_cache_rows carries any run_id/agent/phase attribution today, and both
    tables' own hit_count/last_hit_at columns are wiped to 0/NULL on every INSERT OR REPLACE write
    (write_provider_result_cache()/write_context_packet_cache() above), silently discarding prior
    hit history — this table is additive, append-only history that is never itself INSERT OR
    REPLACE'd, so a row's presence in this log is never lost when its parent cache row is
    refreshed. CREATE TABLE IF NOT EXISTS only — additive, never touches any of the 5 existing
    cache tables or the 3 legacy marker-only tables. Idempotent: safe to call again on a database
    that already has this migration applied. Not called by _get_connection()/_init_schema() or any
    check_*_cache()/write_*_cache()/prune() function above (mirrors every prior migration's own
    "never auto-invoked from the hot read/write path" rule) — invoked only from
    _get_access_log_connection() below. Ordinal 5, the next open ordinal after migration_004 (no
    migration_005_* exists anywhere in this file before this ticket).

    Column shape: `cache_level` ('level1_provider_result' | 'level2_context_packet') plus
    event-type-appropriate key columns (query_hash/repo_branch_scope for Level 1, packet_id for
    Level 2 — both nullable, since only one set is ever populated per row) identify *which* cache
    row the event concerns; `event_type` ('hit' | 'write' | 'invalidate' — this ticket's own
    instrumentation only ever writes 'hit'/'write', since neither cache level has a distinct
    invalidate call site today, see log_cache_access()'s docstring) identifies *what* happened;
    run_id/seq/phase/agent/execution_id/provider/ticket_id are sourced from the same
    `.claude/current_run` sidecar mechanism tools/agent-monitoring/post_tool_hook.py:46-63 already
    uses for tools.jsonl attribution (read_current_run_sidecar() below, not reinvented).
    `sidecar_stale` is a real, file-existence-checked flag (see _sidecar_run_is_stale()) — TRUE
    when the sidecar's own ticket points at a ticket that has already moved to tickets/done/ (the
    exact live failure mode this ticket's own Scope item 6 documents), so a reader can distinguish
    "no attribution recorded" from "attribution recorded but known-untrustworthy" instead of
    silently trusting stale data. Every column here stays within the MAY-list vocabulary
    (docs/observability/retrieval_retention_redaction_policy.md) — IDs, hashes (by reference, never
    raw content), counts via aggregation, timestamps; no prompt/chunk/payload text.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_cache_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_level TEXT NOT NULL,
            event_type TEXT NOT NULL,
            query_hash TEXT,
            repo_branch_scope TEXT,
            packet_id TEXT,
            run_id TEXT,
            seq INTEGER,
            phase TEXT,
            agent TEXT,
            execution_id TEXT,
            provider TEXT,
            ticket_id TEXT,
            sidecar_stale INTEGER NOT NULL DEFAULT 0,
            ts REAL NOT NULL
        )
        """
    )
    conn.execute("DELETE FROM retrieval_cache_generation")
    conn.execute(
        "INSERT INTO retrieval_cache_generation "
        "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
        (3, time.time()),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# KGMCP cache-access-log — work attribution for Level 1/Level 2 cache hit/write events
# (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD)
# ---------------------------------------------------------------------------

# Relative path, matching tools/agent-monitoring/post_tool_hook.py:54's own literal
# Path(".claude/current_run") — a module attribute (not an inline literal) specifically so tests
# can monkeypatch it the same way the _isolated_cache_db fixture already monkeypatches
# CACHE_DB_PATH/_MANIFEST_PATH.
_CURRENT_RUN_SIDECAR_PATH = Path(".claude/current_run")

_ACCESS_LOG_VALID_CACHE_LEVELS = frozenset({"level1_provider_result", "level2_context_packet"})
_ACCESS_LOG_VALID_EVENT_TYPES = frozenset({"hit", "write", "invalidate"})


def _ticket_file_exists(lifecycle: str, ticket_id: str) -> bool:
    """True if tickets/{lifecycle}/{ticket_id}.md exists, either directly or nested one level
    under a todos-style subfolder (tickets/done/{folder}/{ticket_id}.md — CLAUDE.md's own Workflow
    Rule moves a whole completed folder there). Direct-path stat first (O(1), covers the large
    majority of tickets, which are flat) — rglob only as a fallback, so the common case never pays
    a directory-tree-scan cost."""
    base = _REPO_ROOT / "tickets" / lifecycle
    if not base.is_dir():
        return False
    direct = base / f"{ticket_id}.md"
    if direct.is_file():
        return True
    return any(base.rglob(f"{ticket_id}.md"))


def _sidecar_run_is_stale(effective_ticket_id: str | None) -> bool:
    """Real, file-existence-based staleness check (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-
    AND-SKILL-USAGE-DASHBOARD Scope item 6) — reproduced live during this ticket's own
    investigation: `.claude/current_run` held `{"run_id": "TCK-20260817-HOTFIX-DECISION-TRACE-
    SELECTED-MOCK-SCORE", ...}` while that exact ticket already lived under tickets/done/, not
    tickets/inprogress/ — a `search_docs` call made during unrelated, ad-hoc investigation would
    have been silently attributed to that already-closed ticket had this check not existed. Only
    ever returns True when `effective_ticket_id` is set AND it resolves to a real tickets/done/
    file AND it does NOT also exist under tickets/inprogress/ — an ad-hoc call with no ticket_id at
    all (None) is correctly NOT flagged stale (it is simply unattributed, a different and equally
    honest signal, not a false positive here)."""
    if not effective_ticket_id:
        return False
    if _ticket_file_exists("inprogress", effective_ticket_id):
        return False
    return _ticket_file_exists("done", effective_ticket_id)


def read_current_run_sidecar() -> dict:
    """Mirrors tools/agent-monitoring/post_tool_hook.py:46-63's exact `.claude/current_run` read
    pattern — same file, same key names (run_id/seq/phase/agent/execution_id/provider/ticket_id),
    same fail-silent-to-None-on-any-error convention — reused, not reinvented (no shared helper
    previously existed to import; post_tool_hook.py's own version is inlined in a try/except
    block, not an importable function). Adds one field beyond that mechanism's own scope:
    `sidecar_stale` (see _sidecar_run_is_stale()) — a run_id starting with "TCK-" is used as the
    effective ticket_id when the sidecar carries no explicit `ticket_id` of its own (the common
    case for hotfix/standard workflows, where run_id already *is* the ticket_id — confirmed by
    direct inspection of the real, live .claude/current_run sidecar during this ticket's own
    investigation)."""
    run_id = seq = phase = agent = execution_id = provider = ticket_id = None
    try:
        sidecar = json.loads(_CURRENT_RUN_SIDECAR_PATH.read_text())
        run_id = sidecar.get("run_id") or None
        seq = sidecar.get("seq") or None
        phase = sidecar.get("phase") or None
        agent = sidecar.get("agent") or None
        execution_id = sidecar.get("execution_id") or None
        provider = sidecar.get("provider") or None
        ticket_id = sidecar.get("ticket_id") or None
    except Exception:
        pass

    effective_ticket_id = ticket_id or (
        run_id if run_id and run_id.startswith("TCK-") else None
    )

    return {
        "run_id": run_id,
        "seq": seq,
        "phase": phase,
        "agent": agent,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
        "sidecar_stale": _sidecar_run_is_stale(effective_ticket_id),
    }


def _get_access_log_connection() -> sqlite3.Connection:
    """Mirrors _get_level1_connection()/_get_level2_connection()'s own connection-tuning mechanics
    exactly — opens CACHE_DB_PATH via knowledge_gateway_redaction.open_connection_with_limits(),
    not the plain _get_connection() the 3 legacy tables use. Runs migration_001 first (creates
    retrieval_cache_generation, a prerequisite migration_005 assumes exists — same ordering
    constraint _ensure_level2_schema_for_read()'s own docstring already documents for
    migration_002), then migration_005 itself."""
    conn = _kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)
    migration_001_add_level1_tables(conn)
    migration_005_add_cache_access_log_table(conn)
    return conn


def log_cache_access(
    cache_level: str,
    event_type: str,
    *,
    query_hash: str | None = None,
    repo_branch_scope: str | None = None,
    packet_id: str | None = None,
) -> None:
    """Appends one row to retrieval_cache_access_log for a real Level 1/Level 2 cache hit or
    write. Called from the 4 real instrumented call sites below
    (record_provider_result_cache_hit/write_provider_result_cache/
    record_context_packet_cache_hit/write_context_packet_cache) — never from check_*_cache()
    (a bare lookup is not itself a genuine hit; DD9's Non-collapse rule, same distinction
    record_provider_result_cache_hit()'s own docstring already draws). No 'invalidate' call site
    exists yet for either cache level (neither table has a distinct invalidation function today,
    only INSERT OR REPLACE writes) — 'invalidate' remains a valid, schema-supported event_type for
    a future caller, never emitted by this ticket's own instrumentation.

    CLAUDE.md hard rule: "Monitoring write failure must never fail the workflow." This function
    never raises — any failure (malformed sidecar, DB-open failure, disk-full) is swallowed
    silently, exactly like tools/agent-monitoring/post_tool_hook.py's own top-level try/except,
    so a logging failure here can never break the real cache write/hit it is instrumenting.
    """
    try:
        if cache_level not in _ACCESS_LOG_VALID_CACHE_LEVELS:
            return
        if event_type not in _ACCESS_LOG_VALID_EVENT_TYPES:
            return
        sidecar = read_current_run_sidecar()
        conn = _get_access_log_connection()
        try:
            conn.execute(
                "INSERT INTO retrieval_cache_access_log "
                "(cache_level, event_type, query_hash, repo_branch_scope, packet_id, run_id, seq, "
                " phase, agent, execution_id, provider, ticket_id, sidecar_stale, ts) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cache_level,
                    event_type,
                    query_hash,
                    repo_branch_scope,
                    packet_id,
                    sidecar["run_id"],
                    sidecar["seq"],
                    sidecar["phase"],
                    sidecar["agent"],
                    sidecar["execution_id"],
                    sidecar["provider"],
                    sidecar["ticket_id"],
                    int(sidecar["sidecar_stale"]),
                    time.time(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def read_cache_access_log() -> list[dict]:
    """Read-only: every row of retrieval_cache_access_log as a list of dicts, ordered by ts —
    consumed by tools/agent-monitoring/generate_retro.py::compute_kgmcp_cache_efficiency_metrics().
    Mirrors provider_result_cache_stats()/context_packet_cache_stats()'s own "never raise on a
    fresh/never-migrated DB" pattern: returns [] (not an exception) if the table does not exist
    yet. Never mutates."""
    conn = _get_connection()
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='retrieval_cache_access_log'"
        ).fetchone()
        if table_exists is None:
            return []
        rows = conn.execute(
            "SELECT * FROM retrieval_cache_access_log ORDER BY ts"
        ).fetchall()
        columns = [d[0] for d in conn.execute(
            "SELECT * FROM retrieval_cache_access_log LIMIT 0"
        ).description]
    finally:
        conn.close()
    return [dict(zip(columns, row)) for row in rows]


def _validate_may_list_kwargs(kwargs: dict, *, table: str) -> dict:
    """Single shared enforcement point for all three write_*_cache() functions (AC4) — raises
    ValueError on any kwarg not in MAY_LIST_COLUMNS, loud and immediate since this is new code
    with no existing callers a silent-drop would need to protect. created_at is stamped
    internally by the caller (time.time()) and must never arrive as a kwarg here.
    """
    if "created_at" in kwargs:
        raise ValueError(f"{table}: created_at is stamped internally, not caller-supplied")
    prohibited = set(kwargs) - MAY_LIST_COLUMNS
    if prohibited:
        raise ValueError(
            f"{table}: prohibited field(s) not in MAY_LIST_COLUMNS: {sorted(prohibited)}"
        )
    return kwargs


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _hash_filters(filters: dict) -> str:
    return _hash_text(json.dumps(filters, sort_keys=True))


def _corpus_generation() -> str:
    """Read-only proxy for corpus_generation, derived from manifest.json's existing built_at
    field (Resolved Decision 2) — never writes manifest.json, never calls
    knowledge_search.py's cmd_build/cmd_build_incremental.
    """
    if not _MANIFEST_PATH.exists():
        return _NO_MANIFEST
    data = json.loads(_MANIFEST_PATH.read_text())
    return str(data.get("built_at", _NO_MANIFEST))


# ---------------------------------------------------------------------------
# Embedding/index cache (AC1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndexCacheResult:
    status: str
    reason_code: str | None


def check_index_cache(
    content_hash: str, embedding_version: str, chunking_version: str
) -> IndexCacheResult:
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT 1 FROM retrieval_index_cache_rows
               WHERE content_hash = ? AND embedding_version = ? AND chunking_version = ?""",
            (content_hash, embedding_version, chunking_version),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return IndexCacheResult(status=MISS, reason_code="no_cached_row")
    return IndexCacheResult(status=HIT, reason_code=None)


def write_index_cache(
    content_hash: str, embedding_version: str, chunking_version: str, **may_list_kwargs
) -> None:
    """Inserts the new (content_hash, embedding_version, chunking_version) row and evicts any
    stale row(s) sharing content_hash under a different version — satisfies AC1's "changing
    either causes recompute and stale-row eviction."
    """
    validated = _validate_may_list_kwargs(may_list_kwargs, table="retrieval_index_cache_rows")
    conn = _get_connection()
    try:
        conn.execute(
            """DELETE FROM retrieval_index_cache_rows
               WHERE content_hash = ? AND (embedding_version != ? OR chunking_version != ?)""",
            (content_hash, embedding_version, chunking_version),
        )
        conn.execute(
            """INSERT OR REPLACE INTO retrieval_index_cache_rows
               (content_hash, embedding_version, chunking_version, source_id, cache_status,
                reason_code, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                content_hash,
                embedding_version,
                chunking_version,
                validated.get("source_id"),
                validated.get("cache_status", HIT),
                validated.get("reason_code"),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query-result cache (AC2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QueryCacheResult:
    status: str
    reason_code: str | None


def check_query_cache(
    query: str, filters: dict, corpus_generation: str, retrieval_version: int
) -> QueryCacheResult:
    query_hash = _hash_text(_normalize_query(query))
    filters_hash = _hash_filters(filters)
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT corpus_generation, retrieval_version FROM retrieval_query_cache_rows
               WHERE query_hash = ? AND filters_hash = ?""",
            (query_hash, filters_hash),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return QueryCacheResult(status=MISS, reason_code="no_cached_row")
    for stored_generation, stored_version in rows:
        if stored_generation == corpus_generation and stored_version == retrieval_version:
            return QueryCacheResult(status=HIT, reason_code=None)
    stored_generation, _stored_version = rows[0]
    if stored_generation != corpus_generation:
        return QueryCacheResult(status=STALE_REJECTED, reason_code="corpus_generation_mismatch")
    return QueryCacheResult(status=STALE_REJECTED, reason_code="retrieval_version_mismatch")


def write_query_cache(
    query: str,
    filters: dict,
    corpus_generation: str,
    retrieval_version: int,
    **may_list_kwargs,
) -> None:
    validated = _validate_may_list_kwargs(may_list_kwargs, table="retrieval_query_cache_rows")
    query_hash = _hash_text(_normalize_query(query))
    filters_hash = _hash_filters(filters)
    conn = _get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO retrieval_query_cache_rows
               (query_hash, filters_hash, corpus_generation, retrieval_version, cache_status,
                reason_code, score, latency_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                query_hash,
                filters_hash,
                corpus_generation,
                retrieval_version,
                validated.get("cache_status", HIT),
                validated.get("reason_code"),
                validated.get("score"),
                validated.get("latency_ms"),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Context-packet cache (AC3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PacketCacheResult:
    status: str
    reason_code: str | None


def check_packet_cache(
    packet_key_hash: str,
    current_cited_hashes: list[str],
    corpus_generation: str,
    policy_version: str,
) -> PacketCacheResult:
    """Operates on raw fields only — ContextPacket does not exist as a class yet
    (context_packet_contract.md §4), so no such class is imported or assumed here.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT cited_hashes_json, corpus_generation, policy_version
               FROM retrieval_packet_cache_rows WHERE packet_key_hash = ?""",
            (packet_key_hash,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return PacketCacheResult(status=MISS, reason_code="no_cached_row")
    stored_hashes_json, stored_generation, stored_policy_version = row
    if set(current_cited_hashes) != set(json.loads(stored_hashes_json)):
        return PacketCacheResult(status=STALE_REJECTED, reason_code="cited_hash_mismatch")
    if stored_generation != corpus_generation:
        return PacketCacheResult(status=STALE_REJECTED, reason_code="corpus_generation_mismatch")
    if stored_policy_version != policy_version:
        return PacketCacheResult(status=STALE_REJECTED, reason_code="policy_version_mismatch")
    return PacketCacheResult(status=HIT, reason_code=None)


def write_packet_cache(
    packet_key_hash: str,
    cited_hashes: list[str],
    corpus_generation: str,
    policy_version: str,
    **may_list_kwargs,
) -> None:
    validated = _validate_may_list_kwargs(may_list_kwargs, table="retrieval_packet_cache_rows")
    conn = _get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO retrieval_packet_cache_rows
               (packet_key_hash, cited_hashes_json, corpus_generation, policy_version,
                cache_status, reason_code, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                packet_key_hash,
                json.dumps(sorted(cited_hashes)),
                corpus_generation,
                policy_version,
                validated.get("cache_status", HIT),
                validated.get("reason_code"),
                time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Level 1 provider-result cache (§1/§2 identity fields) — read/write, orchestrated by
# tools/knowledge_gateway_cache.py (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING). Follows the
# exact check/write pair shape every other cache level above already uses.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderResultCacheLookup:
    status: str                 # HIT or MISS — never a validity-verdict field (Non-collapse rule, DD9)
    reason_code: str | None
    row: dict | None            # raw stored column values, present only on HIT


def _ensure_level1_schema_for_read() -> None:
    """Guarantees retrieval_provider_result_cache_rows exists via a short-lived plain connection
    before a read — a SELECT against a missing table raises sqlite3.OperationalError on a fresh
    DB. No WAL needed for a read-only path (DD4 restricts the WAL-mode connection to writes)."""
    conn = _get_connection()
    try:
        migration_001_add_level1_tables(conn)
    finally:
        conn.close()


def check_provider_result_cache(
    query_hash: str,
    repo_branch_scope: str,
    *,
    normalized_intent: str,
    filters_json: str,
    budget_class: str,
    routing_policy_version: int,
) -> ProviderResultCacheLookup:
    """SELECT by the real primary key (query_hash, repo_branch_scope), then compare the stored
    normalized_intent/filters/budget_class/routing_policy_version columns against the caller's
    current computed values (DD10 — the PK alone is narrower than the full §1 6-field lookup
    identity: filters/budget_class/routing_policy_version are ordinary columns, not part of the
    primary key). Any mismatch is a MISS, not STALE_REJECTED — a different-identity case, not a
    staleness case, mirroring check_query_cache()'s own existing pattern of comparing
    corpus_generation/retrieval_version in Python after a broader SQL SELECT.
    routing_policy_version is stored as TEXT (see migration_001's CREATE TABLE) — the caller's int
    is coerced via str() for the comparison, matching exactly how write_provider_result_cache()
    below persists it, so the two sides are never compared across mismatched types.
    """
    _ensure_level1_schema_for_read()
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM retrieval_provider_result_cache_rows "
            "WHERE query_hash = ? AND repo_branch_scope = ?",
            (query_hash, repo_branch_scope),
        ).fetchone()
        columns = [d[0] for d in conn.execute(
            "SELECT * FROM retrieval_provider_result_cache_rows LIMIT 0"
        ).description]
    finally:
        conn.close()
    if row is None:
        return ProviderResultCacheLookup(status=MISS, reason_code="no_cached_row", row=None)
    row_dict = dict(zip(columns, row))
    if (
        row_dict["normalized_intent"] != normalized_intent
        or row_dict["filters"] != filters_json
        or row_dict["budget_class"] != budget_class
        or row_dict["routing_policy_version"] != str(routing_policy_version)
    ):
        return ProviderResultCacheLookup(
            status=MISS, reason_code="identity_mismatch_on_shared_key", row=None
        )
    return ProviderResultCacheLookup(status=HIT, reason_code=None, row=row_dict)


def _get_level1_connection() -> sqlite3.Connection:
    """DD4/DD2 — opens CACHE_DB_PATH via knowledge_gateway_redaction.open_connection_with_limits()
    (that helper's own §9 connection-tuning defaults), not the plain _get_connection() the 3 legacy
    tables use.
    Ensures the Level 1 table and the redaction_policy_version column (DD3, migration_003) exist
    before any write."""
    conn = _kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)
    migration_001_add_level1_tables(conn)
    migration_003_add_redaction_policy_version_column(conn)
    return conn


def write_provider_result_cache(
    *,
    query_hash: str, normalized_intent: str, resolved_entity_ids_json: str, filters_json: str,
    budget_class: str, routing_policy_version: int, repo_branch_scope: str,
    provider_name_json: str, adapter_version_json: str, result_payload: str,
    source_ids_json: str, source_paths_json: str, provider_generation: str,
    evidence_fingerprints_json: str, validated_negative_scopes: str | None,
    adapter_version_at_validation_json: str, working_tree_overlap_json: str,
    provider_generation_at_validation: str,
    redaction_policy_version: int | None = None,
) -> None:
    """INSERT OR REPLACE by the (query_hash, repo_branch_scope) primary key — the sole real write
    path for this table (orchestrated only by
    tools/knowledge_gateway_cache.py::perform_cache_write(), after
    knowledge_gateway_redaction.evaluate_write_candidate() has already returned ALLOW; never called
    with raw/unredacted content)."""
    conn = _get_level1_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO retrieval_provider_result_cache_rows "
            "(query_hash, normalized_intent, resolved_entity_ids, filters, budget_class, "
            " routing_policy_version, repo_branch_scope, provider_name, adapter_version, "
            " result_payload, source_ids, source_paths, provider_generation, "
            " evidence_fingerprints, validated_negative_scopes, adapter_version_at_validation, "
            " working_tree_overlap, provider_generation_at_validation, redaction_policy_version, "
            " created_at, last_hit_at, hit_count)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)",
            (
                query_hash, normalized_intent, resolved_entity_ids_json, filters_json, budget_class,
                str(routing_policy_version), repo_branch_scope, provider_name_json,
                adapter_version_json, result_payload, source_ids_json, source_paths_json,
                provider_generation, evidence_fingerprints_json, validated_negative_scopes,
                adapter_version_at_validation_json, working_tree_overlap_json,
                provider_generation_at_validation, redaction_policy_version, time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    # TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD: logged on its own
    # connection, after the real write has already committed and closed — a logging failure here
    # can never roll back or block the write above (log_cache_access() also never raises itself).
    log_cache_access(
        "level1_provider_result", "write", query_hash=query_hash, repo_branch_scope=repo_branch_scope
    )


def record_provider_result_cache_hit(query_hash: str, repo_branch_scope: str) -> None:
    """Called only after a genuine, revalidated HIT (never on a bare lookup hit — DD9) —
    increments hit_count and stamps last_hit_at."""
    conn = _get_level1_connection()
    try:
        conn.execute(
            "UPDATE retrieval_provider_result_cache_rows "
            "SET hit_count = hit_count + 1, last_hit_at = ? "
            "WHERE query_hash = ? AND repo_branch_scope = ?",
            (time.time(), query_hash, repo_branch_scope),
        )
        conn.commit()
    finally:
        conn.close()
    # TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD: see write path's
    # own comment above — logged after the real hit-count update has committed and closed.
    log_cache_access(
        "level1_provider_result", "hit", query_hash=query_hash, repo_branch_scope=repo_branch_scope
    )


def provider_result_cache_stats() -> dict:
    """Read-only aggregation over retrieval_provider_result_cache_rows for
    tools/knowledge_gateway_mcp.py::_run_knowledge_status() (Step 10). Never mutates, never raises
    on a fresh/never-migrated DB (returns zeros instead) — knowledge_status must never error out
    because no cache activity has happened yet.
    """
    conn = _get_connection()
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='retrieval_provider_result_cache_rows'"
        ).fetchone()
        if table_exists is None:
            return {"total_rows": 0, "total_hits": 0}
        total = conn.execute(
            "SELECT COUNT(*) FROM retrieval_provider_result_cache_rows"
        ).fetchone()[0]
        total_hits = conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM retrieval_provider_result_cache_rows"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"total_rows": total, "total_hits": total_hits}


# ---------------------------------------------------------------------------
# Level 2 context-packet cache (§10.2/§10.3) — read/write, orchestrated by
# tools/knowledge_gateway_cache.py (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING). Follows
# the exact check/write pair shape Level 1's provider-result cache above already uses, adapted for
# packet_id being the real primary key (query_key_hash is an ordinary, non-unique, unindexed
# column — plan.md PD1/PD3).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContextPacketCacheLookup:
    status: str                 # HIT or MISS — never a validity-verdict field (Non-collapse rule)
    reason_code: str | None
    row: dict | None            # raw stored column values, present only on HIT


def _ensure_level2_schema_for_read() -> None:
    """Guarantees retrieval_context_packet_cache_rows exists via a short-lived plain connection
    before a read — a SELECT against a missing table raises sqlite3.OperationalError on a fresh
    DB. Deviation from plan.md's literal "mirrors _ensure_level1_schema_for_read() exactly, calls
    migration_002 only" text (discovered during Test-phase execution, not a silent workaround):
    migration_002_add_level2_tables() itself assumes retrieval_cache_generation already exists
    (created only by migration_001 — see TestLevel2Migrations' own class docstring in
    tests/tools/test_retrieval_cache.py, "migration_002 assumes retrieval_cache_generation already
    exists... the real chain this module's own production caller uses today is migration_001 ->
    migration_003 -> migration_002"). Level 2 is now itself a production caller of migration_002,
    reached via a hook that runs BEFORE the Level 1 hooks (plan.md Step 5) — on a genuinely fresh
    DB, migration_002 alone raises sqlite3.OperationalError: no such table:
    retrieval_cache_generation. migration_001_add_level1_tables() must run first here too,
    mirroring the same real ordering _get_level1_connection() already depends on transitively (not
    migration_003 — that migration only touches the Level 1 table, irrelevant to a Level 2
    connection)."""
    conn = _get_connection()
    try:
        migration_001_add_level1_tables(conn)
        migration_002_add_level2_tables(conn)
    finally:
        conn.close()


def check_context_packet_cache(
    query_key_hash: str,
    *,
    normalized_intent: str,
    entity_ids_json: str,
    repository_id: str,
    branch: str,
    budget_tokens: int,
) -> ContextPacketCacheLookup:
    """SELECT by the non-unique query_key_hash column (`.fetchall()`, never `.fetchone()` —
    packet_id is the real primary key, query_key_hash carries no uniqueness constraint) and
    disambiguate in Python against normalized_intent/entity_ids/repository_id/branch/
    budget_requested (plan.md PD3). Any row returned but not matching every field is a MISS with
    reason_code="identity_mismatch_on_shared_key" (mirrors check_provider_result_cache's own
    analogous Level 1 case); zero rows returned is a MISS with reason_code="no_cached_row".
    budget_requested is stored as INTEGER (migration_002's CREATE TABLE) — compared directly
    against the caller's int, no type-coercion gap exists here (unlike Level 1's
    routing_policy_version, which is stored as TEXT).
    """
    _ensure_level2_schema_for_read()
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM retrieval_context_packet_cache_rows WHERE query_key_hash = ?",
            (query_key_hash,),
        ).fetchall()
        columns = [d[0] for d in conn.execute(
            "SELECT * FROM retrieval_context_packet_cache_rows LIMIT 0"
        ).description]
    finally:
        conn.close()
    if not rows:
        return ContextPacketCacheLookup(status=MISS, reason_code="no_cached_row", row=None)
    for row in rows:
        row_dict = dict(zip(columns, row))
        if (
            row_dict["normalized_intent"] == normalized_intent
            and row_dict["entity_ids"] == entity_ids_json
            and row_dict["repository_id"] == repository_id
            and row_dict["branch"] == branch
            and row_dict["budget_requested"] == budget_tokens
        ):
            return ContextPacketCacheLookup(status=HIT, reason_code=None, row=row_dict)
    return ContextPacketCacheLookup(
        status=MISS, reason_code="identity_mismatch_on_shared_key", row=None
    )


def _get_level2_connection() -> sqlite3.Connection:
    """Mirrors _get_level1_connection() exactly in its own connection-tuning mechanics — opens
    CACHE_DB_PATH via knowledge_gateway_redaction.open_connection_with_limits() (that helper's own
    §9 connection-tuning defaults), not the plain _get_connection() the 3 legacy tables use.
    Ensures the Level 2 table and its migration_004 write-path columns exist before any write.
    Also runs migration_001_add_level1_tables() first (deviation from plan.md's literal text,
    discovered during Test-phase execution — see _ensure_level2_schema_for_read()'s own docstring
    for the full explanation): migration_002_add_level2_tables() assumes
    retrieval_cache_generation already exists, which only migration_001 creates, and Level 2's
    write hook is reached before the Level 1 write hook on a genuinely fresh DB (plan.md Step 5)."""
    conn = _kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)
    migration_001_add_level1_tables(conn)
    migration_002_add_level2_tables(conn)
    migration_004_add_level2_write_path_columns(conn)
    return conn


def write_context_packet_cache(
    *,
    packet_id: str,
    normalized_intent: str,
    query_key_hash: str,
    entity_ids_json: str,
    answer: str | None,
    statements_json: str,
    context_items_json: str,
    evidence_json: str,
    conflicts_json: str,
    evidence_dependencies_json: str,
    provenance_providers_json: str,
    providers_consulted_this_call_json: str,
    repository_id: str,
    branch: str,
    head_commit: str | None,
    working_tree_fingerprint: str | None,
    provider_generations_json: str,
    policy_version: str,
    response_schema_version: int,
    budget_requested: int | None,
    budget_returned: int | None,
    status: str,
    freshness: str,
    verification: str,
    lifecycle: str | None,
    redaction_policy_version: int | None,
    budget_truncated: bool | None,
    omitted_statement_count: int | None,
    provider_failures_json: str | None,
) -> None:
    """INSERT OR REPLACE by the packet_id primary key — the sole real write path for this table
    (orchestrated only by tools/knowledge_gateway_cache.py::perform_context_packet_cache_write(),
    after knowledge_gateway_redaction.evaluate_write_candidate() has already returned ALLOW; never
    called with raw/unredacted content). Mirrors write_provider_result_cache()'s shape exactly,
    including its conn.commit()/finally: conn.close() structure."""
    conn = _get_level2_connection()
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
                packet_id, normalized_intent, query_key_hash, entity_ids_json, answer,
                statements_json, context_items_json, evidence_json, conflicts_json,
                evidence_dependencies_json, provenance_providers_json,
                providers_consulted_this_call_json, repository_id, branch, head_commit,
                working_tree_fingerprint, provider_generations_json, policy_version,
                response_schema_version, budget_requested, budget_returned, status, freshness,
                verification, lifecycle, redaction_policy_version,
                int(budget_truncated) if budget_truncated is not None else None,
                omitted_statement_count, provider_failures_json, time.time(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    # TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD: see Level 1 write
    # path's own comment (write_provider_result_cache()) — logged after the real write has
    # already committed and closed.
    log_cache_access("level2_context_packet", "write", packet_id=packet_id)


def record_context_packet_cache_hit(packet_id: str) -> None:
    """Called only after a genuine, revalidated HIT (never on a bare lookup hit) — increments
    hit_count and stamps last_validated_at. Mirrors record_provider_result_cache_hit() exactly,
    adapted for the packet_id primary key and Level 2's last_validated_at column name (Level 1's
    equivalent column is named last_hit_at)."""
    conn = _get_level2_connection()
    try:
        conn.execute(
            "UPDATE retrieval_context_packet_cache_rows "
            "SET hit_count = hit_count + 1, last_validated_at = ? WHERE packet_id = ?",
            (time.time(), packet_id),
        )
        conn.commit()
    finally:
        conn.close()
    # TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD: see Level 1 hit
    # path's own comment (record_provider_result_cache_hit()) — logged after the real hit-count
    # update has committed and closed.
    log_cache_access("level2_context_packet", "hit", packet_id=packet_id)


def context_packet_cache_stats() -> dict:
    """Read-only aggregation over retrieval_context_packet_cache_rows for
    tools/knowledge_gateway_mcp.py::_run_knowledge_status(). Mirrors provider_result_cache_stats()
    exactly — table-existence check via sqlite_master, returns {"total_rows": 0, "total_hits": 0}
    on a fresh/never-migrated DB (never raises)."""
    conn = _get_connection()
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='retrieval_context_packet_cache_rows'"
        ).fetchone()
        if table_exists is None:
            return {"total_rows": 0, "total_hits": 0}
        total = conn.execute(
            "SELECT COUNT(*) FROM retrieval_context_packet_cache_rows"
        ).fetchone()[0]
        total_hits = conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM retrieval_context_packet_cache_rows"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"total_rows": total, "total_hits": total_hits}


# ---------------------------------------------------------------------------
# Lifecycle backstop — manual, non-hot-path prune (Durable State Rule / Decision C)
# ---------------------------------------------------------------------------

_TABLE_NAME_BY_ALIAS = {
    "index": "retrieval_index_cache_rows",
    "query": "retrieval_query_cache_rows",
    "packet": "retrieval_packet_cache_rows",
}


def prune(older_than_days: float, table: str = "all") -> dict[str, int]:
    """Deletes rows whose created_at predates (now - older_than_days). Operator-invoked only —
    never called by any check_*_cache/write_*_cache function above; those never read created_at
    for eviction decisions. No default threshold, no schedule: docs/observability/
    retrieval_retention_redaction_policy.md Decision C frames duration as "a safety backstop, not
    the primary invalidation signal" (hash/version mismatch remains primary).
    """
    threshold = time.time() - older_than_days * 86400
    table_names = (
        list(_TABLE_NAME_BY_ALIAS.values())
        if table == "all"
        else [_TABLE_NAME_BY_ALIAS[table]]
    )
    deleted_by_table: dict[str, int] = {}
    conn = _get_connection()
    try:
        for table_name in table_names:
            cursor = conn.execute(f"DELETE FROM {table_name} WHERE created_at < ?", (threshold,))
            deleted_by_table[table_name] = cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return deleted_by_table


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_stats(_args: argparse.Namespace) -> int:
    conn = _get_connection()
    try:
        for table_name in _TABLE_NAME_BY_ALIAS.values():
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"{table_name}: {count}")
    finally:
        conn.close()
    return 0


def cmd_check_index(args: argparse.Namespace) -> int:
    result = check_index_cache(args.content_hash, args.embedding_version, args.chunking_version)
    print(f"{result.status} {result.reason_code or ''}".rstrip())
    return 0


def cmd_check_query(args: argparse.Namespace) -> int:
    filters = json.loads(args.filters_json)
    result = check_query_cache(
        args.query, filters, _corpus_generation(), args.retrieval_version
    )
    print(f"{result.status} {result.reason_code or ''}".rstrip())
    return 0


def cmd_check_packet(args: argparse.Namespace) -> int:
    cited_hashes = json.loads(args.cited_hashes_json)
    result = check_packet_cache(
        args.packet_key_hash, cited_hashes, _corpus_generation(), args.policy_version
    )
    print(f"{result.status} {result.reason_code or ''}".rstrip())
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    deleted_by_table = prune(args.older_than_days, args.table)
    for table_name, count in deleted_by_table.items():
        print(f"{table_name}: deleted {count}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone SQLite-backed 3-level retrieval cache "
        "(embedding/index, query-result, context-packet)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stats", help="Print row counts per cache table")

    check_index_p = subparsers.add_parser("check-index", help="Check the embedding/index cache")
    check_index_p.add_argument("content_hash")
    check_index_p.add_argument("embedding_version")
    check_index_p.add_argument("chunking_version")

    check_query_p = subparsers.add_parser("check-query", help="Check the query-result cache")
    check_query_p.add_argument("query")
    check_query_p.add_argument("--filters-json", default="{}")
    check_query_p.add_argument("--retrieval-version", type=int, default=RETRIEVAL_VERSION)

    check_packet_p = subparsers.add_parser(
        "check-packet", help="Check the context-packet cache"
    )
    check_packet_p.add_argument("packet_key_hash")
    check_packet_p.add_argument("--cited-hashes-json", default="[]")
    check_packet_p.add_argument("--policy-version", default="1")

    prune_p = subparsers.add_parser(
        "prune", help="Manually delete rows older than a threshold (safety backstop, not scheduled)"
    )
    prune_p.add_argument("--older-than-days", type=float, required=True)
    prune_p.add_argument(
        "--table", choices=["index", "query", "packet", "all"], default="all"
    )

    return parser


_COMMAND_DISPATCH = {
    "stats": cmd_stats,
    "check-index": cmd_check_index,
    "check-query": cmd_check_query,
    "check-packet": cmd_check_packet,
    "prune": cmd_prune,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return _COMMAND_DISPATCH[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
