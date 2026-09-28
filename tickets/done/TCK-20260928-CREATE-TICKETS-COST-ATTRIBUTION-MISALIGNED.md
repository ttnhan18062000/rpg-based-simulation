---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED
phase: done
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED

## Title

`create-tickets` runs record non-null `tool_call_count`/`cost_proxy_score`, but the values land on
the wrong events: unwired sites get counts, wired sites read 0, and one run's rows kept accruing
for 4 hours after the workflow ended.

## Status

DONE

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

Found while checking `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` against real data on
2026-09-28 (`origin/main` @ `9bcae32c5`). That ticket's Out of Scope says a failed check becomes a
separate fix ticket; this is that ticket.

`tools/agent-monitoring/record_events.py::compute_tool_stats()` attributes each tools.jsonl row
to the event with the same `(run_id, seq)`, where the row's `seq` is whatever
`.claude/current_run(.<session_id>)` said at tool-call time. `.claude/workflows/create-tickets.js`
writes that sidecar at 4 sites, each as `writeSidecar(events.length + 1, …)`: comprehend,
structure, write-sequence and link-epic. It deliberately skips the 2 `pipeline()` fan-outs
(investigate, write) and writeMonitoring. Its events get `seq: events.length + 1` from `pushEvent`.

Observed on the only two `create-tickets` runs since 2026-09-06:

| run_id | events (seq phase agent → tcc) | tools.jsonl rows (seq phase/agent → count) |
|---|---|---|
| `CREATE-TICKETS-PERF-M0-ARCHITECTURE-GOVERNANCE` (2026-09-13, W37) | 1 Comprehend → 60; 2 investigate:C1 → **7**; 3 investigate:C2 → **16**; 4 Structure → **0**; 5-6 Write → 0; 7 Link → 0 | 1 Comprehend/comprehend 60; **2 Structure/structure 7**; **3 Write/ticket-scoper 65** |
| `CREATE-TICKETS-DOCS-PLANS-SIMULATION-SEMANTIC-CONTROL-PLANE-ROADMAP` (2026-09-23, W39) | 1 Comprehend → 120; 2-7 investigate → 0; 8 Structure → 28; 9 Write → 0; 10 Link → **0** | 1 comprehend 120; 8 structure **94**, ts 08:47:31 → **13:05:56Z**; **nothing at seq 10** |

Three distinct anomalies, each with a lead to confirm or rule out:

1. **09-13 sidecar seqs don't match the current code.** For 2 concerns, the code's Structure
   sidecar is `events.length + 1` = 4 (1 comprehend + 2 investigate events pushed first), yet rows
   say Structure = 2. There's also a "Write/ticket-scoper" at 3, and no `writeSidecar` call uses
   agent `ticket-scoper` (`implement-ticket.js`'s Scope-phase sidecar does). So the effect is
   that Structure's 7 calls are credited to `investigate:C1` and the Structure event reads 0.
   Leads: a resumed Workflow run whose replayed `events` array was shorter at sidecar time; a
   hand-written or `implement-ticket` sidecar written concurrently in the same checkout (the
   known shared-sidecar contamination); or a stale script version. Confirm from the run's own
   sidecar/tools rows and `git log` of `create-tickets.js` (last changes: #141 2026-09-07,
   #236 2026-09-22).
2. **09-23 write-sequence/link-epic sidecar writes left no rows.** Rows stay at seq 8 through the
   Write fan-out (expected: unwired) and then through link-epic (not expected: it writes seq 10).
   Lead: whether `writeSidecar`'s `python3 -c` ran (it swallows errors with `2>/dev/null ||
   true`), and which file `post_tool_hook.py` read at the time (the session-scoped
   `.claude/current_run.<session_id>` versus the unscoped file).
3. **4-hour tail after the run.** The event was written with Structure = 28, but 94 rows carry
   seq 8, the last until 13:05Z. `create-tickets.js` never resets the sidecar when it finishes;
   `implement-ticket.js` does (`printf '{}' > .claude/current_run`). The lead is that later,
   unrelated tool calls in the same session kept being attributed to this finished run.

## Scope

1. Investigate anomalies 1-3 against the real rows (both runs), the sidecar-writing code, and
   `post_tool_hook.py`'s sidecar resolution order. Record which lead is confirmed for each in
   investigation.md, with evidence. Do not assume the leads above are right.
2. Fix what is confirmed as a code defect, most likely:
   - reset the sidecar at the end of `create-tickets.js` (and on its failure/early-return paths),
     mirroring `implement-ticket.js`;
   - make `writeSidecar` failures visible (a stderr warning) instead of silent, keeping the
     monitoring fail-open rule (it must never fail the workflow).
   If anomaly 1 turns out to be concurrent-session contamination (a known, separately-tracked
   class), record that and do not re-solve it here.
3. Regression tests in `tests/tools/` for each fix: e.g. a source pin that every
   `create-tickets.js` exit path resets the sidecar, and a unit test that the helper surfaces a
   write failure.
4. Update `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`'s Implementation Notes with the
   outcome. Close its `create-tickets` half only if the fix makes the attribution trustworthy for
   the next real run. Otherwise leave that half for the next real run.

## Out of Scope

- Wiring sidecar coverage into the `pipeline()` fan-out sites. That exclusion is deliberate
  (a concurrent shared-sidecar race) and documented in `compute_tool_stats()`.
- Rewriting historical W37/W39 event values. They are durable records; note the misattribution
  in investigation.md instead.
- `implement-epic` (no real run exists to check).
- Running `create-tickets` just to generate test data.

## Acceptance Criteria

- AC1: investigation.md gives a confirmed cause, with evidence, for each of anomalies 1-3, or
  explicitly states that one is unconfirmable and why.
- AC2: every confirmed code defect is fixed, with a regression test that fails on the pre-fix code.
- AC3: `create-tickets.js` leaves no live sidecar behind on any exit path.
- AC4: bare `pytest tests/tools/` passes, run from the worktree.

## Related Tickets

- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`: the check that found this.
- `TCK-20260904-COST-PROXY-EPIC-TICKETS`: the original wiring (#141).
- `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP`: the `omit_when_unattributed`
  semantics ("zero rows" vs "confirmed zero").

## Related Docs

- `docs/agent-monitoring/README.md`

## Related Stored Artifacts

None.

## Related Code Areas

- `.claude/workflows/create-tickets.js` (writeSidecar, pushEvent, all exit paths)
- `tools/agent-monitoring/record_events.py` (`compute_tool_stats`)
- `tools/agent-monitoring/post_tool_hook.py` (sidecar resolution)
- `.claude/workflows/implement-ticket.js` (sidecar reset precedent)

## Assumptions / Open Questions

- Assumes `create-tickets` is still expected to produce trustworthy per-event cost for its 4 wired
  sites. If the investigation shows that per-event attribution can't be made reliable here, say
  so, and propose recording run-level totals instead of per-event values, rather than patching
  symptoms.

## Implementation Notes

See `staging_artifacts/TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED/investigation.md`
for full findings. Summary:

- **Anomaly 1** (09-13 run): stale-script-version lead ruled out directly (`git diff` between the
  two commits touching `create-tickets.js` around that date shows only a cosmetic truncation-marker
  change to the sidecar/event logic). The phantom `"ticket-scoper"` agent literal at seq 3 is
  unambiguous evidence of a different workflow's sidecar write landing in the same file — confirmed
  as the class (same-session cross-workflow sidecar sharing, a variant of the same race
  `create-tickets.js`'s own code already documents for its deliberately-unwired fan-out sites), but
  the exact mechanism is unconfirmable: the historical sidecar's intermediate states are not
  durable/logged anywhere. Recorded, not re-solved, per Out of Scope.
- **Anomalies 2/3** (09-23 run): one real, confirmed code defect. `writeSidecar()`'s
  `2>/dev/null || true` swallowed every failure unconditionally, and `create-tickets.js` had no
  equivalent of `implement-ticket.js`'s sidecar-clear (its own comment claiming "mirrors
  implement-ticket.js's own... exclusion" was incomplete — implement-ticket.js's writeMonitoring
  actively *clears* the sidecar as "Step 0", not just omits its own writeSidecar call). Together
  these meant any silent write-sequence/link-epic failure left the sidecar stuck at Structure's own
  seq, absorbing everything downstream indefinitely (no rows at seq 9/10, 94 rows piled onto seq 8,
  the 4-hour tail).
- **Independent third defect found in the same pass**: `write-sequence`'s own `writeSidecar()` call
  had no matching `pushEvent()` anywhere in its code block — its own tool-call rows were
  permanently orphaned even when the write succeeded. Fixed alongside the above.
- Fix: (1) `writeMonitoring()`'s own agent prompt now clears the sidecar as its own "Step 0",
  mirroring `implement-ticket.js` exactly — since every real exit path already calls
  `writeMonitoring()` immediately before its own `return`, this one change covers every exit path
  without needing separate per-return reset logic; (2) `writeSidecar()` now captures an explicit
  exit-code marker and warns via `log()` on failure instead of silently swallowing it (the shell
  command itself still always exits 0 — the marker echo is unconditional — so the monitoring
  fail-open rule holds); (3) `write-sequence` now pushes a matching event.
- Updated `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`'s Implementation Notes: its
  `create-tickets` half stays open (deliberately not closed by this fix) — the two historical runs'
  rows can't be retroactively repaired, and AC2 needs a genuinely new post-fix run to confirm.

## Test Summary

- New `tests/tools/test_create_tickets_sidecar_reset_and_failure_visibility.py` — 7 tests, all
  confirmed to fail against the pre-fix source (`git stash` of just `create-tickets.js`, 6 of 7
  failed; the 7th — exit-path coverage — was already true pre-fix and correctly unaffected), then
  confirmed to pass after restoring the fix.
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — 1 adjacency-pin literal updated
  to match the new `const seqResult = await agent(` assignment (mechanical consequence of the
  write-sequence pushEvent fix, not a logic change).
- `node --check .claude/workflows/create-tickets.js` — exit 0.
- Regression check: `test_epic_create_tickets_sidecar_orchestrator.py`,
  `test_step0_ts_orchestrator.py`, `test_workflow_meta_conformance.py`, `test_record_events.py`,
  `test_retrieval_event_wrapper_single_source.py` — all pass (77 passed, 1 xfailed).
- AC4: bare `pytest tests/tools/ -m "not slow and not extra_slow"`, run from the worktree — 3180
  passed, 25 skipped, 28 deselected, 1 xfailed, 0 failed.

## Files Changed

- `.claude/workflows/create-tickets.js` — `writeMonitoring()` clears the sidecar as Step 0;
  `writeSidecar()` surfaces failures via `log()` instead of swallowing them; `write-sequence` now
  pushes a matching event.
- `tests/tools/test_create_tickets_sidecar_reset_and_failure_visibility.py` — new file, 7 tests.
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — 1 adjacency-pin literal updated.
- `tickets/todos/TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION.md` — Implementation Notes
  updated with the outcome; stays in `tickets/todos/`, `create-tickets` half still open.
- `agent-monitoring/retro/RETRO-2026-W39.md` — regenerated (this ticket touches workflow prompts).
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`); no manual edits.

## Completion Summary

All 4 acceptance criteria met. Anomaly 1 (09-13) confirmed as the known concurrent-session sidecar
class and recorded, not re-solved (unconfirmable beyond that without durable state that no longer
exists). Anomalies 2/3 (09-23) confirmed as one real code defect — silent `writeSidecar()` failure
plus no sidecar reset on any exit path — and fixed by mirroring `implement-ticket.js`'s own
established "Step 0" sidecar-clear pattern exactly, plus making failures visible instead of
silent. A third, independently-confirmed defect (write-sequence's missing event) found and fixed
in the same pass. `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`'s `create-tickets` half
deliberately stays open pending a genuinely new post-fix run. No known material gap left unstated.

**Addendum, same session (agent-working-design review, found immediately after this ticket
closed): the AC3 claim above was not actually met.** The "Step 0" sidecar-clear this ticket added
only emptied the shared `.claude/current_run` file — `tools/agent-monitoring/post_tool_hook.py`
reads exclusively the per-session-scoped `.claude/current_run.<session_id>` file whenever the hook
payload carries a `session_id` (always, for real hooks; `TCK-20260824-SIDECAR-CROSS-SESSION-
SCOPE`'s own deliberate no-fallback rule). The fix mirrored `implement-ticket.js`'s own
established "Step 0" pattern faithfully — but that precedent carried the identical, previously
unverified defect. So anomaly 3's 4-hour tail was **not** actually fixed by `d1ad0008f`; the real
fix (a shared `clearSidecar()` helper that dual-writes both files, wired into all three workflows)
is delivered by `TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE`. See that ticket for the
real fix, its behavioural (not just text-pin) proof, and the correction to the write-sequence
comment's own "permanently orphaned" claim above (accurate only when no epic is linked — when one
is, write-sequence's rows silently counted into Link's own event instead, since the two phases
shared a seq before this ticket's pushEvent fix separated them).
