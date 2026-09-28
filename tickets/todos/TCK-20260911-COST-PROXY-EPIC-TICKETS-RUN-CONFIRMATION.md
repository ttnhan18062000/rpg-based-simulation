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
**2026-09-28 partial check (read against `origin/main` @ `9bcae32c5`), recorded without closing:**

- `implement-epic`: **still zero runs** since 2026-09-06. AC1 and AC3 remain unverifiable, so the
  ticket stays `BLOCKED` on that half, as designed.
- `create-tickets`: **two real runs exist.** AC2's literal "non-null" is met, but the values are
  attributed to the wrong events, so AC2 is **not** marked confirmed:

  | run_id | event values (tcc / cps) | tools.jsonl rows by sidecar seq |
  |---|---|---|
  | `CREATE-TICKETS-PERF-M0-ARCHITECTURE-GOVERNANCE` (2026-09-13, W37) | seq1 Comprehend 60/174.4; seq2 investigate:C1 **7**; seq3 investigate:C2 **16**; seq4 Structure **0**; Write/Link 0 | seq1 comprehend 60; seq2 "Structure/structure" 7; seq3 "Write/ticket-scoper" 65 |
  | `CREATE-TICKETS-DOCS-PLANS-SIMULATION-SEMANTIC-CONTROL-PLANE-ROADMAP` (2026-09-23, W39) | seq1 Comprehend 120/394.9; seq2-7 investigate 0; seq8 Structure 28/124.9; seq9 Write 0; seq10 Link **0** | seq1 comprehend 120; seq8 structure **94** (08:47 → 13:05Z); **no rows at seq10** |

  Per this ticket's own Out of Scope ("if the check fails, file a separate fix ticket"), the
  attribution problem is filed as `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED`.
  Close the `create-tickets` half of this ticket when that one resolves, or when a new
  `create-tickets` run comes back clean.

**2026-09-28, `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED` closed — fix landed, this
half still stays open.** That ticket's investigation confirmed two real code defects in
`create-tickets.js` (silent `writeSidecar()` failures + no sidecar reset on any exit path,
explaining the 09-23 run's stuck-at-seq-8/4-hour-tail symptoms; plus an independent missing
`pushEvent()` for `write-sequence`) and fixed both. The 09-13 run's own seq/agent mismatch was
confirmed as the known concurrent-session sidecar-sharing class — recorded, not re-solved, not
fixable after the fact. **This ticket's own `create-tickets` half is deliberately NOT closed by
that fix**: the fix cannot retroactively repair the two already-recorded historical runs' rows
(both stay misattributed, permanently, per that ticket's own Out of Scope), and AC2 requires
non-null values landing on the *correct* events, which can only be confirmed against a genuinely
new `create-tickets` run made after the fix. Re-check this ticket the next time `create-tickets`
actually runs for real.

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
