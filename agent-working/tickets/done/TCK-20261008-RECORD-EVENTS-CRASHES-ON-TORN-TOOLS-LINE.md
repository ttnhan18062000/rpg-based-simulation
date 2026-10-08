---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261008-RECORD-EVENTS-CRASHES-ON-TORN-TOOLS-LINE
phase: done
date: 2026-10-08
tags: [agent-monitoring, data-quality]
---

# TCK-20261008-RECORD-EVENTS-CRASHES-ON-TORN-TOOLS-LINE

## Title

`record_events.compute_tool_stats` crashes on a torn tools-shard line, so a closure cannot be recorded

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

On 2026-10-08 the full disk left a torn line in several W41 tools shards. `compute_tool_stats` called `json.loads` on every line of every tools shard and raised, so `record_hand_orchestrated_closure.py` failed with "Expecting ':' delimiter" for every session, whichever shard held the line (agent-working-planner-seat, rpg-seat, rpg-planner-seat).

## Scope

Skip an invalid (or non-object) line and warn on stderr, as `generate_retro` does. Audit the other shard readers in `tools/agent-monitoring` for a bare `json.loads` on a closure or gate path.

## Out of Scope

Repairing the torn lines (the writer fix is TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL).

## Acceptance Criteria

1. A tools shard with a torn line plus a valid line: `compute_tool_stats` returns the valid row's stats and warns naming file and line.
2. No other reader on a closure or gate path has a bare `json.loads` over shard lines.

## Related Tickets

TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL

## Related Docs

docs/agent-monitoring/schema.md

## Related Stored Artifacts

None.

## Related Code Areas

tools/agent-monitoring/record_events.py, tests/tools/test_record_events.py

## Assumptions / Open Questions

None.

## Implementation Notes

`compute_tool_stats` now wraps `json.loads` in try/except ValueError (warning to stderr with file and line) and skips non-dict rows. Audit of the other shard readers (`gate_ledger`, `hand_closure_time`, `manifest`, `bash_command_mix`, `arch_verify_read_check`, `real_token_usage`, `validate`, `session_layer_report`, `main_integrity_report` tools/gate readers) found each already catches the error; the one bare `json.loads(line)` left (`main_integrity_report.py` working_log shards) is a report, not a closure or gate path.

## Test Summary

`pytest tests/tools/test_record_events.py`: 36 passed (1 new: torn line plus valid line plus a non-object line).

## Files Changed

tools/agent-monitoring/record_events.py, tests/tools/test_record_events.py

## Completion Summary

Fixed; both acceptance criteria met.
