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


def test_scans_canonical_nine_including_faction(tmp_path):
    _write_ledger(tmp_path, "faction.yaml", [
        {
            "id": "FAC-001", "text": "x", "status": "verified", "priority": "P0",
            "v2_evidence": "src/factions/diplomacy.py",
            "test_path": "tests/unit/test_y.py",
        },
    ])
    hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(tmp_path))
    assert hits == [("faction.yaml", "FAC-001", "src/factions/diplomacy.py")]
    assert "faction.yaml" in CANONICAL_LEDGER_FILES


def test_detects_real_fac013_p0_intersection():
    hits = find_p0_intersection(
        ["src/observability/event_extractor.py"], ledger_dir="docs/parity_ledger"
    )
    assert ("faction.yaml", "FAC-013", "src/observability/event_extractor.py") in hits


# ---------------------------------------------------------------------------
# CLI entry point (TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT)
# ---------------------------------------------------------------------------

import subprocess

_MODULE_PATH = _TOOLS_DIR / "parity_ledger_scan.py"


def test_cli_prints_readable_output_and_exits_zero_on_no_intersection(tmp_path):
    _write_ledger(tmp_path, "substrate.yaml", [
        {"id": "SUB-001", "priority": "P0", "v2_evidence": "Verified in `src/core/state.py`"},
    ])
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "src/no/such/file.py", "--ledger-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.stdout.strip(), "expected non-empty stdout -- silence is exactly the regression"
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_cli_prints_readable_output_and_exits_nonzero_on_intersection(tmp_path):
    _write_ledger(tmp_path, "substrate.yaml", [
        {"id": "SUB-001", "priority": "P0", "v2_evidence": "Verified in `src/core/state.py`"},
    ])
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "src/core/state.py", "--ledger-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.stdout.strip()
    assert result.returncode != 0
    assert "FAIL" in result.stdout
    assert "SUB-001" in result.stdout


def test_cli_help_produces_usage_text_not_silence():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--help"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_real_corpus_fac013_intersection_via_subprocess():
    # Mirrors test_detects_real_fac013_p0_intersection, but through the real CLI end-to-end.
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "src/observability/event_extractor.py"],
        capture_output=True, text=True, cwd=str(_TOOLS_DIR.parent),
    )
    assert result.returncode != 0
    assert "FAC-013" in result.stdout


def test_cli_still_importable_and_callable_as_plain_function():
    """Pins the Scope constraint: existing python3 -c call sites (find_p0_intersection(...)) must
    keep working unchanged, not routed through the new CLI."""
    assert callable(find_p0_intersection)
    hits = find_p0_intersection(["src/no/such/file.py"], ledger_dir="docs/parity_ledger")
    assert isinstance(hits, list)
