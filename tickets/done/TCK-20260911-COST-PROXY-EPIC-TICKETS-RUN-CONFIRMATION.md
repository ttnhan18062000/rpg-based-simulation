---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION
phase: done
date: 2026-09-11
tags: [agent-monitoring, data-quality]
---

# TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION

## Title
Confirm `cost_proxy_score` is non-null for `implement-epic`/`create-tickets` on their next real run

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260904-COST-PROXY-EPIC-TICKETS` (shipped 2026-09-06, PR #141) wired sidecar coverage into
`implement-epic.js` (4 top-level sites, negative seq range) and `create-tickets.js` (4 of 7 sites)
and widened `record_events.py`'s workflow filter, so both workflows should now record real
non-null `tool_call_count`/`cost_proxy_score` instead of null. `roadmap.md` item 10 records it as
**shipped (code) — real-run confirmation outstanding**, and that acceptance signal has never been
confirmed.

The reason is now established rather than assumed. Verified 2026-09-11 against every
`agent-monitoring/data/*/runs.jsonl` shard: **zero `implement-epic` or `create-tickets` runs have
occurred since 2026-09-06.** The signal is not unverified through neglect — it is unverifiable
until one of those two workflows actually runs. Every ticket in that window was closed by
hand-orchestration or `implement-ticket`.

This ticket therefore opens `BLOCKED` by design, on an event rather than on other work. It exists
so the check is not silently forgotten the next time an epic or ticket-creation pass happens —
which is exactly how this signal went unconfirmed for the five days since it shipped.

## Scope
- On the next real `implement-epic` or `create-tickets` invocation, read that run's record in
  `agent-monitoring/data/<ISO-week>/runs.jsonl` and its events in the sibling `events.jsonl`, and
  confirm `cost_proxy_score` and `tool_call_count` are non-null and non-zero where tool calls
  genuinely occurred.
- Check both workflows before closing — they were wired at different call-site coverage levels
  (`implement-epic` at 4/4 real top-level sites, `create-tickets` at 4 of 7), so confirming one
  does not confirm the other.
- For `implement-epic` specifically, confirm the negative-`seq` range (`-1..-4`) used by its
  top-level sites did not collide with the positive-`seq` `batchEvents` rows under the same
  `run_id` — the collision this design deliberately avoids. `test_batch_top_level_negative_seq_and_child_ticket_positive_seq_do_not_cross_contaminate`
  covers it synthetically; this is the real-data counterpart.
- Update `roadmap.md` item 10 from "shipped (code) — real-run confirmation outstanding" to fully
  shipped, or record what was actually observed if the values are still null.

## Out of Scope
- Triggering an `implement-epic`/`create-tickets` run purely to satisfy this check. Running a
  multi-agent workflow costs real tokens and needs the user to ask for it; this ticket waits for a
  run that happens for its own reasons rather than manufacturing one.
- The 3 deliberately-excluded `create-tickets` sites (`writeMonitoring`'s own `agent()` call and
  the 2 `pipeline()` fan-out sites) — documented as permanently excluded, not a gap. Null values
  there are correct and must not be treated as a failure.
- Any change to `record_events.py`'s `compute_tool_stats()` or the two workflow files — this is a
  verification ticket. If the check fails, file a separate fix ticket rather than repairing here.

## Acceptance Criteria
- [x] A real `implement-epic` run is observed with non-null `cost_proxy_score`/`tool_call_count` (run and values below) - met literally, and the observation found the values were false zeros; fixed (see Implementation Notes).
- [x] A real `create-tickets` run is observed the same way.
- [x] `implement-epic`'s negative-seq top-level rows and positive-seq `batchEvents` rows are confirmed non-contaminating on real data.
- [x] `roadmap.md` item 10 updated to reflect the confirmed outcome either way.

## Related Tickets
- `TCK-20260904-COST-PROXY-EPIC-TICKETS` (done) — shipped the code whose signal this confirms.
- `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP` (done) — the sibling correctness fix
  distinguishing "confirmed zero calls" from "no attribution data"; relevant when interpreting a
  zero here.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` §2 — where this
  item's acceptance signal is defined.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 10.
- `docs/agent-monitoring/schema.md` — `cost_proxy_score` semantics and the null-vs-zero convention.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `agent-monitoring/data/<ISO-week>/{runs,events}.jsonl` (read-only, for verification)
- `.claude/workflows/implement-epic.js`, `.claude/workflows/create-tickets.js` (reference only)

## Assumptions / Open Questions
- Blocked on an external event, not on other work. If a long time passes with neither workflow
  running, that is itself a finding worth surfacing — it would mean both workflows are effectively
  unused, which bears on whether the cost-proxy extension was worth building. Note it rather than
  letting the ticket sit silently.

## Implementation Notes
**Premise re-checked against the run data (2026-09-30); it holds, and the blocking event has happened.**
- `create-tickets`, AC2, met on two post-fix runs. `CREATE-TICKETS-DOCS-PLANS-SCRIPTS-TOOLS-GOVERNANCE-EPIC`
  (2026-09-29): Comprehend 86 tool calls (cps 238.5), Structure 19 (164.1), write-sequence 3, link-epic 3;
  the parallel Investigate/Write rows are 0 by design. `CREATE-TICKETS-DOCS-PLANS-IDEA-STALE-PLANNING-DOC-
  STATUS-AFTER-SHIP` (2026-09-30, the workflow pilot): Comprehend 27, Structure 13, matching the
  `tools.jsonl` rows per sidecar seq (the two earlier misattributed runs were fixed by
  `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED`).
- `implement-epic`, AC3, met: run `FOLDER-tickets-todos-systemic-world-first-wave` (2026-09-29) has 12
  tool rows at seq -1 (Discover) and 55 at seq -2 (batch-monitoring-write) and none at the child rows'
  seq 1-2, so the ranges do not contaminate.
- **AC1 found a defect, so it needed code.** That run's two child-ticket events (`agent: implement-ticket`,
  seq 1-2) were recorded `tool_call_count: 0`, `cost_proxy_score: 0.0`. Those rows never have a sidecar
  (the children ran under their own run ids; the epic's top-level sites use the negative seq range and
  have no events row), so 0 means "no attribution possible", not "confirmed zero". A false zero is the
  class `omit_when_unattributed` already handles for hand-orchestrated closures. `compute_tool_stats` now
  omits an implement-epic batch row (`agent == "implement-ticket"`, seq > 0) that has no matching tool
  rows, so it records null. The epic's own spend stays queryable in `tools.jsonl` at seq -1..-4.
- Docs updated: `roadmap.md` item 10, `standalone_items.md` §2, `docs/agent-monitoring/schema.md`.

## Test Summary
`tests/tools/test_record_events.py` 32 passed: new `test_epic_child_batch_rows_without_tool_rows_are_omitted_not_
false_zero` (null when unattributed, real value kept when rows exist, non-epic implement-ticket rows keep
(0, 0.0)); the existing collision test's expectations unchanged (its seq=2 row uses a non-child agent).

## Files Changed
- `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py`
- `docs/agent-monitoring/schema.md`, `docs/plans/agent_infrastructure/ai_first_hardening_epics/{roadmap,standalone_items}.md`
- this ticket

## Completion Summary
Done. Both halves confirmed on real runs: `create-tickets` attributes correctly after the earlier fix;
`implement-epic`'s negative-seq rows are clean on real data, and the child-ticket events' false zeros are
now null. Existing historical rows are not backfilled (append-only precedent).
