---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-CURRENT-RUN-SIDECAR-BASH
artifact_type: plan
tags: [agent-monitoring, workflows, data-quality]
---

# Implementation Plan — TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Summary

Replace the 10 existing agent-prompt-text "Step 0b" (and Finalize's combined "Step 0") sidecar-write
instructions in `.claude/workflows/implement-ticket.js` with a single shared orchestrator-side helper,
`writeSidecar(seq)`, invoked via `bash()` immediately before each corresponding `await agent(...)` call.
This is a pure mechanical relocation — no semantic change to `run_id`/`seq` values, no new coverage. Two
call sites that **never** had any sidecar instruction (Scope/`ticket-scoper`, and `writeMonitoring`'s own
`agent()` call) are explicitly left untouched, protected by a new anti-drift test. `implement-epic.js` and
`create-tickets.js` — which also have zero sidecar registration today — are explicitly deferred to a
follow-up ticket with documented rationale, satisfying the ticket's AC #3 "fix or document deferring"
requirement. `docs/agent-monitoring/schema.md` is updated for doc/code parity, including a previously
undocumented gap (`implement-epic.js`'s missing sidecar) that this investigation surfaced. A new static
text-parsing test file proves the structural relocation; AC #2's runtime claim is additionally satisfied
by one documented live end-to-end run, not by pytest alone.

## Decisions on the 3 Open Questions (resolved here, not deferred)

**Decision 1 — Scope-phase (`ticket-scoper`) sidecar gap: OUT OF SCOPE for this ticket.**
Rationale: This ticket's title and Scope bullet 1 both use the verb "replace" against "Step 0b sidecar-write
prompt-text instruction[s]" — i.e., its mandate is to relocate an *existing* mechanism, not to build new
coverage where none has ever existed. The Scope-phase call site (`implement-ticket.js:52-136`, both
branches) has never had a Step 0b instruction, exactly like `writeMonitoring`'s own call (which the
investigation confirms must remain excluded by design). Treating "never had one" identically for both sites
keeps the scope boundary simple and auditable: *this ticket only touches call sites that currently emit the
pattern being relocated.* AC #1's literal wording ("agent() call site... **with** a Step 0b instruction")
supports this reading directly. Extending coverage to Scope is a legitimate, real gap (per investigation
Risk #1) but is net-new work requiring its own design/test consideration (e.g., is `seq` always `1` here,
what happens with stale `.claude/current_run` from a crashed prior run) — recommend a follow-up ticket,
not silently rolled into this one's diff.

**Decision 2 — `implement-epic.js` / `create-tickets.js`: DEFER, with documented rationale (AC #3's second option).**
Rationale: Same "relocate vs. build new" boundary as Decision 1. Both files currently have **zero** sidecar
registration — there is nothing in either to "replace." Fixing them would mean designing and adding a new
mechanism, not relocating an existing one, and `implement-epic.js`'s own investigation finding (its
`batchEvents` per-child-ticket array is not 1:1 with its own `agent()` calls) means even a "same fix" isn't
a pure mechanical mirror — it requires a scoping decision (fix only its 3 direct `agent()` calls, exclude
`batch-monitoring-write` by the same by-design exclusion as `writeMonitoring`) that deserves its own
ticket/investigation rather than an ad hoc decision embedded in this diff. This ticket instead: (a) fixes
the doc gap `schema.md:185` has today (its current text incorrectly implies `implement-epic` already
computes `tool_call_count` "the way it is for implement-ticket/implement-epic" — post-fix this is only true
for `implement-ticket`), and (b) records the recommended follow-up ticket in the ticket's Implementation
Notes. This satisfies AC #3's explicit escape valve.

**Decision 3 — AC #2 verification: static tests + one documented live run, not pytest alone.**
Rationale: No JS test runner exists for `.claude/workflows/*.js` (confirmed by investigation). The static
regression suite (Step 6 below) proves the *structural precondition* (no Step 0b prompt text remains, a
`bash()` sidecar write precedes every covered `agent()` call) deterministically and cheaply. It cannot
execute the workflow to observe the *runtime outcome* AC #2 literally describes. Per test_plan.md item 8,
this plan adds an explicit manual-verification step (Step 9) whose result is recorded in the ticket's Test
Summary before Finalize — this is the accepted verification path for AC #2, not a gap.

## Steps

### Step 1 — Add the orchestrator-side `writeSidecar(seq)` helper
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Insert a new helper function immediately after the `pushEvent` const definition (after line
167, before the `classifyChecklistFailure` comment block at line 169). It must close over `tid` (already in
scope from line 140) and take `seq` as its only parameter:

```js
// Orchestrator-side sidecar write — replaces the former per-prompt "Step 0b" (and Finalize's combined
// "Step 0") agent-prompt-text instruction. Call this once, immediately before each corresponding
// `await agent(...)` call below, passing `events.length + 1` (the same seq value the removed prompt-text
// line used to compute inline, at the same point in execution — JS here is single-threaded and
// await-sequenced, so there is no timing drift). Args passed as individually-quoted argv elements, never
// JSON-embedded in the `-c` string (mirrors tagCheckOutput/archCheckOutput/p0ScanOutput's convention,
// documented at implement-ticket.js:756-763 — embedding JSON directly in a double-quoted python3 -c
// string corrupts the script on nested unescaped quotes). Fail-open per CLAUDE.md's "monitoring write
// failure must never fail the workflow" rule — keeps the existing `2>/dev/null || true` suffix.
const writeSidecar = async (seq) => {
  await bash(
    `python3 -c "
import json, sys
open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2])}))
" "${tid}" "${seq}" 2>/dev/null || true`
  )
}
```
**Do NOT touch:** `pushEvent`, `classifyChecklistFailure`, `writeMonitoring` (including its Step 5
`printf '{}' > .claude/current_run` clear at line ~236-237 — leave byte-identical).
**Verify:** `test_tid_and_seq_passed_as_argv_not_json_embedded` (asserts the helper's shape).

### Step 2 — Relocate the 9 two-line call sites (Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity, Security-Review, Verify/done-check)
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** At each of the 9 sites below, (a) delete the single `Step 0b: run \`python3 -c "import
json; open('.claude/current_run'...` line from the prompt template string (only that line — leave the
`Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`...` line directly above it untouched, and leave the blank line
structure otherwise as close to original as reads cleanly), and (b) insert `await writeSidecar(events.length
+ 1)` as its own statement immediately before the `await agent(` call it was paired with:

| Site | `label` | Prompt-text line to delete (approx.) | Insert `writeSidecar` before |
|---|---|---|---|
| Investigate | `investigate` | line 350 | `investigation = await agent(` at line 344 |
| Plan | `plan` | line 393 | `plan = await agent(` at line 387 |
| Review | `architecture-review` | line ~455 | `review = await agent(` at line ~450 |
| Implement | `implement` | line ~526 | `implementation = await agent(` at line ~521 |
| Architecture-Verify | `architecture-verify` | line ~597 | `await agent(` at line ~592 |
| Test | `test-scope-and-run` | line ~660 | `await agent(` at line ~655 |
| Parity | `parity-update` | line 811 | `const parity = await agent(` at line 806 |
| Security-Review | `security-review` (conditional block) | line ~905 | `await agent(` at line ~900 |
| Verify | `done-check` | line ~970 | `const doneCheck = await agent(` at line ~965 |

**Do NOT touch:** the `Step 0` ts-capture line at each site; any `Step 0c`, numbered step, schema object, or
`pushEvent(...)` call below/after each site; the Security-Review block's conditional guard (`if` wrapping its
`agent()` call) — only its interior sidecar line moves.
**Verify:** `test_no_step_0b_agent_prompt_sidecar_text_remains`,
`test_sidecar_bash_write_precedes_each_covered_agent_call`,
`test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`.

### Step 3 — Relocate the Finalize call site
**Files:** `.claude/workflows/implement-ticket.js` (~lines 1022-1025)
**Change:** Delete the combined `Step 0: run \`python3 -c "import json; open('.claude/current_run'...`
line entirely from Finalize's prompt (this is the file's only site where "Step 0" *is* the sidecar write —
no separate ts-capture text exists here today, and none must be introduced). Insert `await
writeSidecar(events.length + 1)` immediately before `await agent(` at line 1022. Renumber nothing else —
Finalize's remaining steps (currently starting at "Complete these steps in order: 1. Update...") keep their
existing numbering; do not insert a new "Step 0" placeholder text.
**Do NOT touch:** Finalize's `agent()` call has no `schema` and its `pushEvent('Finalize', ...)` call (line
~1125) passes no `ts` argument — do not add either.
**Verify:** `test_finalize_call_site_still_registers_sidecar`.

### Step 4 — Guard the two intentionally-excluded call sites
**Files:** `.claude/workflows/implement-ticket.js` (no production-code change — verification only)
**Change:** None. Confirm after Steps 1-3 that no `writeSidecar(` call was inserted before (a) the
Scope-phase `agent()` call (lines 52-136, either the "load existing" or "create new" branch) or (b)
`writeMonitoring`'s own `agent()` call (line 195). This is Decision 1 and the investigation's Risk #3,
respectively — both are deliberate, permanent scope boundaries, not oversights to "complete" later.
**Do NOT touch:** lines 52-136, line 195.
**Verify:** `test_writeMonitoring_call_has_no_preceding_sidecar_write`, plus a companion assertion in the
same test (or a sibling function) confirming the Scope-phase call site region also has no `writeSidecar(`
call — protects Decision 1 from silent "completion" by a future contributor who mechanically iterates every
`await agent(` site.

### Step 5 — Update `docs/agent-monitoring/schema.md` for doc/code parity (AC #4)
**Files:** `docs/agent-monitoring/schema.md`
**Change:**
- Line 221 ("Each agent prompt includes an early Bash step that writes `{"run_id": "...", "seq": N}` to
  `.claude/current_run`...") → rewrite to describe the new mechanism: the orchestrating workflow
  (`implement-ticket.js`) writes `.claude/current_run` itself via a `bash()` call (the shared
  `writeSidecar(seq)` helper) immediately before dispatching each corresponding `agent()` call; agent
  prompts no longer contain this instruction.
- Line 212 ("Written by the agent to `.claude/current_run` as its first Bash step...") → update to say the
  write is made by the orchestrating workflow via `bash()`, immediately before the paired `agent()` call.
- Line 185 (`create-tickets` gap sentence) → correct and extend: state that **both** `create-tickets` and
  `implement-epic` do not register a `.claude/current_run` sidecar per agent call (neither ever has), so
  `tool_call_count` is always `null` on their events; `implement-ticket` now computes it via the
  orchestrator-side `bash()` mechanism described in the section above. Remove the now-inaccurate phrase "not
  computed the way it is for implement-ticket/implement-epic" (it wrongly implied `implement-epic` already
  had this working).
**Do NOT touch:** any other section of `schema.md` (unrelated field tables, `status` value tables, the
`runs.jsonl` section, etc.).
**Verify:** `test_schema_doc_no_longer_describes_agent_self_report_mechanism`.

### Step 6 — New static-text regression test file
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py` (new)
**Change:** Implement, reusing `tests/tools/test_tag_skill_mapping_check.py`'s raw-source-text-parsing
pattern (`Path.read_text()` on `.claude/workflows/implement-ticket.js`; never execute the file):
1. `test_no_step_0b_agent_prompt_sidecar_text_remains`
2. `test_sidecar_bash_write_precedes_each_covered_agent_call` (covers all 9 two-line sites + Finalize; "no
   other `await agent(` interleaved between the write and its paired call")
3. `test_finalize_call_site_still_registers_sidecar`
4. `test_writeMonitoring_call_has_no_preceding_sidecar_write` (extended per Step 4 to also assert the
   Scope-phase region has none)
5. `test_tid_and_seq_passed_as_argv_not_json_embedded`
6. `test_schema_doc_no_longer_describes_agent_self_report_mechanism` (reads `docs/agent-monitoring/schema.md`
   as text; may live here or in `test_validate_agent_monitoring.py` — pick whichever already has a fixture
   for reading that doc file; do not duplicate fixtures)
**Do NOT touch:** `tests/tools/test_tag_skill_mapping_check.py` itself (reference pattern only, read-only).
**Verify:** `pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` passes.

### Step 7 — Anti-drift guards for adjacent must-not-change regions
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py` (additional functions in the Step 6 file),
and `tests/tools/test_record_events.py` only if it lacks a suitable existing assertion
**Change:** Add:
- `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites` — byte-identical `Step 0: run \`date -u
  +%Y-%m-%dT%H:%M:%SZ\`...` text still present at all 9 two-line sites (protects sibling ticket
  `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`'s adjacent scope from being accidentally touched here).
- `test_writeMonitoring_step5_sidecar_clear_still_present` — the `printf '{}' > .claude/current_run` clear
  step inside `writeMonitoring` (Step 5, ~line 236-237) is present, unchanged, unreordered relative to Steps
  1-4.
- `test_record_events_required_fields_unchanged` — `record_events.py`'s `REQUIRED` field set is unmodified.
  Check `tests/tools/test_record_events.py` first for an existing equivalent assertion before adding a new
  one; if one already exists, do not duplicate it — just confirm it still passes.
**Do NOT touch:** `record_events.py` itself; `writeMonitoring`'s Steps 1-4 logic.
**Verify:** full Step 6 + Step 7 suite passes: `pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_record_events.py -v`.

### Step 8 — Record decisions and deferred follow-up in the ticket
**Files:** `tickets/inprogress/TCK-20260710-CURRENT-RUN-SIDECAR-BASH.md` (`Implementation Notes` and
`Assumptions / Open Questions` sections only)
**Change:** Record: (a) Decisions 1-3 above verbatim/summarized, with rationale; (b) a recommended follow-up
ticket description: "extend `.claude/current_run` sidecar coverage to call sites that have never had one —
Scope-phase (`ticket-scoper`) in `implement-ticket.js`, and `implement-epic.js`'s non-excluded `agent()`
calls (`discover`, `folder-cleanup`), and `create-tickets.js`'s `agent()` calls — as net-new coverage, not a
relocation"; (c) note that AC #2 is satisfied via Step 9's manual run, not pytest alone.
**Do NOT touch:** the ticket's `Scope`, `Out of Scope`, or `Acceptance Criteria` sections — those were fixed
at Scope phase; only append to `Implementation Notes`/`Assumptions`.
**Verify:** no pytest test — reviewed by done-checker's "no important decision is undocumented" condition.

### Step 9 — Live end-to-end manual verification (satisfies AC #2's literal runtime claim)
**Files:** none (operational step; no code change)
**Change:** After Steps 1-7 are implemented and committed, run `implement-ticket.js` end-to-end (this
ticket's own close-out run is sufficient — it will naturally exercise the new `writeSidecar` mechanism at
every phase) and confirm `agent-monitoring/events.jsonl` shows non-null/non-empty `tool_call_count` and
`cost_proxy_score` for every phase event produced, with the Step 0b prompt text now structurally absent from
every prompt. Record the observed `run_id` and outcome in the ticket's `Test Summary` section before
Finalize.
**Do NOT touch:** no source files change during this step; observation only.
**Verify:** manual — non-null `tool_call_count`/`cost_proxy_score` fields present in the resulting
`events.jsonl` entries for this run, recorded in the ticket's Test Summary.

## Scope Guards

- Do not touch the `Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`...` ts-capture lines anywhere in
  `.claude/workflows/implement-ticket.js` — that is sibling ticket `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`
  (C2)'s scope, textually adjacent at all 9 two-line sites.
- Do not implement `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT` (C3)'s `verified_by` provenance-enforcement
  scope — unrelated mechanism, file-adjacent only.
- Do not modify `record_events.py`'s REQUIRED-field validation logic — explicitly Out of Scope per the
  ticket.
- Do not touch any of the 4 "related, smaller ideas" from
  `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` (asymmetric gate coverage beyond
  the security tag, cross-retro trend detection in `generate_retro.py`, tag→skill mapping dedup, malformed
  `working_log.csv` row backfill) — explicitly Out of Scope.
- Do not add sidecar-write coverage to the Scope-phase (`ticket-scoper`) call site, `writeMonitoring`'s own
  call, `implement-epic.js`, or `create-tickets.js` in this ticket's diff — Decisions 1 and 2 explicitly
  defer all four to a follow-up ticket.
- Do not reorder or remove `writeMonitoring`'s Step 5 sidecar-clear (`printf '{}' > .claude/current_run`).
- Do not attempt to fix `.claude/current_run`'s single-global-file-with-no-session-partitioning
  characteristic — pre-existing, not named in Scope.
- Do not rename or refactor the `agent()`/`bash()` orchestrator-call abstractions themselves.

## Dependency Map

- Step 1 (helper) must land before Steps 2-4 (all consume `writeSidecar`).
- Steps 2, 3, 4 are otherwise independent of each other (different, non-overlapping line ranges) and can be
  implemented/verified in any order after Step 1.
- Step 5 (schema.md) is independent of Steps 1-4 — can be done in parallel, but logically documents the
  end-state Steps 1-4 produce, so should be reviewed after Steps 1-4 land to ensure the description matches
  the actual final code shape.
- Step 6 (new test file) depends on Steps 1-4 existing (it asserts their post-conditions) and on Step 5 for
  its schema.md-parity test.
- Step 7 depends on Step 6 (same file, additional functions) and is otherwise independent.
- Step 8 depends on Decisions 1-3 already being fixed (they are, in this plan) — purely a documentation
  transcription step, can happen any time after Step 1.
- Step 9 depends on Steps 1-7 all being committed (it exercises the finished mechanism end-to-end).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — every `agent()` call site with a Step 0b instruction has it replaced by orchestrator-side `bash()` | Steps 1, 2, 3 | `test_no_step_0b_agent_prompt_sidecar_text_remains`, `test_sidecar_bash_write_precedes_each_covered_agent_call`, `test_finalize_call_site_still_registers_sidecar` |
| AC #2 — end-to-end run with Step 0b text absent still produces non-empty `tool_call_count`/`cost_proxy_score` | Steps 1-3 (structural precondition), Step 9 (runtime proof) | Structural: Step 6 test suite. Runtime: Step 9 manual verification, recorded in Test Summary |
| AC #3 — `implement-epic.js`/`create-tickets.js` fixed or deferral documented with rationale | Decision 2, Step 5 (schema.md doc-gap fix), Step 8 (ticket documentation) | `test_schema_doc_no_longer_describes_agent_self_report_mechanism`; manual review of ticket's Implementation Notes |
| AC #4 — `schema.md` sidecar-attribution section updated for doc/code parity | Step 5 | `test_schema_doc_no_longer_describes_agent_self_report_mechanism`, `tests/tools/test_validate_agent_monitoring.py` (regression, unmodified) |

## Anti-Drift Notes

- The single highest-probability drift risk is a careless block-level edit at the 9 two-line sites slurping
  sibling ticket C2's adjacent `Step 0` ts-capture scope into this diff, or breaking `ts` capture while
  removing `Step 0b`. Step 2 is explicitly line-scoped (delete only the Step 0b line) and Step 7 adds a
  byte-identical regression guard for exactly this.
- Finalize (Step 3) is structurally different from the other 9 — a mechanical find-and-replace across all
  "Step 0b"/"Step 0" occurrences risks either leaving its sidecar write unmodified (inconsistent) or
  introducing a spurious unused `ts` capture where none exists today. Handle it as its own step with its own
  test, not folded into Step 2's loop.
- `writeMonitoring`'s own `agent()` call (label `monitoring-write`) must remain permanently sidecar-free —
  it is the process that *computes* `tool_call_count`/`cost_proxy_score` by reading `tools.jsonl`; giving it
  its own sidecar creates a self-referential ordering problem (Risk #3 in investigation.md). Step 4's guard
  test exists specifically to keep a future contributor from "completing" this by mistake.
- `.claude/current_run` is a single global, session-wide file with no per-run/session partitioning — this is
  pre-existing and out of scope to fix; do not regress it further (Step 5's edits are documentation-only for
  this file's mechanism, not behavior changes to it).
- This ticket is sequenced first of 3 sibling children (`TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`,
  `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`) specifically to avoid line-number collisions in
  `implement-ticket.js` — land and finalize this ticket's diff before those begin editing the same file.
- `tools/agent-monitoring/post_tool_hook.py` and `.claude/settings.json`'s hook wiring are read-only context
  for this ticket (confirmed identical attribution-count behavior whether the orchestrator or the agent
  issues the write) — no changes are planned or needed there.

## Unresolved Questions

None. All 3 open questions carried forward from investigation.md are resolved above (Decisions 1-3) with
documented reasoning, per this ticket's scope-boundary principle ("relocate existing coverage only; defer
net-new coverage to a follow-up ticket").
