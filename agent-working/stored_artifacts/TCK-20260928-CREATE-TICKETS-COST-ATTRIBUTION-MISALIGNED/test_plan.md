---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED

No JS test runner exists in this repo for `.claude/workflows/*.js` — all tests are static,
raw-source-text-parsing pins, matching every other test file in this family
(`test_epic_create_tickets_sidecar_orchestrator.py`, `test_finalize_epic_parent_advisory_pin.py`,
etc.). They pin the orchestrator's own source text and the agent prompt's wording, not runtime
behavior — an honestly-disclosed limitation shared by this entire test family.

New file: `tests/tools/test_create_tickets_sidecar_reset_and_failure_visibility.py`

1. `test_write_monitoring_clears_the_sidecar_before_any_other_step` — Step 0 exists, precedes
   Step 1, and contains the exact `printf '{}' > .claude/current_run` clear command.
2. `test_every_return_after_the_first_is_preceded_by_write_monitoring` — each of the 3
   `NOTHING_TO_CREATE` exit blocks, plus the final `DONE` exit, calls `writeMonitoring()` before
   its own `return`. (The very first exit, INVALID_ARGS, is excluded — no sidecar write has run
   yet at that point.)
3. `test_write_sidecar_no_longer_blanket_swallows_every_failure` — the old `2>/dev/null || true`
   is gone; an explicit `WRITESIDECAR_EXIT` marker exists.
4. `test_write_sidecar_warns_on_failure_via_log` — a failed write triggers a `log()` WARNING.
5. `test_write_sidecar_still_never_raises_on_failure` — the exit-code echo is unconditional (not
   gated behind `&&`), so the shell command itself always exits 0 regardless of the inner
   `python3 -c` script's own success/failure (monitoring fail-open rule preserved).
6. `test_write_sequence_now_has_a_matching_push_event` — `write-sequence`'s `agent()` result is
   captured and fed into a new `pushEvent('Write', 'write-sequence', ...)` call.
7. `test_write_sequence_push_event_is_after_its_writesidecar_and_agent_call` — correct ordering
   (`writeSidecar` → `agent()` → `pushEvent`).

Existing file updated: `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — one
adjacency-pin literal updated to match the new `const seqResult = await agent(` assignment (a
mechanical consequence of fix #1 above, not a logic change to what the test proves).

## Verification performed

- All 7 new tests confirmed to **fail** against the pre-fix source (`git stash` of just
  `create-tickets.js`, re-run, 6 of 7 failed — the 7th, exit-path coverage, was already true
  pre-fix and correctly unaffected), then confirmed to **pass** after restoring the fix.
- `node --check .claude/workflows/create-tickets.js` — exit 0.
- Full existing sidecar/orchestrator/meta-conformance test files re-run for regressions:
  `test_epic_create_tickets_sidecar_orchestrator.py`, `test_step0_ts_orchestrator.py`,
  `test_workflow_meta_conformance.py`, `test_record_events.py`,
  `test_retrieval_event_wrapper_single_source.py` — all pass.
- AC4: bare `pytest tests/tools/`, run from the worktree — see ticket's own Test Summary for the
  final count.
