---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-CREATE-TICKETS-TAG-CHECK
phase: done
date: 2026-07-06
tags: [tagging, workflows, agent-monitoring]
---

# TCK-20260706-CREATE-TICKETS-TAG-CHECK

## Title
Extend the tag-registry check to create-tickets.js's Structure phase — plus register 3 tags that were live-unregistered

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Follow-up to `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`, which explicitly deferred `create-tickets.js`
(same tag-registry-awareness gap, different workflow). User asked to fix it. While auditing
`create-tickets.js`'s Structure phase to design the fix, found a **live, currently-real bug**, not
just a theoretical gap: the Structure phase's `tags` field is restricted to a closed 4-tag list
(`api-design`, `debugging`, `performance`, `security` — see `TASK_SCHEMA`/prompt Step 4), the exact
same 4 tags named in `ticket_tagging.md`'s skill-suggestion table and `ticket-scoper.md`'s own
prompt — yet only `security` had ever actually been registered in
`docs/guidelines/tag_registry.jsonl` (the other 3 never appeared in the corpus this registry was
seeded from). Any ticket `create-tickets.js` or `ticket-scoper` assigned `debugging`,
`performance`, or `api-design` to would already have been failing (or would now fail immediately at
the new Scope gate) purely because of this registration gap, not a bad tag choice.

## Scope
- **Immediate fix (already done, disclosed here for traceability):** registered `api-design`,
  `debugging`, `performance` in `docs/guidelines/tag_registry.jsonl` as `process-skill-signal`
  (matching `security`'s existing category) via the real `tools/tag_registry.py add` CLI.
- **`.claude/workflows/create-tickets.js`**: after the Structure phase's existing `droppedScopes`
  short_scope-dedup block (the closest existing precedent — defensive skip + warning + continue,
  not a whole-batch abort), add an orchestrator-run tag-registry check across all
  `dedupedTasks[].tags` at once (same `check_tags_registered` function, same
  individually-quoted-argv/marker-JSON pattern as `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`).
  Partition `dedupedTasks` into `tasksReadyToWrite` (proceed to Write phase) and
  `tasksWithUnregisteredTags` (skipped — not written, not included in the SEQUENCE.md dependency
  graph, reported in the final return value alongside the existing `scope_dupes_dropped` field).
  `pushEvent` gains a `reason_code` parameter (mirroring `implement-ticket.js`); a
  `Structure`/`create-tickets` `blocked` event with `reason_code: 'tag_registry_rejection'` is
  pushed when any task is skipped this way.
- **`tools/agent-monitoring/generate_retro.py`**: rename the "DOD_BLOCKED Reason Codes" report
  section to something accurate now that `reason_code` also covers Scope
  (conflicts/tag-registry) and, with this ticket, `create-tickets`'s Structure phase — no other
  code change needed, since the aggregation already iterates all events regardless of source
  workflow.
- **Docs**: `docs/ai/workflows.md`'s `create-tickets` phase table (Structure row) and
  `docs/agent-monitoring/schema.md` (`reason_code` table's `Phase(s)` column, generalize the
  explanatory prose beyond "two phases").

## Out of Scope
- Any change to the Write phase itself, or to `ticket-scoper.md`'s per-ticket agent prompt used
  by Write (Write only formats already-decided task data; the check happens before Write runs).
- Retroactively re-tagging any already-written ticket under `tickets/todos/`.

## Acceptance Criteria
- [ ] `api-design`, `debugging`, `performance` are registered (done; verified via
      `tools/tag_registry.py list`).
- [ ] A batch containing a task with an unregistered tag: that task is not written, is reported in
      the final return's `tags_not_registered` field, and does not appear in `SEQUENCE.md`'s
      dependency graph even if another task in the batch references it.
- [ ] A batch with no unregistered tags is completely unaffected (identical behavior to before
      this ticket).
- [ ] The Structure-phase `blocked` event (when it fires) carries `reason_code:
      "tag_registry_rejection"`.
- [ ] `generate_retro.py`'s report section is renamed accurately and still aggregates correctly
      across both workflows' events.
- [ ] `node --check` passes; no regressions in `tests/tools/`.

## Related Tickets
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK (the sibling fix for `implement-ticket.js`, explicitly
  deferred this exact gap)
- TCK-20260706-MONITORING-REASON-CODE (the `reason_code` mechanism reused here)
- TCK-20260706-TAG-REGISTRY-DATA (the registry these 3 tags were missing from)

## Related Docs
- docs/ai/workflows.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/workflows/create-tickets.js (Structure phase, `pushEvent`)
- tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- Assumed "skip the affected task, continue the batch" (mirroring the existing `droppedScopes`
  precedent) is correct over "abort the whole batch" — `create-tickets.js` is a batch tool whose
  entire point is producing triageable output for a human, and one bad tag on one concern
  shouldn't block N unrelated concerns in the same proposal doc.
- The 3-tag registration gap was a real, live bug independent of this ticket's main fix — recorded
  here for traceability since it was discovered during this ticket's investigation, not assumed
  beforehand.

## Implementation Notes
Implemented per plan.md's 7 steps:

1. **Live-bug fix (done first, during investigation):** registered `api-design`, `debugging`,
   `performance` via `tools/tag_registry.py add`, all `process-skill-signal` — confirmed via a
   direct registry read that only `security` had ever been registered despite all 4 being named in
   the same skill-suggestion table both `ticket-scoper.md` and `create-tickets.js` reference.
2. **`create-tickets.js` `pushEvent`**: gained a 6th `reasonCode` param, mirroring
   `implement-ticket.js`'s addition exactly.
3. **Tag-registry check**: inserted right after the existing `droppedScopes` block — same
   orchestrator-run, individually-quoted-argv, `TAG_CHECK_JSON:`-marker pattern as
   `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`, checked once across the union of all tasks' tags (not
   once per task) for efficiency. Partitions `dedupedTasks` into `tasksReadyToWrite` and
   `tasksWithUnregisteredTags`, mirroring the `droppedScopes` defensive-skip-and-continue
   precedent rather than aborting the whole batch.
4. **Replaced every subsequent `dedupedTasks` reference used for writing or graphing** with
   `tasksReadyToWrite`: the Write phase's `pipeline()` call, both `succeeded.length` comparisons
   (so a tag-check-skipped task is never misreported as "write agent returned null" — a real bug
   that would have existed if I'd left these comparing against the original `dedupedTasks.length`),
   and the SEQUENCE.md `batchIdSet`/`depMap` construction. Verified line-by-line via
   `grep -n dedupedTasks` before and after — final state shows `dedupedTasks` only appears where
   it's being computed or tag-checked, never downstream in Write/SEQUENCE.md.
5. **Final return**: added `tags_not_registered: tasksWithUnregisteredTags` alongside the existing
   `scope_dupes_dropped` field.
6. **`generate_retro.py`**: renamed `"## DOD_BLOCKED Reason Codes"` → `"## Reason Codes"` (the
   section now covers Scope and Structure too, not just Verify/DOD_BLOCKED); updated the
   explanatory comment above it. No aggregation-logic change — confirmed workflow-agnostic by
   inspection, then confirmed again with a new test
   (`test_reason_code_aggregation_is_workflow_agnostic`) mixing `implement-ticket` and
   `create-tickets` events in one report and checking they tally together correctly.
7. **Docs**: `docs/ai/workflows.md`'s `create-tickets` Structure/Write rows and Artifacts-produced
   list; `docs/agent-monitoring/schema.md`'s `reason_code` section (now "three phases" instead of
   two, `tag_registry_rejection`'s `Phase(s)` column now lists Scope/Structure/Verify).

**Updated `tests/tools/test_generate_retro.py`**: the 3 existing tests' string assertions updated
from `"DOD_BLOCKED Reason Codes"` to `"## Reason Codes"` (the actual renamed heading); added the
new cross-workflow aggregation test.

## Test Summary
- `node --check .claude/workflows/create-tickets.js` → syntax OK.
- `pytest tests/tools/test_generate_retro.py -v` → 4 passed (1 new + 3 updated).
- Full `pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py` → 492 passed, 2
  failed (the same 2 pre-existing, unrelated `test_search_mcp.py` failures disclosed repeatedly
  this session).
- `make knowledge-index-update` → 5 files re-embedded, completed successfully.
- `python3 tools/tag_registry.py list` → confirmed `api-design`, `debugging`, `performance` now
  present.
- Could not exercise the new gate via a live `create-tickets` run on this ticket itself (same
  bootstrapping limitation as every workflow-orchestration ticket this session) — verified via
  code read-through (the `grep -n dedupedTasks` line-by-line check) instead.

## Files Changed
- `docs/guidelines/tag_registry.jsonl` (3 tags registered: `api-design`, `debugging`, `performance`)
- `.claude/workflows/create-tickets.js` (`pushEvent` reason_code param, tag-registry check,
  `tasksReadyToWrite` threaded through Write/SEQUENCE.md, `tags_not_registered` in final return)
- `tools/agent-monitoring/generate_retro.py` (section renamed)
- `tests/tools/test_generate_retro.py` (updated + 1 new test)
- `docs/ai/workflows.md`, `docs/agent-monitoring/schema.md` (updated)
- `tickets/inprogress/TCK-20260706-CREATE-TICKETS-TAG-CHECK.md` → `tickets/done/...`
- `staging_artifacts/TCK-20260706-CREATE-TICKETS-TAG-CHECK/` → `stored_artifacts/...`

## Completion Summary
Closed the sibling gap `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK` explicitly deferred:
`create-tickets.js`'s Structure phase now checks all tasks' tags against the registry before
Write runs, skipping (not writing) any task with an unregistered tag while letting the rest of the
batch proceed — mirroring the workflow's own existing `droppedScopes` defensive-skip precedent
rather than introducing a new whole-batch-abort behavior. Also found and fixed a real, currently-
live bug during investigation (not assumed): 3 of the 4 tags this exact workflow's own schema
restricts itself to (`api-design`, `debugging`, `performance`) had never actually been registered,
meaning any ticket ever tagged with them would already have been failing (or would now fail
instantly at the Scope gate) for a pure registration-gap reason unrelated to tag quality — fixed
immediately rather than left as a ticking time bomb. Reused the `reason_code` tracing mechanism
end to end: `generate_retro.py`'s aggregation needed zero logic changes to pick up the new
`Structure`-phase codes (confirmed by a new cross-workflow test), only a section-title rename to
stop implying `DOD_BLOCKED`-only scope.
