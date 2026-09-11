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

_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_ledger_scan import find_p0_intersection  # noqa: E402
from gate_checks.parity_updater_static import derive_mapping  # noqa: E402


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

    def test_multi_citation_test_path_produces_one_test_refs_row_per_citation(self, tmp_path):
        """Before TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT's Step 1, the old
        `_TEST_PATH_DECLARED_RE` accepted only a single bare path and rejected a `,`-joined
        multi-citation `test_path` outright -- this entry produced zero test_refs rows and its
        stale second citation was invisible to `absent_file`. The shared parser fixes this."""
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-950",
                        v2_evidence="`src/engine/legality.py`",
                        test_path=(
                            "tests/tools/test_parity_index.py::test_some_function, "
                            "tests/tools/test_nonexistent_module_xyz.py::test_other"
                        ),
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        rows = conn.execute(
            "SELECT path FROM test_refs WHERE entry_id = ? ORDER BY path", ("COMB-950",)
        ).fetchall()
        absent_file_findings = conn.execute(
            "SELECT detail FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("COMB-950",),
        ).fetchall()
        conn.close()

        assert [row[0] for row in rows] == [
            "tests/tools/test_nonexistent_module_xyz.py::test_other",
            "tests/tools/test_parity_index.py::test_some_function",
        ]
        assert any("test_nonexistent_module_xyz.py" in detail for (detail,) in absent_file_findings)
        assert not any("test_parity_index.py" in detail for (detail,) in absent_file_findings)


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

    def test_frontend_only_source_path_does_not_flag_absent_file(self, tmp_path):
        """dashboard-frontend/src/App.tsx is real, but the ledger's convention cites
        it as bare src/App.tsx -- _path_resolves() must check the dashboard-frontend/
        root as a second package root for this extension class, not just repo root."""
        paths = _make_corpus(
            tmp_path,
            {
                "infrastructure.yaml": [
                    _entry(
                        "INFRA-900",
                        status="verified",
                        v2_evidence="Dashboard root component at `src/App.tsx`.",
                        test_path="tests/tools/test_parity_index.py::dummy",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        findings = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("INFRA-900",),
        ).fetchall()
        conn.close()

        assert findings == []

    def test_genuinely_absent_source_path_still_flags_absent_file(self, tmp_path):
        """A path that resolves at neither the repo root nor dashboard-frontend/ must
        still be flagged -- the frontend second-root check must not become a blanket
        suppression of real absent_file drift."""
        paths = _make_corpus(
            tmp_path,
            {
                "infrastructure.yaml": [
                    _entry(
                        "INFRA-901",
                        status="verified",
                        v2_evidence="Removed helper at `src/nonexistent_helper_xyz.tsx`.",
                        test_path="tests/tools/test_parity_index.py::dummy",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        findings = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("INFRA-901",),
        ).fetchall()
        conn.close()

        assert findings and findings[0][0] == "absent_file"

    def test_declared_test_path_with_node_id_suffix_does_not_flag_absent_file(self, tmp_path):
        """A declared test_path like tests/x/test_y.py::test_case is a real pytest
        node id -- the `::test_case` suffix is not part of the filesystem path.
        _path_resolves() must strip it before checking existence, or every declared
        test_path with a function suffix would be wrongly flagged as absent even
        though the underlying .py file exists."""
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-900",
                        status="verified",
                        v2_evidence="See `src/engine/legality.py`.",
                        test_path="tests/tools/test_parity_index.py::test_some_function",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        findings = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("COMB-900",),
        ).fetchall()
        conn.close()

        assert findings == []

    def test_declared_test_path_with_nonexistent_file_still_flags_absent_file(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-901",
                        status="verified",
                        v2_evidence="See `src/engine/legality.py`.",
                        test_path="tests/tools/test_nonexistent_module_xyz.py::test_some_function",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        findings = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("COMB-901",),
        ).fetchall()
        conn.close()

        assert findings and findings[0][0] == "absent_file"

    def test_legacy_evidence_absent_path_does_not_flag_absent_file(self, tmp_path):
        """legacy_evidence exists specifically to document the pre-V2 implementation
        location, paired against v2_evidence's current-location claim -- it is
        expected, not anomalous, for that path to no longer exist post-migration.
        Real repo cases: SUB-007/SUB-073 correctly cite a deleted
        src/core/entities/entity_builder.py here while v2_evidence correctly cites
        the live src/core/builder.py."""
        paths = _make_corpus(
            tmp_path,
            {
                "substrate.yaml": [
                    _entry(
                        "SUB-900",
                        status="verified",
                        legacy_evidence="src/core/entities/entity_builder_removed_long_ago.py",
                        v2_evidence="`src/engine/legality.py`",
                        test_path="tests/tools/test_parity_index.py::dummy",
                    )
                ]
            },
        )

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        conn = sqlite3.connect(str(paths["db_path"]))
        findings = conn.execute(
            "SELECT finding_type FROM entry_health WHERE entry_id = ? AND finding_type = 'absent_file'",
            ("SUB-900",),
        ).fetchall()
        conn.close()

        assert findings == []


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

    def test_impact_query_is_reproducible_on_unchanged_index(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-901",
                        v2_evidence="`src/engine/legality.py`",
                        test_path="tests/parity/test_legality.py",
                    )
                ]
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        impact_1 = _pi.impact(changed_path="src/engine/legality.py", db_path=paths["db_path"])
        impact_2 = _pi.impact(changed_path="src/engine/legality.py", db_path=paths["db_path"])
        assert _pi.serialize_manifest(impact_1) == _pi.serialize_manifest(impact_2)

        entry_1 = _pi.entry("COMB-901", db_path=paths["db_path"])
        entry_2 = _pi.entry("COMB-901", db_path=paths["db_path"])
        assert _pi.serialize_manifest(entry_1) == _pi.serialize_manifest(entry_2)

        health_1 = _pi.health(db_path=paths["db_path"])
        health_2 = _pi.health(db_path=paths["db_path"])
        assert _pi.serialize_manifest(health_1) == _pi.serialize_manifest(health_2)


# ---------------------------------------------------------------------------
# Group 8 — architecture guards (anti-drift)
# ---------------------------------------------------------------------------


class TestArchitectureGuards:

    def test_impact_entry_health_still_forbid_search_cli(self):
        """Narrowed by TCK-20260731-PARITY-IMPACT-PROOF: Phase 1's guard originally forbade
        impact/entry/health entirely. Phase 2 (this ticket) is the named, anticipated
        successor authorized to add exactly those three subcommands (see Phase 1's own
        plan.md Scope Guards forward reference). Only `search` (FTS-backed) remains out of
        scope and is still asserted absent here.
        """
        source = _MODULE_PATH.read_text(encoding="utf-8")
        assert 'add_parser("search"' not in source

        result = subprocess.run(
            [sys.executable, str(_MODULE_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        combined = result.stdout + result.stderr
        assert "build" in combined
        assert "search" not in combined

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

    def test_health_subcommand_never_writes_to_docs_parity_ledger(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry("COMB-401", status="verified", v2_evidence=None, test_path=None)
                ],
                "town_resource.yaml": [
                    _entry(
                        "TOWN-401",
                        status="verified",
                        v2_evidence="unstructured text with no recognizable path",
                        test_path=None,
                    )
                ],
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        before = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }

        result = _pi.health(db_path=paths["db_path"])
        finding_types = {f["finding_type"] for f in result["findings"]}
        assert "missing_test_path" in finding_types
        assert "legacy_unstructured" in finding_types

        after = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in paths["shard_paths"].items()
        }
        assert before == after


# ---------------------------------------------------------------------------
# Group 9 — entry query (TCK-20260731-PARITY-IMPACT-PROOF)
# ---------------------------------------------------------------------------


class TestEntryQuery:

    def test_entry_returns_full_normalized_record_for_known_id(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-101",
                        v2_evidence="`src/engine/legality.py`",
                        test_path="tests/parity/test_legality.py",
                    )
                ]
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.entry("COMB-101", db_path=paths["db_path"])

        assert result["found"] is True
        assert result["entry_id"] == "COMB-101"
        assert result["record"]["id"] == "COMB-101"
        assert result["record"]["status"] == "verified"
        assert result["record"]["priority"] == "P1"
        assert any(ref["path"] == "src/engine/legality.py" for ref in result["code_refs"])
        assert any(ref["path"] == "tests/parity/test_legality.py" for ref in result["test_refs"])
        assert result["constraint_refs"] == []
        assert result["ticket_refs"] == []
        assert isinstance(result["health_findings"], list)
        for ref in result["test_refs"]:
            assert ref["selection_reason"] == "test_refs declared via test_path field"
        for ref in result["code_refs"]:
            assert ref["selection_reason"] == "code_refs match via v2_evidence field"

    def test_entry_returns_explicit_unknown_for_missing_id(self, tmp_path):
        paths = _make_corpus(tmp_path, {"combat_movement.yaml": [_entry("COMB-102")]})
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.entry("NONEXISTENT-999", db_path=paths["db_path"])

        assert result == {"entry_id": "NONEXISTENT-999", "found": False}


# ---------------------------------------------------------------------------
# Group 10 — impact query (TCK-20260731-PARITY-IMPACT-PROOF)
# ---------------------------------------------------------------------------


class TestImpactQuery:

    def test_impact_returns_sorted_deterministic_schema_for_known_changed_path(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-201",
                        priority="P1",
                        status="verified",
                        v2_evidence="`src/engine/legality.py`",
                    )
                ],
                "strategic_cognition.yaml": [
                    _entry(
                        "STRA-201",
                        priority="P0",
                        status="divergent",
                        v2_evidence="`src/engine/legality.py`",
                    )
                ],
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.impact(changed_path="src/engine/legality.py", db_path=paths["db_path"])

        assert result["status"] == "ok"
        # P0/divergent must sort ahead of P1/verified.
        assert [r["entry_id"] for r in result["results"]] == ["STRA-201", "COMB-201"]
        required_keys = {"entry_id", "priority", "status", "table", "path", "source_field", "selection_reason"}
        for row in result["results"]:
            assert required_keys <= set(row.keys())

        result_again = _pi.impact(changed_path="src/engine/legality.py", db_path=paths["db_path"])
        assert _pi.serialize_manifest(result) == _pi.serialize_manifest(result_again)

    def test_impact_returns_explicit_no_match_for_unknown_path(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry("COMB-202", v2_evidence="`src/engine/legality.py`")
                ]
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        no_match_result = _pi.impact(changed_path="src/nonexistent/path.py", db_path=paths["db_path"])
        assert no_match_result == {"status": "no_match", "results": []}

        no_filter_result = _pi.impact(db_path=paths["db_path"])
        assert no_filter_result == {"status": "no_filter_provided", "results": []}

    def test_impact_never_claims_symbol_level_match(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry("COMB-203", v2_evidence="`src/engine/legality.py`")
                ]
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.impact(
            changed_path="src/engine/legality.py",
            symbol="LegalityChecker.check",
            db_path=paths["db_path"],
        )

        assert result["status"] == "ok"
        assert "warnings" in result
        assert any("symbol" in warning.lower() for warning in result["warnings"])
        for row in result["results"]:
            assert "symbol" not in row

        result_without_symbol = _pi.impact(
            changed_path="src/engine/legality.py", db_path=paths["db_path"]
        )
        assert "warnings" not in result_without_symbol


# ---------------------------------------------------------------------------
# Group 11 — health query (TCK-20260731-PARITY-IMPACT-PROOF)
# ---------------------------------------------------------------------------


class TestHealthQuery:

    def test_health_output_is_ordered_and_machine_readable(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry("COMB-301", status="verified", v2_evidence=None, test_path=None)
                ],
                "town_resource.yaml": [
                    _entry(
                        "TOWN-301",
                        status="verified",
                        v2_evidence="unstructured text with no recognizable path",
                        test_path=None,
                    )
                ],
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.health(db_path=paths["db_path"])

        shards_in_order = [f["shard"] for f in result["findings"]]
        assert shards_in_order == sorted(shards_in_order)
        assert set(result["summary"].keys()) == {
            "schema_version", "built_at", "shard_count", "entry_count", "fts5_available",
        }

        serialized = _pi.serialize_manifest(result)
        assert serialized.endswith("\n")
        assert json.loads(serialized) == result

        result_again = _pi.health(db_path=paths["db_path"])
        assert _pi.serialize_manifest(result) == _pi.serialize_manifest(result_again)


# ---------------------------------------------------------------------------
# Group 12 — equivalence fixtures against legacy comparison targets
# (TCK-20260731-PARITY-IMPACT-PROOF)
# ---------------------------------------------------------------------------


class TestEquivalenceFixtures:

    def test_equivalence_p0_substring_vs_all_priority_documented(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "COMB-501",
                        priority="P0",
                        v2_evidence="`src/engine/legality.py`",
                        test_path="tests/parity/test_legality.py",
                    ),
                    _entry(
                        "COMB-502",
                        priority="P1",
                        v2_evidence="`src/engine/legality.py`",
                        test_path="tests/parity/test_legality2.py",
                    ),
                ],
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        # Legacy behavior: find_p0_intersection is P0-only, v2_evidence-only, substring.
        legacy_hits = find_p0_intersection(
            ["src/engine/legality.py"], ledger_dir=str(paths["ledger_dir"])
        )
        legacy_ids = {hit[1] for hit in legacy_hits}
        assert legacy_ids == {"COMB-501"}

        # New behavior: impact is all-priority by design -- an intentional, documented
        # difference from find_p0_intersection's P0-only scope, not an accidental omission.
        impact_result = _pi.impact(changed_path="src/engine/legality.py", db_path=paths["db_path"])
        impact_ids = {r["entry_id"] for r in impact_result["results"]}
        assert impact_ids == {"COMB-501", "COMB-502"}

    def test_equivalence_any_of_multi_shard_semantics_matches_legacy(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "combat_movement.yaml": [
                    _entry(
                        "CM-601",
                        v2_evidence="src/engine/apply.py",
                        test_path="tests/unit/test_apply.py",
                    )
                ],
                "strategic_cognition.yaml": [
                    _entry(
                        "SC-601",
                        v2_evidence="src/engine/apply.py",
                        test_path="tests/unit/test_apply2.py",
                    )
                ],
            },
        )
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        legacy_mapping = derive_mapping(paths["ledger_dir"])
        assert legacy_mapping["src/engine/apply.py"] == {
            "combat_movement.yaml", "strategic_cognition.yaml",
        }

        impact_result = _pi.impact(changed_path="src/engine/apply.py", db_path=paths["db_path"])
        impact_ids = {r["entry_id"] for r in impact_result["results"]}
        assert impact_ids == {"CM-601", "SC-601"}

    def test_equivalence_malformed_input_treatment_documented_as_divergence(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "town_resource.yaml": [
                    _entry(
                        "TR-701",
                        v2_evidence="src/town/harvest.py",
                        test_path="tests/unit/test_harvest.py",
                    )
                ],
            },
        )
        (paths["ledger_dir"] / "combat_movement.yaml").write_text(
            ": : : not valid yaml : : :\n\tbad indent"
        )

        # Legacy divergence: derive_mapping silently skips the malformed shard and keeps
        # going, returning a mapping built only from the valid shard.
        legacy_mapping = derive_mapping(paths["ledger_dir"])
        assert legacy_mapping["src/town/harvest.py"] == {"town_resource.yaml"}

        # New importer divergence: the same malformed shard aborts the whole build. This is
        # a labeled intentional difference (Phase 1's deliberate strengthening over the
        # legacy silent-skip) -- it must not be "fixed" to match derive_mapping's tolerance.
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "failed"
        assert report["failure_class"] == "ShardParseError"
        assert not paths["db_path"].exists()

    def test_faction_evidence_case_present_in_both_legacy_and_new_index(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            {
                "faction.yaml": [
                    _entry(
                        "FAC-801",
                        priority="P1",
                        v2_evidence="`src/factions/diplomacy.py`",
                        test_path="tests/unit/test_diplomacy.py",
                    )
                ],
            },
        )

        # find_p0_intersection now scans faction.yaml too, but FAC-801 is priority P1, so the
        # P0-only filter still excludes it -- unrelated to which files are scanned.
        legacy_hits = find_p0_intersection(
            ["src/factions/diplomacy.py"], ledger_dir=str(paths["ledger_dir"])
        )
        assert legacy_hits == []
        legacy_mapping = derive_mapping(paths["ledger_dir"])
        assert legacy_mapping["src/factions/diplomacy.py"] == {"faction.yaml"}

        # New index: faction.yaml is included like any other shard.
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        entry_result = _pi.entry("FAC-801", db_path=paths["db_path"])
        assert entry_result["found"] is True

        impact_result = _pi.impact(
            changed_path="src/factions/diplomacy.py", db_path=paths["db_path"]
        )
        assert impact_result["status"] == "ok"
        assert any(r["entry_id"] == "FAC-801" for r in impact_result["results"])


# ---------------------------------------------------------------------------
# Group 13 — all-nine-shards coverage via entry/impact (TCK-20260731-PARITY-IMPACT-PROOF)
# ---------------------------------------------------------------------------


class TestAllShardsCoverage:

    def test_impact_and_entry_cover_all_nine_shards_including_faction(self, tmp_path):
        shards = {
            filename: [_entry(f"{filename[:4].upper()}-001")]
            for filename in _NINE_SHARD_FILENAMES
        }
        shards["faction.yaml"] = [
            _entry("FACT-001", v2_evidence="`src/factions/diplomacy.py`")
        ]
        paths = _make_corpus(tmp_path, shards)

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        for filename in _NINE_SHARD_FILENAMES:
            entry_id = f"{filename[:4].upper()}-001"
            result = _pi.entry(entry_id, db_path=paths["db_path"])
            assert result["found"] is True, f"entry {entry_id} from {filename} not found"

        impact_result = _pi.impact(
            changed_path="src/factions/diplomacy.py", db_path=paths["db_path"]
        )
        assert impact_result["status"] == "ok"
        assert any(r["entry_id"] == "FACT-001" for r in impact_result["results"])


# ---------------------------------------------------------------------------
# Group 14 — staleness check (TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY)
# ---------------------------------------------------------------------------


class TestCheckStaleness:

    def test_check_staleness_not_built_when_db_missing(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)
        result = _pi.check_staleness(db_path=paths["db_path"], ledger_dir=paths["ledger_dir"])
        assert result["status"] == "NOT_BUILT"

    def test_check_staleness_fresh_immediately_after_build(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        result = _pi.check_staleness(db_path=paths["db_path"], ledger_dir=paths["ledger_dir"])
        assert result["status"] == "FRESH"
        assert result["db_hash"] == result["live_hash"]

    def test_check_staleness_stale_after_shard_edit(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)
        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        # Append a real, valid new entry to one shard -- a genuine live-ledger edit.
        edited_filename = "combat_movement.yaml"
        existing = yaml.safe_load((paths["ledger_dir"] / edited_filename).read_text())
        existing.append(_entry("COMB-STALE-001"))
        (paths["ledger_dir"] / edited_filename).write_text(yaml.safe_dump(existing, sort_keys=False))

        result = _pi.check_staleness(db_path=paths["db_path"], ledger_dir=paths["ledger_dir"])
        assert result["status"] == "STALE"
        assert result["db_hash"] != result["live_hash"]

    def test_check_staleness_reuses_load_shards_not_reimplemented(self, tmp_path):
        """The live_hash check_staleness() computes must be byte-identical to what a fresh
        build() into a second scratch DB would produce for the same ledger dir -- proves the
        check can't silently drift from what a real build actually hashes."""
        paths = _full_nine_shard_corpus(tmp_path)
        report1 = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report1["status"] == "ok"

        staleness = _pi.check_staleness(db_path=paths["db_path"], ledger_dir=paths["ledger_dir"])
        assert staleness["status"] == "FRESH"

        second_db_path = paths["db_path"].parent / "second.db"
        report2 = _pi.build(ledger_dir=paths["ledger_dir"], db_path=second_db_path)
        assert report2["status"] == "ok"
        assert report2["ledger_generation"]["source_manifest_hash"] == staleness["live_hash"]

    def test_check_staleness_cli_exit_code(self, tmp_path):
        paths = _full_nine_shard_corpus(tmp_path)

        # NOT_BUILT -> exit 1
        result = subprocess.run(
            [
                sys.executable, str(_MODULE_PATH), "check-staleness",
                "--db-path", str(paths["db_path"]), "--ledger-dir", str(paths["ledger_dir"]),
            ],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 1

        report = _pi.build(ledger_dir=paths["ledger_dir"], db_path=paths["db_path"])
        assert report["status"] == "ok"

        # FRESH -> exit 0
        result = subprocess.run(
            [
                sys.executable, str(_MODULE_PATH), "check-staleness",
                "--db-path", str(paths["db_path"]), "--ledger-dir", str(paths["ledger_dir"]),
            ],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0

        edited_filename = "combat_movement.yaml"
        existing = yaml.safe_load((paths["ledger_dir"] / edited_filename).read_text())
        existing.append(_entry("COMB-STALE-002"))
        (paths["ledger_dir"] / edited_filename).write_text(yaml.safe_dump(existing, sort_keys=False))

        # STALE -> exit 1
        result = subprocess.run(
            [
                sys.executable, str(_MODULE_PATH), "check-staleness",
                "--db-path", str(paths["db_path"]), "--ledger-dir", str(paths["ledger_dir"]),
            ],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Group 15 — real-ledger CI collision guard (TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS)
# ---------------------------------------------------------------------------


class TestRealLedgerCollisionGuard:
    """Wires the existing DuplicateEntryIdError detector (build(), via _populate_shards()) into
    CI against the real, live docs/parity_ledger/*.yaml corpus — not a synthetic fixture. Before
    this ticket, the detector was only exercised by test_duplicate_cross_shard_id_rejected_at_import
    (a tmp_path fixture proving the LOGIC works) and by `make parity-index`, explicitly marked
    "(on-demand only — not CI)" in the Makefile and never referenced in
    .github/workflows/test.yml — so a real cross-shard ID collision reaching main (the exact
    failure mode this session hit three times) would never fail a CI job. This test carries no
    @pytest.mark.slow marker, so it runs inside the api-tools CI job's existing
    `pytest tests/tools -m "not slow"` invocation with zero .github/workflows/test.yml edits —
    same zero-new-CI-wiring pattern TCK-20260709-REGISTRY-DRIFT-CHECK-GATE already established
    for docs/REGISTRY.yaml's own real-corpus drift check
    (TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry in
    tests/tools/test_generate_registry.py)."""

    def test_build_against_real_docs_parity_ledger_has_no_duplicate_ids(self, tmp_path):
        report = _pi.build(
            ledger_dir=_REPO_ROOT / "docs" / "parity_ledger", db_path=tmp_path / "real_ledger.db"
        )
        assert report["status"] == "ok", (
            f"Real docs/parity_ledger/*.yaml corpus failed to build cleanly — "
            f"{report.get('failure_class')}: {report.get('detail')}"
        )
