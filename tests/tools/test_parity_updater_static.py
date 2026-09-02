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

import pytest

from gate_checks.parity_updater_static import (  # noqa: E402
    CANONICAL_LEDGER_FILES,
    cross_reference_touched,
    derive_mapping,
    expected_subsystems_for_files,
    next_available_id,
    search_existing_entries,
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


def test_includes_faction_yaml(tmp_path):
    _write_ledger(tmp_path, "faction.yaml", [
        {
            "id": "FAC-001", "text": "x", "status": "verified", "priority": "P1",
            "v2_evidence": "src/factions/diplomacy.py", "test_path": "tests/unit/test_diplomacy.py",
        },
    ])

    mapping = derive_mapping(tmp_path)
    assert mapping["src/factions/diplomacy.py"] == {"faction.yaml"}


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


def test_expected_subsystems_includes_faction_for_real_ledger_path():
    result = expected_subsystems_for_files(
        ["src/observability/event_extractor.py"], ledger_dir="docs/parity_ledger"
    )
    assert result["src/observability/event_extractor.py"] is not None
    assert "faction.yaml" in result["src/observability/event_extractor.py"]


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


# ---------------------------------------------------------------------------
# next_available_id
# ---------------------------------------------------------------------------


def test_next_available_id_uses_max_suffix_not_count(tmp_path):
    # IDs are not dense — INFRA-379 is the real-world precedent (384 entries, highest id 379).
    # Reproduced here with a small gapped shard: 3 entries, but the max suffix is 7.
    _write_ledger(tmp_path, "infrastructure.yaml", [
        {"id": "INFRA-001", "text": "a", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
        {"id": "INFRA-003", "text": "b", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
        {"id": "INFRA-007", "text": "c", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])

    assert next_available_id("infrastructure.yaml", ledger_dir=tmp_path) == "INFRA-008"


def test_next_available_id_derives_prefix_and_width_from_shard(tmp_path):
    _write_ledger(tmp_path, "town_resource.yaml", [
        {"id": "TOWN-041", "text": "a", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])

    assert next_available_id("town_resource.yaml", ledger_dir=tmp_path) == "TOWN-042"


def test_next_available_id_raises_on_shard_with_no_valid_ids(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [])

    with pytest.raises(ValueError):
        next_available_id("combat_movement.yaml", ledger_dir=tmp_path)


def test_next_available_id_accepts_multi_segment_id(tmp_path):
    # TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT
    _write_ledger(tmp_path, "world_dynamics.yaml", [
        {"id": "WORLD-DEMO-001", "text": "a", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
        {"id": "WORLD-DEMO-002", "text": "b", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])

    assert next_available_id("world_dynamics.yaml", ledger_dir=tmp_path) == "WORLD-DEMO-003"


def test_next_available_id_groups_max_suffix_per_prefix_family_not_globally(tmp_path):
    # A shard mixing a bare-prefix family (WORLD-NNN) with a higher-numbered multi-segment
    # family (WORLD-DEMO-NNN) must never let one family's suffix leak into the other's count --
    # reproduces the real world_dynamics.yaml shape (WORLD-001..119 alongside WORLD-DEMO-001..006).
    _write_ledger(tmp_path, "world_dynamics.yaml", [
        {"id": "WORLD-119", "text": "a", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
        {"id": "WORLD-DEMO-001", "text": "b", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
        {"id": "WORLD-DEMO-006", "text": "c", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])

    assert next_available_id("world_dynamics.yaml", ledger_dir=tmp_path) == "WORLD-DEMO-007"


def test_next_available_id_against_real_world_dynamics_shard():
    # Real-corpus regression proof (ticket AC): the live shard's last entry is now a bare
    # WORLD-NNN id (WORLD-123, added by TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE
    # for the individual-birth population-pressure nudge mechanism itself), so this must
    # propose the next id in that family, WORLD-124.
    assert next_available_id("world_dynamics.yaml", ledger_dir="docs/parity_ledger") == "WORLD-124"


# ---------------------------------------------------------------------------
# search_existing_entries
# ---------------------------------------------------------------------------


def test_search_existing_entries_finds_case_insensitive_substring_hit(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {"id": "COMB-001", "text": "Damage formula uses TCK-20260824-PARITY-NEXT-ID-LOOKUP logic",
         "status": "verified", "priority": "P1",
         "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py"},
    ])

    results = search_existing_entries("tck-20260824-parity-next-id-lookup", ledger_dir=tmp_path)
    assert len(results) == 1
    assert results[0]["id"] == "COMB-001"
    assert results[0]["shard"] == "combat_movement.yaml"
    assert results[0]["matched_field"] == "text"
    assert "TCK-20260824-PARITY-NEXT-ID-LOOKUP" in results[0]["excerpt"]


def test_search_existing_entries_returns_empty_on_clean_miss(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {"id": "COMB-001", "text": "Damage formula", "status": "verified", "priority": "P1",
         "v2_evidence": "src/engine/foo.py", "test_path": "tests/unit/test_foo.py"},
    ])

    assert search_existing_entries("no-such-query-string", ledger_dir=tmp_path) == []


def test_search_existing_entries_scoped_to_single_shard(tmp_path):
    _write_ledger(tmp_path, "combat_movement.yaml", [
        {"id": "COMB-001", "text": "shared marker", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])
    _write_ledger(tmp_path, "town_resource.yaml", [
        {"id": "TOWN-001", "text": "shared marker", "status": "verified", "priority": "P1",
         "v2_evidence": "x", "test_path": "y"},
    ])

    results = search_existing_entries("shared marker", ledger_dir=tmp_path, shard_filename="combat_movement.yaml")
    assert len(results) == 1
    assert results[0]["shard"] == "combat_movement.yaml"
