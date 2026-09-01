"""Tests for tools/parity_ledger_writer.py (TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL)."""

import inspect
import sys
from pathlib import Path

import pytest
import yaml

_TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import parity_index as pi  # noqa: E402
import parity_ledger_writer as plw  # noqa: E402
from parity_ledger_writer import EntryValidationError, validate_entry, write_entry  # noqa: E402

_MODULE_PATH = _TOOLS_DIR / "parity_ledger_writer.py"
_AGENT_DOC_PATH = (
    Path(__file__).resolve().parent.parent.parent / ".claude" / "agents" / "parity-updater.md"
)


def _entry(
    entry_id="SUB-001",
    text="x",
    status="verified",
    priority="P1",
    v2_evidence="src/core/state.py",
    test_path="tests/unit/test_x.py::test_x",
    divergence_note=None,
    proof_type=None,
):
    return {
        "id": entry_id,
        "text": text,
        "status": status,
        "priority": priority,
        "v2_evidence": v2_evidence,
        "test_path": test_path,
        "divergence_note": divergence_note,
        "proof_type": proof_type,
    }


def _write_shard(tmp_path, filename, entries):
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir(exist_ok=True)
    shard_path = ledger_dir / filename
    shard_path.write_text(yaml.safe_dump(entries, sort_keys=False))
    return ledger_dir, shard_path


class TestValidateEntryRejections:

    def test_writer_rejects_bad_id_pattern(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(entry_id="not-a-valid-id")

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "id"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_verified_missing_v2_evidence(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(entry_id="SUB-002", status="verified", v2_evidence=None)

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "v2_evidence"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_verified_missing_test_path(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(entry_id="SUB-002", status="verified", test_path=None)

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "test_path"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_divergent_missing_v2_evidence(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(
            entry_id="SUB-002", status="divergent", v2_evidence=None, divergence_note="because"
        )

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "v2_evidence"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_divergent_missing_test_path(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(
            entry_id="SUB-002", status="divergent", test_path=None, divergence_note="because"
        )

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "test_path"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_divergent_missing_divergence_note(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(entry_id="SUB-002", status="divergent", divergence_note=None)

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "divergence_note"
        assert shard_path.read_bytes() == before

    def test_writer_rejects_p0_missing_test_path(self, tmp_path):
        ledger_dir, shard_path = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        before = shard_path.read_bytes()
        bad_entry = _entry(
            entry_id="SUB-002", status="missing", priority="P0",
            v2_evidence=None, test_path=None,
        )

        with pytest.raises(EntryValidationError) as excinfo:
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db")
        assert excinfo.value.field == "test_path"
        assert shard_path.read_bytes() == before


class TestValidateEntryAcceptance:

    @pytest.mark.parametrize(
        "entry_id",
        ["WORLD-DEMO-001", "WORLD-DEMO-006", "WORLD-CULT-001", "WORLD-CULT-003"],
    )
    def test_writer_accepts_multi_segment_ids(self, entry_id):
        # TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT: these ids are already live in
        # docs/parity_ledger/world_dynamics.yaml -- _ID_PATTERN must accept them, not just
        # synthetic single-segment fixtures.
        validate_entry(_entry(entry_id=entry_id))

    def test_writer_accepts_valid_verified_entry_and_writes_shard(self, tmp_path):
        ledger_dir = tmp_path / "ledger"
        ledger_dir.mkdir()
        good_entry = _entry(entry_id="SUB-003", status="verified")

        result = write_entry(
            "substrate.yaml", good_entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db"
        )

        assert result["status"] == "ok"
        assert result["entry_id"] == "SUB-003"
        written = yaml.safe_load((ledger_dir / "substrate.yaml").read_text())
        assert written == [good_entry]

    def test_writer_accepts_missing_status_without_evidence(self, tmp_path):
        ledger_dir = tmp_path / "ledger"
        ledger_dir.mkdir()
        entry = _entry(
            entry_id="SUB-004", status="missing", priority="P1",
            v2_evidence=None, test_path=None,
        )

        # must not raise
        validate_entry(entry)
        result = write_entry(
            "substrate.yaml", entry, ledger_dir=ledger_dir, db_path=tmp_path / "parity.db"
        )
        assert result["status"] == "ok"


class TestArchitectureGuards:

    def test_writer_never_bypasses_validation_via_direct_yaml_dump(self):
        source = inspect.getsource(write_entry)
        assert "yaml.dump(" not in source

        validate_call_index = source.index("validate_entry(")
        write_call_indexes = [
            index for index in (
                source.find("write_text("),
                source.find("yaml.safe_dump("),
            ) if index != -1
        ]
        assert write_call_indexes, "expected at least one write call in write_entry"
        assert all(validate_call_index < index for index in write_call_indexes)

        full_source = _MODULE_PATH.read_text(encoding="utf-8")
        assert full_source.count("write_text(") == 1
        assert full_source.count("yaml.safe_dump(") == 1


class TestIndexRebuildOnWrite:

    def test_successful_write_rebuilds_index_in_same_run(self, tmp_path):
        ledger_dir = tmp_path / "ledger"
        ledger_dir.mkdir()
        db_path = tmp_path / "parity.db"
        good_entry = _entry(entry_id="SUB-005", status="verified")

        write_entry("substrate.yaml", good_entry, ledger_dir=ledger_dir, db_path=db_path)

        staleness = pi.check_staleness(db_path=db_path, ledger_dir=ledger_dir)
        assert staleness["status"] == "FRESH"

    def test_failed_write_never_triggers_index_rebuild(self, tmp_path, monkeypatch):
        ledger_dir, _ = _write_shard(tmp_path, "substrate.yaml", [_entry()])
        db_path = tmp_path / "parity.db"
        pre_build_report = pi.build(ledger_dir=ledger_dir, db_path=db_path)
        assert pre_build_report["status"] == "ok"
        staleness_before = pi.check_staleness(db_path=db_path, ledger_dir=ledger_dir)

        calls = []
        monkeypatch.setattr(plw, "build", lambda **kwargs: calls.append(kwargs))

        bad_entry = _entry(entry_id="SUB-002", status="verified", v2_evidence=None)
        with pytest.raises(EntryValidationError):
            write_entry("substrate.yaml", bad_entry, ledger_dir=ledger_dir, db_path=db_path)

        assert calls == []
        staleness_after = pi.check_staleness(db_path=db_path, ledger_dir=ledger_dir)
        assert staleness_after == staleness_before


class TestParityUpdaterAgentDocUsesNewWritePath:

    def test_parity_updater_agent_md_uses_new_write_path(self):
        text = _AGENT_DOC_PATH.read_text()
        assert "parity_ledger_writer" in text
        assert "write_entry" in text
        assert "python3 tools/parity_index.py build" in text


_WORLD_DYNAMICS_LEDGER_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "parity_ledger" / "world_dynamics.yaml"
)


class TestValidateEntryAgainstRealMultiSegmentCorpus:
    """TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT AC: validate_entry() must accept the
    real, already-live WORLD-DEMO-*/WORLD-CULT-* entries in docs/parity_ledger/world_dynamics.yaml,
    not just synthetic fixtures."""

    def test_real_world_demo_and_world_cult_entries_pass_validate_entry(self):
        entries = yaml.safe_load(_WORLD_DYNAMICS_LEDGER_PATH.read_text())
        multi_segment_entries = [
            entry for entry in entries
            if entry.get("id", "").startswith(("WORLD-DEMO-", "WORLD-CULT-"))
        ]
        assert len(multi_segment_entries) >= 9, (
            "expected the known WORLD-DEMO-001..006 and WORLD-CULT-001..003 entries to still be "
            "present in world_dynamics.yaml"
        )
        for entry in multi_segment_entries:
            validate_entry(entry)


_INFRASTRUCTURE_LEDGER_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "parity_ledger" / "infrastructure.yaml"
)


class TestInfra352DocumentsChangedPathsIntegrationDecision:
    """Content-lock for TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT's INFRA-352 entry (plan.md
    Step 3): asserts the entry's real, written text/support_boundary still discloses both the
    live integration point (a) wiring and the declined integration point (b) decision, so a
    future silent edit that drops either half of the record fails this test rather than eroding
    unnoticed. Mirrors the doc-content-assertion pattern in
    test_evidence_cache_identity_contract.py::
    test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented (asserts
    specific substrings are present in a frozen doc rather than re-testing the underlying code)."""

    @staticmethod
    def _infra_352_entry():
        entries = yaml.safe_load(_INFRASTRUCTURE_LEDGER_PATH.read_text())
        for entry in entries:
            if entry.get("id") == "INFRA-352":
                return entry
        raise AssertionError("INFRA-352 entry not found in docs/parity_ledger/infrastructure.yaml")

    def test_infra_352_documents_changed_paths_integration_decision(self):
        entry = self._infra_352_entry()

        assert "changed_paths" in entry["text"]
        assert "working_tree_overlap_forces_revalidation" in entry["text"]

        assert "impact" in entry["support_boundary"]
        assert (
            "test_changed_path_impact_call_is_not_wired_by_this_ticket"
            in entry["support_boundary"]
        )

        assert entry["status"] == "verified"
        assert entry["test_path"]
