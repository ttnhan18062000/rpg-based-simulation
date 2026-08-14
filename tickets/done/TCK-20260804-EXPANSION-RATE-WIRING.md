---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260804-EXPANSION-RATE-WIRING
phase: open
date: 2026-08-04
tags: [agent-monitoring, observability]
---

# TCK-20260804-EXPANSION-RATE-WIRING

## Title
Wire expansion_reason/expansion_count into the retrieval-event wrap_*() producers so expansion_rate stops being permanently inert

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`generate_retro.py`'s `compute_retrieval_metrics()` (lines ~699-711) computes `expansion_rate` as the fraction of retrieval events carrying a non-None `expansion_reason`/`expansion_count`, and this computation itself is correct and already unconditional (not gated on `adequacy_verdict`, per an earlier resolved design decision). The problem is upstream: none of the 3 shipped `wrap_*()` functions in `tools/retrieval_events.py` (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) ever pass `expansion_reason`/`expansion_count` to `emit_retrieval_event()` — the fields exist in `RETRIEVAL_EVENT_FIELDS` (schema-level) but no producer populates them, so `expansion_rate` is permanently 0.0% regardless of real retrieval behavior. `docs/agent-monitoring/schema.md:287` documents the fields as "Present only if a follow-up expansion occurred" — implying a caller-driven retry/widen-and-retry pattern is the intended trigger, not something the wrapper computes internally. A grep across `tools/knowledge_search.py`, `tools/hybrid_retrieval.py`, and `tools/context_packet_assembler.py` for retry/widen/broaden/expand logic found **zero hits** — no caller in the current codebase actually performs a follow-up expanded retrieval today. This means the fix is not pure plumbing (adding pass-through kwargs alone would leave `expansion_rate` still stuck at 0% in practice, since nothing would ever populate them) — it requires a real design decision about what "an expansion" concretely means for each of the 3 producer types, given no real expansion-triggering caller exists yet.

## Scope
- Investigate whether any existing caller (test invocations, the shadow-packet call site in `.claude/workflows/implement-ticket.js`, or any Phase 3/4 module) has an implicit "try again with different params" pattern that could be the natural `expansion_reason`/`expansion_count` trigger, even if not currently instrumented.
- Design (Plan phase) a concrete, minimal definition of "expansion" per producer:
  - `wrap_hybrid_retrieval` (candidate/selection widening)
  - `wrap_retrieval_cache_check` (cache-miss-triggered escalation to a broader cache level, if that's a real behavior — verify)
  - `wrap_context_packet_assembly` (the `"budget_exceeded"` example value in `tests/tools/test_retrieval_events.py:118` suggests packet-budget-triggered re-assembly with a smaller/different candidate set — verify whether `assemble_context_packet()` has any such retry today)
- Add optional `expansion_reason: str | None = None` / `expansion_count: int | None = None` parameters to the relevant `wrap_*()` function(s), forwarded to `emit_retrieval_event()` only when the caller supplies them (never fabricated, never defaulted to a fake value).
- If investigation finds that NO real caller-side expansion behavior exists anywhere yet (most likely, per the grep above), the plan must explicitly decide between: (a) scoping this ticket to plumbing-only (wire the pass-through, document that `expansion_rate` will remain 0.0% until a future caller actually performs an expansion — an honest, disclosed limitation, not a fabricated fix) or (b) implementing a minimal, real, in-scope expansion trigger for one producer (likely `wrap_context_packet_assembly`'s budget-exceeded case, since that's the one with a documented example value and a plausible existing signal — `ContextPacket`'s own budget/exclusion data). This decision must not be assumed here; investigation.md and plan.md make the call explicitly.
- Add/update tests in `tests/tools/test_retrieval_events.py` and `tests/tools/test_generate_retro.py` covering whatever is actually wired.
- Update `docs/agent-monitoring/schema.md` if the "present only if a follow-up expansion occurred" description needs sharpening once the concrete trigger is defined.

## Out of Scope
- Building a general-purpose retry/backoff framework for retrieval — if a real expansion trigger is implemented, it must be the minimal mechanism needed to make the metric real, not a new abstraction layer.
- Any change to `compute_retrieval_metrics()`'s existing `expansion_rate` formula itself — it is already correct; this ticket is producer-side only.
- The raw-investigation-count metric (sibling ticket TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC, already DONE).
- Wiring `tools/hybrid_retrieval.py`/`tools/context_packet_assembler.py` into any real (non-shadow) production workflow path — that remains explicitly deferred per `docs/plans/archive/agent_infrastructure/context_efficient_agent_retrieval/` and the backlogged epic TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.

## Acceptance Criteria
- [ ] Investigation explicitly determines whether real expansion-triggering caller behavior exists anywhere in the codebase today, with evidence (not assumed).
- [ ] Plan makes an explicit, disclosed decision between plumbing-only vs. minimal-real-trigger, with rationale.
- [ ] Whatever is implemented is tested, and the test suite does not assert a fabricated/fake expansion rate — either real coverage of an actual trigger, or an explicit test that expansion_rate legitimately stays 0.0% absent any real expansion event (never a hardcoded fake to make a number move).
- [ ] `docs/agent-monitoring/schema.md`'s field description remains accurate to whatever was actually implemented.
- [ ] No fabricated or silent expansion data anywhere in the change.

## Related Tickets
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT (defined the `expansion_reason`/`expansion_count` schema fields, explicitly left population out of scope)
- TCK-20260729-RETRIEVAL-RETRO-VIEWS (built `compute_retrieval_metrics()`'s `expansion_rate` computation)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (sibling ticket, same user request, already DONE)

## Related Docs
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/`
- `stored_artifacts/TCK-20260729-RETRIEVAL-RETRO-VIEWS/`

## Related Code Areas
- `tools/retrieval_events.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, `tools/context_packet_assembler.py` (potential expansion trigger sites)

## Assumptions / Open Questions
Whether a real, minimal expansion trigger should be implemented (option b) or whether honest plumbing-only with a disclosed permanent-0%-until-real-usage limitation (option a) is correct — this is the central open question the Investigate/Plan phases must resolve with evidence, not an assumption made at Scope time.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260804-EXPANSION-RATE-WIRING/plan.md`'s
6-step Option A (plumbing-only) decision. No deviation from the plan.

- **Step 1-3**: Added keyword-only `expansion_reason: str | None = None` /
  `expansion_count: int | None = None` params to all 3 `wrap_*()` functions in
  `tools/retrieval_events.py` (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`,
  `wrap_context_packet_assembly`), placed after `ts` and before the `**kwargs` catch-all so they
  are never accidentally forwarded into the wrapped function's own call. `wrap_hybrid_retrieval`
  and `wrap_context_packet_assembly` build a new `optional_expansion_fields` conditional dict
  (only populated when the caller's value is not `None`) and spread it (`**`) as the final
  argument to their existing `emit_retrieval_event()` call. `wrap_retrieval_cache_check` extends
  its pre-existing conditional `retrieval_fields` dict (the same one already used for
  `corpus_generation`/`retrieval_version`) with the same `if ... is not None:` guards — no new
  dict or spread site needed there, matching the codebase's own established precedent exactly.
  This guarantees the `None`-vs-absent-key distinction the plan calls out as the ticket's single
  most important correctness detail: omitting the caller kwarg means the key is genuinely absent
  from the emitted JSON record, never present with a literal `null`.
- **Step 4**: Added 7 tests to `tests/tools/test_retrieval_events.py`: 2 per wrapper class
  (`test_wrapper_omits_expansion_fields_when_not_supplied`,
  `test_wrapper_forwards_expansion_fields_when_supplied` — 6 total across
  `TestWrapHybridRetrieval`/`TestWrapRetrievalCacheCheck`/`TestWrapContextPacketAssembly`), plus
  one new class `TestWrapFunctionsNeverFabricateExpansionReason` holding
  `test_wrap_functions_never_fabricate_expansion_reason_internally`, which exercises all 3
  wrappers with a cache MISS, a `noisy`-triggering candidate/selected ratio, and a nonzero
  `exclusion_reason_counts` respectively — none supplying `expansion_reason`/`expansion_count` —
  and asserts both keys stay absent in every case. The new `wrap_hybrid_retrieval` tests needed
  the same `_dense_candidates` monkeypatch pattern the file's pre-existing
  `test_wrapper_emits_exactly_one_retrieval_event` already uses (the bare test sqlite DB has no
  `knowledge_vec` virtual table, so the real dense-candidate SQL path would otherwise raise
  `OperationalError`). For the noisy-verdict case, used a 1-doc DB with `top_k=2`
  (`candidate_k(2)=8 >= NOISY_RATIO_THRESHOLD(5) * selected_count(1)`), verified against
  `compute_adequacy_verdict()`'s actual branch logic before writing the assertion. Also added
  `test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger` to
  `tests/tools/test_generate_retro.py`'s `TestComputeRetrievalMetrics`, which was not yet present
  (checked first, per test_plan.md's instruction) — reads the real
  `agent-monitoring/events.jsonl` via `generate_retro.load_jsonl(generate_retro.EVENTS_FILE)` and
  asserts `compute_retrieval_metrics()` still reports `expansion_rate == 0.0`, an explicit
  regression guard against a future silent fabrication.
- **Step 5**: Updated `docs/agent-monitoring/schema.md`'s `expansion_reason`/`expansion_count`
  row to disclose that all 3 producers now accept these as optional pass-through params but none
  currently supplies them, cross-referencing Open Decisions 5/6 and
  `EXPANSION_POLICY_STUB`. Per the reviewer's non-blocking nit on the plan (the phrase "no shipped
  wrap_*() function emits expansion_reason/expansion_count today" actually lives in INFRA-298's
  `text` field, `docs/parity_ledger/infrastructure.yaml:6330`, not INFRA-297's
  `support_boundary`), the new schema.md sentence states the characterization directly in its own
  words rather than implying it was already written verbatim in INFRA-297.
- **Step 6**: Amended `INFRA-297` (`docs/parity_ledger/infrastructure.yaml`) in place — appended a
  descriptive clause to each of the 3 wrapper bullets in `v2_evidence` (mirroring the exact
  in-place-amendment precedent already used there for
  `TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE`), and appended one clarifying sentence to
  `support_boundary` confirming the "no producer wired" characterization for these two fields
  predates this ticket and remains true after it. No new `INFRA-3xx` entry created.
  `status: verified`, `priority: P2`, `proof_type: regression`, `test_path` all left unchanged.
  Confirmed the file still parses as valid YAML after editing.

No architectural conflicts encountered; no deviation from plan.md required (see staging
artifacts — no Deviations section was added since none was needed).

## Test Summary
`pytest tests/tools/test_retrieval_events.py tests/tools/test_generate_retro.py -v` — **133
passed, 0 failed, 0 skipped** (36 in `test_retrieval_events.py`, 97 in `test_generate_retro.py`,
including all 7 new tests from Step 4). Confirmed zero existing tests required modification, as
test_plan.md predicted — `emit_retrieval_event()`'s record shape is additive/dict-based, not
key-set-enumerated at this layer.

## Files Changed
- `tools/retrieval_events.py` — added optional `expansion_reason`/`expansion_count` pass-through
  params to `wrap_hybrid_retrieval()`, `wrap_retrieval_cache_check()`,
  `wrap_context_packet_assembly()`.
- `tests/tools/test_retrieval_events.py` — added 6 per-wrapper omit/forward tests plus 1
  cross-wrapper anti-fabrication regression test (7 new tests total).
- `tests/tools/test_generate_retro.py` — added
  `test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger` to
  `TestComputeRetrievalMetrics`.
- `docs/agent-monitoring/schema.md` — updated `expansion_reason`/`expansion_count` row
  description (line ~287) to disclose the current no-producer state and why.
- `docs/parity_ledger/infrastructure.yaml` — amended `INFRA-297`'s `v2_evidence` (3 wrapper
  bullets) and `support_boundary` in place; no new entry.

## Completion Summary
Added optional, never-fabricated `expansion_reason`/`expansion_count` pass-through parameters to
all 3 `wrap_*()` producers in `tools/retrieval_events.py`, resolving the mechanical half of the
user's original question about `generate_retro.py`'s permanently-0.0% `expansion_rate` metric.
Investigation found real, load-bearing cross-ticket architectural evidence — `context_packet_
assembler.py`'s `EXPANSION_POLICY_STUB` and a dedicated regression test guarding it — showing that
inventing a real expansion trigger now would force-resolve deferred Open Decisions 5/6 through a
monitoring-event side door, directly contradicting `ticket_plan_structure_phase3.md`'s explicit
"do not force-resolve" instruction. Plan independently re-verified this evidence and chose the
plumbing-only path (Option A): the mechanism is now ready for a future ticket to use the moment
real escalation semantics are designed, but `expansion_rate` honestly continues reading 0.0% today
— disclosed explicitly in `docs/agent-monitoring/schema.md`, the ticket itself, and a dedicated
regression test (`test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger`)
guarding against future silent fabrication. 7 new tests, 133/133 total passing. Parity phase caught
and fixed 2 real stale line-range citations in `INFRA-297` (from Implement not re-deriving line
numbers after inserting code) plus a can-vs-does precision clarification on `INFRA-298`. Verify's
first pass correctly BLOCKED on a real (if minor) format defect in this ticket's own investigation.md
bullet syntax — fixed by aligning to the established, already-working convention (confirmed against
the sibling ticket) rather than weakening the checker. Full standard-tier pipeline: Investigate →
Plan → Review (APPROVED) → Implement → Architecture-Verify (APPROVED) → Document-Update (clean) →
Test (133/133) → Parity (2 real fixes) → Verify (1st pass BLOCKED on a real format defect, fixed,
2nd pass READY TO CLOSE, all 13 DoD conditions PASS).
