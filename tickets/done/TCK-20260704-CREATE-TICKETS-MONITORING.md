---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260704-CREATE-TICKETS-MONITORING
phase: open
date: 2026-07-04
tags: [agent-monitoring, create-tickets, observability]
---

# TCK-20260704-CREATE-TICKETS-MONITORING

## Title
Instrument `create-tickets` workflow with agent-monitoring records

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/ai/agent_infrastructure_audit.md` and follow-up investigation confirmed that `.claude/workflows/create-tickets.js` has zero integration with `agent-monitoring/` — no calls to `record_run.py` or `record_events.py` at any of its five phases or four exit points, and no `"create-tickets"` value ever appears in `runs.jsonl`. This is the only one of the three primary workflows (`create-tickets`, `implement-ticket`, `implement-epic`) with no observability coverage at all — the ticket-generation phase, the literal first step of the pipeline, is currently invisible to monitoring. This ticket mirrors the existing `writeMonitoring`/`pushEvent` pattern already used in `implement-ticket.js` and `implement-epic.js` into `create-tickets.js`.

## Scope
- Add a `pushEvent`/`writeMonitoring` bookkeeping pattern to `.claude/workflows/create-tickets.js`, mirroring `implement-ticket.js`'s implementation.
- Capture a start timestamp at the beginning of the Comprehend phase (add `ts` to `COMPREHEND_SCHEMA`, instruct the agent to run `date -u +%Y-%m-%dT%H:%M:%SZ` first).
- Derive a stable `run_id` from the `source` argument (mirrors `implement-epic`'s `FOLDER-{path}` convention): `CREATE-TICKETS-{sanitized source path}`.
- Push one event per phase (Comprehend, Investigate — one per concern investigated, Structure, Write — one per ticket written, Link when applicable).
- Call `writeMonitoring(finalStatus)` at all four exit points: the two `NOTHING_TO_CREATE` early returns (empty concerns, all-duplicates, no tasks after structure) and the final `DONE` return.
- Document the new `workflow: "create-tickets"` value and the `tier: "n/a"` placeholder (create-tickets doesn't operate on a single ticket's tier) in `docs/agent-monitoring/schema.md`.

## Out of Scope
- The `INVALID_ARGS` early return (missing `source` argument) — no agent call has happened yet at that point, so there is nothing meaningful to record; this mirrors how `implement-ticket.js` has no pre-Scope-phase monitoring hook either.
- Retroactively backfilling any historical `create-tickets` runs — none exist in `runs.jsonl` to backfill (confirmed: zero matches for `"create-tickets"` in the file).
- Fixing the broader schema drift found in the audit (null `workflow` fields on ~21% of legacy `runs.jsonl` records, inconsistent `phase`/`agent` casing in `events.jsonl`) — tracked separately as a deferred idea doc, not implemented here.
- Adding automated tests for `.claude/workflows/*.js` orchestration scripts in general — none of the three primary workflows (including `implement-ticket.js` and `implement-epic.js`) currently have automated test coverage; introducing that harness is a separate, much larger effort.

## Acceptance Criteria
- [ ] `create-tickets.js` computes a `run_id` and a `startTs` before the first agent call.
- [ ] A `pushEvent` call exists for each of the five phases (Comprehend, Investigate ×N concerns, Structure, Write ×N tickets, Link).
- [ ] A `writeMonitoring(finalStatus)` call exists at all four `return` statements, using the same `agent()`-based bash/record_run.py/record_events.py pattern as `implement-ticket.js`.
- [ ] The emitted run record satisfies `record_run.py`'s `REQUIRED` field set (`run_id`, `start_ts`, `workflow`, `tier`, `final_status`) and the emitted event records satisfy `record_events.py`'s `REQUIRED` set (`run_id`, `seq`, `ts`, `phase`, `agent`, `summary`, `status`) with `status` in `{ok, failed, blocked, skipped}`.
- [ ] `node --check .claude/workflows/create-tickets.js` passes (no syntax errors introduced).
- [ ] `docs/agent-monitoring/schema.md` documents the new `workflow: "create-tickets"` value and the `tier: "n/a"` convention.

## Related Tickets
None.

## Related Docs
- docs/ai/agent_infrastructure_audit.md
- docs/agent-monitoring/schema.md
- docs/ai/workflows.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .claude/workflows/create-tickets.js
- .claude/workflows/implement-ticket.js (pattern reference)
- .claude/workflows/implement-epic.js (pattern reference)
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
None — pattern is fully established by the two existing workflows; no unresolved design questions.

## Implementation Notes
Mirrored the `pushEvent`/`writeMonitoring` pattern from `implement-ticket.js` into `create-tickets.js`:
- `run_id` is derived from the `source` arg path (`CREATE-TICKETS-{sanitized path}`), since no single `ticket_id` exists until the Write phase and this workflow can produce many tickets in one run — mirrors `implement-epic`'s `FOLDER-{path}` convention.
- `start_ts` is captured by the Comprehend agent (added a `ts` field to `COMPREHEND_SCHEMA`, added a Step 0 instructing it to run `date -u` first) — this is the earliest point an agent call actually happens.
- One `pushEvent` per phase: Comprehend (1), Investigate (1 per concern, `skipped` for duplicates), Structure (1), Write (1 per ticket written, plus a `failed` event if any write agent returned null), Link (1, only when `epic_id` given).
- `writeMonitoring(finalStatus)` called at all 4 real exit points: the two `NOTHING_TO_CREATE` returns (empty concerns; all-duplicates) that existed already, the `NOTHING_TO_CREATE` after Structure, and the final `DONE` return.
- The pre-agent `INVALID_ARGS` guard (missing `source`) intentionally has no monitoring call — no agent has run yet, nothing to record, matching how `implement-ticket.js` has no hook before its first agent call either.
- `create-tickets` does not register a `.claude/current_run` sidecar per agent call (unlike `implement-ticket`/`implement-epic`), so `tool_call_count` is always `null` on its events — documented in `schema.md` rather than silently omitted.
- `tier` is always `"n/a"` for `create-tickets` runs since the workflow doesn't operate on one ticket's tier — each generated ticket gets its own tier decided during Structure. Documented as a real enum value in `schema.md`, not a silent magic string.

## Test Summary
No automated test harness exists for `.claude/workflows/*.js` orchestration scripts — confirmed neither `implement-ticket.js` nor `implement-epic.js` (the two workflows this change mirrors) have any test coverage either; this is a pre-existing repo-wide gap, not something introduced or fixed by this ticket.

Verification performed:
- `node --check .claude/workflows/create-tickets.js` — passes, no syntax errors.
- Manually cross-checked every emitted run/event record shape against `tools/agent-monitoring/record_run.py`'s `REQUIRED = {run_id, start_ts, workflow, tier, final_status}` and `tools/agent-monitoring/record_events.py`'s `REQUIRED = {run_id, seq, ts, phase, agent, summary, status}` + `VALID_STATUS = {ok, failed, blocked, skipped}` — all satisfied.
- Traced all 4 monitored exit points (`grep -n "writeMonitoring(" .claude/workflows/create-tickets.js` → 4 matches) against all 4 real `return` statements in the file (excluding the pre-agent `INVALID_ARGS` guard, out of scope by design).

## Files Changed
- `.claude/workflows/create-tickets.js` — added monitoring instrumentation (run_id derivation, pushEvent/writeMonitoring, calls at all phases and exit points)
- `docs/agent-monitoring/schema.md` — documented `workflow: "create-tickets"`, `tier: "n/a"`, `final_status: "NOTHING_TO_CREATE"`, and the `create-tickets` phase list / `tool_call_count` caveat

## Completion Summary
`create-tickets` is now the third workflow (alongside `implement-ticket` and `implement-epic`) with full `agent-monitoring` coverage, closing the gap identified in `docs/ai/agent_infrastructure_audit.md` and the follow-up investigation. Historical `create-tickets` runs remain unrecorded (none existed to backfill) — only runs from this point forward will appear in `runs.jsonl`/`events.jsonl` under `workflow: "create-tickets"`.
