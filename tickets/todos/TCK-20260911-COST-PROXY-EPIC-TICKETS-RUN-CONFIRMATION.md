---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION
phase: open
date: 2026-09-11
tags: [agent-monitoring, data-quality]
---

# TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION

## Title
Confirm `cost_proxy_score` is non-null for `implement-epic`/`create-tickets` on their next real run

## Status
BLOCKED

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
- [ ] A real `implement-epic` run is observed with non-null `cost_proxy_score`/`tool_call_count`,
      with the run_id and observed values recorded.
- [ ] A real `create-tickets` run is observed the same way.
- [ ] `implement-epic`'s negative-seq top-level rows and positive-seq `batchEvents` rows are
      confirmed non-contaminating on real data.
- [ ] `roadmap.md` item 10 updated to reflect the confirmed outcome either way.

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
(filled in during implementation)

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
