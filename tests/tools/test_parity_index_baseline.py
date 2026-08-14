"""Tests for tools/parity_index_baseline.py (TCK-20260731-PARITY-INDEX-BASELINE).

Covers the Phase-0 baseline manifest generator's determinism/coverage, fixture-captured
legacy-tool behavior (faction/unmapped/multi-shard/malformed-YAML), the v1 decision document's
completeness, and anti-scope-creep guards proving this ticket built no database, index, or
mutation CLI. This ticket touches no `src/` code; the manifest/decision artifacts are the tested
surface.
"""

import hashlib
import inspect
import subprocess
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import parity_index_baseline  # noqa: E402
from parity_index_baseline import build_manifest, serialize_manifest  # noqa: E402
from parity_ledger_scan import CANONICAL_LEDGER_FILES, find_p0_intersection  # noqa: E402
from gate_checks.parity_updater_static import derive_mapping, expected_subsystems_for_files  # noqa: E402

LEDGER_DIR = _REPO_ROOT / "docs" / "parity_ledger"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "parity_index_baseline"
DECISION_DOC = (
    _REPO_ROOT
    / "docs"
    / "plans"
    / "agent_infrastructure"
    / "parity_ledger_sqlite_context"
    / "v1_decisions_phase0.md"
)


# ---------------------------------------------------------------------------
# Manifest determinism and coverage (Step 2)
# ---------------------------------------------------------------------------


def test_baseline_manifest_is_byte_identical_on_rerun():
    first = serialize_manifest(build_manifest(str(LEDGER_DIR)))
    second = serialize_manifest(build_manifest(str(LEDGER_DIR)))
    assert first == second


def test_baseline_manifest_covers_all_nine_shards():
    manifest = build_manifest(str(LEDGER_DIR))
    assert manifest["shard_count"] == 9
    filenames = {shard["filename"] for shard in manifest["shards"]}
    assert "faction.yaml" in filenames
    assert len(filenames) == 9


def test_baseline_manifest_source_hashes_match_live_files():
    manifest = build_manifest(str(LEDGER_DIR))
    for shard in manifest["shards"]:
        live_path = LEDGER_DIR / shard["filename"]
        expected_hash = hashlib.sha256(live_path.read_bytes()).hexdigest()
        assert shard["sha256"] == expected_hash


def test_manifest_records_both_historical_and_current_entry_counts():
    manifest = build_manifest(str(LEDGER_DIR))
    live_count = sum(
        len(yaml.safe_load(path.read_text()) or []) for path in sorted(LEDGER_DIR.glob("*.yaml"))
    )
    assert manifest["entry_count_current"] == live_count
    assert manifest["entry_count_historical_reference"] == 1936
    assert manifest["entry_count_current"] != manifest["entry_count_historical_reference"]
    assert manifest["drift"]["delta"] == live_count - 1936


def test_manifest_records_legacy_eight_shard_faction_gap():
    manifest = build_manifest(str(LEDGER_DIR))
    assert manifest["excluded_from_legacy_scan"] == ["faction.yaml"]


# ---------------------------------------------------------------------------
# Anti-drift guards (Step 2)
# ---------------------------------------------------------------------------


def test_baseline_script_never_writes_to_docs_parity_ledger(monkeypatch):
    # Static source-text guard: no write-mode string appears in the module at all, source or
    # otherwise scoped.
    source = inspect.getsource(parity_index_baseline)
    assert 'open(..., "w"' not in source
    assert "unlink(" not in source

    # Runtime guard: monkeypatch write_text/write_bytes to fail loudly if invoked against any
    # path under docs/parity_ledger while running the manifest builder end to end.
    def _forbidden_write(self, *args, **kwargs):
        if "parity_ledger" in str(self):
            raise AssertionError(f"unexpected write to {self}")
        raise AssertionError("write_text/write_bytes must not be called by build_manifest")

    monkeypatch.setattr(Path, "write_text", _forbidden_write)
    monkeypatch.setattr(Path, "write_bytes", _forbidden_write)
    build_manifest(str(LEDGER_DIR))


def test_baseline_manifest_does_not_coerce_missing_test_path():
    manifest = build_manifest(str(LEDGER_DIR))
    live_missing = 0
    for path in sorted(LEDGER_DIR.glob("*.yaml")):
        for entry in yaml.safe_load(path.read_text()) or []:
            if entry.get("status") in ("verified", "divergent") and not entry.get("test_path"):
                live_missing += 1
    assert manifest["missing_evidence_health"]["missing_test_path_count"] == live_missing
    assert live_missing == 1347


# ---------------------------------------------------------------------------
# Legacy-tool fixture captures (Step 3)
# ---------------------------------------------------------------------------


def test_faction_fixture_matches_live_legacy_scan_output():
    fixture_dir = FIXTURES_DIR / "faction_case"
    hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(fixture_dir))
    assert hits == []


def test_unmapped_path_fixture_matches_live_legacy_scan_output():
    fixture_dir = FIXTURES_DIR / "unmapped_case"
    result = expected_subsystems_for_files(["src/never/cited.py"], ledger_dir=str(fixture_dir))
    assert result == {"src/never/cited.py": None}


def test_multi_shard_fixture_matches_live_legacy_scan_output():
    fixture_dir = FIXTURES_DIR / "multi_shard_case"
    result = expected_subsystems_for_files(["src/engine/apply.py"], ledger_dir=str(fixture_dir))
    assert result == {"src/engine/apply.py": ["combat_movement.yaml", "strategic_cognition.yaml"]}


def test_malformed_yaml_fixture_matches_live_legacy_scan_output():
    fixture_dir = FIXTURES_DIR / "malformed_yaml_case"
    mapping = derive_mapping(str(fixture_dir))
    assert mapping["src/town/harvest.py"] == {"town_resource.yaml"}
    assert "src/engine" not in str(mapping.keys())


def test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture():
    manifest = build_manifest(str(LEDGER_DIR))
    filenames = {shard["filename"] for shard in manifest["shards"]}
    assert "faction.yaml" in filenames

    fixture_dir = FIXTURES_DIR / "faction_case"
    hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(fixture_dir))
    assert hits == []
    assert "faction.yaml" not in CANONICAL_LEDGER_FILES


# ---------------------------------------------------------------------------
# V1 decision-doc completeness (Step 5)
# ---------------------------------------------------------------------------

REQUIRED_DECISION_SECTIONS = (
    "Ownership",
    "Discovery / IDs",
    "Normalized schema",
    "FTS fallback",
    "Atomic lifecycle",
    "Path-only links",
    "Output convention",
    "CLI/module ownership",
    "`parity-record` deferral",
    "Known gaps",
)


def test_v1_decision_artifact_covers_all_scope_boundaries():
    text = DECISION_DOC.read_text()
    for heading in REQUIRED_DECISION_SECTIONS:
        assert f"## {heading}" in text, f"missing required section heading: {heading!r}"


# ---------------------------------------------------------------------------
# Anti-scope-creep guards (Step 6)
# ---------------------------------------------------------------------------


def test_no_database_or_gitignore_or_make_target_created():
    staging_dir = _REPO_ROOT / "staging_artifacts" / "TCK-20260731-PARITY-INDEX-BASELINE"
    for pattern in ("*.db", "*.sqlite", "*.sqlite3"):
        assert list(staging_dir.glob(pattern)) == []

    # This checks TCK-20260731-PARITY-INDEX-BASELINE's OWN commit diff, not the live repo
    # state. A live-state assertion ("parity-index" not in the current .gitignore/Makefile)
    # would break by design the moment TCK-20260731-PARITY-INDEX-IMPORTER (Phase 1) ships,
    # since that ticket's own scope -- per v1_decisions_phase0.md's atomic-lifecycle decision
    # -- requires adding a `parity-index/` .gitignore entry. This BASELINE (Phase 0) ticket's
    # real AC #5 ("No DB, workflow/config/context integration, source rewrite, or mutation
    # command is introduced") is a claim about what THIS ticket's own commit did, so it is
    # checked against that commit's actual diff -- a fact that stays true forever, unlike a
    # present-tense read of files later tickets are expected to modify.
    baseline_commit = "1ec93c0d"
    changed_paths = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", baseline_commit],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    assert ".gitignore" not in changed_paths
    assert "Makefile" not in changed_paths


def test_v1_decision_artifact_does_not_authorize_mutation_cli():
    text = DECISION_DOC.read_text()
    assert "stays deferred" in text
    assert "parity-record validate" not in text
    assert "parity-record propose" not in text
    assert "parity-record apply" not in text
    assert "```text" not in text
    assert "```python" not in text
    assert "```bash" not in text
