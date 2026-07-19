---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-LIVE-PHASE-AGENT-LABEL
artifact_type: plan
tags: [agent-monitoring, observability, workflows]
---

# Implementation Plan — TCK-20260719-LIVE-PHASE-AGENT-LABEL

## Summary

Thread `phase`/`agent` string literals through the existing `writeSidecar(seq)` helper (→
`writeSidecar(seq, phase, agent)`) at all 10 call sites in `.claude/workflows/implement-ticket.js`,
carry them through the Scope-phase resume-branch inline sidecar write (a documented "yes"
decision, scoped to that one branch only), read and persist them in
`tools/agent-monitoring/post_tool_hook.py`'s `tools.jsonl` record, update the two test files whose
static-source-text assertions hard-code the old 1-arg signature / closed field set (6 breakage
points total across both files, 3 more than the ticket's own enumeration), and document the two
new nullable fields in `docs/agent-monitoring/schema.md`. No `src/` file changes; this is
orchestration-tooling only, matching the INFRA-274 precedent for a dedicated parity ledger entry
despite no Mechanics Bible chapter applying.

**Scope-phase decision (made here, per AC #6 — see Step 2):** add `phase='Scope'`,
`agent='ticket-scoper'` to the **resume branch only** (`if (ticketId) { ... }`) of the Scope inline
sidecar write. The new-ticket (`else`) branch's `printf '{}'` stays untouched. Rationale: the
resume branch already carries a real `run_id` (the resumed ticket ID) — adding phase/agent to it
is a direct, low-cost extension of the same JSON literal, consistent with the ticket's live-dashboard
motivation (Scope is the very first phase of every run; leaving it permanently unlabeled undermines
the feature this ticket exists to build). The new-ticket branch, by contrast, has no `run_id` at all
yet (`{}`, not `{run_id: null}`) — it represents "no run identity known," a materially different
state than "run known but phase/agent not yet threaded." Adding partial fields there (phase/agent
populated, run_id absent) would be a new, undocumented partial-record shape with no evidence any
consumer needs it, and it would additionally break `test_scope_phase_has_sidecar_coverage`'s
`printf '{}'` assertion (line 163) for zero AC-mapped benefit. Keeping the `else` branch as `{}` is
also cheaper: `post_tool_hook.py`'s existing `try/except`-wrapped `.get(...) or None` reads already
produce `phase: null, agent: null` for that state for free — no code path needs to special-case it.

## Implementation Safety — editing `implement-ticket.js` while it is the live orchestrator for this run

**This plan modifies the exact script (`.claude/workflows/implement-ticket.js`) that is currently
guiding the pipeline that spawned this Planner.** The real execution model, confirmed against
`.claude/skills/implement-ticket/SKILL.md` (not assumed from Node.js semantics — there is no Node
process running this file at all): **"Do not call the Workflow tool — it is not available. Execute
the workflow directly: 1. Read `.claude/workflows/implement-ticket.js` in full before doing
anything else. 2. Execute each phase block in order, translating JS constructs to tool calls..."**
An orchestrating Claude session reads the file once, as plain text, at the start of the run, and
manually translates each `phase()`/`agent()`/gate construct into real tool calls from that point
forward — it is not interpreted or executed as running code by any process, Node or otherwise.

Confirmed safe to edit during Implement, for the correct reason:

1. **The orchestrator already has the pipeline's structure in its own context from its initial
   read** — the Scope→Investigate→Plan→Review→Implement→...→Finalize sequence and each phase's
   call-and-gate shape were loaded once, before this ticket's Implement step ever touches the file
   on disk. Editing the file's text does not retroactively change what the orchestrator already
   read and is already acting on for phases prior to Implement (Scope/Investigate/Plan/Review, all
   already complete for this run before Implement starts).
2. **No test in scope ever executes the file.** `tests/tools/test_current_run_sidecar_orchestrator.py`'s
   own module docstring states explicitly: *"The workflow file is never executed (no JS test runner
   exists in this repo for `.claude/workflows/*.js`)"* — every assertion in that file is
   `Path.read_text()` + string/regex parsing, never a subprocess/interpreter invocation.

**Real residual risk, correctly named, not the Node-hot-reload framing this section previously
used**: if the orchestrating session's context is compacted or it re-reads
`.claude/workflows/implement-ticket.js` mid-pipeline (e.g. after a stall-and-resume, which this
long-running session has already needed more than once), it would pick up the **new**
`writeSidecar(seq, phase, agent)` signature and the 10 updated call sites for any phase it executes
*after* that re-read — including, potentially, the remainder of this very run. This is judged
acceptably safe, not escalated, because the change is purely additive (new trailing optional-shaped
args threaded consistently at every call site) and self-consistent (a stale in-context understanding
using the old 1-arg form and a fresh re-read using the new 3-arg form each independently produce a
syntactically valid call — `writeSidecar(seq)` still works after the signature adds two optional
trailing params). **Guidance for the implementer:** make the edits with the `Edit` tool (targeted
string replacement) rather than a full-file rewrite, to keep each individual edit atomic and
minimize the on-disk window where the file is a partial mix of old/new call-site shapes; if a
context refresh/resume does occur mid-Implement, re-verify the edits made so far against the
Step 1 call-site table below before continuing, rather than assuming prior progress was complete.

## Steps

### Step 1 — `writeSidecar` helper signature + all 10 call sites
**Files:** `.claude/workflows/implement-ticket.js`
**Change:**
- At the helper definition (`:202-209`, `const writeSidecar = async (seq) => { ... }`): change the
  signature to `async (seq, phase, agent)`, add `"${phase}" "${agent}"` as two more individually
  quoted argv elements after `"${tid}" "${seq}"`, and extend the embedded `python3 -c` script to
  read `sys.argv[3]`/`sys.argv[4]` and add `'phase': sys.argv[3], 'agent': sys.argv[4]` to the
  `json.dumps({...})` dict alongside the existing `run_id`/`seq` keys. Do **not** embed `${phase}`/
  `${agent}` directly inside the `-c` string — argv-only, matching the existing `tid`/`seq`
  convention (Anti-Drift Hazard in investigation.md: "Preserve the argv-quoting convention").
  Preserve the `2>/dev/null || true` fail-open suffix unchanged.
- At each of the 10 call sites (lines 419, 460, 541, 610, 679, 740, 889, 981, 1044, 1098 — relocate
  by content match, `await writeSidecar(events.length + 1)` immediately preceding each `agent(`
  call, per the ticket's own line-number-drift warning), change the call to
  `writeSidecar(events.length + 1, '<Phase>', '<agent>')` using this exact mapping (from
  investigation.md's Current Behavior table):

  | Site (current line) | Phase literal | Agent literal |
  |---|---|---|
  | 419 | `Investigate` | `investigator` |
  | 460 | `Plan` | `planner` |
  | 541 | `Review` | `architecture-reviewer` |
  | 610 | `Implement` | `implementer` |
  | 679 | `Architecture-Verify` | `architecture-reviewer` |
  | 740 | `Test` | `test-scoper` |
  | 889 | `Parity` | `parity-updater` |
  | 981 | `Security-Review` | `security-reviewer` |
  | 1044 | `Verify` | `done-checker` |
  | 1098 | `Finalize` | `finalizer` |

**Do NOT touch:** `writeMonitoring` (`:258-320`) — it must continue to never call `writeSidecar`
itself (its own tool calls stay `run_id: null`); do not add any "consistency" tracking call there.
Do not touch the Step-0 sidecar-clear-first ordering inside `writeMonitoring`. Do not touch
`pushEvent`, `classifyChecklistFailure`, or any `phase('X')`/`pushEvent(phase, agent, ...)` call
itself — only the `writeSidecar(...)` call immediately preceding each `agent()` call changes.
**Verify:** `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` (Step 4),
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` (Step 4),
`test_sidecar_bash_write_precedes_each_covered_agent_call` (Step 4),
`test_finalize_call_site_still_registers_sidecar` (Step 4).

### Step 2 — Scope-phase inline sidecar write: implement the "yes, resume-branch-only" decision
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** At the Scope inline sidecar write (`:44-53`), in the `if (ticketId) { ... }` branch
only, add `'phase': 'Scope', 'agent': 'ticket-scoper'` to the existing
`json.dumps({'run_id': sys.argv[1], 'seq': 1})` dict literal, e.g.
`json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'})`. These
are hardcoded string literals in the Python snippet (not new argv elements) — `phase`/`agent` are
constant for this branch, unlike `run_id` which is genuinely per-invocation via `sys.argv[1]`, so
no new argv plumbing is needed here (this branch has no `bash()` variable interpolation risk for
these two fields since they're not shell-substituted `${}` values).
**Do NOT touch:** the `else` branch (`printf '{}' > .claude/current_run ...`) — leave it exactly
as-is per the decision rationale in the Summary above. Do not touch anything else in the Scope
phase block (the ticket-scoper `agent()` call, its prompt text, or the `search_docs`/`graphify`
Step-0b context-warm-start instructions immediately following, which `test_scope_phase_has_sidecar_coverage`
explicitly distinguishes from this sidecar write).
**Also:** append a short rationale note to `tickets/inprogress/TCK-20260719-LIVE-PHASE-AGENT-LABEL.md`'s
`## Implementation Notes` section recording this decision and its rationale (durable record
satisfying AC #6's "explicit, documented decision" requirement — do not rely on this plan.md alone,
since plan.md moves to `stored_artifacts/` and Implementation Notes is the ticket's own permanent
record).
**Verify:** `test_scope_phase_has_sidecar_coverage` (Step 4, updated assertion).

### Step 3 — `post_tool_hook.py`: read and persist `phase`/`agent`
**Files:** `tools/agent-monitoring/post_tool_hook.py`
**Change:**
- In the existing sidecar-read `try` block (`:44-51`), which currently sets `run_id`/`seq` via
  `sidecar.get("run_id") or None` / `sidecar.get("seq") or None`, add two more lines using the same
  pattern: `phase = sidecar.get("phase") or None` and `agent = sidecar.get("agent") or None`. Keep
  them inside the same `try/except Exception: pass` block (fail-open contract: a missing/malformed
  sidecar or missing keys must degrade both new fields to `None`, never raise).
- In the `record = {...}` dict construction (`:61-70`), add `"phase": phase, "agent": agent,`
  (insert immediately after `"seq": seq,` and before `"ts": now,`, mirroring `events.jsonl`'s
  existing `seq` → `phase`/`agent` field ordering documented in `docs/agent-monitoring/schema.md`).
**Do NOT touch:** the `fcntl.flock` locking block (`:72-77`) — the lock wraps the whole
already-built `record` dict's serialization; adding keys to the dict before that point requires no
change to the lock mechanism itself (confirmed in investigation.md). Do not touch
`_input_summary`, the `duration_ms` computation, the `status` derivation, or the outer
`try/except Exception: pass` wrapper's scope.
**Verify:** `test_phase_and_agent_included_when_sidecar_present`,
`test_phase_and_agent_null_when_no_active_run` (both Step 5), plus re-run (unmodified)
`test_locking_failure_does_not_propagate`.

### Step 4 — Update `tests/tools/test_current_run_sidecar_orchestrator.py` (6 breakage points)
**Files:** `tests/tools/test_current_run_sidecar_orchestrator.py`
**Change:** Update exactly these six things — do not touch any other test in the file:
1. `_COVERED_SITE_ADJACENCY` (lines 49-60): append `, '<Phase>', '<agent>'` inside each of the 10
   `writeSidecar(events.length + 1)` substrings, using the Step 1 mapping table, e.g. entry 1
   becomes `"  await writeSidecar(events.length + 1, 'Investigate', 'investigator')\n  investigation = await agent("`.
2. `test_sidecar_bash_write_precedes_each_covered_agent_call` (line 99's counting regex): change
   `r"await writeSidecar\(events\.length \+ 1\)"` to a pattern matching the new 3-arg call shape,
   e.g. `r"await writeSidecar\(events\.length \+ 1, '[^']+', '[^']+'\)"`, keeping the `== 10`
   count assertion unchanged.
3. `test_finalize_call_site_still_registers_sidecar` (lines 119-121's regex): update
   `r"...await writeSidecar\(events\.length \+ 1\)\nawait agent\(..."` to include `, 'Finalize',
   'finalizer'` in the `writeSidecar(...)` portion of the pattern.
4. `test_tid_and_seq_passed_as_argv_not_json_embedded` → rename to
   `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`: update the helper-match
   regex (line 180) from `r"const writeSidecar = async \(seq\) => \{.*?\n\}\n"` to
   `r"const writeSidecar = async \(seq, phase, agent\) => \{.*?\n\}\n"`; add assertions for
   `'"${tid}" "${seq}" "${phase}" "${agent}"' in helper_body`, `"sys.argv[3]"`, `"sys.argv[4]"`; keep
   the existing negative assertions (no inline `'run_id':'${tid}'`-style JSON embedding) and add
   equivalent negative assertions for `phase`/`agent` (e.g. `"'phase': '${phase}'" not in
   helper_body`); keep the `"2>/dev/null || true" in helper_body` fail-open assertion.
5. `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure` (line 198-204):
   change the literal `"const writeSidecar = async (seq)"` to `"const writeSidecar = async (seq, phase, agent)"`
   at both the `source.index(...)` call (line 201) and the `source.count(...)` assertion (line 204).
6. `test_scope_phase_has_sidecar_coverage` (line 161): update the hardcoded string assertion from
   `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1}))"` to
   `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'}))"`
   (or the exact string produced by Step 2's edit — match it verbatim). Leave the `else`-branch
   assertion (`"printf '{}' > .claude/current_run 2>/dev/null || true"`, line 163) unchanged, per
   the Step 2 decision.
**Do NOT touch:** `test_no_step_0b_agent_prompt_sidecar_text_remains`,
`test_writeMonitoring_call_has_no_preceding_sidecar_write`,
`test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4`,
`test_record_events_required_fields_unchanged`, `test_all_nine_two_line_site_labels_present`, or
`test_schema_doc_no_longer_describes_agent_self_report_mechanism` (Step 6 extends this one file's
doc-assertions with a *new* test function, it does not modify this existing one) — none of these
have any dependency on the `writeSidecar` arg count or the Scope JSON shape. Do not redesign
`_COVERED_SITE_ADJACENCY`'s or `test_scope_phase_has_sidecar_coverage`'s assertion *strategy*
(exact-string/regex matching) — mechanical literal updates only, per investigation.md's Anti-Drift
Hazard #3.
**Verify:** `python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py -v` — all tests
pass, including the 6 updated above and all untouched ones.

### Step 5 — Update `tests/tools/test_post_tool_hook.py` (2 breakage points + 2 new tests)
**Files:** `tests/tools/test_post_tool_hook.py`
**Change:**
1. `_RECORD_FIELDS` (lines 23-26): add `"phase"`, `"agent"` to the set literal.
2. Extend `test_single_writer_produces_one_well_formed_line` (no sidecar file present case): add
   `assert record["phase"] is None` and `assert record["agent"] is None` alongside the existing
   `run_id`/`seq`/`duration_ms` None assertions — this is AC #2's "outside any active workflow run"
   case; do not create a separate duplicate test for it (investigation's guidance: extend, don't
   duplicate).
3. Add new test `test_phase_and_agent_included_when_sidecar_present`: write a `.claude/current_run`
   file into `tmp_path` before invoking the hook (new fixture code — no existing helper writes a
   sidecar in this file today, matching investigation's note that the "existing fixture pattern" is
   subprocess-driven but not yet sidecar-writing) containing
   `{"run_id": "TCK-X", "seq": 3, "phase": "Implement", "agent": "implementer"}`; assert the
   resulting `tools.jsonl` record has `"phase": "Implement"` and `"agent": "implementer"` (matching
   the sidecar, not null/dropped).
4. Add new test `test_phase_and_agent_default_to_none_on_partial_sidecar`: write a
   `.claude/current_run` file with only `{"run_id": "TCK-X", "seq": 3}` (old-shape sidecar, no
   `phase`/`agent` keys — simulates a stale sidecar from before this change, or a race) and assert
   the resulting record has `"phase": None, "agent": None` with no exception/non-zero exit —
   proves the fail-open contract (investigation.md Anti-Drift Hazard: "malformed/missing phase/agent
   value must degrade to null, never raise or block a tool call").
**Do NOT touch:** `test_locking_failure_does_not_propagate` — re-run unmodified as a guard that the
new fields don't change the forced-lock-failure fail-silent contract (per test_plan.md's
Anti-Drift Test Guards).
**Verify:** `python3 -m pytest tests/tools/test_post_tool_hook.py -v` — all 5 tests pass (3
existing + 2 new).

### Step 6 — Document `phase`/`agent` in `docs/agent-monitoring/schema.md`
**Files:** `docs/agent-monitoring/schema.md`
**Change:**
1. `tools.jsonl` Fields table (lines 219-228): add two new rows, following the exact
   Type/Nullable/Description convention already used for `events.jsonl`'s `tool_call_count`/
   `reason_code`/`cost_proxy_score` rows (lines 109-111):
   - `phase` | string | Yes | Workflow phase this tool call occurred during, matching the `phase`
     literal at the corresponding `writeSidecar` call site (or the Scope-phase inline write).
     `null` when the tool call occurred outside an active workflow run, or for records predating
     `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (no backfill).
   - `agent` | string | Yes | Agent identifier active during this tool call, matching the `agent`
     literal at the corresponding call site. Same nullability rules as `phase`.
2. `tools.jsonl`'s JSON example block (lines 204-215): add `"phase": "Implement", "agent":
   "implementer"` key/value pairs to the example, keeping it consistent with the updated Fields
   table (matching the pattern where `events.jsonl`'s own example already includes its documented
   fields).
3. "How tool calls are attributed to agent events" prose section (lines 234-242): add one sentence
   noting that the sidecar (and thus the `tools.jsonl` record) now also carries `phase`/`agent`,
   not just `run_id`/`seq` — light, factual addition only, not a rewrite of the section.
**Do NOT touch:** `docs/guides/agent_ops_dashboard.md` (its "Known limitation" prose at lines
173-178 becomes slightly stale but updating it is dashboard-consumption-adjacent, explicitly out of
this ticket's scope per the ticket's Out of Scope bullet 4 — leave it as a noted follow-up, not a
change here). Do not touch the `reason_code`/`cost_proxy_score`/`status` sections, or the `phase`/
`agent` value-enumeration sections under `events.jsonl` (lines ~186-196) — those already correctly
describe `events.jsonl`'s pre-existing `phase`/`agent` fields and need no change.
**Verify:** new test `test_schema_doc_documents_tools_jsonl_phase_agent_fields` (add to
`tests/tools/test_current_run_sidecar_orchestrator.py`, extending its existing `_read_schema_doc()`
static-doc-text helper rather than a new file) asserting the `tools.jsonl` Fields table contains a
`phase` row and an `agent` row each marked `Yes` nullable with a `TCK-20260719-LIVE-PHASE-AGENT-LABEL`
predating-null note. Also re-run (unmodified) `test_schema_doc_no_longer_describes_agent_self_report_mechanism`
as a guard that this edit didn't disturb its required markers.

### Step 7 — Report `behavior_changed: true` in the Implement-phase output (process step, not a code change)
**Files:** None (this is an instruction for how the Implement-phase agent's own structured report
must be filled in, not a file edit).
**Change:** When this ticket's Implement phase completes and reports its `files_changed`/
`behavior_changed` summary back to the orchestrator, `behavior_changed` **must be reported as
`true`**. Rationale (from investigation.md): none of this ticket's changed files
(`.claude/workflows/implement-ticket.js`, `tools/agent-monitoring/post_tool_hook.py`, two
`tests/tools/*.py` files, `docs/agent-monitoring/schema.md`) are under `src/`, so
`implement-ticket.js`'s Parity-phase skip condition (`:832-833`,
`implementation.files_changed.every(f => !f.startsWith('src/')) && !implementation.behavior_changed`)
will evaluate `parityNoSrcChange` to `true` — **the Parity phase (and thus the new
`infrastructure.yaml` `INFRA-281` entry) will only run at all if `behavior_changed` is correctly
reported `true`.** This is a real, observable behavior change to the monitoring data pipeline
(`tools.jsonl`'s on-disk schema gains two keys per row; `writeSidecar`'s call signature changes) —
under-reporting `behavior_changed: false` here would silently skip Parity and leave this ticket
without its parity ledger entry, breaking this repo's INFRA-274 precedent for orchestration-tooling
changes.
**Do NOT touch:** the Parity-phase skip-condition logic itself (`:832-833`) — this step is about
correctly reporting into the existing condition, not modifying the condition.
**Verify:** N/A directly (process compliance, not a testable code path) — confirmed after the fact
by checking that a `parity-updater` agent call occurred for this ticket and that
`docs/parity_ledger/infrastructure.yaml` gained an `INFRA-281` entry during the Parity phase.

## Scope Guards

- Do not change `writeMonitoring()`'s call cadence, flush timing, or add any `writeSidecar`
  tracking to `writeMonitoring`'s own `agent()` call (out of scope per ticket; would reintroduce
  the exact misattribution bug TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION fixed).
- Do not surface phase/gate *history* (pass/fail per phase before a run completes) — additive
  per-tool-call labeling only.
- Do not backfill historical `tools.jsonl` rows with `phase`/`agent` — nullable/additive only, no
  migration script, no rewrite of existing file contents.
- Do not add validation of the new `phase`/`agent` values against
  `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`is_known_agent` — explicitly out of
  scope; leave `vocabulary.py` completely untouched.
- Do not touch the Scope inline sidecar write's `else` (new-ticket) branch — stays `printf '{}'`
  exactly as-is (Step 2 decision).
- Do not touch `docs/guides/agent_ops_dashboard.md` or any dashboard-side consumption/rendering
  code (`src/api/agent_ops_dashboard/ingest.py` confirmed unaffected and untouched — its
  `phase`/`agent` derivation reads `events.jsonl`, not `tools.jsonl`).
- Do not redesign `_COVERED_SITE_ADJACENCY`'s or `test_scope_phase_has_sidecar_coverage`'s
  assertion strategy (exact-string/regex matching vs. something looser) — mechanical literal
  updates only.
- Do not loosen `test_post_tool_hook.py`'s `_RECORD_FIELDS` check from exact-set equality (`==`) to
  a subset/superset check — keep it strict per test_plan.md's anti-drift guard.
- Do not touch `record_events.py` or any `events.jsonl`-side code/tests (`test_record_events_required_fields_unchanged`
  exists specifically to guard against scope creep into that file).
- Do not modify the Parity-phase skip-condition logic in `implement-ticket.js` (Step 7 is about
  reporting into it correctly, not changing it).

## Dependency Map

- **Step 1** and **Step 2** (both edit `implement-ticket.js`) are independent of each other in
  content but should land together before Step 4, since Step 4's assertions read the final state of
  the whole file.
- **Step 3** (`post_tool_hook.py`) is independent of Steps 1/2 — it only depends on the sidecar
  *shape* (`phase`/`agent` keys), which Steps 1/2 produce but Step 3's code doesn't care which
  write path populated them.
- **Step 4** depends on Steps 1 and 2 being complete (its assertions target the post-edit source
  text).
- **Step 5** depends on Step 3 being complete (its assertions target the post-edit record dict).
- **Step 6** depends on Steps 1-3 being conceptually settled (field semantics/nullability need to
  be final before documenting them) but has no code dependency — can be done last.
- **Step 7** is a reporting instruction with no file dependency; applies at Implement-phase
  completion regardless of step order.
- Recommended execution order: **1 → 2 → 3 → 4 → 5 → 6**, with Step 7's reporting requirement kept
  in mind throughout (it's not a discrete "do this after step N" action, it's how the whole
  Implement-phase output gets summarized at the end).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `writeSidecar(seq, phase, agent)` writes all 4 keys; matching `tools.jsonl` row is non-null | Steps 1, 3 | `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`, `test_phase_and_agent_included_when_sidecar_present` |
| AC #2 — tool call outside any active run has `phase: null, agent: null` | Step 3 | extended `test_single_writer_produces_one_well_formed_line` |
| AC #3 — historical rows without phase/agent keys remain readable as None/absent | Step 3 (via `.get(...) or None` read pattern) | `test_phase_and_agent_default_to_none_on_partial_sidecar` |
| AC #4 — the 3 (really 5, in `test_current_run_sidecar_orchestrator.py`) named tests pass against the new signature | Step 4 | full `tests/tools/test_current_run_sidecar_orchestrator.py` run |
| AC #5 — schema.md documents phase/agent with the nullable/historical-null convention | Step 6 | `test_schema_doc_documents_tools_jsonl_phase_agent_fields` |
| AC #6 — explicit, documented, implemented decision for Scope's inline write | Step 2 | `test_scope_phase_has_sidecar_coverage` (updated) + Implementation Notes rationale text |

## Anti-Drift Notes

- `writeMonitoring` must never gain a `writeSidecar` call of its own — this is a guarded invariant
  (`test_writeMonitoring_call_has_no_preceding_sidecar_write`), not incidental; resist "consistency"
  edits there while touching adjacent code in Step 1.
- Preserve the argv-quoting convention for all new `writeSidecar` arguments (`"${phase}" "${agent}"`
  as separate quoted argv elements, read via `sys.argv[3]`/`sys.argv[4]`) — never JSON-embed a
  shell-interpolated value directly inside the `python3 -c "..."` string. This file has repeated
  explicit warnings about exactly this failure mode elsewhere (`p0ScanOutput`, `filesChangedArgs`).
- Preserve the fail-open contract end-to-end: `writeSidecar`'s `2>/dev/null || true` suffix and
  `post_tool_hook.py`'s outer `try/except Exception: pass` must both remain untouched in spirit — a
  malformed/missing `phase`/`agent` value degrades to `null`, never raises or blocks a tool call
  (CLAUDE.md Hard Rule: "monitoring write failure must never fail the workflow").
- Keep `_RECORD_FIELDS`'s exact-set (`==`) equality check in `test_post_tool_hook.py` — it is what
  caught this ticket's own scope gap during investigation (a test file the ticket didn't know
  existed) and is the correct forcing-function for any *future* record-shape change to require an
  explicit test touch.
- The Step 1 call-site mapping table must be applied exactly — a swapped phase/agent pair at any of
  the 10 sites (e.g. mislabeling the `Architecture-Verify` site's agent as something other than
  `architecture-reviewer`, which is intentionally the same literal as the `Review` site's agent but
  a different phase) would silently corrupt live dashboard labeling without failing any test unless
  `_COVERED_SITE_ADJACENCY` is updated with the exact same (correct) literal — double-check against
  investigation.md's Current Behavior table, not from memory.
- Step 7's `behavior_changed: true` reporting is easy to miss because every changed file is outside
  `src/` — the natural (wrong) instinct is "no src/ files changed, so behavior_changed should be
  false." Do not follow that instinct here; the monitoring data pipeline's on-disk schema is itself
  the behavior that changed.

The one open question investigation flagged for Plan to decide (Scope-phase inline write
phase/agent labeling, AC #6) is resolved above: **yes, resume branch only** — see Summary and Step
2 for the decision and full rationale. No unresolved questions remain.

## Deviations

**Third test-breakage file, found during Step 4/5 verification, not enumerated by investigation.md
or this plan:** `tests/tools/test_step0_ts_orchestrator.py` (a regression-guard file for
TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH, distinct from and not referenced by either of this
ticket's two named test files) independently hardcodes the pre-change `writeSidecar` shape in two
places:

- `_IMPLEMENT_TICKET_ADJACENCY` (9 of its 10 entries) embeds the bare
  `writeSidecar(events.length + 1)` call shape as part of a larger `captureTs()`-plus-`writeSidecar`
  adjacency string.
- `test_captureTs_helper_defined_once_after_writeSidecar` asserts
  `it_source.index("const writeSidecar = async (seq)")` as an ordering anchor.

Both broke under Step 1's 3-arg signature change, for the identical mechanical reason Step 4's
items 2/3/5 (in `test_current_run_sidecar_orchestrator.py`) did — confirmed by running the file and
observing exactly these two failures, with the other 4 tests in the file unaffected. Fixed both:
appended the same `, '<Phase>', '<agent>'` literals (Step 1's mapping table) to the 9 adjacency
entries, and updated the literal-match string to
`"const writeSidecar = async (seq, phase, agent)"`. This is the same category of change as Step 4
(mechanical literal update forced by the signature change, no design decision) — not a scope
expansion or an architectural change — so it was implemented directly rather than escalated. Full
file re-run: 6/6 passing. Recorded here per CLAUDE.md's "never silently deviate" rule; also noted
in the ticket's Implementation Notes and Files Changed.

No other deviations. All other steps were implemented exactly as specified.
