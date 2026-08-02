"""Read-only importer: rebuild the derived SQLite parity-ledger index.

Phase 1 of the parity-ledger SQLite context work
(docs/plans/agent_infrastructure/parity_ledger_sqlite_context/), built for
TCK-20260731-PARITY-INDEX-IMPORTER on top of TCK-20260731-PARITY-INDEX-BASELINE's
evidence-capture precedent. This module dynamically globs every current
docs/parity_ledger/*.yaml shard (all nine, including faction.yaml -- deliberately
independent of tools.parity_ledger_scan.CANONICAL_LEDGER_FILES's frozen 8-file
compatibility list) and imports them into a local, gitignored, derived-only SQLite
database (default parity-index/parity.db). It never writes into docs/parity_ledger/
and implements no mutation CLI ("build" is the only subcommand).

Build lifecycle: a sibling temporary database file is created next to the final
path, populated and validated in full, then atomically swapped into place with
os.replace. This deliberately does NOT copy tools/agent-monitoring/build_index.py's
delete-the-existing-file-then-rebuild-in-place pattern -- that
lifecycle leaves no usable database if a rebuild crashes partway through. A failed
build here (malformed shard, duplicate cross-shard id, or a post-build validation
failure) deletes only the temporary file and never touches the last-good database
or any source YAML.

entry_health is a materialized table, not a live SQL VIEW, because its
absent_file finding requires a filesystem Path.exists() check that cannot be
expressed as portable SQL without registering a custom SQLite function. This is a
documented interpretation of the idea doc's "view" language, not a scope
reduction -- see staging_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/plan.md
Step 4.

Reference resolution (code_refs/test_refs/constraint_refs/ticket_refs) is
path-level string matching only, per v1_decisions_phase0.md's "Path-only links"
decision -- no Graphify symbol resolution. A field with no confident match
produces no row anywhere; nothing is fabricated.

impact_candidates (the Phase-2 impact query view) is intentionally not built
here -- see TCK-20260731-PARITY-IMPACT-PROOF.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_index_baseline import _sha256_hex, serialize_manifest  # noqa: E402

SCHEMA_VERSION = 1
IMPORTER_VERSION = "1.0.0"

DEFAULT_LEDGER_DIR = Path("docs/parity_ledger")
DEFAULT_DB_PATH = Path("parity-index/parity.db")

_TEST_PATH_DECLARED_RE = re.compile(r"^tests/[\w./:-]+\.py(::[\w_]+)?$")
_PATH_REF_RE = re.compile(r"\b(?:src|tools|tests|docs)/[\w./-]+\.\w+\b")
_TICKET_REF_RE = re.compile(r"\bTCK-\d{8}-[A-Z0-9-]+\b")
_CONSTRAINT_DOC_PREFIXES = (
    "docs/mechanics/",
    "docs/engine/",
    "docs/architecture/",
    "docs/guidelines/",
    "docs/core/",
)

_REF_TABLES = ("code_refs", "test_refs", "constraint_refs", "ticket_refs")

_EXPECTED_COLUMNS = {
    "ledger_generation": {
        "schema_version", "importer_version", "built_at", "source_manifest_hash",
        "shard_manifest_json", "shard_count", "entry_count", "fts5_available",
    },
    "entries": {
        "id", "shard", "subsystem", "entry_order", "text", "status", "priority",
        "legacy_evidence", "v2_evidence", "proof_type", "test_path",
        "divergence_note", "support_boundary", "canonical_fragment_hash",
    },
    "code_refs": {"id", "entry_id", "path", "relation", "source_field"},
    "test_refs": {"id", "entry_id", "path", "relation", "source_field"},
    "constraint_refs": {"id", "entry_id", "path", "relation", "source_field"},
    "ticket_refs": {"id", "entry_id", "path", "relation", "source_field"},
    "entry_health": {"entry_id", "finding_type", "detail"},
}


class ShardParseError(Exception):
    def __init__(self, filename: str, message: str):
        self.filename = filename
        self.message = message
        super().__init__(f"failed to parse shard {filename!r}: {message}")


class DuplicateEntryIdError(Exception):
    def __init__(self, entry_id: str, filenames: list):
        self.entry_id = entry_id
        self.filenames = filenames
        super().__init__(f"duplicate entry id {entry_id!r} found in shards {filenames!r}")


class BuildValidationError(Exception):
    pass


def _probe_fts5(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE _fts5_probe")
        return True
    except sqlite3.OperationalError:
        return False


def _create_schema(conn: sqlite3.Connection, fts5_available: bool) -> None:
    conn.execute(
        """
        CREATE TABLE ledger_generation (
            schema_version INTEGER,
            importer_version TEXT,
            built_at TEXT,
            source_manifest_hash TEXT,
            shard_manifest_json TEXT,
            shard_count INTEGER,
            entry_count INTEGER,
            fts5_available INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE entries (
            id TEXT PRIMARY KEY,
            shard TEXT NOT NULL,
            subsystem TEXT NOT NULL,
            entry_order INTEGER NOT NULL,
            text TEXT,
            status TEXT,
            priority TEXT,
            legacy_evidence TEXT,
            v2_evidence TEXT,
            proof_type TEXT,
            test_path TEXT,
            divergence_note TEXT,
            support_boundary TEXT,
            canonical_fragment_hash TEXT NOT NULL
        )
        """
    )
    for table in _REF_TABLES:
        conn.execute(
            f"""
            CREATE TABLE {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT NOT NULL REFERENCES entries(id),
                path TEXT NOT NULL,
                relation TEXT,
                source_field TEXT NOT NULL
            )
            """
        )
    conn.execute(
        """
        CREATE TABLE entry_health (
            entry_id TEXT NOT NULL REFERENCES entries(id),
            finding_type TEXT NOT NULL,
            detail TEXT
        )
        """
    )
    if fts5_available:
        conn.execute(
            "CREATE VIRTUAL TABLE entry_fts USING fts5(id, text, subsystem, status, v2_evidence)"
        )


def _load_shards(ledger_dir: Path) -> list:
    shard_paths = sorted(ledger_dir.glob("*.yaml"))
    shards = []
    for path in shard_paths:
        try:
            raw_entries = yaml.safe_load(path.read_text()) or []
        except yaml.YAMLError as exc:
            raise ShardParseError(path.name, str(exc)) from exc
        shards.append({"filename": path.name, "entries": raw_entries, "sha256": _sha256_hex(path)})
    return shards


def _populate_entries(conn: sqlite3.Connection, shards: list) -> int:
    seen_ids = {}
    total = 0
    for shard in shards:
        subsystem = shard["filename"][: -len(".yaml")]
        for order, entry in enumerate(shard["entries"]):
            entry_id = entry.get("id")
            if entry_id in seen_ids:
                raise DuplicateEntryIdError(entry_id, [seen_ids[entry_id], shard["filename"]])
            seen_ids[entry_id] = shard["filename"]

            fragment_hash = hashlib.sha256(
                json.dumps(entry, sort_keys=True, ensure_ascii=True).encode("utf-8")
            ).hexdigest()

            conn.execute(
                """
                INSERT INTO entries (
                    id, shard, subsystem, entry_order, text, status, priority,
                    legacy_evidence, v2_evidence, proof_type, test_path,
                    divergence_note, support_boundary, canonical_fragment_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    shard["filename"],
                    subsystem,
                    order,
                    entry.get("text"),
                    entry.get("status"),
                    entry.get("priority"),
                    entry.get("legacy_evidence"),
                    entry.get("v2_evidence"),
                    entry.get("proof_type"),
                    entry.get("test_path"),
                    entry.get("divergence_note"),
                    entry.get("support_boundary"),
                    fragment_hash,
                ),
            )
            total += 1
    return total


def _populate_ref_tables(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, v2_evidence, legacy_evidence, text, test_path FROM entries ORDER BY shard, id"
    ).fetchall()
    inserted = set()

    def _insert(table, entry_id, path, relation, source_field):
        key = (table, entry_id, path)
        if key in inserted:
            return
        inserted.add(key)
        conn.execute(
            f"INSERT INTO {table} (entry_id, path, relation, source_field) VALUES (?, ?, ?, ?)",
            (entry_id, path, relation, source_field),
        )

    for entry_id, v2_evidence, legacy_evidence, text, test_path in rows:
        if test_path and _TEST_PATH_DECLARED_RE.match(test_path):
            _insert("test_refs", entry_id, test_path, "declared", "test_path")

        for source_field, field_value in (
            ("v2_evidence", v2_evidence),
            ("legacy_evidence", legacy_evidence),
            ("text", text),
        ):
            if not field_value:
                continue
            for match in _PATH_REF_RE.finditer(field_value):
                matched_path = match.group(0)
                if matched_path.startswith(("src/", "tools/")):
                    _insert("code_refs", entry_id, matched_path, None, source_field)
                elif matched_path.startswith("tests/"):
                    _insert("test_refs", entry_id, matched_path, None, source_field)
                elif matched_path.startswith(_CONSTRAINT_DOC_PREFIXES):
                    _insert("constraint_refs", entry_id, matched_path, None, source_field)
                # Any other src/tools/tests/docs-prefixed match (e.g. a bare docs/
                # path outside the five recognized constraint subdirectories) is a
                # low-confidence match and is deliberately left uninserted anywhere.
            for match in _TICKET_REF_RE.finditer(field_value):
                _insert("ticket_refs", entry_id, match.group(0), None, source_field)


def _populate_entry_health(conn: sqlite3.Connection) -> dict:
    counts = {"missing_test_path": 0, "missing_v2_evidence": 0, "legacy_unstructured": 0, "absent_file": 0}

    def _insert(entry_id, finding_type, detail):
        conn.execute(
            "INSERT INTO entry_health (entry_id, finding_type, detail) VALUES (?, ?, ?)",
            (entry_id, finding_type, detail),
        )
        counts[finding_type] += 1

    entries = conn.execute(
        "SELECT id, status, v2_evidence, legacy_evidence, test_path FROM entries ORDER BY shard, id"
    ).fetchall()

    entries_with_refs = set()
    for table in _REF_TABLES:
        for (entry_id,) in conn.execute(f"SELECT DISTINCT entry_id FROM {table}"):
            entries_with_refs.add(entry_id)

    for entry_id, status, v2_evidence, legacy_evidence, test_path in entries:
        if status in ("verified", "divergent"):
            if not test_path:
                _insert(entry_id, "missing_test_path", f"status={status}")
            if not v2_evidence:
                _insert(entry_id, "missing_v2_evidence", f"status={status}")
        if (v2_evidence or legacy_evidence) and entry_id not in entries_with_refs:
            _insert(
                entry_id,
                "legacy_unstructured",
                "v2_evidence/legacy_evidence present but no structured reference was parsed",
            )

    for table in ("code_refs", "test_refs", "constraint_refs"):
        for entry_id, path in conn.execute(f"SELECT entry_id, path FROM {table}"):
            if not (_REPO_ROOT / path).exists():
                _insert(entry_id, "absent_file", f"{table}:{path}")

    return counts


def _populate_entry_fts(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, text, subsystem, status, v2_evidence FROM entries ORDER BY shard, id"
    ).fetchall()
    conn.executemany(
        "INSERT INTO entry_fts (id, text, subsystem, status, v2_evidence) VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def _validate_build(conn: sqlite3.Connection, shard_manifest: list, entry_count: int, fts5_available: bool) -> None:
    expected_entry_count = sum(s["entry_count"] for s in shard_manifest)
    if entry_count != expected_entry_count:
        raise BuildValidationError(
            f"entries row count {entry_count} != shard manifest total {expected_entry_count}"
        )
    actual_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    if actual_count != entry_count:
        raise BuildValidationError(f"entries table has {actual_count} rows, expected {entry_count}")

    tables_to_check = dict(_EXPECTED_COLUMNS)
    if fts5_available:
        tables_to_check["entry_fts"] = {"id", "text", "subsystem", "status", "v2_evidence"}

    for table, expected_cols in tables_to_check.items():
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if not rows:
            raise BuildValidationError(f"expected table {table!r} missing from build")
        actual_cols = {row[1] for row in rows}
        if not expected_cols.issubset(actual_cols):
            missing = expected_cols - actual_cols
            raise BuildValidationError(f"table {table!r} missing expected columns: {missing}")


def _build_into(conn: sqlite3.Connection, ledger_dir: Path, force_fts5_unavailable: bool) -> dict:
    fts5_available = False if force_fts5_unavailable else _probe_fts5(conn)
    _create_schema(conn, fts5_available)

    shards = _load_shards(ledger_dir)

    entry_count = _populate_entries(conn, shards)
    _populate_ref_tables(conn)
    health_counts = _populate_entry_health(conn)
    if fts5_available:
        _populate_entry_fts(conn)

    shard_manifest = [
        {"filename": s["filename"], "sha256": s["sha256"], "entry_count": len(s["entries"])}
        for s in shards
    ]
    shard_manifest_json = serialize_manifest(shard_manifest)
    source_manifest_hash = hashlib.sha256(shard_manifest_json.encode("utf-8")).hexdigest()
    built_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO ledger_generation (
            schema_version, importer_version, built_at, source_manifest_hash,
            shard_manifest_json, shard_count, entry_count, fts5_available
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            SCHEMA_VERSION,
            IMPORTER_VERSION,
            built_at,
            source_manifest_hash,
            shard_manifest_json,
            len(shards),
            entry_count,
            1 if fts5_available else 0,
        ),
    )

    _validate_build(conn, shard_manifest, entry_count, fts5_available)

    return {
        "status": "ok",
        "ledger_generation": {
            "schema_version": SCHEMA_VERSION,
            "importer_version": IMPORTER_VERSION,
            "built_at": built_at,
            "source_manifest_hash": source_manifest_hash,
            "shard_count": len(shards),
            "entry_count": entry_count,
            "fts5_available": fts5_available,
        },
        "shard_count": len(shards),
        "entry_count": entry_count,
        "fts5_available": fts5_available,
        "health_finding_counts": health_counts,
    }


def _atomic_replace_db(build_fn, final_path: Path) -> dict:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{final_path.name}.tmp-", dir=str(final_path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)

    conn = sqlite3.connect(str(tmp_path))
    try:
        report = build_fn(conn)
        conn.commit()
    except Exception:
        conn.close()
        tmp_path.unlink(missing_ok=True)
        raise
    conn.close()

    fd2 = os.open(str(tmp_path), os.O_RDONLY)
    try:
        os.fsync(fd2)
    finally:
        os.close(fd2)

    os.replace(str(tmp_path), str(final_path))
    return report


def build(
    ledger_dir=None,
    db_path=None,
    force_fts5_unavailable: bool = False,
) -> dict:
    ledger_path = DEFAULT_LEDGER_DIR if ledger_dir is None else Path(ledger_dir)
    final_path = DEFAULT_DB_PATH if db_path is None else Path(db_path)
    try:
        return _atomic_replace_db(
            lambda conn: _build_into(conn, ledger_path, force_fts5_unavailable),
            final_path,
        )
    except (ShardParseError, DuplicateEntryIdError, BuildValidationError) as exc:
        return {
            "status": "failed",
            "failure_class": type(exc).__name__,
            "detail": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only importer: rebuild the derived SQLite parity-ledger index."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build", help="Rebuild parity-index/parity.db from docs/parity_ledger/*.yaml"
    )
    build_parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    build_parser.add_argument("--force-fts5-unavailable", action="store_true")

    args = parser.parse_args()

    report = build(db_path=args.db_path, force_fts5_unavailable=args.force_fts5_unavailable)
    print(serialize_manifest(report), end="")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
