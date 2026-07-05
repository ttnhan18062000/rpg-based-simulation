"""Tests for tools/gate_checks/parity_updater_static.py (TCK-20260705-GATE-DET-PARITY-UPDATER).

Coverage-honesty requirement (SEQUENCE.md decision 4): every check function below has at least
one fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.parity_updater_static import (  # noqa: E402
    CANONICAL_LEDGER_FILES,
    cross_reference_touched,
    derive_mapping,
    expected_subsystems_for_files,
)


def _write_ledger(tmp_path, filename, entries):
    (tmp_path / filename).write_text(yaml.safe_dump(entries))


# ---------------------------------------------------------------------------
# derive_mapping
# ---------------------------------------------------------------------------


def test_derive_mapping_reads_v2_evidence_paths(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])
    _write_ledger(tmp_path, "town_resource.yaml", [
        {
            "id": "TR-001", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/town/harvest.py", "test_path": "tests/unit/test_harvest.py",
        },
    ])

    mapping = derive_mapping(tmp_path)
    assert mapping["src/engine/foo.py"] == {"combat_movement.yaml"}
    assert mapping["src/town/harvest.py"] == {"town_resource.yaml"}


def test_derive_mapping_handles_multi_subsystem_file(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/apply.py", "test_path": "tests/unit/test_apply.py",
        },
    ])
    _write_ledger(tmp_path, "strategic_cognition.yaml", [
        {
            "id": "SC-001", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/apply.py", "test_path": "tests/unit/test_apply2.py",
        },
    ])

    mapping = derive_mapping(tmp_path)
    assert mapping["src/engine/apply.py"] == {"combat_movement.yaml", "strategic_cognition.yaml"}


def test_derive_mapping_skips_malformed_yaml_file(tmp_path):
    # Legacy-data tolerance (Anti-Drift Notes): a malformed/legacy-format YAML file must never
    # crash the derivation — caught and skipped, continuing to the next canonical file.
    (tmp_path / "combat_movement.yaml").write_text(": : : not valid yaml : : :\n\tbad indent")
    _write_ledger(tmp_path, "town_resource.yaml", [
        {
            "id": "TR-001", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/town/harvest.py", "test_path": "tests/unit/test_harvest.py",
        },
    ])

    mapping = derive_mapping(tmp_path)
    assert mapping["src/town/harvest.py"] == {"town_resource.yaml"}


def test_excludes_faction_yaml(tmp_path):
    _write_ledger(tmp_path, "faction.yaml", [
        {
            "id": "FAC-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/factions/diplomacy.py", "test_path": "tests/unit/test_diplomacy.py",
        },
    ])

    mapping = derive_mapping(tmp_path)
    assert "src/factions/diplomacy.py" not in mapping


def test_reuses_canonical_ledger_files_constant():
    from parity_ledger_scan import CANONICAL_LEDGER_FILES as SCAN_CANONICAL_LEDGER_FILES

    assert CANONICAL_LEDGER_FILES is SCAN_CANONICAL_LEDGER_FILES


# ---------------------------------------------------------------------------
# expected_subsystems_for_files
# ---------------------------------------------------------------------------


def test_non_src_paths_ignored(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])

    result = expected_subsystems_for_files(
        ["src/engine/foo.py", "tests/unit/test_foo.py", "docs/ai/workflows.md"], ledger_dir=tmp_path
    )
    assert "tests/unit/test_foo.py" not in result
    assert "docs/ai/workflows.md" not in result
    assert result["src/engine/foo.py"] == ["combat_movement.yaml"]


# ---------------------------------------------------------------------------
# cross_reference_touched
# ---------------------------------------------------------------------------


def test_flags_untouched_mapped_subsystem(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])

    results = cross_reference_touched(["src/engine/foo.py"], [], ledger_dir=tmp_path)
    by_file = {r["file"]: r for r in results}
    assert by_file["src/engine/foo.py"]["status"] == "FAIL"
    assert "combat_movement.yaml" in by_file["src/engine/foo.py"]["evidence"]


def test_does_not_flag_when_mapped_subsystem_touched(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])

    results = cross_reference_touched(
        ["src/engine/foo.py"], ["docs/parity_ledger/combat_movement.yaml"], ledger_dir=tmp_path
    )
    by_file = {r["file"]: r for r in results}
    assert by_file["src/engine/foo.py"]["status"] == "PASS"


def test_any_of_candidate_subsystems_touched_clears_flag(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/apply.py", "test_path": "tests/unit/test_apply.py",
        },
    ])
    _write_ledger(tmp_path, "strategic_cognition.yaml", [
        {
            "id": "SC-001", "text": "y", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/apply.py", "test_path": "tests/unit/test_apply2.py",
        },
    ])

    # Only combat_movement.yaml touched, strategic_cognition.yaml not touched — must still PASS
    # (ANY-of-candidates, not ALL-of-candidates). This is the guard against a future regression
    # that silently tightens multi-subsystem semantics from ANY to ALL.
    results = cross_reference_touched(
        ["src/engine/apply.py"], [" M docs/parity_ledger/combat_movement.yaml"], ledger_dir=tmp_path
    )
    by_file = {r["file"]: r for r in results}
    assert by_file["src/engine/apply.py"]["status"] == "PASS"


def test_unmapped_file_is_not_a_failure(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {
            "id": "CM-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py",
        },
    ])

    results = cross_reference_touched(["src/never/cited.py"], [], ledger_dir=tmp_path)
    by_file = {r["file"]: r for r in results}
    assert by_file["src/never/cited.py"]["status"] == "NA"
    assert by_file["src/never/cited.py"]["status"] != "FAIL"
