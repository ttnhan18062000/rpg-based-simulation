#!/usr/bin/env python3
"""SimQ audit gap scanner.

Read-only, informational cross-check used by `make simq-full-audit` and the
`.claude/workflows/simq-audit.js` Recalibrate phase. Never writes to any file.

Two checks:
1. Anchor coverage — every key in tests/simulation_quality/fixtures/grade_anchors.json
   must appear in FAST_ANCHOR_KEYS or SLOW_ANCHOR_KEYS (test_grade_regression.py),
   otherwise the regression test never actually checks it.
2. Parity ledger candidates — entries under docs/parity_ledger/*.yaml whose text,
   divergence_note, or v2_evidence reference SimQ/calibration/QualityHub/a pillar name,
   surfaced as a ready-made candidate list for the workflow's Parity Check phase.

Exit code is always 0 — this is a gap-finder, not a pass/fail gate.

Usage:
    python3 tools/simq_audit_gaps.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DEFAULT_ANCHORS_PATH = Path("tests/simulation_quality/fixtures/grade_anchors.json")
DEFAULT_LEDGER_DIR = Path("docs/parity_ledger")

_META_KEYS = {"_note", "_instructions", "_grade_order"}

_PILLAR_NAMES = [
    "AGENCY",
    "COMBAT",
    "COGNITION",
    "ECONOMY",
    "FACTION",
    "INFORMATION",
    "NARRATIVE",
    "SOCIAL",
    "WORLD",
]

_CANDIDATE_TERMS = ["simq", "calibrat", "qualityhub"] + [p.lower() for p in _PILLAR_NAMES]


def load_anchor_keys(path: Path = DEFAULT_ANCHORS_PATH) -> list[str]:
    data = json.loads(path.read_text())
    return [k for k in data if k not in _META_KEYS]


def find_uncovered_anchor_keys(
    anchor_keys: list[str], fast_keys: list[str], slow_keys: list[str]
) -> list[str]:
    covered = set(fast_keys) | set(slow_keys)
    return [k for k in anchor_keys if k not in covered]


def _entry_matches(entry: dict) -> bool:
    haystack = " ".join(
        str(entry.get(field, "") or "")
        for field in ("text", "divergence_note", "v2_evidence")
    ).lower()
    return any(term in haystack for term in _CANDIDATE_TERMS)


def scan_parity_ledger_candidates(ledger_dir: Path = DEFAULT_LEDGER_DIR) -> list[dict]:
    candidates: list[dict] = []
    for yaml_path in sorted(ledger_dir.glob("*.yaml")):
        entries = yaml.safe_load(yaml_path.read_text()) or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if not _entry_matches(entry):
                continue
            note = entry.get("divergence_note") or entry.get("v2_evidence") or entry.get("text") or ""
            candidates.append(
                {
                    "id": entry.get("id"),
                    "file": yaml_path.name,
                    "status": entry.get("status"),
                    "divergence_note_excerpt": str(note)[:160],
                }
            )
    return candidates


def _load_fast_slow_keys() -> tuple[list[str], list[str]]:
    import tests.simulation_quality.test_grade_regression as tgr

    return list(tgr.FAST_ANCHOR_KEYS), list(tgr.SLOW_ANCHOR_KEYS)


def main() -> int:
    anchor_keys = load_anchor_keys()
    fast_keys, slow_keys = _load_fast_slow_keys()
    uncovered = find_uncovered_anchor_keys(anchor_keys, fast_keys, slow_keys)

    print("=== UNCOVERED ANCHOR KEYS ===")
    if uncovered:
        for key in uncovered:
            print(f"  UNCOVERED: {key} — regression test will never check this key")
    else:
        print(f"  None — all {len(anchor_keys)} anchor keys covered.")
    print()

    candidates = scan_parity_ledger_candidates()
    print("=== PARITY LEDGER CANDIDATES ===")
    if not candidates:
        print("  None found.")
    else:
        by_file: dict[str, list[dict]] = {}
        for c in candidates:
            by_file.setdefault(c["file"], []).append(c)
        for file_name in sorted(by_file):
            print(f"  {file_name}:")
            for c in by_file[file_name]:
                print(f"    {c['id']} [{c['status']}] — {c['divergence_note_excerpt']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
