"""Read-only provenance classifier for agent-monitoring/*.jsonl records
(TCK-20260721-BASELINE-MONITORING-MANIFEST).

Classifies a single already-parsed record against the documented legacy
schema generations in docs/agent-monitoring/schema.md's "Known Limitations"
section, without mutating anything. Pure function, no I/O — the manifest
tool (manifest.py) and its tests are the only intended callers.
"""
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).resolve().parent
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from validate import LEGACY_COMPLETION_FIELDS, LEGACY_TERMINAL_STATUS_VALUES  # noqa: E402,F401

# The individual field names the runs-shape rules below key on must stay a subset
# of validate.py's own LEGACY_COMPLETION_FIELDS — this assertion is what keeps the
# classifier's notion of "legacy completion field" single-sourced with the existing
# validator, since the rules themselves are written against literal field names
# (matching schema.md's per-shape descriptions) rather than iterating the tuple.
# LEGACY_TERMINAL_STATUS_VALUES is imported alongside it for the same single-source
# reason even though shape classification here is purely structural (which keys are
# present, not value-based) and so has no direct use for it.
_RUN_SHAPE_COMPLETION_FIELDS = {"finished_at", "end_ts", "completed_at", "ts_end"}
assert _RUN_SHAPE_COMPLETION_FIELDS <= set(LEGACY_COMPLETION_FIELDS), (
    "legacy_reader's runs-shape rules reference a completion field not in "
    "validate.py's LEGACY_COMPLETION_FIELDS"
)


def classify_provenance(record: dict, source: str) -> frozenset[str]:
    """source is one of 'runs', 'events', 'tools'. Returns a set of legacy-shape
    labels; an empty frozenset means the record matches the current schema for
    its source."""
    if source == "runs":
        return _classify_runs(record)
    if source == "tools":
        return _classify_tools(record)
    if source == "events":
        return _classify_events(record)
    raise ValueError(f"unknown source: {source!r}")


def _classify_runs(record: dict) -> frozenset[str]:
    # TCK-20260623-TYPE-CHECKER: the one permanently-documented residual exception
    # (schema.md "Final residual after the fix: exactly 1") — checked first since
    # its signature (outcome present, final_status/status both absent) is the most
    # narrowly identifiable and must never fall through to another shape's rule.
    if "outcome" in record and "final_status" not in record and "status" not in record:
        return frozenset({"shape6_type_checker_exception"})

    run_id = str(record.get("run_id", ""))
    if (
        run_id.startswith(("FOLDER-", "EPIC-"))
        and "final_status" not in record
        and "start_ts" not in record
        and "end_ts" not in record
    ):
        return frozenset({"shape5_folder_epic_bare_status"})

    if "started_at" in record and "finished_at" in record and "phases_completed" in record:
        return frozenset({"shape1_started_finished_notes"})

    if "final_status" in record and "end_ts" not in record:
        return frozenset({"shape2_final_status_no_end_ts"})

    if "ts_start" in record and "ts_end" in record and "result" in record:
        return frozenset({"shape3_ts_start_ts_end_result"})

    if "completed_at" in record and "finished_at" not in record and "final_status" not in record:
        return frozenset({"shape4_completed_at_status"})

    return frozenset()


def _classify_tools(record: dict) -> frozenset[str]:
    if record.get("run_id") is None and record.get("seq") is None:
        return frozenset({"interactive_null"})
    if "phase" not in record or "agent" not in record:
        return frozenset({"tools_phase_agent_null_gap"})
    return frozenset()


def _classify_events(record: dict) -> frozenset[str]:
    labels = set()
    if "reason_code" not in record:
        labels.add("events_reason_code_null")
    if "tool_call_count" not in record:
        labels.add("events_tool_call_count_absent")
    return frozenset(labels)
