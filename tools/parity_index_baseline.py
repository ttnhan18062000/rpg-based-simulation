"""Deterministic Phase-0 baseline manifest for docs/parity_ledger/.

Built for TCK-20260731-PARITY-INDEX-BASELINE, the baseline/decision precursor to a future
SQLite parity index (docs/plans/agent_infrastructure/parity_ledger_sqlite_context/). This
script is evidence-capture only: it enumerates every current `docs/parity_ledger/*.yaml` shard
(all nine, including `faction.yaml` — a dynamic glob, deliberately independent of
`tools.parity_ledger_scan.CANONICAL_LEDGER_FILES`'s frozen 8-file compatibility list) and emits
a versioned, byte-reproducible JSON snapshot: per-shard source hashes, entry/ID counts,
status/priority tallies, the legacy eight-shard/faction exclusion gap, the schema.json
duplicate-"if"-key parsing defect (documented as observed fact, not fixed here), and a
missing-evidence health count. It builds no database and never writes into
`docs/parity_ledger/` — every shard is opened read-only.
"""

import hashlib
import json
import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_ledger_scan import CANONICAL_LEDGER_FILES  # noqa: E402

ENTRY_COUNT_HISTORICAL_REFERENCE = 1936
HISTORICAL_REFERENCE_SOURCE = (
    "docs/plans/agent_infrastructure/parity_ledger_sqlite_context/"
    "idea_parity_ledger_sqlite_context_integration.md, 'Why this is needed' section, "
    "dated 2026-07-31"
)

SCHEMA_PATH = "docs/parity_ledger/schema.json"


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scan_shard(path: Path) -> dict:
    entries = yaml.safe_load(path.read_text()) or []
    status_counts: dict = {}
    priority_counts: dict = {}
    ids = []
    for entry in entries:
        ids.append(entry.get("id"))
        status_counts[entry.get("status")] = status_counts.get(entry.get("status"), 0) + 1
        priority_counts[entry.get("priority")] = priority_counts.get(entry.get("priority"), 0) + 1
    return {
        "filename": path.name,
        "sha256": _sha256_hex(path),
        "entry_count": len(entries),
        "ids": ids,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "entries": entries,
    }


def _schema_coverage_as_parsed() -> dict:
    """Describe docs/parity_ledger/schema.json as it actually parses today.

    The source file contains two top-level "if" keys inside the same `items` object. JSON
    object keys must be unique, so any standard parser (including `json.loads`, used here)
    silently keeps only the second "if"/"then" pair and discards the first. This function
    reports the enforced-as-parsed rule set, not the human-readable source text's apparent
    intent — read-only, never modifies schema.json.
    """
    schema = json.loads(Path(SCHEMA_PATH).read_text())
    items = schema.get("items", {})
    surviving_if = items.get("if")
    surviving_then = items.get("then")
    return {
        "path": SCHEMA_PATH,
        "known_defect": (
            "source text declares two top-level \"if\" keys under `items` (verified/divergent -> "
            "v2_evidence+test_path, and divergent -> divergence_note); duplicate JSON object keys "
            "mean only the second survives standard parsing"
        ),
        "enforced_as_parsed_if": surviving_if,
        "enforced_as_parsed_then": surviving_then,
        "discarded_rule": (
            "verified/divergent entries requiring v2_evidence and test_path is NOT enforced by "
            "json.loads-based validation, despite appearing in the source text"
        ),
    }


def _missing_evidence_health(shards: list) -> dict:
    """Count, never coerce, verified/divergent entries missing test_path or v2_evidence."""
    missing_test_path = 0
    missing_v2_evidence = 0
    for shard in shards:
        for entry in shard["entries"]:
            if entry.get("status") not in ("verified", "divergent"):
                continue
            if not entry.get("test_path"):
                missing_test_path += 1
            if not entry.get("v2_evidence"):
                missing_v2_evidence += 1
    return {
        "scope": "verified and divergent entries only (schema's intended v2_evidence+test_path rule)",
        "missing_test_path_count": missing_test_path,
        "missing_v2_evidence_count": missing_v2_evidence,
    }


def build_manifest(ledger_dir: "Path | str" = "docs/parity_ledger") -> dict:
    ledger_path = Path(ledger_dir)
    shard_files = sorted(ledger_path.glob("*.yaml"))
    shards = [_scan_shard(path) for path in shard_files]

    all_ids = [entry_id for shard in shards for entry_id in shard["ids"]]
    seen: set = set()
    duplicate_ids = sorted({eid for eid in all_ids if eid in seen or seen.add(eid)})

    status_counts_total: dict = {}
    priority_counts_total: dict = {}
    for shard in shards:
        for status, count in shard["status_counts"].items():
            status_counts_total[status] = status_counts_total.get(status, 0) + count
        for priority, count in shard["priority_counts"].items():
            priority_counts_total[priority] = priority_counts_total.get(priority, 0) + count

    entry_count_current = sum(shard["entry_count"] for shard in shards)
    excluded_from_legacy_scan = sorted(
        {shard["filename"] for shard in shards} - set(CANONICAL_LEDGER_FILES)
    )

    manifest_shards = [
        {
            "filename": shard["filename"],
            "sha256": shard["sha256"],
            "entry_count": shard["entry_count"],
            "ids": shard["ids"],
            "status_counts": shard["status_counts"],
            "priority_counts": shard["priority_counts"],
        }
        for shard in shards
    ]

    return {
        "generator": "tools/parity_index_baseline.py",
        "ledger_dir": str(ledger_path),
        "shard_count": len(shards),
        "shards": manifest_shards,
        "entry_count_current": entry_count_current,
        "entry_count_historical_reference": ENTRY_COUNT_HISTORICAL_REFERENCE,
        "drift": {
            "delta": entry_count_current - ENTRY_COUNT_HISTORICAL_REFERENCE,
            "source": HISTORICAL_REFERENCE_SOURCE,
            "note": (
                "entry_count_current is the live, authoritative count; "
                "entry_count_historical_reference is a dated comparison figure from the idea doc, "
                "never overwritten or reconciled to match the live count"
            ),
        },
        "duplicate_ids": {
            "count": len(duplicate_ids),
            "ids": duplicate_ids,
            "note": "observed fact for the current corpus, not an enforced invariant at Phase 0",
        },
        "excluded_from_legacy_scan": excluded_from_legacy_scan,
        "status_counts_total": status_counts_total,
        "priority_counts_total": priority_counts_total,
        "schema_coverage": _schema_coverage_as_parsed(),
        "missing_evidence_health": _missing_evidence_health(shards),
    }


def serialize_manifest(manifest: dict) -> str:
    return json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def main() -> None:
    manifest = build_manifest()
    output_path = Path(
        "staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_manifest(manifest))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
