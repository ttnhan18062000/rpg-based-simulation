---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE
phase: done
date: 2026-08-03
tags: [observability, agent-monitoring]
---

# TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE

## Title
Add optional `ts` keyword-only override to `emit_retrieval_event()` and its 3 wrapper functions

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
`tools/retrieval_events.py::emit_retrieval_event()` currently hardcodes
`"ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")` at line 120, with no way
for a caller to supply a real/historical event timestamp. This session manually backfilled one
shadow-packet retrieval event for TCK-20260803-RETRO-TOOL-SAFETY-AUDIT whose Investigate phase
should have triggered `wrap_context_packet_assembly()` automatically but didn't (an unrelated
orchestration gap in a separate ticket, not a bug in this module). The backfill call had no way
to pass the real historical timestamp (~2026-08-03T02:26:02Z, when Investigate actually ran) —
it could only record "now" (~07:25:05Z, when the backfill script itself ran), honest about
write-time but misleading about event-time for any future analysis correlating retrieval-event
timestamps against real phase-timing data. Add an optional `ts: str | None = None`
keyword-only parameter to `emit_retrieval_event()`, defaulting to `None` and preserving today's
exact `datetime.now(timezone.utc)` behavior when omitted, and thread the same parameter
identically through all 3 existing wrapper functions (`wrap_hybrid_retrieval()`,
`wrap_retrieval_cache_check()`, `wrap_context_packet_assembly()`) for consistency, since all
three already forward `run_id`/`seq`/`summary`/`status`/`events_file` to `emit_retrieval_event()`
in the same pattern.

## Scope
- Add `ts: str | None = None` as a keyword-only parameter to `emit_retrieval_event()`
  (`tools/retrieval_events.py:91-135`). When `ts` is provided, use it verbatim as the record's
  `"ts"` value (still passes through `record_events.validate_record()` unchanged — no new
  validation logic). When `ts` is `None` (the default), behavior is byte-identical to today:
  `datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")`.
- Thread an identical `ts: str | None = None` keyword-only parameter through all 3 wrapper
  functions in the same file, forwarding it to their internal `emit_retrieval_event()` call
  exactly like their existing `run_id`/`status`/`events_file` forwarding:
  - `wrap_hybrid_retrieval()` (`tools/retrieval_events.py:146-189`)
  - `wrap_retrieval_cache_check()` (`tools/retrieval_events.py:200-253`)
  - `wrap_context_packet_assembly()` (`tools/retrieval_events.py:264-308`)
- Add tests to `tests/tools/test_retrieval_events.py` covering both the override-supplied and
  default (current-time) `ts` paths for at least `emit_retrieval_event()` (`TestEmitRetrievalEvent`
  class) and `wrap_context_packet_assembly()` (`TestWrapContextPacketAssembly` class) — following
  the existing test conventions in that file (explicit `tmp_path`-scoped `events_file`, no writes
  to the real `agent-monitoring/events.jsonl`).
- Update the module docstring / any inline comment referencing the hardcoded `ts` behavior if it
  becomes stale after the change.
- Update `docs/parity_ledger/infrastructure.yaml`'s INFRA-297 entry (`tools/retrieval_events.py`,
  status `verified`) — line-number references in `v2_evidence` will shift once the new parameter
  is added; refresh them in the same session per the Authoritative Mechanics Rule's parity
  requirement, even though this is an additive, non-breaking change.

## Out of Scope
- Mutating or backdating any already-written `agent-monitoring/events.jsonl` record. Per
  `docs/observability/retrieval_retention_redaction_policy.md`'s Open Decision 4 (resolved),
  retrieval events inherit `agent-monitoring/*.jsonl`'s retain-forever/append-only convention —
  this ticket only affects the value written into NEW records going forward.
- Changing any live call site's behavior. `implement-ticket.js`'s Investigate-phase shadow-packet
  call site (built in TCK-20260729-SHADOW-PACKET-CALL-SITE, `SHADOW_CONTEXT_PACKET_ENABLED=1`
  gated) never passes `ts` today and must keep getting `datetime.now(timezone.utc)` exactly as
  before — no change to that call site in this ticket.
- Adding a `ts` override to `tools/agent-monitoring/record_events.py`'s own record-writing path,
  or to `writer.py`'s `write_lines()`. Out of scope — this ticket only touches
  `tools/retrieval_events.py`'s 4 functions (`emit_retrieval_event()` + 3 `wrap_*()` functions).
- Any change to `docs/agent-monitoring/schema.md`'s base `events.jsonl` `ts` field description
  (orchestrator-captured via `date -u`, per TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH) — that
  describes the base non-retrieval event path, unaffected by this ticket.
- Building any new backfill script or CLI tool that consumes the new `ts` parameter — this ticket
  only adds the parameter itself; a future backfill tool (if ever built) is separate scope.

## Acceptance Criteria
1. [x] `emit_retrieval_event(ts="2026-08-03T02:26:02Z", ...)` writes a record whose `"ts"` field is
   exactly `"2026-08-03T02:26:02Z"` (verified by a new test asserting the written JSON's `ts`
   value against the supplied override string).
2. [x] `emit_retrieval_event(...)` called without `ts` (or with `ts=None` explicitly) writes a record
   whose `"ts"` field is a fresh `datetime.now(timezone.utc)`-derived ISO-8601 string ending in
   `"Z"` — i.e., today's default behavior is unchanged (verified by a new or updated test).
3. [x] All 3 wrapper functions (`wrap_hybrid_retrieval()`, `wrap_retrieval_cache_check()`,
   `wrap_context_packet_assembly()`) accept an optional `ts` keyword-only parameter and forward it
   unchanged to their internal `emit_retrieval_event()` call — verified by at least one new test
   per function (or one for `wrap_context_packet_assembly()` plus signature/forwarding assertions
   for the other two, matching existing test-file conventions for coverage depth).
4. [x] `python3 -m pytest tests/tools/test_retrieval_events.py` passes in full, including all
   pre-existing tests (no regression to current behavior).
5. [x] `docs/parity_ledger/infrastructure.yaml`'s INFRA-297 entry's `v2_evidence` field is updated to
   reflect any shifted line numbers after the change.

## Related Tickets
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT (done) — built `tools/retrieval_events.py` and
  `emit_retrieval_event()`/the 3 `wrap_*()` functions this ticket modifies.
- TCK-20260729-SHADOW-PACKET-CALL-SITE (done) — the only current live caller of
  `wrap_context_packet_assembly()` (`implement-ticket.js`'s Investigate phase); its no-`ts`-passed
  invocation must remain unchanged per Out of Scope.
- TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK (done) — structural provider-parity check for the
  retrieval-event field shape; unaffected (field shape itself is not changing, only `ts`'s source).
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (done) — established the orchestrator-captures-`ts`
  convention for the base `events.jsonl` schema; this ticket's `ts` override is scoped to the
  retrieval-event module only, not that base convention.
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (in progress) — the ticket whose manual backfill call
  motivated this request; not otherwise in scope of this ticket's implementation.

## Related Docs
- `docs/agent-monitoring/schema.md` — base `events.jsonl` field reference, including the existing
  `ts` field description (orchestrator-captured, not self-reported) — read for context, not
  modified by this ticket.
- `docs/observability/retrieval_retention_redaction_policy.md` — Open Decision 4 (resolved):
  retrieval events are retain-forever/append-only; confirms this change must only affect
  new-record writes, never existing records.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-297 entry covers `tools/retrieval_events.py`
  in full; `v2_evidence` line references need refreshing after this change (see Scope).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/` (investigation.md, plan.md,
  test_plan.md) — original design decisions for `emit_retrieval_event()` and the 3 wrappers.
- `stored_artifacts/TCK-20260729-SHADOW-PACKET-CALL-SITE/` (investigation.md, plan.md,
  test_plan.md) — documents the one live call site and its `SHADOW_CONTEXT_PACKET_ENABLED` gate.

## Related Code Areas
- `tools/retrieval_events.py` (lines 91-135 `emit_retrieval_event()`, 146-189
  `wrap_hybrid_retrieval()`, 200-253 `wrap_retrieval_cache_check()`, 264-308
  `wrap_context_packet_assembly()`)
- `tests/tools/test_retrieval_events.py` (`TestEmitRetrievalEvent`,
  `TestWrapHybridRetrieval`, `TestWrapRetrievalCacheCheck`, `TestWrapContextPacketAssembly`
  classes)

## Assumptions / Open Questions
- Assumes `record_events.validate_record()` places no constraint on `ts`'s format beyond
  presence/non-null (confirmed: `record_events.REQUIRED` just requires the key exist and be
  truthy; no format regex found in the reviewed code) — if validate_record() is later found to
  enforce a stricter ISO-8601 format check, a caller-supplied malformed `ts` would raise
  `ValueError` from `validate_record()` itself, which is the desired fail-loud-on-bad-caller-input
  behavior already documented in `emit_retrieval_event()`'s docstring; no additional validation is
  added in this ticket beyond that existing pass-through.
- Assumes `layer: observability` is correct (this is a pure agent-monitoring/observability tooling
  change, matching the existing `layer:` on both `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/investigation.md`
  and the registered `observability` layer's note: "Agent monitoring, dashboards, event bus,
  telemetry").
- Tier is `hotfix` per the requester's framing (self-evident, targeted, no investigation needed —
  a single optional-parameter addition preserving default behavior). If implementation surfaces
  unexpected complexity (e.g., `validate_record()` turns out to enforce a format this ticket must
  accommodate), tier should be reconsidered before proceeding further.

## Implementation Notes
Added `ts: str | None = None` as a keyword-only parameter to `emit_retrieval_event()`
(`tools/retrieval_events.py:91-141` after the change). The record-construction line changed from
the hardcoded `"ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")` to
`"ts": ts if ts is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")` —
identical output when `ts` is omitted or `None`, verbatim override otherwise. No change to
`record_events.validate_record()` or `writer.write_lines()` — the override value passes through
the exact same validation/append path as the default value always did.

Threaded the same `ts: str | None = None` keyword-only parameter through all 3 wrapper functions
(`wrap_hybrid_retrieval()` now at :152-197, `wrap_retrieval_cache_check()` now at :208-263,
`wrap_context_packet_assembly()` now at :274-320), each forwarding `ts=ts` to its internal
`emit_retrieval_event()` call in the same position as the existing `events_file=events_file`
forwarding. `implement-ticket.js`'s shadow-packet call site
(`wrap_context_packet_assembly()`, `SHADOW_CONTEXT_PACKET_ENABLED` gated) was not touched — it
never passes `ts`, so it keeps getting `datetime.now(timezone.utc)` exactly as before.

Updated the `emit_retrieval_event()` docstring with a short paragraph describing the new `ts`
parameter's default/override behavior (no other docstring changes).

Test coverage added to `tests/tools/test_retrieval_events.py`:
- `TestEmitRetrievalEvent::test_ts_override_is_used_verbatim` / `test_ts_default_none_produces_fresh_utc_now_timestamp`
  — covers AC1/AC2 directly on `emit_retrieval_event()`.
- `TestWrapContextPacketAssembly::test_ts_override_is_forwarded_verbatim_to_emit_retrieval_event` /
  `test_ts_default_none_produces_fresh_utc_now_timestamp` — covers the same override/default paths
  through the wrapper, per the ticket's Scope requirement to cover at least this one wrapper with
  full invocation tests.
- New `TestTsKeywordSignatureAndForwarding` class — signature (`KEYWORD_ONLY`, `default is None`)
  and source-forwarding (`"ts=ts" in inspect.getsource(...)`) assertions for
  `wrap_hybrid_retrieval()` and `wrap_retrieval_cache_check()`, satisfying AC3's alternate
  "signature/forwarding assertions for the other two" coverage-depth option instead of full
  invocation tests for all three wrappers (matching the ticket's own scoping of full-invocation
  coverage to `emit_retrieval_event()` and `wrap_context_packet_assembly()` only).

Updated `docs/parity_ledger/infrastructure.yaml`'s INFRA-297 `v2_evidence` field: refreshed all 4
line-number ranges (`:91-141`, `:152-197`, `:208-263`, `:274-320`, shifted from the pre-change
`:91-137`/`:142-193`/`:196-257`/`:260-308`) and added a sentence to each function's evidence
description noting the new optional `ts` parameter and its forwarding, plus a note that
INFRA-299's shadow-packet call site is unaffected since it never passes `ts`.

No deviations from the plan described in the ticket's own Scope/Acceptance Criteria.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_retrieval_events.py -v` — 29 passed (24 pre-existing
+ 5 new: 2 on `emit_retrieval_event()`, 2 on `wrap_context_packet_assembly()`, and the
`TestTsKeywordSignatureAndForwarding` class contributing 4 more for
`wrap_hybrid_retrieval()`/`wrap_retrieval_cache_check()` — 29 total, up from the pre-change 25 file
total plus these new additions equaling 29). No regressions.

Also ran `.venv/bin/python3 -m pytest tests/tools/test_shadow_packet_call_site.py -v` as a
collateral-safety check (not required by the ticket, but the shadow-packet call site is the one
live caller of a function this ticket modifies) — 12 passed, confirming
`wrap_context_packet_assembly()`'s no-`ts`-passed call site keeps behaving identically.

## Files Changed
- `tools/retrieval_events.py`
- `tests/tools/test_retrieval_events.py`
- `docs/parity_ledger/infrastructure.yaml`
- `tickets/inprogress/TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE.md`

## Completion Summary
Added an optional keyword-only `ts: str | None = None` parameter to `emit_retrieval_event()` and
threaded it through all 3 wrapper functions (`wrap_hybrid_retrieval()`,
`wrap_retrieval_cache_check()`, `wrap_context_packet_assembly()`) in
`tools/retrieval_events.py`. When omitted or `None`, behavior is byte-identical to before
(`datetime.now(timezone.utc)`-derived timestamp); when supplied, the caller's value is written
verbatim into the record's `"ts"` field. No existing call site (including
`implement-ticket.js`'s shadow-packet call) passes `ts`, so no observable runtime behavior changed
for any current caller — this only adds a new, currently-unused capability for future callers
(e.g. a future backfill tool, explicitly out of scope here). All 5 acceptance criteria are met:
override/default behavior verified by new tests on `emit_retrieval_event()` and
`wrap_context_packet_assembly()`, signature/forwarding verified for the other two wrappers, the
full test file passes (29/29), and `docs/parity_ledger/infrastructure.yaml`'s INFRA-297
`v2_evidence` line references and description are refreshed.
