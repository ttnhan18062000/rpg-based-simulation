#!/usr/bin/env python3
"""Committed measurement runner for TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT.

Formalizes the Investigate-phase preliminary script
(`staging_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/investigate_measurement_
script.py`) into a committed, reproducible artifact, mirroring Phase 0-4's own
`tools/agent-monitoring/kgmcp_phase{N}_*_runner.py` + `tests/tools/fixtures/kgmcp_phase{N}_*_
results.json` + `tests/tools/test_kgmcp_phase{N}_*.py` pattern.

Data sources: two frozen, point-in-time snapshot fixtures --
`tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` (521 records, one per distinct
ticket run_id with a real Investigate-phase summary in `agent-monitoring/events.jsonl` as of this
ticket's own Implement step, explicitly excluding this ticket's own run_id --
`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` -- to avoid the self-contamination hazard where
this ticket's own mandatory monitoring write would land in the exact dataset it measures) and
`tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` (1,411 records, one per
`tickets/working_log.csv` row with a non-empty `title` or `summary`). Neither
`agent-monitoring/events.jsonl` nor `tickets/working_log.csv` (both live, append-only, ever-growing
files) is read by this module -- only the frozen snapshots, so a re-run always reproduces the same
numbers regardless of how much either live file has grown since.

Method (mirrors proposal Sec.11.2's conservative multi-signal approach -- normalize -> extract stable
identifiers -> classify intent -> compare identity+intent agreement; explicitly NOT raw-string-only,
NOT embedding-only):

1. Normalize: collapse whitespace (already applied to the events snapshot's `summary` field at
   freeze time; applied here for the working-log snapshot's `title`+`summary` text).
2. Extract stable identifiers per record, four kinds:
   - subsystem-topic tags via `tools/registry_query.py::candidate_tags_from_text()` (imported
     unmodified, never reimplemented).
   - CamelCase symbol-shaped tokens (e.g. AuthoritativeState, ContextPacket) via regex requiring an
     actual lowercase letter (not just a digit) between two capitals and a minimum 6-character
     length -- this tightening is load-bearing: a first pass without it matched bare ALL-CAPS
     acronyms (INFRA, STRAT, TOWN, TCK) and digit-joined pseudo-CamelCase tokens (E2E) as if they
     were specific code symbols, inflating the secondary-source pair count from 748 to a corrected
     372 once fixed.
   - repo-relative file paths (src/..., docs/..., tools/..., tests/...) via regex.
   - referenced ticket IDs (TCK-YYYYMMDD-...) and parity-ledger entry IDs (INFRA-206, STRAT-227,
     etc.) via regex.
3. Classify intent into one of 6 buckets via keyword rules (mechanism_explanation,
   root_cause_debugging, completeness_verification, feasibility_evaluation, location_lookup, other).
4. Compare: two DIFFERENT records count as a conservative repeated-demand pair only if (a) same
   intent bucket (and not "other", too weak to count) AND (b) at least one overlapping specific
   extracted identifier (CamelCase symbol, file path, ticket ID, or parity-entry ID) -- NOT
   subsystem-topic tag alone, since tags like "mcp"/"cognition" are shared by dozens of otherwise-
   unrelated tickets and would produce an unusably noisy result if used as the sole matching signal.
   Tag-only overlap is reported separately as a weaker, explicitly not-counted signal.

Run once, by hand, during Implementation -- never wired into the fast pytest loop, mirroring
`kgmcp_phase4_direct_tool_comparison_runner.py`'s own one-time-script convention (INFRA-344's own
v2_evidence precedent: "written the committed fixture, run once by hand," not wired into any
recurring CI/test-time execution path).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent

if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from registry_query import candidate_tags_from_text  # noqa: E402

_EVENTS_SNAPSHOT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase5_events_investigate_snapshot.json"
)
_WORKING_LOG_SNAPSHOT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase5_working_log_snapshot.json"
)
_RESULTS_OUTPUT_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase5_repeated_demand_measurement_results.json"
)

# Requires an actual lowercase LETTER (not just a digit) between two uppercase letters, so bare
# ALL-CAPS acronyms (INFRA, STRAT, TOWN, TCK) and digit-joined pseudo-camel tokens (E2E, S3) never
# match here -- those are handled separately by PARITY_ID_RE / TICKET_RE, or excluded entirely,
# since a bare acronym/digit-joined token is a coarse category signal, not a specific entity.
# Minimum total length 6 further suppresses short incidental matches.
CAMEL_RE = re.compile(r"\b[A-Z][a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b")
_CAMEL_MIN_LEN = 6
PATH_RE = re.compile(r"\b(?:src|docs|tools|tests)/[\w./-]+\.(?:py|md|yaml|json|csv)\b")
TICKET_RE = re.compile(r"\bTCK-\d{8}-[A-Z0-9-]+\b")
# A specific parity-ledger entry ID (e.g. INFRA-206, STRAT-227, TOWN-173) is a strong, specific
# identifier -- much stronger than its bare category prefix alone.
PARITY_ID_RE = re.compile(r"\b(?:[A-Z]{2,}-)?[A-Z]{3,}-\d{2,4}\b")

INTENT_KEYWORDS = {
    "mechanism_explanation": [
        "how does", "how the", "traced", "trace ", "flow is", "pipeline", "confirmed", "call chain",
        "calls into", "invoked", "understand", "how it works", "mechanism", "works by",
    ],
    "root_cause_debugging": [
        "bug", "fail", "failing", "failed", "error", "root cause", "broken", "regression",
        "incorrect", "wrong", "mismatch", "crash", "exception", "why is", "why was", "unexpected",
    ],
    "completeness_verification": [
        "implemented", "not yet implemented", "gap", "missing", "verify", "parity", "complete",
        "coverage", "already exists", "already satisfied", "unimplemented", "status of",
    ],
    "feasibility_evaluation": [
        "evaluate", "recommend", "should we", "worth", "compare", "measure", "economics",
        "justify", "warranted", "advantage", "feasibility", "net-positive", "net positive",
    ],
    "location_lookup": [
        "found in", "located", "file is", "defined in", "lives in", "site", "sites found",
        "is in ", "found at",
    ],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def classify_intent(text: str) -> str:
    lower = text.lower()
    scores = {}
    for bucket, kws in INTENT_KEYWORDS.items():
        scores[bucket] = sum(1 for kw in kws if kw in lower)
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return "other"
    return best[0]


def extract_identifiers(text: str) -> dict:
    ticket_ids = set(TICKET_RE.findall(text))
    # Exclude any parity-id lookalike match that is actually a TCK-... ticket id.
    parity_ids = {m for m in PARITY_ID_RE.findall(text) if not m.startswith("TCK-")}
    return {
        "camel": {m for m in CAMEL_RE.findall(text) if len(m) >= _CAMEL_MIN_LEN},
        "path": set(PATH_RE.findall(text)),
        "ticket": ticket_ids,
        "parity": parity_ids,
    }


def load_investigate_events() -> list[dict]:
    """Reads the frozen Step 1 snapshot only -- never `agent-monitoring/events.jsonl` live."""
    return json.loads(_EVENTS_SNAPSHOT_PATH.read_text())


def load_working_log_rows() -> list[dict]:
    """Reads the frozen Step 1 snapshot only -- never `tickets/working_log.csv` live."""
    return json.loads(_WORKING_LOG_SNAPSHOT_PATH.read_text())


def _build_records(items: list[dict], id_key: str, text_fn) -> list[dict]:
    records = []
    for item in items:
        text = normalize(text_fn(item))
        ids = extract_identifiers(text)
        tags = candidate_tags_from_text(text, root=_REPO_ROOT)
        intent = classify_intent(text)
        records.append(
            {
                "id": item[id_key],
                "text": text,
                "ids": ids,
                "tags": tags,
                "intent": intent,
            }
        )
    return records


def _compare_records(records: list[dict]) -> tuple[list[dict], int]:
    """Pairwise conservative comparison: same intent + overlapping specific identifier, different
    records. Returns (repeated_pairs, tag_only_pair_count)."""
    repeated_pairs = []
    tag_only_pairs = 0
    n = len(records)
    for i in range(n):
        ri = records[i]
        for j in range(i + 1, n):
            rj = records[j]
            if ri["intent"] != rj["intent"]:
                continue
            if ri["intent"] == "other":
                continue  # too weak a bucket to count as a real intent match
            shared_camel = ri["ids"]["camel"] & rj["ids"]["camel"]
            shared_path = ri["ids"]["path"] & rj["ids"]["path"]
            shared_ticket = ri["ids"]["ticket"] & rj["ids"]["ticket"]
            shared_parity = ri["ids"]["parity"] & rj["ids"]["parity"]
            shared_specific = shared_camel | shared_path | shared_ticket | shared_parity
            shared_tags = ri["tags"] & rj["tags"]
            if shared_specific:
                repeated_pairs.append(
                    {
                        "a": ri["id"],
                        "b": rj["id"],
                        "intent": ri["intent"],
                        "shared_identifiers": sorted(shared_specific),
                        "shared_camel_or_path": sorted(shared_camel | shared_path),
                        "shared_ticket_or_parity_id": sorted(shared_ticket | shared_parity),
                        "a_text": ri["text"],
                        "b_text": rj["text"],
                    }
                )
            elif shared_tags:
                tag_only_pairs += 1
    return repeated_pairs, tag_only_pairs


def _measure(records: list[dict]) -> dict:
    intent_counts = Counter(r["intent"] for r in records)
    repeated_pairs, tag_only_pairs = _compare_records(records)

    strong_pairs = [p for p in repeated_pairs if p["shared_camel_or_path"]]
    ref_only_pairs = [
        p for p in repeated_pairs if not p["shared_camel_or_path"] and p["shared_ticket_or_parity_id"]
    ]

    tickets_involved = set()
    for p in repeated_pairs:
        tickets_involved.add(p["a"])
        tickets_involved.add(p["b"])

    return {
        "total_tickets": len(records),
        "intent_distribution": dict(intent_counts),
        "conservative_repeated_pair_count": len(repeated_pairs),
        "strong_pair_count": len(strong_pairs),
        "ref_only_pair_count": len(ref_only_pairs),
        "tag_only_pair_count": tag_only_pairs,
        "distinct_tickets_in_repeated_pairs": len(tickets_involved),
        "pairs": repeated_pairs,
    }


def measure_primary() -> dict:
    events = load_investigate_events()
    records = _build_records(events, "run_id", lambda e: e["summary"])
    return _measure(records)


def measure_secondary() -> dict:
    rows = load_working_log_rows()
    records = _build_records(rows, "ticket_id", lambda r: f"{r['title']}; {r['summary']}")
    return _measure(records)


def run() -> dict:
    primary = measure_primary()
    secondary = measure_secondary()

    primary_out = dict(primary)
    # Full pair list for primary (small, 17 entries).
    secondary_out = dict(secondary)
    # pairs_sample (first 20) for secondary, mirroring the preserved investigate output's own
    # pairs_sample field name -- 372 full pairs would bloat the committed fixture unnecessarily.
    secondary_out["pairs_sample"] = secondary_out.pop("pairs")[:20]

    return {"primary": primary_out, "secondary": secondary_out}


def main() -> None:
    report = run()
    print(f"Primary (events.jsonl): total_tickets={report['primary']['total_tickets']}, "
          f"conservative_repeated_pair_count={report['primary']['conservative_repeated_pair_count']}, "
          f"distinct_tickets_in_repeated_pairs={report['primary']['distinct_tickets_in_repeated_pairs']}")
    print(f"Secondary (working_log.csv): total_tickets={report['secondary']['total_tickets']}, "
          f"conservative_repeated_pair_count={report['secondary']['conservative_repeated_pair_count']}, "
          f"distinct_tickets_in_repeated_pairs={report['secondary']['distinct_tickets_in_repeated_pairs']}")
    _RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True, default=list) + "\n")
    print(f"Wrote {_RESULTS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
