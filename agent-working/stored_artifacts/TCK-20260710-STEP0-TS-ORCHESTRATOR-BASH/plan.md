---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
artifact_type: plan
tags: [agent-monitoring, workflows, data-quality]
---

# Implementation Plan — TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Summary

Replace every agent-prompt "Step 0: run `date -u +%Y-%m-%dT%H:%M:%SZ`" instruction across
`.claude/workflows/implement-ticket.js` (11 genuine sites, corrected from the ticket's stale "12"),
`.claude/workflows/implement-epic.js` (3 sites), and `.claude/workflows/create-tickets.js` (1 site) —
**15 total, not the ticket's stated 16** — with an orchestrator-side `bash('date -u +%Y-%m-%dT%H:%M:%SZ')`
capture, mirroring the shape of C1's already-landed `writeSidecar(seq)` helper
(`implement-ticket.js:178-185`). A new `captureTs()` helper is added to `implement-ticket.js` (composing
alongside `writeSidecar`, never merged into it); `implement-epic.js` and `create-tickets.js` each get
their own equivalent local helper since they don't share `implement-ticket.js`'s module scope. Each
capture happens *before* the paired `writeSidecar` call (where one exists) so C1's adjacency-string
regression tests keep matching unmodified. The two-mechanism split (JSON-schema `ts` field at 13 sites;
free-text `PHASE_TS: <result>` prefix + regex-strip at Investigate/Plan) is fully retired — both prompt
text and the `PHASE_TS` parsing logic are removed, replaced by direct assignment of the orchestrator-
captured value. `TICKET_SCHEMA.required` and `DISCOVER_SCHEMA.required` drop `'ts'` (the only two
schemas that force it); no other schema needs a companion edit since `ts` is already optional there and
is simply no longer populated. `record_events.py` and `generate_retro.py` are untouched.
`docs/agent-monitoring/schema.md`'s `ts` field description is updated to state it is orchestrator-
captured. The sibling ticket's now-incorrect regression test
(`test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`) is removed from
`tests/tools/test_current_run_sidecar_orchestrator.py` (its guarding job — protecting this ticket's scope
from C1 — is complete now that this ticket is the one making the change), and full new coverage is added
in a new dedicated file, `tests/tools/test_step0_ts_orchestrator.py`, to keep the sidecar file scoped
purely to C1's mechanism.

## Decisions on the 4 Planning-Time Open Questions

1. **Does any Step 0 need the agent's own wall-clock moment, not the orchestrator's dispatch moment?**
   **Decision: No — confirmed, not just recommended.** Independently re-verified during planning:
   `generate_retro.py` reads `runs.jsonl`'s `duration_s`/`start_ts` for its Slow Runs / Avg Duration /
   `iso_week()` computations, never `events.jsonl`'s per-event `ts` (confirmed directly against the file
   in investigation). `record_events.py`'s `validate_record` only checks `ts` is present/non-null, never
   its provenance or precision. `docs/agent-monitoring/schema.md`'s Join Example uses `ts` as passthrough
   display data only. No code path anywhere distinguishes "the instant the agent began reasoning" from
   "the instant the orchestrator dispatched the call" — in a single-threaded, `await`-sequenced JS
   workflow these are the same instant to sub-second precision in every practical case. All 15 sites
   convert with no loss of meaning.

2. **Correct AC #1's site count (16→15) in the ticket?**
   **Decision: Yes.** The ticket's own AC #1 and Scope bullet 1 double-counted a Finalize "Step 0" that
   never existed as a ts-capture site (Finalize's only "Step 0" was always the sidecar-only mechanism C1
   relocated; it has no `date -u` text and no schema `ts` field). Step 8 of this plan updates the ticket
   file directly: AC #1 becomes "15 total sites" and the stale line-number list is replaced with the
   corrected, current numbers below. This is a factual correction, not a scope change — the set of sites
   actually being fixed does not change, only the count and citations describing it.

3. **Fold in create-tickets.js:651 (Write-phase per-task `ts`, same failure shape, not literally
   "Step 0"-labeled)?**
   **Decision: Defer, explicitly, do not touch in this ticket.** The ticket's Scope section literally
   enumerates "Step 0" blocks and cites exactly 1 site for `create-tickets.js` (Comprehend, line 157).
   Line 651 is `2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS.` inside the per-task Write-phase
   prompt — same underlying problem, different label, outside this ticket's literal AC wording. Per
   CLAUDE.md ("Never plan more work than the ticket scope... note adjacent problems as future tickets"),
   this is flagged as a same-shape gap for a follow-up ticket, not added to this plan. Step 8 records this
   deferral in the ticket's Assumptions/Open Questions section so it isn't silently lost.

4. **Extend `tests/tools/test_current_run_sidecar_orchestrator.py` or create a new dedicated file?**
   **Decision: Both, in a coordinated split.** Remove
   `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites` from the existing sidecar file (Step 7) —
   its stated purpose, per its own docstring, was to protect this ticket's adjacent scope from being
   accidentally touched by C1; now that this ticket is the one intentionally making the change, that
   specific guard's job is complete and leaving a stale "count >= 9" assertion in a file scoped to a
   different ticket would be confusing. All new coverage (Step 0 text gone, `captureTs()` adjacency,
   `PHASE_TS` convention removed, schema `required` edits, END_TS captures untouched) goes into a new
   file, `tests/tools/test_step0_ts_orchestrator.py`, keeping `test_current_run_sidecar_orchestrator.py`
   scoped purely to C1's sidecar mechanism (its other 10 tests are untouched — see Scope Guards).

## Steps

### Step 1 — Add `captureTs()` helper in `implement-ticket.js`

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Immediately after the existing `writeSidecar` helper (ends line 185, before the
`classifyChecklistFailure` comment block at line 187), add:
```js
// Orchestrator-side ts capture — replaces the former per-prompt "Step 0: run `date -u ...`"
// agent-prompt-text instruction (TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH). Call this once,
// immediately before writeSidecar/the paired `await agent(...)` call, so the captured value can be
// wired directly into pushEvent — never depends on agent prose compliance. Called BEFORE
// writeSidecar at each site so C1's writeSidecar-to-agent() adjacency strings (tests/tools/
// test_current_run_sidecar_orchestrator.py) are untouched by this insertion.
const captureTs = async () => {
  const out = await bash('date -u +%Y-%m-%dT%H:%M:%SZ')
  return (out || '').trim() || null
}
```
**Do NOT touch:** `writeSidecar` itself (lines 178-185) or `pushEvent` (lines 156-167) — this helper
composes alongside them, never merges into either.

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_captureTs_helper_defined_once_after_writeSidecar`
(new test, Step 6).

---

### Step 2 — Convert Scope phase (both branches) to orchestrator-captured `ts`

**Files:** `.claude/workflows/implement-ticket.js`

**Change:**
- Remove `Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` — save result as TS (use as the \`ts\` field).`
  from both prompt branches (line 56, load-existing; line 91, create-new).
- Remove the trailing `, ts=TS.` / `ts=TS.` from each branch's `Return:` sentence (end of load-existing
  branch, line 88; end of create-new branch, line 136) — Return now ends at the preceding field.
- In `TICKET_SCHEMA` (line 33), drop `'ts'` from the `required` array only:
  `required: ['ticket_id', 'ticket_path', 'status', 'conflicts', 'tier', 'tags', 'summary']`.
  Leave the `ts` property definition (line 48) in place, untouched — do not remove it from `properties`,
  it becomes a harmless unused optional field (minimizes diff surface, matches investigation Risk #4's
  exact framing of "companion edit" as a `required`-array fix only).
- Immediately before `const ticketInfo = await agent(` (line 52), insert:
  `const scopeTs = await captureTs()`
- Change `const startTs = ticketInfo.ts || null` (line 142) to `const startTs = scopeTs || null`.
- Change `pushEvent('Scope', 'ticket-scoper', ..., ticketInfo.summary || 'Scoped ticket ' + tid,
  ticketInfo.ts, null, scopeReasonCode)` (line 295) — replace the `ticketInfo.ts` argument with
  `scopeTs`.

**Do NOT touch:** Step 0b (context-warm-start search_docs/graphify instructions, lines 93-98) — this is
an unrelated convention that happens to also be labeled "Step 0b"; `test_scope_phase_call_site_has_no_preceding_sidecar_write`
already asserts `"search_docs"` remains in the Scope region. Do not touch `todos_source_path`,
`mistag_warning`, `suggested_skills`, or any other `TICKET_SCHEMA` field.

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_step_0_ts_capture_lines_gone_from_all_covered_sites`
(Scope portion), `::test_ts_capture_bash_precedes_each_covered_agent_call` (Scope portion),
`::test_ts_schema_required_field_dropped_at_scope_and_discover` (TICKET_SCHEMA portion).

---

### Step 3 — Convert Investigate and Plan phases: remove `PHASE_TS:` free-text convention

**Files:** `.claude/workflows/implement-ticket.js`

**Change:**
- Investigate (inside `if (tier !== 'hotfix') {`): remove the two-line block
  `` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):\nPHASE_TS: <result> ``
  (lines 366-367). Immediately before `await writeSidecar(events.length + 1)` (line 362), insert
  `const investigationTs = await captureTs()`. Change line 396-397 from:
  ```js
  const investigationTs = investigation.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
  investigationText = investigation.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
  ```
  to just:
  ```js
  investigationText = investigation.toString().trim()
  ```
  (the `investigationTs` variable already exists from the new pre-call `captureTs()` line — do not
  redeclare it). `pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200),
  investigationTs)` (line 398) is unchanged — it now receives the orchestrator-captured value.
- Plan (same block): remove the identical two-line block (lines 408-409). Immediately before
  `await writeSidecar(events.length + 1)` (line 404), insert `const planTs = await captureTs()`. Change
  lines 432-433 from:
  ```js
  const planTs = plan.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
  planText = plan.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
  ```
  to:
  ```js
  planText = plan.toString().trim()
  ```
  Lines 435-447 (unresolved-question check, `pushEvent('Plan', ...)` calls) are unchanged — they already
  reference `planText`/`planTs` by name.

**Do NOT touch:** The `unresolved question` substring check (line 435), the `NEEDS_HUMAN_INPUT` early
return (lines 436-445), or any other part of `investigationText`/`planText`'s downstream use in later
phases (Review/Implement prompts embed `investigationText`/`planText` via template literals elsewhere —
verify no other line references the now-removed `PHASE_TS:` prefix before considering this step done).

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_phase_ts_prefix_convention_removed_from_investigate_and_plan`.

---

### Step 4 — Convert the 7 remaining JSON-schema `ts` sites (Review, Implement, Architecture-Verify, Test, Parity, Security-Review, Verify)

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Same mechanical edit at each of the 7 sites — remove the one-line
`` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field. `` prompt text,
insert a `const <phase>Ts = await captureTs()` line immediately before the existing
`await writeSidecar(events.length + 1)` line for that site (same indentation as the surrounding block),
and replace every downstream `<returnedObject>.ts` reference for that phase with the new local variable.
Do not remove the `ts` property from any of these 7 schemas — they are already optional (not in
`required`), so no schema edit is needed; the field simply becomes unused.

| Phase | Step 0 line | Insert `captureTs()` before | New var | Downstream `.ts` refs → replace |
|---|---|---|---|---|
| Review | 470 | line 466 (`await writeSidecar...`) | `reviewTs` | line 500 `review.ts`, line 510 `review.ts` |
| Implement | 540 | the `await writeSidecar(events.length + 1)` line immediately preceding `const implementation = await agent(` | `implementTs` | line 565 `implementation.ts` |
| Architecture-Verify | 610 | its preceding `await writeSidecar(...)` line | `archVerifyTs` | line 633 `archVerify.ts`, line 643 `archVerify.ts` |
| Test | 672 | its preceding `await writeSidecar(...)` line | `testTs` | line 690 `testResult.ts`, line 702 `testResult.ts`, line 737 `testResult.ts` |
| Parity | 822 | line 818 (`await writeSidecar...`) | `parityTs` | line 874 `parity.ts`, line 887 `parity.ts` |
| Security-Review | 915 | line 911 (`await writeSidecar...`) | `securityReviewTs` | line 933 `securityReview.ts`, line 943 `securityReview.ts` |
| Verify (done-check) | 979 | its preceding `await writeSidecar(...)` line | `doneCheckTs` | line 1012 `doneCheck.ts`, line 1025 `doneCheck.ts` |

(Line numbers for Implement/Architecture-Verify/Test/Verify's exact `writeSidecar` line and downstream
refs may shift by a few lines once Steps 2-3 land — re-locate each by the unique text shown, e.g.
`const implementation = await agent(`, not by absolute line number alone.)

**Do NOT touch:** Finalize (no Step 0 site exists there at all — do not add one; C1's plan.md already
established this and this ticket's investigation reconfirmed it). Do not alter any `required` array for
these 7 schemas — `ts` was already optional in all of them.

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_step_0_ts_capture_lines_gone_from_all_covered_sites`,
`::test_ts_capture_bash_precedes_each_covered_agent_call` (both, for these 7 sites).

---

### Step 5 — Convert `implement-epic.js` Discover phase (3 ternary branches, 1 agent call)

**Files:** `.claude/workflows/implement-epic.js`

**Change:**
- Add a local `captureTs()` helper (same shape as Step 1's, since this file does not share
  `implement-ticket.js`'s module scope) near the top of the file, adjacent to where `DISCOVER_SCHEMA` is
  defined (before line 41) or immediately before the `const discovery = await agent(` call (line 62) —
  planner's preference: place it directly before line 62 since this file has no `pushEvent`/`writeSidecar`
  cluster to compose alongside.
- Remove `` Step 0 — run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field. `` from
  all 3 branches (folder mode line 66, epic_id mode line 99, request mode line 124).
- In `DISCOVER_SCHEMA` (line 41), drop `'ts'` from `required` only (line 43):
  `required: ['mode', 'ticket_ids', 'already_done', 'summary']`. Leave the `ts` property (line 58)
  in place.
- Immediately before `const discovery = await agent(` (line 62), insert `const discoverTs = await captureTs()`.
- Change `const batchStartTs = discovery.ts || null` (line 143) to
  `const batchStartTs = discoverTs || null`.

**Do NOT touch:** The batch-monitoring-write `Step 1 — get current timestamp` END_TS capture (line 235)
— structurally excluded, same reasoning as `implement-ticket.js`'s `writeMonitoring` END_TS capture (it
backfills `end_ts` after all events already exist; it is not a per-phase `pushEvent` dispatch-time
capture). Do not touch `batchEvents` (lines 221-227) — it carries no `ts` key by design, out of scope by
construction per investigation.

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_step_0_ts_capture_lines_gone_from_all_covered_sites`
(epic portion), `::test_ts_capture_bash_precedes_each_covered_agent_call` (epic portion),
`::test_ts_schema_required_field_dropped_at_scope_and_discover` (DISCOVER_SCHEMA portion),
`::test_end_ts_and_batch_end_ts_captures_untouched` (batch END_TS untouched portion).

---

### Step 6 — Convert `create-tickets.js` Comprehend phase (1 site)

**Files:** `.claude/workflows/create-tickets.js`

**Change:**
- Add a local `captureTs()` helper (same shape) near the existing local `pushEvent` definition
  (after line 114, before line 116's `let startTs = null`).
- Remove `` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and return it as "ts" — captured before any
  other work. `` (line 157).
- Remove the trailing `, ts` from `Return: concerns[], summary (one sentence: N concerns extracted), ts.`
  (line 183) → `Return: concerns[], summary (one sentence: N concerns extracted).`
- Immediately before `const comprehension = await agent(` (line 146), insert
  `const comprehendTs = await captureTs()`.
- Change `startTs = comprehension.ts || null` (line 187) to `startTs = comprehendTs || null`.
- `COMPREHEND_SCHEMA`'s `ts` field (line 88) is already optional (not in `required`, which is
  `['concerns', 'summary']` at line 81) — no schema edit needed here.

**Do NOT touch:** Line 651 (Write-phase per-task `ts` capture) — explicitly deferred, see Decision 3
above. Do not touch `WRITE_SCHEMA`, the Structure/Link phases, or any tag→skill mapping logic in this
file (out of scope, matches `test_tag_skill_mapping_check.py`'s existing guard).

**Verify:** `tests/tools/test_step0_ts_orchestrator.py::test_step_0_ts_capture_lines_gone_from_all_covered_sites`
(create-tickets portion), `::test_ts_capture_bash_precedes_each_covered_agent_call` (create-tickets
portion).

---

### Step 7 — Remove the stale regression test from the sidecar test file

**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py`

**Change:** Delete the `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites` function (lines 94-102)
in its entirety. Leave a one-line comment in its place:
```python
# test_step_0_ts_capture_lines_unchanged_at_all_nine_sites removed —  its guard (protecting this
# ticket's Step 0 `date -u` sites from C1's sidecar work) is obsolete now that
# TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH has itself removed those sites. See
# tests/tools/test_step0_ts_orchestrator.py for the replacement coverage.
```

**Do NOT touch:** Any of the other 10 test functions in this file
(`test_no_step_0b_agent_prompt_sidecar_text_remains`,
`test_sidecar_bash_write_precedes_each_covered_agent_call`,
`test_finalize_call_site_still_registers_sidecar`,
`test_writeMonitoring_call_has_no_preceding_sidecar_write`,
`test_scope_phase_call_site_has_no_preceding_sidecar_write`,
`test_tid_and_seq_passed_as_argv_not_json_embedded`,
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`,
`test_schema_doc_no_longer_describes_agent_self_report_mechanism`,
`test_writeMonitoring_step5_sidecar_clear_still_present`,
`test_record_events_required_fields_unchanged`, `test_all_nine_two_line_site_labels_present`) — all must
keep passing unmodified. Do not touch the module docstring (lines 1-15), `_SIDECAR_WRITE_PROMPT_TEXT`,
`_COVERED_SITE_ADJACENCY`, or `_NINE_TWO_LINE_SITE_LABELS` constants — Step 4's edits must produce source
that still satisfies `_COVERED_SITE_ADJACENCY`'s exact strings (this is why Step 4 inserts `captureTs()`
*before*, not between, `writeSidecar` and each `agent(` call).

**Verify:**
```
pytest tests/tools/test_current_run_sidecar_orchestrator.py -v
```
All 10 remaining tests pass; the removed test no longer collects.

---

### Step 8 — New test file: `tests/tools/test_step0_ts_orchestrator.py`

**Files:** `tests/tools/test_step0_ts_orchestrator.py` (new)

**Change:** Create a new file, reusing the established `Path.read_text()` raw-source-parsing pattern from
`test_current_run_sidecar_orchestrator.py` / `test_tag_skill_mapping_check.py`. Implement the 5 pytest
tests from test_plan.md's New Tests Required (tests 1-4 and 6; test 5 is satisfied by the existing
`test_record_events_required_fields_unchanged` in the sidecar file — confirm it stays green, do not
duplicate its assertion here):

1. `test_step_0_ts_capture_lines_gone_from_all_covered_sites` — asserts
   `` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` `` (implement-ticket.js's 11-site phrasing) and
   `` Step 0 — run \`date -u +%Y-%m-%dT%H:%M:%SZ\` `` (implement-epic.js's 3-site phrasing, note the
   em-dash) and `` Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and return it as "ts" `` (create-tickets.js's
   1 site) are all **absent** from their respective files. Must NOT assert anything about
   `writeMonitoring`'s/batch-monitoring-write's `Step 1 — get current timestamp` END_TS captures (covered
   separately by test 5 below) — those remain present.
2. `test_ts_capture_bash_precedes_each_covered_agent_call` — for each of the 10 implement-ticket.js
   `agent()` call sites (Scope counts once — 2 branches, 1 call), 1 implement-epic.js call site, and 1
   create-tickets.js call site, assert the adjacency `const <name>Ts = await captureTs()\n` immediately
   precedes (whitespace/indentation aside) either `await writeSidecar(...)` (implement-ticket.js) or the
   `agent(` call directly (implement-epic.js, create-tickets.js, which have no `writeSidecar`). Mirror
   `test_sidecar_bash_write_precedes_each_covered_agent_call`'s adjacency-string-list approach.
3. `test_phase_ts_prefix_convention_removed_from_investigate_and_plan` — asserts `PHASE_TS:` is absent
   from implement-ticket.js entirely, and `/^PHASE_TS: (\S+)/m` / `/^PHASE_TS: \S+\n?/` regex literals are
   absent from the source text.
4. `test_ts_schema_required_field_dropped_at_scope_and_discover` — asserts `TICKET_SCHEMA`'s `required`
   array (implement-ticket.js) and `DISCOVER_SCHEMA`'s `required` array (implement-epic.js) do not contain
   `'ts'`, while still containing their other original required fields.
5. `test_end_ts_and_batch_end_ts_captures_untouched` — asserts `` Run via Bash: date -u
   +%Y-%m-%dT%H:%M:%SZ `` inside `writeMonitoring`'s prompt (implement-ticket.js) and the equivalent batch
   END_TS capture text (implement-epic.js, line ~235) are both still present, byte-identical, unmoved.
6. `test_captureTs_helper_defined_once_after_writeSidecar` (Step 1's own verification) — asserts
   `const captureTs = async ()` appears exactly once in implement-ticket.js, positioned after
   `const writeSidecar = async (seq)` and before `const classifyChecklistFailure`.

Give the file a module docstring naming this ticket, mirroring the sidecar file's docstring shape, and
explicitly stating it covers all 3 workflow files (not just implement-ticket.js).

**Do NOT touch:** `tests/tools/test_current_run_sidecar_orchestrator.py` beyond Step 7's single removal —
do not move any of its other 10 tests into this new file.

**Verify:**
```
pytest tests/tools/test_step0_ts_orchestrator.py -v
```
All new tests pass.

---

### Step 9 — Update `docs/agent-monitoring/schema.md`'s `ts` field description (AC #4)

**Files:** `docs/agent-monitoring/schema.md`

**Change:** In the `events.jsonl` Fields table (around line 93), change the `ts` row's description from
`UTC timestamp when this event was recorded.` to state explicitly that the value is orchestrator-
captured, not agent-self-reported — e.g. `UTC timestamp when this event was recorded. Captured by the
orchestrator (bash \`date -u\`) immediately before the paired agent() call, not self-reported by the
agent — see TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH.` Also check the `runs.jsonl`
`start_ts` field description nearby (if it separately claims agent-self-report, update it too; if it
already just says "UTC timestamp" with no provenance claim, leave it — do not invent a claim that wasn't
there before).

**Do NOT touch:** Any other field description, the Join Example JSON blocks, or the status-value tables
already present in this file (lines 55-67) — those are unrelated to this ticket.

**Verify:** `tests/tools/test_step0_ts_orchestrator.py` — add a small assertion (fold into test 1 or a
7th test) that `docs/agent-monitoring/schema.md` contains "orchestrator" near "ts" in the events.jsonl
section. Manual read-through is also acceptable since this is a single sentence change; prefer adding the
assertion for durability.

---

### Step 10 — Correct the ticket's own AC #1 and Scope bullet 1 (Decision 2)

**Files:** `tickets/inprogress/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH.md`

**Change:**
- Scope bullet 1: replace
  `Replace every "Step 0" \`date -u\` prompt-text block across \`.claude/workflows/implement-ticket.js\`
  (12 sites: lines 56, 91, 347, 390, 453, 524, 595, 658, 809, 903, 968, 1025), ...`
  with the corrected count and current line numbers:
  `Replace every "Step 0" \`date -u\` prompt-text block across \`.claude/workflows/implement-ticket.js\`
  (11 sites: lines 56, 91, 366, 408, 470, 540, 610, 672, 822, 915, 979 — Finalize has no separate Step 0
  ts-capture site and is not counted), \`.claude/workflows/implement-epic.js\` (3 sites: lines 66, 99,
  124), and \`.claude/workflows/create-tickets.js\` (1 site: line 157) with an orchestrator-side \`bash()\`
  call whose captured value is wired directly into \`pushEvent\`/\`start_ts\`.`
- AC #1: replace `16 total sites` with `15 total sites` and drop any implied Finalize citation.
- Add to Assumptions/Open Questions: a line recording Decision 3 (create-tickets.js:651 deferred,
  same-shape gap, not in this ticket's scope) so it is not silently lost.

**Do NOT touch:** Any other section of the ticket (Out of Scope, Acceptance Criteria items 2-4, Related
Tickets, etc.).

**Verify:** Manual re-read of the ticket file — no pytest equivalent; this is a documentation-accuracy
fix on the ticket itself, not covered by the test suite.

---

### Step 11 — Live end-to-end verification (AC #3)

**Files:** None (operational step).

**Change:** None — this is the manual verification step, not a code change. After Steps 1-10 land, this
ticket's own close-out run of `/implement-ticket` (or a small scratch run) produces
`agent-monitoring/events.jsonl` entries for the run whose `ts` values are monotonically non-decreasing in
`seq` order. Record the observed `run_id` and outcome in the ticket's Test Summary before Finalize —
same resolution pattern C1 used for its own AC #2.

**Do NOT touch:** No code changes in this step.

**Verify:** Manual inspection of `agent-monitoring/events.jsonl` for the recorded `run_id`; no pytest
equivalent exists (no JS test runner in this repo, per investigation).

## Scope Guards

- Do not touch `writeSidecar` (implement-ticket.js:178-185), its 10 call sites' relative order to
  `writeSidecar`, or `writeMonitoring`'s Steps 1-5 (tool-tracking sidecar write/clear) — C1's already-
  landed, separate mechanism. This ticket's `captureTs()`/equivalent helper composes alongside
  `writeSidecar`, called *before* it at each site, never replacing or merging into it.
- Do not implement `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`'s (C3) `verified_by` provenance scope —
  unrelated mechanism, file-adjacent only.
- Do not touch `record_events.py`'s `REQUIRED` field validation — `ts` stays hard-required at write time;
  only its origin changes.
- Do not touch any of the 4 "related, smaller ideas" from the idea doc (asymmetric gate coverage,
  cross-retro trend detection, tag→skill mapping dedup, `working_log.csv` backfill).
- Do not touch `create-tickets.js:651` (Write-phase per-task `ts`) — explicitly deferred (Decision 3).
- Do not touch `implement-epic.js`'s batch-monitoring-write `Step 1` END_TS capture (line ~235) or
  `implement-ticket.js`'s `writeMonitoring` END_TS capture (line ~217) — both backfill after the fact,
  not per-phase dispatch-time captures.
- Do not remove `ts` from any schema's `properties` (only from `required`, and only for `TICKET_SCHEMA`
  and `DISCOVER_SCHEMA`) — minimizes diff surface, matches investigation Risk #4 exactly.
- Do not move any of `test_current_run_sidecar_orchestrator.py`'s other 10 tests into the new file — only
  the one stale test is removed from it.
- Do not expand this ticket's AC #1 correction into a broader ticket-content rewrite — Step 10 touches
  only Scope bullet 1, AC #1, and one Assumptions/Open Questions addition.

## Dependency Map

- Step 1 (helper) must land before Steps 2-4 (all reference `captureTs()` in implement-ticket.js).
- Steps 2, 3, 4 are independent of each other (different call sites, different variable names) but all
  depend on Step 1.
- Step 5 (implement-epic.js) and Step 6 (create-tickets.js) are independent of Steps 1-4 and of each
  other — each file gets its own local `captureTs()` helper.
- Step 7 (remove stale test) has no code dependency but should land in the same commit as Steps 2-6 to
  avoid a window where the suite has a failing/stale assertion.
- Step 8 (new test file) depends on Steps 1-6 being complete (it asserts the post-change source shape).
- Step 9 (schema.md) is independent of all code steps.
- Step 10 (ticket self-correction) is independent of all code steps but should land before Finalize.
- Step 11 (live verification) depends on Steps 1-9 being complete and merged into a runnable state.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — every Step 0 `date -u` site (corrected: 15, not 16) replaced by orchestrator `bash()`, wired into `pushEvent`/`start_ts` | Steps 1-6 | `test_step_0_ts_capture_lines_gone_from_all_covered_sites`, `test_ts_capture_bash_precedes_each_covered_agent_call`, `test_phase_ts_prefix_convention_removed_from_investigate_and_plan` |
| AC #2 — `record_events.py`'s REQUIRED check for `ts` still passes | (no change — explicitly out of scope) | `test_record_events_required_fields_unchanged` (existing, unmodified) |
| AC #3 — live run's `events.jsonl` `ts` monotonically non-decreasing in `seq` order | Step 11 | Manual — no pytest equivalent |
| AC #4 — `docs/agent-monitoring/schema.md`'s `ts` field description updated | Step 9 | New assertion in `tests/tools/test_step0_ts_orchestrator.py` (Step 9's Verify) |
| Ticket's own AC #1 count correction (16→15) | Step 10 | Manual re-read |

## Anti-Drift Notes

- **The single most important ordering constraint:** at every implement-ticket.js site that has a
  `writeSidecar` call, `captureTs()` must be inserted **before** `writeSidecar`, never between
  `writeSidecar` and the paired `await agent(...)` call — otherwise C1's
  `test_sidecar_bash_write_precedes_each_covered_agent_call` (which checks the exact adjacency string
  `await writeSidecar(events.length + 1)\n<call> = await agent(`) breaks. This is why every step above
  says "insert before the existing `await writeSidecar(...)` line," not "insert before the `agent(` call."
- Two structurally different mechanisms exist and both must be converted: 13 JSON-schema `ts` fields, and
  2 free-text `PHASE_TS:` prefix sites (Investigate, Plan) with orchestrator-side regex parsing. Converting
  only one class leaves the fix incomplete — this is the investigation's Risk #3, addressed by Steps 2-4
  (schema sites) and Step 3 (PHASE_TS sites) together.
- `TICKET_SCHEMA` and `DISCOVER_SCHEMA` are the *only* two schemas needing a `required`-array edit — every
  other `ts`-bearing schema is already optional. Do not "complete the pattern" by also editing the other
  9 schemas' `required` arrays; they don't need it and doing so isn't wrong but is unnecessary scope.
- Finalize genuinely has no Step 0 ts-capture site and never did — do not search for a "missing 12th site"
  in implement-ticket.js to reconcile the ticket's stale AC count; Step 10 corrects the count instead of
  chasing a nonexistent site.
- `docs/ai/ticket-lifecycle.md` (lines 259, 323, 360) uses "Step 0" for an unrelated, pre-existing
  orchestrator-run static-precheck convention (architecture-reviewer/parity-updater/done-checker). This
  ticket's "Step 0 `date -u`" is a different "Step 0" in the same files — if any doc update mentions "Step
  0," be precise about which convention is meant.
- No parity ledger entries require updating (confirmed in investigation — `layer: ai`, no mechanics/engine
  overlap).

## Unresolved Questions

None — all 4 planning-time questions from the investigation are resolved above with documented reasoning
(see "Decisions on the 4 Planning-Time Open Questions").

## Deviations

Implementation followed all 11 steps as written, with two minor corrections discovered during Step 8
(new test file), both strengthening rather than weakening coverage — recorded here per CLAUDE.md's
"never silently deviate" rule:

1. **Step 8, test 5 (`test_end_ts_and_batch_end_ts_captures_untouched`)**: the plan's prose described
   `implement-ticket.js`'s and `implement-epic.js`'s END_TS capture text as "byte-identical." On
   implementation, the two are not identical — `implement-ticket.js` says `"Step 1 — get current
   timestamp (run end time):\n  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ\n  Save result as END_TS."`
   while `implement-epic.js` says `"Step 1 — get current timestamp (batch end time):\n  Run via Bash:
   date -u +%Y-%m-%dT%H:%M:%SZ\n  Save as END_TS."`. The test asserts both exact strings separately
   instead of one shared string. The underlying invariant (both are unmodified, unmoved) is preserved;
   only the plan's factual assumption about text identity was wrong.
2. **Step 8/Step 9's schema.md assertion**: Step 9's Verify note suggested folding a bare
   `"orchestrator" in schema_doc` check into test 1. Implemented instead as a regex match against the
   specific events.jsonl `ts` field-row text, because a bare whole-document substring check would have
   passed vacuously — `docs/agent-monitoring/schema.md` already contains an unrelated "orchestrator"
   mention (from C1's `tool_call_count` work) even before Step 9's edit landed. The tightened assertion
   is strictly more durable than the plan's literal suggestion and verifies the same fact (AC #4).

Both corrections are documented here and in the ticket's Implementation Notes; neither changes scope,
files touched, or the set of sites converted.
