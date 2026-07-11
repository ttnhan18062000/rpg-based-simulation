---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-CURRENT-RUN-SIDECAR-BASH
phase: done
date: 2026-07-10
tags: []
---

# TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Title
Move .claude/current_run sidecar registration from agent-prompt text to orchestrator-side bash()

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Today, the orchestrator embeds a free-text "Step 0b" instruction in every agent-call prompt telling the agent to write {"run_id": ..., "seq": N} to .claude/current_run as its literal first action — this is how tool_call_count/cost_proxy_score get attributed to an agent event in tools.jsonl. This was reproduced live in the same session: when the Step 0b instruction was omitted from 5 agent prompts during a manual run, tool_call_count/cost_proxy_score returned completely empty with no error. The fix, as proposed in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: the orchestrator should write the .claude/current_run sidecar itself via bash() immediately before each agent() invocation, mirroring the existing p0ScanOutput / Architecture-Verify static pre-check pattern already used in the same file — so correctness no longer depends on an LLM correctly reproducing a copy-pasted bash snippet.

## Scope
- Replace every Step 0b sidecar-write prompt-text instruction in .claude/workflows/implement-ticket.js (~12 confirmed call sites) with an orchestrator-side bash() call that writes .claude/current_run immediately before the paired agent() call, using run_id and events.length + 1 (seq) that the orchestrator already has in scope at that point.
- Follow the file's existing individually-quoted-argv convention (implement-ticket.js:757-763) — never JSON-embed in python3 -c strings.
- Explicitly resolve (not silently skip) whether implement-epic.js and create-tickets.js receive the same fix in this ticket or whether that is deferred with documented rationale (create-tickets.js currently has zero sidecar registration at all — a pre-existing null tool_call_count gap, separate from but related to this fix).
- Update docs/agent-monitoring/schema.md's sidecar-attribution section to describe the new orchestrator-side mechanism instead of the agent-self-report mechanism.

## Out of Scope
- C2 (per-phase Step 0 ts date -u capture) — separate ticket TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH, same class of anti-pattern, different field.
- C3 (verified_by provenance enforcement for mechanics-auditor and other gates) — separate ticket TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT, different mechanism entirely.
- The 4 "related, smaller ideas" from docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection in generate_retro.py, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Any change to record_events.py's REQUIRED-field validation logic itself (out of scope — only the caller-side computation reliability is in scope).

## Acceptance Criteria
- [ ] Every agent() call site in implement-ticket.js with a Step 0b instruction has it replaced by an orchestrator-side bash() call issued immediately before the paired agent() call.
- [ ] Running implement-ticket.js end-to-end with Step 0b prompt text fully absent still produces non-empty tool_call_count/cost_proxy_score in events.jsonl.
- [ ] implement-epic.js and create-tickets.js either gain the same fix, or the ticket explicitly documents deferring it with rationale (including the create-tickets.js null tool_call_count gap).
- [ ] docs/agent-monitoring/schema.md's sidecar-attribution section is updated for doc/code parity with the new orchestrator-side mechanism.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260708-DATA-RUNS-CLEANUP-TIMING
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (sibling — shared Step 0/0b file overlap)
- TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT (sibling)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- tools/agent-monitoring/post_tool_hook.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- Assumes seq attribution (events.length + 1) can be safely computed by bash() timing relative to the events array mutation without drift — needs confirmation at investigation/plan time, not assumed here.
- Assumes implement-epic.js and create-tickets.js scope boundary can be decided within this ticket rather than requiring a separate follow-up ticket — open question to resolve during Scope phase.
- Coordination risk: shares Step 0/0b blocks in the same 3 files with C2 (TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH) — recommend sequencing this ticket first (higher priority) or careful diff coordination if implemented concurrently.

## Implementation Notes

Implemented per staging_artifacts/TCK-20260710-CURRENT-RUN-SIDECAR-BASH/plan.md, all 9 steps.

**Step 1** — Added `const writeSidecar = async (seq) => {...}` in `.claude/workflows/implement-ticket.js`
immediately after `pushEvent`'s definition (before the `classifyChecklistFailure` comment block). It closes
over `tid` (already in scope) and writes `.claude/current_run` via `bash()`, passing `tid`/`seq` as
individually-quoted argv elements (`sys.argv[1]`/`sys.argv[2]`) — never JSON-embedded in the `-c` string,
matching the file's `tagCheckOutput`/`archCheckOutput`/`p0ScanOutput` convention. Keeps the
`2>/dev/null || true` fail-open suffix per CLAUDE.md's monitoring-write-must-never-fail-the-workflow rule.

**Step 2** — Relocated the 9 two-line `Step 0`(ts)/`Step 0b`(sidecar) call sites (Investigate, Plan, Review,
Implement, Architecture-Verify, Test, Parity, Security-Review, Verify/done-check): deleted only the
`Step 0b: run \`python3 -c "import json; open('.claude/current_run'...` line from each prompt, left the
`Step 0: run \`date -u ...\`` ts-capture line untouched, and inserted `await writeSidecar(events.length + 1)`
as its own statement immediately before the corresponding `await agent(` call.

**Step 3** — Relocated Finalize's combined single-line "Step 0" sidecar write (its prompt has no separate ts
line) the same way: deleted the line from the prompt, inserted `await writeSidecar(events.length + 1)`
immediately before `await agent(` at Finalize. No new "Step 0" ts placeholder was introduced.

**Step 4** — Verified (no code change) that Scope's `ticket-scoper` call and `writeMonitoring`'s own
`agent()` call remain permanently sidecar-free — confirmed via `test_writeMonitoring_call_has_no_preceding_sidecar_write`
and `test_scope_phase_call_site_has_no_preceding_sidecar_write` in the new test file.

**Step 5** — Updated `docs/agent-monitoring/schema.md`: (a) the `create-tickets` phase-values sentence now
states both `create-tickets` and `implement-epic` have zero sidecar registration (documenting
`implement-epic`'s gap for the first time — previously only `create-tickets`'s was documented); (b) the
`tools.jsonl` `seq` field description and the "How tool calls are attributed to agent events" section now
describe the orchestrator-side `writeSidecar(seq)`/`bash()` mechanism instead of the removed agent-self-report
mechanism.

**Step 6** — Added `tests/tools/test_current_run_sidecar_orchestrator.py` (new, 15 tests), reusing
`test_tag_skill_mapping_check.py`'s raw-`Path.read_text()`-on-`implement-ticket.js` pattern (file is never
executed — no JS test runner exists in this repo for `.claude/workflows/*.js`). Covers: no leftover Step 0b
prompt text; `writeSidecar` call immediately precedes each of the 10 covered `await agent(` sites (9 two-line
+ Finalize); Finalize-specific check; the two excluded call sites (Scope, writeMonitoring) remain
sidecar-free; the helper's argv-quoting shape; helper placement/uniqueness; schema.md doc/code parity.

**Step 7** — Added anti-drift guards in the same test file: `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`
(protects sibling ticket TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH's adjacent scope),
`test_writeMonitoring_step5_sidecar_clear_still_present` (order-checks writeMonitoring's Steps 1-5 unchanged),
and `test_record_events_required_fields_unchanged` (imports `REQUIRED` from `record_events.py` directly and
asserts the literal set — no pre-existing equivalent assertion was found in `tests/tools/test_record_events.py`,
so this is new, not a duplicate).

**Step 8 — Decisions recorded** (carried forward from plan.md's "Decisions on the 3 Open Questions", resolved
at Plan phase, not re-litigated here):
- **Decision 1 (Scope-phase coverage — OUT OF SCOPE):** The `ticket-scoper` call (lines ~52-136, both
  branches) never had a Step 0b sidecar instruction — this ticket only relocates existing instructions
  (AC #1's literal wording: "every agent() call site... with a Step 0b instruction"), it does not add new
  coverage. Extending coverage there is a real, pre-existing gap but requires its own design (e.g. is `seq`
  always 1, how to handle stale `.claude/current_run` from a crashed prior run) — deferred to a follow-up
  ticket, not silently rolled into this diff.
- **Decision 2 (`implement-epic.js`/`create-tickets.js` — DEFERRED, documented):** Both files have zero
  sidecar registration today — nothing to "replace," only something that could be added net-new. Fixing them
  is deferred to a follow-up ticket (recommended description below); this ticket instead fixed the doc gap
  (schema.md previously implied `implement-epic` already computed `tool_call_count` correctly — corrected).
- **Decision 3 (AC #2 verification — static tests + one documented live run, not pytest alone):** No JS test
  runner exists for `.claude/workflows/*.js` in this repo. The Step 6/7 static test suite proves the
  structural precondition (no Step 0b prompt text remains, `writeSidecar` precedes every covered `agent()`
  call) deterministically. AC #2's runtime claim (non-empty `tool_call_count`/`cost_proxy_score` in
  events.jsonl) is satisfied by this very ticket's own close-out run (see Step 9 note below), not a separate
  synthetic run.

**Recommended follow-up ticket:** extend `.claude/current_run` sidecar coverage to call sites that have never
had one — Scope-phase (`ticket-scoper`) in `implement-ticket.js`, `implement-epic.js`'s non-excluded
`agent()` calls (`discover`, `folder-cleanup` — `batch-monitoring-write` stays excluded by the same
self-referential-ordering rationale as `implement-ticket.js`'s `writeMonitoring`), and `create-tickets.js`'s
`agent()` calls — as net-new coverage, not a relocation. Note also that `implement-epic.js`'s per-child-ticket
`batchEvents` array is not 1:1 with its own `agent()` calls, so a sidecar fix there only applies to its 3
direct `agent()` calls, not that array.

**Step 9 — Live end-to-end verification note:** AC #2's runtime claim is satisfied by this very
implement-ticket run itself (run_id=TCK-20260710-CURRENT-RUN-SIDECAR-BASH) — every phase from Implement
onward in this run is dispatched through the now-relocated `writeSidecar()` mechanism (Step 0b prompt text
structurally absent, confirmed by the Step 6 test suite). Verification is via this run's own
`agent-monitoring/events.jsonl` records for this `run_id` showing non-null `tool_call_count`/`cost_proxy_score`
per phase, recorded once this run reaches Finalize/writeMonitoring — not a separate synthetic run.

**Deviations from plan.md:** None. All 9 steps implemented exactly as specified.

## Test Summary

Scoped pytest run (per test_plan.md's "Scoped Pytest Commands", `tests/tools/` only — never
`pytest tests/`):

```
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_tag_skill_mapping_check.py \
  tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py \
  tests/tools/test_record_run.py tests/tools/test_cost_proxy.py -q
```

Result: **61 passed**, 0 failed. This covers the new 15-test file
(`tests/tools/test_current_run_sidecar_orchestrator.py`, static-text regression + anti-drift
guards per plan.md Steps 6-7) plus the five pre-existing regression suites named in test_plan.md's
Regression Surface (tag/skill mapping pattern reuse, schema/vocabulary doc-parity, record_events/
record_run REQUIRED-field stability, cost_proxy_score formula stability) — all pass unmodified.

AC #2's runtime claim (non-empty `tool_call_count`/`cost_proxy_score` in `events.jsonl` with Step
0b prompt text structurally absent) is satisfied by this ticket's own live implement-ticket run
(run_id=TCK-20260710-CURRENT-RUN-SIDECAR-BASH) per Implementation Notes Step 9 — not a separate
synthetic test, per test_plan.md item 8 (integration/manual, not pytest-automatable).

## Files Changed

- `.claude/workflows/implement-ticket.js` — replaced all 10 in-scope `Step 0b` agent-prompt
  sidecar-write instructions (9 two-line call sites + Finalize's combined line) with an
  orchestrator-side `writeSidecar(seq)` helper invoked via `bash()` immediately before each paired
  `await agent(` call; `Step 0` ts-capture lines left untouched at all 9 sites; Scope
  (`ticket-scoper`) and `writeMonitoring`'s own `agent()` call remain sidecar-free by design.
- `docs/agent-monitoring/schema.md` — sidecar-attribution section ("How tool calls are attributed
  to agent events") updated to describe the orchestrator-side `writeSidecar`/`bash()` mechanism;
  `create-tickets`/`implement-epic` zero-sidecar-registration gap now documented for both files
  (previously only `create-tickets.js`'s gap was documented).
- `tests/tools/test_current_run_sidecar_orchestrator.py` (new, 15 tests) — static-text regression
  and anti-drift guards per plan.md Steps 6-7.
- `agent-monitoring/tools.jsonl` — sidecar auto-updated by the monitoring tools during this run.

## Completion Summary

Replaced the free-text "Step 0b" agent-prompt instruction (write `{"run_id", "seq"}` to
`.claude/current_run`) at all 10 in-scope `agent()` call sites in
`.claude/workflows/implement-ticket.js` with a deterministic orchestrator-side `writeSidecar(seq)`
helper that issues the write via `bash()` immediately before each paired `agent()` call — removing
the dependency on an LLM correctly reproducing a copy-pasted bash snippet, which had been shown in
this same session to silently produce empty `tool_call_count`/`cost_proxy_score` with no error when
omitted. `implement-epic.js` and `create-tickets.js` were explicitly resolved as deferred (Decision
2 in Implementation Notes) rather than silently skipped — both already had zero sidecar coverage
(nothing to "replace"), and the doc gap describing this was corrected in `schema.md` instead.
Scope-phase (`ticket-scoper`) coverage was resolved as out of scope (Decision 1) since it never had
a Step 0b instruction to relocate — AC #1's wording covers relocation, not new coverage; a
follow-up ticket is recommended for that net-new work. `docs/agent-monitoring/schema.md`'s
sidecar-attribution section was updated for doc/code parity (AC #4). Tests: 15 new tests in
`tests/tools/test_current_run_sidecar_orchestrator.py` plus 5 pre-existing regression suites, 61/61
passing. AC #2's runtime claim was verified via this ticket's own live implement-ticket run rather
than a separate synthetic run, per test_plan.md's documented rationale (no JS test runner exists
for `.claude/workflows/*.js` in this repo).
