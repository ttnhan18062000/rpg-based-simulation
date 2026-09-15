"""Aggregate coherence validator for `agent-monitoring/data/*` (TCK-20260915-MONITORING-ANOMALY-VALIDATOR,
child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC, scoped LAST per the epic's own instruction
so it encodes tickets 1-7's confirmed causes, not this ticket's own original hypotheses).

**What `agent-monitoring-validate` (tools/agent-monitoring/validate.py) already answers**: is the
record *present* -- every DONE working_log entry has a run record, every run record has an event
record. This module answers a different question: is a *present* record *coherent* -- internally
consistent with the rest of the corpus, not contradicting itself.

**Six candidate coherence checks were named in this ticket's own text; two of the six turned out,
on investigation, not to be real anomalies at all**:

- "Vocabulary conformance: non-canonical agents (`orchestrator` 144, `concern-investigator` 6,
  `context-packet-wrapper` 1)" -- re-measured at ticket-close time (and independently
  cross-checked by the peer session that originally scoped this candidate check, who found the
  same result from a different angle): `orchestrator` was actually 401-501 occurrences spanning
  2026-06 through 2026-09 and still growing, `context-packet-wrapper` was 59 (not 1, and a
  constant-defined mechanism -- `tools/retrieval_events.py:305`), and every one of the ticket's
  own three named literals is real, long-established, or grep-confirmed -- a
  `tools/agent-monitoring/vocabulary.py` registry GAP, not corpus drift. Investigation surfaced 3
  more of the same shape (the workflow's own name used as a self-referential "the orchestrator did
  it" label for `implement-ticket`/`implement-epic`, and `write-sequence`, a real
  `create-tickets.js` Write-phase label). All 6 registered there instead of ratcheted here (see
  that file's own updated comments -- each documents what it is and how it was confirmed,
  matching the file's existing standard). The genuine residual after registering them -- 162
  agent-literal occurrences and 2 tier-literal occurrences, a long tail of many small historical
  one-offs (confirmed dead, not an active writer: the largest sub-clusters --
  model-name-as-agent-identity and alternate role-naming -- stop entirely in 2026-07, nothing
  since) plus 2 real `epic_batch`/`epic-batch` typo-variants of the canonical `"epic"` tier -- IS
  ratcheted below.

  **Separate, explicitly-noted-not-ratcheted finding**: 258 events carry no `agent` field at all
  (not a literal value, so outside this drift computation's own shape). All historical (185 in
  2026-06, 19 in 2026-07), 54 with no parseable `ts` either (already counted in
  `monitoring_integrity_backlog_check.py`'s own item-4 unusable-ts ratchet), and 177 also lacking
  a `phase`, with lowercase phase values among the rest (`implement`/`test`/`finalize`) marking
  them as pre-schema records. Recorded here rather than silently dropped; not given its own ratchet
  condition since it is a different check shape (field absence, not a wrong literal) and is
  already covered in spirit by the ts/unknown-week ratchets above.
- "Working_log rows not matching the 6-column schema" -- fully FIXED by
  `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` (the writer was already safe going forward; the 9
  known-historical malformed rows were repaired in place) and structurally protected by
  `tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer`. A
  genuinely-achieved, structurally-guarded zero does not need its own ratchet entry here -- the
  sole-writer test already guards the only realistic regression path (a second ad-hoc writer
  appearing). Not included below.

**The remaining four checks are each already built as their own standalone ratchet module by a
sibling ticket** (duplicate run records: ticket 1; seq integrity: ticket 4; tool_call_count
mismatch: ticket 3; unusable `ts` + `unknown-week`: ticket 7's items 4/5). This module's own job is
narrow: aggregate all of them (plus the new vocabulary-drift check) into ONE wired, reportable
surface -- the "validator that fails on incoherent records the way `agent-monitoring-validate`
fails on missing ones" this ticket's own Title asks for -- rather than five/six separately-run
`make` targets nobody remembers to check together.

Mirrors the batch's own `check_*()` shape: `List[dict]` (`{"status": "PASS"|"FAIL", "evidence":
"..."}`), `MARKER:` + `json.dumps(result)` stdout contract in `__main__`. Reproducible from the raw
JSONL shards directly (via `generate_retro._load_runs_and_events()`/`_load_source()`), never from
`agent-monitoring-index/monitoring.db`, which goes stale (see `generate_retro.py`'s own warning) --
per this ticket's own Implementation Notes.
"""
import json
import sys
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_runs_and_events, _load_source, DEFAULT_TOOLS_FILE  # noqa: E402
from validate import compute_vocabulary_drift_counts  # noqa: E402

from duplicate_run_record_check import check_duplicate_run_records  # noqa: E402
from event_seq_integrity_check import check_event_seq_integrity  # noqa: E402
from tool_call_count_mismatch_check import check_tool_call_count_mismatches  # noqa: E402
from monitoring_integrity_backlog_check import (  # noqa: E402
    UNKNOWN_WEEK_ROW_CEILING,
    UNUSABLE_TS_EVENT_CEILING,
    UNUSABLE_TS_RUN_CEILING,
    count_unknown_week_rows,
    find_unusable_ts_records,
)

# Ratchet ceilings: the real corpus's own measured counts as of 2026-09-15, AFTER registering
# orchestrator/context-packet-wrapper/concern-investigator/implement-ticket/implement-epic/
# write-sequence as canonical agent literals in vocabulary.py (see this module's own docstring).
# May only decrease.
AGENT_DRIFT_CEILING = 162
TIER_DRIFT_CEILING = 2


def check_vocabulary_drift(runs: List[dict] = None, events: List[dict] = None) -> List[dict]:
    """Two-condition ratchet over compute_vocabulary_drift_counts()'s agent_drift/tier_drift
    Counters -- the genuine residual after this ticket's own vocabulary.py registry fix."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events

    counts = compute_vocabulary_drift_counts(runs, events)
    agent_total = sum(counts["agent_drift"].values())
    tier_total = sum(counts["tier_drift"].values())

    results = []
    if agent_total > AGENT_DRIFT_CEILING:
        results.append({
            "status": "FAIL",
            "evidence": (
                f"non-canonical agent literals: {agent_total} exceeds the ratchet ceiling "
                f"({AGENT_DRIFT_CEILING}) by {agent_total - AGENT_DRIFT_CEILING}. "
                f"Top offenders: {counts['agent_drift'].most_common(5)}"
            ),
        })
    else:
        results.append({
            "status": "PASS",
            "evidence": f"non-canonical agent literals: {agent_total} (ceiling {AGENT_DRIFT_CEILING})",
        })

    if tier_total > TIER_DRIFT_CEILING:
        results.append({
            "status": "FAIL",
            "evidence": (
                f"non-canonical tier literals: {tier_total} exceeds the ratchet ceiling "
                f"({TIER_DRIFT_CEILING}) by {tier_total - TIER_DRIFT_CEILING}. "
                f"Values: {dict(counts['tier_drift'])}"
            ),
        })
    else:
        results.append({
            "status": "PASS",
            "evidence": f"non-canonical tier literals: {tier_total} (ceiling {TIER_DRIFT_CEILING})",
        })

    return results


def check_ts_shape_and_unknown_week(
    runs: List[dict] = None,
    events: List[dict] = None,
    data_dir=None,
) -> List[dict]:
    """Thin wrapper reusing monitoring_integrity_backlog_check.py's own items 4/5 functions --
    presence (item 2, whether a run record exists at all) is validate.py's job, not this
    coherence-focused module's; only the shape/coherence conditions (unusable ts, unknown-week)
    belong here."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events

    bad_runs, bad_events = find_unusable_ts_records(runs, events)
    if data_dir is not None:
        unknown_week_count = count_unknown_week_rows(data_dir)
    else:
        unknown_week_count = count_unknown_week_rows()

    results = []
    for label, count, ceiling in (
        ("runs.jsonl records with unusable ts", len(bad_runs), UNUSABLE_TS_RUN_CEILING),
        ("events.jsonl records with unusable ts", len(bad_events), UNUSABLE_TS_EVENT_CEILING),
        ("unknown-week/ shard row count", unknown_week_count, UNKNOWN_WEEK_ROW_CEILING),
    ):
        if count > ceiling:
            results.append({
                "status": "FAIL",
                "evidence": f"{label}: {count} exceeds the ratchet ceiling ({ceiling}) by {count - ceiling}.",
            })
        else:
            results.append({"status": "PASS", "evidence": f"{label}: {count} (ceiling {ceiling})"})
    return results


def check_monitoring_anomalies(
    runs: List[dict] = None,
    events: List[dict] = None,
    tools: List[dict] = None,
    data_dir=None,
) -> List[dict]:
    """Aggregate: runs every coherence check and returns every individual result, tagged by
    which check produced it. A caller cares about the union -- FAIL if ANY sub-check FAILs."""
    if runs is None or events is None:
        loaded_runs, loaded_events = _load_runs_and_events()
        runs = runs if runs is not None else loaded_runs
        events = events if events is not None else loaded_events
    if tools is None:
        tools = _load_source(DEFAULT_TOOLS_FILE, "tools")

    all_results = []
    for check_name, results in (
        ("duplicate_run_records", check_duplicate_run_records(runs)),
        ("event_seq_integrity", check_event_seq_integrity(events)),
        ("tool_call_count_mismatch", check_tool_call_count_mismatches(runs, events, tools)),
        ("ts_shape_and_unknown_week", check_ts_shape_and_unknown_week(runs, events, data_dir)),
        ("vocabulary_drift", check_vocabulary_drift(runs, events)),
    ):
        for r in results:
            all_results.append({"check": check_name, **r})
    return all_results


if __name__ == "__main__":
    result = check_monitoring_anomalies()
    print("MARKER:" + json.dumps(result))
    fail_count = sum(1 for r in result if r["status"] == "FAIL")
    if fail_count:
        sys.exit(1)
