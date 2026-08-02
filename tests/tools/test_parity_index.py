"""
Tests for tools/parity_index.py (TCK-20260731-PARITY-INDEX-IMPORTER).

Groups:
  1. atomic lifecycle (sibling temp file, .gitignore)
  2. shard import (all nine shards, byte hashes, duplicate id, malformed shard)
  3. reference tables (joins, anti-invention)
  4. entry_health (missing evidence)
  5. FTS5 (present + forced-unavailable fallback)
  6. atomic failure safety (prior-good db preserved, source never written)
  7. determinism
  8. architecture guards (anti-drift)
"""
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_MODULE_PATH = _REPO_ROOT / "tools" / "parity_index.py"


def _load_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("parity_index", _MODULE_PATH)
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_pi = _load_module()

_NINE_SHARD_FILENAMES = (
    "combat_movement.yaml",
    "faction.yaml",
    "infrastructure.yaml",
    "progression.yaml",
    "social_narrative.yaml",
    "strategic_cognition.yaml",
    "substrate.yaml",
    "town_resource.yaml",
    "world_dynamics.yaml",
)


def _entry(
    entry_id,
    text="Some parity statement.",
    status="verified",
    priority="P1",
    legacy_evidence=None,
    v2_evidence=None,
    proof_type="parity",
    test_path=None,
    divergence_note=None,
    support_boundary=None,
) -> dict:
    return {
        "id": entry_id,
        "text": text,
        "status": status,
        "priority": priority,
        "legacy_evidence": legacy_evidence,
        "v2_evidence": v2_evidence,
        "proof_type": proof_type,
        "test_path": test_path,
        "divergence_note": divergence_note,
        "support_boundary": support_boundary,
    }


def _write_shard(ledger_dir: Path, filename: str, entries: list) -> Path:
    path = ledger_dir / filename
    path.write_text(yaml.safe_dump(entries, sort_keys=False))
    return path


def _make_corpus(tmp_path: Path, shards: dict) -> dict:
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    shard_paths = {}
    for filename, entries in shards.items():
        shard_paths[filename] = _write_shard(ledger_dir, filename, entries)
    db_path = tmp_path / "index" / "parity.db"
    return {"ledger_dir": ledger_dir, "shard_paths": shard_paths, "db_path": db_path}


def _full_nine_shard_corpus(tmp_path: Path) -> dict:
    shards = {
        filename: [_entry(f"{filename[:4].upper()}-001")]
        for filename in _NINE_SHARD_FILENAMES
    }
    return _make_corpus(tmp_path, shards)


# ---------------------------------------------------------------------------
# Group 1 — atomic lifecycle
# ---------------------------------------------------------------------------


class TestAtomicLifecycle:

    def test_build_uses_sibling_temp_file_then_atomic_replace(self, tmp_path):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        assert "if db_path.exists():" not in source
        assert "os.replace(" in source

        paths = _full_nine_shard_corpus(tmp_path)
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        assert report["status"] == "ok"
        assert paths["db_path"].exists()
        leftovers = list(paths["db_path"].parent.glob(".*.tmp-*"))
        assert leftovers == []

    def test_db_not_tracked_by_git(self):
        gitignore = (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "parity-index/" in gitignore

        result = subprocess.run(
            ["git", "check-ignore", "-v", "parity-index/parity.db"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, "parity-index/parity.db is not git-ignored"


# ---------------------------------------------------------------------------
# Group 2 — shard import
# ---------------------------------------------------------------------------


class TestShardImport:

    def test_importer_imports_all_nine_shards(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        assert report["status"] == "ok"
        assert report["shard_count"] == 9
        assert report["entry_count"] == 9

        conn = sqlite3.connect(str(paths["db_path"]))
        shards_in_db = {row[0] for row in conn.execute("SELECT DISTINCT shard FROM entries")}
        conn.close()
        assert shards_in_db == set(_NINE_SHARD_FILENAMES)

    def test_importer_preserves_source_byte_hashes(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)
        before = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        after = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }
        assert before == after

        conn = sqlite3.connect(str(paths["db_path"]))
        shard_manifest_json = conn.execute(
            "SELECT shard_manifest_json FROM ledger_generation"
        ).fetchone()[0]
        conn.close()
        shard_manifest = json.loads(shard_manifest_json)
        recorded_hashes = {entry["filename"]: entry["sha256"] for entry in shard_manifest}
        assert recorded_hashes == before

    def test_duplicate_cross_shard_id_rejected_at_import(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [_entry("DUP-001")],
                "faction.yaml": [_entry("DUP-001")],
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        assert report["status"] == "failed"
        assert report["failure_class"] == "DuplicateEntryIdError"
        assert not paths["db_path"].exists()

    def test_malformed_yaml_shard_produces_classified_finding_not_crash(self, tmp_path):
        paths = _make_corpus(tmp_path, {"combat_movement.yaml": [_entry("COMB-001")]})
        (paths["ledger_dir"] / "faction.yaml").write_text("id: [unterminated\n  - broken: yaml")

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        assert report["status"] == "failed"
        assert report["failure_class"] == "ShardParseError"
        assert not paths["db_path"].exists()


# ---------------------------------------------------------------------------
# Group 3 — reference tables
# ---------------------------------------------------------------------------


class TestReferenceTables:

    def test_entries_table_supports_join_to_code_test_constraint_ticket_refs(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-001",
                        v2_evidence=(
                            "`src/engine/legality.py` implements this; see "
                            "`docs/mechanics/02_combat_laws.md` and TCK-20260101-EXAMPLE-TICKET."
                        ),
                        test_path="tests/parity/test_movement_parity.py",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        code = conn.execute(
            "SELECT entries.id FROM entries JOIN code_refs ON code_refs.entry_id = entries.id "
            "WHERE entries.id = ?",
            ("COMB-001",),
        ).fetchall()
        test = conn.execute(
            "SELECT entries.id FROM entries JOIN test_refs ON test_refs.entry_id = entries.id "
            "WHERE entries.id = ?",
            ("COMB-001",),
        ).fetchall()
        constraint = conn.execute(
            "SELECT entries.id FROM entries JOIN constraint_refs ON constraint_refs.entry_id = entries.id "
            "WHERE entries.id = ?",
            ("COMB-001",),
        ).fetchall()
        ticket = conn.execute(
            "SELECT entries.id FROM entries JOIN ticket_refs ON ticket_refs.entry_id = entries.id "
            "WHERE entries.id = ?",
            ("COMB-001",),
        ).fetchall()
        conn.close()

        assert code and code[0][0] == "COMB-001"
        assert test and test[0][0] == "COMB-001"
        assert constraint and constraint[0][0] == "COMB-001"
        assert ticket and ticket[0][0] == "COMB-001"

    def test_unparseable_code_ref_never_invents_a_link(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-002",
                        v2_evidence="See the migration guide in the wiki for details.",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        counts = {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE entry_id = ?", ("COMB-002",)
            ).fetchone()[0]
            for table in ("code_refs", "test_refs", "constraint_refs", "ticket_refs")
        }
        finding = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'legacy_unstructured'",
            ("COMB-002",),
        ).fetchall()
        conn.close()

        assert counts == {"code_refs": 0, "test_refs": 0, "constraint_refs": 0, "ticket_refs": 0}
        assert finding


# ---------------------------------------------------------------------------
# Group 4 — entry_health
# ---------------------------------------------------------------------------


class TestEntryHealth:

    def test_missing_test_path_produces_entry_health_finding(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-003",
                        status="verified",
                        v2_evidence="`src/engine/legality.py`",
                        test_path=None,
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        finding = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'missing_test_path'",
            ("COMB-003",),
        ).fetchall()
        conn.close()

        assert finding
        assert report["health_finding_counts"]["missing_test_path"] >= 1


# ---------------------------------------------------------------------------
# Group 5 — FTS5
# ---------------------------------------------------------------------------


class TestFts5:

    def test_fts5_present_populates_entry_fts_table(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {"combat_movement.yaml": [_entry("COMB-004", text="Manhattan distance rules movement.")]},
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"
        assert report["fts5_available"] is True

        conn = sqlite3.connect(str(paths["db_path"]))
        rows = conn.execute("SELECT id FROM entry_fts WHERE entry_fts MATCH 'Manhattan'").fetchall()
        conn.close()

        assert rows and rows[0][0] == "COMB-004"

    def test_fts5_forced_unavailable_falls_back_to_exact_lookup(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {"combat_movement.yaml": [_entry("COMB-005", text="Manhattan distance rules movement.")]},
        )

        report = _pi.build(
            ledger_dir=paths["ledger_dir"], db_path=paths["db_path"], force_fts5_unavailable=True
        )
        assert report["status"] == "ok"
        assert report["fts5_available"] is False
        assert report["ledger_generation"]["fts5_available"] is False

        conn = sqlite3.connect(str(paths["db_path"]))
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
        assert "entry_fts" not in tables
        row = conn.execute("SELECT id, text FROM entries WHERE id = ?", ("COMB-005",)).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "COMB-005"


# ---------------------------------------------------------------------------
# Group 6 — atomic failure safety
# ---------------------------------------------------------------------------


class TestAtomicFailureSafety:

    def test_failed_build_preserves_prior_good_db_byte_identical(self, tmp_path):
        paths = _make_corpus(tmp_path, {"combat_movement.yaml": [_entry("COMB-006")]})
        good_report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert good_report["status"] == "ok"
        good_bytes = paths["db_path"].read_bytes()

        _write_shard(
            paths["ledger_dir"],
            "faction.yaml",
            [_entry("COMB-006")],  # duplicate of combat_movement.yaml's id
        )
        failed_report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])

        assert failed_report["status"] == "failed"
        assert paths["db_path"].read_bytes() == good_bytes
        leftovers = list(paths["db_path"].parent.glob(".*.tmp-*"))
        assert leftovers == []

    def test_failed_build_never_writes_to_source_yaml(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [_entry("DUP-002")],
                "faction.yaml": [_entry("DUP-002")],
            },
        )
        before = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "failed"

        after = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }
        assert before == after


# ---------------------------------------------------------------------------
# Group 7 — determinism
# ---------------------------------------------------------------------------


class TestDeterminism:

    def test_build_is_deterministic_on_unchanged_source(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)

        def _snapshot(db_path):
            conn = sqlite3.connect(str(db_path))
            snapshot = {
                "entries": conn.execute("SELECT * FROM entries ORDER BY shard, id").fetchall(),
                "entry_health": conn.execute(
                    "SELECT * FROM entry_health ORDER BY entry_id, finding_type"
                ).fetchall(),
                "ledger_generation": dict(
                    zip(
                        [d[0] for d in conn.execute("SELECT * FROM ledger_generation").description],
                        conn.execute("SELECT * FROM ledger_generation").fetchone(),
                    )
                ),
            }
            conn.close()
            return snapshot

        _pi.build(ledger_dir=paths["ledger_dir"], db_path=tmp_path / "first" / "parity.db")
        first = _snapshot(tmp_path / "first" / "parity.db")

        _pi.build(ledger_dir=paths["ledger_dir"], db_path=tmp_path / "second" / "parity.db")
        second = _snapshot(tmp_path / "second" / "parity.db")

        assert first["entries"] == second["entries"]
        assert first["entry_health"] == second["entry_health"]

        first_gen = dict(first["ledger_generation"])
        second_gen = dict(second["ledger_generation"])
        # built_at is a wall-clock timestamp and is legitimately expected to
        # differ between runs -- excluded from the equality check by design,
        # not a determinism gap.
        del first_gen["built_at"]
        del second_gen["built_at"]
        assert first_gen == second_gen


# ---------------------------------------------------------------------------
# Group 8 — architecture guards (anti-drift)
# ---------------------------------------------------------------------------


class TestArchitectureGuards:

    def test_importer_does_not_implement_impact_or_entry_or_health_cli(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        assert 'add_parser("impact"' not in source
        assert 'add_parser("search"' not in source
        assert 'add_parser("entry"' not in source
        assert 'add_parser("health"' not in source

        result = subprocess.run(
            [sys.executable, str(_MODULE_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + result.stderr
        assert "build" in combined
        assert "impact" not in combined
        assert "entry" not in combined

    def test_no_mutation_cli_or_write_path_to_docs_parity_ledger(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        assert "parity-record" not in source
        assert "parity_record" not in source

        import re as _re

        forbidden_write_calls = _re.findall(
            r'open\([^)]*["\']w["\'][^)]*\)|\.write_text\([^)]*\)', source
        )
        for call in forbidden_write_calls:
            assert "docs/parity_ledger" not in call
