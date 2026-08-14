---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-CREATE-TICKETS-TAG-CHECK
artifact_type: investigation
tags: [tagging, workflows, agent-monitoring]
---

# Investigation — TCK-20260706-CREATE-TICKETS-TAG-CHECK

## The live bug, confirmed by reading the registry directly

```
python3 -c "
import json
for line in open('docs/guidelines/tag_registry.jsonl'):
    e = json.loads(line)
    if e['tag'] in ('api-design','debugging','performance','security'):
        print(e['tag'], e['category'])
"
```
returned only `security process-skill-signal` before this ticket — `api-design`, `debugging`,
`performance` were absent. `create-tickets.js`'s `TASK_SCHEMA.tags` description and its Structure
prompt (Step 4, "tags") restrict assignable tags to exactly these 4 — a genuinely new tag is never
possible from this workflow by design. So the only way any of the other 3 could ever have been
used was already broken before this ticket, for a reason unrelated to whether the tag choice was
sound — pure registration-gap, not a tagging-quality issue. Fixed immediately (not deferred) via
the real CLI, matching this session's established seeding convention.

## create-tickets.js architecture (read in full, not assumed)

- `pushEvent` (line 101): `(phaseLabel, agentName, status, summary, ts)` — no `tool_call_count`
  (already documented in `schema.md` as always-null for this workflow — it doesn't register a
  `.claude/current_run` sidecar) and, before this ticket, no `reason_code` either.
- Structure phase (line 446+): one `agent()` call returns `structured.tasks[]`
  (`TASK_SCHEMA`, includes `.tags`), `structured.skipped[]` (concerns not converted at all).
- Existing defensive-skip precedent (line 637-652): `droppedScopes` — if the structure agent
  produces a duplicate `short_scope` despite instructions, that task is silently dropped from
  `dedupedTasks`, logged as a `WARNING`, and the batch continues. This is the shape to mirror for
  the tag-registry check, not a whole-batch-abort.
- Write phase (line 672+): `pipeline(dedupedTasks, task => agent(...))` — one parallel `agent()`
  call per task, writes the ticket file. Runs **after** `dedupedTasks` is finalized.
- SEQUENCE.md generation (line 758+): iterates `dedupedTasks` again to build a dependency graph
  and topologically sort ticket IDs — if a task is later excluded from writing (this ticket's new
  behavior), it must also be excluded here, or the graph would reference a ticket ID that was never
  written.
- Final return (line 872+): always `status: 'DONE'` if any tickets were written at all;
  `scope_dupes_dropped` is the existing precedent field for "these were silently excluded, here's
  why" — the new `tags_not_registered` field follows the identical shape.

## Why "skip the task, continue the batch" over "abort the whole batch"

`create-tickets.js` exists specifically to convert a multi-concern proposal doc into N tickets in
one pass — the existing `droppedScopes`/`structured.skipped` mechanisms already establish that
partial success (some concerns become tickets, some don't, all clearly reported) is the intended
failure mode for this workflow, not all-or-nothing. Aborting the entire batch over one task's tag
choice would be a UX regression relative to the workflow's own existing precedent, not a
consistency improvement.

## reason_code reuse requires zero generate_retro.py logic changes

`generate_retro.py`'s reason-code aggregation (`Counter(e.get("reason_code") for e in events if
e.get("reason_code"))`) iterates every event in the input window regardless of which workflow wrote
it — `create-tickets.js` and `implement-ticket.js` both append to the same
`agent-monitoring/events.jsonl`. Adding `reason_code` to `create-tickets.js`'s `pushEvent` calls
is automatically picked up with no aggregation-logic change needed. Only the report's section
*title* ("DOD_BLOCKED Reason Codes") is now inaccurate — it needs renaming to something that
doesn't imply DOD_BLOCKED-only scope, confirmed by re-reading that code, not assumed.
