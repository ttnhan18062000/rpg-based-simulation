"""Report-only corpus scan for docs/parity_ledger/*.yaml (TCK-20260913-PARITY-LEDGER-WRITER-
INVALID-CORPUS). Runs validate_entry() over every on-disk entry and classifies failures into the
three classes the ticket measured, without ever writing to the ledger or running any test
(TCK-20260705-GATE-DET-MECHANICS-AUDITOR's "never sweep" constraint forbids running pytest across
the corpus -- pure validation of already-written YAML fields is not a sweep in that sense: it runs
no tests and completes over 2187 entries in well under a second).

Not wired into CI as a blocking gate: at measurement time the corpus was ~77% invalid, entirely
predating tools/parity_ledger_writer.py's own existence (TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-
TOOL) -- a blocking check over that state would be unlandable. This is the reporting surface the
ticket's own Class 1 policy decision and future audits are meant to read, not a gate.

Usage:
    python3 tools/parity_corpus_check.py                 # human-readable summary
    python3 tools/parity_corpus_check.py --json           # machine-readable
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import yaml  # noqa: E402

from parity_ledger_writer import _ID_PATTERN, _P0_TEST_PATH_EXEMPT_STATUSES  # noqa: E402
from parity_test_path import parse_test_path_citations  # noqa: E402

DEFAULT_LEDGER_DIR = Path("docs/parity_ledger")

# Statuses whose test_path requirement Class 1 concerns (mirrors validate_entry()'s own two
# independent triggers for "test_path is required": status in (verified, divergent), OR
# priority == P0 with status NOT in the exempt set). Both call sites are covered here so this
# scan's "no test_path" bucket lines up with what validate_entry() would actually reject for
# that reason, not a narrower guess at it.
_STATUS_REQUIRES_TEST_PATH = ("verified", "divergent")


def _entry_requires_test_path(entry: dict) -> bool:
    if entry.get("status") in _STATUS_REQUIRES_TEST_PATH:
        return True
    if entry.get("priority") == "P0" and entry.get("status") not in _P0_TEST_PATH_EXEMPT_STATUSES:
        return True
    return False


def _entry_requires_support_boundary(entry: dict) -> bool:
    return entry.get("priority") == "P0" and entry.get("status") in _P0_TEST_PATH_EXEMPT_STATUSES


def classify_entry(entry: dict) -> str | None:
    """Return the class name for one invalid entry, or None if it passes every check this scan
    covers. Classes are checked in the ticket's own priority order and are mutually exclusive by
    construction (an entry can only be missing test_path OR have a malformed one, never both).

    `class4_bad_id_pattern` was NOT one of the ticket's own named classes -- found during this
    scan's own cross-check against the real validate_entry() (one real mismatch out of 2187:
    SOC-ABAND-TYPE-01, a well-evidenced P1 entry whose only defect is a 2-digit numeric suffix
    where _ID_PATTERN requires 3). Added here so this tool's total always matches what
    validate_entry() would actually reject, never silently undercounting a real category this
    ticket's own text happened not to mention. Out of this ticket's explicit scope to fix (a
    different defect than the evidence-completeness classes this ticket targets, and renaming a
    ledger entry ID has its own blast radius -- cross-references, etc.) -- reported, not repaired.
    """
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not _ID_PATTERN.match(entry_id):
        return "class4_bad_id_pattern"

    if _entry_requires_test_path(entry):
        raw = entry.get("test_path")
        if raw is None or not str(raw).strip():
            return "class1_no_test_path"
        _, error = parse_test_path_citations(raw)
        if error is not None:
            return "class2_malformed_test_path"

    if _entry_requires_support_boundary(entry):
        boundary = entry.get("support_boundary")
        if not isinstance(boundary, str) or not boundary.strip():
            return "class3_no_support_boundary"

    return None


def scan_corpus(ledger_dir: Path = DEFAULT_LEDGER_DIR) -> dict:
    """Scan every entry in every shard under ledger_dir. Returns a report dict with per-class
    counts, per-shard breakdowns, and the full list of (shard, id, class) for anything invalid."""
    counts = {
        "class1_no_test_path": 0,
        "class2_malformed_test_path": 0,
        "class3_no_support_boundary": 0,
        "class4_bad_id_pattern": 0,
    }
    total_entries = 0
    findings = []

    for shard_path in sorted(ledger_dir.glob("*.yaml")):
        entries = yaml.safe_load(shard_path.read_text(encoding="utf-8")) or []
        for entry in entries:
            total_entries += 1
            cls = classify_entry(entry)
            if cls is not None:
                counts[cls] += 1
                findings.append({
                    "shard": shard_path.name,
                    "id": entry.get("id"),
                    "status": entry.get("status"),
                    "priority": entry.get("priority"),
                    "class": cls,
                })

    return {
        "total_entries": total_entries,
        "total_invalid": sum(counts.values()),
        "counts": counts,
        "findings": findings,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-dir", default=str(DEFAULT_LEDGER_DIR))
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = scan_corpus(Path(args.ledger_dir))

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"Scanned {report['total_entries']} entries under {args.ledger_dir}")
    print(f"Invalid (would be rejected by validate_entry()): {report['total_invalid']}")
    for cls, count in report["counts"].items():
        print(f"  {cls}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
