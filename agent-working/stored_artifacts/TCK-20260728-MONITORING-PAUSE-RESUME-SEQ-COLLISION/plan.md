---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
artifact_type: plan
tags: [agent-monitoring, data-quality, root-cause, bug]
---

# Implementation Plan — TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION

## Summary

Candidate 1 (max-seq continuation) from investigation.md is implemented as a single computed
`seqOffset` value: a new pure Python function `compute_seq_offset(run_id, events)` in a new module
`tools/agent-monitoring/seq_offset.py` (mirroring `scope_ticket_relocate.py`'s
lookup-function-plus-`MARKER:`-CLI shape exactly) returns the max prior `seq` already recorded for
a `run_id` in `agent-monitoring/events.jsonl` (0 if none). `.claude/workflows/implement-ticket.js`
calls this once, at Scope-phase resume (the only point `ticketId` is known before any other
`seq`-producing code runs), via a new `resolveSeqOffset()` orchestrator helper mirroring
`resolveScopeTicketLocation()`. The resulting `seqOffset` is threaded into the Scope-phase resume
sidecar write (replacing the hardcoded `'seq': 1` literal) and into `pushEvent`'s and all 10
`writeSidecar(...)` call sites' `seq` expression — every one of these 11 sites uses the textually
identical substring `events.length + 1,`, confirmed by direct grep (exactly 11 matches, no
collateral matches), so one `replace_all` correctly updates all of them in a single mechanical
step. `seqOffset` defaults to `0` on the brand-new-ticket branch, so non-resumed runs (the
overwhelming majority) are provably unaffected. A second, independent new function,
`compute_multi_invocation_collision_report(events)` in `tools/agent-monitoring/validate.py`,
detects the historical signature of this bug (`run_id`s with more than one `phase="Scope", seq=1`
event) as an automated regression detector. `docs/agent-monitoring/schema.md`'s "How tool calls
are attributed to agent events" section gets a new paragraph documenting this third mechanism
alongside the two `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` already documented there.
Two existing tests in `tests/tools/test_current_run_sidecar_orchestrator.py` that assert the exact
literal/expression this plan changes are updated in the same steps that change them, never left
broken.

**Open questions resolved by this plan** (both were carried from investigation.md as
Plan-phase decisions, per this ticket's own Assumptions/Open Questions and Out of Scope sections):

1. **`implement-epic.js` exposure** — confirmed NOT exposed to this specific mechanism, by direct
   read (this session, not assumed): `implement-epic.js` never writes a `.claude/current_run`
   sidecar (grep confirms zero occurrences of `current_run`/`writeSidecar` in that file), so
   `tools.jsonl` never gets tagged with any of its `seq` values in the first place — the bug this
   ticket fixes is specifically the corruption of `tool_call_count`/`cost_proxy_score` via
   `tools.jsonl`'s `(run_id, seq)` grouping, and that grouping mechanism is structurally absent for
   `implement-epic.js` (confirms `docs/agent-monitoring/schema.md:206`'s existing claim: "Neither
   `create-tickets` nor `implement-epic` registers a `.claude/current_run` sidecar per agent
   call"). `implement-epic.js` does independently hardcode small `seq` values into
   `record_events.py --data` calls (lines 176, 202, 265: `"seq":1`, `"seq":1`, `seq: i + 1`) as
   part of `events.jsonl`'s own per-record shape, and a paused/resumed epic run could in principle
   produce duplicate `(run_id, seq)` rows in `events.jsonl` alone — but with no sidecar-driven
   `tools.jsonl` attribution to alias, there is no `tool_call_count`/`cost_proxy_score` corruption
   possible, which is this ticket's actual bug. Scoped as **Step 1: verification-only, no code
   change** — the finding is recorded in the ticket's Implementation Notes, not implemented as a
   fix (a hypothetical `implement-epic.js` `events.jsonl`-only duplicate-`seq` issue, if one
   exists, is a different, narrower concern than this ticket's scope and would need its own
   ticket).
2. **Where `seqOffset`'s lookup function lives** — a named, importable, unit-testable function
   (`compute_seq_offset` in a new dedicated module `tools/agent-monitoring/seq_offset.py`), not an
   inline one-liner. This mirrors `resolveScopeTicketLocation()` / `scope_ticket_relocate.py`'s
   existing precedent exactly (same MARKER-prefixed-JSON-over-`bash()` calling convention, same
   dedicated-test-file convention — `scope_ticket_relocate.py` has its own
   `tests/tools/test_scope_orphan_fix.py`, confirmed by direct check), and satisfies this ticket's
   AC that the lookup needs its own unit tests.

**Refinement note on test_plan.md's example numbers**: test_plan.md's illustrative test description
("assert it returns 7 (not 1) as the next seq... must return 1... for no prior history") describes
lookup semantics in terms of "next seq to use." This plan instead defines
`compute_seq_offset()` to return the **max prior seq** (0 default), consumed as `seqOffset` in JS
expressions shaped `events.length + 1 + seqOffset` — this is the naming and semantics
investigation.md itself already settled on ("`seqOffset` is `0` on the brand-new-ticket branch...
hardcoded `'seq': 1` literal... would need to become `seqOffset + 1`"), and keeps the Python
function's contract a direct, obvious mirror of the JS variable it feeds. Concretely: for a fixture
with `seq` values 1-6 for one `run_id`, `compute_seq_offset()` must return `6` (not `7`); for a
`run_id` with no prior history, it must return `0` (not `1`). This is a naming refinement only —
the underlying behavior test_plan.md's AC #2 requires (resumed session continues past prior max,
non-resumed session unaffected) is identical either way.

## Steps

### Step 1 — Verify `implement-epic.js` has no analogous sidecar/tool-attribution exposure
**Files:** None changed. Read-only verification against `.claude/workflows/implement-epic.js`.
**Change:** No code change. Confirm (already done once during planning; implementer must
independently re-confirm before Implement claims completion) that
`grep -n "writeSidecar\|current_run\|events.length + 1" .claude/workflows/implement-epic.js`
returns no matches for a per-child-call sidecar write. Record the finding verbatim in this
ticket's `## Implementation Notes` section: that `implement-epic.js` cannot exhibit this ticket's
specific bug (tool_call_count/cost_proxy_score corruption via `tools.jsonl` `(run_id, seq)`
aliasing) because it never writes the `.claude/current_run` sidecar that mechanism depends on,
closing the ticket's "not assumed either way" open question with a direct-evidence answer rather
than an assumption.
**Do NOT touch:** `.claude/workflows/implement-epic.js` itself — this step is verification-only.
Do not add a fix, an offset, or a comment to that file. If the grep unexpectedly finds a sidecar
write (contradicting this plan's finding), STOP and flag to the human — do not silently expand
scope to fix it under this ticket.
**Verify:** No automated test (documentation-only finding). Manual confirmation the grep above
returns zero matches, and that the finding is written into Implementation Notes.

### Step 2 — Add `compute_seq_offset()` lookup function and its dedicated test file
**Files:** `tools/agent-monitoring/seq_offset.py` (new), `tests/tools/test_seq_offset.py` (new)
**Change:** Create `tools/agent-monitoring/seq_offset.py`, mirroring
`tools/agent-monitoring/scope_ticket_relocate.py`'s shape exactly:
- `compute_seq_offset(run_id: str, events: list) -> int` — pure function, no file I/O. Scans
  `events` (list of dicts, `events.jsonl`-shaped) for records where `e.get("run_id") == run_id`,
  tracks the max `e.get("seq")` among those where `seq` is an `int`, returns that max (or `0` if no
  matching records exist). Must not mutate the input list (mirrors
  `compute_tool_count_drift_report`'s existing read-only convention in `validate.py`).
- A small `_load_events(path)` helper reading `agent-monitoring/events.jsonl` line-by-line JSON
  (mirror `validate.py`'s `load_jsonl`, or import it directly from `validate.py` if that avoids
  duplicating the same ~10-line function — prefer import over duplication).
- `if __name__ == "__main__":` entrypoint: reads `run_id` from `sys.argv[1]`, calls
  `compute_seq_offset(run_id, _load_events())`, prints `"MARKER:" + json.dumps(offset)` — identical
  calling convention to `scope_ticket_relocate.py`'s own `MARKER:`-prefixed stdout protocol, so the
  JS side can reuse the exact same `markerIndex`/`JSON.parse` parsing pattern
  `resolveScopeTicketLocation()` already uses.

Create `tests/tools/test_seq_offset.py` (new dedicated file, mirroring
`tests/tools/test_scope_orphan_fix.py`'s existing precedent of one test file per
`tools/agent-monitoring/*.py` orchestrator-helper module):
- `test_compute_seq_offset_continues_past_prior_session_max_seq` — fixture: list of dicts with
  `run_id="TCK-FAKE"` and `seq` values `1..6` (mirrors the ticket's own
  `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` table). Assert `compute_seq_offset("TCK-FAKE", fixture)
  == 6`.
- `test_compute_seq_offset_returns_zero_for_run_id_with_no_prior_history` — empty list, and
  separately a list containing only unrelated `run_id`s. Assert `compute_seq_offset("TCK-NEW", ...)
  == 0` in both cases (never `None`, never an error) — the single highest-value case, since this is
  the overwhelmingly common non-resume path.
- `test_compute_seq_offset_ignores_other_run_ids` — fixture mixing `run_id="TCK-FAKE"` (seq 1-3)
  and `run_id="TCK-OTHER"` (seq 1-9). Assert `compute_seq_offset("TCK-FAKE", fixture) == 3` (not 9)
  — proves the lookup is correctly scoped per-`run_id`, not global.
- `test_compute_seq_offset_is_read_only` — call with a fixture list, assert the list (and its dict
  elements) are unchanged after the call (`==` comparison against a `copy.deepcopy` taken before the
  call).
**Do NOT touch:** `validate.py`'s existing functions (`compute_drift_report`,
`compute_tool_count_drift_report`) — this is a new sibling module, not an addition to `validate.py`
directly (that comes in Step 5, for a different function). Do not wire this new module into
`implement-ticket.js` yet — that is Step 3.
**Verify:** `pytest tests/tools/test_seq_offset.py -v` — all new tests pass.

### Step 3 — Wire `seqOffset` into `implement-ticket.js`'s resume path
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Three coordinated edits, all in this one file:
1. Immediately above the existing `if (ticketId) { ... } else { ... }` block at line 44 (after the
   existing comment block explaining Scope-phase net-new sidecar coverage, before the block
   itself), add a new `resolveSeqOffset` helper:
   ```js
   const resolveSeqOffset = async (id) => {
     const out = await bash(`python3 tools/agent-monitoring/seq_offset.py "${id}" 2>/dev/null`)
     const markerIndex = (out || '').indexOf('MARKER:')
     if (markerIndex === -1) return 0
     try {
       const val = JSON.parse(out.slice(markerIndex + 'MARKER:'.length).trim())
       return typeof val === 'number' && Number.isInteger(val) ? val : 0
     } catch (e) { return 0 }
   }
   ```
   This mirrors `resolveScopeTicketLocation()`'s exact shape (same `MARKER:` parsing, same
   fail-open-to-safe-default pattern — `0`, not `null`/`NaN`, per the investigation's explicit
   anti-drift hazard).
2. Change the `if (ticketId) { ... } else { ... }` block itself:
   ```js
   let seqOffset = 0
   if (ticketId) {
     seqOffset = await resolveSeqOffset(ticketId)
     await bash(
       `python3 -c "
   import json, sys
   open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))
   " "${ticketId}" "${seqOffset + 1}" 2>/dev/null || true`
     )
   } else {
     await bash(`printf '{}' > .claude/current_run 2>/dev/null || true`)
   }
   ```
   The `else` branch is unchanged (`seqOffset` stays at its `let`-initialized `0`). Note the
   `'seq': 1` literal becomes `'seq': int(sys.argv[2])`, and `seqOffset + 1` is passed as a new
   argv element — this preserves the "argv-quoted, not JSON-embedded" convention
   `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` guards for
   `writeSidecar` itself (this is a *different* python3 -c call, the Scope-phase inline one, but
   should follow the same convention for consistency).
3. Update `pushEvent`'s `seq` expression and all 10 `writeSidecar(...)` call sites: run a single
   `replace_all` of the exact substring `events.length + 1,` → `events.length + 1 + seqOffset,`
   across the file. Confirmed by direct grep (this planning session) that this substring occurs
   **exactly 11 times** in the file — once inside `pushEvent`'s object literal (line 209:
   `seq: events.length + 1,`) and once at each of the 10 `writeSidecar(...)` call sites (lines 427,
   468, 549, 618, 734, 795, 944, 1036, 1099, 1153) — with no other coincidental match. After the
   edit, re-run the same grep for `events.length + 1,` (should now find 0 matches) and for
   `events.length + 1 + seqOffset,` (should find exactly 11) as a mechanical correctness check
   before moving to Step 4.
**Do NOT touch:** `writeSidecar`'s own function signature/body (`const writeSidecar = async (seq,
phase, agent) => {...}` at line 229) — it still receives a single pre-computed `seq` value as its
first argument; only the *expression passed at each call site* changes, not the helper itself.
Do NOT touch `writeMonitoring`'s Step-0-sidecar-clear-first ordering (lines 285-304) — unrelated,
already-closed fix from the sibling ticket. Do NOT touch `resolveScopeTicketLocation()` itself
(lines 257-263) — this step adds a new sibling helper, not a modification to that one.
**Verify:** No dedicated new test in this step (covered by Step 4's updated assertions and Step
2's already-passing unit tests) — but confirm `node --check .claude/workflows/implement-ticket.js`
(or equivalent syntax check available in this repo's tooling) passes, since this step edits 11+
call sites by mechanical substitution and a stray syntax error is the main risk.

### Step 4 — Update existing tests that assert the old `seq` expression/literal
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py`
**Change:**
1. `test_sidecar_bash_write_precedes_each_covered_agent_call` (currently lines 93-99): update every
   string in `_COVERED_SITE_ADJACENCY` (lines 49-60) from
   `"  await writeSidecar(events.length + 1, '<Phase>', '<agent>')\n..."` to
   `"  await writeSidecar(events.length + 1 + seqOffset, '<Phase>', '<agent>')\n..."` (10 strings,
   preserving each site's existing leading-whitespace/indentation and trailing `await agent(`
   continuation exactly as today — only the `events.length + 1` substring inside each changes).
   Update the regex assertion (line 99) from
   `r"await writeSidecar\(events\.length \+ 1, '[^']+', '[^']+'\)"` to
   `r"await writeSidecar\(events\.length \+ 1 \+ seqOffset, '[^']+', '[^']+'\)"`, keeping the
   `== 10` count assertion unchanged (Step 3 adds no new call sites, only changes the expression at
   the existing 10).
2. `test_scope_phase_has_sidecar_coverage` (currently lines 147-169): update the two assertions
   that pin the old shape:
   - Line 161's literal string assertion changes from
     `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'}))"`
     to
     `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))"`.
   - Line 162's `'"${ticketId}" 2>/dev/null || true'` assertion changes to
     `'"${ticketId}" "${seqOffset + 1}" 2>/dev/null || true'`.
   - Add a new assertion: `"resolveSeqOffset(" in pre_scope_region` and
     `"seqOffset = await resolveSeqOffset(ticketId)" in pre_scope_region` — proves the new helper is
     actually invoked at this call site, not just defined elsewhere unused.
   - The `else`-branch assertion (line 163, `"printf '{}' > .claude/current_run..."`) is unchanged.
3. Add one new test, `test_new_ticket_branch_seq_offset_is_zero_not_null` (place near
   `test_scope_phase_has_sidecar_coverage`, same static-source-parsing style): asserts
   `"let seqOffset = 0" in source` (the initialization, before the `if (ticketId)` block) and that
   the substring `resolveSeqOffset(` appears **inside** the `if (ticketId) { ... }` block only
   (i.e., does not appear in the `pre_scope_region` slice up to `else`'s body / does not appear a
   second time in the `else` branch text) — proves the brand-new-ticket branch leaves `seqOffset` at
   its safe `0` default rather than calling the lookup for a `ticketId` that doesn't exist yet.
**Do NOT touch:** `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`,
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`,
`test_record_events_required_fields_unchanged`, `test_finalize_call_site_still_registers_sidecar`,
`test_writeMonitoring_call_has_no_preceding_sidecar_write`,
`test_writeMonitoring_step0_sidecar_clear_precedes_other_steps`,
`test_no_step_0b_agent_prompt_sidecar_text_remains` — none of these assert anything Step 3 changes;
leave them exactly as-is as regression proof the fix is additive, not a rewrite.
**Verify:** `pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` — full 27(+1 new)-test
suite green.

### Step 5 — Add `compute_multi_invocation_collision_report()` to `validate.py`
**Files:** `tools/agent-monitoring/validate.py`, `tests/tools/test_validate_agent_monitoring.py`
**Change:** Add a new function to `validate.py`, placed directly after
`compute_tool_count_drift_report` (after line 167), following its exact docstring/shape convention
(pure function, `list -> str`, never gates, never mutates input):
```python
def compute_multi_invocation_collision_report(events: list) -> str:
    """Read-only detector for TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION's specific
    mechanism: a run_id with more than one phase="Scope", seq=1 event is the empirical signature
    of a resumed session whose seq numbering restarted at 1 and aliased onto a prior session's
    (run_id, seq) tools.jsonl buckets (the exact signature this ticket's own investigation used to
    find the 8 affected run_ids in the live corpus). Distinct from
    compute_tool_count_drift_report's recorded-vs-actual mismatch detection: that function detects
    THAT a count disagrees; this one flags the specific multi-invocation cause."""
    scope_seq1_counts = Counter()
    for e in events:
        if e.get("phase") == "Scope" and e.get("seq") == 1 and e.get("run_id"):
            scope_seq1_counts[e["run_id"]] += 1

    collided = {run_id: count for run_id, count in scope_seq1_counts.items() if count > 1}

    lines = ["--- Multi-Invocation Seq Collision Report ---", ""]
    lines.append(
        f"run_ids with more than one Scope/seq=1 event (resume-collision candidates): {len(collided)}"
    )
    if collided:
        lines.append("")
        for run_id, count in sorted(collided.items()):
            lines.append(f"  {run_id}: {count} Scope/seq=1 events")
    return "\n".join(lines)
```
Wire into `main()`: immediately after the existing
`print(compute_tool_count_drift_report(events, tools))` line (line 249), add
`print()` then `print(compute_multi_invocation_collision_report(events))` — purely additive
output, does not change `main()`'s exit-code contract (errors still gate exit 1; this new report,
like the two existing drift reports, never gates).

Add to `tests/tools/test_validate_agent_monitoring.py`, alongside the existing
`compute_tool_count_drift_report` tests, same no-file-I/O fixture-construction style:
- `test_multi_invocation_collision_report_detects_duplicate_scope_seq1` — fixture: two dicts with
  `run_id="TCK-COLLIDED", phase="Scope", seq=1` (from different fake sessions), plus one dict with
  `run_id="TCK-NORMAL", phase="Scope", seq=1`. Assert `"TCK-COLLIDED"` appears in the report output
  and `"TCK-NORMAL"` does not (negative case — no false positive on an ordinary single-session run
  that happens to also have a Scope/seq=1 event, which is every normal run).
- `test_multi_invocation_collision_report_is_read_only` — mirrors
  `test_tool_count_drift_report_is_read_only`'s existing pattern exactly: call with a fixture list,
  assert it is unchanged (`==` against a pre-call deep copy) afterward.
**Do NOT touch:** `compute_tool_count_drift_report`'s existing signature, return shape, or
docstring — this is a new sibling function, not a modification. Do NOT touch `compute_drift_report`
(the unrelated vocabulary/null-field drift report) or any of the four existing
`test_tool_count_drift_report_*` tests.
**Verify:** `pytest tests/tools/test_validate_agent_monitoring.py -v` — full suite green including
the 2 new tests.

### Step 6 — Document the third mechanism in `docs/agent-monitoring/schema.md`
**Files:** `docs/agent-monitoring/schema.md`, `tests/tools/test_current_run_sidecar_orchestrator.py`
**Change:** In the "How tool calls are attributed to agent events" section, insert a new paragraph
immediately after the existing paragraph ending "...rather than attributed to the not-yet-known new
ticket)." (line 263) and before the `writeMonitoring` paragraph (line 265). New paragraph content
(adapt wording to match the surrounding section's voice, must include the ticket ID marker and the
mechanism name for the new doc-guard test below):
> A third mechanism, `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`: when a ticket's run is
> paused mid-pipeline and resumed later as a separate session sharing the same `run_id`, the
> resumed session's own `seq` numbering (both `pushEvent`'s and every `writeSidecar` call site's
> `events.length + 1` expression, and the Scope-phase resume branch's own sidecar write) would
> previously restart at `1`, silently aliasing the new session's tool-call attribution onto
> whatever `(run_id, seq)` buckets the pre-pause session already wrote in `tools.jsonl`. Fixed by a
> `seqOffset` computed once at Scope-phase resume — `tools/agent-monitoring/seq_offset.py`'s
> `compute_seq_offset(run_id, events)` looks up the max `seq` this `run_id` already has in
> `agent-monitoring/events.jsonl` (`0` for a brand-new ticket) — added into every `seq`-producing
> expression so a resumed session's numbering continues past the prior session's instead of
> restarting. `tools/agent-monitoring/validate.py`'s `compute_multi_invocation_collision_report()`
> detects this mechanism's historical signature (a `run_id` with more than one `phase="Scope",
> seq=1` event) so a future recurrence surfaces automatically.

Add one new test to `tests/tools/test_current_run_sidecar_orchestrator.py` (same module already
owns this section's doc-guard tests — extends existing scope, no new module warranted):
- `test_schema_doc_documents_pause_resume_seq_collision_fix` — asserts
  `"TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION" in doc`,
  `"compute_seq_offset" in doc` or `"seqOffset" in doc`, and
  `"compute_multi_invocation_collision_report" in doc`, scoped to the "How tool calls are
  attributed to agent events" section region (mirror
  `test_schema_doc_documents_tools_jsonl_phase_agent_fields`'s existing pattern of slicing the doc
  between two known section-heading markers before asserting, rather than asserting against the
  whole file).
**Do NOT touch:** Any other section of `schema.md` (the `tools.jsonl` fields table, Join Example,
Known Limitations, etc.) — this is one new paragraph in one existing section. Do NOT touch
`test_schema_doc_no_longer_describes_agent_self_report_mechanism` or
`test_schema_doc_documents_tools_jsonl_phase_agent_fields` — unrelated existing doc-guard tests,
must stay passing unmodified.
**Verify:** `pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` (re-run full suite;
confirms Step 4's and Step 6's test additions both pass together).

## Scope Guards

- Do not implement Candidate 2 (unique per-invocation token replacing int `seq`). Do not touch
  `record_events.py`'s `REQUIRED` set, `tools.jsonl`'s documented field types, or
  `compute_tool_count_drift_report`'s existing `(run_id, seq)` grouping key shape.
  `test_record_events_required_fields_unchanged` must still pass unmodified as proof.
- Do not touch `writeMonitoring`'s Step-0-sidecar-clear-first ordering (lines 285-304) — that is
  `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`'s already-closed, unrelated fix.
- Do not change `writeSidecar`'s own function signature or its argv-quoting convention (lines
  229-236) — only the expression passed as its first argument at each call site changes.
- Do not implement a fix in `implement-epic.js` — Step 1 is verification-only; if it somehow
  surfaces a real exposure, that is new-ticket territory, not this one's.
- Do not backfill or correct any historical `tool_call_count`/`cost_proxy_score` values for the 8
  already-collided `run_id`s named in the ticket, or for
  `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` specifically. Prevention-only, append-only precedent.
- Do not touch `tools/agent-monitoring/cost_proxy.py`'s weighting formula — out of scope, unaffected
  in principle.
- Do not fold in the wall-clock `duration_s` pause/resume contamination fix
  (`docs/plans/idea_agent_monitoring_active_duration.md`) — separate ticket, separate field,
  separate consumer.
- Do not modify `resolveScopeTicketLocation()` itself or `scope_ticket_relocate.py` — Step 3 adds a
  new sibling helper (`resolveSeqOffset`) alongside it, not a change to the existing one.
- Do not widen `compute_seq_offset()`'s scope to read `tools.jsonl` as a fallback source —
  investigation.md explicitly identifies `events.jsonl` as the sole correct/authoritative source for
  this lookup; a `tools.jsonl` fallback was named only as a hypothetical future enhancement, not part
  of this ticket's scope.

## Dependency Map

- Step 1 (verify `implement-epic.js`) — independent, no dependency on any other step. Can run first
  or in parallel with Step 2.
- Step 2 (new `seq_offset.py` module + tests) — independent; must complete before Step 3 (Step 3
  imports/calls the module Step 2 creates).
- Step 3 (wire into `implement-ticket.js`) — depends on Step 2. Must complete before Step 4 (Step 4
  updates tests that assert Step 3's exact new source text).
- Step 4 (update existing sidecar-orchestrator tests) — depends on Step 3.
- Step 5 (new `validate.py` collision-report function + tests) — independent of Steps 2-4 (different
  file, no shared symbols). Can run any time after Step 1, including in parallel with Steps 2-4.
- Step 6 (schema.md doc update + doc-guard test) — depends on Step 3 and Step 5 (the doc paragraph
  describes both the `seqOffset` mechanism from Step 3 and the `compute_multi_invocation_collision_report`
  function from Step 5 by name). Must run last.

Suggested execution order: 1 → 2 → 3 → 4 → 5 → 6 (5 could move earlier/parallel but sequential is
simpler to verify step-by-step per this ticket's narrow-step discipline).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause mechanism confirmed and documented precisely | Already satisfied by investigation.md (pre-Plan); Step 6 documents the fix side in schema.md | `test_schema_doc_documents_pause_resume_seq_collision_fix` (Step 6) |
| Resumed sessions can no longer write into a `(run_id, seq)` bucket a prior session already populated, verified against a `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`-shaped reproduction | Steps 2, 3 | `test_compute_seq_offset_continues_past_prior_session_max_seq`, `test_compute_seq_offset_returns_zero_for_run_id_with_no_prior_history`, `test_compute_seq_offset_ignores_other_run_ids` (Step 2); `test_scope_phase_has_sidecar_coverage`, `test_sidecar_bash_write_precedes_each_covered_agent_call`, `test_new_ticket_branch_seq_offset_is_zero_not_null` (Step 4) |
| `compute_tool_count_drift_report()` (or a sibling) can detect this mechanism, distinct from the two the sibling ticket already covers | Step 5 | `test_multi_invocation_collision_report_detects_duplicate_scope_seq1`, `test_multi_invocation_collision_report_is_read_only` |
| `docs/agent-monitoring/schema.md` updated with the third mechanism and its fix | Step 6 | `test_schema_doc_documents_pause_resume_seq_collision_fix` |
| Existing `test_current_run_sidecar_orchestrator.py` and `test_validate_agent_monitoring.py` suites still pass; new tests cover the fix and its detection | Steps 2, 3, 4, 5, 6 (collectively) | Full scoped pytest command below |
| (Ticket Scope item) `implement-epic.js` exposure question resolved | Step 1 | Manual verification (documented in Implementation Notes; no test — no code changed) |

Final verification command (from test_plan.md, run after all 6 steps):
```
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_seq_offset.py tests/tools/test_scope_orphan_fix.py -v
```
(`test_seq_offset.py` added to test_plan.md's original command since Step 2 creates it as a new
file; `test_scope_orphan_fix.py` added as a cheap regression guard since Step 3 adds a new sibling
helper next to `resolveScopeTicketLocation()` in the same file region.)

## Anti-Drift Notes

- **The 11-site `events.length + 1,` replacement is exact and mechanical** — confirmed by direct
  grep during planning (11 matches, no collateral hits). If Step 3's implementer finds a different
  count when they run the same grep (e.g., due to intervening changes on this branch), STOP and
  re-verify before proceeding — a mismatched count means either a stale assumption or an
  unexpected structural change to the file that this plan did not anticipate.
- **`seqOffset` must never become `NaN`/`null`/`undefined`** on the non-resume branch — this is the
  single highest-blast-radius risk in this ticket, since a broken offset would corrupt `seq` for
  *every* run, not just resumed ones. `let seqOffset = 0` plus `resolveSeqOffset`'s fail-open
  `return 0` (both on JSON-parse failure and on missing `MARKER:` output) are the two guards; Step
  4's new `test_new_ticket_branch_seq_offset_is_zero_not_null` is the regression test for this
  specifically.
- **`compute_seq_offset()`'s return semantics (max prior seq, defaulting to 0) intentionally
  diverge from test_plan.md's illustrative wording** ("returns 7"/"returns 1") — see the Summary's
  refinement note above. This is a deliberate naming choice made at Plan time to keep the Python
  function's contract a direct mirror of the JS `seqOffset` variable it feeds; it does not change
  the underlying behavior the AC requires.
- **Do not let Step 5's new report function drift into gating** — like `compute_drift_report` and
  `compute_tool_count_drift_report`, `compute_multi_invocation_collision_report` must never affect
  `main()`'s exit code (only `errors` — the working_log/no-events checks — gate exit 1). It is
  purely additive `print()` output, same as its two siblings.
- **Historical corrupted data stays uncorrected** — the 8 named `run_id`s (and
  `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` specifically) keep their wrong
  `tool_call_count`/`cost_proxy_score` values forever, per this ticket's own Out of Scope section
  and the sibling ticket's established append-only precedent. `compute_multi_invocation_collision_report`
  will correctly flag these 8 in its output after this fix lands — that is expected, not a bug to
  chase; the report's job is prevention/detection going forward, not historical cleanup.

## Deviations

- **Step 3/4's collateral scope was one test file too narrow.** This plan's Step 3 anti-drift note
  confirmed the `events.length + 1,` → `events.length + 1 + seqOffset,` `replace_all` was exact
  (11 matches in `implement-ticket.js` itself), and Step 4 updated the one test file this plan
  named, `tests/tools/test_current_run_sidecar_orchestrator.py`, whose own `_COVERED_SITE_ADJACENCY`
  list independently pins the same substring. What this plan's grep did not check: whether any
  *other* test file also carries its own independent copy of that substring. It does —
  `tests/tools/test_step0_ts_orchestrator.py` (built for the earlier, unrelated
  TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH ticket) has its own `_IMPLEMENT_TICKET_ADJACENCY` list
  with 9 of the same `writeSidecar(events.length + 1, ...)` adjacency strings, layered on top of
  its own `captureTs()` assertions. Implement discovered this via
  `test_ts_capture_bash_precedes_each_covered_agent_call` failing after Step 3's edit, then ran a
  repo-wide grep for `events.length + 1` across `tests/`, `.claude/`, `tools/`, `docs/` to confirm
  no further collateral existed beyond this one file (two unrelated workflow files,
  `create-tickets.js` and `simq-audit.js`, use the same expression shape internally but are
  out-of-scope per this ticket's own Scope section, which names only `implement-ticket.js`).
  Fixed by applying the identical mechanical substitution to
  `test_step0_ts_orchestrator.py`'s 9 strings — same fix shape as Step 4, just a second file.
  No architectural or scope conflict; a plan-time grep gap, corrected in Implement per this ticket's
  own "never silently deviate" rule.
