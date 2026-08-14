"""Tests for tools/simq_audit_gaps.py — anchor coverage + parity ledger candidate scan."""
from __future__ import annotations

import json
from pathlib import Path

import tools.simq_audit_gaps as sag
from tools.simq_audit_gaps import (
    find_uncovered_anchor_keys,
    load_anchor_keys,
    scan_parity_ledger_candidates,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_flags_uncovered_anchor_key():
    anchor_keys = ["known_seed1_100t", "orphan_seed9_999t"]
    fast_keys = ["known_seed1_100t"]
    slow_keys: list[str] = []

    uncovered = find_uncovered_anchor_keys(anchor_keys, fast_keys, slow_keys)

    assert uncovered == ["orphan_seed9_999t"]


def test_no_false_positive_for_covered_keys():
    import tests.simulation_quality.test_grade_regression as tgr

    anchor_keys = load_anchor_keys(REPO_ROOT / "tests/simulation_quality/fixtures/grade_anchors.json")
    uncovered = find_uncovered_anchor_keys(anchor_keys, tgr.FAST_ANCHOR_KEYS, tgr.SLOW_ANCHOR_KEYS)

    assert uncovered == []


def test_parity_ledger_candidate_scan_finds_known_entries():
    candidates = scan_parity_ledger_candidates(REPO_ROOT / "docs/parity_ledger")
    ids = {c["id"] for c in candidates}

    assert {"SOC-237", "SOC-238", "INFRA-251", "INFRA-258"}.issubset(ids)


def test_exit_code_always_zero(tmp_path, monkeypatch, capsys):
    fixture = {
        "_note": "test fixture",
        "known_seed1_100t": {"AGENCY": "A"},
        "orphan_seed9_999t": {"AGENCY": "B"},
    }
    fixture_path = tmp_path / "grade_anchors.json"
    fixture_path.write_text(json.dumps(fixture))

    monkeypatch.setattr(sag, "load_anchor_keys", lambda path=fixture_path: load_anchor_keys(fixture_path))

    exit_code = sag.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "orphan_seed9_999t" in output
