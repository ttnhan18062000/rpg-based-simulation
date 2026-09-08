"""
tools/knowledge_gateway_redaction.py — Pre-archival remainder of the original
`knowledge_gateway_redaction.py`.

`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` moved every symbol here that had a real consumer
outside the Knowledge Gateway MCP package to `tools/write_path_guard.py` (§2-§7 allowlist/
redaction/secret-scan/size-cap/never-cache checks, `WriteDecision`/`evaluate_write_candidate()`,
and `open_connection_with_limits()`) — see that module for the live, load-bearing code and its own
docstring for the full extraction rationale.

What remains here has zero real consumer outside the Knowledge Gateway MCP package (confirmed by
that ticket's own investigation): §9's `check_db_size_within_limit()`/
`execute_bounded_transaction()`, the per-key stampede write-guard pair
(`acquire_write_guard()`/`release_write_guard()`), and all of §10 (cache-GC eligibility
predicates). This file is archived as-is immediately after this trim, at
`tools/archive/knowledge_gateway_redaction.py`, alongside the rest of the now-deregistered
Knowledge Gateway MCP.

Originally built for TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH; trimmed by
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# §9 — SQLite operational limits (remainder)
# ---------------------------------------------------------------------------

SQLITE_MAX_DB_SIZE_BYTES: int = 256 * 1024 * 1024   # §9 table, redaction_retention_policy.md:208


def check_db_size_within_limit(db_path: Path) -> bool:
    return not db_path.exists() or db_path.stat().st_size < SQLITE_MAX_DB_SIZE_BYTES


def execute_bounded_transaction(conn: sqlite3.Connection, statements: list[tuple[str, tuple]]) -> None:
    """Executes each (sql, params) pair then commits exactly once — never leaves an open
    transaction across calls. Generic: contains no literal INSERT/UPDATE text of its own; callers
    supply statements. This ticket calls it with zero real statements in its own tests/production
    use — it exists as the reusable primitive child 3 wires real writes through.
    """
    for sql, params in statements:
        conn.execute(sql, params)
    conn.commit()


_write_locks: dict[str, threading.Lock] = {}
_write_locks_guard = threading.Lock()


def acquire_write_guard(cache_key: str) -> bool:
    """Non-blocking, in-process only — not multi-process safe (§9's own text offers either an
    INSERT OR IGNORE sentinel row or an in-process lock; this module chooses the in-process lock,
    see plan.md DD8). True if this caller may proceed; False if another in-process caller already
    holds the guard for cache_key.
    """
    with _write_locks_guard:
        lock = _write_locks.setdefault(cache_key, threading.Lock())
    return lock.acquire(blocking=False)


def release_write_guard(cache_key: str) -> None:
    with _write_locks_guard:
        lock = _write_locks.get(cache_key)
    if lock is not None and lock.locked():
        lock.release()


# ---------------------------------------------------------------------------
# §10 — Cache-GC eligibility predicates
# ---------------------------------------------------------------------------

CACHE_STATUS_WRITE_COMPLETE = "complete"

_PROTECTED_EVIDENCE_KINDS: frozenset[str] = frozenset({"SYMBOL", "FILE"})


@dataclass(frozen=True)
class CacheRowSnapshot:
    """Plan-invented convenience shape for this ticket's own pure-function GC-eligibility testing
    (plan.md DD7) — NOT a 1:1 mirror of LEVEL1_CACHE_COLUMNS (tools/retrieval_cache.py:104-128),
    which has no cache_status column. CACHE-READ-WRITE-WIRING must decide how any field here that
    has no real column counterpart (cache_status, evidence_kind,
    only_change_is_provider_generation_bump) maps onto the real 21-column row shape when it wires
    real read/write logic; this ticket's GC checks are validated only against this synthetic
    snapshot.
    """
    repo_branch_scope: str
    provider_generation: str
    hit_count: int
    created_at: float
    last_hit_at: float | None
    cache_status: str | None            # Plan-invented; see docstring above
    evidence_kind: str | None           # e.g. "SYMBOL" / "FILE" — see evidence_identity_kinds.schema.json
    only_change_is_provider_generation_bump: bool = False


def gc_eligible_expired_exact_query_result(
    snapshot: CacheRowSnapshot, *, now: float, max_age_seconds: float
) -> bool:
    return (now - snapshot.created_at) > max_age_seconds


def gc_eligible_deleted_branch_packet(snapshot: CacheRowSnapshot, *, branch_exists: bool) -> bool:
    return not branch_exists


def gc_eligible_obsolete_provider_version_row(
    snapshot: CacheRowSnapshot, *, current_provider_generation: str
) -> bool:
    return snapshot.provider_generation != current_provider_generation


def gc_eligible_low_use_regenerable_packet(
    snapshot: CacheRowSnapshot, *, low_use_threshold: int
) -> bool:
    return snapshot.hit_count < low_use_threshold


def gc_eligible_stale_row_superseded_by_refresh(
    snapshot: CacheRowSnapshot, *, superseded: bool
) -> bool:
    return superseded


def gc_eligible_failed_incomplete_write(snapshot: CacheRowSnapshot) -> bool:
    """True iff snapshot.cache_status is present and is anything other than the terminal
    CACHE_STATUS_WRITE_COMPLETE status (§10: "a row left in a non-terminal cache_status by an
    interrupted write, never a row with a completed, valid cache_status"). None means this
    synthetic field's real-table counterpart does not apply — never flagged as failed.
    """
    return snapshot.cache_status is not None and snapshot.cache_status != CACHE_STATUS_WRITE_COMPLETE


def gc_eligibility_never_flags_protected_evidence(snapshot: CacheRowSnapshot) -> bool:
    """True (never-flag) iff snapshot.evidence_kind is SYMBOL/FILE and
    only_change_is_provider_generation_bump is True — enforces
    evidence_cache_identity_contract.md §4's fallback rule (quoted at
    redaction_retention_policy.md:244-246): such a row must never be evicted on a bare
    PROVIDER_GENERATION bump alone. Callers must consult this before honoring any of the 6
    predicates above.
    """
    return (
        snapshot.evidence_kind in _PROTECTED_EVIDENCE_KINDS
        and snapshot.only_change_is_provider_generation_bump
    )
