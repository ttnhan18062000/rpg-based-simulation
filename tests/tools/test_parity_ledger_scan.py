"""Tests for tools/parity_ledger_scan.py."""

import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_ledger_scan import (  # noqa: E402
    find_p0_intersection,
    CANONICAL_LEDGER_FILES,
    ShardParseError,
)


def _write_ledger(tmp_path, filename, entries):
    (tmp_path / filename).write_text(yaml.safe_dump(entries))


def test_detects_p0_intersection_via_synthetic_fixture(tmp_path):
    # Positive control: none of the real ledger's current P0 entries can exercise this branch
    # (investigation.md's empirical finding), so this uses a synthetic fixture.
    _write_ledger(tmp_path, "substrate.yaml", [
        {
            "id": "SUB-001", "text": "x", "status": "verified", "priority": "P0",
            "v2_evidence": "Verified in `src/core/state.py` (IdentityComponent)",
            "test_path": "tests/unit/test_x.py",
        },
    ])
    hits = find_p0_intersection(["src/core/state.py"], ledger_dir=str(tmp_path))
    assert hits == [("substrate.yaml", "SUB-001", "src/core/state.py")]


def test_no_intersection_for_representative_docs_only_change():
    # Negative control against the real 8-file ledger.
    hits = find_p0_intersection(["docs/ai/workflows.md"], ledger_dir="docs/parity_ledger")
    assert hits == []


def test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash(tmp_path):
    (tmp_path / "substrate.yaml").write_text("id: [unbalanced flow mapping\n")
    try:
        find_p0_intersection(["src/core/state.py"], ledger_dir=str(tmp_path))
        assert False, "expected ShardParseError"
    except ShardParseError as exc:
        assert exc.filename == "substrate.yaml"


def test_only_scans_canonical_eight_not_faction(tmp_path):
    _write_ledger(tmp_path, "faction.yaml", [
        {
            "id": "FAC-001", "text": "x", "status": "verified", "priority": "P0",
            "v2_evidence": "src/factions/diplomacy.py",
            "test_path": "tests/unit/test_y.py",
        },
    ])
    hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(tmp_path))
    assert hits == []
    assert "faction.yaml" not in CANONICAL_LEDGER_FILES
