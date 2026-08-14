---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-PACKET-CALL-SITE
artifact_type: plan
tags: [workflows, agent-monitoring, observability]
---

# Implementation Plan — TCK-20260729-SHADOW-PACKET-CALL-SITE

## Summary

This is a revised plan superseding the previous version after an architecture-review
`NEEDS_CHANGES` verdict. The overall approach is unchanged: add exactly one orchestrator-side
`bash()` call inside `.claude/workflows/implement-ticket.js`'s Investigate phase that
shadow-builds a `ContextPacket` via `tools/retrieval_events.py::wrap_context_packet_assembly()`
(which itself calls `tools/context_packet_assembler.py::assemble_context_packet()`), strictly
advisory, off by default, fail-open. What changes in this revision is **only how the shadow
event's `seq` value is computed**. The previous plan computed `seq` as
`events.length + 1 + seqOffset` (the same expression `pushEvent`/`writeSidecar` use everywhere
else in the file), reasoning that placing the call after Investigate's own `pushEvent` would give
it a value one greater than Investigate's own event. That reasoning was wrong: the shadow write
goes directly to `events.jsonl` via `emit_retrieval_event()`, entirely bypassing the JS `events`
array, so `events.length` never advances because of it — the very next real phase (Plan) then
independently evaluates the identical expression against the same, still-unchanged
`events.length`, producing the same `seq` value and colliding with the shadow event on
`(run_id, seq)` on every standard-tier run. This revision replaces that expression with a
**monotonic negative counter**, computed entirely independently of `events.length`/`seqOffset` by
scanning `agent-monitoring/events.jsonl` for prior `context-packet-wrapper` rows for this
`run_id`: `seq = -(1 + prior_shadow_count_for_this_run_id)`. Every real per-phase `seq` in this
file is provably `>= 1` (`events.length >= 0`, `seqOffset >= 0` per
`tools/agent-monitoring/seq_offset.py::compute_seq_offset()`, which starts at 0 and only rises),
so any `seq <= 0` is mathematically guaranteed disjoint from every real phase's seq for the run,
independent of placement, run length, or resume count. This is a stronger, provable guarantee, not
a practically-bounded heuristic. All other mechanics from the original plan are unchanged: the
call is gated behind `SHADOW_CONTEXT_PACKET_ENABLED=1` (shell-side strict-equals check), wrapped
in `timeout 10s`, fully fail-open at both shell and Python level, uses an empty candidate set, and
passes the real ticket's `tid` as `run_id`. `docs/agent-monitoring/schema.md` gets two edits in
this revision instead of one: the Provenance-section correction (as before, now also describing
the negative-seq scheme) plus a new one-sentence carve-out on the `seq` field's own table row,
since that row's "1-based, monotonically increasing" wording is now technically inaccurate for
this one wrapper's rows.

## Deviations from Original Plan

The original plan's Step 1 computed the shadow call's `seq` as
`${events.length + 1 + seqOffset}`, placed textually after `pushEvent('Investigate', ...)` so
that `events.length` would "already reflect Investigate's own just-pushed event." An
architecture-review gate returned `NEEDS_CHANGES` because this reasoning conflated two different
seq-producing mechanisms: `pushEvent`'s `events.length + 1 + seqOffset` is only meaningful because
`pushEvent` itself grows the JS `events` array immediately after computing it — the shadow call's
write path (`emit_retrieval_event()` → `write_lines()` directly against
`agent-monitoring/events.jsonl`) never touches that array at all, so the "same expression"
computed by the shadow call and by Plan's subsequent `writeSidecar` call evaluate against the
identical, unchanged `events.length` and produce the identical `seq` value — a real
`(run_id, seq)` collision between the shadow event and Plan's own real event, on every
standard-tier run, regardless of where in Investigate the call is textually placed. The fix
(adopted directly from investigation.md's resolved recommendation, not re-derived here) is to stop
sharing any expression with `pushEvent`/`writeSidecar` at all: derive the shadow `seq` from an
independent, monotonically negative counter — provably `<= 0`, hence provably disjoint from the
real per-phase range (`>= 1`) for the entire run. This revision also adds the regression test the
review flagged as missing (test_plan.md item 11,
`test_shadow_event_seq_never_collides_with_any_real_phase_seq`) and a second `schema.md` edit
(the `seq` field-table carve-out) alongside the already-planned Provenance-section correction.

## Steps

### Step 1 — Add the shadow-packet bash() call site to implement-ticket.js's Investigate phase

**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Insert one new `await bash(...)` statement immediately after the existing line

```js
pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), investigationTs)
```

(current line 478), and before the blank line / `// ─── Phase 3: Plan ───` comment that follows
it (current line 480). Do not touch any text on or between lines 441-478 (the
`writeSidecar`→`agent()` adjacency and the `pushEvent('Investigate', ...)` call itself). The new
statement:

```js
// Shadow context-packet call site (TCK-20260729-SHADOW-PACKET-CALL-SITE): advisory-only,
// opt-in instrumentation of assemble_context_packet() via wrap_context_packet_assembly().
// Placed strictly after pushEvent('Investigate', ...) — never between writeSidecar(...) and
// the agent() call above (see test_current_run_sidecar_orchestrator.py's exact-adjacency
// guard). Placement here is for adjacency-safety only; it has NO bearing on seq math (see
// below) — do not reintroduce that conflation.
//
// seq: computed as a monotonic NEGATIVE counter, entirely independent of this file's
// `events.length`/`seqOffset` — NEVER reuse the `events.length + 1 + seqOffset` idiom here.
// This write goes directly to agent-monitoring/events.jsonl via emit_retrieval_event(),
// bypassing the JS `events` array entirely, so `events.length` never advances because of it;
// reusing that expression silently aliases onto whatever the next real phase's own
// pushEvent/writeSidecar independently computes from the same, unchanged `events.length` —
// this is the exact defect an architecture-review NEEDS_CHANGES verdict caught. Every real
// per-phase seq in this file is provably >= 1 (events.length >= 0, seqOffset >= 0 per
// seq_offset.py::compute_seq_offset(), which starts at 0 and only rises) — so any seq <= 0 is
// mathematically guaranteed disjoint from the real range for this run, regardless of
// placement, run length, or resume count. The Python script below computes
// seq = -(1 + prior_shadow_count_for_this_run_id) by scanning events.jsonl for prior
// agent=="context-packet-wrapper" rows matching this run_id (mirrors seq_offset.py's own
// resume-lookup precedent, filtered to shadow rows and negated) — this handles Investigate
// itself re-running across a resumed session (as this very ticket has done) without two
// shadow events colliding with each other, in addition to never colliding with any real event.
//
// Gated behind SHADOW_CONTEXT_PACKET_ENABLED=1 (strict string equality, off by default,
// shell-side only — no .claude/workflows/*.js file reads process.env today and this call
// should not be the first to do so). Wrapped in `timeout 10s`; fully fail-open at both the
// shell level (2>/dev/null || true, matching writeSidecar's existing convention) and the
// Python level (try/except: pass) so a hang/crash/non-zero exit can never change this phase's
// pushEvent status or the workflow's return value. Empty candidate set — no real retrieval
// pipeline wired in (tools/hybrid_retrieval.py wiring is explicitly deferred to a follow-up
// ticket).
await bash(
  `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]; then timeout 10s python3 -c "
import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, 'tools/agent-monitoring')
from retrieval_events import wrap_context_packet_assembly
from validate import load_jsonl
import record_events
try:
    run_id = sys.argv[1]
    prior_shadow_count = sum(
        1 for e in load_jsonl(record_events.EVENTS_FILE)
        if e.get('run_id') == run_id and e.get('agent') == 'context-packet-wrapper'
    )
    shadow_seq = -(1 + prior_shadow_count)
    wrap_context_packet_assembly(
        seq=shadow_seq,
        summary='shadow packet build for Investigate phase',
        run_id=run_id,
        packet_id='shadow-investigate-' + run_id,
        corpus_generation='shadow',
        retrieval_version=1,
        budget_requested=0,
        included_candidates=[],
    )
except Exception:
    pass
" "${tid}" 2>/dev/null || true; fi`
)
```

Notes for the implementer:
- The `seq` argument (`shadow_seq`) is computed entirely inside the Python script from a read of
  `agent-monitoring/events.jsonl` — it must never reference the JS `events.length` or `seqOffset`
  variables, and must not be interpolated from the JS side at all (unlike the previous plan's
  `${events.length + 1 + seqOffset}` template interpolation, which is the exact defect being
  fixed).
- `load_jsonl` (from `tools/agent-monitoring/validate.py`) and `record_events.EVENTS_FILE` are
  both already-published, already-tested functions/constants — reused here read-only, not
  modified. Neither `tools/retrieval_events.py` nor `tools/agent-monitoring/seq_offset.py` is
  edited by this ticket; the counting logic lives entirely inside this new inline script, keeping
  `retrieval_events.py` workflow-unaware exactly as
  `test_retrieval_event_wrapper_single_source.py` requires.
- `"${tid}"` is passed as a single, individually-quoted shell argv element (`sys.argv[1]` inside
  the Python script) — matching the file's established argv-passing convention (never
  interpolating `tid` directly into the Python source string).
- The result of `await bash(...)` is deliberately not captured into any variable used later —
  there is nothing to parse (unlike `tagCheckOutput`/`docStalenessOutput`/`archCheckOutput`,
  which return JSON for the JS side to act on); this call's only effect is the durable
  `events.jsonl` row `emit_retrieval_event()` writes internally, if it runs at all.
- Do not reformat the template literal in a way that breaks the `if [ ... ]; then ... ; fi` shell
  syntax or splits the `python3 -c "..."` quoting.

**Do NOT touch:** Any text on lines 441-478; the Plan phase block starting at the `phase('Plan')`
call; `tools/retrieval_events.py`, `tools/context_packet_assembler.py`, or
`tools/agent-monitoring/seq_offset.py` (all are called only via their already-published public
functions/constants, never edited); any `agent()` template-literal prompt string anywhere in the
file; `pushEvent`'s or `writeSidecar`'s own `events.length + 1 + seqOffset` computation (must
remain byte-for-byte as-is everywhere else in the file).

**Verify:** `tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`
must still pass unmodified (regression check that the adjacency string is untouched) — run this
immediately after making the edit, before writing Step 2's new tests, as a fast sanity check.

---

### Step 2 — Add tests/tools/test_shadow_packet_call_site.py (including the seq-non-collision regression test)

**Files:** `tests/tools/test_shadow_packet_call_site.py` (new file)

**Change:** Create the new static-source-parsing test module per test_plan.md's "New Tests
Required" list, items 1-8, 10, and **11 (new in this revision)**. Item 9 is handled in Step 3. All
static-source tests read `.claude/workflows/implement-ticket.js` via `Path.read_text()` (never
execute the file), following the exact technique `test_current_run_sidecar_orchestrator.py`
already uses.

1. `test_call_site_present_and_invokes_wrap_context_packet_assembly` — assert the source contains
   both `wrap_context_packet_assembly` and `context_packet_assembler`-or-`assemble_context_packet`
   inside the Investigate phase block (text span between the `phase('Investigate')` call and the
   `phase('Plan')` call).
2. `test_call_site_does_not_break_writesidecar_agent_adjacency` — assert the exact string
   `"  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')\n  investigation = await agent("`
   still appears verbatim, AND assert the new shadow-packet call's text index is strictly greater
   than the index of `pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), investigationTs)`.
3. `test_call_wrapped_in_timeout_and_env_var_gate` — assert `timeout 10s` (or `timeout` followed
   by `python3` on the same call) appears, AND assert
   `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]` (strict equality, not a truthy/`-n` check)
   appears immediately guarding that call.
4. `test_forcing_failure_or_timeout_does_not_change_investigate_pushevent_or_return_value` — static
   half: assert the call ends in `2>/dev/null || true` before the closing `fi`. Behavioral half
   (Python-level): monkeypatch `context_packet_assembler.assemble_context_packet` to raise, call
   `wrap_context_packet_assembly(...)` through the same kwargs this ticket passes, and assert the
   exception propagates only as far as would be caught by the `python3 -c` script's own
   `except Exception: pass` — confirming the fail-open guarantee comes from this ticket's own
   inline `try/except`, not from `wrap_context_packet_assembly()` itself.
5. `test_no_shadow_packet_call_when_env_var_unset` — extract the exact command string via regex
   from the file, run it in a subprocess with `SHADOW_CONTEXT_PACKET_ENABLED` unset (and a scoped
   `tid` substituted), and assert no `events.jsonl` row is appended / no `python3` process launches
   (the shell `if` should short-circuit before reaching `timeout`).
6. `test_no_packet_variable_in_any_agent_prompt_backtick_literal` — parse each `agent(\`...\`)`
   call's literal body (balanced-backtick scan) and assert none contains `packet`,
   `ContextPacket`, `wrap_context_packet_assembly`, or `assemble_context_packet` — distinct from
   asserting these strings don't appear in the file at all (they legitimately appear inside the
   new orchestrator-only `bash()` call added in Step 1, which is not an `agent()` prompt).
7. `test_real_run_id_passed_and_phase_field_unchanged` — assert the command string references
   `"${tid}"` (or the JS `tid` variable) as an argv element passed into the script, AND assert
   `tools/retrieval_events.py`'s source still contains `phase="Retrieval"` and
   `AGENT_PACKET = "context-packet-wrapper"` verbatim (regression proof this ticket's diff does
   not touch that file).
8. `test_minimal_candidate_set_no_hybrid_retrieval_import` — assert the new call's command string
   contains no reference to `hybrid_retrieval` or `hybrid_fuse_and_filter`, and does contain
   `included_candidates=[]`.
10. `test_no_new_field_in_retrieval_event_fields` — reuse
    `TestFieldShapeConstant::test_field_set_contains_exactly_expected_retrieval_fields`'s known
    18-member `RETRIEVAL_EVENT_FIELDS` set as a local frozenset literal and assert
    `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS` still equals it exactly, as a ticket-specific
    negative control.
11. **`test_shadow_event_seq_never_collides_with_any_real_phase_seq` (new — the specific gap the
    architecture-review NEEDS_CHANGES verdict flagged as missing).** Two required sub-checks:
    - **Static:** assert, via source-text/regex inspection of the new `bash()` call's `-c` script
      body, that the substring supplying `seq=` (`shadow_seq = -(1 + prior_shadow_count)`) does
      **not** contain `events.length` or a bare `seqOffset` reference anywhere in its
      construction, and that the expression is structurally provable as `<= 0` (a negation of
      `1 + <a count that can only be >= 0>`).
    - **Behavioral:** import `compute_seq_offset`-style fixture-building (reuse
      `tests/tools/test_seq_offset.py`'s `_event(run_id, seq)` helper shape for consistency)
      to build a synthetic `events.jsonl`-equivalent list covering: (a) a fresh run
      (`seqOffset=0`, real `seq` values `1..N` for `N` from 1 through at least 10), (b) a resumed
      run (`seqOffset=K>0`, real `seq` values `K+1..K+N`), and (c) a fixture that already
      contains **two** prior `context-packet-wrapper` rows for the same `run_id` (simulating this
      exact re-investigation scenario). For each fixture, replicate the Step 1 script's own
      computation (`shadow_seq = -(1 + count of prior context-packet-wrapper rows for run_id)`)
      against the fixture and assert `shadow_seq not in {e["seq"] for e in real_events}` in every
      case, and that a **third** shadow call against fixture (c) computes a seq (`-3`) distinct
      from the two prior shadow seqs (`-1`, `-2`) as well as from every real seq.
    Location: `tests/tools/test_shadow_packet_call_site.py`.

**Do NOT touch:** Any existing test file. This is an additive new file only.

**Verify:** `pytest tests/tools/test_shadow_packet_call_site.py -v` — all new tests pass,
including `test_shadow_event_seq_never_collides_with_any_real_phase_seq`.

---

### Step 3 — Update docs/agent-monitoring/schema.md (Provenance section correction + seq field carve-out)

**Files:** `docs/agent-monitoring/schema.md`

**Change (two edits in this one file, both required):**

**3a. Provenance-section correction** (current lines 273-291, "Provenance (`run_id`/`seq`/
`phase`/`agent`) for standalone invocations"). The sentence beginning "retrieval events are
emitted from test/manual invocations of the Phase 3 retrieval modules... **none of which are
wired into any `.claude/workflows/*.js` file**" is no longer accurate for the
`context_packet_assembler.py` wrapper specifically. Change:

- "...(`tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, `tools/context_packet_assembler.py`), none of which are wired into any `.claude/workflows/*.js` file..."

to:

- "...(`tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`), neither of which is wired into
  any `.claude/workflows/*.js` file. The third, `tools/context_packet_assembler.py`, is the one
  exception: `.claude/workflows/implement-ticket.js`'s Investigate phase carries an advisory,
  opt-in shadow-packet call site (gated behind `SHADOW_CONTEXT_PACKET_ENABLED=1`, off by default)
  that passes the real ticket's `tid` as `run_id` instead of the `RETRIEVAL-EVENT-<slug>`
  synthetic prefix described below — see TCK-20260729-SHADOW-PACKET-CALL-SITE. Because this
  wrapper's write path bypasses `implement-ticket.js`'s own JS `events` array entirely (it writes
  directly to `events.jsonl`), its `seq` value is **not** drawn from that file's
  `events.length + 1 + seqOffset` idiom — doing so would silently alias onto whatever the next
  real phase independently computes from the same, unchanged `events.length`. Instead it uses a
  monotonic **negative** counter, `seq = -(1 + prior_shadow_count_for_this_run_id)`, computed by
  scanning `events.jsonl` for prior `context-packet-wrapper` rows matching this `run_id` — provably
  disjoint from the real per-phase range (`>= 1`) for the entire run, and stable across repeated
  Investigate re-runs for the same `run_id`. Once this real-`tid`-attributed event lands,
  `vocabulary.py::infer_workflow()` resolves it to the `implement-ticket` workflow for the first
  time for one of these wrapper-emitted events, and
  `tools/agent-monitoring/validate.py::compute_drift_report()` will show `'Retrieval'` /
  `'context-packet-wrapper'` under 'Non-canonical phase/agent values' for that workflow going
  forward — this is expected and non-gating (`compute_drift_report()` never gates anything), not a
  vocabulary regression to chase."

Keep the remainder of the paragraph (the `RETRIEVAL-EVENT-<slug>` explanation for the other two
wrappers' standalone invocations, and the final sentence about `run_id`-scoped retro/dashboard
exclusion) intact — it is still accurate for those two.

**3b. `seq` field-table carve-out** (current line 137, the `Fields` table). The row currently
reads:

```
| `seq` | int | No | 1-based call order within the run. Monotonically increasing. |
```

Append one sentence to the Description cell (do not touch the `Field`/`Type`/`Nullable` columns or
any other row):

```
| `seq` | int | No | 1-based call order within the run. Monotonically increasing. **Exception:** the advisory context-packet shadow-call site (TCK-20260729-SHADOW-PACKET-CALL-SITE, see Provenance note below) emits `seq <= 0` values, deliberately disjoint from this monotonic range — never assume `seq >= 1` when reading `context-packet-wrapper` rows. |
```

**Do NOT touch:** Any other section of `schema.md` (the JSON example block above the field table,
the `status`/`reason_code`/`cost_proxy_score` sections, the `tools.jsonl` section below, the
Retrieval-event field-family table's other rows); do not add a new doc file — both of this
ticket's docs/ edits live entirely inside `docs/agent-monitoring/schema.md`'s existing field table
and Provenance paragraph.

**Verify:** `tools/gate_checks/doc_staleness_check.py::check_doc_staleness()` called with
`files_changed=[".claude/workflows/implement-ticket.js", "docs/agent-monitoring/schema.md", "tests/tools/test_shadow_packet_call_site.py"]`,
`behavior_changed=True` returns `status == "PASS"` — add this as
`test_docs_path_present_in_the_same_diff` in `tests/tools/test_shadow_packet_call_site.py`
(test_plan.md item 9).

---

### Step 4 — Full regression pass

**Files:** none changed in this step — verification only.

**Change:** Run the full regression surface named in test_plan.md to confirm nothing outside the
new call site regressed, with special attention to the seq-disjointness guard.

**Do NOT touch:** No code changes in this step. If any regression test fails, return to the
relevant earlier step (do not patch tests to make them pass without understanding why).

**Verify:**
```
pytest tests/tools/test_shadow_packet_call_site.py -v
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py \
       tests/tools/test_scope_orphan_fix.py tests/tools/test_monitoring_bypass_fix.py \
       tests/tools/test_plan_gate_static.py -v
pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_parity_check.py \
       tests/tools/test_retrieval_event_wrapper_single_source.py -v
pytest tests/tools/test_seq_offset.py -v
pytest tests/tools/test_done_checker_static.py -v
```
All must pass unmodified (per test_plan.md's Regression Surface section).
`tests/tools/test_seq_offset.py` is added to this regression run in this revision — Step 1
imports `load_jsonl`/`record_events.EVENTS_FILE` (used elsewhere by `seq_offset.py`), and although
`seq_offset.py` itself is not edited, its existing test suite is cheap, closely-related
insurance that nothing about the shared read helper's behavior was misunderstood.

## Scope Guards

Explicit list of things this plan must not touch, derived from the ticket's Out of Scope section
and investigation.md's Anti-Drift Hazards (reiterated in full for this revision):

- No promotion to default/mandatory behavior — the toggle stays opt-in and off by default
  (`SHADOW_CONTEXT_PACKET_ENABLED` must default to unset/not-`"1"` = skipped).
- No packet content (a real `ContextPacket`'s `included[]`/`excluded_summary[]`, or any candidate
  text) surfaced to any agent's real prompt/context — that is Phase 6 work, not this ticket. No
  `agent(\`...\`)` template literal anywhere in `implement-ticket.js` may reference `packet`,
  `ContextPacket`, `wrap_context_packet_assembly`, or `assemble_context_packet`.
- No `execution_id`/`provider` field, and no new `shadow_mode` (or equivalently-named) field added
  to `tools/retrieval_events.py::RETRIEVAL_EVENT_FIELDS` — the real `tid`-as-`run_id` reuse is the
  entire provenance signal, by design. `tests/tools/test_retrieval_event_parity_check.py` must pass
  unmodified.
- No live Codex pilot of any kind.
- No wiring of `tools/hybrid_retrieval.py` into this call site — the candidate set stays empty.
  Real-candidate wiring is an explicitly deferred follow-up ticket once call-site/toggle/fail-open
  mechanics are proven safe in production.
- No call site added to any phase other than Investigate — in particular, do not duplicate the
  call into Plan "for consistency," and do not touch any other phase block in
  `implement-ticket.js`.
- No modification of `wrap_context_packet_assembly()`'s hardcoded `phase="Retrieval"` or
  `agent=AGENT_PACKET` fields, and no modification of its function signature or any other code in
  `tools/retrieval_events.py` — `tests/tools/test_retrieval_event_wrapper_single_source.py` asserts
  that module's source never references `.claude/workflows`, `implement-ticket.js`, `pushEvent`,
  or `writeSidecar`; all wiring lives in `implement-ticket.js` only.
- No modification of `tools/context_packet_assembler.py` (only called via its already-published
  `assemble_context_packet()` entry point).
- No modification of `tools/agent-monitoring/seq_offset.py` — its `compute_seq_offset()` function
  and CLI entry point are reused nowhere by this ticket's diff; the shadow call's own negative-seq
  logic is self-contained inside the new inline Python script added in Step 1, not added to this
  file.
- **No changes to `pushEvent`'s or `writeSidecar`'s own `events.length + 1 + seqOffset` counting
  logic anywhere in `implement-ticket.js`** — this expression must remain byte-for-byte identical
  at all 10 existing call sites (`writeSidecar` at lines 444, 485, 566, 635, 751, 812, 961, 1053,
  1116, 1170, plus `pushEvent`'s own internal use). The shadow call's `seq` must never be derived
  from, or share any sub-expression with, this counting logic — that conflation is exactly the
  defect this revision fixes.
- No JS-side `process.env` read introduced anywhere in `.claude/workflows/*.js` — the env-var gate
  must be read shell-side (`$SHADOW_CONTEXT_PACKET_ENABLED` inside the `bash()` command string
  only).
- No insertion of the new call between `writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')`
  and `investigation = await agent(...)` — this is the single highest-risk mistake this plan must
  avoid; it must land strictly after `pushEvent('Investigate', ...)`.
- No change to `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` sets
  to "silence" the resulting drift-report lines — the drift is expected and must be documented
  (Step 3), never suppressed by adding `Retrieval`/`context-packet-wrapper` as canonical values for
  `implement-ticket`.

## Dependency Map

- Step 2 depends on Step 1 (its tests, including the new seq-disjointness test, assert against
  the exact code and exact `seq`-derivation script Step 1 adds; write Step 1 first).
- Step 3 is independent of Steps 1-2 in terms of file content (it touches only
  `docs/agent-monitoring/schema.md`), but must ship in the same commit/diff as Step 1 for the
  doc-staleness gate to pass — order relative to Step 1/2 doesn't matter, but it cannot be dropped
  or deferred to a later ticket. Step 3's text (3a and 3b) must accurately describe whatever exact
  `seq`-derivation code Step 1 ships, so verify Step 3's wording after Step 1 is final, not before.
- Step 4 depends on Steps 1, 2, and 3 all being complete — it is the final full-regression gate
  before the ticket is considered implementation-complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Investigate phase contains orchestrator-side `bash()` call invoking `assemble_context_packet()` via `wrap_context_packet_assembly()`, matching the orchestrator-only pattern | Step 1 | `test_call_site_present_and_invokes_wrap_context_packet_assembly` (Step 2) |
| Invocation wrapped in `timeout <N>s python3 ...` so a hang/crash cannot delay/block Investigate | Step 1 | `test_call_wrapped_in_timeout_and_env_var_gate` (Step 2) |
| Forcing failure/timeout does not change Investigate's `pushEvent` status or the workflow's return value | Step 1 | `test_forcing_failure_or_timeout_does_not_change_investigate_pushevent_or_return_value` (Step 2) |
| Call site skipped entirely unless `SHADOW_CONTEXT_PACKET_ENABLED=1`; unset var produces zero shadow-packet events | Step 1 | `test_call_wrapped_in_timeout_and_env_var_gate`, `test_no_shadow_packet_call_when_env_var_unset` (Step 2) |
| No packet variable/contents interpolated into any `agent()`-prompt template | Step 1 | `test_no_packet_variable_in_any_agent_prompt_backtick_literal` (Step 2) |
| Call passes real ticket's `tid` as `run_id`; `phase="Retrieval"` left unchanged | Step 1 | `test_real_run_id_passed_and_phase_field_unchanged` (Step 2) |
| Candidate list is minimal smoke-test set (here: empty); no `hybrid_retrieval.py` call in the diff | Step 1 | `test_minimal_candidate_set_no_hybrid_retrieval_import` (Step 2) |
| No field added to `RETRIEVAL_EVENT_FIELDS`; `test_retrieval_event_parity_check.py` passes unmodified | Step 1 (by construction — `tools/retrieval_events.py` untouched) | `test_no_new_field_in_retrieval_event_fields` (Step 2) + regression run of `test_retrieval_event_parity_check.py` (Step 4) |
| A `docs/` path is included in `files_changed` so the doc-staleness gate does not block the diff | Step 3 | `test_docs_path_present_in_the_same_diff` (Step 3) |
| **Reviewer-added correctness requirement (not a literal ticket AC checkbox): the shadow event's `seq` must never collide with any subsequent real phase's `seq` in the same run** | Step 1 (negative-counter `seq` derivation, independent of `events.length`/`seqOffset`) | `test_shadow_event_seq_never_collides_with_any_real_phase_seq` (Step 2) |

## Anti-Drift Notes

- The single highest-probability mistake for this ticket is placing the new call between
  `writeSidecar('Investigate', 'investigator')` and `investigation = await agent(...)` — this
  silently corrupts tool-call attribution for every future Investigate phase run (not just a loud
  test failure) if the adjacency guard test itself were also weakened at the same time. Step 1's
  placement (strictly after `pushEvent('Investigate', ...)`) is non-negotiable; Step 2's test 2
  checks both the adjacency string's continued presence and the new call's relative text position.
- **The single highest-probability mistake specific to this revision** is "simplifying" the
  `seq` argument back to the `events.length + 1 + seqOffset` idiom that appears everywhere else in
  this file — it looks visually consistent with the rest of `implement-ticket.js` but silently
  reintroduces the exact `(run_id, seq)` collision with the next real phase's event that the prior
  architecture-review gate caught. The `seq` value must always come from the independent, negative
  counter computed by scanning `events.jsonl`, never from any expression touching the JS `events`
  array or `seqOffset`. Step 2's test 11 is the guard against this regression and must run and
  pass alongside test 2 (the adjacency guard) before any other verification.
- `wrap_context_packet_assembly()`'s `run_id` parameter defaults to the synthetic
  `RETRIEVAL-EVENT-context-packet` sentinel (`RUN_ID_PACKET`) — it is easy to forget to pass
  `run_id=` explicitly and silently fall back to that default, which would defeat this ticket's
  entire purpose (real-run attribution) while still looking superficially correct (the call still
  runs, still emits an event, just under the wrong provenance). Step 1's code passes
  `run_id=sys.argv[1]` explicitly; Step 2's test 7 guards against a regression to the default.
- The vocabulary-drift side effect (Step 3's doc addition) is expected and permanent once
  `SHADOW_CONTEXT_PACKET_ENABLED=1` is used in production — do not "fix" it later by adding
  `Retrieval`/`context-packet-wrapper` to `vocabulary.py`'s canonical sets; that would misrepresent
  a deliberately distinct observation-category label as a real workflow phase/agent.
- This ticket's own diff touches `.claude/workflows/implement-ticket.js` (a behavior-changing file
  under the doc-staleness gate's watch list) — Step 3's doc edits must ship in the same commit, not
  a follow-up, or the gate will block at Implement.
- Because `.claude/current_run`'s sidecar still holds `('Investigate', 'investigator')` when this
  new `bash()` call runs (not overwritten until Plan's own `writeSidecar`), the shadow call's own
  tool-call row will be attributed to Investigate's `(run_id, seq)` in `tools.jsonl`, inflating its
  `tool_call_count`/`cost_proxy_score` slightly — this is a known, pre-existing, accepted
  characteristic already shared by `tagCheckOutput`/`docStalenessOutput`/`archCheckOutput`, not a
  new regression this ticket introduces or needs to fix.
- No consumer of `events.jsonl`/`tools.jsonl` breaks on a negative `seq` (confirmed in
  investigation.md, adopted as-is): `record_events.py::validate_record()` has no type/sign/range
  check on `seq`; `seq_offset.py::compute_seq_offset()` only takes a `max()`, so a negative value
  is always ignored; `weight_sensitivity_check.py`'s `(run_id, seq)`-keyed dicts are only ever
  looked up by real, positive, sidecar-driven keys, so the shadow entry is built but never read;
  `build_index.py`'s `seq INTEGER` SQLite column and its indexes are non-unique, non-`CHECK`-
  constrained. Do not add a `CHECK (seq >= 1)`-style constraint or similar validation anywhere as
  a "safety improvement" in this ticket — that would break the shadow event by construction and is
  explicitly out of this ticket's scope.

## Deviations (Implementer, post-approval)

- Step 2's test_plan.md item 11 specified two required sub-checks (a static seq-derivation-
  expression check and a behavioral fixture-based non-collision check) as one combined test
  function, `test_shadow_event_seq_never_collides_with_any_real_phase_seq`. The implementer split
  these into two separate test functions in `tests/tools/test_shadow_packet_call_site.py` —
  `test_shadow_call_seq_derivation_does_not_reference_events_length_or_seqoffset` (the static
  sub-check) and `test_shadow_event_seq_never_collides_with_any_real_phase_seq` (the behavioral
  sub-check, retaining the item's exact name) — for pytest failure-isolation (a static-assertion
  failure and a behavioral-fixture failure now report as two distinct, independently-diagnosable
  test names rather than one). Coverage is identical to what item 11 specified; both tests pass.
  No other deviation from this plan occurred — Step 1's code, Step 3's doc edits, and Step 4's
  regression surface all match this plan verbatim.
