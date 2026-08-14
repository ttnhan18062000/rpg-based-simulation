---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CLAUDE-EXECUTION-IDENTITY
artifact_type: plan
tags: [ai, workflows, agent-monitoring, observability, testing]
---

# Implementation Plan — TCK-20260730-CLAUDE-EXECUTION-IDENTITY

## Summary

This is a small, surgical write-side activation confined almost entirely to two function
*bodies* inside `.claude/workflows/implement-ticket.js` — `writeSidecar` and `writeMonitoring` —
plus one new generation point that both close over, exactly the way both already close over
`tid`. It is explicitly **not** a 25-call-site sweep: all 15 `writeMonitoring(...)` call sites
and all 10 `writeSidecar(...)` call sites keep their exact existing call shape; only the shared
function bodies gain the three new fields. No production Python file changes (`post_tool_hook.py`,
`record_events.py`, `record_run.py`, dashboard `ingest.py`/`models.py` already support these
fields per `TCK-20260721-MONITORING-WRITER-UNIFICATION`). The plan proceeds: (1) generate
`executionId`/`PROVIDER` once after `tid` is known, (2) thread them into `writeSidecar`'s body via
closure + trailing argv, (3) thread them into `writeMonitoring`'s prompt-constructed JSON via
closure, (4) add a guard test proving the two pre-`tid` identity-less paths stay untouched
(resolving the investigation's one open question as "no — stays identity-less"), (5) add
integration coverage proving one execution's records share one `execution_id` and a second
execution gets a different one, (6) add a byte-level pre/post baseline-prefix test operationalizing
AC6 using this ticket's own remaining workflow phases as the controlled validation run, **plus an
explicit content-correctness assertion on the newly appended lines themselves** (parsing each new
line for exactly-once, correctly-valued `execution_id`/`provider`/`ticket_id`/`run_id` — added in
this revision per architecture-review's NEEDS_CHANGES finding; see Revision Note below), (7) add
legacy-token tolerance coverage, (8) update the two docs required to satisfy the doc-staleness
gate and keep the activation-status tracker accurate, and (9) update the two P2 parity-ledger
entries (`INFRA-275`, `INFRA-281`) that describe the functions being extended.

## Revision Note

This is a revised plan addressing architecture-review's `NEEDS_CHANGES` verdict on the prior
version of this plan. Steps 1-5, 7, 8, and 9 are unchanged from the reviewed version; only Step 6
(and the AC6 row in the Acceptance Criteria Map, plus two cross-referencing notes in the
Dependency Map and Anti-Drift Notes) were revised.

**Finding (quoted, abridged):** "`writeMonitoring`'s Step 2/Step 3 'JSON construction'
(`implement-ticket.js:339-348`) is not deterministic JS code — it is natural-language prompt text
that an LLM agent interprets at runtime to build the JSON payload... The plan's Step 6
baseline-comparison mechanism (checksum of the first N pre-existing lines, before/after) only
proves pre-existing lines are never rewritten — it does NOT prove that the newly-appended lines
themselves are well-formed (e.g. no duplicate/colliding JSON keys, no accidental overwrite of
`run_id` by the new `ticket_id`/`execution_id` instructions within the same object, no LLM-side
misconstruction of the three new fields)... none of Steps 1/2/3/5/6/7 as currently scoped would
catch it."

**Fix applied:** Step 6 now has two required parts. Part A retains the original byte-checksum
prefix comparison (proves old lines untouched). Part B is new: it parses every newly appended
JSONL line — in both the synthetic fixture test and the real controlled-validation run's
Implementation-Notes-recorded manual check — using a duplicate-key-sensitive parse plus a raw-text
occurrence count, and asserts `execution_id`/`provider`/`ticket_id`/`run_id` each appear exactly
once with the expected non-empty/correct value. See Step 6 below and the "`json.loads` alone hides
duplicate keys" bullet in Anti-Drift Notes for why a plain parsed-dict comparison was insufficient.

## Steps

### Step 1 — Generate `executionId`/`PROVIDER` once, right after `tid` is known
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Immediately after `const tid = ticketInfo.ticket_id` (line 202), before the "Agent
Monitoring Setup" block (line 206) — i.e. before `pushEvent`, `writeSidecar`, `writeMonitoring`
are defined — insert:
```js
const PROVIDER = 'claude'
const execIdSuffixRaw = await bash(`python3 -c "
import secrets, time
print('EXECID:' + str(int(time.time() * 1000)) + '-' + secrets.token_hex(4))
" 2>/dev/null`)
const execIdMarker = (execIdSuffixRaw || '').indexOf('EXECID:')
const execIdSuffix = execIdMarker !== -1 ? execIdSuffixRaw.slice(execIdMarker + 'EXECID:'.length).trim() : `${Date.now()}-fallback`
const executionId = `${PROVIDER}-${tid}-${execIdSuffix}`
```
This is the single insertion point; `executionId` and `PROVIDER` become available to every
downstream closure (`writeSidecar`, `writeMonitoring`, `pushEvent`) the same way `tid` already is.
Do not touch the `tid`-definition line itself, `pushEvent`'s own definition, or anything above
line 202.
**Do NOT touch:** Any of the 15 `writeMonitoring(...)` or 10 `writeSidecar(...)` call sites; the
Scope-phase code above line 202 (lines 62-194).
**Verify:** `test_execution_id_generated_once_and_reused_across_events` (new, in
`tests/tools/test_current_run_sidecar_orchestrator.py`) — asserts `executionId` is computed
exactly once, after `tid`'s definition and before `writeSidecar`/`writeMonitoring`'s definitions
(index-ordering assertion).

### Step 2 — Thread `execution_id`/`provider` into `writeSidecar`'s body via closure
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Edit only the *body* of `writeSidecar` (`implement-ticket.js:240-247`). Keep the
declared signature exactly `async (seq, phase, agent)` — do not widen it. Inside the body's
python payload, add `'execution_id': sys.argv[5], 'provider': sys.argv[6]` to the JSON dict being
written, and append `"${executionId}" "${PROVIDER}"` as new trailing argv elements in the bash
template literal — **after** the existing `"${agent}"`, never inserted between existing args. The
existing substring `'"${tid}" "${seq}" "${phase}" "${agent}"'` must remain present unbroken.
**Do NOT touch:** Any of the 10 call sites (`:456,559,640,709,825,886,1035,1127,1190,1244`) — they
keep calling `writeSidecar(seq, phase, agent)` exactly as today. Do not touch
`post_tool_hook.py` (already reads these fields off the sidecar, confirmed in investigation).
**Verify:** `test_writeSidecar_body_includes_execution_id_and_provider_via_closure_not_param` (new)
and the extended `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` (existing,
must keep passing on the unbroken substring), plus
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` (existing
signature literal-match guard) must keep passing unmodified — proves the parameter list wasn't
widened.

### Step 3 — Thread `execution_id`/`provider`/`ticket_id` into `writeMonitoring`'s prompt JSON
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Edit only the *body* of `writeMonitoring(finalStatus)` (`implement-ticket.js:314-357`).
In Step 2's per-event JSON construction instructions (~line 341) and Step 3's `record_run.py
--data` JSON literal (~line 348), add `"execution_id": "${executionId}", "provider":
"${PROVIDER}", "ticket_id": "${tid}"` to the JSON the agent prompt instructs be written. The
literal provider value must be exactly `"claude"` — never `"claude-code"` anywhere in this new
text. Keep Step 0's sidecar-clear-first ordering and the Step 0-1-2-3 label structure/count
completely unchanged — only the *content* of what Steps 2/3 instruct changes.
**Do NOT touch:** Any of the 15 call sites (`:401,413,428,611,673,775,851,908,955,1090,1148,1228,1325,1337,1347`)
— they keep calling `writeMonitoring(status)` with a bare status string exactly as today. Do not
touch `record_events.py`'s or `record_run.py`'s `REQUIRED` sets (confirmed unchanged/optional by
investigation — adding these three fields there would break every non-Claude-workflow caller of
these tools, e.g. `implement-epic`, `create-tickets`).
**Verify:** `test_writeMonitoring_prompt_embeds_execution_id_provider_ticket_id_in_events_and_run_record`
(new) and `test_writeMonitoring_step0_sidecar_clear_precedes_other_steps` (existing, must keep
passing unmodified) plus `test_record_events_required_fields_unchanged` (existing, must keep
passing unmodified, proves `record_events.py` itself is untouched).

### Step 4 — Guard test: pre-`tid` identity-less paths stay untouched (resolves the open question)
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py`
**Change:** Add `test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less`, asserting
that neither the Scope-agent-failed fallback block (`implement-ticket.js:189-194`) nor the
Scope-phase resume-branch's pre-`tid` inline sidecar write (`implement-ticket.js:62-67`) contains
`execution_id`/`provider` in their source text. **No production code changes in this step** — this
is a decision made explicit and pinned by a test, not new behavior. Decision (per investigation's
recommendation, now adopted as final): the resume-branch's pre-`tid` sidecar write at `:62-67`
does **not** get `execution_id`/`provider` even though a raw `ticketId` string is already known
at that point, because that `ticketId` is unvalidated (not yet confirmed to correspond to a real
ticket by the `ticket-scoper` agent). `execution_id` is defined to exist only after `tid` is
confirmed real at line 202. This keeps `post_tool_hook.py`'s existing null-default handling as the
correct behavior for this path and avoids synthesizing identity for a possibly-invalid ticket.
**Do NOT touch:** `implement-ticket.js:62-70` (resume-branch sidecar write and new-ticket clear)
and `:189-194` (Scope-agent-failed fallback) — zero production edits here, ever, for this ticket.
**Verify:** `test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less` (new).

### Step 5 — Integration test: one execution shares one identity, a second gets a different one
**Files:** `tests/tools/test_execution_identity_end_to_end.py` (new)
**Change:** Add `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`.
Since this repo has no JS test runner for `.claude/workflows/*.js`, express this as a
Python-level integration test that drives `record_events.py`/`record_run.py`/`post_tool_hook.py`
directly with a shared, realistically-shaped `execution_id` (`claude-{tid}-{ts}-{hex}`),
`provider="claude"`, and `ticket_id` across a simulated multi-phase run (2+ events + 1 run record
+ 1+ `tools.jsonl` row produced via a sidecar fixture matching the new `writeSidecar` body's
shape). Assert every written line for that run shares one `execution_id` and `provider="claude"`,
and that a second simulated run (fresh `executionId` computed the same way Step 1's snippet
computes it) produces a different `execution_id` while reusing the same `ticket_id` (proves
identity is per-*execution*, not per-*ticket*).
**Do NOT touch:** `record_events.py`, `record_run.py`, `post_tool_hook.py` production code — this
test only drives them as black boxes with `--data` payloads, matching how `writeMonitoring`'s
agent prompt already invokes them.
**Verify:** `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`
(new). Maps to AC1 and AC2.

### Step 6 — Baseline prefix/manifest comparison PLUS content-correctness assertion on newly appended lines (AC6 mechanism)
**Files:** `tests/tools/test_execution_identity_end_to_end.py` (same file as Step 5, or
`tests/tools/test_agent_monitoring_manifest.py` if that file exists and its fixture pattern
fits — check first per investigation's note about not colliding with the narrowed
`validate.py`-only guard from `TCK-20260721-MONITORING-WRITER-UNIFICATION`)

**Change:** This step now has two required parts. Part A alone (byte-checksum of the pre-existing
prefix) only proves old lines are never rewritten — it says nothing about whether the *new* lines
themselves are well-formed. Part B closes that gap by actually parsing and asserting on the
content of every newly appended line. Both parts are required; neither substitutes for the other.

**Part A — prefix/manifest comparison (unchanged mechanism from the prior plan revision):**
1. In a temp/fixture copy of `agent-monitoring/{runs,events,tools}.jsonl`, seed N pre-existing
   lines (representing legacy, identity-less records).
2. Snapshot: line count (`wc -l`-equivalent) and a SHA-256 checksum of the exact first-N-lines
   byte content, per file.
3. Append new identity-bearing records (using the same `record_events.py`/`record_run.py`/sidecar
   flow as Step 5) via the real writer tools.
4. Re-snapshot: assert the first N lines are byte-identical to the pre-snapshot checksum (proves
   no rewrite of pre-existing lines), and assert the new line count is exactly N + (number of
   appended records) (proves pure append, no in-place mutation, no dropped lines).

**Part B — content-correctness assertion on the newly appended lines (NEW, added in this
revision to resolve architecture-review's NEEDS_CHANGES finding):**
For each of the newly appended lines (lines N+1..N+k from Part A's Step 3 append), run two
independent checks — a naive `json.loads(line)` alone is not sufficient here, because Python's
standard JSON decoder silently collapses duplicate keys (last value wins), which would hide
exactly the failure mode this check exists to catch (e.g. a botched merge where `run_id` gets
written twice, or where the new `ticket_id`/`execution_id` insertion accidentally overwrites
`run_id`'s value within the same object):
1. **Duplicate-key detection**: parse the raw line with a duplicate-key-sensitive hook, e.g.
   `json.loads(line, object_pairs_hook=lambda pairs: _reject_if_duplicate_keys(pairs))` where the
   hook raises/fails the assertion if any key name appears more than once in the `pairs` list for
   that object. Additionally, as a belt-and-suspenders raw-text check, regex/substring-count each
   of `"execution_id":`, `"provider":`, `"ticket_id":`, `"run_id":` in the raw line and assert each
   count is exactly 1 — this catches malformed-but-still-parseable JSON where a key was
   duplicated inside a way `object_pairs_hook` might not isolate (e.g. nested under an unexpected
   key).
2. **Value correctness**: from the successfully-parsed (single-valued) record, assert
   `record["run_id"]` equals the pre-existing/expected `run_id` convention for that record (i.e.
   `tid`, unchanged from today — proves the new fields did not clobber it), `record["execution_id"]`
   equals the one `executionId` generated once in Step 1 and shared across the whole simulated run,
   `record["provider"]` equals exactly `"claude"`, and `record["ticket_id"]` equals `tid`. All four
   values must be non-empty/non-null.
This applies to **both**:
- **The synthetic fixture test** (new `test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values`,
  same file as Part A) — runs the duplicate-key-hook parse + regex-count + value-correctness
  assertions against every line appended in Part A's Step 3.
- **The real controlled-validation run**, recorded in this ticket's own Implementation Notes. The
  Verify-phase manual check must not stop at `wc -l`/line-count comparison — it must actually open
  and read each newly appended real line from `agent-monitoring/{runs,events,tools}.jsonl`, run
  the same exactly-once-key-count + value-correctness check (by hand or via a small one-off
  script — does not need to be a pytest artifact, but must be performed and its result recorded),
  and explicitly state in Implementation Notes that (a) `run_id` was not overwritten by the new
  `execution_id`/`provider`/`ticket_id` fields in any new line, and (b) `provider`, `execution_id`,
  and `ticket_id` are each singular (appear exactly once) and correctly valued in every new line.
  A line-count-only manual check ("N new lines appeared, byte-prefix unchanged") is **not**
  sufficient to close this step.

**Do NOT touch:** The real `agent-monitoring/{runs,events,tools}.jsonl` files directly with any
destructive operation (no rewriting, no `git checkout` of them, no manual edits) — only ever
append via the real writer tools, consistent with the append-only contract in
`docs/ai/monitoring_writer_decision.md`.

**Verify:** `test_baseline_prefix_unchanged_after_new_identity_writes` (new, Part A) and
`test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values` (new, Part B) plus
the real before/after checksum comparison **and** the real per-line content-correctness read-check,
both recorded manually during this ticket's own Verify phase. Maps to AC6.

### Step 7 — Legacy `claude-code` token: tolerated on read, never emitted on write
**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py`;
`tests/tools/test_current_run_sidecar_orchestrator.py` (merge into Step 3's test)
**Change:** Add `test_provider_claude_code_legacy_value_tolerated_not_normalized_as_new_write`,
split in two parts: (a) in `test_agent_ops_dashboard_ingest.py`, feed a synthetic legacy-shaped
row with `"provider": "claude-code"` through `ingest.py`/`load_jsonl` and assert it parses without
error (tolerant pass-through, no normalization) — this is a synthetic fixture, not a claim that
real historical data ever had this value (investigation confirmed the corpus has zero
provider-bearing records today); (b) in `test_current_run_sidecar_orchestrator.py` (can merge
into Step 3's test), a static-source assertion that the string `"claude-code"` does not appear
anywhere inside the new code this ticket adds to `implement-ticket.js` (only `"claude"` is ever
constructed as a value).
**Do NOT touch:** `docs/ai/monitoring_writer_decision.md`'s or
`docs/ai/shadow_promotion_gate_thresholds_decision.md`'s illustrative `claude-code` prose (quoted
verbatim, consumed-as-input, not in this ticket's scope). Do NOT touch
`tools/retrieval_event_parity_check.py`'s `_KNOWN_PROVIDER_TOKENS` — unrelated subsystem
(shadow context-packet retrieval-event field-collision guard), out of scope. Do not add any
normalization/aliasing function anywhere — investigation confirmed none is needed since nothing
emits the legacy token and no historical data carries it.
**Verify:** `test_provider_claude_code_legacy_value_tolerated_not_normalized_as_new_write` (new,
both parts). Maps to AC3.

### Step 8 — Update docs to satisfy the doc-staleness gate and keep the activation tracker accurate
**Files:** `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`;
`agent-orchestration/intentional-divergences.md`
**Change:** In `current_codex_runtime_status_and_activation_plan.md` Section 5's status table,
update the "Execution identity" row from "Schema supported, not supplied by real Claude/Codex
writes — Not operational" to reflect that real Claude `implement-ticket` writes now supply
`provider="claude"`/`execution_id`/`ticket_id` (Codex remains not-operational — out of scope here,
do not claim Codex activation). Update the "Current limitation" bullet that currently reads "Real
Claude workflow records do not currently supply `provider` or `execution_id`" to no longer claim
this for Claude. In `agent-orchestration/intentional-divergences.md`, update the "Known
Configuration Gaps" note that references this same limitation. **This step is required, not
optional** — `tools/gate_checks/doc_staleness_check.py::check_doc_staleness` FAILs
(`DOC_STALENESS_BLOCKED`) when `behavior_changed=true`, `.claude/workflows/implement-ticket.js`
is a changed path, and zero changed paths start with `docs/`; the `agent-orchestration/` file
alone does not satisfy this gate.
**Do NOT touch:** Any other section of `current_codex_runtime_status_and_activation_plan.md`
describing Codex status (out of scope per ticket). Do not touch
`docs/ai/monitoring_writer_decision.md` (source-of-truth design doc this ticket implements
verbatim, not redefines) or `docs/architecture/agent_orchestration_contract.md` (marks execution
identity "Consumed-as-input" — this ticket doesn't change the field shape, only activates it).
**Verify:** Manual Verify-phase check (per test_plan.md's "Doc-staleness gate guard") that both
files are present among `files_changed` when `implement-ticket.js` changes with
`behavior_changed=true`; no automated pytest covers doc prose content itself.

### Step 9 — Parity ledger follow-up notes on INFRA-275 and INFRA-281
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a follow-up evidence note to `INFRA-275` (status stays `verified`, P2) stating
that this ticket is the first to make the dashboard's already-built `provider`/`execution_id`/
`ticket_id` fields carry real data from a live Claude `implement-ticket` run, with a pointer to
this ticket's `execution_id`. Append a follow-up note to `INFRA-281` (status stays `verified`, P2)
stating that `writeSidecar`'s body was extended again (this ticket adds `execution_id`/`provider`
via closure, `TCK-20260719-LIVE-PHASE-AGENT-LABEL`'s `phase`/`agent` widening remains accurate),
with a pointer to the new argv shape. Do not change either entry's `status` field or invent a new
`test_path` gate — neither is P0 and neither requires one.
**Do NOT touch:** Any other entry in `infrastructure.yaml`, or any other parity ledger file. Do
not create a new ledger entry — both existing entries already cover this function/field surface
and only need supplementary evidence, per investigation.
**Verify:** No automated test; this is a documentation-parity step performed during this ticket's
own Parity phase, consistent with the Authoritative Mechanics Rule's parity requirement (docs and
ledger stay in sync with what's operationally true).

## Scope Guards

Explicit list of things this plan must NOT touch, derived from the ticket's Out of Scope and the
investigation's Anti-Drift Hazards:

- Any Codex runtime, hook registration, or Codex monitoring writer code (ticket Out of Scope).
- Shared-sidecar concurrency across unrelated workflows — no locking/coordination changes (ticket
  Out of Scope).
- Historical JSONL backfill, migration, or rewriting of any existing line in
  `agent-monitoring/{runs,events,tools}.jsonl` (ticket Out of Scope; also directly enforced by
  Step 6's baseline-prefix test).
- Dashboard field semantics beyond established additive reader behavior — no new filtering
  behavior, no schema redefinition in `models.py`/`ingest.py` (ticket Out of Scope; these files
  are already correct per investigation and are not touched by this plan).
- `tools/agent-monitoring/post_tool_hook.py`, `record_events.py`, `record_run.py` — signatures,
  `REQUIRED` sets, and merge semantics stay exactly as-is; investigation proved these already
  support the new fields via generic pass-through and pre-existing green tests.
- `writeSidecar`'s declared parameter list — must remain exactly `(seq, phase, agent)`. New
  fields go in via closure only, never by widening the signature (would require touching all 10
  call sites and risks call-site drift; also breaks
  `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`'s literal
  signature match).
- Any of the 15 `writeMonitoring(...)` or 10 `writeSidecar(...)` call sites themselves — only the
  two function bodies change.
- The Scope-agent-failed fallback (`:189-194`) and the Scope-phase resume-branch's pre-`tid`
  inline sidecar write (`:62-67`) and new-ticket clear (`:69`) — all three stay identity-less by
  explicit decision (Step 4).
- `writeMonitoring`'s Step 0-1-2-3 structure, ordering, and label count — only Steps 2/3's JSON
  *content* changes.
- `classifyChecklistFailure` (`:287-312`) and `check_tag_drift` (`:1383-1402`) — confirmed by
  investigation to be pure read/classify calls, not real disk-write sites; zero changes needed,
  zero changes planned. (This also fully answers `TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP`'s
  question — that ticket's own closure is not this ticket's job.)
- `check_tag_drift`'s and `check_monitoring_write_recorded`'s post-`writeMonitoring('DONE')`
  `pushEvent` calls — must remain non-flushing; do not add a second `writeMonitoring`/
  `record_run.py`/`record_events.py` call after them.
- `docs/ai/monitoring_writer_decision.md` and `docs/architecture/agent_orchestration_contract.md`
  — both are consumed-as-input design docs this ticket implements verbatim, not sources to edit.
- `tools/retrieval_event_parity_check.py`'s `_KNOWN_PROVIDER_TOKENS` — unrelated subsystem, out of
  scope.
- `record_events.py`'s and `record_run.py`'s `REQUIRED` field sets — must never gain
  `provider`/`execution_id`/`ticket_id` (would break `implement-epic`, `create-tickets`, and any
  other caller that doesn't populate them).

## Dependency Map

- **Step 1** is a hard prerequisite for **Step 2** and **Step 3** (both need `executionId`/
  `PROVIDER` in closure scope).
- **Step 2** and **Step 3** are independent of each other (different function bodies) — either
  order is fine, both depend only on Step 1.
- **Step 4** is independent of Steps 2/3's content but is most meaningful once they exist (proves
  the boundary held); can be written in parallel with Step 1-3 and simply re-run after.
- **Step 5** and **Step 6** are Python-level integration tests that drive the writer tools
  directly (not the JS file) — they do not have a hard code dependency on Steps 1-3 landing, but
  they exist to validate the exact shape those steps produce, so sequence them after Steps 1-3 for
  a meaningful review order.
- **Step 7** is independent; can be done any time.
- **Step 8** (docs) has no code dependency but must land in the same commit/session as Steps 1-3
  to avoid `DOC_STALENESS_BLOCKED` at this ticket's own Implement/Finalize gate.
- **Step 9** (parity ledger) is independent; typically performed during this ticket's own Parity
  phase, after Steps 1-3 are implemented and understood.
- Steps 5 and 6 should land before this ticket's own Verify phase, since Step 6's real
  before/after checksum comparison (Part A) **and** its real per-line content-correctness
  read-check (Part B) against `agent-monitoring/*.jsonl` are both AC6 evidence and need the
  Step 1-3 code already active in this ticket's own remaining workflow phases.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A controlled Claude `implement-ticket` execution appends coherent `provider`, `execution_id`, `ticket_id`, and `run_id` values to relevant new tools, events, and run records. | Steps 1, 2, 3 (code); Step 6 (real-run evidence, both Parts A and B) | `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources` (Step 5); `test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values` (Step 6 Part B) — "coherent" is specifically what Part B's exactly-once-key + value-correctness check proves, not just Part A's byte-prefix check; real before/after checksum AND real per-line content-correctness read-check recorded in Step 6 |
| Every record from one execution uses the same non-empty execution ID; a subsequent execution receives a different ID. | Steps 1, 2, 3 | `test_execution_id_generated_once_and_reused_across_events` (Step 1); `test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources` (Step 5) |
| New workflow writes use exactly `provider="claude"`; tests define the intended treatment of legacy `claude-code` input without allowing it as a new-write alternative. | Steps 1, 3, 7 | `test_writeMonitoring_prompt_embeds_execution_id_provider_ticket_id_in_events_and_run_record` (Step 3); `test_provider_claude_code_legacy_value_tolerated_not_normalized_as_new_write` (Step 7) |
| The no-ticket Scope and scope-failure paths remain identity-less rather than emitting an invalid ticket/execution identity. | Step 4 (explicit decision, no code change) | `test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less` (Step 4) |
| Existing sidecar adjacency, pause/resume sequence, tool-count attribution, reader/dashboard legacy normalization, and non-blocking writer behavior remain covered and green. | Steps 2, 3 (body-only edits preserve all existing structure) | Full existing regression suite in test_plan.md's Regression Surface, especially `test_sidecar_bash_write_precedes_each_covered_agent_call`, `test_writeMonitoring_step0_sidecar_clear_precedes_other_steps`, `test_execution_identity_fields_included_when_sidecar_present`, `test_load_jsonl_handles_all_legacy_shapes_plus_new_execution_identity_format` |
| Baseline verification proves all pre-existing monitoring JSONL lines/bytes remain unchanged, AND the newly appended lines are themselves well-formed (no duplicate/colliding identity keys, no `run_id` overwrite). | Step 6 (Part A: prefix/manifest; Part B: content-correctness on new lines) | `test_baseline_prefix_unchanged_after_new_identity_writes` (Step 6 Part A, synthetic) + `test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values` (Step 6 Part B, synthetic) + real checksum comparison AND real per-line content-correctness read-check, both recorded during this ticket's own Verify phase |

## Anti-Drift Notes

- **Closure, not parameter widening.** Every new field on `writeSidecar` and `writeMonitoring`
  must be threaded via closure over `executionId`/`PROVIDER` (the same idiom `tid` already uses),
  never by adding parameters. `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`
  does a literal string match on `"const writeSidecar = async (seq, phase, agent)"` — widening the
  signature breaks this test and requires touching all 10 call sites, which this plan is
  specifically designed to avoid.
- **Argv append order matters byte-for-byte.** New argv elements in `writeSidecar`'s bash template
  literal must be appended strictly after `"${agent}"`. The existing substring `'"${tid}" "${seq}"
  "${phase}" "${agent}"'` must remain unbroken — `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`
  does a substring match, not a semantic one.
- **`REQUIRED` sets are load-bearing for other workflows.** Do not add `provider`/`execution_id`/
  `ticket_id` to `record_events.py`'s or `record_run.py`'s `REQUIRED` field sets — `implement-epic`
  and `create-tickets` don't populate them and would start failing.
- **Step 0-1-2-3 structure in `writeMonitoring` is pinned.** Only the JSON *content* inside Steps
  2 and 3 changes; the step count, labels, and Step-0-clears-first ordering must not move.
- **Doc-staleness gate needs a real `docs/` path.** `agent-orchestration/intentional-divergences.md`
  alone will NOT satisfy `check_doc_staleness` — Step 8's edit to
  `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md` is
  the one that actually clears the gate.
- **Post-`DONE` `pushEvent` calls (`check_tag_drift`, `check_monitoring_write_recorded`) must stay
  non-flushing.** Do not "fix" them by adding a second `writeMonitoring` call — this would
  double-write a `DONE`-equivalent run record, violating the established advisory-only pattern.
- **No real historical `provider` data exists yet.** Step 7's `claude-code` tolerance test must be
  built as a synthetic fixture, not framed as replaying real corpus data — the investigation
  confirmed the current corpus has zero provider-bearing records.
- **This ticket's own workflow execution is the controlled validation run.** Step 6's real
  before/after checksum comparison (Part A) should be taken across this very ticket's own
  Implement → Verify phases (the first real writes to carry `provider="claude"`), not a separate
  throwaway ticket — record both snapshots in the ticket's Implementation Notes section as the
  evidentiary artifact for AC1/AC6. **This is not sufficient on its own**: Implementation Notes
  must also record the Part B per-line content-correctness read-check (each new line actually
  opened and parsed, not just counted), confirming `run_id` was not overwritten and that
  `provider`/`execution_id`/`ticket_id` each appear exactly once with correct values in every new
  line. A checksum-only Implementation Notes entry does not close Step 6.
- **`json.loads` alone hides duplicate keys.** Step 6 Part B must use a duplicate-key-sensitive
  parse (`object_pairs_hook`) plus a raw-text occurrence count for each identity field name — a
  plain `json.loads(line)["execution_id"]`-style assertion would silently pass even if the
  LLM-constructed JSON contained a duplicate/colliding key, because Python's decoder keeps only
  the last value for a repeated key. This is the specific gap architecture-review flagged; do not
  regress it back to a value-only check.
