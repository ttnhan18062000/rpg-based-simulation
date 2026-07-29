---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-PACKET-CALL-SITE
artifact_type: test_plan
tags: [workflows, agent-monitoring, observability]
---

# Test Plan — TCK-20260729-SHADOW-PACKET-CALL-SITE

## Regression Surface

No JS test runner exists for `.claude/workflows/*.js` in this repo — all coverage of that file is
static, raw-source-text-parsing Python tests against `Path.read_text()`. Every test below in this
category must continue to pass unmodified against the post-change file.

**Unit / static-source-parsing (must all still pass):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — asserts the exact
  `writeSidecar(...)\ninvestigation = await agent(` adjacency string for Investigate (and the 9
  other covered sites) still appears verbatim; asserts exactly 10 `writeSidecar()` calls total.
  **This is the single highest-risk regression surface for this ticket** — any placement of the
  new call between `writeSidecar` and `agent(` breaks it immediately.
- `tests/tools/test_step0_ts_orchestrator.py` — `captureTs()` placement/adjacency guards.
- `tests/tools/test_scope_orphan_fix.py` — Scope-phase orchestrator bash() placement guards
  (unrelated phase, but same file — must not regress from an unrelated edit elsewhere in the
  file).
- `tests/tools/test_monitoring_bypass_fix.py` — null-guard/monitoring-write-before-return guards
  on `implement-ticket.js`/`implement-epic.js`.
- `tests/tools/test_plan_gate_static.py` — Plan-phase unresolved-questions gate (unrelated
  section of the same file; regression-only).

**Unit (retrieval-event / packet-assembly modules — must all still pass unmodified, no field/
signature changes expected):**
- `tests/tools/test_retrieval_events.py` — full suite, especially
  `TestWrapContextPacketAssembly::test_reason_code_and_hash_counts_match_wrapped_call_output` and
  `TestEmitRetrievalEvent::test_new_run_id_prefix_produces_no_vocabulary_warning`.
- `tests/tools/test_retrieval_event_parity_check.py` — explicit Acceptance Criterion: "passes
  unmodified." No new field may be added to `RETRIEVAL_EVENT_FIELDS`.
- `tests/tools/test_retrieval_event_wrapper_single_source.py` — asserts
  `tools/retrieval_events.py`'s source never references `.claude/workflows`,
  `implement-ticket.js`, `pushEvent`, or `writeSidecar`. This ticket must wire the call from
  `implement-ticket.js` *into* `retrieval_events.py`'s public functions, never the reverse — this
  test is the structural proof of that direction.
- Existing tests in `tests/tools/test_context_packet_assembler.py` (if present) covering
  `assemble_context_packet()`/`Candidate`/`unrated_candidate()` — regression only, no signature
  change expected.

**Integration:**
- `tests/tools/test_done_checker_static.py` — frontmatter/DoD static-check coverage; this ticket's
  own staging artifacts must satisfy it (`artifact_type` in `investigation|plan|test_plan`).
- `tests/tools/test_tag_skill_mapping_check.py` / tag-registry tests — this ticket's tags
  (`workflows`, `agent-monitoring`, `observability`) are already registered; regression-only.

**Arena-combat:** none — this ticket has zero overlap with `src/combat/` or any simulation-tick
code path.

## New Tests Required

All new tests below live in a new or extended static-source-parsing test module, following the
`test_current_run_sidecar_orchestrator.py`/`test_monitoring_bypass_fix.py` precedent
(`Path.read_text()` against `implement-ticket.js`, never executing the file). Suggested new file:
`tests/tools/test_shadow_packet_call_site.py`.

1. **`test_call_site_present_and_invokes_wrap_context_packet_assembly`**
   Category: unit / static-source guard.
   Verifies: `implement-ticket.js` contains a `bash()` call whose command string references both
   `wrap_context_packet_assembly` and `context_packet_assembler` (or equivalently imports/invokes
   `assemble_context_packet` via the wrapper), inside the Investigate phase block (i.e. between
   the `phase('Investigate')` call and the start of the Plan phase block).
   Location: `tests/tools/test_shadow_packet_call_site.py`.

2. **`test_call_site_does_not_break_writesidecar_agent_adjacency`**
   Category: architecture guard (regression-prevention, ticket-specific).
   Verifies: the exact adjacency string
   `"  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')\n  investigation = await agent("`
   still appears in the file (duplicates the existing
   `test_current_run_sidecar_orchestrator.py` assertion locally, so a failure here is caught by
   its own name rather than an unrelated-looking test file), AND the new shadow-packet call's
   text position in the source is strictly *after* the `investigation = await agent(` call's
   closing (i.e. after `investigationText = investigation.toString().trim()` or later), never
   between `writeSidecar` and `agent(`.
   Location: `tests/tools/test_shadow_packet_call_site.py`.

3. **`test_call_wrapped_in_timeout_and_env_var_gate`**
   Category: unit / static-source guard.
   Verifies: the command string contains `timeout` immediately preceding the `python3` invocation,
   AND is conditioned on `SHADOW_CONTEXT_PACKET_ENABLED` (e.g. `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]`
   or `[ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ] &&`), matching consent_gate.py's strict
   equals-`"1"` semantics (no truthy coercion) adapted to shell.
   Location: `tests/tools/test_shadow_packet_call_site.py`.

4. **`test_forcing_failure_or_timeout_does_not_change_investigate_pushevent_or_return_value`**
   Category: integration (behavioral, not static-source).
   Verifies (per Acceptance Criteria item 3): the command string ends in a fail-open suffix
   (`... 2>/dev/null || true`, matching `writeSidecar`'s established convention) so a non-zero
   exit from `timeout`/`python3` never propagates as a JS exception or changes control flow. Since
   there is no JS test runner, this is verified by asserting the exact fail-open suffix text is
   present on the new call's command string (static), plus (if a harness-level integration test is
   feasible) a scoped Python-level test that directly calls `wrap_context_packet_assembly()` with
   a monkeypatched `assemble_context_packet` that raises, confirming
   `emit_retrieval_event`/`write_lines` are never reached and no exception propagates past the
   `python3 -c` script's own explicit `except: pass`-shaped fallback (added at implementation time
   to make the *Python* side itself fail open, not only the shell wrapper).
   Location: `tests/tools/test_shadow_packet_call_site.py` (static) +
   `tests/tools/test_retrieval_events.py` or a new focused test (behavioral, Python-level).

5. **`test_no_shadow_packet_call_when_env_var_unset`**
   Category: integration.
   Verifies (per Acceptance Criteria item 4): running the equivalent shell command with
   `SHADOW_CONTEXT_PACKET_ENABLED` unset (or `!= "1"`) produces no `python3`/`wrap_context_packet_assembly`
   invocation and appends zero lines to `events.jsonl`. Implementable as a subprocess-level test
   that extracts the exact command string from `implement-ticket.js` (via regex) and runs it in a
   `tmp_path`-scoped shell with `SHADOW_CONTEXT_PACKET_ENABLED` unset, asserting no new file/line
   appears in a scoped `events_file` path (if the command is parameterized to accept one) or that
   no `python3` subprocess launches (e.g. by asserting the shell short-circuits before reaching
   `timeout`).
   Location: `tests/tools/test_shadow_packet_call_site.py`.

6. **`test_no_packet_variable_in_any_agent_prompt_backtick_literal`**
   Category: architecture guard (grep-based, per Acceptance Criteria item 5).
   Verifies: zero occurrences of any packet-related identifier (`packet`, `ContextPacket`,
   `wrap_context_packet_assembly`, `assemble_context_packet`) inside the body of any `` agent(`...`) ``
   template-literal call in `implement-ticket.js` — implemented by extracting each `agent(\`...\`)`
   call's literal body (regex/balanced-backtick scan) and asserting none contains those
   substrings, distinct from asserting they don't appear in the file *at all* (they legitimately
   appear inside the new orchestrator-only `bash()` call, which is not an `agent()` prompt).
   Location: `tests/tools/test_shadow_packet_call_site.py`.

7. **`test_real_run_id_passed_and_phase_field_unchanged`**
   Category: unit / static-source guard.
   Verifies (per Acceptance Criteria item 6): the command string passes the real ticket's `tid`
   (i.e. references the JS `tid` variable, e.g. via an individually-quoted argv element
   `"${tid}"`, or the equivalent inside the `-c` script's `sys.argv`) into the call, AND the
   source of `tools/retrieval_events.py` is unchanged — `phase="Retrieval"` and
   `AGENT_PACKET = "context-packet-wrapper"` literals still present verbatim (regression check,
   overlapping with the Regression Surface's `test_retrieval_events.py` coverage but asserted
   directly against source text here too, since this ticket's diff must not touch that file at
   all).
   Location: `tests/tools/test_shadow_packet_call_site.py`.

8. **`test_minimal_candidate_set_no_hybrid_retrieval_import`**
   Category: unit / static-source guard.
   Verifies (per Acceptance Criteria item 7): the command string contains no reference to
   `hybrid_retrieval` (module name or `hybrid_fuse_and_filter`), and `included_candidates` is
   constructed either as an empty list or from a small, fixed number of `unrated_candidate(...)`
   calls built from ticket title/summary-derived argv strings — not a call into the real retrieval
   pipeline.
   Location: `tests/tools/test_shadow_packet_call_site.py`.

9. **`test_docs_path_present_in_the_same_diff`**
   Category: integration (repo-state check, not source-text).
   Verifies (per Acceptance Criteria item 8 and the ticket's own Scope): a `docs/` path (expected:
   `docs/agent-monitoring/schema.md`, per this ticket's investigation finding that its existing
   Provenance section becomes factually stale once this ships) is part of the ticket's
   `files_changed` set for `tools/gate_checks/doc_staleness_check.py::check_doc_staleness()` to
   return `PASS` for a `behavior_changed=True`, `.claude/workflows/implement-ticket.js`-containing
   `files_changed` list. Can be tested directly and cheaply by calling
   `check_doc_staleness(files_changed=[".claude/workflows/implement-ticket.js", "docs/agent-monitoring/schema.md", ...], behavior_changed=True)`
   and asserting `status == "PASS"`.
   Location: `tests/tools/test_shadow_packet_call_site.py` (or reuse
   `tests/tools/test_doc_staleness_check.py` if it exists, as an additive test case).

10. **`test_no_new_field_in_retrieval_event_fields`**
    Category: architecture guard (regression-prevention, ticket-specific negative control).
    Verifies (per Acceptance Criteria item 8-of-the-Related-Docs-numbered-list / Out of Scope):
    `frozenset` equality of `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS` against its known,
    pre-this-ticket 18-member set (mirrors `TestFieldShapeConstant::test_field_set_contains_exactly_expected_retrieval_fields`
    in `tests/tools/test_retrieval_events.py`, run again here as a ticket-specific negative
    control so a regression is caught under this ticket's own test name too, not only the shared
    one).
    Location: `tests/tools/test_shadow_packet_call_site.py`.

11. **`test_shadow_event_seq_never_collides_with_any_real_phase_seq`**
    Category: unit / regression guard — **this is the specific gap an architecture-review
    NEEDS_CHANGES verdict flagged as missing from the original test list** (see investigation.md's
    "Resolved: Disjoint Shadow-Event Seq Scheme" subsection): the original plan's shadow call
    computed `seq` via `events.length + 1 + seqOffset` evaluated *after* `pushEvent('Investigate',
    ...)`, which silently aliases onto the identical expression Plan's own `writeSidecar` evaluates
    next (since the shadow write never advances `events.length`) — producing a real
    `('Plan', 'planner')` event and the shadow `('Retrieval', 'context-packet-wrapper')` event
    sharing one `(run_id, seq)` key.
    Verifies two properties, both required:
    (a) **Static** — the shadow call's `seq` argument in `implement-ticket.js`'s new `bash()` call
    is a literal that does not reference `events.length` or `seqOffset` anywhere in its
    construction (regex/source-text check that the shadow call site's argv/script does not contain
    the substring `events.length` or bare `seqOffset` in the position supplying `seq=`), and is
    provably `<= 0` (a negative integer literal, or an expression that can only ever produce a
    non-positive integer, e.g. `-(1 + <count>)`).
    (b) **Behavioral** — construct a fixture list of real per-phase events for a synthetic run,
    covering both a fresh run (`seqOffset=0`, `seq` values `1..N`) and a resumed run
    (`seqOffset=K>0`, `seq` values `K+1..K+N`) — reusing `tests/tools/test_seq_offset.py`'s
    `_event(run_id, seq)` fixture-building helper for consistency — then compute the shadow
    event's `seq` value using whatever function/literal the implementation ships, and assert
    `shadow_seq not in {e["seq"] for e in real_events}` for every `N` from 1 through at least 10
    (covering every current phase count) and for at least two distinct `seqOffset` values
    (0 and a nonzero resume offset). Additionally assert the property holds even when the fixture
    includes **two** prior shadow events for the same `run_id` (simulating this exact re-investigation
    scenario — Investigate re-executing after a NEEDS_CHANGES gate failure) if the implementation
    ships the monotonic-negative-counter variant rather than a fixed sentinel; if a fixed sentinel
    is shipped instead, assert the fixed sentinel's own value stays `<= 0` and add a code comment
    (not a test skip) noting the shadow-vs-shadow duplicate-identity gap is accepted, not covered.
    Location: `tests/tools/test_shadow_packet_call_site.py`.

## Scoped Pytest Commands

```
# New/ticket-specific static-source guards
pytest tests/tools/test_shadow_packet_call_site.py -v

# Full orchestrator-file regression surface (implement-ticket.js static guards)
pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py \
       tests/tools/test_scope_orphan_fix.py tests/tools/test_monitoring_bypass_fix.py \
       tests/tools/test_plan_gate_static.py -v

# Retrieval-event / packet-assembly regression surface (must remain green, no signature changes)
pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_parity_check.py \
       tests/tools/test_retrieval_event_wrapper_single_source.py -v

# Gate-check regression (doc-staleness gate this ticket's own diff must satisfy)
pytest tests/tools/test_doc_staleness_check.py -v   # if present; otherwise covered inline above

# Frontmatter / DoD static-check coverage for this ticket's own staging artifacts
pytest tests/tools/test_done_checker_static.py -v
```

Never `pytest tests/` — scope stays within `tests/tools/` (agent-orchestration/monitoring domain),
consistent with this ticket having zero `src/` or simulation-logic touch.

## Anti-Drift Test Guards

- **Adjacency guard (test #2)** directly protects against the single highest-probability mistake
  in this ticket: inserting the new call between `writeSidecar` and `agent(` for Investigate,
  which would silently corrupt tool-call attribution for every future Investigate phase run, not
  just fail a test loudly — this guard must run and pass before any other verification.
- **Structural guard (test #9 target, `test_retrieval_event_wrapper_single_source.py`)** already
  in the Regression Surface catches any accidental edit to `tools/retrieval_events.py` itself to
  "make wiring easier" (e.g. adding a workflow-aware helper there instead of keeping all
  JS-side wiring in `implement-ticket.js`) — this must stay untouched by this ticket's diff.
- **Negative control (test #10)** catches scope creep toward "just add one more field while I'm in
  here" — a single-line diff to `RETRIEVAL_EVENT_FIELDS` would otherwise pass unnoticed by any
  test that only checks the new call site's shape.
- **Env-var-unset guard (test #5)** catches the specific regression of the toggle silently
  defaulting to enabled (e.g. an inverted condition, `!=` written as `==`, or a shell quoting bug
  that makes the guard always-true) — this is the ticket's core safety property ("off by default,
  opt-in") and must never regress silently.
- **Agent-prompt-isolation guard (test #6)** catches the most severe possible scope-creep outcome
  for this ticket: any future edit that starts surfacing packet content to a real agent's prompt
  (explicitly Phase 6 work, not this ticket) — this guard must distinguish "packet reference
  inside the orchestrator's own `bash()` string" (expected, fine) from "packet reference inside an
  `agent()` backtick literal" (forbidden), so it must parse `agent()` call boundaries specifically,
  not just grep the whole file for the word "packet".
- **`RUN_ID_PACKET` default-vs-override guard (implicit in test #7)** — protects against silently
  reverting to the synthetic `RETRIEVAL-EVENT-context-packet` default `run_id` instead of passing
  the real `tid`, which would defeat the entire point of this ticket (attributing the shadow event
  to the real workflow run) while still looking superficially correct (the call would still run,
  still emit an event, just under the wrong provenance).
- **Seq-disjointness guard (test #11)** — the highest-priority guard added in this re-investigation
  pass: catches a regression back to computing the shadow call's `seq` from `events.length`/
  `seqOffset` (the exact defect an architecture-review NEEDS_CHANGES verdict caught in the original
  plan). Without this guard, a future edit could "simplify" the shadow call by reusing the
  `events.length + 1 + seqOffset` idiom already visible everywhere else in the file — visually
  consistent with the rest of `implement-ticket.js`, but silently reintroducing a `(run_id, seq)`
  collision with the next real phase's event on every standard-tier run. This guard must run and
  pass before any other verification, alongside the adjacency guard (test #2).
