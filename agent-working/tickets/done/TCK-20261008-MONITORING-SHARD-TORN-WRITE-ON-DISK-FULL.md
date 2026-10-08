---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL
phase: done
date: 2026-10-08
tags: [agent-monitoring, data-quality]
---

# TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL

## Title
A full disk tears a monitoring record, and the next append glues onto it

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
On 2026-10-08, /mnt/data reached 100%. Three live W41 tools shards (agent-working-planner-seat, rpg-seat, rpg-planner-seat) now hold one invalid JSON line each. A record was cut short mid-write, and the next hook append continued on the same line (seen in `make agent-monitoring-retro`: "invalid JSON — Expecting ':' delimiter"). Cause: `tools/agent-monitoring/writer.py::write_line`/`write_lines` append through buffered `open(path, "a")` and never check that the file ends in a newline, so one failed write corrupts the following good record too.

## Scope
- `writer.py` `write_line` and `write_lines`: under the existing lock, if the file is non-empty and its last byte is not `\n`, write a `\n` first, so a torn tail stays one bad line and the new record starts clean.
- Write each call's payload with a single `os.write` on an O_APPEND fd (as `_write_diagnostic` already does). If the write fails or is short, truncate back to the size before the write, so no partial record is left. On failure, still write the diagnostic and return False; never raise.

## Out of Scope
Repairing the three existing bad lines (the reader already skips and warns). The disk-headroom guard (TCK-20261008-SESSION-DISK-HEADROOM-GUARD).

## Acceptance Criteria
1. A file whose last line has no newline: the next `write_line` produces two lines, with the new record parseable on its own line.
2. A simulated short or ENOSPC write (monkeypatched `os.write`) leaves the file byte-identical to before, writes a diagnostic and returns False.
3. Existing writer tests pass; the "monitoring write failure never fails the workflow" rule holds.

## Related Tickets
TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE (same data-hygiene area, different defect).

## Related Docs
docs/agent-monitoring/schema.md

## Related Stored Artifacts
agent-working/agent-monitoring/retro/RETRO-2026-W41.md (Addendum 2026-10-08)

## Related Code Areas
tools/agent-monitoring/writer.py, tests/tools/ (writer tests)

## Assumptions / Open Questions
None.

## Implementation Notes
`writer.py` gained `_append_all_or_nothing`: under the existing lock it heals a missing trailing newline, writes the whole payload (heal byte included) with one `os.write` on an O_APPEND fd, and on a short or failed write truncates back to the prior size and re-raises so the caller records the diagnostic and returns False. `write_line`/`write_lines` use it. The existing forced-failure test patched `builtins.open`; it now patches `os.open` for the target.

## Test Summary
`pytest tests/tools -k 'monitoring or writer or hook'`: all pass; 5 new writer tests (torn tail single and batch, no extra newline, short write, ENOSPC).

## Files Changed
tools/agent-monitoring/writer.py, tests/tools/test_monitoring_writer.py

## Completion Summary
All three acceptance criteria met. The three existing bad shard lines are untouched (out of scope).
