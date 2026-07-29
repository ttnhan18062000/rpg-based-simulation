---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-SHADOW-PACKET-CALL-SITE
phase: done
date: 2026-07-29
tags: [workflows, agent-monitoring, observability]
---

# TCK-20260729-SHADOW-PACKET-CALL-SITE

## Title
Add advisory shadow context-packet call site to implement-ticket.js Investigate phase

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Insert a shadow-packet-build call site into implement-ticket.js's Investigate phase, built via tools/context_packet_assembler.py, that stays strictly advisory (never blocks, never changes gate outcomes, never read by the agent doing that phase's work) and is trivially disable-able. Record the resulting shadow-packet request/outcome through tools/retrieval_events.py's existing emit_retrieval_event() schema/writer path, extending it additively only if a genuinely new field turns out to be necessary — and per this ticket's own resolution, reusing the real ticket's TCK-... run_id as the real-vs-synthetic provenance signal instead of adding a new field.

## Scope
- Add one orchestrator-side bash() call inside implement-ticket.js's Investigate phase (only) that invokes tools/context_packet_assembler.py's assemble_context_packet() via wrap_context_packet_assembly(), mirroring the existing orchestrator-only pattern used by tagCheckOutput/archCheckOutput/docStalenessOutput
- Wrap the invocation with a coreutils `timeout <N>s` around the python3 call — the only fail-open primitive available since no existing timeout primitive exists elsewhere in .claude/workflows/*.js
- Gate the call behind a new `SHADOW_CONTEXT_PACKET_ENABLED` env var, off by default (opt-in), adapting consent_gate.py's env-var pattern into the orchestrator's bash()-based idiom
- Pass the real ticket's TCK-... run_id into wrap_context_packet_assembly() so the emitted retrieval event is attributable to the real workflow run
- Leave wrap_context_packet_assembly()'s hardcoded phase="Retrieval" field unmodified — treated as a deliberate, distinct observation-category label, not a duplicate of implement-ticket.js's own phase names
- Use a minimal smoke-test candidate set (derived from the ticket's own title/summary, or empty) as input to assemble_context_packet() — no real retrieval pipeline wired in
- Verify no new field is required in RETRIEVAL_EVENT_FIELDS; the real run_id alone distinguishes a real workflow-triggered shadow event from Phase 4's synthetic RETRIEVAL-EVENT-<slug> standalone invocations
- Ship the required docs/ path update in the same diff so implement-ticket.js's doc-staleness gate does not hard-block the behavior-changing .claude/workflows/*.js diff

## Out of Scope
- No promotion to default/mandatory workflow behavior — toggle stays opt-in, off by default
- No packet content surfaced to any agent's real prompt/context (that is Phase 6)
- No execution_id/provider fields added to the retrieval event schema
- No live Codex pilot
- No real-candidate wiring via tools/hybrid_retrieval.py — deferred to a follow-up ticket once call-site/disable-toggle/fail-open mechanics are proven safe in production
- No call site added to any phase other than Investigate (not Plan, not any other phase)
- No modification of wrap_context_packet_assembly()'s phase="Retrieval" field or its function signature
- No new shadow_mode (or equivalent) field added to RETRIEVAL_EVENT_FIELDS

## Acceptance Criteria
- [x] implement-ticket.js's Investigate phase contains an orchestrator-side bash() call invoking assemble_context_packet() via wrap_context_packet_assembly(), matching the tagCheckOutput/archCheckOutput/docStalenessOutput orchestrator-only pattern
- [x] The invocation is wrapped in `timeout <N>s python3 ...` so a hang or crash cannot delay or block the Investigate phase
- [x] Forcing the packet-build call to fail or time out does not change the Investigate phase's pushEvent status or the workflow's overall return value (covered by a test that simulates failure)
- [x] The call site is skipped entirely unless SHADOW_CONTEXT_PACKET_ENABLED=1 is set — verified by a test run with the var unset producing zero shadow-packet events
- [x] No packet variable or its contents are interpolated into any agent()-prompt template — verified by grep showing zero occurrences inside any agent()-prompt backtick literal
- [x] The call passes the real ticket's TCK-... run_id into wrap_context_packet_assembly(); wrap_context_packet_assembly()'s phase="Retrieval" field is left unchanged
- [x] The candidate list passed to assemble_context_packet() is a minimal smoke-test set (ticket title/summary derived, or empty) — no hybrid_retrieval.py call present in the diff
- [x] No field is added to RETRIEVAL_EVENT_FIELDS; test_retrieval_event_parity_check.py passes unmodified
- [x] A docs/ path is included in files_changed so the doc-staleness gate does not block the diff

## Related Tickets
None.

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/ai/default_packet_scenarios_decision.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/context_packet_assembler.py
- tools/retrieval_events.py
- tools/agent_replay_codex/consent_gate.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_retrieval_events.py
- tests/tools/test_retrieval_event_parity_check.py
- tests/tools/test_retrieval_event_wrapper_single_source.py

## Assumptions / Open Questions
- Exact timeout duration N (seconds) for the coreutils timeout wrapper is an implementation-time decision, left to the Plan phase, since no existing precedent value exists in this repo
- The specific docs/ file to update to satisfy the doc-staleness gate is a Plan-phase decision (e.g. docs/ai/default_packet_scenarios_decision.md or a new short note under docs/engine/contracts/) — must ship in the same diff

## Implementation Notes
Implemented exactly per the approved (post-NEEDS_CHANGES) plan.md, in 3 steps:

1. **`.claude/workflows/implement-ticket.js`** — inserted one new `await bash(...)` statement
   immediately after `pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), investigationTs)`
   (the line that follows `writeSidecar`/`agent()` at the top of Investigate) and before the
   `// ─── Phase 3: Plan ───` comment. Verified with `node --check` (valid JS syntax) and
   `tests/tools/test_current_run_sidecar_orchestrator.py` (14/14 pass unmodified — the
   `writeSidecar`→`agent()` adjacency string is untouched). The call: gated behind
   `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]` (strict equality, shell-side only, no
   `process.env` read introduced anywhere in JS), wrapped in `timeout 10s`, and the inner
   `python3 -c` script wraps its own logic in `try/except Exception: pass`; the whole thing ends
   in `2>/dev/null || true`. Inside the script: `run_id = sys.argv[1]` (the real `tid`, passed as
   a single quoted argv element — never interpolated into the Python source string directly);
   `prior_shadow_count` is computed via a read-only scan of `agent-monitoring/events.jsonl` using
   `validate.load_jsonl()` and `record_events.EVENTS_FILE` (both reused read-only, unmodified);
   `shadow_seq = -(1 + prior_shadow_count)`; then `wrap_context_packet_assembly(seq=shadow_seq,
   run_id=run_id, packet_id='shadow-investigate-' + run_id, corpus_generation='shadow',
   retrieval_version=1, budget_requested=0, included_candidates=[])` — empty candidate list, no
   `hybrid_retrieval.py` reference, `phase="Retrieval"` left untouched (hardcoded inside
   `wrap_context_packet_assembly` itself, not edited). Manually dry-ran the extracted command
   (both with the env var set — confirmed two sequential calls produce `seq=-1` then `seq=-2` —
   and unset — confirmed the shell `if` short-circuits with zero writes) against the real
   `events.jsonl`, then removed the two test rows before finishing (`grep -v` cleanup, verified
   via `git diff` that only this ticket's own pre-existing pipeline history — Scope/Investigate/
   Plan/Review events from earlier phases of this same run — remained modified, no test
   pollution left behind).
2. **`tests/tools/test_shadow_packet_call_site.py`** (new) — 12 tests covering all 11 items from
   test_plan.md/plan.md (items 1-8, 10, 11) plus the doc-staleness gate check (item 9). Item 11's
   two required sub-checks (static seq-derivation-expression check, behavioral
   fixture-based non-collision check) are split into two separate test functions
   (`test_shadow_call_seq_derivation_does_not_reference_events_length_or_seqoffset` and
   `test_shadow_event_seq_never_collides_with_any_real_phase_seq`) rather than one combined
   function — a minor structural deviation from the plan's literal grouping, noted in
   staging_artifacts/TCK-20260729-SHADOW-PACKET-CALL-SITE/plan.md's Deviations section; coverage
   is identical to what the plan specified. All 12 tests pass.
3. **`docs/agent-monitoring/schema.md`** — two edits in the one file, exactly as planned: (a) the
   `seq` field-table row (line ~137) gets an appended "Exception" sentence documenting that this
   wrapper's shadow rows use `seq <= 0`; (b) the Provenance-section paragraph (~line 273) is
   split: the `context_packet_assembler.py` case is now called out as the one Phase-3-module
   exception that IS wired into `.claude/workflows/*.js` (via this ticket's call site), with the
   negative-seq scheme and expected `compute_drift_report()` non-canonical-phase/agent side
   effect explained; the remaining prose (for the other two modules' standalone/synthetic
   `RETRIEVAL-EVENT-<slug>` invocations) is kept intact in a following paragraph.

Full regression pass (Step 4 of plan.md): `test_shadow_packet_call_site.py` (12),
`test_current_run_sidecar_orchestrator.py` + `test_step0_ts_orchestrator.py` +
`test_scope_orphan_fix.py` + `test_monitoring_bypass_fix.py` + `test_plan_gate_static.py`,
`test_retrieval_events.py` + `test_retrieval_event_parity_check.py` +
`test_retrieval_event_wrapper_single_source.py`, `test_seq_offset.py`,
`test_done_checker_static.py` — 142 tests total, all pass, none modified.

No scope guard was violated: no call site added outside Investigate; no packet
content/variable referenced inside any `agent()`-prompt backtick literal (verified by grep-based
test); `RETRIEVAL_EVENT_FIELDS` unchanged (18 members, verified against the known set);
`tools/retrieval_events.py`, `tools/context_packet_assembler.py`,
`tools/agent-monitoring/seq_offset.py` untouched; `pushEvent`/`writeSidecar`'s own
`events.length + 1 + seqOffset` expression untouched everywhere in the file.

## Test Summary
- `pytest tests/tools/test_shadow_packet_call_site.py -v` — 12/12 pass (new file).
- `pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py tests/tools/test_scope_orphan_fix.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_plan_gate_static.py tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_parity_check.py tests/tools/test_retrieval_event_wrapper_single_source.py tests/tools/test_seq_offset.py tests/tools/test_done_checker_static.py -v` — 142/142 pass, all unmodified (full regression surface from plan.md Step 4).
- Manual dry-run of the extracted shell command against the real `agent-monitoring/events.jsonl`, both with `SHADOW_CONTEXT_PACKET_ENABLED=1` (two sequential runs produced `seq=-1` then `seq=-2`, confirming the monotonic-negative-counter/resume behavior) and unset (zero writes, shell `if` short-circuits) — verified then cleaned up (no test rows left in the real file).
- `node --check .claude/workflows/implement-ticket.js` — valid JS syntax after the edit.

## Files Changed
- `.claude/workflows/implement-ticket.js` (modified — new shadow-packet `bash()` call site in Investigate phase)
- `tests/tools/test_shadow_packet_call_site.py` (new)
- `docs/agent-monitoring/schema.md` (modified — Provenance section correction + `seq` field carve-out)
- `docs/parity_ledger/infrastructure.yaml` (modified — corrected INFRA-296/INFRA-297's stale "never wired into workflows" claims, added INFRA-299 for this call site)

## Completion Summary
Added an advisory, opt-in (`SHADOW_CONTEXT_PACKET_ENABLED=1`, off by default), fully fail-open
shadow-packet `bash()` call site to `implement-ticket.js`'s Investigate phase, instrumenting
`assemble_context_packet()` via `wrap_context_packet_assembly()` with the real ticket's `tid` as
`run_id` and a monotonic-negative `seq` counter (`-(1 + prior_shadow_count_for_this_run_id)`)
that is provably disjoint from every real per-phase `seq` (`>= 1`) for the run — the fix adopted
after an architecture-review `NEEDS_CHANGES` verdict on the original `events.length`-derived
`seq` approach. Shipped with 12 new tests (`tests/tools/test_shadow_packet_call_site.py`)
covering placement, the env-var gate, fail-open behavior, prompt-isolation, run_id/phase
passthrough, empty-candidate-set/no-hybrid-retrieval, `RETRIEVAL_EVENT_FIELDS` stability, and the
seq-non-collision regression guard, plus the required `docs/agent-monitoring/schema.md` update
(Provenance section + `seq` field carve-out) and `docs/parity_ledger/infrastructure.yaml`
corrections (INFRA-296/297 amended, INFRA-299 added) so the doc-staleness gate does not block this
behavior-changing `.claude/workflows/*.js` diff. Full regression surface (142 tests) passes
unmodified. No scope guard was violated.

As stated in Out of Scope, real-candidate wiring via `tools/hybrid_retrieval.py` remains
deliberately deferred to a follow-up ticket, pending this call-site's opt-in toggle and fail-open
mechanics being proven safe in production — no such wiring is present in this diff.
