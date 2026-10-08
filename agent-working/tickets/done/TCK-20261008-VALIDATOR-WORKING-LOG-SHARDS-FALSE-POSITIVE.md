---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261008-VALIDATOR-WORKING-LOG-SHARDS-FALSE-POSITIVE
phase: done
date: 2026-10-08
tags: [agent-monitoring, data-quality]
---

# TCK-20261008-VALIDATOR-WORKING-LOG-SHARDS-FALSE-POSITIVE

## Title

The validator's "DONE has no working_log entry" check reads only working_log.csv, so every closure recorded in a working_log shard warns

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

`validate.py` cross-checks every DONE run against `agent-working/tickets/working_log.csv` only. Closures are recorded in per-branch `working_log` shards (`data/YYYY-Www/*.working_log.jsonl`, written by `record_hand_orchestrated_closure.py`), so about 126 of the 165 warnings on main 821d543a6 were false positives and would drown the report built by TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE.

## Scope

The DONE-to-working_log check also reads the working_log shards (same source the closure tool writes).

## Out of Scope

The remaining historical warnings (runs genuinely without a row), the incomplete-run warning, any gate.

## Acceptance Criteria

- [x] A DONE run whose row exists only in a shard raises no warning
- [x] A DONE run with no row anywhere still warns
- [x] The warning count before and after is recorded

## Related Tickets

TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE, TCK-20261007-EPIC-RETRO-READABILITY-AND-MONITORING-DATA-HYGIENE

## Related Docs

docs/agent-monitoring/schema.md

## Related Stored Artifacts

None.

## Related Code Areas

tools/agent-monitoring/validate.py, tests/tools/test_validate_agent_monitoring.py

## Assumptions / Open Questions

None. Filed by the planner as a fourth ticket in the retro hygiene batch.

## Implementation Notes

`working_log_shard_ticket_ids(data_dir)` reads the `working_log` shards with the existing shard loader and `main()` unions their ticket ids with the CSV's before the check. Warning counts on the real corpus, main 821d543a6: **before 165 total / 131 for W40+; after 35 total / 1 for W40+**. The one W40+ warning left is real: TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT-ADDENDUM has no working_log row in the CSV or any shard.

## Test Summary

`pytest tests/tools/test_validate_agent_monitoring.py`: shard-only row raises no warning, no row anywhere still warns (and the W40+ count says 1 of 1), a CSV row still satisfies the check.

## Files Changed

tools/agent-monitoring/validate.py, tests/tools/test_validate_agent_monitoring.py

## Completion Summary

Fixed; all acceptance criteria met. Before/after counts above.
